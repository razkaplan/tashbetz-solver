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


# Mechanisms that only ever emit a hit backed by TARGETED evidence -- a mined equivalence
# match, a literal clue-word occurrence, or an independent BM25 definition match -- never
# a blind scan of every same-length character window the way anagram/hidden/reversal/
# pattern/charade/container/homophone(_vowel) do. A hit from one of these is evidence in
# itself, the same reason phrase_ok/split_ok below get a tier-1 floor (see that docstring):
# a verified-real-words-glued-together hit and a targeted-mechanism hit are both signal a
# plain window scan cannot produce by accident, so neither should rank behind one.
PRECISION_MECHANISMS = {
    'retrieval', 'defspan_retrieval', 'culture_category', 'homograph', 'substitution',
    'abbreviation', 'double_definition',
}


def rank_candidates(cands, enum, max_n=25):
    """Annotate an already-generated candidate list with lexicon priority tier + split
    feasibility, and rank by the signals that actually discriminate (see module
    docstring): culture/corpus-tier hits first, then multi-part hits whose pieces are
    real words, then a proof-string convenience field. Does NOT claim any candidate is
    correct. Factored out of rank() (2026-10-12) so a caller that already has a WIDE raw
    pool (e.g. candidates.py recall_eval's `use_rank` diagnostic, see its own docstring
    for why the offline recall metric needs this same fix) can rank it without
    regenerating candidates a second time.

    `phrase_ok`/crediting `split_ok` in the PRIMARY key (2026-10-12, found while building
    the `use_rank` fix above, in two parts): several mechanisms (anagram/hidden/reversal/
    container/substitution) can accept a hit via `phrase_split()` -- the WHOLE answer is
    not itself a lex() entry, but IS the unbroken concatenation of 2-3 words that each ARE
    (e.g. `צר`+`נוביל` -> `צרנוביל`, a real anagram hit on 2026-05-29's 25 across).
    Those hits carry a `phrase` field but `lexicon_tier` only ever looks up the WHOLE
    answer string, so `words.get()` correctly returns 0 -- not a bug in the lookup, but
    the ranker then treated verified-real-words-glued-together identically to pure
    noise. The SAME gap existed, worse, for `split` (candidates.split_candidates(), the
    OLDER field, used for every multi-part-enum candidate including retrieval hits):
    it was already read here, but only as a SECONDARY tiebreaker (`split_ok is False`),
    never promoted into the PRIMARY tier -- so a `split_ok=True` hit with
    `lexicon_tier=0` (e.g. a retrieval-sourced multi-word answer, 2026-05-29's 26 across
    `פחותאבלכואב`, `split=['פחות','אבל','כואב']`) still sorted behind every single tier-1
    dictionary word, and in practice got pushed OUT of the top 25 entirely once the raw
    pool widened enough to surface more tier>=1 noise ahead of it -- measured directly:
    fixing ONLY `phrase_ok` first and shipping it alone made `recall_eval(use_rank=True)`
    REGRESS (2/40 -> 1/40) by demoting this exact retrieval hit, which is why both fields
    are fixed together here, not one at a time. Both `phrase_split()` and
    `split_candidates()` only ever accept a hit when EVERY piece is independently a
    lex() member, so either signal deserves the same tier-1 floor a plain dictionary
    word gets.

    `mechanism_ok` (2026-10-18): 2026-10-12's fix only promotes a MULTI-part hit (via
    split_ok/phrase_ok). A SINGLE-part retrieval/culture_category/homograph/substitution
    hit has neither field set (split_ok is None when len(enum)==1, phrase_ok is only ever
    set by the phrase_split() path those mechanisms don't use) -- so it still sat at the
    unmodified lexicon_tier, usually 0, and still lost to every tier>=1 dictionary-word
    window-scan hit once the wide raw pool was ranked. Found by RUNNING recall_eval
    (use_rank=True) on a fresh, independently transcribed 2026-05-29 and seeing recall
    regress 7.1%->3.6% (2/28->1/28): the lost hit was 1D `ברישניקוב` (Baryshnikov), a
    single-part (9) `retrieval` hit with split=None, phrase unset, lexicon_tier=0 (it is
    not itself a lex() member -- the whole point of retrieval is finding an answer the
    lexicon doesn't already contain). PRECISION_MECHANISMS gets the exact same tier-1
    floor phrase_ok/split_ok already get, for the exact same reason: a hit from one of
    these mechanisms cannot have been produced by blind character-window noise.

    `retrieval_score` tertiary tie-break (2026-11-16): PRECISION_MECHANISMS promotes every
    member to the SAME tier-1 floor, which is correct as far as it goes -- but once two or
    more of them land there together, this function had NOTHING left to order them by
    except `len(fodder)` (always 0 for retrieval/defspan_retrieval, since they set
    fodder=None) and, below that, Python's STABLE sort falling back to whatever order
    generate() happened to concatenate mechanisms in -- an accident of which mechanism's
    `cands +=` line runs first, not a quality signal. Root-caused on a real regression PR
    #122 flagged but left unfixed: `candidates.retrieval_candidates()` queries
    `retrieve_defs.candidates()`, which scores PER DOCUMENT, not per answer -- a single
    external document that lists ~30 near-synonyms (confirmed directly, 2026-11-16, on a
    freshly re-crawled corpus: a "weapons" document scores גרזנ/מקלע/סכינ/רומח/מטול... all
    at the SAME BM25 score) hands every one of its ~30 answers the identical score, so
    `retrieve_defs.candidates()`'s own internal order among them is already just
    insertion-order luck. That alone is not this fix's target (it is a separate, deeper
    gap in retrieve_defs.py's doc-level scoring, not fixed here). What IS fixed: once
    OTHER, unrelated PRECISION_MECHANISMS (substitution/culture_category/container/
    abbreviation/double_definition, all live together now, more of them than when this
    file was first measured) also fire on the same clue and add their own tier-1-floor
    candidates, generate()'s fixed mechanism order put every one of THOSE ahead of
    retrieval's entire batch (retrieval is appended comparatively late) -- so a real,
    positively-scored retrieval hit like 2026-06-26's 17A `רומח` (retrieve_defs rank 4/25
    for this clue, confirmed directly) could get pushed past the final max_n=25 cutoff not
    by anything that outranks it on merit, but by signal-less candidates from mechanisms
    that carry no score at all. Threading retrieval's own (coarse, doc-level, but real)
    BM25 score through as a THIRD sort key -- after the tier floor, after split_ok, before
    the existing len(fodder) catch-all -- lets a scored candidate outrank a same-floor,
    unscored one, without changing anything for the common case where neither candidate
    being compared has a score (both default to 0.0, so the comparison is a no-op and
    falls through to len(fodder) exactly as before). This is also independently supported
    by the IR literature, not just this project's own code: Lin & Yang (SIGIR 2019,
    arXiv:1807.05798) show that breaking BM25 ties on an index-internal key (document id,
    insertion order) is non-deterministic and carries no relevance signal, and recommend
    breaking ties on a stable, EXTERNAL key -- exactly what this does (RESEARCH.md,
    2026-11-16)."""
    words = candidates.lex()
    out = []
    for c in cands:
        c = dict(c)
        c['lexicon_tier'] = words.get(c['answer'], 0)
        c['split_ok'] = bool(c.get('split')) if len(enum) > 1 else None
        c['phrase_ok'] = bool(c.get('phrase'))
        c['mechanism_ok'] = c.get('mechanism') in PRECISION_MECHANISMS
        c['proof'] = proof_for(c)
        out.append(c)
    out.sort(key=lambda c: (
        -max(c['lexicon_tier'],
             1 if (c['phrase_ok'] or c['split_ok'] or c['mechanism_ok']) else 0),
        c['split_ok'] is False,       # multi-part hits with real-word pieces rank first
        -c.get('retrieval_score', 0.0),  # 2026-11-16: real score beats no score, see above
        len(c.get('fodder') or ''),
    ))
    return out[:max_n]


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
    raw_pool = max(max_n * 8, 200)
    cands = candidates.generate(clue_text, enum, pattern=pattern, max_n=raw_pool)
    return rank_candidates(cands, enum, max_n=max_n)


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

    print('--- mechanism_ok: a SINGLE-part precision-mechanism hit outranks tier-0 '
          'window-scan noise (2026-10-18 regression: 1D ברישניקוב, a retrieval hit, '
          'measured dropped by ranking before this fix) ---')
    # synthetic, controlled noise -- 30 fake tier-0 anagram hits (not real lex() words,
    # so lexicon_tier=0 and mechanism_ok=False for every one), same shape generate()'s
    # raw char-window scan produces in bulk. The precision_hit's answer is ALSO not a
    # lex() member (tier 0) -- mechanism_ok is the ONLY signal that can rank it above
    # the noise, same as a real retrieval hit (not itself a dictionary word) relies on.
    fake_noise = [{'answer': candidates.norm('קקקק') + str(i), 'mechanism': 'anagram',
                   'fodder': 'xx'} for i in range(30)]
    precision_hit = {'answer': candidates.norm('קקקק'), 'mechanism': 'retrieval', 'fodder': None}
    mixed = rank_candidates(fake_noise + [precision_hit], [4], max_n=5)
    kept = any(c['answer'] == precision_hit['answer'] and c.get('mechanism_ok')
               for c in mixed)
    print(f'  single-part retrieval hit survives ranking into the top 5: {kept} '
          f'(expected True)')
    ok &= kept

    print('--- retrieval_score tertiary tie-break (2026-11-16 regression fix): a scored '
          'hit survives being OUTNUMBERED by same-floor, unscored precision-mechanism '
          'noise placed ahead of it, reproducing the real 2026-06-26 17A רומח shape (a '
          'single BM25-matched document lists ~30 near-synonyms, all tied at the same '
          'floor, crowding a genuine hit past the cutoff by sheer insertion-order volume) ---')
    # 30 unscored PRECISION_MECHANISMS hits (mechanism_ok=True, no retrieval_score),
    # INSERTED FIRST so plain stable-sort insertion order would keep them and drop
    # anything appended after once max_n truncates -- same shape generate() produces
    # when substitution/culture_category/container all fire on the same clue before
    # retrieval_candidates() is even called. The real hit is appended LAST (maximally
    # disadvantaged by insertion order) and is the ONLY one of the 31 with a score.
    synonym_noise = [{'answer': candidates.norm('טבעת') + str(i), 'mechanism': 'substitution',
                       'fodder': None} for i in range(30)]
    scored_hit = {'answer': candidates.norm('רומח'), 'mechanism': 'retrieval', 'fodder': None,
                  'retrieval_score': 4.37}
    ranked = rank_candidates(synonym_noise + [scored_hit], [4], max_n=5)
    survived = any(c['answer'] == scored_hit['answer'] for c in ranked)
    print(f'  scored hit (appended last, outnumbered 30:1) survives top-5: {survived} '
          f'(expected True)')
    ok &= survived
    # and the control: WITHOUT a score (same shape, score defaults to 0.0 like the noise),
    # insertion order alone buries it -- confirms the test is actually exercising the new
    # key, not passing for some unrelated reason.
    unscored_hit = {'answer': candidates.norm('רומח'), 'mechanism': 'retrieval', 'fodder': None}
    ranked_control = rank_candidates(synonym_noise + [unscored_hit], [4], max_n=5)
    buried = not any(c['answer'] == unscored_hit['answer'] for c in ranked_control)
    print(f'  SAME hit with no score, same insertion position, is buried: {buried} '
          f'(expected True -- proves the fix, not a scoring-independent effect, is what '
          f'rescues the case above)')
    ok &= buried

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
