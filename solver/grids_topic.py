#!/usr/bin/env python3
"""The four grid templates the topic-crossword product is built on.

Two regular crosswords (תשבץ) and two arrowwords (תשחץ). Same RTL convention
as solver/grid_tools.py: row string index 0 is the RIGHTMOST cell, '#' is a
non-letter cell.

The difference between the two families is where the clue text lives:

  regular   clues are printed beside the grid, numbered. '#' is a plain black
            cell. A slot may start at the grid edge.
  arrowword clues are printed INSIDE the grid: '#' is a clue cell, and the
            entry it introduces starts in the neighbouring cell, marked by an
            arrow. An across entry is hosted by the cell to its right (RTL:
            string index-1, arrow pointing left); a down entry by the cell
            above it (arrow pointing down). So in an arrowword no entry may
            start at the top row or the right edge, and one clue cell carries
            at most one across clue and one down clue.

Every template is checked at import rather than trusted: an unhosted entry or
an uncheckable cell is a puzzle nobody can solve, and that is not something to
discover after publishing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid_tools import slots   # noqa: E402

# ---------------------------------------------------------------- regular

# Both are 180-degree rotationally symmetric, every cell checked in both
# directions, and no entry longer than 6. The length ceiling is the point: a
# curated topic bank has plenty of 4- and 5-letter answers and almost no
# 9-letter ones, so a board full of long entries can only be filled with
# filler, which is the opposite of a topic crossword.
REGULAR = {
    # 16 entries, 3 to 5 letters. The small board: one sitting, ~10 minutes.
    'classic7': [
        '.#.....',
        '....#.#',
        '.#.....',
        '...#...',
        '.....#.',
        '#.#....',
        '.....#.',
    ],
    # 32 entries, 3 to 6 letters, 16% black. The full board.
    'classic9': [
        '.....#...',
        '...#.....',
        '.....#...',
        '###......',
        '....#....',
        '......###',
        '...#.....',
        '.....#...',
        '...#.....',
    ],
}

# ---------------------------------------------------------------- arrowword

# Found by hill-climbing under the hosting rules below, then frozen. Clue-cell
# density (~35%) is what a printed תשחץ actually looks like: the clues live in
# the board, so the board needs room for them.
ARROW = {
    # 26 entries, 2 to 6 letters.
    'arrow9': [
        '#########',
        '#....#...',
        '#....#...',
        '###......',
        '#...##...',
        '#.....#.#',
        '#......#.',
        '#..#.....',
        '#.#......',
    ],
    # 33 entries, 2 to 6 letters. The big board: a full-page תשחץ.
    'arrow11': [
        '#########',
        '#...#....',
        '#...#....',
        '#......#.',
        '#...##...',
        '#.....#..',
        '#..#.....',
        '###.....#',
        '#......#.',
        '#...#....',
        '#..#.....',
    ],
}

SHAPES = {**{k: ('regular', v) for k, v in REGULAR.items()},
          **{k: ('arrow', v) for k, v in ARROW.items()}}


def host_of(slot_key, cells):
    """The cell that must carry an arrowword clue for this entry."""
    r, i = cells[0]
    return (r, i - 1) if slot_key[1] == 'across' else (r - 1, i)


def arrow_hosts(grid):
    """{(num, dir): host_cell} for an arrowword grid. Raises if unhostable.

    Also enforces one across clue and one down clue per cell: a printed clue
    cell has room for two clues, not three.
    """
    out, load = {}, {}
    for key, cells in slots(grid).items():
        h = host_of(key, cells)
        if h[0] < 0 or h[1] < 0:
            raise AssertionError(f'{key} starts at the board edge: no cell can host its clue')
        if grid[h[0]][h[1]] != '#':
            raise AssertionError(f'{key} would be hosted by the letter cell {h}')
        load.setdefault(h, set())
        if key[1] in load[h]:
            raise AssertionError(f'cell {h} would carry two {key[1]} clues')
        load[h].add(key[1])
        out[key] = h
    return out


def idle_cells(grid):
    """Clue cells that introduce no entry - rendered as plain blocks."""
    used = set(arrow_hosts(grid).values())
    return [(r, i) for r, row in enumerate(grid)
            for i, ch in enumerate(row) if ch == '#' and (r, i) not in used]


def audit(name):
    """Shape facts a caller (or an eval) can assert against."""
    kind, grid = SHAPES[name]
    sl = slots(grid)
    white = {(r, i) for r, row in enumerate(grid)
             for i, ch in enumerate(row) if ch == '.'}
    covered = {c for cells in sl.values() for c in cells}
    lens = sorted(len(v) for v in sl.values())
    info = {'name': name, 'kind': kind, 'rows': len(grid), 'cols': len(grid[0]),
            'entries': len(sl), 'lens': lens, 'white': len(white),
            'unchecked': sorted(white - covered),
            'blocks': sum(row.count('#') for row in grid)}
    if kind == 'arrow':
        info['idle'] = idle_cells(grid)
    return info


def _self_check():
    for name in SHAPES:
        kind, grid = SHAPES[name]
        assert len({len(r) for r in grid}) == 1, f'{name}: ragged rows'
        info = audit(name)
        assert not info['unchecked'], \
            f"{name}: {len(info['unchecked'])} cells belong to no entry"
        assert info['lens'][0] >= 2, f'{name}: 1-letter entry'
        if kind == 'regular':
            n, m = len(grid), len(grid[0])
            assert all(grid[r][i] == grid[n - 1 - r][m - 1 - i]
                       for r in range(n) for i in range(m)), f'{name}: not symmetric'
        else:
            arrow_hosts(grid)   # raises on any unhostable entry


_self_check()


if __name__ == '__main__':
    for name in SHAPES:
        info = audit(name)
        print(f"{name}  {info['kind']}  {info['rows']}x{info['cols']}  "
              f"entries={info['entries']}  lens={info['lens']}")
        print('  blocks=%d white=%d%s' % (
            info['blocks'], info['white'],
            f"  idle-clue-cells={len(info['idle'])}" if 'idle' in info else ''))
        print('\n'.join(SHAPES[name][1]))
        print()
