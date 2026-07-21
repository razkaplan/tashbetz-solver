#!/usr/bin/env python3
"""Join transcribed clues (data/clues/*.json) with answers (data/answers/by_date/*.json)
into data/dataset/clues.jsonl with train/dev/eval split by puzzle date."""
import json, glob, os, re, datetime

FINALS = str.maketrans('ךםןףץ', 'כמנפצ')

def heb_len(s):
    return len(re.sub(r'[^א-ת]', '', s))

def to_iso(d):  # dd/mm/yyyy -> yyyy-mm-dd
    dd, mm, yy = d.split('/')
    return f'{yy}-{mm}-{dd}'

def main():
    rows = []
    clue_files = sorted(glob.glob('data/clues/*.json'))
    for cf in clue_files:
        c = json.load(open(cf))
        iso = os.path.basename(cf).replace('.json', '')
        af = f'data/answers/by_date/{iso}.json'
        if not os.path.exists(af):
            print('no answers for', iso); continue
        a = json.load(open(af))
        amap = {(x['clue_number'], x['direction']): x for x in a['clues']}
        for direction in ('across', 'down'):
            for cl in c.get(direction, []):
                key = (cl['num'], direction)
                ans = amap.get(key)
                row = {
                    'puzzle_id': f'haaretz-yoram-{iso}',
                    'puzzle_date': iso,
                    'clue_number': cl['num'],
                    'direction': direction,
                    'clue_text': cl['clue'].strip(),
                    'enum': cl.get('enum', []),
                    'answer_raw': ans['answer'] if ans else None,
                    'answer_len': heb_len(ans['answer']) if ans else None,
                    'explanations_crowd': ans['explanations'] if ans else [],
                    'len_ok': (sum(cl.get('enum', [])) == heb_len(ans['answer'])) if ans else False,
                }
                rows.append(row)
    # split by date: newest 6 puzzles = eval, next 4 = dev, rest = train
    dates = sorted({r['puzzle_date'] for r in rows}, reverse=True)
    eval_d, dev_d = set(dates[:6]), set(dates[6:10])
    for r in rows:
        r['split'] = 'eval' if r['puzzle_date'] in eval_d else 'dev' if r['puzzle_date'] in dev_d else 'train'
    os.makedirs('data/dataset', exist_ok=True)
    with open('data/dataset/clues.jsonl', 'w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    n_bad = sum(1 for r in rows if not r['len_ok'])
    n_miss = sum(1 for r in rows if r['answer_raw'] is None)
    from collections import Counter
    print(f'{len(rows)} rows across {len(dates)} puzzles; len mismatches: {n_bad}; missing answers: {n_miss}')
    print(Counter(r['split'] for r in rows))

if __name__ == '__main__':
    main()
