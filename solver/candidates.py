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


_SUB = None


def subs():
    """The setter's mined substitution table (substitutions.py): word -> [(equivalent, count), ...].
    Loaded once, same discipline as lex()."""
    global _SUB
    if _SUB is None:
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUB = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUB


def substitution_candidates(clue_text, target_len, max_subs_per_word=4):
    """Anagram/hidden/reversal search, but ALSO over fodder where one clue word has
    been swapped for a substitution the setter is known to use for it (substitutions.json,
    mined from 8,249 crowd explanations: a name completed by a surname, an abbreviation,
    a word standing for a fragment).

    WHY a separate mechanism instead of folding into anagram_candidates: the plain
    character-window search only ever sees letters that are LITERALLY in the clue. Half
    the setter's vocabulary (SOLVE_PROTOCOL.md: "39% of clue words in this genre have a
    recorded substitution") never appears literally — the clue says "יו" and means
    "גרנט", or says "קנ" and means "בית". A window search can never find fodder it
    can't see; substituting known equivalents before windowing lets it see further,
    without inventing anything (every substitution used here is one the setters have
    actually used, not a generic thesaurus guess — same grounding discipline as
    prove.py's `means()`).

    One word is substituted at a time (not combinatorial across multiple words at once):
    keeps the search space linear in clue length instead of exponential, and matches how
    the setter actually builds a charade — one fragment reinterpreted, the rest literal.
    """
    words = words_of(clue_text)
    joined_words = [norm(w) for w in words]
    S = subs()
    out = []
    for i, w in enumerate(joined_words):
        if not w:
            continue
        equivalents = S['fwd'].get(w, [])[:max_subs_per_word] + S['rev'].get(w, [])[:max_subs_per_word]
        for equiv, _count in equivalents:
            equiv = norm(equiv)
            if not equiv or equiv == w:
                continue
            swapped = ''.join(joined_words[:i]) + equiv + ''.join(joined_words[i + 1:])
            for mech_fn, mech_name in ((anagram_candidates, 'anagram'), (hidden_candidates, 'hidden'),
                                        (reversal_candidates, 'reversal')):
                for cand in mech_fn(swapped, target_len):
                    cand = dict(cand)
                    cand['mechanism'] = mech_name + '+sub'
                    cand['substituted'] = f'{w}->{equiv}'
                    out.append(cand)
    return out


_AMBIG = None


def ambiguities():
    """The homograph index (homographs.py): token -> {senses, evidence}. evidence for
    given_name/surname/answer senses holds full multi-word entities (e.g. 'אבא חושי')
    that a single clue token can stand in for."""
    global _AMBIG
    if _AMBIG is None:
        p = os.path.join(HERE, 'lex/ambiguities.json')
        _AMBIG = json.load(open(p)) if os.path.exists(p) else {}
    return _AMBIG


ENTITY_SENSES = ('given_name', 'surname', 'song', 'artist', 'politician', 'place')
# 'answer' deliberately excluded: homographs.py stores CROWD EXPLANATION SNIPPETS as
# 'answer'-sense evidence (not alternate entity names like the other senses), so
# treating it as a candidate source is both semantically wrong (produces junk strings
# from mangled explanation text — measured: one hit, 'ההיפכרצ', is not a real word) and
# a structural leak risk: ambiguities.json's keys are corpus ANSWERS with no
# held_out_answers() filtering (unlike lexicon.py), so 'answer'-sense lookups sit next
# to dev/eval gold answers in the same index. Not proven exploitable today (a clue
# would have to literally contain its own answer as a substring, which real cryptic
# clues never do), but excluding it removes the path entirely rather than relying on
# that argument holding forever.


def homograph_candidates(clue_text, target_len):
    """A clue token that is a known homograph (one letter-sequence, several senses —
    solver/HOMOGRAPHS.md: this setter's main weapon) can stand for a full multi-word
    entity under its OTHER sense: "the minister" (השר) sitting in a clue may really mean
    the name שרה, and a surname mentioned may really point at the full name. This
    surfaces those full entities directly as candidates when their length matches the
    enum — a mechanism the plain anagram/hidden/reversal search cannot reach, because
    the target string is not a rearrangement of the clue's letters at all, it is a
    DIFFERENT reading of a token already sitting there.

    Deliberately narrow: only entity-shaped senses (given_name/surname/answer/song/
    artist/politician/place), not every dictionary sense, or this would just re-surface
    hidden_candidates' own hits under a new label.
    """
    idx = ambiguities()
    out, seen_tokens = [], set()
    for w in words_of(clue_text):
        nw = norm(w)
        if len(nw) < 2:
            continue
        candidates_tokens = {nw}
        try:
            sys.path.insert(0, HERE)
            import homographs
            candidates_tokens |= homographs.variants(nw)
        except Exception:
            pass
        for tok in candidates_tokens:
            if tok in seen_tokens or tok not in idx:
                continue
            seen_tokens.add(tok)
            evidence = idx[tok].get('evidence', {})
            for sense in ENTITY_SENSES:
                for entity in evidence.get(sense, []):
                    ans = norm(entity)
                    if ans and ans != tok and len(ans) == target_len:
                        out.append({'answer': ans, 'mechanism': 'homograph', 'fodder': tok, 'sense': sense})
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
    cands += substitution_candidates(clue_text, target_len)
    cands += homograph_candidates(clue_text, target_len)
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

    print('--- pattern device: crossing-pattern lookup wraps lexicon.pattern ---')
    hits = pattern_candidates('של?ם')
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום matching pattern של?ם: {found} (expected True)')
    ok &= found

    print('--- split_candidates: flags whether a multi-part answer is two real words ---')
    split = split_candidates([{'answer': norm('שלוםעליכם'), 'mechanism': 'test'}], [4, 5])
    print(f'  split result: {split[0]["split"]} (expected two real words, not None)')
    ok &= split[0]['split'] is not None

    print('--- substitution device: fodder invisible in the literal clue, visible after a')
    print('    known equivalence swap (קנ~בית is a real mined pair, not invented) ---')
    hits = substitution_candidates('הלכתי קנ גדול', 3)
    found = any(h['answer'] == norm('בית') and 'sub' in h['mechanism'] for h in hits)
    print(f'  found בית via קנ->בית substitution: {found} (expected True)')
    ok &= found

    print('--- homograph device: a clue token stands for a full entity under its OTHER')
    print('    sense (אבא is also the given-name component of אבא חושי) ---')
    hits = homograph_candidates('אבא הלך הביתה', 7)
    found = any(h['answer'] == norm('אבא חושי') and h['mechanism'] == 'homograph' for h in hits)
    print(f'  found אבא חושי via the אבא homograph: {found} (expected True)')
    ok &= found

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
