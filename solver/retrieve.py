#!/usr/bin/env python3
"""Retrieve similar solved clues from the corpus to few-shot the solver.

Similarity = shared content words + shared mechanism-indicator words, over the
TRAIN + SECONDARY corpora only (never dev/eval — no leakage). Each hit shows the
clue, answer, and its crowd explanation (the reasoning to imitate).

CLI: python3 solver/retrieve.py "<clue text>" [k]
"""
import sys, os, re, json, glob
from collections import Counter

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
STOP = set('של עם על אל את זה הוא היא לא כי גם או אבל אם כמו יש אין מה מי'.split())

def toks(s):
    return [w for w in re.findall(r'[א-ת]+', s or '') if w not in STOP and len(w) > 1]

def load_pool():
    pool = []
    # main corpus: only train/dev? we must exclude dev+eval puzzle dates.
    evaldev = set()
    if os.path.exists('data/dataset/clues.jsonl'):
        for line in open('data/dataset/clues.jsonl'):
            r = json.loads(line)
            if r['split'] in ('dev', 'eval'):
                evaldev.add(r['puzzle_date'])
    # main corpus has clue text only via data/clues/*.json joined w/ answers; use dataset
    if os.path.exists('data/dataset/clues.jsonl'):
        for line in open('data/dataset/clues.jsonl'):
            r = json.loads(line)
            if r['split'] == 'train' and r.get('clue_text') and r.get('answer_raw'):
                pool.append((r['clue_text'], r['answer_raw'], r.get('explanations_crowd', [])))
    # secondary corpus has NO clue text (answers site only) — skip for text retrieval,
    # but its explanations are keyed to answers; not usable without clue text. Skipped.
    return pool

def main():
    clue = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    q = Counter(toks(clue))
    pool = load_pool()
    scored = []
    for text, ans, expl in pool:
        c = Counter(toks(text))
        overlap = sum((q & c).values())
        if overlap:
            scored.append((overlap, text, ans, expl))
    scored.sort(key=lambda x: -x[0])
    for ov, text, ans, expl in scored[:k]:
        e = expl[0] if expl else ''
        print(f'[{ov}] {text}  => {ans}   | {e}')
    if not scored:
        print('(no similar clue found)')

if __name__ == '__main__':
    main()
