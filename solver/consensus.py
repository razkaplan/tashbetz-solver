#!/usr/bin/env python3
"""Merge N independent solver runs into a consensus, grid-checked.

For each clue, tally normalized answers across runs. An answer is a TRUSTED anchor
if >=2 runs agree on it. We then greedily place anchors on the grid most-agreed
first, skipping any that conflict with already-placed letters. Remaining clues are
filled from the highest-confidence single-run answer that fits the current pattern.

Usage: python3 solver/consensus.py <date> <run_dir1> <run_dir2> ... > out.json
Writes a consensus solutions array to stdout (also usable by run_eval).
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from grid_tools import slots

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s): return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def main():
    date = sys.argv[1]
    run_dirs = sys.argv[2:]
    grid = json.load(open(f'data/grids/{date}.json'))['grid']
    sl = slots(grid)
    # gather per-clue candidates across runs
    cand = {}  # key -> list of (answer_norm, confidence, explanation, raw)
    for rd in run_dirs:
        p = f'{rd}/{date}.json'
        if not os.path.exists(p): continue
        for s in json.load(open(p)):
            key = (s['clue_number'], s['direction'])
            a = norm(s.get('answer'))
            if key in sl and len(a) == len(sl[key]):
                cand.setdefault(key, []).append((a, s.get('confidence', 0), s.get('explanation', ''), s.get('answer')))
    # tally agreement
    scored = []
    for key, lst in cand.items():
        from collections import Counter
        cnt = Counter(a for a, _, _, _ in lst)
        top, votes = cnt.most_common(1)[0]
        best = max((x for x in lst if x[0] == top), key=lambda x: x[1])
        scored.append({'key': key, 'answer': top, 'votes': votes, 'nruns': len(lst),
                       'conf': best[1], 'expl': best[2], 'raw': best[3]})
    # place anchors: agreed (votes>=2) first, then by confidence
    scored.sort(key=lambda x: (-(x['votes'] >= 2), -x['votes'], -x['conf']))
    board = {}
    placed = {}
    for it in scored:
        cells = sl[it['key']]
        ok = all(board.get(c, it['answer'][i]) == it['answer'][i] for i, c in enumerate(cells))
        if ok:
            for i, c in enumerate(cells):
                board[c] = it['answer'][i]
            placed[it['key']] = it
    # any clue not placed (lost a conflict): re-pick a candidate that fits current board
    out = []
    for key, cells in sl.items():
        if key in placed:
            it = placed[key]
            out.append({'puzzle_date': date, 'clue_number': key[0], 'direction': key[1],
                        'answer': it['raw'], 'explanation': it['expl'],
                        'confidence': it['conf'], 'votes': it['votes']})
            continue
        # pick any candidate consistent with board, else top-voted
        chosen = None
        for a, conf, expl, raw in sorted(cand.get(key, []), key=lambda x: -x[1]):
            if all(board.get(c, a[i]) == a[i] for i, c in enumerate(cells)):
                chosen = (a, conf, expl, raw); break
        if not chosen and cand.get(key):
            a, conf, expl, raw = max(cand[key], key=lambda x: x[1]); chosen = (a, conf, expl, raw)
        if chosen:
            a, conf, expl, raw = chosen
            for i, c in enumerate(cells):
                board.setdefault(c, a[i])
            out.append({'puzzle_date': date, 'clue_number': key[0], 'direction': key[1],
                        'answer': raw, 'explanation': expl, 'confidence': conf, 'votes': 1})
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
