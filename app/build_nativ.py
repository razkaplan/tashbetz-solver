#!/usr/bin/env python3
"""Build daily puzzles for נתיב (docs/nativ/puzzles.json).

For each day: pick a themed category from the milon, pick 4 entity names
(4-8 letters each, normalized non-final Hebrew) whose lengths sum to exactly
25 (5x5) or 30 (6x5), then lay the concatenated letters along a random
self-avoiding path that visits every cell exactly once (8-directional
adjacency, backtracking search). Validates every puzzle before writing.
"""
import json
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "docs" / "milon" / "entities.json"
OUT = ROOT / "docs" / "nativ" / "puzzles.json"

START = date(2026, 8, 16)
DAYS = 90
WORDS_PER_PUZZLE = 4
MIN_LEN, MAX_LEN = 4, 8
COLS = 5
TOTALS = (25, 30)  # 5x5 or 6x5

ROTATION = [
    "artist", "nation", "city_il", "mountain", "bible", "kibbutz",
    "politician", "athlete", "author", "actor", "world_city", "common",
]

THEMES = {
    "artist": ("כולם זמרים ולהקות", "🎤"),
    "nation": ("כולן מדינות", "🌍"),
    "city_il": ("כולם יישובים בישראל", "🏙️"),
    "mountain": ("כולם הרים", "⛰️"),
    "bible": ("כולם מהתנ\"ך", "📜"),
    "kibbutz": ("כולם קיבוצים", "🌾"),
    "politician": ("כולם פוליטיקאים", "🏛️"),
    "athlete": ("כולם ספורטאים", "🏅"),
    "author": ("כולם סופרים", "📚"),
    "actor": ("כולם שחקנים", "🎬"),
    "world_city": ("כולן ערים בעולם", "🗺️"),
    "common": ("מילים וביטויים מהמילון", "✏️"),
}

HEB_ONLY = re.compile(r"^[א-ת]+$")
FINALS = set("ךםןףץ")


def load_candidates():
    data = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_cat = {}
    for e in data:
        cat = e.get("c")
        if cat not in THEMES:
            continue
        n = e.get("n", "")
        if not HEB_ONLY.match(n) or set(n) & FINALS:
            continue
        if not (MIN_LEN <= len(n) <= MAX_LEN):
            continue
        bucket = by_cat.setdefault(cat, {})
        if n not in bucket:  # dedupe by normalized name
            bucket[n] = {"n": n, "t": e.get("t", n), "d": e.get("d", "")}
    return {cat: list(v.values()) for cat, v in by_cat.items()}


def neighbors(rows, cols):
    adj = []
    for i in range(rows * cols):
        r, c = divmod(i, cols)
        cur = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
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


def pick_words(cands, total, rng, used_global):
    """Pick WORDS_PER_PUZZLE distinct words with lengths summing to total.
    Prefer words not used on earlier days."""
    order = sorted(cands, key=lambda e: (e["n"] in used_global, rng.random()))

    def dfs(start, chosen, s):
        if len(chosen) == WORDS_PER_PUZZLE:
            return list(chosen) if s == total else None
        for i in range(start, len(order)):
            e = order[i]
            length = len(e["n"])
            rem = WORDS_PER_PUZZLE - len(chosen) - 1
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
        assert max(abs(ra - rb), abs(ca - cb)) == 1, "path cells must be adjacent"
    letters = "".join(grid[i] for i in path)
    assert letters == "".join(w["n"] for w in puzzle["words"]), "path letters must spell the words"
    for w in puzzle["words"]:
        assert MIN_LEN <= len(w["n"]) <= MAX_LEN, "word length out of range"


def build_day(day_index, cands, rng, used_global):
    cat = ROTATION[day_index % len(ROTATION)]
    theme, emoji = THEMES[cat]
    totals = list(TOTALS)
    rng.shuffle(totals)
    for total in totals:
        for _attempt in range(40):
            words = pick_words(cands[cat], total, rng, used_global)
            if not words:
                break
            rows = total // COLS
            path = hamiltonian_path(rows, COLS, rng)
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
                "cols": COLS,
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

    rng = random.Random("nativ-v1")
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

    out = {"start": START.isoformat(), "days": days}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # re-validate everything from disk
    reread = json.loads(OUT.read_text(encoding="utf-8"))
    for d, p in reread["days"].items():
        validate(p)

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
