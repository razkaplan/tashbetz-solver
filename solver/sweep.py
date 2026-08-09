#!/usr/bin/env python3
"""Sweep worklist (lever 1, SweepClip-inspired; recalibrated by measurement 2026-08-08).

MEASURED on the two live puzzles: promoting a suggestion because it fits 2+ committed
crossings was 1/5 correct (e.g. קלינטון fit the crossings of gold קריפטון), and an as-if
promotion chain poisoned later patterns exactly as the precision rule predicts. So this
tool does NOT promote. It emits a RE-CRACK WORKLIST: every unsolved slot, ranked by how
many verified letters it now has, with its pattern, the surviving-or-dead status of the
engine's old suggestion, and any unique lexicon fit (flagged as a lead, not an answer).
The agent re-cracks the top slots WITH the letters and must pass prove.py as always.

CLI:
  python3 solver/sweep.py report <puzzle.json> <engine.json>
"""
import json, os, re, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'solver')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

_LEX = None
def lex():
    global _LEX
    if _LEX is None:
        import lexicon
        _LEX = set(lexicon.load())
    return _LEX

def load(puzzle_path, engine_path):
    p = json.load(open(puzzle_path))
    e = json.load(open(engine_path))
    ents = e['entries'] if isinstance(e, dict) else e
    return p, ents

def key(c): return f"{c['clue_number']}-{c['direction']}"

def sweep_once(p, ents):
    cells = {}
    for c in ents:
        if c.get('tier') == 'committed' and c.get('answer'):
            for (r, col), ch in zip(p['slots'][key(c)], norm(c['answer'])):
                cells[(r, col)] = ch
    out = []
    committed = {key(c) for c in ents if c.get('tier') == 'committed'}
    for c in ents:
        k = key(c)
        if k in committed or k not in p['slots']:
            continue
        slot = p['slots'][k]
        pat = ''.join(cells.get((r, col), '.') for r, col in slot)
        crossings = sum(ch != '.' for ch in pat)
        sugg = norm(c.get('answer', '')) if c.get('tier') == 'suggestion' else ''
        sugg_state = ''
        if sugg:
            alive = len(sugg) == len(slot) and all(pc in ('.', sc) for pc, sc in zip(pat, sugg))
            sugg_state = f'old suggestion {sugg} ' + ('still fits (weak evidence!)' if alive
                          else 'CONTRADICTED by crossings - discard')
        lead = ''
        if crossings >= max(2, len(slot) // 2):
            rx = re.compile('^' + pat.replace('.', '[א-ת]') + '$')
            fits = [w for w in lex() if len(w) == len(slot) and rx.match(w)]
            if 1 <= len(fits) <= 5:
                lead = 'lexicon leads: ' + ', '.join(fits)
        out.append({'slot': k, 'pattern': pat, 'crossings': crossings,
                    'suggestion': sugg_state, 'lead': lead, 'clue': c.get('clue', '')})
    return sorted(out, key=lambda x: -x['crossings'])

def main():
    p, ents = load(sys.argv[2], sys.argv[3])
    print(json.dumps({'recrack': sweep_once(p, ents)}, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
