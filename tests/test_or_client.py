"""Typed OpenRouter replies: schema validator, legacy parser and the guardrails.

The guard is the part that can silently cost coverage (downgrading a proven
answer) or precision (letting a broken claim through), so both directions are
pinned here with answers from the shipped demo puzzles.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solver'))

from or_client import (CLUE_SCHEMA, TRANSCRIBE_SCHEMA, validate, parse_json, guard_clue,
                       anagram_window, in_lexicon, ORClient)

LEX = {'זרע', 'פורענות', 'פליטים', 'סנהדריה', 'עבדו', 'טפילים'}


def clue_reply(**kw):
    e = {'answer': 'זרע הפורענות', 'tier': 'committed', 'confidence': 0.93, 'mechanism': 'container',
         'fodder': '', 'words': ['זרע', 'הפורענות'], 'definition_side': 'end',
         'hint_fragment': 'דב = פו', 'explanation': 'ז[רעהפורע]נות'}
    e.update(kw)
    return e


class Validator(unittest.TestCase):
    def test_valid_clue(self):
        self.assertEqual(validate(clue_reply(), CLUE_SCHEMA), [])

    def test_missing_and_enum(self):
        probs = validate({'answer': 'x', 'tier': 'sure'}, CLUE_SCHEMA)
        self.assertTrue(any('confidence: missing' in p for p in probs))
        self.assertTrue(any("'sure' not in" in p for p in probs))

    def test_extra_key_and_types(self):
        probs = validate(clue_reply(extra=1, confidence='high', words='זרע'), CLUE_SCHEMA)
        self.assertTrue(any('extra: unexpected key' in p for p in probs))
        self.assertTrue(any('confidence: expected number' in p for p in probs))
        self.assertTrue(any('words: expected array' in p for p in probs))

    def test_transcription_refs(self):
        ok = {'grid': ['..#', '.#.'], 'across': [{'num': 1, 'clue': 'a', 'enum': [2]}], 'down': []}
        self.assertEqual(validate(ok, TRANSCRIBE_SCHEMA), [])
        bad = {'grid': ['..#'], 'across': [{'num': '1', 'clue': 'a', 'enum': [2.5]}], 'down': []}
        probs = validate(bad, TRANSCRIBE_SCHEMA)
        self.assertTrue(any('across[0].num: expected integer' in p for p in probs))
        self.assertTrue(any('enum[0]: expected integer' in p for p in probs))


class LegacyParser(unittest.TestCase):
    def test_fenced_then_bare(self):
        self.assertEqual(parse_json('text ```json\n{"a":1}\n``` more'), {'a': 1})
        self.assertEqual(parse_json('reply: {"a":[1,2]}'), {'a': [1, 2]})
        with self.assertRaises(ValueError):
            parse_json('no json here')


class Guard(unittest.TestCase):
    def test_proven_multiword_survives(self):
        e = guard_clue(clue_reply(), [3, 8], '?' * 11, 'דב מוקף חברים בעסוק מפוקפק, וזה מבשר רע', LEX)
        self.assertEqual(e['tier'], 'committed')
        self.assertEqual(e['guard'], [])

    def test_length_and_split(self):
        e = guard_clue(clue_reply(), [3, 7], None, None, None)
        self.assertEqual(e['tier'], 'suggestion')
        self.assertTrue(any(p.startswith('length') for p in e['guard']))
        e = guard_clue(clue_reply(words=['זרעה', 'פורענות']), [3, 8], None, None, None)
        self.assertTrue(any('word lengths' in p for p in e['guard']))
        e = guard_clue(clue_reply(words=[]), [3, 8], None, None, None)
        self.assertTrue(any('no word split' in p for p in e['guard']))

    def test_crossings(self):
        e = guard_clue(clue_reply(), [3, 8], 'ז??????????', None, None)
        self.assertEqual(e['tier'], 'committed')
        e = guard_clue(clue_reply(), [3, 8], 'ר??????????', None, None)
        self.assertEqual(e['tier'], 'suggestion')
        self.assertTrue(any('crossing' in p for p in e['guard']))

    def test_anagram_needs_literal_window(self):
        clue = 'הטפילים עבדו על השכונה הירושלמית'
        good = clue_reply(answer='הפליטים', mechanism='anagram', fodder='הטפילים', words=['הפליטים'])
        self.assertEqual(guard_clue(dict(good), [7], None, clue, None)['guard'], [])
        bad = clue_reply(answer='הפליטים', mechanism='anagram', fodder='הטפילים עבדו', words=['הפליטים'])
        self.assertTrue(any('fodder letters' in p for p in guard_clue(bad, [7], None, clue, None)['guard']))
        far = clue_reply(answer='הפליטים', mechanism='anagram', fodder='הפליטים', words=['הפליטים'])
        self.assertTrue(any('contiguous window' in p for p in guard_clue(far, [7], None, 'מילים אחרות לגמרי', None)['guard']))
        self.assertTrue(anagram_window(clue, 'הפליטים'))
        self.assertFalse(anagram_window(clue, 'סנהדריה'))

    def test_lexicon_single_word_with_prefix(self):
        self.assertTrue(in_lexicon(LEX, 'הפליטים'))
        self.assertFalse(in_lexicon(LEX, 'קטמונים'))
        e = guard_clue(clue_reply(answer='קטמונים', words=['קטמונים'], mechanism='definition'), [7], None, None, LEX)
        self.assertEqual(e['tier'], 'suggestion')
        e = guard_clue(clue_reply(answer='פקקיסטן', words=['פקקיסטן'], mechanism='portmanteau'), [7], None, None, LEX)
        self.assertEqual(e['tier'], 'committed')

    def test_echo_and_confidence(self):
        e = guard_clue(clue_reply(answer='עבדו', words=['עבדו'], mechanism='definition'), [4], None,
                       'הטפילים עבדו על השכונה', LEX)
        self.assertTrue(any('word of the clue' in p for p in e['guard']))
        e = guard_clue(clue_reply(confidence=0.5), [3, 8], None, None, None)
        self.assertEqual(e['tier'], 'suggestion')
        self.assertEqual(e['tier_raw'], 'committed')

    def test_blank_and_garbage(self):
        self.assertEqual(guard_clue({'answer': '', 'tier': 'committed'}, [4], None, None, None)['tier'], 'blank')
        self.assertEqual(guard_clue('not a dict', [4], None, None, None)['tier'], 'blank')
        e = guard_clue({'answer': 'זרע', 'tier': 'sure'}, [3], None, None, None)
        self.assertEqual(e['tier'], 'suggestion')


class RequestBody(unittest.TestCase):
    def test_structured_body_pins_sampling_and_routing(self):
        c = ORClient(model='m', api_key='k')
        b = c.body([{'role': 'user', 'content': 'x'}], CLUE_SCHEMA)
        self.assertEqual(b['temperature'], 0.0)
        self.assertEqual(b['seed'], 7)
        self.assertEqual(b['response_format']['type'], 'json_schema')
        self.assertTrue(b['response_format']['json_schema']['strict'])
        self.assertEqual(b['provider'], {'require_parameters': True})
        f = c.body([{'role': 'user', 'content': 'x'}], None, deterministic=False)
        self.assertNotIn('response_format', f)
        self.assertNotIn('temperature', f)


if __name__ == '__main__':
    unittest.main()
