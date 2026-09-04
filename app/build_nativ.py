#!/usr/bin/env python3
"""Build daily puzzles for נתיב (docs/nativ/puzzles.json).

For each day: take the day's theme from the rotation in app/nativ_pools.py,
pick 4 words (4-8 letters each, normalized non-final Hebrew) from that theme's
curated pool whose lengths sum to exactly 20 (5x4) or 25 (5x5), then lay the
concatenated letters along a random self-avoiding path that visits every cell
exactly once (4-directional orthogonal adjacency - no diagonals, backtracking
search). Easy mode builds the same way with 3 words on a 4x4 or 4x5 board.

Every word carries a one-line description, so the easy board can print a clue
per word and the finished board can name what each answer was. Validates every
puzzle before writing, and refuses to build if any pooled word fails to
resolve against its source.
"""
import json
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nativ_pools import POOLS, THEMES, ROTATION, FILLBANK_CATS

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "docs" / "milon" / "entities.json"
FILLBANK = ROOT / "solver" / "lex" / "fillbank.json"
OUT = ROOT / "docs" / "nativ" / "puzzles.json"

START = date(2026, 8, 16)
DAYS = 90
WORDS_PER_PUZZLE = 4
MIN_LEN, MAX_LEN = 4, 8
COLS = 5
# 5x4 and 5x5. The old 6x5 board did not fit a phone screen together with the
# clue list, and 30 letters over 4 words demanded a 7.5-letter average that
# only obscure long names could supply.
TOTALS = (20, 25)

# Easy mode (נתיב קל): smaller board, fewer words, and every word must carry a
# description so the player gets a clue up front. Generated with its own rng and
# used-set so the regular puzzles stay byte-identical across rebuilds.
EASY_WORDS = 3
EASY_COLS = 4
EASY_TOTALS = (16, 20)  # 4x4, or 4x5 when a thinner pool cannot tile 16
# Word pools, themes and the day rotation now live in app/nativ_pools.py: the
# milon is an exhaustive crossword reference, so drawing a daily board straight
# from it served names nobody could produce. Both modes draw from the curated
# pools; difficulty comes from the board, not from obscurity.

# The kibbutz theme says "kibbutzim and moshavim", so it accepts both milon
# categories; every other theme maps to the milon category of the same name.
ENTITY_SOURCES = {"kibbutz": ("kibbutz", "moshav")}

HEB_ONLY = re.compile(r"^[\u05d0-\u05ea]+$")
FINALS = set("\u05da\u05dd\u05df\u05e3\u05e5")
FIN_TR = str.maketrans("\u05da\u05dd\u05df\u05e3\u05e5", "\u05db\u05de\u05e0\u05e4\u05e6")


def _norm(s):
    return re.sub(r"[^\u05d0-\u05ea]", "", s or "").translate(FIN_TR)


def load_candidates():
    """Resolve every pooled name to {n, t, d} against its source.

    Fails loudly on anything that does not resolve: a pool entry that silently
    vanished would shrink a day's choices without anyone noticing, which is how
    the boards drifted into obscurity in the first place.
    """
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_cat = {}
    for e in entities:
        by_cat.setdefault(e.get("c"), {}).setdefault(_norm(e.get("t", "")), e)
    fillbank = json.loads(FILLBANK.read_text(encoding="utf-8"))
    fb_by_norm = {}
    for word, desc in fillbank.items():
        if HEB_ONLY.match(word):
            fb_by_norm.setdefault(_norm(word), (word, desc))

    cands, broken = {}, []
    for cat, names in POOLS.items():
        bucket = {}
        for name in names:
            n = _norm(name)
            if not (MIN_LEN <= len(n) <= MAX_LEN) or set(n) & FINALS:
                broken.append(f"{cat}/{name}: unusable length {len(n)}")
                continue
            if cat in FILLBANK_CATS:
                hit = fb_by_norm.get(n)
                if not hit:
                    broken.append(f"{cat}/{name}: not in fillbank.json")
                    continue
                display, desc = hit
            else:
                rec = None
                for src in ENTITY_SOURCES.get(cat, (cat,)):
                    rec = by_cat.get(src, {}).get(n)
                    if rec:
                        break
                if not rec:
                    broken.append(f"{cat}/{name}: not in entities.json")
                    continue
                display, desc = rec.get("t", name), rec.get("d", "")
            if not desc:
                broken.append(f"{cat}/{name}: no description")
                continue
            bucket.setdefault(n, {"n": n, "t": display, "d": desc})
        cands[cat] = list(bucket.values())
    if broken:
        sys.exit("pool entries that do not resolve:\n  " + "\n  ".join(broken))
    return cands


def neighbors(rows, cols):
    adj = []
    for i in range(rows * cols):
        r, c = divmod(i, cols)
        cur = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                cur.append(nr * cols + nc)
        adj.append(cur)
    return adj


def hamiltonian_path(rows, cols, rng, restarts=60, budget=80000):
    """Random self-avoiding path visiting every cell exactly once."""
    n = rows * cols
    adj = neighbors(rows, cols)
    for _ in range(restarts):
        start = rng.randrange(n)
        path = [start]
        used = {start}
        nodes = [budget]

        def dfs():
            if nodes[0] <= 0:
                return False
            nodes[0] -= 1
            if len(path) == n:
                return True
            nbrs = [x for x in adj[path[-1]] if x not in used]
            rng.shuffle(nbrs)
            for x in nbrs:
                path.append(x)
                used.add(x)
                if dfs():
                    return True
                path.pop()
                used.remove(x)
            return False

        if dfs():
            return path
    return None


def pick_words(cands, total, rng, used_global, n_words=WORDS_PER_PUZZLE,
               forbid=frozenset()):
    """Pick n_words distinct words with lengths summing to total.
    Prefer words not used on earlier days; never pick words in forbid."""
    pool = [e for e in cands if e["n"] not in forbid]
    order = sorted(pool, key=lambda e: (e["n"] in used_global, rng.random()))

    def dfs(start, chosen, s):
        if len(chosen) == n_words:
            return list(chosen) if s == total else None
        for i in range(start, len(order)):
            e = order[i]
            length = len(e["n"])
            rem = n_words - len(chosen) - 1
            if s + length + rem * MIN_LEN > total:
                continue
            if s + length + rem * MAX_LEN < total:
                continue
            chosen.append(e)
            r = dfs(i + 1, chosen, s + length)
            if r:
                return r
            chosen.pop()
        return None

    return dfs(0, [], 0)


def validate(puzzle):
    rows, cols = puzzle["rows"], puzzle["cols"]
    n = rows * cols
    path = puzzle["path"]
    grid = puzzle["grid"]
    assert len(grid) == n, "grid size mismatch"
    assert len(path) == n, "path length mismatch"
    assert sorted(path) == list(range(n)), "path must visit each cell exactly once"
    for a, b in zip(path, path[1:]):
        ra, ca = divmod(a, cols)
        rb, cb = divmod(b, cols)
        assert abs(ra - rb) + abs(ca - cb) == 1, "path cells must be orthogonally adjacent (no diagonals)"
    letters = "".join(grid[i] for i in path)
    assert letters == "".join(w["n"] for w in puzzle["words"]), "path letters must spell the words"
    for w in puzzle["words"]:
        assert MIN_LEN <= len(w["n"]) <= MAX_LEN, "word length out of range"


def build_day(day_index, cands, rng, used_global, n_words=WORDS_PER_PUZZLE,
              cols=COLS, day_totals=TOTALS, forbid=frozenset()):
    cat = ROTATION[day_index % len(ROTATION)]
    theme, emoji = THEMES[cat]
    totals = list(day_totals)
    rng.shuffle(totals)
    for total in totals:
        for _attempt in range(40):
            words = pick_words(cands[cat], total, rng, used_global, n_words,
                               forbid)
            if not words:
                break
            rows = total // cols
            path = hamiltonian_path(rows, cols, rng)
            if not path:
                continue
            letters = "".join(w["n"] for w in words)
            grid = [""] * total
            for pos, cell in enumerate(path):
                grid[cell] = letters[pos]
            puzzle = {
                "cat": cat,
                "theme": theme,
                "emoji": emoji,
                "rows": rows,
                "cols": cols,
                "grid": grid,
                "words": words,
                "path": path,
            }
            validate(puzzle)
            for w in words:
                used_global.add(w["n"])
            return puzzle
    return None


def main():
    cands = load_candidates()
    missing = [c for c in ROTATION if not cands.get(c)]
    if missing:
        sys.exit(f"no candidates for categories: {missing}")

    rng = random.Random("nativ-v2")
    used_global = set()
    days = {}
    stats = {}
    for i in range(DAYS):
        d = (START + timedelta(days=i)).isoformat()
        puzzle = build_day(i, cands, rng, used_global)
        if puzzle is None:
            sys.exit(f"FAILED to build puzzle for {d}")
        days[d] = puzzle
        stats[puzzle["cat"]] = stats.get(puzzle["cat"], 0) + 1

    # Easy mode: separate rng + used-set. Same day-theme as the regular puzzle;
    # the day's regular words are forbidden so the two boards never share a
    # word. Both modes draw from the same curated pool - easy differs by a
    # smaller board, one word fewer, and a clue printed under every slot.
    easy_rng = random.Random("nativ-easy-v1")
    easy_used = set()
    easy = {}
    for i in range(DAYS):
        d = (START + timedelta(days=i)).isoformat()
        day_words = frozenset(w["n"] for w in days[d]["words"])
        puzzle = build_day(i, cands, easy_rng, easy_used, n_words=EASY_WORDS,
                           cols=EASY_COLS, day_totals=EASY_TOTALS,
                           forbid=day_words)
        if puzzle is None:
            sys.exit(f"FAILED to build easy puzzle for {d}")
        easy[d] = puzzle

    out = {"start": START.isoformat(), "days": days, "easy": easy}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # re-validate everything from disk
    reread = json.loads(OUT.read_text(encoding="utf-8"))
    for d, p in reread["days"].items():
        validate(p)
    for d, p in reread["days"].items():
        assert all(w.get("d") for w in p["words"]), f"{d}: word without a clue"
    for d, p in reread["easy"].items():
        validate(p)
        assert all(w.get("d") for w in p["words"]), f"easy {d}: word without clue"

    sizes = {}
    for p in days.values():
        key = f"{p['rows']}x{p['cols']}"
        sizes[key] = sizes.get(key, 0) + 1
    print(f"OK: {len(days)} puzzles validated -> {OUT}")
    print(f"grid sizes: {sizes}")
    print(f"distinct words used: {len(used_global)}")
    print("category counts:", dict(sorted(stats.items())))


if __name__ == "__main__":
    main()
