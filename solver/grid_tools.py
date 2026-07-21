#!/usr/bin/env python3
"""Grid tools for Hebrew (RTL) crosswords.

Grid representation: list of N strings, one per row (top to bottom).
Each string is read in RTL cell order: index 0 = RIGHTMOST cell of the row.
'.' = white cell, '#' = black cell.

Numbering follows standard crossword rules adapted to RTL: scan rows top to
bottom, cells right to left (i.e., string index ascending). A white cell gets a
number if it starts an across slot (no white cell to its right, i.e. index-1)
and/or starts a down slot (no white cell above), with slot length >= 2.

Usage:
  python3 solver/grid_tools.py validate <grid.json> <clues_input.json>
grid.json: {"grid": ["....#....", ...]}
Checks: computed numbering == printed clue numbers, slot lengths == enum sums.
"""
import json, sys


def slots(grid):
    """Return {(num, 'across'|'down'): [(r, i), ...]} cell lists in reading order."""
    nrows, ncols = len(grid), len(grid[0])
    out, num = {}, 0
    for r in range(nrows):
        for i in range(ncols):
            if grid[r][i] == '#':
                continue
            starts_a = (i == 0 or grid[r][i-1] == '#') and i + 1 < ncols and grid[r][i+1] == '.'
            starts_d = (r == 0 or grid[r-1][i] == '#') and r + 1 < nrows and grid[r+1][i] == '.'
            if starts_a or starts_d:
                num += 1
            if starts_a:
                cells = []
                j = i
                while j < ncols and grid[r][j] == '.':
                    cells.append((r, j)); j += 1
                out[(num, 'across')] = cells
            if starts_d:
                cells = []
                k = r
                while k < nrows and grid[k][i] == '.':
                    cells.append((k, i)); k += 1
                out[(num, 'down')] = cells
    return out


def validate(grid, clues):
    """clues: {'across': [{'num','enum'},...], 'down': [...]}. Returns list of problems."""
    problems = []
    ncols = len(grid[0])
    if any(len(row) != ncols for row in grid):
        return ['ragged rows']
    sl = slots(grid)
    want = {}
    for d in ('across', 'down'):
        for c in clues[d]:
            want[(c['num'], d)] = sum(c['enum'])
    got = {k: len(v) for k, v in sl.items()}
    for k in sorted(set(want) | set(got)):
        if k not in got:
            problems.append(f'{k}: printed clue but grid has no such slot')
        elif k not in want:
            problems.append(f'{k}: grid slot (len {got[k]}) but no printed clue')
        elif want[k] != got[k]:
            problems.append(f'{k}: enum sum {want[k]} != slot length {got[k]}')
    return problems


def crossings(grid):
    """Return {cell: [slot_keys]} for constraint propagation."""
    cellmap = {}
    for key, cells in slots(grid).items():
        for c in cells:
            cellmap.setdefault(c, []).append(key)
    return cellmap


def check_fill(grid, solutions, clues):
    """solutions: {(num, dir): answer_str}. Returns conflicts list where crossing
    letters disagree. Answer strings are unspaced, index 0 = first letter."""
    sl = slots(grid)
    board = {}
    conflicts = []
    for key, ans in solutions.items():
        cells = sl.get(key)
        if not cells:
            conflicts.append(f'{key}: no slot'); continue
        if len(ans) != len(cells):
            conflicts.append(f'{key}: answer len {len(ans)} != slot {len(cells)}'); continue
        for cell, ch in zip(cells, ans):
            if cell in board and board[cell][0] != ch:
                conflicts.append(f'{key} vs {board[cell][1]} at {cell}: {ch} != {board[cell][0]}')
            else:
                board[cell] = (ch, key)
    return conflicts, board


if __name__ == '__main__':
    if sys.argv[1] == 'validate':
        g = json.load(open(sys.argv[2]))['grid']
        c = json.load(open(sys.argv[3]))
        probs = validate(g, c)
        print('OK' if not probs else '\n'.join(probs))
        sys.exit(0 if not probs else 1)
