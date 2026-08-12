#!/usr/bin/env python3
"""Mechanical candidate generation for cryptic clues.

WHY: the measured bottleneck (RESULTS.md, DAILY.md) is not verification — the proof
gate (prove.py) is airtight once it has something to check. The bottleneck is that a
solver produces ONE candidate and tries to justify it. That is backwards: a cryptic
clue's wordplay is mechanical (anagram/hidden/reversal/charade), so a machine should
enumerate every candidate a mechanism can produce and hand the LIST to the proof gate,
rather than have the solver guess once and rationalize.

This module does exactly that, per clue, with no LLM involved:
  - anagram_candidates:  every contiguous word-window whose letter count matches the
                          enum total, checked against the lexicon for real-word anagrams.
  - hidden_candidates:   a contiguous run inside the space-removed clue that is itself
                          a real word (the "hidden word" device).
  - reversal_candidates: same search, reversed.
  - pattern_candidates:  wraps lexicon.py's crossing-pattern lookup, for when grid
                          letters are already known.
  - split_candidates:    for multi-part enums (e.g. (5,2)), splits a hit at the enum
                          boundary and flags whether BOTH pieces are real words — the
                          precondition prove.py's word_order() needs to succeed.

Each of the three window devices (anagram/hidden/reversal) also runs against
SUBSTITUTION VARIANTS of the clue text (substitution_variants(), backed by
solver/substitutions.py's 3,141 mined equivalences): one clue word at a time is
replaced by a recorded equivalent fragment before the window search runs, tagged
with mechanism '<device>+sub' and a `substitution` provenance note. This was the
explicit next step in DAILY.md after the first candidates.py measurement (3.6%
recall, 2026-08-06): a purely literal-text search cannot reach fodder that only
exists once a clue word is read through the setter's own substitution vocabulary
(SOLVE_PROTOCOL v14's "one word of the surface does nothing" failure mode).

None of this asserts an answer is CORRECT — it only asserts an answer is POSSIBLE by a
named mechanism. Selecting among candidates and proving one is still prove.py's job.
Held-out dev/eval answers are excluded from the lexicon by lexicon.held_out_answers(),
so this generator cannot recover a dev/eval gold answer by looking it up — only by
actually deriving it mechanically, same discipline as the rest of the solver.

CLI:
  python3 solver/candidates.py clue "<text>" <enum...>            # e.g. ... "7,2"
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval   # offline recall@N
  python3 solver/candidates.py selftest
"""
import sys, os, re, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


_LEX = None


def lex():
    global _LEX
    if _LEX is None:
        sys.path.insert(0, HERE)
        import lexicon
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            _LEX = lexicon.load()
        finally:
            os.chdir(cwd)
    return _LEX


# (עפ"י ...) contributor credits and (מ)/(ח) spelling flags are not wordplay letters.
CREDIT_RE = re.compile(r'\((עפ["\']?י|מ|ח)[^)]*\)')


def strip_credit(text):
    return CREDIT_RE.sub(' ', text or '')


def words_of(text):
    return re.findall(r'[א-ת]+', strip_credit(text))


def joined_letters(clue_text):
    """The clue's letters, credit-stripped, spaces removed, finals folded."""
    return norm(''.join(words_of(clue_text)))


_SUB = None


def subs():
    """The setter's mined substitution vocabulary (solver/substitutions.py),
    3,141 clue-fragment -> answer-fragment equivalences read off 11,931 crowd
    explanations. Loaded lazily and cached, same pattern as lex()."""
    global _SUB
    if _SUB is None:
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUB = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUB


def substitution_variants(clue_text, max_per_word=3):
    """Yield (variant_letters, note) for every recorded substitution of a single
    clue word. SOLVE_PROTOCOL v14: 39% of clue words in this genre have one, and
    the commonest failure mode noted there is "one word of the surface does
    nothing" — that leftover word is usually standing in for a differently-spelled
    fragment. The literal clue text alone cannot supply that fragment's letters to
    the anagram/hidden/reversal window search; substituting it in, one word at a
    time, can. This is ADDITIVE to literal-text search, not a replacement — most
    clue words have no recorded substitution and the literal search still runs."""
    ws = words_of(clue_text)
    s = subs()
    out = []
    for i, w in enumerate(ws):
        nw = norm(w)
        for b, _n in s['fwd'].get(nw, [])[:max_per_word]:
            new_ws = list(ws)
            new_ws[i] = b
            out.append((norm(''.join(new_ws)), f'{nw}~{norm(b)}'))
    return out


def _windows(text, target_len):
    """Every target_len-character run of `text`, WITHOUT requiring word alignment.
    Setters routinely use partial-word fodder (e.g. dropping a trailing possessive
    vav), so a window restricted to whole-word boundaries misses real fodder —
    measured: it missed the worked example in SOLVE_PROTOCOL.md itself ('משפר חיי'
    is 'משפר' plus the first 3 of 4 letters of 'חייו')."""
    for i in range(len(text) - target_len + 1):
        yield text[i:i + target_len]


def _anagram_hits(text, target_len, mechanism, note=None):
    out = []
    for sub in _windows(text, target_len):
        for hit in anagram_lookup(sub, target_len):
            if hit == sub:
                continue  # not a rearrangement, just the fodder itself
            c = {'answer': hit, 'mechanism': mechanism, 'fodder': sub}
            if note:
                c['substitution'] = note
            out.append(c)
    return out


def _hidden_hits(text, target_len, mechanism, note=None):
    words = lex()
    out = []
    for sub in _windows(text, target_len):
        if sub in words:
            c = {'answer': sub, 'mechanism': mechanism, 'fodder': sub}
            if note:
                c['substitution'] = note
            out.append(c)
    return out


def _reversal_hits(text, target_len, mechanism, note=None):
    words = lex()
    out = []
    for sub in _windows(text, target_len):
        rev = sub[::-1]
        if rev in words:
            c = {'answer': rev, 'mechanism': mechanism, 'fodder': sub}
            if note:
                c['substitution'] = note
            out.append(c)
    return out


_BY_LEN = None


def by_len():
    """Lexicon indexed by word length. anagram_candidates does a Counter-equality
    scan per window; without this index every window rescans the full ~140k-word
    lexicon, which is what made character-level scanning (below) too slow to run."""
    global _BY_LEN
    if _BY_LEN is None:
        d = {}
        for w in lex():
            d.setdefault(len(w), []).append(w)
        _BY_LEN = d
    return _BY_LEN


def anagram_lookup(letters, target_len):
    target = Counter(letters)
    return [w for w in by_len().get(target_len, []) if Counter(w) == target]


def anagram_candidates(clue_text, target_len):
    out = _anagram_hits(joined_letters(clue_text), target_len, 'anagram')
    for variant, note in substitution_variants(clue_text):
        out += _anagram_hits(variant, target_len, 'anagram+sub', note)
    return out


def hidden_candidates(clue_text, target_len):
    out = _hidden_hits(joined_letters(clue_text), target_len, 'hidden')
    for variant, note in substitution_variants(clue_text):
        out += _hidden_hits(variant, target_len, 'hidden+sub', note)
    return out


def reversal_candidates(clue_text, target_len):
    out = _reversal_hits(joined_letters(clue_text), target_len, 'reversal')
    for variant, note in substitution_variants(clue_text):
        out += _reversal_hits(variant, target_len, 'reversal+sub', note)
    return out


def pattern_candidates(pattern):
    """pattern like '?ו?ר??' — '?' or '_' = unknown crossing letter. The lexicon folds
    final letters (ם/ן/ץ/ף/ך -> מ/נ/צ/פ/כ) everywhere, so fixed cells must be folded
    the same way before matching or a pattern ending in a final letter never hits."""
    words = lex()
    cells = [c for c in pattern if c != ' ']
    L = len(cells)
    rx = re.compile('^' + ''.join('.' if c in '?_' else c.translate(FIN) for c in cells) + '$')
    return [{'answer': w, 'mechanism': 'pattern', 'fodder': pattern}
            for w in words if len(w) == L and rx.match(w)]


def split_candidates(cands, enum):
    """Multi-part enum: split each hit at the enum boundary, flag if both pieces
    are real words (the precondition for prove.py's word_order to succeed)."""
    if len(enum) < 2:
        for c in cands:
            c['split'] = None
        return cands
    words = lex()
    out = []
    for c in cands:
        a = c['answer']
        i, pieces, ok = 0, [], True
        for n in enum:
            p = a[i:i + n]
            if len(p) > 1 and p not in words:
                ok = False
            pieces.append(p)
            i += n
        c = dict(c)
        c['split'] = pieces if ok else None
        out.append(c)
    return out


def generate(clue_text, enum, pattern=None, max_n=25):
    """Diverse candidates for one clue. Never consults the answer."""
    target_len = sum(enum)
    cands = []
    cands += anagram_candidates(clue_text, target_len)
    cands += hidden_candidates(clue_text, target_len)
    cands += reversal_candidates(clue_text, target_len)
    if pattern:
        cands += pattern_candidates(pattern)

    seen, uniq = set(), []
    for c in cands:
        key = (c['answer'], c['mechanism'], c.get('fodder'))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    uniq = split_candidates(uniq, enum)
    return uniq[:max_n]


# ---------------------------------------------------------------------------
# offline evaluation: recall@N — does the correct answer ever appear in the
# generated list? This is the honest metric for a candidate generator in
# isolation, BEFORE it is wired into a live solve+proof loop (which is a
# separate integration step, not done by this lever).
# ---------------------------------------------------------------------------
def recall_eval(dataset_path, split=None, max_n=25):
    total = 0
    hit = 0
    by_mech = Counter()
    sizes = []
    misses = []
    for line in open(dataset_path):
        r = json.loads(line)
        if split and r['split'] != split:
            continue
        if not r.get('answer_raw'):
            continue
        total += 1
        cands = generate(r['clue_text'], r['enum'], max_n=max_n)
        sizes.append(len(cands))
        gold = norm(r['answer_raw'])
        found = [c for c in cands if c['answer'] == gold]
        if found:
            hit += 1
            by_mech[found[0]['mechanism']] += 1
        else:
            misses.append((r['clue_number'], r['direction'], r['clue_text'], gold))
    return {
        'total': total, 'hit': hit,
        'recall': hit / total if total else 0.0,
        'avg_candidates': sum(sizes) / len(sizes) if sizes else 0.0,
        'by_mechanism': dict(by_mech),
        'misses': misses,
    }


# ---------------------------------------------------------------------------
def selftest():
    """Unit-level checks on synthetic examples — independent of any puzzle's gold
    data, so this file never embeds a dev/eval answer (same discipline lexicon.py
    enforces at load time)."""
    ok = True

    # anagram: every real-word anagram of a clue window is a candidate. 'שלום' (4)
    # is a real word; scrambled in the clue as 'םולש' it should still be found by
    # rearranging the letters of the (nonsense) fodder word 'םולש'.
    print('--- anagram device: scrambled fodder recovers the real word ---')
    cands = anagram_candidates('הביטו אל םולש עכשיו', 4)
    found = any(h['answer'] == norm('שלום') for h in cands)
    print(f'  found שלום as an anagram of םולש: {found} (expected True)')
    ok &= found

    print('--- hidden device: finds a real word hiding across a word boundary ---')
    # עברית (5 letters) hides across the join of 'קרא' + 'עב' ... use a run that
    # is NOT a clue word by itself: 'קרעב' + 'ריתו' -> slide window finds עברית only
    # via the concatenation, not because עברית is a standalone word in the clue.
    text = 'זה נק ראע ברית ולא אחרת'
    hits = hidden_candidates(text, 5)
    found = any(h['answer'] == norm('עברית') for h in hits)
    print(f'  found עברית as a hidden word: {found} (expected True)')
    ok &= found

    print('--- reversal device: a real word read backwards ---')
    # רב (2, a standalone clue word) reversed is בר (2), also a real word.
    hits = reversal_candidates('אמר הרבנים על רב גדול', 2)
    found = any(h['answer'] == norm('בר') for h in hits)
    print(f'  found בר as a reversal of רב: {found} (expected True)')
    ok &= found

    print('--- substitution-augmented anagram: fodder only closes through a mined equivalence ---')
    # 'משהו' stands for the (synthetic, monkeypatched) fragment 'םלוש', which
    # anagrams to שלום. The literal clue text has no fodder that anagrams to
    # שלום; only the substitution-expanded text does.
    global _SUB
    saved_sub = _SUB
    _SUB = {'fwd': {norm('משהו'): [[norm('םלוש'), 9]]}, 'rev': {}}
    try:
        text = 'ראה משהו יפה עכשיו'
        literal_hit = any(h['answer'] == norm('שלום')
                           for h in _anagram_hits(joined_letters(text), 4, 'anagram'))
        sub_hits = [h for h in anagram_candidates(text, 4) if h['mechanism'] == 'anagram+sub']
        found = any(h['answer'] == norm('שלום') for h in sub_hits)
        print(f'  literal text alone finds שלום: {literal_hit} (expected False)')
        print(f'  substitution-augmented search finds שלום: {found} (expected True)')
        ok &= (not literal_hit) and found
    finally:
        _SUB = saved_sub

    print('--- pattern device: crossing-pattern lookup wraps lexicon.pattern ---')
    hits = pattern_candidates('של?ם')
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום matching pattern של?ם: {found} (expected True)')
    ok &= found

    print('--- split_candidates: flags whether a multi-part answer is two real words ---')
    split = split_candidates([{'answer': norm('שלוםעליכם'), 'mechanism': 'test'}], [4, 5])
    print(f'  split result: {split[0]["split"]} (expected two real words, not None)')
    ok &= split[0]['split'] is not None

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'clue':
        text = sys.argv[2]
        enum = [int(x) for x in sys.argv[3].split(',')]
        for c in generate(text, enum):
            print(c)
    elif cmd == 'recall':
        path = sys.argv[2] if len(sys.argv) > 2 else 'data/dataset/clues.jsonl'
        split = sys.argv[3] if len(sys.argv) > 3 else None
        os.chdir(ROOT)
        res = recall_eval(path, split)
        print(f"recall@N: {res['hit']}/{res['total']} = {res['recall']:.1%}  "
              f"(avg {res['avg_candidates']:.1f} candidates/clue)")
        print('hits by mechanism:', res['by_mechanism'])
        if res['misses']:
            print(f"\n{len(res['misses'])} misses (clue_number, direction, gold):")
            for num, direction, text, gold in res['misses']:
                print(f'  {num} {direction}: {gold}  <-  {text}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
