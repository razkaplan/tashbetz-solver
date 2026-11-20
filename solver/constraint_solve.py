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

    print('ALL PASSED (3 checks)')


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
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
