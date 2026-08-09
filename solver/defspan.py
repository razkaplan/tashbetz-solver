#!/usr/bin/env python3
"""Definition-span detection — classify which END of a cryptic clue holds the
definition, so wordplay-mechanism search can be restricted to the residual.

WHY: every cryptic clue is definition + wordplay, and the definition sits
entirely at ONE END (SOLVE_PROTOCOL.md section 1; PLAYBOOK.md section 0; the
standard rule in the English-cryptic literature). `candidates.py`'s char-window
search currently scans the WHOLE clue's letters for anagram/hidden/reversal
fodder — it does not know which words are the definition, so a window can
straddle the definition/wordplay boundary and produce a hit built partly from
definition letters, which are not fodder at all. That is a false positive:
noise the proof gate has to sift through for no reason. Once we know which end
is the definition, restricting the search to the wordplay residual removes
this whole class of spurious candidate — see `selftest` for a real,
dictionary-word example where this measurably shrinks the candidate list.

Method is rule-based, not learned. RESEARCH.md (2026-08-09) re-checked the
English-cryptic literature's definition-span technique (arXiv 2403.12094) and
found it depends on FastText-embedding similarity tuned on English clue
corpora — there is no equivalent Hebrew embedding space for this genre, and
this project's corpus is too thin to train a span classifier from scratch. So:
enumerate every plausible definition length (1-3 words at either end —
PLAYBOOK.md's double-definition clues run 2-4 words total, so a definition
longer than 3 words is rare) and score each hypothesis by whether ITS residual
alone contains real wordplay for the enum's target length. A hypothesis whose
residual produces nothing is not preferred over one that does — that is the
only leak-free signal available without gold data: internal parseability, not
agreement with a held-out answer.

This does NOT decide which candidate is correct — same discipline as
candidates.py. It narrows WHERE candidates.py looks, and reports which words
it assumed were the definition so a solver (or a later pass) can sanity-check
that against the clue's meaning.

CLI:
  python3 solver/defspan.py clue "<text>" <enum...>   # best hypothesis + candidates
  python3 solver/defspan.py selftest
  python3 solver/defspan.py stress [n]   # aggregate synthetic-clue measurement
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidates as C

# PLAYBOOK.md section 1.2: double-definitions run 2-4 words total, so a lone
# definition is almost always 1-3 words; longer than that is not worth trying.
MAX_DEF_WORDS = 3


def hypotheses(clue_text, max_def_words=MAX_DEF_WORDS):
    """Every (side, k) split of the clue into (definition words, wordplay words).
    wordplay_text is built from the ORIGINAL word list with the definition words
    removed entirely — not a substring of the full clue — so a mechanism search
    over it structurally cannot reach a definition letter."""
    ws = C.words_of(clue_text)
    n = len(ws)
    out = []
    for k in range(1, min(max_def_words, n - 1) + 1):  # always leave >=1 wordplay word
        out.append({'side': 'start', 'k': k,
                    'definition_text': ' '.join(ws[:k]),
                    'wordplay_text': ' '.join(ws[k:])})
        out.append({'side': 'end', 'k': k,
                    'definition_text': ' '.join(ws[-k:]),
                    'wordplay_text': ' '.join(ws[:-k])})
    return out


def classify(clue_text, enum, max_n=25):
    """Score every hypothesis by generating candidates from its residual ONLY.
    Sorted best-first: a hypothesis whose residual parses (>=1 candidate) beats
    one that doesn't; among parsing hypotheses, shorter k first (a definition
    is usually short, so prefer the least aggressive split that still parses)."""
    scored = []
    for h in hypotheses(clue_text):
        cands = C.generate(h['wordplay_text'], enum, max_n=max_n)
        h = dict(h, candidates=cands, parses=bool(cands))
        scored.append(h)
    scored.sort(key=lambda h: (not h['parses'], h['k']))
    return scored


def best(clue_text, enum):
    scored = classify(clue_text, enum)
    return scored[0] if scored else None


def generate(clue_text, enum, max_n=25):
    """Practical entry point: candidates from the single best definition-span
    hypothesis's residual, instead of the whole clue. Falls back to the plain
    whole-clue generator if no hypothesis parses (e.g. very short clues where
    every split leaves too little text) so this is never WORSE than the
    unrestricted search, only more precise when a hypothesis parses."""
    b = best(clue_text, enum)
    if b and b['parses']:
        return b['candidates'], b
    return C.generate(clue_text, enum, max_n=max_n), b


# ---------------------------------------------------------------------------
def selftest():
    """Real dictionary words (hspell), never a dev/eval answer — same discipline
    candidates.py's own selftest enforces."""
    ok = True

    print('--- definition-at-start: residual search drops boundary-contaminated hits ---')
    # 'נס' (miracle, real 2-letter word) as definition + 'ברז' (faucet, real
    # 3-letter word) as the wordplay itself: 'ברז' is found both as the
    # hidden word and, scrambled, as the real word 'בזר' -- both genuinely
    # live inside the residual alone, so both are legitimate. Scanning the
    # WHOLE clue's letters ('נסברז') for 3-letter windows ALSO turns up
    # 'נסב'/'סבנ'/'סבר'/'סרב' -- each straddles the definition/wordplay
    # boundary (uses ס or נ from the definition word) and could never survive
    # a definition-aware search. That is the false-positive class this lever
    # removes; it is not about collapsing to a single candidate.
    clue = 'נס ברז'
    boundary_contaminated = {'נסב', 'סבנ', 'סבר', 'סרב'}
    residual_only = {C.norm('ברז'), C.norm('בזר')}

    whole = C.generate(clue, [3])
    whole_answers = {c['answer'] for c in whole}
    print(f'  whole-clue search finds: {sorted(whole_answers)}')
    ok &= boundary_contaminated <= whole_answers  # the false positives ARE there today
    ok &= residual_only <= whole_answers

    cands, hyp = generate(clue, [3])
    found = {c['answer'] for c in cands}
    print(f'  best hypothesis: side={hyp["side"]} k={hyp["k"]} '
          f'definition="{hyp["definition_text"]}" wordplay="{hyp["wordplay_text"]}"')
    print(f'  defspan-restricted search finds: {sorted(found)} '
          f'(expected exactly {sorted(residual_only)}, no boundary hits)')
    ok &= hyp['side'] == 'start' and hyp['definition_text'] == 'נס'
    ok &= found == residual_only
    ok &= not (found & boundary_contaminated)

    print('--- definition-at-end: same pair, reversed clue order ---')
    clue2 = 'ברז נס'
    cands2, hyp2 = generate(clue2, [3])
    found2 = {c['answer'] for c in cands2}
    print(f'  best hypothesis: side={hyp2["side"]} k={hyp2["k"]} '
          f'definition="{hyp2["definition_text"]}" wordplay="{hyp2["wordplay_text"]}"')
    print(f'  found: {sorted(found2)} (expected exactly {sorted(residual_only)})')
    ok &= hyp2['side'] == 'end' and hyp2['definition_text'] == 'נס'
    ok &= found2 == residual_only

    print('--- fallback: no hypothesis exists (single-word clue) -> whole-clue search ---')
    # A one-word clue leaves no room for a >=1-word definition AND a >=1-word
    # residual, so hypotheses() is structurally empty and generate() must fall
    # back to candidates.py's own (already-validated) whole-clue search.
    # Reuses candidates.py selftest's own fodder for the same reason it uses
    # synthetic examples: no dev/eval answer embedded here either.
    clue3 = 'םולש'
    cands3, hyp3 = generate(clue3, [4])
    found3 = {c['answer'] for c in cands3}
    print(f'  best hypothesis: {hyp3} (expected None -- no split possible)')
    print(f'  found: {sorted(found3)} (expected שלום via fallback)')
    ok &= hyp3 is None and C.norm('שלום') in found3

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


# ---------------------------------------------------------------------------
def stress(n=200, def_len=2, wordplay_len=3):
    """Aggregate, reproducible measurement (no randomness) of how often
    definition-span restriction shrinks the candidate list on synthetic
    "<real DEF word> <real WORDPLAY word>" clues built from the plain hspell
    dictionary -- NOT a claim about live puzzle recall (that needs a
    transcribed puzzle, blocked this run, see the log). This only quantifies
    the false-positive-reduction mechanism itself, at scale, beyond the two
    hand-picked selftest examples."""
    words = sorted(w for w in C.lex() if len(w) == def_len)[:n]
    wp_words = sorted(w for w in C.lex() if len(w) == wordplay_len)[:n]
    total_whole, total_residual, shrank, examined = 0, 0, 0, 0
    for d, w in zip(words, wp_words):
        clue = f'{d} {w}'
        whole = len(C.generate(clue, [wordplay_len]))
        cands, hyp = generate(clue, [wordplay_len])
        residual = len(cands)
        examined += 1
        total_whole += whole
        total_residual += residual
        if residual < whole:
            shrank += 1
    print(f'{examined} synthetic clues (DEF={def_len}-letter + WORDPLAY='
          f'{wordplay_len}-letter real words)')
    print(f'mean candidates whole-clue: {total_whole / examined:.2f}')
    print(f'mean candidates defspan-restricted: {total_residual / examined:.2f}')
    print(f'clues where restriction shrank the list: {shrank}/{examined} '
          f'({shrank / examined:.0%})')


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
        cands, hyp = generate(text, enum)
        print(f'best split: side={hyp["side"] if hyp else None} '
              f'k={hyp["k"] if hyp else None} '
              f'definition="{hyp["definition_text"] if hyp else ""}" '
              f'wordplay="{hyp["wordplay_text"] if hyp else text}"')
        for c in cands:
            print(c)
    elif cmd == 'stress':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        stress(n)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
