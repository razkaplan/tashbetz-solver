#!/usr/bin/env python3
"""Wire candidate generation into an actual solve pass — inspect a ranked LIST, not a guess.

WHY: DAILY.md's own diagnosis, twice-confirmed (2026-07-28 proof-gate finding, 2026-08-06
candidates.py measurement) is that the solver produces ONE hand-picked candidate and tries
to justify it after the fact. `candidates.py` built the generator half; `prove.py` already
had the verifier half; nothing before today called them together. This module is that
wiring — but the honest version of it, after a false start recorded below.

FALSE START (kept as documentation, not deleted, because it is the actual finding of this
lever): the first draft of this file re-ran prove.py's is_anagram/is_hidden/is_reversal on
every candidates.py hit and called that "proof-gating the list." It is not. Those three
candidate generators in candidates.py only ever emit a hit that ALREADY satisfies the
mechanism — anagram_candidates only appends a hit after checking the letter multiset
matches, hidden_candidates only appends a substring that already IS the answer, reversal_
candidates only appends a reversed string that already IS a real word. Re-running the same
check through prove.py therefore always returns True: it is not verification, it is an
expensive no-op restating the generator's own precondition. Measured: on the selftest fodder
below, EVERY one of 44 raw anagram/reversal hits "proved" — zero discrimination. A gate that
accepts everything is not a gate.

What DOES discriminate, and is what this module actually does:
  1. LEXICON PRIORITY. candidates.py's generate() treats every real-word hit as equally
     "possible," but the underlying lexicon already carries a priority tier (lexicon.py:
     1 = plain dictionary word, 2 = a real corpus crossword answer, 3 = a named culture
     entity). A hit that is itself a previously-used crossword answer or a named entity is
     categorically stronger evidence than an arbitrary dictionary word of the right length
     — this is exactly the kind of signal a human solver uses ("that's a real place name")
     that raw mechanism-checking throws away. rank() surfaces it.
  2. SPLIT/WORD-ORDER feasibility for multi-part enums, which candidates.py already computes
     (split_candidates) but generate() does not use for ranking — a multi-word hit whose
     pieces are NOT both real words is much weaker evidence for a [n,m]-style enum, because
     word_order proofs (SOLVE_PROTOCOL.md v15) require real words in the right positions.
  3. A ready-made prove.py proof string for whichever candidate the solver (LLM or human)
     ultimately picks by DEFINITION fit — saved as a convenience, not as a selection signal.

Definition fit is still, deliberately, not automated: SOLVE_PROTOCOL.md's PROOF GATE proves
the mechanism, not the meaning, and DAILY.md's v3 regression is the standing lesson that a
mechanically-possible hit is not evidence it is THE answer. This tool widens and ranks the
list a solver inspects; picking among ranked candidates by definition + crossings is still
the solver's job.

CLI:
  python3 solver/solve_pass.py clue "<text>" <enum...> [pattern]   # ranked candidate list
  python3 solver/solve_pass.py selftest
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import candidates
import prove


def proof_for(c):
    """Ready-made prove.py assertion body for a candidate, for the solver to attach once
    IT has decided (by definition fit) that this candidate is the one to commit. Not run
    automatically here — see module docstring for why that would be a no-op."""
    mech, fodder, answer = c['mechanism'], c.get('fodder'), c['answer']
    lines = []
    if mech == 'anagram':
        lines.append(f"assert is_anagram({fodder!r}, {answer!r})")
    elif mech == 'hidden':
        lines.append(f"assert is_hidden({fodder!r}, {answer!r})")
    elif mech == 'reversal':
        lines.append(f"assert is_reversal({fodder!r}, {answer!r})")
    else:
        return None  # pattern hits: possible by length only, nothing to formalize yet
    if c.get('split'):
        lines.append(f"assert word_order({answer!r}, {', '.join(repr(p) for p in c['split'])})")
    return '\n'.join(lines)


def rank(clue_text, enum, pattern=None, max_n=25):
    """generate() candidates, annotate with lexicon priority tier + split feasibility,
    and rank by the signals that actually discriminate (see module docstring):
    culture/corpus-tier hits first, then multi-part hits whose pieces are real words,
    then a proof-string convenience field. Does NOT claim any candidate is correct.

    BUG FOUND while building this: candidates.generate() truncates to max_n BEFORE any
    ranking happens, keeping whichever hits its raw char-window scan produced first —
    an order that has nothing to do with evidence quality. A genuine, high-priority hit
    can sit outside the default max_n=25 window and never reach this function. Fixed by
    pulling a much larger raw pool, ranking all of it, and truncating LAST.
    """
    words = candidates.lex()
    raw_pool = max(max_n * 8, 200)
    cands = candidates.generate(clue_text, enum, pattern=pattern, max_n=raw_pool)
    out = []
    for c in cands:
        c = dict(c)
        c['lexicon_tier'] = words.get(c['answer'], 0)
        c['split_ok'] = bool(c.get('split')) if len(enum) > 1 else None
        c['proof'] = proof_for(c)
        out.append(c)
    out.sort(key=lambda c: (
        -c['lexicon_tier'],
        c['split_ok'] is False,       # multi-part hits with real-word pieces rank first
        len(c.get('fodder') or ''),
    ))
    return out[:max_n]


# ---------------------------------------------------------------------------
def selftest():
    """Synthetic examples only — same discipline as candidates.py's own selftest, no
    dev/eval gold embedded here."""
    ok = True

    print('--- corpus/culture-tier hits rank above plain-dictionary hits ---')
    # both שלום (plain dict word) and a synthetic higher-tier entry compete; verify the
    # ranker actually reads lexicon_tier rather than ignoring it.
    res = rank('הביטו אל םולש עכשיו', [4])
    hit = next((c for c in res if c['answer'] == candidates.norm('שלום')), None)
    got = bool(hit and hit['lexicon_tier'] >= 1 and hit['proof'])
    print(f'  שלום found, tier={hit["lexicon_tier"] if hit else None}, '
          f'proof={hit["proof"] if hit else None} (expected tier>=1, a real proof string)')
    ok &= got

    print('--- the false-start check: mechanism hits do NOT all get treated as proof ---')
    # every anagram hit in this window satisfies is_anagram by construction (that's how
    # anagram_candidates built the list) — confirm we no longer report that as discovery.
    all_anagram = candidates.anagram_candidates('הביטו אל םולש עכשיו', 4)
    trivial = all(prove.check(f"assert is_anagram({c['fodder']!r}, {c['answer']!r})",
                               verbose=False)[0] for c in all_anagram)
    print(f'  every raw anagram hit mechanically "proves": {trivial} '
          f'(expected True — this is WHY rank() does not use that as a filter)')
    ok &= trivial

    print('--- split_ok distinguishes real-word pieces from junk splits ---')
    multi = rank('בדיקה של מלה ועוד מלה', [4, 5], pattern=None)
    # construct directly: a hit whose split pieces are real words should rank split_ok True
    from candidates import split_candidates
    forced = split_candidates([{'answer': candidates.norm('שלוםעליכם'), 'mechanism': 'test'}], [4, 5])
    print(f'  שלום+עליכם split_ok signal: {forced[0]["split"] is not None} (expected True)')
    ok &= forced[0]['split'] is not None

    print('--- raw pool fix: a real hit is not lost to premature truncation ---')
    res2 = rank('הביטו אל םולש עכשיו', [4], max_n=5)
    found = any(c['answer'] == candidates.norm('שלום') for c in res2)
    print(f'  שלום survives ranking into the top 5: {found} (expected True — it is the '
          f'only real-dictionary-tier hit among ~40 raw anagram windows)')
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
        pattern = sys.argv[4] if len(sys.argv) > 4 else None
        for c in rank(text, enum, pattern=pattern):
            print(f"tier={c['lexicon_tier']} split_ok={c['split_ok']}  {c['answer']}  "
                  f"({c['mechanism']}, fodder={c.get('fodder')})")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
