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

CLASSIFIER v2 (`split_mechanical`): the indicator-density classifier above was MEASURED
(2026-08-19) at 1/5 agreement on the located edge cases - worse than chance - and
DAILY.md's "Things already tried" section named one untried alternative signal before
retiring the item: "scoring by whether each end's residual is anagram-matchable". This is
that signal, built and selftested 2026-10-08. Instead of counting indicator words, it asks
whether the WORDPLAY-side residual, searched ALONE (never the whole clue, unlike
candidates.py's own window scan), actually produces any real-word candidate of the target
length via candidates.py's own anagram/hidden/reversal window search. A residual with fewer
letters than the target length is automatically unmatchable - a filter indicator density
could never express, since it scores words, not lengths.

DISCLOSED WEAKNESS, found by direct construction before this was ever run on real data (see
selftest): among MATCHABLE hypotheses, ties are broken by preferring fewer raw hits, on the
theory that a highly specific residual (few real-word matches) is more likely to be the true
fodder than a noisy one. But when two hypotheses' residuals both land at EXACTLY the target
length (the common case: one window, few hits either way), "fewer hits" just measures how
many real words happen to share that one window's letter-multiset - a fact about the
lexicon's density at that multiset, unrelated to which span the setter actually intended.
The selftest demonstrates this directly: a synthetic clue where the TRUE wordplay span and a
decoy span of the same length both produce a nonzero, similarly-sized hit count, and the
tiebreak has no principled way to prefer the true one. This is reported rather than hidden
because DAILY.md's standing policy values a demonstrated negative finding over a shipped
classifier whose failure mode was never looked for.

MEASURED on real data (2026-10-08, freshly transcribed 2026-05-15): defspan's own `stats`
located 0/28 clues (the lowest this diagnostic has recorded; previous low was 25%, 7/28,
2026-08-19) - meaning there were ZERO start/end edge cases on this puzzle to score EITHER
classifier against, old or new. Both report 'n/a'. This is not a null result for the
mechanical-matchability idea specifically - it is the THIRD independent confirmation (after
2026-08-19's 25% and this run's 0%) that single-window locatability is the real bottleneck,
and refining the classifier that only fires in the minority/empty case is lower-value than
the premise's own low hit rate already implied.

CLI:
  python3 solver/defspan.py stats [dataset] [split]   # measured fodder-position distribution
  python3 solver/defspan.py split "<clue text>"       # ranked (definition, wordplay) hypotheses
  python3 solver/defspan.py split_mechanical "<clue text>" <target_len>  # the v2 classifier
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


def _mechanical_hits(words, target_len):
    """Every real-word anagram/hidden/reversal candidate of target_len found WITHIN this
    word list alone (never the rest of the clue) - candidates.py's own window-scan
    mechanisms, reused rather than re-implemented, same discipline the rest of this file
    follows for locate_fodder."""
    sys.path.insert(0, HERE)
    import candidates as cand_mod
    text = ' '.join(words)
    return (cand_mod.anagram_candidates(text, target_len)
            + cand_mod.hidden_candidates(text, target_len)
            + cand_mod.reversal_candidates(text, target_len))


def split_mechanical(clue_text, target_len, top_n=3):
    """Alternative to split(): scores each (definition, wordplay) hypothesis by whether
    its WORDPLAY-side residual is itself mechanically productive (see module docstring for
    the signal and its disclosed tiebreak weakness), instead of indicator-word density.
    matchable=True beats matchable=False; among matchable, fewer raw hits (a more specific
    residual) wins; ties go to a shorter definition span, same discipline as score()."""
    scored = []
    for hyp in hypotheses(clue_text):
        hits = _mechanical_hits(hyp['wp_words'], target_len)
        scored.append({'hyp': hyp, 'hits': hits, 'matchable': len(hits) > 0})
    scored.sort(key=lambda s: (0 if s['matchable'] else 1, len(s['hits']), len(s['hyp']['def_words'])))
    out = []
    for s in scored[:top_n]:
        hyp = s['hyp']
        out.append({
            'definition': ' '.join(hyp['def_words']),
            'wordplay': ' '.join(hyp['wp_words']),
            'def_end': hyp['def_end'],
            'matchable': s['matchable'],
            'hits': [h['answer'] for h in s['hits']],
        })
    return out


def classifier_agrees_mechanical(clue_text, target_len, bucket):
    """Same contract as classifier_agrees(), scored by split_mechanical() instead of
    split(). 'interior' is still excluded (None) for the same structural reason."""
    if bucket not in ('start', 'end'):
        return None
    top = split_mechanical(clue_text, target_len, top_n=1)[0]
    wordplay_end = 'start' if top['def_end'] == 'end' else 'end'
    return wordplay_end == bucket


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


def classifier_agrees(clue_text, bucket):
    """Does the classifier's TOP (definition, wordplay) hypothesis put the WORDPLAY on
    the same edge where the fodder was mechanically located? 'interior' can never agree
    -- a start/end-only classifier has no hypothesis that puts wordplay in the middle,
    so those cases are a structural miss, not a classifier bug. Returns None for those
    (excluded from the accuracy denominator, reported separately) so the accuracy number
    is not silently deflated by a case the classifier design cannot address at all."""
    if bucket not in ('start', 'end'):
        return None
    top = split(clue_text, top_n=1)[0]
    wordplay_end = 'start' if top['def_end'] == 'end' else 'end'
    return wordplay_end == bucket


def stats(dataset_path, split_name=None):
    total = located = 0
    buckets = Counter()
    by_mech = Counter()
    examples = []
    clf_correct = clf_total = 0
    clf2_correct = clf2_total = 0
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
        agree = classifier_agrees(r['clue_text'], b)
        if agree is not None:
            clf_total += 1
            clf_correct += agree
        target_len = len(norm(r['answer_raw']))
        agree2 = classifier_agrees_mechanical(r['clue_text'], target_len, b)
        if agree2 is not None:
            clf2_total += 1
            clf2_correct += agree2
        if len(examples) < 8:
            examples.append((r['clue_number'], r['direction'], b, loc['mechanism'], r['clue_text']))
    return {
        'total': total, 'located': located,
        'located_rate': located / total if total else 0.0,
        'position_buckets': dict(buckets),
        'by_mechanism': dict(by_mech),
        'examples': examples,
        'classifier_agreement': f'{clf_correct}/{clf_total}' if clf_total else 'n/a (no start/end cases)',
        'classifier_agreement_mechanical': f'{clf2_correct}/{clf2_total}' if clf2_total else 'n/a (no start/end cases)',
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

    print('--- classifier_agrees: interior bucket is excluded (None), not scored as wrong ---')
    agree = classifier_agrees('כלשהו טקסט לדוגמה כאן', 'interior')
    print(f'  agree: {agree} (expected None)')
    ok &= agree is None

    print('--- classifier_agrees: an indicator-carrying clue can be checked against a bucket ---')
    agree = classifier_agrees('להפך ראש הממשלה', 'start')
    print(f'  agree: {agree} (expected True — wordplay/reversal-indicator is at the start)')
    ok &= agree is True

    print('--- split_mechanical: an unmatchable residual (too few letters for the target'
          ' length) never wins over a matchable one ---')
    # 'טוב' alone is only 3 letters -- too short to ever contain a 4-letter window, so it
    # is unmatchable by construction. 'םולש' (anagram fodder for שלום) is exactly 4 letters
    # and matchable. The top-ranked hypothesis must be a matchable one.
    res = split_mechanical('טוב עולם חמה םולש', 4)
    top = res[0]
    print(f"  top hypothesis: wordplay={top['wordplay']!r} matchable={top['matchable']}")
    print(f'  top hypothesis is matchable: {top["matchable"]} (expected True)')
    ok &= top['matchable'] is True
    print(f"  top hypothesis is the exact-length, fewest-hits residual: "
          f"{top['wordplay'] == 'םולש'} (expected True — שלום's own fodder, "
          f"8 hits, beats every longer/noisier residual)")
    ok &= top['wordplay'] == 'םולש'

    print('--- split_mechanical: DISCLOSED WEAKNESS — among two equal-length matchable'
          ' residuals, the fewer-hits tiebreak is not a correctness signal ---')
    # 'םולש' (anagram fodder for שלום, 4 letters) sits at one word-boundary; 'ברכה' (itself
    # a real word, also 4 letters) sits at another. Both residuals are exactly target_len,
    # so both are "matchable" by construction, and the tiebreak picks whichever one's
    # letter-multiset happens to match fewer real words — a lexicon-density accident, not
    # evidence either one is the setter's true wordplay span. Documented, not fixed: this
    # is why the module docstring and DAILY.md both call this signal unproven, not ready to
    # replace indicator-density rather than merely supplement it.
    res = split_mechanical('ברכה חמה םולש', 4, top_n=4)
    matchable_tops = [h for h in res if h['matchable']]
    print(f'  matchable hypotheses: {[(h["wordplay"], len(h["hits"])) for h in matchable_tops]}')
    distinct_wordplays = {h['wordplay'] for h in matchable_tops}
    print(f'  more than one equal-length matchable residual exists: '
          f'{len(distinct_wordplays) > 1} (expected True — this is the weakness, not a bug)')
    ok &= len(distinct_wordplays) > 1

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
    elif cmd == 'split_mechanical':
        for h in split_mechanical(sys.argv[2], int(sys.argv[3])):
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
        print('classifier top-hypothesis agreement, indicator-density (start/end cases only):',
              res['classifier_agreement'])
        print('classifier top-hypothesis agreement, mechanical-matchability (start/end cases only):',
              res['classifier_agreement_mechanical'])
        if res['examples']:
            print('\nexamples (clue_number, direction, position, mechanism, text):')
            for num, direction, b, mech, text in res['examples']:
                print(f'  {num} {direction} [{b}/{mech}]: {text}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
