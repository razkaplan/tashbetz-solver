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
  - substitution_candidates: the setter's private-vocabulary device — a clue word (or two
                          adjacent ones) substituted for a fragment mined from crowd
                          explanations (solver/substitutions.py), when the substitute(s)
                          cover the FULL answer length. Rebuilt in-memory with held-out
                          clues excluded (see sub_fwd()) rather than trusting the
                          committed lex/substitutions.json, which predates that exclusion.
  - homograph_candidates: the setter's signature device — a clue word already has another
                          sense (lex/ambiguities.json) that matches the enum length, so it
                          IS the answer undisguised. Cannot invent an answer that isn't
                          already a literal clue substring.
  - pattern_candidates:  wraps lexicon.py's crossing-pattern lookup, for when grid
                          letters are already known.
  - split_candidates:    for multi-part enums (e.g. (5,2)), splits a hit at the enum
                          boundary and flags whether BOTH pieces are real words — the
                          precondition prove.py's word_order() needs to succeed.

None of this asserts an answer is CORRECT — it only asserts an answer is POSSIBLE by a
named mechanism. Selecting among candidates and proving one is still prove.py's job.
Held-out dev/eval answers are excluded from the lexicon by lexicon.held_out_answers(),
and (for substitution_candidates) from the mined equivalence table by
substitutions.held_out(), so this generator cannot recover a dev/eval gold answer by
looking it up — only by actually deriving it mechanically, same discipline as the rest
of the solver.

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


def _char_windows(clue_text, target_len):
    """Every target_len-character run of the clue's letters, WITHOUT requiring word
    alignment. Setters routinely use partial-word fodder (e.g. dropping a trailing
    possessive vav), so a window restricted to whole-word boundaries misses real
    fodder — measured: it missed the worked example in SOLVE_PROTOCOL.md itself
    ('משפר חיי' is 'משפר' plus the first 3 of 4 letters of 'חייו')."""
    joined = joined_letters(clue_text)
    for i in range(len(joined) - target_len + 1):
        yield joined[i:i + target_len]


def anagram_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        for hit in anagram_lookup(sub, target_len):
            if hit == sub:
                continue  # not a rearrangement, just the fodder itself (that's `hidden`)
            out.append({'answer': hit, 'mechanism': 'anagram', 'fodder': sub})
    return out


def hidden_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        if sub in words:
            out.append({'answer': sub, 'mechanism': 'hidden', 'fodder': sub})
    return out


def reversal_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        rev = sub[::-1]
        if rev in words:
            out.append({'answer': rev, 'mechanism': 'reversal', 'fodder': sub})
    return out


_SUB_FWD = None


def sub_fwd():
    """Clue-word -> answer-fragment equivalences, rebuilt IN-MEMORY from the currently
    available corpus with held-out (dev/eval) clues excluded (substitutions.held_out()).
    Deliberately does NOT load the committed solver/lex/substitutions.json: that file was
    built at an earlier date, from a corpus mix that likely included dev/eval puzzles'
    own crowd explanations, without this exclusion — using it here would risk crediting a
    substitution pair with 'solving' the very clue its own explanation was mined from,
    the same leak shape RESULTS.md's INTEGRITY FINDING already caught once via lexicon.py.
    In-memory rebuild costs a few hundred ms and is the only way to make this mechanism
    honestly measurable."""
    global _SUB_FWD
    if _SUB_FWD is None:
        sys.path.insert(0, HERE)
        import substitutions
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            pairs = substitutions.mine(substitutions.explanations())
        finally:
            os.chdir(cwd)
        fwd = {}
        for (a, b), n in pairs.items():
            fwd.setdefault(a, []).append((b, n))
        for k in fwd:
            fwd[k].sort(key=lambda x: -x[1])
        _SUB_FWD = fwd
    return _SUB_FWD


def substitution_candidates(clue_text, target_len, table=None):
    """The setter's private-vocabulary device (SOLVE_PROTOCOL.md 'Substitutions'): a clue
    word stands in for a fragment mined from crowd explanations (a name completed by a
    surname, an abbreviation, a gloss). Two shapes:
      (a) one clue word's substitute already has the FULL target length -- propose it
          directly, filtered to real words/names (lex()) to cut noise;
      (b) two ADJACENT clue words' substitutes concatenate, in clue order, to the full
          target length -- a tightly scoped two-part charade. Deliberately NOT the
          open-ended every-enum-split search charade.py already tried and measured weak
          (2.8% recall, DAILY.md 2026-08-08): unrestricted part search over a sparse table
          combinatorially explodes false positives. Adjacency + full-length coverage keeps
          this mechanism precise instead.
    `table` is injectable (tests / callers) instead of always hitting sub_fwd()."""
    fwd = table if table is not None else sub_fwd()
    words = lex()
    ws = words_of(clue_text)
    subs_of = lambda w: [b for b, n in fwd.get(norm(w), [])]
    out = []
    for w in ws:
        for b in subs_of(w):
            if len(b) == target_len and b in words:
                out.append({'answer': b, 'mechanism': 'substitution', 'fodder': w})
    for i in range(len(ws) - 1):
        for b1 in subs_of(ws[i]):
            for b2 in subs_of(ws[i + 1]):
                joined = b1 + b2
                if len(joined) == target_len and joined in words:
                    out.append({'answer': joined, 'mechanism': 'substitution',
                                'fodder': f'{ws[i]}+{ws[i + 1]}'})
    return out


_AMBIG = None


def ambiguities():
    global _AMBIG
    if _AMBIG is None:
        p = os.path.join(HERE, 'lex/ambiguities.json')
        _AMBIG = json.load(open(p)) if os.path.exists(p) else {}
    return _AMBIG


HOMO_PREFIXES = ['ו', 'ה', 'ב', 'ל', 'מ', 'ש', 'כ', 'וה', 'ול', 'וב', 'שה', 'מה', 'כש', 'לה', 'בה']
HOMO_SUFFIXES = ['ים', 'ות', 'י', 'ה', 'ו', 'ת', 'נו', 'כם', 'יו']


def _destem(w):
    """A clue word may carry a prefix/suffix the ambiguous STEM does not (mirrors
    homographs.py's variants(), duplicated rather than imported so this mechanism stays
    self-contained and independently testable)."""
    out = {w}
    for p in HOMO_PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 2:
            out.add(w[len(p):])
    for s in HOMO_SUFFIXES:
        if w.endswith(s) and len(w) - len(s) >= 2:
            out.add(w[:-len(s)])
    return out


def homograph_candidates(clue_text, target_len, idx=None):
    """The setter's signature device (PLAYBOOK.md / SOLVE_PROTOCOL.md 'Homographs'): a
    word already sitting in the clue, read in its OTHER sense, simply IS the answer -- no
    letter manipulation, just a second meaning (שרה = she sings / a minister / Sarah).
    Any clue token (or its de-affixed stem) that is a recorded ambiguity in
    lex/ambiguities.json and matches the enum length exactly is a candidate. Because the
    candidate is always a literal substring of the clue text itself, this cannot leak a
    held-out answer that ISN'T already sitting undisguised in the clue -- the same
    no-invention guarantee hidden_candidates has.
    `idx` is injectable (tests / callers) instead of always hitting ambiguities()."""
    table = idx if idx is not None else ambiguities()
    out = []
    for w in words_of(clue_text):
        nw = norm(w)
        for stem in _destem(nw):
            if len(stem) == target_len and stem in table:
                out.append({'answer': stem, 'mechanism': 'homograph', 'fodder': w})
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
    """Diverse candidates for one clue. Never consults the answer.

    Mechanism order here is a PRIORITY order, not just an accumulation order: dedup +
    the max_n cap keep a prefix of whichever list is built first, so whatever is listed
    first survives truncation. Measured bug (2026-08-20): with substitution/homograph
    appended last, a character-level anagram/hidden window scan alone routinely produces
    40-50+ raw hits on a short target length (lots of short real words exist), crowding
    every substitution/homograph candidate for that clue out of the top max_n before the
    proof gate — or a recall eval — ever sees them, even when they were found. Homograph
    and substitution are comparatively RARE and higher-precision (a token already sitting
    in the clue, or a mined equivalence, either fires or it doesn't — there's no
    combinatorial window scan inflating their count), so they go first; the cheap,
    high-volume window-scan mechanisms fill whatever budget is left."""
    target_len = sum(enum)
    cands = []
    cands += homograph_candidates(clue_text, target_len)
    cands += substitution_candidates(clue_text, target_len)
    if pattern:
        cands += pattern_candidates(pattern)
    cands += anagram_candidates(clue_text, target_len)
    cands += hidden_candidates(clue_text, target_len)
    cands += reversal_candidates(clue_text, target_len)

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

    print('--- pattern device: crossing-pattern lookup wraps lexicon.pattern ---')
    hits = pattern_candidates('של?ם')
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום matching pattern של?ם: {found} (expected True)')
    ok &= found

    print('--- substitution device: one clue word\'s mined substitute covers the full length ---')
    # injected table, independent of the live corpus — same discipline as the mechanical
    # tests above, and it also means this check cannot pass by accidentally hitting a
    # held-out answer: the table is synthetic, not sub_fwd()'s corpus rebuild.
    sub_table = {norm('טרמפ'): [(norm('שלום'), 5)]}
    hits = substitution_candidates('קיבלתי טרמפ הביתה', 4, table=sub_table)
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום as the substitute of טרמפ: {found} (expected True)')
    ok &= found

    print('--- substitution device: two ADJACENT clue words\' substitutes concatenate ---')
    sub_table2 = {norm('אחד'): [(norm('של'), 1)], norm('שני'): [(norm('ום'), 1)]}
    hits = substitution_candidates('אחד שני משהו', 4, table=sub_table2)
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום as של+ום from two adjacent words: {found} (expected True)')
    ok &= found

    print('--- homograph device: a clue word, de-prefixed, already IS the answer ---')
    # שרה is the canonical example (PLAYBOOK.md/SOLVE_PROTOCOL.md): she sings / a female
    # minister / the name Sarah. Here it appears with a ו- prefix glued on ('ושרה'); the
    # mechanism must strip the prefix to find the 3-letter ambiguous stem.
    homo_idx = {norm('שרה'): {'senses': ['role_noun', 'given_name']}}
    hits = homograph_candidates('ושרה בבוקר את השיר', 3, idx=homo_idx)
    found = any(h['answer'] == norm('שרה') for h in hits)
    print(f'  found שרה (destemmed from ושרה) as a homograph: {found} (expected True)')
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
