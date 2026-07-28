#!/usr/bin/env python3
"""Score solver outputs — PRECISION-FIRST metrics.

Policy (from the project owner): prefer a blank cell over a wrong one. A wrong answer
does not merely score zero, it writes wrong letters into crossings and corrupts
neighbouring clues. Blank is recoverable; wrong is contagious.

Answers come in three tiers, declared by the solver:
  committed  — asserted as correct (counts for precision)
  suggestion — plausible but unverified (reported separately, never grid-propagated)
  blank      — omitted or empty answer

Metrics:
  PRECISION = correct committed / committed          <- the headline number
  COVERAGE  = committed / total clues                <- how much it dared answer
  YIELD     = correct committed / total clues        <- accurate fulfilment overall
  SUGG-HIT  = correct suggestions / suggestions      <- is the uncertainty tier calibrated?

A solver that commits to 12 clues and gets 12 right (100% precision, 43% coverage,
43% yield) is preferred over one that answers 28 and gets 15 (54% precision, 100%
coverage, 54% yield) when the grid must stay clean for a later pass.

Usage: python3 evals/run_eval.py <solutions.json> [--split dev|eval]
Back-compat: entries with no "tier" are treated as committed if confidence >= 0.6,
otherwise as suggestions.
"""
import json, re, sys, os
from collections import defaultdict

FINALS = str.maketrans('ךםןףץ', 'כמנפצ')
COMMIT_THRESHOLD = 0.75

def norm(s):
    return re.sub(r'[^א-ת]', '', (s or '')).translate(FINALS)

def tier_of(entry):
    t = (entry.get('tier') or '').lower()
    if t in ('committed', 'suggestion', 'blank'):
        # enforce the commit bar even on self-declared commits: a solver may label an
        # answer 'committed' while reporting confidence below the policy threshold.
        if t == 'committed' and (entry.get('confidence') or 0) < COMMIT_THRESHOLD:
            return 'suggestion'
        return t
    if not norm(entry.get('answer')):
        return 'blank'
    return 'committed' if (entry.get('confidence') or 0) >= COMMIT_THRESHOLD else 'suggestion'

def load_gold(split=None):
    gold = {}
    for line in open('data/dataset/clues.jsonl'):
        r = json.loads(line)
        if split and r['split'] != split:
            continue
        gold[(r['puzzle_date'], r['clue_number'], r['direction'])] = r
    return gold

def main():
    sol_path = sys.argv[1]
    split = None
    if '--split' in sys.argv:
        split = sys.argv[sys.argv.index('--split') + 1]
    gold = load_gold(split)
    sols = json.load(open(sol_path))

    per = defaultdict(lambda: {'commit': 0, 'commit_ok': 0, 'sugg': 0, 'sugg_ok': 0, 'blank': 0, 'total': 0})
    errors, sugg_wrong = [], []
    seen = set()

    for s in sols:
        pd = s['puzzle_date']
        if '/' in pd:
            d, m, y = pd.split('/'); pd = f'{y}-{m}-{d}'
        key = (pd, s['clue_number'], s['direction'])
        g = gold.get(key)
        if not g:
            continue
        seen.add(key)
        p = per[pd]
        tier = tier_of(s)
        ok = norm(s.get('answer')) == norm(g['answer_raw'])
        if tier == 'committed':
            p['commit'] += 1
            p['commit_ok'] += ok
            if not ok:
                errors.append({'key': list(key), 'clue': g['clue_text'], 'enum': g['enum'],
                               'gold': g['answer_raw'], 'got': s.get('answer'),
                               'explanation': s.get('explanation'), 'confidence': s.get('confidence')})
        elif tier == 'suggestion':
            p['sugg'] += 1
            p['sugg_ok'] += ok
            if not ok:
                sugg_wrong.append([key[1], key[2], s.get('answer'), g['answer_raw']])
        else:
            p['blank'] += 1

    # restrict scoring to the puzzle dates this solution file actually covers
    dates = {k[0] for k in seen}
    for k in gold:
        if k[0] not in dates:
            continue
        per[k[0]]['total'] += 1
        if k not in seen:
            per[k[0]]['blank'] += 1

    T = {'commit': 0, 'commit_ok': 0, 'sugg': 0, 'sugg_ok': 0, 'blank': 0, 'total': 0}
    for pd in sorted(per):
        p = per[pd]
        for k in T:
            T[k] += p[k]
        prec = p['commit_ok'] / p['commit'] if p['commit'] else 0
        cov = p['commit'] / p['total'] if p['total'] else 0
        yld = p['commit_ok'] / p['total'] if p['total'] else 0
        print(f"{pd}: PRECISION {p['commit_ok']}/{p['commit']} = {prec:.0%} | "
              f"COVERAGE {cov:.0%} | YIELD {yld:.0%} | "
              f"suggestions {p['sugg_ok']}/{p['sugg']} | blank {p['blank']}")

    prec = T['commit_ok'] / T['commit'] if T['commit'] else 0
    cov = T['commit'] / T['total'] if T['total'] else 0
    yld = T['commit_ok'] / T['total'] if T['total'] else 0
    shit = T['sugg_ok'] / T['sugg'] if T['sugg'] else 0
    print(f"\nOVERALL  PRECISION {T['commit_ok']}/{T['commit']} = {prec:.1%}   "
          f"COVERAGE {T['commit']}/{T['total']} = {cov:.1%}   YIELD {yld:.1%}")
    print(f"         suggestion hit-rate {T['sugg_ok']}/{T['sugg']} = {shit:.0%}   blanks {T['blank']}")
    if T['commit'] and prec < 0.9:
        print(f"         [!] precision below 90% — {T['commit']-T['commit_ok']} wrong commitments "
              f"would corrupt crossings")

    rep = sol_path.replace('.json', '_errors.json')
    json.dump({'wrong_commitments': errors, 'wrong_suggestions': sugg_wrong},
              open(rep, 'w'), ensure_ascii=False, indent=1)
    print('error report:', rep)

if __name__ == '__main__':
    main()
