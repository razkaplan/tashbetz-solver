#!/usr/bin/env python3
"""Ranked retrieval over definition->answer pairs (lever 2, Berkeley-style QA).

Index: private_defs (note.co.il + mordo crawls) + our own train-split clue->answer pairs
and their crowd explanations. Dev/eval answers are NEVER indexed (held-out rule, same as
lexicon.py). Query = clue text; result = answers of the wanted length, ranked by BM25
over word tokens + de-prefixed stems.

CLI:
  python3 solver/retrieve.py candidates "<clue>" <len>     # ranked answers
  python3 solver/retrieve.py eval                          # dev-split hit-rate (honest)
"""
import json, math, os, re, sys, glob
from collections import defaultdict

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)
PREFIXES = ('וה','שה','כש','מה','לה','בה','ו','ב','ל','מ','ש','כ','ה')
STOP = set('של עם על אל את זה זו זאת הוא היא לא כמו או גם יש אין מי מה כך פי אם'.split())

def toks(s):
    out = []
    for w in re.findall(r'[א-ת]+', s or ''):
        if len(w) < 2 or w in STOP: continue
        out.append(w)
        for p in PREFIXES:
            if w.startswith(p) and len(w) - len(p) >= 2:
                out.append(w[len(p):]); break
    return out

def held_out():
    ho = set()
    for line in open('data/dataset/clues.jsonl'):
        c = json.loads(line)
        if c.get('split') in ('dev', 'eval'):
            ho.add(norm(c['answer_raw']))
    return ho

def build_index(exclude_puzzle=None):
    ho = held_out()
    docs = []                                   # (tokens, answers, source_puzzle)
    # private defs are independent external knowledge (like a crossword dictionary):
    # held-out does NOT apply. It applies only to our own corpus pairings below.
    for f in glob.glob('data/answers/private_defs/*.jsonl'):
        for line in open(f):
            r = json.loads(line)
            ans = [norm(a) for a in r.get('answers', []) if norm(a)]
            if ans:
                docs.append((toks(r.get('definition', '')), ans, None))
    for line in open('data/dataset/clues.jsonl'):
        c = json.loads(line)
        if c.get('split') != 'train': continue
        a = norm(c['answer_raw'])
        if a in ho: continue
        text = c['clue_text'] + ' ' + ' '.join(c.get('explanations_crowd', []))
        docs.append((toks(text), [a], c['puzzle_id']))
    df = defaultdict(int)
    for t, _, _ in docs:
        for w in set(t): df[w] += 1
    return docs, df

_IDX = None
def index():
    global _IDX
    if _IDX is None: _IDX = build_index()
    return _IDX

def candidates(clue, length, topk=25, docs_df=None, skip_puzzle=None):
    docs, df = docs_df or index()
    N = len(docs); q = set(toks(clue))
    avg = sum(len(t) for t, _, _ in docs) / max(N, 1)
    scored = defaultdict(float)
    for t, ans, pid in docs:
        if skip_puzzle and pid == skip_puzzle: continue
        tl = len(t) or 1
        s = 0.0
        for w in q:
            tf = t.count(w)
            if not tf: continue
            idf = math.log(1 + (N - df[w] + .5) / (df[w] + .5))
            s += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * tl / avg))
        if s <= 0: continue
        for a in ans:
            if len(a) == length: scored[a] = max(scored[a], s)
    return sorted(scored.items(), key=lambda x: -x[1])[:topk]

def end_candidates(clue, length, docs_df=None, skip_puzzle=None):
    """query each end of the clue separately (definition side is at one end)"""
    words = re.findall(r'[א-ת"\']+', clue)
    queries = {' '.join(words[:n]) for n in (2, 3, 4)} | \
              {' '.join(words[-n:]) for n in (2, 3, 4)}
    best = {}
    for q in queries:
        for a, sc in candidates(q, length, docs_df=docs_df, skip_puzzle=skip_puzzle):
            best[a] = max(best.get(a, 0), sc)
    return sorted(best.items(), key=lambda x: -x[1])[:25]

def main():
    if sys.argv[1] == 'candidates':
        for a, s in candidates(sys.argv[2], int(sys.argv[3])):
            print(f'[{s:.2f}] {a}')
    elif sys.argv[1] == 'eval':
        docs_df = build_index()
        tot = hit1 = hit25 = 0
        for line in open('data/dataset/clues.jsonl'):
            c = json.loads(line)
            if c.get('split') != 'dev': continue
            a = norm(c['answer_raw'])
            cands = end_candidates(c['clue_text'], len(a), docs_df=docs_df,
                                   skip_puzzle=c['puzzle_id'])
            tot += 1
            ranked = [x for x, _ in cands]
            hit25 += a in ranked
            hit1 += bool(ranked) and ranked[0] == a
        print(f'dev clues: {tot}; gold@1: {hit1} ({hit1/max(tot,1):.1%}); '
              f'gold@25: {hit25} ({hit25/max(tot,1):.1%})')

if __name__ == '__main__':
    main()
