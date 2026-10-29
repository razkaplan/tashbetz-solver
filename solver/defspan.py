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

STRUCTURAL CLASSIFIER (`split_structural`, 2026-10-25): the 2026-08-19 indicator-density
classifier scored 1/5 on the mechanically-locatable edge cases — worse than chance — because
most of this setter's clues carry NO indicator word at all (PLAYBOOK.md already notes the
anagram signal here is mechanical, not lexical). That run's own log named one untried,
fundamentally different signal rather than a retry of the same one: "scoring by whether each
end's residual is anagram-matchable". This is that signal. Instead of counting trigger words,
it asks candidates.py's own mechanism generators (anagram / hidden / reversal) whether a given
end's word-span, taken as fodder, actually PRODUCES a real Hebrew word of the exact target
length (the enum total — known at solve time, not a leak). A real definition phrase has no
particular reason to also happen to be a letter-rearrangement of a real word of that exact
length; the wordplay side does, by construction, for the correct hypothesis. This needs no
gold answer to run (target_len comes from the clue's own enum), so unlike `locate_fodder`
(a diagnostic that can only ever check a known answer) it is a real, usable classifier.

CLI:
  python3 solver/defspan.py stats [dataset] [split]   # measured fodder-position distribution
                                                       # + both classifiers' agreement
  python3 solver/defspan.py split "<clue text>"       # ranked hypotheses, indicator classifier
  python3 solver/defspan.py split_structural "<clue text>" <enum...>  # structural classifier
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
# structural classifier: does this end's residual actually PRODUCE a real word
# of the right length by a named mechanism, rather than merely carry a trigger word?
# ---------------------------------------------------------------------------
def structural_hits(words, target_len):
    """candidates.py's anagram/hidden/reversal generators, restricted to the text of
    these words only, searched for the exact target length. Returns the raw hit list
    (empty if this word-span cannot produce a real word of that length by any of the
    three mechanisms)."""
    if target_len <= 0 or not words:
        return []
    import candidates
    text = ' '.join(words)
    out = []
    out += candidates.anagram_candidates(text, target_len)
    out += candidates.hidden_candidates(text, target_len)
    out += candidates.reversal_candidates(text, target_len)
    return out


def score_structural(hyp, target_len):
    """wordplay-side structural hit count minus definition-side structural hit count.
    The wordplay side is EXPECTED to hit (that is what a mechanism does); the
    definition side hitting too is not disqualifying by itself (short common words
    anagram to other short common words by chance) but is weaker corroboration, so it
    counts against the hypothesis rather than for it. Tie-break: shorter wordplay span
    first (a tighter mechanical account is less likely to be a coincidence)."""
    wp_hits = structural_hits(hyp['wp_words'], target_len)
    def_hits = structural_hits(hyp['def_words'], target_len)
    return len(wp_hits) - len(def_hits), -len(hyp['wp_words']), wp_hits, def_hits


def split_structural(clue_text, enum, top_n=3):
    """Ranked (definition, wordplay) hypotheses by the structural signal. enum is the
    clue's own printed enumeration (list of ints) — known at solve time, not derived
    from the gold answer."""
    target_len = sum(enum) if enum else 0
    scored = []
    for hyp in hypotheses(clue_text):
        s, tiebreak, wp_hits, def_hits = score_structural(hyp, target_len)
        scored.append((s, tiebreak, hyp, wp_hits, def_hits))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for s, _, hyp, wp_hits, def_hits in scored[:top_n]:
        out.append({
            'definition': ' '.join(hyp['def_words']),
            'wordplay': ' '.join(hyp['wp_words']),
            'def_end': hyp['def_end'],
            'score': s,
            'wordplay_hits': wp_hits,
        })
    return out


def classifier_agrees_structural(clue_text, enum, bucket):
    """Same contract as classifier_agrees(), for the structural classifier. None when
    there is no top hypothesis with POSITIVE net evidence (score <= 0: no word-span
    structurally produced a real word of the target length, or the two ends tied) --
    abstaining is the honest answer when the mechanism found nothing, not a forced
    guess -- or the bucket is 'interior'/'whole_clue'."""
    if bucket not in ('start', 'end'):
        return None
    ranked = split_structural(clue_text, enum, top_n=1)
    if not ranked or ranked[0]['score'] <= 0:
        return None
    top = ranked[0]
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
    struct_correct = struct_total = 0
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
        sagree = classifier_agrees_structural(r['clue_text'], r.get('enum') or [], b)
        if sagree is not None:
            struct_total += 1
            struct_correct += sagree
        if len(examples) < 8:
            examples.append((r['clue_number'], r['direction'], b, loc['mechanism'], r['clue_text']))
    return {
        'total': total, 'located': located,
        'located_rate': located / total if total else 0.0,
        'position_buckets': dict(buckets),
        'by_mechanism': dict(by_mech),
        'examples': examples,
        'classifier_agreement': f'{clf_correct}/{clf_total}' if clf_total else 'n/a (no start/end cases)',
        'structural_classifier_agreement': f'{struct_correct}/{struct_total}' if struct_total else 'n/a (no start/end cases)',
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

    print('--- structural: a tail word-span that anagrams to the target length scores ' +
          'as wordplay, no indicator word involved ---')
    # 'קבר' (3 letters) anagrams to 'בקר'/'ברק'/'קרב'/'רקב', all real words -- a letter-
    # rearrangement device with zero trigger vocabulary, exactly the setter's own
    # documented pattern. 'אם' (2 letters) is shorter than the 3-letter target, so it
    # structurally CANNOT produce a window of that length -- the definition side is
    # guaranteed zero hits by construction, isolating the signal this test checks.
    os.chdir(ROOT)
    res = split_structural('אם קבר', [3])
    top = res[0]
    got = top['def_end'] == 'start' and 'קבר' in top['wordplay']
    print(f"  top hypothesis: def={top['definition']!r} wordplay={top['wordplay']!r} "
          f"hits={top['wordplay_hits']}")
    print(f'  wordplay landed on the anagram-bearing tail: {got} (expected True)')
    ok &= got

    print('--- structural: an all-zero-score clue returns hypotheses but no classifier claim ---')
    # No word-span here anagrams/hides/reverses to a real 4-letter word; the classifier
    # must not force a confident pick it has no structural evidence for.
    sagree = classifier_agrees_structural('קקקקק קקקקק', [4], 'start')
    print(f'  classifier_agrees_structural on an unsolvable clue: {sagree} '
          f'(expected None — no hypothesis scored above the null)')
    ok &= sagree is None

    print('--- structural_hits: needs no gold answer, only the enum total ---')
    hits = structural_hits(['קבר'], 3)
    print(f'  hits: {hits} (expected a nonempty anagram hit)')
    ok &= bool(hits)

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
    elif cmd == 'split_structural':
        enum = [int(x) for x in sys.argv[3:]]
        os.chdir(ROOT)
        for h in split_structural(sys.argv[2], enum):
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
        print('indicator-density classifier agreement (start/end cases only):',
              res['classifier_agreement'])
        print('structural classifier agreement (start/end cases only):',
              res['structural_classifier_agreement'])
        if res['examples']:
            print('\nexamples (clue_number, direction, position, mechanism, text):')
            for num, direction, b, mech, text in res['examples']:
                print(f'  {num} {direction} [{b}/{mech}]: {text}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
