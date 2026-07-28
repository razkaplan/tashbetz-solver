import json, sys, os
P = 'evals/runs/v8b/2026-05-29.json'
rows = json.load(open(P)) if os.path.exists(P) else []
idx = {(r['clue_number'], r['direction']): r for r in rows}
# args: num dir answer conf explanation
n, d, a, c, e = int(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
FIN = str.maketrans('םןץףך', 'מנצפכ')
a = a.replace(' ', '').translate(FIN)
r = idx.get((n, d))
if r is None:
    r = {'puzzle_date': '2026-05-29', 'clue_number': n, 'direction': d}
    rows.append(r)
r['answer'] = a; r['explanation'] = e; r['confidence'] = c
rows.sort(key=lambda r: (r['clue_number'], r['direction']))
json.dump(rows, open(P, 'w'), ensure_ascii=False, indent=1)
print(len(rows), n, d, a, len(a), c)
