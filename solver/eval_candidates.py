#!/usr/bin/env python3
"""Recall@N for the candidate generator against a transcribed puzzle's real answers.

This does NOT feed gold answers into candidates.py — lexicon.py already excludes
every dev/eval answer from its own wordlist (held_out_answers), so the generator
structurally cannot see them. This script only compares its output to gold AFTER
generation, offline, exactly like evals/run_eval.py compares a solver's committed
answers to gold. That is measurement, not leakage.

Usage: python3 solver/eval_candidates.py <puzzle-date> [--top N]
Requires data/clues/<date>.json and data/answers/by_date/<date>.json to exist.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidates

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def main():
    date = sys.argv[1]
    top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 50
    os.chdir(os.path.dirname(HERE))
    clues = json.load(open(f'data/clues/{date}.json'))
    answers = json.load(open(f'data/answers/by_date/{date}.json'))
    amap = {(c['clue_number'], c['direction']): c['answer'] for c in answers['clues']}

    hits, total, by_mech = 0, 0, {}
    for direction in ('across', 'down'):
        for c in clues.get(direction, []):
            gold = norm(amap.get((c['num'], direction), ''))
            if not gold:
                continue
            cands = candidates.generate(c['clue'], c['enum'], top=top)
            found = next((x for x in cands if x['answer'] == gold), None)
            total += 1
            status = 'HIT' if found else '--'
            if found:
                hits += 1
                by_mech[found['mechanism']] = by_mech.get(found['mechanism'], 0) + 1
            print(f"{status}  {c['num']:>2} {direction:<6} {gold:<12} "
                  f"{len(cands)} candidates" + (f"  via {found['mechanism']}" if found else ''))

    print(f"\nRECALL@{top}: {hits}/{total} = {hits/total:.0%}" if total else 'no clues scored')
    if by_mech:
        print('hits by mechanism:', by_mech)

if __name__ == '__main__':
    main()
