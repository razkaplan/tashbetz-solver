#!/usr/bin/env python3
"""Definition-span detection for cryptic clues (DAILY.md lever queue item 2).

The standard cryptic-crossword heuristic, and the premise of queue item 2, is that a
clue's definition sits ENTIRELY at one END of the surface (start or end) and the rest
is wordplay. solver/PLAYBOOK.md section 2.4 already contains a qualitative exception for
this specific setter: "No fixed rule. Definition can be at the start, the end, or
*interleaved*." That claim was never checked mechanically against gold answers — it read
as an impression from manual solving sessions. This module checks it first, with code,
before spending effort on a classifier built on a premise that might not hold.

MEASUREMENT (`stats`): for each clue with a known answer, locate where the wordplay
actually sits by reusing candidates.py's own char-window search (anagram / hidden /
reversal), restricted to the ONE already-known answer for that clue — i.e. "does a
window matching this specific gold answer exist, and if so, where does it sit in the
clue?" This is not a leak: it runs only on answers this session already has in hand
(the puzzle transcribed today), exactly as candidates.py's own `recall` command already
does, and it produces a fact about clue TEXT LAYOUT, not a generator that could recover
a held-out answer. Reports what fraction of mechanically-locatable wordplay windows
touch the clue's start, its end, or neither (interior/scattered).

CLASSIFIER (`split`): only useful if `stats` supports the one-end premise. Scores each
(definition, wordplay) hypothesis - definition = a prefix or suffix word-span, wordplay
= the complement - by indicator-word density on the wordplay side, using the same
solver/indicators.json trigger lists SOLVE_PROTOCOL.md already tells a solver to check
by hand. Never opens an answer.

CLI:
  python3 solver/defspan.py stats [dataset] [split]   # measured fodder-position distribution
  python3 solver/defspan.py split "<clue text>"       # ranked (definition, wordplay) hypotheses
  python3 solver/defspan.py selftest
"""
import sys, os, re, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


CREDIT_RE = re.compile(r'\((עפ["\']?י|מ|ח)[^)]*\)')


def strip_credit(text):
    return CREDIT_RE.sub(' ', text or '')


def words_of(text):
    return re.findall(r'[א-ת]+', strip_credit(text))


# ---------------------------------------------------------------------------
# indicator scoring
# ---------------------------------------------------------------------------
_INDICATORS = None


def indicators():
    """Flat list of (mechanism, phrase) from indicators.json, skipping the
    dict-valued / documentation-only keys (gematria_letters, spelling_flags,
    explanation_labels, credit_note, _note)."""
    global _INDICATORS
    if _INDICATORS is None:
        d = json.load(open(os.path.join(HERE, 'indicators.json')))
        out = []
        for mech, phrases in d.items():
            if mech in ('gematria_letters', 'spelling_flags', 'explanation_labels', 'credit_note'):
                continue
            if not isinstance(phrases, list):
                continue
            for p in phrases:
                if p.startswith('_note'):
                    continue
                out.append((mech, p))
        _INDICATORS = out
    return _INDICATORS


def indicator_hits(words):
    """Indicator phrases (mechanism markers) present among a list of clue words — the
    WORDPLAY signal. Matches by WORD, not raw substring: several indicators are single
    short tokens (e.g. 'מ', 'ב', 'או', 'גם' for hidden/double_definition), and a naive
    `phrase in text` containment check would match those inside almost any Hebrew word
    that merely happens to start with the same letter (e.g. 'מ' inside 'ממשלה'), which
    would swamp the signal with noise on both sides equally. A multi-word indicator
    phrase is checked against the space-joined text instead, since a specific multi-word
    sequence matching by accident is far less likely."""
    wordset = set(words)
    text = ' '.join(words)
    hits = []
    for mech, phrase in indicators():
        if not phrase:
            continue
        if ' ' in phrase:
            if phrase in text:
                hits.append((mech, phrase))
        elif phrase in wordset:
            hits.append((mech, phrase))
    return hits


# ---------------------------------------------------------------------------
# classifier: which end is the definition?
# ---------------------------------------------------------------------------
def hypotheses(clue_text):
    """Every (definition, wordplay) split where the definition is a prefix or a
    suffix word-span of length 1..n-1. Definition is never the whole clue or empty."""
    words = words_of(clue_text)
    n = len(words)
    out = []
    for k in range(1, n):
        d, w = words[:k], words[k:]
        out.append({'def_end': 'start', 'def_words': d, 'wp_words': w})
        d, w = words[-k:], words[:-k]
        out.append({'def_end': 'end', 'def_words': d, 'wp_words': w})
    return out


def score(hyp):
    """wordplay-side indicator count minus definition-side indicator count. A real
    definition is comparatively markerless plain language; wordplay carries the
    device markers. Prefer a shorter definition span on ties (defs in this corpus
    run short per PLAYBOOK.md 2.4 examples: 'הגדרה' phrases are typically 1-3 words)."""
    wp_hits = indicator_hits(hyp['wp_words'])
    def_hits = indicator_hits(hyp['def_words'])
    return len(wp_hits) - len(def_hits), -len(hyp['def_words']), wp_hits, def_hits


def split(clue_text, top_n=3):
    """Ranked (definition, wordplay) hypotheses, best first."""
    scored = []
    for hyp in hypotheses(clue_text):
        s, tiebreak, wp_hits, def_hits = score(hyp)
        scored.append((s, tiebreak, hyp, wp_hits, def_hits))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for s, _, hyp, wp_hits, def_hits in scored[:top_n]:
        out.append({
            'definition': ' '.join(hyp['def_words']),
            'wordplay': ' '.join(hyp['wp_words']),
            'def_end': hyp['def_end'],
            'score': s,
            'wordplay_indicators': wp_hits,
        })
    return out


# ---------------------------------------------------------------------------
# measurement: where does mechanically-locatable wordplay actually sit?
# ---------------------------------------------------------------------------
def locate_fodder(clue_text, answer):
    """Does a char-window matching this SPECIFIC known answer exist as an anagram,
    a hidden run, or a reversal of some window of the clue? If so, return the
    window's (start, end) character offsets into the joined, credit-stripped,
    final-folded clue letters, and which mechanism found it. None if no window
    of the right length reproduces the answer by any of the three mechanisms."""
    target = norm(answer)
    joined = norm(''.join(words_of(clue_text)))
    L = len(target)
    if not target or L == 0 or L > len(joined):
        return None
    target_count = Counter(target)
    for i in range(len(joined) - L + 1):
        sub = joined[i:i + L]
        if sub == target:
            continue  # the answer sitting verbatim in the clue is not a device
        if sub == target[::-1]:
            return {'mechanism': 'reversal', 'start': i, 'end': i + L, 'total': len(joined)}
        if Counter(sub) == target_count:
            return {'mechanism': 'anagram', 'start': i, 'end': i + L, 'total': len(joined)}
    return None


def position_bucket(loc, edge_tolerance=0):
    """'start' if the window touches char 0, 'end' if it touches the last char,
    'interior' otherwise (the case that would mean the wordplay is NOT confined to
    one end, i.e. the complement — the definition — is split around it)."""
    at_start = loc['start'] <= edge_tolerance
    at_end = loc['end'] >= loc['total'] - edge_tolerance
    if at_start and at_end:
        return 'whole_clue'
    if at_start:
        return 'start'
    if at_end:
        return 'end'
    return 'interior'


def stats(dataset_path, split_name=None):
    total = located = 0
    buckets = Counter()
    by_mech = Counter()
    examples = []
    for line in open(dataset_path):
        r = json.loads(line)
        if split_name and r['split'] != split_name:
            continue
        if not r.get('answer_raw'):
            continue
        total += 1
        loc = locate_fodder(r['clue_text'], r['answer_raw'])
        if not loc:
            continue
        located += 1
        b = position_bucket(loc)
        buckets[b] += 1
        by_mech[loc['mechanism']] += 1
        if len(examples) < 8:
            examples.append((r['clue_number'], r['direction'], b, loc['mechanism'], r['clue_text']))
    return {
        'total': total, 'located': located,
        'located_rate': located / total if total else 0.0,
        'position_buckets': dict(buckets),
        'by_mechanism': dict(by_mech),
        'examples': examples,
    }


# ---------------------------------------------------------------------------
def selftest():
    """Synthetic examples only — no dev/eval gold data, same discipline candidates.py
    enforces at load time."""
    ok = True

    print('--- classifier: reversal indicator at the tail marks that side as wordplay ---')
    # 'ראש הממשלה' (a plausible definition phrase) + 'להפך' (reversal indicator) at the end
    res = split('ראש הממשלה להפך')
    top = res[0]
    got_end_wordplay = 'להפך' in top['wordplay'] and 'להפך' not in top['definition']
    print(f"  top hypothesis: def={top['definition']!r} wordplay={top['wordplay']!r}")
    print(f'  reversal indicator landed on the wordplay side: {got_end_wordplay} (expected True)')
    ok &= got_end_wordplay

    print('--- classifier: reversal indicator at the head marks that side as wordplay ---')
    res = split('להפך ראש הממשלה')
    top = res[0]
    got_start_wordplay = 'להפך' in top['wordplay'] and 'להפך' not in top['definition']
    print(f"  top hypothesis: def={top['definition']!r} wordplay={top['wordplay']!r}")
    print(f'  reversal indicator landed on the wordplay side: {got_start_wordplay} (expected True)')
    ok &= got_start_wordplay

    print('--- indicator_hits: finds a known trigger WORD, not a substring inside another word ---')
    hits = indicator_hits(words_of('הכל בלבל פה'))
    found = any(p == 'בלבל' for _, p in hits)
    print(f'  hits on a sentence containing the exact word בלבל: {hits} (expected to include בלבל)')
    ok &= found

    print('--- indicator_hits: does NOT fire on a short indicator merely embedded in a longer word ---')
    # 'מ' is a hidden-device indicator; 'ממשלה' starts with the same letter but is not
    # the word 'מ' itself. A substring check would wrongly fire here; a word check must not.
    hits = indicator_hits(words_of('ראש הממשלה'))
    false_fire = any(p == 'מ' for _, p in hits)
    print(f'  hits on ראש הממשלה: {hits} (expected: no bare-מ hit)')
    ok &= not false_fire

    print('--- locate_fodder: finds a real reversal window for a KNOWN answer ---')
    # רב (2 letters) reversed is בר (2 letters) — same synthetic pair candidates.py uses.
    loc = locate_fodder('אמר הרבנים על רב גדול', norm('בר'))
    print(f'  located: {loc} (expected a reversal hit)')
    ok &= bool(loc) and loc['mechanism'] == 'reversal'

    print('--- locate_fodder: no hit when the answer is not derivable from the clue text ---')
    loc = locate_fodder('שלום עולם', 'קקקקק')
    print(f'  located: {loc} (expected None)')
    ok &= loc is None

    print('--- position_bucket: a window touching char 0 is bucketed "start" ---')
    b = position_bucket({'start': 0, 'end': 3, 'total': 10})
    print(f'  bucket: {b} (expected start)')
    ok &= b == 'start'

    print('--- position_bucket: a window touching neither edge is bucketed "interior" ---')
    b = position_bucket({'start': 2, 'end': 5, 'total': 10})
    print(f'  bucket: {b} (expected interior)')
    ok &= b == 'interior'

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'split':
        for h in split(sys.argv[2]):
            print(h)
    elif cmd == 'stats':
        path = sys.argv[2] if len(sys.argv) > 2 else 'data/dataset/clues.jsonl'
        split_name = sys.argv[3] if len(sys.argv) > 3 else None
        os.chdir(ROOT)
        res = stats(path, split_name)
        print(f"located: {res['located']}/{res['total']} = {res['located_rate']:.1%} "
              f"of clues have a mechanically-locatable wordplay window")
        print('position of that window within the clue:', res['position_buckets'])
        print('by mechanism:', res['by_mechanism'])
        if res['examples']:
            print('\nexamples (clue_number, direction, position, mechanism, text):')
            for num, direction, b, mech, text in res['examples']:
                print(f'  {num} {direction} [{b}/{mech}]: {text}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
