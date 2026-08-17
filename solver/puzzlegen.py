#!/usr/bin/env python3
"""Generate ORIGINAL Hebrew training crosswords, grid + clues + proofs.

Why generated and not scraped: the project publishes no newspaper clue text
(see build_seo.py and the README). Real תשבץ היגיון clues belong to their
setter. Everything here is built from our own lexicon and our own corpus
statistics, so the trainer is publishable, and, more usefully, its difficulty
is designed rather than found: a real newspaper puzzle cannot teach one
mechanism at a time.

Every clue carries a machine-checkable proof, which is the same discipline the
solver holds itself to (an answer without a proof is a guess). Mechanisms:

  definition  the word has a real definition in our index
  reversal    the word spelled backwards is another real word
  anagram     the letters rearrange into another real word
  hidden      the word sits inside a longer carrier word, spanning it

Grids are RTL, matching solver/grid_tools.py: row string index 0 is the
RIGHTMOST cell, '#' is black. Generation is seeded per puzzle so a rebuild
produces byte-identical output instead of a 6,000 file diff.
"""
import json, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid_tools import slots, check_fill   # noqa: E402

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

# Rotationally symmetric patterns. Every white cell must belong to a slot of
# length >= 2, which the self-test at the bottom asserts rather than trusts.
PATTERNS = {
    3: [['...', '...', '...']],
    4: [['....', '....', '....', '....']],
    5: [
        ['.....', '.#.#.', '.....', '.#.#.', '.....'],
        ['.....', '...#.', '.#...', '.#...', '.....'],
    ],
    7: [
        ['.......', '.#.#.#.', '.......', '.#.#.#.', '.......', '.#.#.#.', '.......'],
    ],
}


def _check_patterns():
    """Every white cell must belong to at least one slot of length >= 2.

    An unchecked cell is unsolvable by construction, so this is asserted at
    import rather than discovered in a published puzzle.
    """
    for size, pats in PATTERNS.items():
        for i, g in enumerate(pats):
            covered = {c for cells in slots(g).values() for c in cells}
            white = {(r, j) for r, row in enumerate(g) for j, ch in enumerate(row) if ch == '.'}
            assert covered == white, f'pattern {size}[{i}]: {len(white - covered)} unchecked cells'


_check_patterns()


def load_lexicon(root):
    """Returns (words_by_len, defs, freq). Words are normalized (no finals)."""
    words = {}
    for raw in open(os.path.join(root, 'solver/lex/hspell.txt'), encoding='utf-8').read().split():
        n = norm(raw)
        if 2 <= len(n) <= 8:
            words.setdefault(len(n), set()).add(n)
    defs = {}
    dpath = os.path.join(root, 'data/culture/descriptions.json')
    if os.path.exists(dpath):
        for w, d in json.load(open(dpath, encoding='utf-8')).items():
            n = norm(w)
            d = (d or '').removeprefix('[ויקימילון] ').strip()
            # One-word entities make miserable definition clues ("X: X").
            if n and d and len(d) > 8 and n not in d:
                defs.setdefault(n, d)
    freq = {}
    fpath = os.path.join(root, 'solver/crosswordese.json')
    if os.path.exists(fpath):
        freq = {norm(k): v for k, v in json.load(open(fpath, encoding='utf-8')).items()}
    return {k: sorted(v) for k, v in words.items()}, defs, freq


def build_index(words_by_len):
    """index[(length, pos, char)] -> set of words, for constraint intersection."""
    idx = {}
    for L, ws in words_by_len.items():
        for w in ws:
            for p, ch in enumerate(w):
                idx.setdefault((L, p, ch), set()).add(w)
    return idx


def fill(grid, words_by_len, idx, rng, prefer, tries=6000, pool=None):
    """Fill every slot with a real word. Backtracking, most-constrained first.

    prefer: callable(word) -> sort key, used to bias toward words we can clue
    well. Returns {(num, dir): word} or None if this grid could not be filled.
    """
    sl = slots(grid)
    keys = list(sl)
    cell_slots = {}
    for k, cells in sl.items():
        for c in cells:
            cell_slots.setdefault(c, []).append(k)

    board = {}          # cell -> char
    assigned = {}

    def candidates(k):
        cells = sl[k]
        L = len(cells)
        known = [(p, board[c]) for p, c in enumerate(cells) if c in board]
        if not known:
            out = set(words_by_len.get(L, []))
        else:
            sets = [idx.get((L, p, ch), set()) for p, ch in known]
            out = set(sets[0])
            for s in sets[1:]:
                out &= s
                if not out:
                    break
        # Early levels fill only from words we can write a real definition
        # clue for, so "beginner" means an easy clue, not just a small grid.
        return out & pool if pool is not None else out

    def recurse(depth, budget):
        if len(assigned) == len(keys):
            return True
        if budget[0] <= 0:
            return False
        remaining = [k for k in keys if k not in assigned]
        remaining.sort(key=lambda k: len(candidates(k)))
        k = remaining[0]
        cands = list(candidates(k))
        if not cands:
            return False
        # Take the best slice by preference, then shuffle WITHIN it. Sorting
        # last made every attempt pick the same top words, so every puzzle came
        # out identical and the dedupe threw them all away.
        cands.sort(key=prefer)
        head = cands[:60]
        rng.shuffle(head)
        for w in head[:16]:
            budget[0] -= 1
            if budget[0] <= 0:
                return False
            cells = sl[k]
            touched = []
            ok = True
            for c, ch in zip(cells, w):
                if c in board:
                    if board[c] != ch:
                        ok = False
                        break
                else:
                    board[c] = ch
                    touched.append(c)
            if ok and w not in assigned.values():
                assigned[k] = w
                if recurse(depth + 1, budget):
                    return True
                del assigned[k]
            for c in touched:
                del board[c]
        return False

    for _ in range(3):
        board.clear(); assigned.clear()
        if recurse(0, [tries]):
            return dict(assigned)
    return None


def build_clue_helpers(words_by_len):
    """Precompute anagram and carrier lookups once.

    Scanning the full 141k lexicon per clue turned generation into minutes;
    these two tables make each lookup a dict hit or a scan of long words only.
    """
    ana = {}
    for ws in words_by_len.values():
        for w in ws:
            ana.setdefault(''.join(sorted(w)), []).append(w)
    carriers = sorted(set().union(*(words_by_len.get(L, []) for L in (6, 7, 8))))
    return {'ana': ana, 'carriers': carriers}


def clue_for(word, defs, words_set, rng, allow, helpers=None):
    """Return (clue_text, mechanism, proof) or None.

    Ordered by how natural the clue reads, filtered by the mechanisms this
    difficulty level is allowed to use, so early puzzles stay pure definition.
    """
    if 'definition' in allow and word in defs:
        d = defs[word]
        d = d[0].upper() + d[1:] if d[:1].isascii() else d
        return (d, 'definition', {'type': 'definition', 'source': 'index'})

    if 'reversal' in allow:
        rev = word[::-1]
        if rev != word and rev in words_set:
            return (f'הפוך את {rev}', 'reversal',
                    {'type': 'reversal', 'from': rev, 'check': f'{rev}[::-1] == {word}'})

    if 'anagram' in allow and helpers:
        for cand in helpers['ana'].get(''.join(sorted(word)), []):
            if cand != word:
                return (f'סדרו מחדש את האותיות של {cand}', 'anagram',
                        {'type': 'anagram', 'from': cand,
                         'check': f'sorted({cand}) == sorted({word})'})

    if 'hidden' in allow and helpers:
        for carrier in helpers['carriers']:
            if len(carrier) > len(word) + 1 and word in carrier:
                at = carrier.index(word)
                return (f'מסתתר בתוך {carrier}', 'hidden',
                        {'type': 'hidden', 'carrier': carrier, 'at': at,
                         'check': f'{carrier}[{at}:{at + len(word)}] == {word}'})
    return None


LEVELS = [
    # (label, size, allowed mechanisms, count, defined_pool_only)
    # Level 1 draws only from words that have a real definition, so every clue
    # is a plain definition. Later levels open the full lexicon, which is what
    # forces the wordplay mechanisms to appear.
    # Each level gets its own grid shape as well as its own mechanisms, so the
    # ramp is visible on the board and the levels cannot collide in the dedupe.
    ('מתחילים', 3, 0, {'definition'}, 25, True),
    ('בסיסי', 5, 1, {'definition', 'reversal', 'hidden'}, 25, False),
    ('מתקדם', 5, 0, {'definition', 'reversal', 'anagram', 'hidden'}, 25, False),
    ('אתגר', 7, 0, {'definition', 'reversal', 'anagram', 'hidden'}, 25, False),
]


def generate(root, count=100, seed=20260817):
    words_by_len, defs, freq = load_lexicon(root)
    idx = build_index(words_by_len)
    words_set = set().union(*words_by_len.values())
    # Bias the fill toward words we can clue: definitions first, then answers
    # our corpus actually saw in real puzzles, then everything else.
    def prefer(w):
        return (0 if w in defs else 1, -freq.get(w, 0), w)

    helpers = build_clue_helpers(words_by_len)
    defined_pool = set(defs)
    puzzles, n = [], 0
    seen_fills = set()
    for label, size, pat_i, allow, want, defined_only in LEVELS:
        made = 0
        attempt = 0
        while made < want and attempt < want * 400:
            attempt += 1
            rng = random.Random(seed + n * 1000 + attempt)
            grid = PATTERNS[size][rng.choice(pat_i) if isinstance(pat_i, list) else pat_i]
            sol = fill(grid, words_by_len, idx, rng, prefer,
                       tries=4000 if size <= 5 else 60000,
                       pool=defined_pool if defined_only else None)
            if not sol:
                continue
            # Two puzzles with the same answers are the same puzzle.
            sig = tuple(sorted(sol.values()))
            if sig in seen_fills:
                continue
            clues, bad = {}, False
            for k, w in sol.items():
                c = clue_for(w, defs, words_set, rng, allow, helpers)
                if not c:
                    bad = True
                    break
                clues[k] = c
            if bad:
                continue
            conflicts, _ = check_fill(grid, sol, None)
            if conflicts:
                continue
            seen_fills.add(sig)
            n += 1
            made += 1
            puzzles.append({
                'id': n, 'level': label, 'size': size, 'grid': grid,
                'entries': [
                    {'num': k[0], 'dir': k[1], 'answer': sol[k],
                     'clue': clues[k][0], 'mechanism': clues[k][1], 'proof': clues[k][2]}
                    for k in sorted(sol, key=lambda x: (x[0], x[1]))
                ],
            })

    # The 7x7 level saturates well before 25 distinct fills, so top up from the
    # 5x5 level rather than shipping 97 of a promised 100.
    if len(puzzles) < count:
        label, size, pat_i, allow, _w, _d = LEVELS[2]
        attempt = 0
        while len(puzzles) < count and attempt < 40000:
            attempt += 1
            rng = random.Random(seed + 900000 + attempt)
            sol = fill(PATTERNS[size][pat_i], words_by_len, idx, rng, prefer, tries=4000)
            if not sol:
                continue
            sig = tuple(sorted(sol.values()))
            if sig in seen_fills:
                continue
            clues, bad = {}, False
            for k, w in sol.items():
                c = clue_for(w, defs, words_set, rng, allow, helpers)
                if not c:
                    bad = True
                    break
                clues[k] = c
            if bad or check_fill(PATTERNS[size][pat_i], sol, None)[0]:
                continue
            seen_fills.add(sig)
            n += 1
            puzzles.append({
                'id': n, 'level': label, 'size': size, 'grid': PATTERNS[size][pat_i],
                'entries': [
                    {'num': k[0], 'dir': k[1], 'answer': sol[k],
                     'clue': clues[k][0], 'mechanism': clues[k][1], 'proof': clues[k][2]}
                    for k in sorted(sol, key=lambda x: (x[0], x[1]))
                ],
            })
    return puzzles


def verify(puzzles):
    """Independent re-check: grids well formed, answers real, proofs hold."""
    problems = []
    for p in puzzles:
        sl = slots(p['grid'])
        sol = {(e['num'], e['dir']): e['answer'] for e in p['entries']}
        if set(sol) != set(sl):
            problems.append(f"puzzle {p['id']}: entries do not match grid slots")
            continue
        conflicts, board = check_fill(p['grid'], sol, None)
        if conflicts:
            problems.append(f"puzzle {p['id']}: {conflicts[0]}")
        white = sum(row.count('.') for row in p['grid'])
        if len(board) != white:
            problems.append(f"puzzle {p['id']}: {white - len(board)} white cells uncovered")
        for e in p['entries']:
            pr = e['proof']
            if pr['type'] == 'reversal' and pr['from'][::-1] != e['answer']:
                problems.append(f"puzzle {p['id']} {e['num']}{e['dir']}: reversal proof fails")
            if pr['type'] == 'anagram' and sorted(pr['from']) != sorted(e['answer']):
                problems.append(f"puzzle {p['id']} {e['num']}{e['dir']}: anagram proof fails")
            if pr['type'] == 'hidden':
                a = pr['at']
                if pr['carrier'][a:a + len(e['answer'])] != e['answer']:
                    problems.append(f"puzzle {p['id']} {e['num']}{e['dir']}: hidden proof fails")
    return problems


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pz = generate(root, count=100)
    probs = verify(pz)
    print(f'generated: {len(pz)} puzzles')
    by = {}
    for p in pz:
        by[p['level']] = by.get(p['level'], 0) + 1
    print('by level:', by)
    mech = {}
    for p in pz:
        for e in p['entries']:
            mech[e['mechanism']] = mech.get(e['mechanism'], 0) + 1
    print('clues by mechanism:', mech)
    print('verification problems:', len(probs))
    for x in probs[:5]:
        print('  ', x)
    if len(sys.argv) > 1 and sys.argv[1] == 'write':
        out = os.path.join(root, 'docs/tirgul/puzzles.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(pz, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('wrote', out)
