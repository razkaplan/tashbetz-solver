#!/usr/bin/env python3
"""Fold real solving sessions back into the engine — the learning loop of the assistant UI.

Every UI session logs to data/sessions/<pid>.jsonl: hints requested, wrong attempts,
confirmed answers. That is exactly the supervision the solver lacks:

  confirmed answers    -> new (clue, answer) pairs: crosswordese counts, lexicon entries,
                          and rows for data/dataset/live_confirmed.jsonl (future fine-tune)
  wrong attempts       -> negative examples: which plausible-looking candidates humans
                          reject (feeds the candidate-generation lever)
  hint usage           -> difficulty signal: a clue that needed level-4/5 hints is HARD;
                          hard-clue clusters tell the playbook where its explanations fail
  human beat engine    -> the gold nuggets: clues where the engine was blank/wrong but the
                          human solved it. These become priority worked examples.

Run:  python3 solver/learn_from_sessions.py          # report + apply
      python3 solver/learn_from_sessions.py --dry    # report only
"""
import json, os, re, sys, glob
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s): return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def main():
    dry = '--dry' in sys.argv
    confirmed, wrong, hard, beat_engine = [], [], Counter(), []
    for f in glob.glob('data/sessions/*.jsonl'):
        pid = os.path.basename(f)[:-6]
        puzfile = f'app/puzzles/{pid}/puzzle.json'
        engfile = f'app/puzzles/{pid}/engine.json'
        clues = {}
        if os.path.exists(puzfile):
            p = json.load(open(puzfile))
            for d in ('across', 'down'):
                for c in p['clues'][d]:
                    clues[(c['num'], d)] = c
        engine = {}
        if os.path.exists(engfile):
            for e in json.load(open(engfile)):
                engine[(e['clue_number'], e['direction'])] = e
        for line in open(f):
            ev = json.loads(line)
            key = (ev.get('num'), ev.get('dir'))
            clue = clues.get(key, {})
            if ev.get('t') == 'user_answer':
                v = ev.get('verdict', {})
                ok = v.get('engine_agrees') is True or (v.get('ok') and v.get('in_lexicon'))
                row = {'pid': pid, 'num': key[0], 'dir': key[1],
                       'clue': clue.get('clue'), 'enum': clue.get('enum'),
                       'answer': norm(ev.get('answer')),
                       'hints_spent': ev.get('hints_spent', 0)}
                if ok:
                    confirmed.append(row)
                    if ev.get('hints_spent', 0) >= 50:
                        hard[row['clue'] or ''] += 1
                    eng = engine.get(key, {})
                    if eng.get('tier') in (None, 'blank') or \
                       (norm(eng.get('answer', '')) and norm(eng.get('answer', '')) != row['answer']):
                        beat_engine.append(row)
                else:
                    wrong.append(row)

    print(f'sessions: {len(glob.glob("data/sessions/*.jsonl"))}')
    print(f'confirmed answers: {len(confirmed)}  | wrong attempts: {len(wrong)}'
          f'  | human-beat-engine: {len(beat_engine)}')
    if dry or not confirmed:
        return

    # 1. crosswordese counts
    cw_path = 'solver/crosswordese.json'
    cw = json.load(open(cw_path)) if os.path.exists(cw_path) else {}
    for r in confirmed:
        if r['answer']:
            cw[r['answer']] = cw.get(r['answer'], 0) + 1
    json.dump(cw, open(cw_path, 'w'), ensure_ascii=False)

    # 2. training rows (clue text + confirmed answer) — future fine-tune / retrieval
    os.makedirs('data/dataset', exist_ok=True)
    with open('data/dataset/live_confirmed.jsonl', 'a') as out:
        for r in confirmed:
            if r['clue'] and r['answer']:
                out.write(json.dumps(r, ensure_ascii=False) + '\n')

    # 3. negative examples for the candidate generator
    with open('data/dataset/live_rejected.jsonl', 'a') as out:
        for r in wrong:
            if r['clue'] and r['answer']:
                out.write(json.dumps(r, ensure_ascii=False) + '\n')

    # 4. human-beat-engine: the priority study list
    if beat_engine:
        with open('data/dataset/beat_engine.jsonl', 'a') as out:
            for r in beat_engine:
                out.write(json.dumps(r, ensure_ascii=False) + '\n')
        print('\nClues where the human beat the engine (add to playbook examples):')
        for r in beat_engine[:10]:
            print(f"  {r['num']} {r['dir']}: {r['clue']}  -> {r['answer']}")
    print('\napplied: crosswordese updated, live_confirmed/rejected appended')

if __name__ == '__main__':
    main()
