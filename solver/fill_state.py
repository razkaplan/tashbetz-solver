#!/usr/bin/env python3
"""Show grid fill state from a partial solutions file.

Usage: python3 solver/fill_state.py <date> [min_confidence]
Reads data/grids/<date>.json and evals/runs/dev_v2/<date>.json (if it exists).
Fills answers with confidence >= min_confidence (default 0.6) into the grid,
reports conflicts, then prints for every clue its current letter pattern
('?' = unknown), pct of letters known, sorted by most-known-first.
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from grid_tools import slots

def main():
    date = sys.argv[1]
    minc = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
    run_dir = os.environ.get('RUN_DIR', 'evals/runs/dev_v2')
    grid = json.load(open(f'data/grids/{date}.json'))['grid']
    sl = slots(grid)
    sol_path = f'{run_dir}/{date}.json'
    sols = json.load(open(sol_path)) if os.path.exists(sol_path) else []
    board = {}
    conflicts = []
    for s in sols:
        if (s.get('confidence') or 0) < minc or not s.get('answer'):
            continue
        key = (s['clue_number'], s['direction'])
        cells = sl.get(key)
        if not cells:
            conflicts.append(f'{key}: no such slot'); continue
        if len(s['answer']) != len(cells):
            conflicts.append(f'{key}: len {len(s["answer"])} != slot {len(cells)}'); continue
        for cell, ch in zip(cells, s['answer']):
            if cell in board and board[cell][0] != ch:
                conflicts.append(f'{key} conflicts with {board[cell][1]} at {cell}: {ch} vs {board[cell][0]}')
            else:
                board[cell] = (ch, key)
    if conflicts:
        print('CONFLICTS (fix these first):')
        for c in conflicts:
            print(' ', c)
    have = {(s['clue_number'], s['direction']): s.get('confidence', 0) for s in sols}
    rows = []
    for key, cells in sl.items():
        pat = ''.join(board.get(c, ('?',))[0] for c in cells)
        known = sum(1 for c in cells if c in board)
        rows.append((known / len(cells), key, pat, have.get(key)))
    rows.sort(key=lambda r: (-r[0], r[1]))
    print('pattern per clue (most-known first): num dir pattern known% your_conf')
    for frac, key, pat, conf in rows:
        print(f'  {key[0]:>2} {key[1]:<6} {pat}  {frac:.0%}  {"-" if conf is None else conf}')

if __name__ == '__main__':
    main()
