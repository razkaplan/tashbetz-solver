#!/usr/bin/env python3
"""Global constraint propagation over per-slot candidate lists.

DAILY.md's lever queue item 4 ("global constraint optimization ... the real
prize") has been on the queue since PLAN_V2.md was written and has never been
attempted, despite roughly ten PRs adding new candidate-GENERATION mechanisms
(container/gematria/segment/substitution charades/defspan/...). Every one of
those levers improves candidates.py's per-clue list in isolation and is
scored by recall@N: is gold ANYWHERE in this one clue's list, judged with no
knowledge of the rest of the grid. SOLVE_PROTOCOL.md's "cross-letter pass"
also uses the grid, but only AFTER a clue is already committed, and only as a
pattern filter on lexicon.py (one slot at a time, greedily, in some fixed
clue order) -- never as a constraint that runs across every slot at once,
before anything is committed.

This module adds exactly the missing piece: arc consistency (the same idea
Dr. Fill / the Berkeley Crossword Solver / Proverb use, scoped down to
something shippable in one run rather than a full weighted-CSP solve). A
candidate for one slot survives a propagation round only if, at every cell it
shares with another slot, at least one candidate in that OTHER slot's own
list agrees with it at that cell. This can only ever shrink a slot's
candidate set (or leave it unchanged); run to a fixpoint, a few slots may be
narrowed to exactly one surviving candidate -- "forced" by nothing but
cross-referencing the whole grid's candidate pools against each other, no
single-clue confidence judgement involved.

HONEST FAILURE MODE this module is built to surface, not hide: arc
consistency is only as good as the candidate pools it propagates. This
project's own recall@N is ~3.6% mechanically -- most slots' candidate lists
do NOT contain the gold answer at all. When slot A's true letter at a shared
cell has no support in slot B's candidate list (because B's generator never
found the true answer either), a correct candidate in A gets pruned as if it
were wrong, even though the grid itself is perfectly consistent. So this is
expected to often make precision WORSE, not better, until candidate recall
improves -- a global optimizer can only rank/filter what candidate
generation hands it, exactly as PLAN_V2.md's own ordering (A after B) says.
Measuring that honestly, on this project's own data, is the point.

2026-11-15 ADDITION: every measurement of `soft_propagate()` so far (PR #118,
#119) scored gold's RANK in a single flat batch-scoring pass -- never an
actual sequential solve. Dr.Fill/Cruciform's own account (arXiv 1611.02360)
describes something this project had only cited, never built: commit one
slot at a time, picking next the slot with the largest CONFIDENCE GAP
(top-candidate score minus runner-up), and letting each commit's letters
inform the slots still waiting. `confidence_gap()` / `simulate_sequential_commit()`
/ `measure_commit_order()` close that gap -- see their docstrings.
"""
import json
import sys

sys.path.insert(0, 'solver')
import candidates as C
import grid_tools as G


def build_candidate_lists(grid, clue_rows, max_n=40, **gen_kwargs):
    """clue_rows: iterable of dicts with clue_number, direction, clue_text, enum.
    Returns {(num, direction): set(answer_str)}, never touching gold answers."""
    sl = G.slots(grid)
    out = {}
    for row in clue_rows:
        key = (row['clue_number'], row['direction'])
        cells = sl.get(key)
        if not cells:
            continue
        cands = C.generate(row['clue_text'], row['enum'], max_n=max_n, **gen_kwargs)
        out[key] = {c['answer'] for c in cands if len(c['answer']) == len(cells)}
    return out


def propagate(grid, cand_lists, max_rounds=10):
    """Arc-consistency fixpoint. Mutates and returns a NEW dict (input untouched).
    Returns (pruned_lists, rounds_run, any_emptied)."""
    sl = G.slots(grid)
    crossmap = G.crossings(grid)
    lists = {k: set(v) for k, v in cand_lists.items()}
    any_emptied = False
    for round_n in range(1, max_rounds + 1):
        changed = False
        for cell, keys in crossmap.items():
            if len(keys) < 2:
                continue
            for key in keys:
                if key not in lists:
                    continue
                cells = sl[key]
                idx = cells.index(cell)
                # A crossing slot with an EMPTY candidate list is missing
                # information (our own generator came up short), not proof
                # that no letter works there -- treat it as unconstraining
                # rather than letting one empty neighbor veto every
                # candidate everywhere it touches. Measured without this
                # guard: 10/28 slots on the canonical dev puzzle start with
                # zero candidates, and naive strict arc-consistency cascades
                # that into every slot on the grid emptying out within two
                # rounds (avg candidates after: 0.0, including the one slot
                # that held the gold answer). See the module docstring.
                others = [k for k in keys if k != key and k in lists and lists[k]]
                if not others:
                    continue
                kept = set()
                for cand in lists[key]:
                    if idx >= len(cand):
                        continue
                    ch = cand[idx]
                    ok = True
                    for ok_key in others:
                        ocells = sl[ok_key]
                        oidx = ocells.index(cell)
                        if not any(len(oc) > oidx and oc[oidx] == ch for oc in lists[ok_key]):
                            ok = False
                            break
                    if ok:
                        kept.add(cand)
                if kept != lists[key]:
                    changed = True
                    if not kept and lists[key]:
                        any_emptied = True
                    lists[key] = kept
        if not changed:
            return lists, round_n, any_emptied
    return lists, max_rounds, any_emptied


def measure(dataset_path, split=None, max_n=40, **gen_kwargs):
    """Loads one puzzle's rows (must all share one puzzle_date), runs
    build+propagate, and reports the comparison the mandatory audit needs:
    candidate-pool size before/after, how many slots get forced to one
    surviving candidate, how many of those are actually correct, and --
    the critical safety check -- whether propagation ever threw away the
    gold answer that was present before propagation ran."""
    rows = [json.loads(l) for l in open(dataset_path)]
    if split:
        rows = [r for r in rows if r['split'] == split]
    by_puzzle = {}
    for r in rows:
        by_puzzle.setdefault(r['puzzle_date'], []).append(r)

    report = []
    for date, prows in sorted(by_puzzle.items()):
        grid_path = f'data/grids/{date}.json'
        try:
            grid = json.load(open(grid_path))['grid']
        except FileNotFoundError:
            continue
        gold = {(r['clue_number'], r['direction']): C.norm(r['answer_raw'])
                for r in prows if r.get('answer_raw')}
        cand_lists = build_candidate_lists(grid, prows, max_n=max_n, **gen_kwargs)
        before_sizes = {k: len(v) for k, v in cand_lists.items()}
        gold_in_before = {k for k, g in gold.items()
                           if k in cand_lists and g in cand_lists[k]}
        after, rounds_run, any_emptied = propagate(grid, cand_lists)
        after_sizes = {k: len(v) for k, v in after.items()}
        gold_in_after = {k for k, g in gold.items()
                          if k in after and g in after[k]}
        gold_lost = gold_in_before - gold_in_after
        forced = {k for k, v in after.items() if len(v) == 1}
        forced_correct = {k for k in forced if gold.get(k) in after[k]}

        n_slots = len(cand_lists)
        avg_before = sum(before_sizes.values()) / n_slots if n_slots else 0
        avg_after = sum(after_sizes.values()) / n_slots if n_slots else 0
        report.append({
            'puzzle_date': date,
            'n_slots': n_slots,
            'rounds_to_fixpoint': rounds_run,
            'avg_candidates_before': round(avg_before, 2),
            'avg_candidates_after': round(avg_after, 2),
            'recall_before': len(gold_in_before),
            'recall_after': len(gold_in_after),
            'gold_lost_to_pruning': sorted(gold_lost),
            'forced_unique': len(forced),
            'forced_unique_correct': len(forced_correct),
            'any_slot_emptied': any_emptied,
        })
    return report


def build_candidate_lists_scored(grid, clue_rows, max_n=40, **gen_kwargs):
    """Like build_candidate_lists, but keeps a BASE SCORE per candidate instead of
    collapsing to a bare set. The score is the candidate's position in generate()'s
    own priority-ordered output (see candidates.generate()'s docstring: mechanism
    order there is a deliberate rare/high-precision-first tier, not an arbitrary
    accumulation order) -- the first-listed candidate for a clue scores highest.
    This is the existing, already-documented confidence signal this project has,
    not an invented one. Returns {(num, direction): {answer: score}}."""
    sl = G.slots(grid)
    out = {}
    for row in clue_rows:
        key = (row['clue_number'], row['direction'])
        cells = sl.get(key)
        if not cells:
            continue
        cands = C.generate(row['clue_text'], row['enum'], max_n=max_n, **gen_kwargs)
        n = len(cands)
        scores = {}
        for i, c in enumerate(cands):
            ans = c['answer']
            if len(ans) != len(cells):
                continue
            scores[ans] = max(scores.get(ans, 0), float(n - i))
        out[key] = scores
    return out


_REAL_WORD_CACHE = {}


def is_real_word(ans):
    """True iff `ans` sits in candidates.lex() at all (any of the three tiers:
    hspell/corpus/culture). Held-out-safe by construction -- lex() already runs
    every dev/eval puzzle's own gold answers through lexicon.held_out_answers()
    before this ever sees them (same guard every other tool in this project
    uses), so this can never leak a held-out answer by letting it "pass" the
    real-word check BECAUSE it is the answer. The one accepted side effect,
    disclosed rather than hidden: a CORRECT candidate that happens to equal
    the puzzle's own held-out gold answer in some OTHER slot is scrubbed from
    lex() too, so it will read as "not real" here even though it is -- a
    conservative bias against this puzzle's specific answers, never a leak in
    the other direction. Cached per answer string (lex() itself is already
    cached in candidates.py; this just avoids re-hashing in a hot loop)."""
    if ans not in _REAL_WORD_CACHE:
        _REAL_WORD_CACHE[ans] = C.norm(ans) in C.lex()
    return _REAL_WORD_CACHE[ans]


def soft_propagate(grid, cand_scores, rounds=3, support_weight=1.0, real_word_support=False):
    """Weighted-CSP-style re-ranking, in the spirit of Dr.Fill (Ginsberg, arXiv
    1401.4597 / JAIR 42:851-886): Dr.Fill assigns every candidate fill a score and
    searches for the highest-scoring assignment that agrees at every crossing --
    it never hard-deletes a candidate just because a crossing slot's OWN pool
    currently lacks support for it. That is exactly the failure mode propagate()'s
    strict (arc-consistency) version hit on this project's own canonical dev
    puzzle: the one slot holding the gold answer got pruned to empty because its
    crossing neighbour's generator never separately produced the matching letter
    (see this module's docstring and DAILY.md's 2026-11-06/11-10 entries).

    This function is a deliberately scoped translation of that principle, not a
    port of Dr.Fill's own search (a full limited-discrepancy search over the whole
    grid's joint assignment -- see RESEARCH.md's 2026-11-11 entry for why that is
    a bigger-than-one-day unit). What IS ported: scoring instead of deleting. Each
    round, a candidate's score accumulates SUPPORT from its crossing slots' own
    current best-scoring agreeing candidate at the shared cell. A candidate with
    no support anywhere simply keeps its base score -- it is NEVER removed from
    its slot's pool, by construction (every key and every candidate present on
    input is present on output; only the attached score changes). That guarantee
    is what a hard-elimination pass cannot offer and is the entire point of this
    function: a correct-but-currently-unsupported candidate can still be ranked
    #1 by its own base score even when nothing agrees with it yet, and never
    disappears the way it did under propagate().

    real_word_support (queue item 4's own named next step, PR #118 2026-11-11):
    when True, a candidate in the SUPPORTING slot may only lend support if it is
    itself a real word per is_real_word() -- PR #118 measured only 357/988
    (36.1%) of this puzzle's whole candidate pool are real lexicon entries at
    all, so unfiltered "does anything agree with me" mostly counts agreement
    among anagram/reversal letter-salad, which is noise, not signal. This never
    changes which candidates exist in the SUPPORTED slot (the construction
    guarantee above is untouched) -- it only restricts which candidates in
    OTHER slots are allowed to cast a supporting vote.

    cand_scores: {(num, direction): {answer: base_score}} (e.g. from
    build_candidate_lists_scored). Returns a NEW dict of the same shape; the
    *set* of answers per slot is always identical to the input's, only scores
    change."""
    sl = G.slots(grid)
    crossmap = G.crossings(grid)
    scores = {k: dict(v) for k, v in cand_scores.items()}
    for _ in range(max(0, rounds)):
        new_scores = {k: dict(v) for k, v in scores.items()}
        for cell, keys in crossmap.items():
            if len(keys) < 2:
                continue
            for key in keys:
                if key not in scores:
                    continue
                cells = sl[key]
                idx = cells.index(cell)
                others = [k for k in keys if k != key and k in scores]
                if not others:
                    continue
                for cand, base in cand_scores[key].items():
                    if idx >= len(cand):
                        continue
                    ch = cand[idx]
                    support = 0.0
                    for ok in others:
                        ocells = sl[ok]
                        oidx = ocells.index(cell)
                        pool = scores[ok].items()
                        if real_word_support:
                            pool = ((oc, sc) for oc, sc in pool if is_real_word(oc))
                        best = max((sc for oc, sc in pool
                                    if len(oc) > oidx and oc[oidx] == ch), default=0.0)
                        support += best
                    new_scores[key][cand] = base + support_weight * support
        scores = new_scores
    return scores


def _rank_of(score_map, target):
    """1-based rank of `target` by score descending (stable tie-break: answer
    string), or None if target isn't a key at all."""
    if target not in score_map:
        return None
    order = sorted(score_map.items(), key=lambda kv: (-kv[1], kv[0]))
    for i, (ans, _) in enumerate(order, 1):
        if ans == target:
            return i
    return None


def measure_soft(dataset_path, split=None, max_n=40, rounds=3, support_weight=1.0,
                  **gen_kwargs):
    """Honest before/after for the soft/scored variant, run alongside the SAME
    puzzle's strict propagate() result so the comparison this lever exists to make
    -- does scoring instead of deleting actually avoid strict's failure mode? --
    is answered directly, not just asserted. See soft_propagate()'s docstring for
    the construction guarantee this function checks rather than assumes."""
    rows = [json.loads(l) for l in open(dataset_path)]
    if split:
        rows = [r for r in rows if r['split'] == split]
    by_puzzle = {}
    for r in rows:
        by_puzzle.setdefault(r['puzzle_date'], []).append(r)

    report = []
    for date, prows in sorted(by_puzzle.items()):
        grid_path = f'data/grids/{date}.json'
        try:
            grid = json.load(open(grid_path))['grid']
        except FileNotFoundError:
            continue
        gold = {(r['clue_number'], r['direction']): C.norm(r['answer_raw'])
                for r in prows if r.get('answer_raw')}
        cand_scores = build_candidate_lists_scored(grid, prows, max_n=max_n, **gen_kwargs)

        gold_in_pool = {k for k, g in gold.items()
                        if k in cand_scores and g in cand_scores[k]}
        ranks_before = {k: _rank_of(cand_scores[k], gold[k]) for k in gold_in_pool}

        after = soft_propagate(grid, cand_scores, rounds=rounds, support_weight=support_weight)

        # Construction guarantee: cardinality (the candidate SET) never changes.
        for k in cand_scores:
            assert set(after.get(k, {})) == set(cand_scores[k]), \
                f'{k}: soft_propagate must never change a slot\'s candidate SET'

        ranks_after = {k: _rank_of(after[k], gold[k]) for k in gold_in_pool}
        gold_lost_soft = {k for k in gold_in_pool if gold[k] not in after.get(k, {})}

        # Cross-check against strict propagate() on the SAME raw pools -- the
        # comparison this lever exists to make.
        strict_lists = {k: set(v.keys()) for k, v in cand_scores.items()}
        strict_after, _, _ = propagate(grid, strict_lists)
        gold_lost_strict = {k for k in gold_in_pool if gold[k] not in strict_after.get(k, set())}

        top1_before = sum(1 for k in gold_in_pool if ranks_before[k] == 1)
        top1_after = sum(1 for k in gold_in_pool if ranks_after[k] == 1)
        rank_improved = sorted(k for k in gold_in_pool if ranks_after[k] < ranks_before[k])
        rank_worsened = sorted(k for k in gold_in_pool if ranks_after[k] > ranks_before[k])

        # Queue item 4's own named next step (PR #118, 2026-11-11): does
        # restricting cross-slot SUPPORT to real-lexicon-word candidates (not
        # touching which candidates exist, same construction guarantee) fix
        # the "agreement among noise" problem PR #118 found and measured?
        after_rw = soft_propagate(grid, cand_scores, rounds=rounds,
                                   support_weight=support_weight, real_word_support=True)
        for k in cand_scores:
            assert set(after_rw.get(k, {})) == set(cand_scores[k]), \
                f'{k}: real_word_support must never change a slot\'s candidate SET either'
        ranks_after_rw = {k: _rank_of(after_rw[k], gold[k]) for k in gold_in_pool}
        gold_lost_rw = {k for k in gold_in_pool if gold[k] not in after_rw.get(k, {})}
        top1_after_rw = sum(1 for k in gold_in_pool if ranks_after_rw[k] == 1)
        rank_improved_rw = sorted(k for k in gold_in_pool if ranks_after_rw[k] < ranks_before[k])
        rank_worsened_rw = sorted(k for k in gold_in_pool if ranks_after_rw[k] > ranks_before[k])
        n_real = sum(1 for scores in cand_scores.values() for ans in scores if is_real_word(ans))
        n_total = sum(len(scores) for scores in cand_scores.values())

        report.append({
            'puzzle_date': date,
            'n_slots_with_gold_in_pool': len(gold_in_pool),
            'pool_real_word_fraction': round(n_real / n_total, 3) if n_total else None,
            'gold_lost_strict_hard_elimination': sorted(gold_lost_strict),
            'gold_lost_soft_scoring': sorted(gold_lost_soft),
            'gold_lost_soft_scoring_real_word_support': sorted(gold_lost_rw),
            'strict_lost_but_soft_kept': sorted(gold_lost_strict - gold_lost_soft),
            'top1_before_scoring': top1_before,
            'top1_after_soft_propagation': top1_after,
            'top1_after_real_word_support': top1_after_rw,
            'rank_improved': rank_improved,
            'rank_worsened': rank_worsened,
            'rank_improved_real_word_support': rank_improved_rw,
            'rank_worsened_real_word_support': rank_worsened_rw,
        })
    return report


def confidence_gap(score_map):
    """Gap between a slot's best- and second-best-scoring candidate.

    Cruciform's account of Dr.Fill's own variable-selection heuristic (arXiv
    1611.02360, section on Dr.Fill; the underlying solver is Ginsberg's, arXiv
    1401.4597) picks the slot where this gap is LARGEST to commit first: a
    decisive slot (one clear leader) is unlikely to change its mind no matter
    what the rest of the grid does, while a slot with several near-tied
    candidates should wait for more crossing information before being forced.
    DAILY.md's 2026-11-12 research entry named this as a genuinely new,
    not-yet-built idea (found reading Cruciform directly, not just its title)
    and explicitly left it for a future run -- this is that run.

    A slot with zero candidates has no gap to measure (treated as the LEAST
    decisive, -inf, so it is picked last and never crashes the max-selection
    below). A slot with exactly one candidate is maximally decisive (+inf,
    picked first) -- there is nothing to be tied with, so by this heuristic's
    own logic it carries zero remaining uncertainty."""
    n = len(score_map)
    if n == 0:
        return float('-inf')
    if n == 1:
        return float('inf')
    top2 = sorted(score_map.values(), reverse=True)[:2]
    return top2[0] - top2[1]


def _apply_commit_bonus(grid, scores, key, answer, bonus=1000.0, penalty=-1000.0):
    """After committing `answer` for slot `key`, adjust every OTHER uncommitted
    slot's candidate scores at the cells they share with `key`: a candidate
    agreeing with the now-locked letter gets `bonus` (so it is very likely to
    be picked next, the whole point of letting a commit inform later picks);
    a candidate disagreeing gets `penalty` (so it is very unlikely to be
    picked, though -- unlike propagate()'s strict elimination -- it is never
    actually removed from the pool, same never-delete discipline
    soft_propagate() already established, since the committed answer could
    itself be wrong and a later audit may need the full pool intact).
    Mutates `scores` in place; returns nothing."""
    sl = G.slots(grid)
    crossmap = G.crossings(grid)
    cells = sl.get(key)
    if not cells:
        return
    for idx, cell in enumerate(cells):
        if idx >= len(answer):
            continue
        ch = answer[idx]
        for other_key in crossmap.get(cell, ()):
            if other_key == key or other_key not in scores:
                continue
            ocells = sl[other_key]
            oidx = ocells.index(cell)
            for cand in scores[other_key]:
                if oidx >= len(cand):
                    continue
                scores[other_key][cand] += bonus if cand[oidx] == ch else penalty


def simulate_sequential_commit(grid, cand_scores, gold=None, gap_order=True,
                                bonus=1000.0, penalty=-1000.0):
    """The actual incremental solve Dr.Fill/Cruciform describe and that
    `measure_soft()` never built: one slot at a time, pick-and-commit-and-
    propagate, rather than one flat batch scoring pass. At every step, the
    uncommitted slot with the largest `confidence_gap()` is committed next
    (`gap_order=True`, the heuristic under test) or -- for the controlled
    comparison -- slots are committed in a fixed, confidence-blind order
    (`gap_order=False`, sorted by (clue_number, direction), the simplest
    baseline a real solve loop could use instead). Either way the exact same
    scoring mechanism (`_apply_commit_bonus`) propagates each commit's
    letters to every other still-uncommitted slot before the next pick, so
    the comparison isolates ONE variable: does gap-based ORDERING (not the
    propagation itself) commit more gold answers, on the same real candidate
    pools this project's own recall@N has already measured?

    `gold`, if given ({key: norm_answer}), only used to ANNOTATE the trace
    (was_gold) for reporting -- it never influences which candidate is
    picked, by construction (checked by the selftest below).

    Returns a list of trace dicts in commit order:
      {'key', 'answer', 'was_gold' (or None if `gold` wasn't given),
       'rank_at_commit' (1-based rank of the committed answer among its OWN
       slot's live scores at the moment it was committed -- always 1, since
       the committed answer IS the top-scored one; kept for symmetry with
       measure_soft()'s rank reporting and as a sanity check)}."""
    scores = {k: dict(v) for k, v in cand_scores.items()}
    committed = set()
    trace = []
    remaining = {k for k, v in scores.items() if v}
    while remaining:
        if gap_order:
            pick = max(remaining, key=lambda k: (confidence_gap(scores[k]), k[0], k[1]))
        else:
            pick = min(remaining, key=lambda k: (k[0], k[1]))
        best_answer = max(scores[pick].items(), key=lambda kv: (kv[1], kv[0]))[0]
        was_gold = (gold.get(pick) == best_answer) if gold is not None else None
        trace.append({'key': pick, 'answer': best_answer, 'was_gold': was_gold,
                      'rank_at_commit': _rank_of(scores[pick], best_answer)})
        committed.add(pick)
        remaining.discard(pick)
        _apply_commit_bonus(grid, scores, pick, best_answer, bonus=bonus, penalty=penalty)
    return trace


def measure_commit_order(dataset_path, split=None, max_n=40, **gen_kwargs):
    """Honest before/after for queue item 4's own named next step (PR #119,
    2026-11-12 research entry): does Cruciform/Dr.Fill's confidence-gap
    variable-ordering heuristic, run as an actual sequential commit
    simulation (see `simulate_sequential_commit()`), commit more of a
    puzzle's gold answers than committing in a fixed, confidence-blind
    order -- on the exact same base candidate pools this project's own
    `candidates.py recall` already measured, so the comparison is isolated
    to the ordering policy alone, nothing else."""
    rows = [json.loads(l) for l in open(dataset_path)]
    if split:
        rows = [r for r in rows if r['split'] == split]
    by_puzzle = {}
    for r in rows:
        by_puzzle.setdefault(r['puzzle_date'], []).append(r)

    report = []
    for date, prows in sorted(by_puzzle.items()):
        grid_path = f'data/grids/{date}.json'
        try:
            grid = json.load(open(grid_path))['grid']
        except FileNotFoundError:
            continue
        gold = {(r['clue_number'], r['direction']): C.norm(r['answer_raw'])
                for r in prows if r.get('answer_raw')}
        cand_scores = build_candidate_lists_scored(grid, prows, max_n=max_n, **gen_kwargs)
        gold_in_pool = {k for k, g in gold.items()
                        if k in cand_scores and g in cand_scores[k]}

        trace_gap = simulate_sequential_commit(grid, cand_scores, gold=gold, gap_order=True)
        trace_fixed = simulate_sequential_commit(grid, cand_scores, gold=gold, gap_order=False)

        def correct_on_gold_slots(trace):
            by_key = {t['key']: t for t in trace}
            return sorted(k for k in gold_in_pool if by_key[k]['was_gold'])

        correct_gap = correct_on_gold_slots(trace_gap)
        correct_fixed = correct_on_gold_slots(trace_fixed)

        # Where a gold-bearing slot sits in each policy's commit ORDER (1-based
        # position in the trace) -- does gap-ordering actually commit the
        # gold-bearing slots earlier, which is the heuristic's own stated
        # rationale (commit decisive slots first), independent of whether the
        # committed answer is correct?
        order_gap = {t['key']: i + 1 for i, t in enumerate(trace_gap)}
        order_fixed = {t['key']: i + 1 for i, t in enumerate(trace_fixed)}

        report.append({
            'puzzle_date': date,
            'n_slots': len(cand_scores),
            'n_slots_with_gold_in_pool': len(gold_in_pool),
            'correct_commits_gap_order': correct_gap,
            'correct_commits_fixed_order': correct_fixed,
            'gap_order_better_on': sorted(set(correct_gap) - set(correct_fixed)),
            'fixed_order_better_on': sorted(set(correct_fixed) - set(correct_gap)),
            'gold_slot_commit_position_gap_order': {f'{k[0]}{k[1][0]}': order_gap[k] for k in gold_in_pool},
            'gold_slot_commit_position_fixed_order': {f'{k[0]}{k[1][0]}': order_fixed[k] for k in gold_in_pool},
        })
    return report


def selftest():
    """Synthetic fixtures only (no puzzle data) -- same discipline every
    other selftest in this repo follows: never embed held-out answers."""
    # 2x2 toy grid, two across words crossing two down words.
    # across1 (row0): cells (0,0)-(0,1); across2 (row1): (1,0)-(1,1)
    # down1 (col0 i.e. rightmost index 0... grid_tools indexes RTL, doesn't
    # matter for this synthetic check, only internal consistency does):
    grid = ['..', '..']
    sl = G.slots(grid)
    assert len(sl) == 4, f'expected 4 slots in a 2x2 open grid, got {len(sl)}: {sl}'

    # Build a tiny candidate pool by hand. Real answer set: אב / גד crossing
    # בג / אד at the shared cells (purely synthetic strings, not real words).
    # Grid (RTL, index0=rightmost): row0 = "אב", row1 = "גד"
    #   across (1,'across') = row0 cells -> "אב"
    #   across (3,'across') = row1 cells -> "גד"
    #   down slots share column cells with the across rows.
    keys = sorted(sl.keys())
    # Figure out the actual numbering grid_tools assigned.
    a_keys = [k for k in keys if k[1] == 'across']
    d_keys = [k for k in keys if k[1] == 'down']
    assert len(a_keys) == 2 and len(d_keys) == 2

    a0, a1 = a_keys
    d0, d1 = d_keys
    cells_a0 = sl[a0]
    cells_a1 = sl[a1]
    cells_d0 = sl[d0]
    cells_d1 = sl[d1]
    # Ground truth fill consistent at every shared cell.
    truth = {a0: 'אב', a1: 'גד'}
    # derive down truths from the across truth at the shared cells
    def word_for(cells, cellmap):
        return ''.join(cellmap[c] for c in cells)
    cellmap = {}
    for c, ch in zip(cells_a0, truth[a0]):
        cellmap[c] = ch
    for c, ch in zip(cells_a1, truth[a1]):
        cellmap[c] = ch
    truth[d0] = word_for(cells_d0, cellmap)
    truth[d1] = word_for(cells_d1, cellmap)

    # Candidate pools: the truth plus one DECOY per slot that is wrong and
    # shares no letters with any crossing truth at the shared cell.
    decoy = {a0: 'זח', a1: 'זח', d0: 'זח', d1: 'זח'}
    cand_lists = {k: {truth[k], decoy[k]} for k in keys}

    after, rounds_run, emptied = propagate(grid, cand_lists)
    assert not emptied, 'synthetic fixpoint should never empty a slot when the truth is mutually consistent'
    for k in keys:
        assert after[k] == {truth[k]}, f'{k}: expected arc consistency to force {truth[k]!r}, got {after[k]}'
    assert rounds_run >= 1

    # Second check: a candidate with NO support anywhere must be pruned even
    # when the slot it lives in has only decoys (tests empty-result path).
    cand_lists2 = {k: {decoy[k]} for k in keys}
    # decoys share no cell value with each other by construction (all 'ז'/'ח'
    # vs the crossing cell from truth)... construct a case with genuine
    # mutual inconsistency: two decoys of different first letters that must
    # agree at a shared cell.
    bad = {a0: 'זט', a1: 'חכ', d0: 'לל', d1: 'מצ'}
    cand_lists3 = {k: {bad[k]} for k in keys}
    after3, _, emptied3 = propagate(grid, cand_lists3)
    assert emptied3, 'mutually inconsistent singleton candidates must empty at least one slot'

    # --- soft_propagate() checks (never hard-deletes; re-ranks instead) ---
    # Check 4: equal base scores for truth and a decoy2 in every slot. decoy
    # (checks 1-3) reuses the SAME 2-letter string 'זח' in all four slots, which
    # can coincidentally self-agree at some crossing index -- fine for strict
    # propagate()'s pass/fail check, but not a clean "shares nothing" fixture for
    # a scoring test. decoy2 uses globally-unique letters (no letter repeated
    # across any slot) so it is GUARANTEED to get zero crossing support anywhere,
    # unlike truth (mutually consistent by construction). soft_propagate must
    # therefore rank truth #1 after scoring, even though it starts tied with
    # decoy2 and NEVER removes decoy2 from the pool.
    decoy2 = {a0: 'זח', a1: 'טכ', d0: 'סע', d1: 'פצ'}
    equal_scores = {k: {truth[k]: 1.0, decoy2[k]: 1.0} for k in keys}
    soft_after = soft_propagate(grid, equal_scores, rounds=2)
    for k in keys:
        assert set(soft_after[k]) == {truth[k], decoy2[k]}, \
            f'{k}: soft_propagate must never remove a candidate, got {soft_after[k]}'
        assert soft_after[k][truth[k]] > soft_after[k][decoy2[k]], (
            f'{k}: truth (mutually consistent) should outrank decoy2 (not) after '
            f'scoring, got truth={soft_after[k][truth[k]]} decoy2={soft_after[k][decoy2[k]]}')
        assert _rank_of(soft_after[k], truth[k]) == 1, f'{k}: truth should rank #1'

    # Check 5: the mutually-INCONSISTENT singleton case (check 2's `bad`, where
    # strict propagate() emptied a slot outright). soft_propagate on a single-
    # candidate-per-slot pool must still never remove anything -- cardinality
    # preserved even when nothing anywhere agrees with anything.
    bad_scores = {k: {bad[k]: 1.0} for k in keys}
    soft_bad = soft_propagate(grid, bad_scores, rounds=2)
    for k in keys:
        assert set(soft_bad[k]) == {bad[k]}, \
            f'{k}: soft_propagate must keep the sole candidate even with zero support'

    # --- real_word_support checks (queue item 4's PR #118 2026-11-11 next step) ---
    # Check 6: the construction guarantee (cardinality never changes) must hold under
    # real_word_support too, not just the default path.
    tied = {k: {truth[k]: 1.0, decoy[k]: 1.0} for k in keys}
    rw_after = soft_propagate(grid, tied, rounds=2, real_word_support=True)
    for k in keys:
        assert set(rw_after[k]) == {truth[k], decoy[k]}, \
            f'{k}: real_word_support=True must never remove a candidate either'

    # Check 7: the actual discriminator. Seed the cache (never touches the real
    # lexicon -- is_real_word() checks this cache before any file access, so this
    # stays a fully synthetic fixture) marking `truth` real and `decoy` not. `decoy`
    # reuses the identical string in all four slots, which -- as check 1-3's own
    # comment already notes -- lets it coincidentally self-agree with itself at
    # some crossings. That self-agreement is a direct model of PR #118's measured
    # bug: 357/988 (36.1%) of the real puzzle's pool are real words, so plain
    # "does anything agree with me" mostly counts noise agreeing with noise.
    # Confirm the fixture actually reproduces a false tie first (decoy, which is
    # WRONG, scoring equal to truth after plain propagation) -- otherwise this
    # check would be testing nothing.
    for k in keys:
        _REAL_WORD_CACHE[truth[k]] = True
        _REAL_WORD_CACHE[decoy[k]] = False
    plain_tied = soft_propagate(grid, tied, rounds=2, real_word_support=False)
    false_tie = [k for k in keys if plain_tied[k][truth[k]] == plain_tied[k][decoy[k]]]
    assert false_tie, ('fixture precondition failed: expected plain soft_propagate to '
                        'produce at least one false tie between truth and noise-decoy '
                        f'(got {plain_tied}) -- this check would test nothing otherwise')
    filtered_tied = soft_propagate(grid, tied, rounds=2, real_word_support=True)
    for k in keys:
        assert filtered_tied[k][truth[k]] > filtered_tied[k][decoy[k]], (
            f'{k}: with decoy marked non-real, truth should strictly outrank it after '
            f'filtered propagation (the false tie plain scoring produced), got {filtered_tied[k]}')

    # --- confidence_gap() / simulate_sequential_commit() checks (queue item 4's
    # own named next step, PR #119 2026-11-12 research entry: Cruciform's
    # confidence-gap variable-ordering heuristic, never built until now) ---

    # Check 8: confidence_gap()'s own edge cases, independent of any grid.
    assert confidence_gap({}) == float('-inf'), 'an empty pool has no gap -- least decisive'
    assert confidence_gap({'א': 1.0}) == float('inf'), 'a singleton pool is maximally decisive'
    assert confidence_gap({'א': 5.0, 'ב': 5.0}) == 0.0, 'a tie has zero gap'
    assert confidence_gap({'א': 9.0, 'ב': 5.0, 'ג': 1.0}) == 4.0, 'gap is top minus RUNNER-UP, not top minus worst'

    # Check 9: a hand-built case where gap-ordering provably helps, so this is a
    # positive capability proof independent of whatever today's real puzzle
    # measurement finds -- same discipline as check 4's decoy2 fixture for
    # soft_propagate(). Reuses THIS SAME function's own grid/truth fixture
    # above (a0 across, d0 down -- they share exactly one cell, since a0 spans
    # row 0 and d0 spans a single column). d0 is made DECISIVE (one candidate,
    # gap = +inf); a0's candidate pool has a DECOY that starts out-scoring the
    # truth (2.0 vs 1.0 -- modelling a real situation: candidates.py's own
    # generation-priority base score has no idea which candidate is gold, so a
    # wrong candidate legitimately outranking a right one pre-propagation is
    # the normal case, not a contrived one), differing from truth ONLY at the
    # cell shared with d0. Gap-order must commit d0 (the decisive slot) first
    # regardless of key order, so its bonus can swing a0's shared cell toward
    # truth and overturn the decoy's base-score lead; a fixed, confidence-
    # blind order that happens to commit a0 before d0 has no such information
    # yet and must commit the decoy.
    shared_cell = [c for c in cells_a0 if c in cells_d0][0]
    idx_in_a0 = cells_a0.index(shared_cell)
    wrong_letter = next(ch for ch in 'זחטיכ' if ch != truth[a0][idx_in_a0])
    decoy_a0 = list(truth[a0])
    decoy_a0[idx_in_a0] = wrong_letter
    decoy_a0 = ''.join(decoy_a0)
    assert decoy_a0 != truth[a0]
    scores9 = {d0: {truth[d0]: 1.0}, a0: {truth[a0]: 1.0, decoy_a0: 2.0}}

    trace_gap = simulate_sequential_commit(grid, scores9, gap_order=True)
    trace_fixed = simulate_sequential_commit(grid, scores9, gap_order=False)
    order_gap = [t['key'] for t in trace_gap]
    assert order_gap[0] == d0, f'gap-order must commit the decisive (singleton) slot first, got {order_gap}'
    gap_a0 = next(t for t in trace_gap if t['key'] == a0)
    assert gap_a0['answer'] == truth[a0], (
        f'gap-order: committing the decisive slot first should let its bonus overturn the '
        f'decoy\'s base-score lead, got {gap_a0["answer"]!r} (truth {truth[a0]!r})')
    order_fixed = [t['key'] for t in trace_fixed]
    assert order_fixed == sorted(order_fixed), 'fixed order must commit strictly by (clue_number, direction)'
    if order_fixed[0] == a0:
        # The informative case this fixture is built for: a0 sorts first, so
        # fixed order must commit by raw base score BEFORE d0 can inform it,
        # and the decoy's base score is higher -- so it must get it wrong.
        fixed_a0 = next(t for t in trace_fixed if t['key'] == a0)
        assert fixed_a0['answer'] == decoy_a0, (
            f'fixed order: a0 committed before d0 can inform it must pick the higher-base-score '
            f'decoy, got {fixed_a0["answer"]!r} -- if this changed, the fixture no longer '
            f'demonstrates anything and must be rebuilt')
        assert gap_a0['answer'] != fixed_a0['answer'], (
            'the whole point of this fixture: gap-order and fixed-order must DISAGREE on a0, '
            'with gap-order correct and fixed-order wrong')

    # Check 10: _apply_commit_bonus never DELETES a candidate (same
    # never-remove discipline as soft_propagate), it only rescales scores.
    probe = {a0: {truth[a0]: 1.0, decoy_a0: 1.0}}
    before_keys = set(probe[a0])
    _apply_commit_bonus(grid, probe, d0, truth[d0])
    assert set(probe[a0]) == before_keys, '_apply_commit_bonus must never remove a candidate'

    print('ALL PASSED (10 checks)')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'selftest':
        selftest()
    elif cmd == 'measure':
        dataset_path = sys.argv[2]
        split = sys.argv[3] if len(sys.argv) > 3 else None
        kwargs = {}
        for flag, key in (('--no-culture', 'use_culture'), ('--no-retrieval', 'use_retrieval'),
                           ('--no-gematria', 'use_gematria'), ('--no-container', 'use_container')):
            if flag in sys.argv:
                kwargs[key] = False
        for r in measure(dataset_path, split, **kwargs):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == 'measure-soft':
        dataset_path = sys.argv[2]
        split = sys.argv[3] if len(sys.argv) > 3 else None
        kwargs = {}
        for flag, key in (('--no-culture', 'use_culture'), ('--no-retrieval', 'use_retrieval'),
                           ('--no-gematria', 'use_gematria'), ('--no-container', 'use_container')):
            if flag in sys.argv:
                kwargs[key] = False
        for r in measure_soft(dataset_path, split, **kwargs):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == 'commit-order':
        dataset_path = sys.argv[2]
        split = sys.argv[3] if len(sys.argv) > 3 else None
        kwargs = {}
        for flag, key in (('--no-culture', 'use_culture'), ('--no-retrieval', 'use_retrieval'),
                           ('--no-gematria', 'use_gematria'), ('--no-container', 'use_container')):
            if flag in sys.argv:
                kwargs[key] = False
        for r in measure_commit_order(dataset_path, split, **kwargs):
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
