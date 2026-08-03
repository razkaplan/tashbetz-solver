#!/usr/bin/env python3
"""Candidate generation — propose N answers per clue instead of one.

WHY (measured, DAILY.md log 2026-07-28): the proof gate (prove.py) has nothing to
filter because upstream produces a single guess and tries to justify it. Two runs on
the same puzzle each got 12/28 right but only 5 the SAME 12 (RESULTS.md v8) — the
correct answer is very often *findable* mechanically, just not the one thing a single
greedy pass happened to propose. This module inverts that: for a clue + its enumeration,
independently scan for every mechanically-defensible candidate by mechanism, dedupe, and
hand the pool to prove.py / a human pass to pick from. It does not decide anything itself
and it is blind — it never sees the gold answer, only clue text + a target length.

Two mechanisms, chosen because they are exactly the ones prove.py can verify with zero
ambiguity (is_anagram, is_hidden) and need no synonym knowledge to PROPOSE, only to
recognize a real word once assembled:

  anagram-window : every contiguous run of clue words whose letter count equals the
                    target; if some real lexicon word/phrase is an anagram of that run,
                    it is a candidate. (Mirrors PLAYBOOK.md's own empirical finding that
                    this mechanical check has ~85% recall / ~0.5% false positive rate on
                    the anagram class.)
  hidden-run      : every contiguous run of `target` letters in the space-free clue text;
                    real-word runs are candidates for the hidden-word mechanism.

Both are cheap, exhaustive, and precision-checked only by "is this string a real word" —
which is why they are candidates, not commitments. A container/charade generator needs
synonym knowledge (what a clue word can STAND FOR) to be more than a blind substring
search over an 11-word clue, and is left for a follow-up lever rather than bolted on
half-working here.

CLI:
  python3 solver/candidates.py gen "<clue text>" <total_len>
  python3 solver/candidates.py selftest
"""
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


def tokenize(clue_text):
    """Strip parenthetical enum/credit asides and punctuation, return normalized words."""
    text = re.sub(r'\([^)]*\)', ' ', clue_text or '')
    text = re.sub(r'[?׳\'"“”.,]', ' ', text)
    return [norm(w) for w in text.split() if norm(w)]


_LEX = None


def lex():
    """Lazy-load the shared lexicon (hspell + corpus + culture), held-out answers
    already excluded — see lexicon.held_out_answers(). Chdir to ROOT because
    lexicon.load() reads paths relative to the repo root."""
    global _LEX
    if _LEX is None:
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            sys.path.insert(0, HERE)
            import lexicon
            _LEX = lexicon.load()
        except Exception:
            _LEX = {}
        finally:
            os.chdir(cwd)
    return _LEX


def gen_anagram(clue_text, target_len, words=None):
    """Every contiguous run of clue words whose combined letter count == target_len;
    yield every real lexicon word/phrase that is a letter-for-letter anagram of it."""
    words = tokenize(clue_text) if words is None else words
    L = lex()
    out, seen = [], set()
    n = len(words)
    for i in range(n):
        acc = ''
        for j in range(i, n):
            acc += words[j]
            if len(acc) > target_len:
                break
            if len(acc) == target_len:
                cnt = Counter(acc)
                for w in L:
                    if len(w) == target_len and w != acc and w not in seen and Counter(w) == cnt:
                        seen.add(w)
                        out.append({'answer': w, 'mechanism': 'anagram',
                                    'fodder': ' '.join(words[i:j + 1])})
    return out


def gen_hidden(clue_text, target_len, words=None):
    """Every contiguous run of target_len letters in the space-free clue text that is
    itself a real word — the hidden-word mechanism (רצף אותיות)."""
    words = tokenize(clue_text) if words is None else words
    joined = ''.join(words)
    L = lex()
    out, seen = [], set()
    for i in range(len(joined) - target_len + 1):
        cand = joined[i:i + target_len]
        if cand in L and cand not in seen:
            seen.add(cand)
            out.append({'answer': cand, 'mechanism': 'hidden', 'fodder': joined})
    return out


def generate(clue_text, total_len):
    """Run every generator, dedupe by answer (keep first mechanism tag), return the pool."""
    words = tokenize(clue_text)
    pool, seen = [], set()
    for cand in gen_anagram(clue_text, total_len, words) + gen_hidden(clue_text, total_len, words):
        if cand['answer'] not in seen:
            seen.add(cand['answer'])
            pool.append(cand)
    return pool


def selftest():
    cases_ok = 0
    total = 0

    def check(label, clue, total_len, expect):
        nonlocal cases_ok, total
        total += 1
        pool = generate(clue, total_len)
        answers = [c['answer'] for c in pool]
        ok = expect in answers
        cases_ok += ok
        print(f'{"OK " if ok else "FAIL"} {label}: pool={answers[:8]}'
              f'{"..." if len(answers) > 8 else ""} (n={len(answers)}) expect={expect}')

    print('--- anagram: a synthetic case with an unrelated distractor word present ---')
    check('anagram ignores words outside the matching window',
          'כלבים מלוש בגינה', 4, norm('שלום'))  # מלוש is a scrambled שלום; כלבים/בגינה are noise

    print('\n--- hidden: answer spans a word boundary ---')
    check('hidden run inside a longer phrase',
          'טיפוס על הר גבוה מאוד', 3, 'יפו')  # ט(יפו)ס

    print('\n--- anti-leak interaction: EXPECTED absence, not a bug ---')
    print('The real clue this module was designed against is 2026-05-29 7a:')
    print('  "איך מוני אמריליו משפר חיי?" (7) -> ישפרחימ, anagram of משפר חיי (prove.py\'s own worked example).')
    real_pool = [c['answer'] for c in generate('איך מוני אמריליו משפר חיי?', 7)]
    leaked = 'ישפרחימ' in real_pool
    print(f'  pool blind from clue text alone: {real_pool}')
    print(f'  gold answer present: {leaked} (expected False -- this puzzle is now data/dataset '
          f'dev-split gold, so lexicon.held_out_answers() correctly hides it, same guard that '
          f'caught the 2026-07-21 leak. A generator that found it here would be regenerating the leak.)')
    total += 1
    cases_ok += (not leaked)
    print(f'  {"OK " if not leaked else "FAIL"}: held out as required')
    print('  (note: the window "משפר חיי" -> ישפרחימ is a 2-word PHRASE, not an hspell single-word '
          'entry, so once held out it has no other route into the lexicon -- a real limitation of '
          'anagram-realness-checking against a single-word dictionary, not just the leak guard.)')

    print(f'\n{cases_ok}/{total} selftest cases behaved as expected')
    return cases_ok == total


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 2 and sys.argv[1] == 'gen':
        pool = generate(sys.argv[2], int(sys.argv[3]))
        for c in pool:
            print(f"{c['answer']}\t{c['mechanism']}\t{c['fodder']}")
        if not pool:
            print('(empty pool)')
    else:
        print(__doc__)
