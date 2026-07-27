#!/usr/bin/env python3
"""Detect and fix reversed enumerations.

The newspaper prints multi-word enumerations inside RTL text, so the digit tuple's
visual order does not always match the answer's word order. Transcription agents
normalized this per-puzzle by eye and got it backwards on some puzzles, which
systematically misleads the solver about where word boundaries fall.

Automatic test: split the gold answer at the boundaries implied by enum and by
reversed(enum); score each split by how many pieces are real Hebrew words
(hspell + culture entities). The better-scoring orientation wins.

Usage:
  python3 solver/fix_enums.py report      # per-puzzle orientation verdict
  python3 solver/fix_enums.py apply       # rewrite data/dataset/inputs/*.json
"""
import json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lexicon

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s): return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def split_by(ans, enum):
    out, i = [], 0
    for n in enum:
        out.append(ans[i:i+n]); i += n
    return out

def score(words, pieces):
    """How many pieces are real words (prefix-tolerant: Hebrew glues ה/ו/ב/ל/מ/ש/כ)."""
    s = 0
    for p in pieces:
        if len(p) < 2:
            s += 0.5; continue
        if p in words:
            s += 1
        elif any(p[1:] in words for _ in [0]) and p[0] in 'הובלמשכ':
            s += 0.8
        elif any(p[k:] in words for k in (1, 2)):
            s += 0.4
    return s

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mode = sys.argv[1] if len(sys.argv) > 1 else 'report'
    words = lexicon.load()
    gold = {}
    for line in open('data/dataset/clues.jsonl'):
        r = json.loads(line)
        gold[(r['puzzle_date'], r['clue_number'], r['direction'])] = norm(r['answer_raw'] or '')

    verdicts = {}
    for f in sorted(glob.glob('data/dataset/inputs/*.json')):
        date = os.path.basename(f)[:-5]
        d = json.load(open(f))
        fwd = rev = 0.0
        n_multi = 0
        for direction in ('across', 'down'):
            for c in d.get(direction, []):
                e = c.get('enum') or []
                if len(e) < 2:
                    continue
                a = gold.get((date, c['num'], direction), '')
                if not a or sum(e) != len(a):
                    continue
                n_multi += 1
                fwd += score(words, split_by(a, e))
                rev += score(words, split_by(a, list(reversed(e))))
        if n_multi:
            verdicts[date] = ('REVERSED' if rev > fwd + 0.5 else 'ok', round(fwd, 1), round(rev, 1), n_multi)

    bad = [d for d, v in verdicts.items() if v[0] == 'REVERSED']
    for d in sorted(verdicts):
        v = verdicts[d]
        flag = '  <-- REVERSED' if v[0] == 'REVERSED' else ''
        print(f'{d}: fwd={v[1]:5} rev={v[2]:5} n={v[3]:2}{flag}')
    print(f'\n{len(bad)}/{len(verdicts)} puzzles have reversed enumerations')

    if mode == 'apply' and bad:
        for date in bad:
            f = f'data/dataset/inputs/{date}.json'
            d = json.load(open(f))
            for direction in ('across', 'down'):
                for c in d.get(direction, []):
                    if len(c.get('enum') or []) > 1:
                        c['enum'] = list(reversed(c['enum']))
            json.dump(d, open(f, 'w'), ensure_ascii=False, indent=1)
        print(f'fixed {len(bad)} puzzles')

if __name__ == '__main__':
    main()
