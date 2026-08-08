#!/usr/bin/env python3
"""Mechanical candidate generation for cryptic clues.

WHY: the measured bottleneck (RESULTS.md, DAILY.md) is not verification — the proof
gate (prove.py) is airtight once it has something to check. The bottleneck is that a
solver produces ONE candidate and tries to justify it. That is backwards: a cryptic
clue's wordplay is mechanical (anagram/hidden/reversal/charade), so a machine should
enumerate every candidate a mechanism can produce and hand the LIST to the proof gate,
rather than have the solver guess once and rationalize.

This module does exactly that, per clue, with no LLM involved:
  - anagram_candidates:       every contiguous word-window whose letter count matches
                               the enum total, checked against the lexicon for
                               real-word anagrams.
  - hidden_candidates:        a contiguous run inside the space-removed clue that is
                               itself a real word (the "hidden word" device).
  - reversal_candidates:      same search, reversed.
  - substitution_candidates:  the setter's private vocabulary (substitutions.py):
                               swap one clue word for a recorded equivalence, then
                               re-run the hidden/anagram search over the substituted
                               letter stream — the charade device, mechanised.
  - homograph_candidates:     a clue word already sitting in ambiguities.json (a name,
                               role noun, place, song) proposed directly as the answer,
                               or expanded to the full entity it is a component of
                               (טומי -> טומי לפיד) — the setter's other main device.
  - pattern_candidates:       wraps lexicon.py's crossing-pattern lookup, for when grid
                               letters are already known.
  - split_candidates:         for multi-part enums (e.g. (5,2)), splits a hit at the
                               enum boundary and flags whether BOTH pieces are real
                               words — the precondition prove.py's word_order() needs.

None of this asserts an answer is CORRECT — it only asserts an answer is POSSIBLE by a
named mechanism. Selecting among candidates and proving one is still prove.py's job.
Held-out dev/eval answers are excluded from the lexicon by lexicon.held_out_answers(),
so this generator cannot recover a dev/eval gold answer by looking it up — only by
actually deriving it mechanically, same discipline as the rest of the solver.
homograph_candidates deliberately excludes ambiguities.json's 'answer' sense (mined
from the full, unfiltered answers corpus) as a generation source for the same reason —
see its docstring.

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


_SUBS = None


def subs():
    """solver/lex/substitutions.json — 3,141 clue-fragment -> answer-fragment
    equivalences mined from crowd explanations (substitutions.py). Same file
    prove.py's means() assertion already checks proposed answers against; this is
    the same table used for generation instead of verification."""
    global _SUBS
    if _SUBS is None:
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUBS = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUBS


def substitution_candidates(clue_text, target_len, max_per_word=5):
    """Charade candidates: swap ONE clue word for a recorded substitution (either
    direction — what it can be written as, or what it can stand for), then re-run the
    same hidden/anagram window search over the substituted letter stream. Mechanises
    the setter's commonest unaccounted-for-word device (SOLVE_PROTOCOL.md v14):
    'I have most of the answer but one word does nothing' -> that word usually has a
    recorded substitution.
    """
    words = lex()
    d = subs()
    clue_words = words_of(clue_text)
    out = []
    for i, w in enumerate(clue_words):
        nw = norm(w)
        repls = set()
        for side in ('fwd', 'rev'):
            for b, _n in d.get(side, {}).get(nw, [])[:max_per_word]:
                repls.add(b)
        for repl in repls:
            new_words = list(clue_words)
            new_words[i] = repl
            joined = norm(''.join(new_words))
            for j in range(len(joined) - target_len + 1):
                sub_win = joined[j:j + target_len]
                if sub_win in words:
                    out.append({'answer': sub_win, 'mechanism': 'substitution',
                                'fodder': f'{w}->{repl}'})
                for hit in anagram_lookup(sub_win, target_len):
                    if hit != sub_win:
                        out.append({'answer': hit, 'mechanism': 'substitution+anagram',
                                    'fodder': f'{w}->{repl}'})
    return out


_AMBIG = None


def ambig():
    global _AMBIG
    if _AMBIG is None:
        p = os.path.join(HERE, 'lex/ambiguities.json')
        _AMBIG = json.load(open(p)) if os.path.exists(p) else {}
    return _AMBIG


# Deliberately excludes 'answer' and 'song_word' (see homograph_candidates docstring).
_SAFE_SENSES = {'given_name', 'surname', 'role_noun', 'artist', 'politician', 'song',
                 'place', 'common_word', 'bible'}
_FULL_KINDS = ('given_name', 'surname', 'artist', 'politician', 'song', 'place')


def _stems(nw):
    """Delegate to homographs.py's own prefix/suffix stripping so the two modules
    agree on what counts as the ambiguous stem of an inflected/prefixed clue word."""
    sys.path.insert(0, HERE)
    import homographs
    return homographs.variants(nw)


def homograph_candidates(clue_text, target_len):
    """The setter's other core device (SOLVE_PROTOCOL.md v7): unvocalized Hebrew
    collapses several words into one letter sequence, and the clue's definition often
    targets a sense OTHER than the surface reading of a word already sitting in the
    clue. Two candidate shapes, both requiring nothing but the clue text itself:
      (a) the clue word (or an inflected stem of it) taken plain, if its own length
          matches the enum — the answer IS a word already in the clue, read differently;
      (b) for a name-component word (e.g. טומי), the FULL entity name it is a fragment
          of (טומי לפיד), if THAT length matches — the first-name-only device.

    Deliberately excludes ambiguities.json's 'answer' sense: that sense is set
    whenever a token happened to be SOME crossword answer anywhere in the 52-puzzle
    corpus, dev/eval puzzles included, with no exclusion. Using it to justify a
    candidate would leak a held-out gold answer's identity through the token's own
    history rather than deriving it from the clue in front of us — the same failure
    mode RESULTS.md's INTEGRITY FINDING already caught once in lexicon.py. The senses
    used here instead (dictionary membership, curated role nouns, Wikipedia-sourced
    culture entities) are all independent of the answers corpus.
    """
    idx = ambig()
    if not idx:
        return []
    out = []
    for w in words_of(clue_text):
        nw = norm(w)
        for stem in _stems(nw):
            d = idx.get(stem)
            if not d:
                continue
            senses = set(d.get('senses', [])) & _SAFE_SENSES
            if not senses:
                continue
            if len(stem) == target_len:
                out.append({'answer': stem, 'mechanism': 'homograph', 'fodder': w,
                            'senses': sorted(senses)})
            evidence = d.get('evidence', {})
            for kind in _FULL_KINDS:
                for full in evidence.get(kind, []):
                    fn = norm(full)
                    if fn and fn != stem and len(fn) == target_len:
                        out.append({'answer': fn, 'mechanism': 'homograph_full',
                                    'fodder': f'{w}->{full}', 'senses': sorted(senses)})
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

    print('--- substitution device: swapping a clue word for its recorded equivalence ---')
    # טומי -> לפיד is a real, committed substitution (substitutions.json); לפיד (4) is
    # also a plain dictionary word ("torch"), so after the swap it should surface as
    # a hidden-word hit at the very start of the substituted letter stream.
    cands = substitution_candidates('טומי בלי כלום', 4)
    found = any(h['answer'] == norm('לפיד') and h['mechanism'] == 'substitution' for h in cands)
    print(f'  found לפיד via טומי->לפיד substitution: {found} (expected True)')
    ok &= found

    print('--- homograph device: a clue word taken plain, at its own alternate sense ---')
    # שרה (3) has multiple recorded senses (given_name/role_noun/song/...); asking for
    # a 3-letter answer should surface the word itself as a homograph candidate.
    cands = homograph_candidates('הבוקר שרה בטלוויזיה', 3)
    found = any(h['answer'] == norm('שרה') and h['mechanism'] == 'homograph' for h in cands)
    print(f'  found שרה as itself (alternate sense): {found} (expected True)')
    ok &= found

    print('--- homograph device: a name component expanded to its full entity ---')
    # אבא is a recorded given-name component of the full name "אבא חושי" (7 letters,
    # ambiguities.json, sourced from he-wikipedia culture entities, not the answers
    # corpus) — the "first-name-only" device.
    cands = homograph_candidates('אבא לא היה שם', 7)
    found = any(h['answer'] == norm('אבא חושי') and h['mechanism'] == 'homograph_full' for h in cands)
    print(f'  found אבא חושי via אבא name-component expansion: {found} (expected True)')
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
