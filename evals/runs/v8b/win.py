import sys, json, re
FIN = str.maketrans('םןץףך', 'מנצפכ')
inp = json.load(open('data/dataset/inputs/2026-05-29.json'))
clues = [(c['num'], 'across', c['clue'], sum(c['enum'])) for c in inp['across']] + \
        [(c['num'], 'down', c['clue'], sum(c['enum'])) for c in inp['down']]
sel = sys.argv[1:] if len(sys.argv) > 1 else None
for num, d, text, L in clues:
    key = f"{num}{d[0]}"
    if sel and key not in sel:
        continue
    t = re.sub(r'\(עפ"י[^)]*\)|\(מחדושי[^)]*\)|\([מח]\)', ' ', text)
    words = [w for w in re.sub(r'[^֐-ת ]', ' ', t).split() if w]
    out = []
    for i in range(len(words)):
        for j in range(i+1, min(i+6, len(words))+1):
            s = ''.join(words[i:j]).translate(FIN)
            if abs(len(s) - L) <= 1:
                out.append((len(s)-L, ' '.join(words[i:j]), s))
    print(f"--- {num} {d} L={L}: {text}")
    for delta, w, s in out:
        print(f"   d={delta:+d} [{w}] -> {s}")
