#!/usr/bin/env python3
"""Emit pass-2 seed patterns: place committed answers on the grid, then report the
letter pattern now known for every unsolved slot.

Only `committed` answers are placed. Suggestions and blanks are never propagated —
that is the whole point of the precision-first policy: the board a second pass builds
on is guaranteed clean.

Usage: python3 solver/pass2_patterns.py <date> <run_dir> [<run_dir> ...]
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid_tools import slots

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s): return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def main():
    date = sys.argv[1]
    run_dirs = sys.argv[2:]
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    grid = json.load(open(f'data/grids/{date}.json'))['grid']
    sl = slots(grid)
    clues = json.load(open(f'data/dataset/inputs/{date}.json'))
    ctext = {}
    for d in ('across', 'down'):
        for c in clues[d]:
            ctext[(c['num'], d)] = (c['clue'], c['enum'])

    board, placed = {}, {}
    for rd in run_dirs:
        p = f'{rd}/{date}.json'
        if not os.path.exists(p):
            continue
        for s in json.load(open(p)):
            if (s.get('tier') or '').lower() != 'committed':
                continue
            key = (s['clue_number'], s['direction'])
            a = norm(s.get('answer'))
            cells = sl.get(key)
            if not cells or len(a) != len(cells):
                continue
            if any(board.get(c, a[i]) != a[i] for i, c in enumerate(cells)):
                print(f'# CONFLICT skipped {key}', file=sys.stderr); continue
            for i, c in enumerate(cells):
                board[c] = a[i]
            placed[key] = s.get('answer')

    print(f'# {date}: {len(placed)} verified anchors placed, {len(board)} letters known')
    print('# SOLVED (do not re-solve):')
    for k in sorted(placed):
        print(f'#   {k[0]} {k[1]}: {placed[k]}')
    print('\n# UNSOLVED SLOTS — pattern shows letters already fixed by verified anchors:')
    out = []
    for key, cells in sorted(sl.items()):
        if key in placed:
            continue
        pat = ''.join(board.get(c, '?') for c in cells)
        known = sum(1 for ch in pat if ch != '?')
        txt, en = ctext.get(key, ('', []))
        out.append((known, key, pat, txt, en))
    for known, key, pat, txt, en in sorted(out, key=lambda x: -x[0]):
        mark = '  <-- attack first' if known >= 2 else ''
        print(f'{key[0]:>2} {key[1]:<6} enum={en} known={known} pattern={pat}{mark}')
        print(f'     clue: {txt}')

if __name__ == '__main__':
    main()
