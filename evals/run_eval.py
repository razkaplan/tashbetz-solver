#!/usr/bin/env python3
"""Score solver outputs against gold answers.

Usage: python3 evals/run_eval.py <solutions.json> [--split dev|eval]
solutions.json: [{"puzzle_date": "2026-07-17"|"dd/mm/yyyy", "clue_number": 1,
                  "direction": "across", "answer": "...", "explanation": "..."}]
Scoring: exact match on normalized answer (Hebrew letters only, final forms folded).
Prints per-puzzle and overall accuracy; writes an error report next to input.
"""
import json, re, sys, os
from collections import defaultdict

FINALS = str.maketrans('ךםןףץ', 'כמנפצ')

def norm(s):
    return re.sub(r'[^א-ת]', '', (s or '')).translate(FINALS)

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
    per = defaultdict(lambda: [0, 0])
    errors = []
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
        ok = norm(s.get('answer')) == norm(g['answer_raw'])
        per[pd][1] += 1
        per[pd][0] += ok
        if not ok:
            errors.append({'key': list(key), 'clue': g['clue_text'], 'enum': g['enum'],
                           'gold': g['answer_raw'], 'got': s.get('answer'),
                           'solver_explanation': s.get('explanation'),
                           'crowd_explanation': g['explanations_crowd'][:2]})
    unanswered = [k for k in gold if k not in seen]
    tot_ok = sum(v[0] for v in per.values())
    tot = sum(v[1] for v in per.values()) + len(unanswered)
    for pd in sorted(per):
        ok, n = per[pd]
        print(f'{pd}: {ok}/{n} = {ok/n:.0%}')
    print(f'OVERALL: {tot_ok}/{tot} = {tot_ok/max(tot,1):.1%} (unanswered: {len(unanswered)})')
    rep = sol_path.replace('.json', '_errors.json')
    json.dump({'errors': errors, 'unanswered': [list(k) for k in unanswered]},
              open(rep, 'w'), ensure_ascii=False, indent=1)
    print('error report:', rep)

if __name__ == '__main__':
    main()
