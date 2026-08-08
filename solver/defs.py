#!/usr/bin/env python3
"""PRIVATE definitions dictionary — candidate generation from crawled def->answer pairs.

Data: data/answers/private_defs/*.jsonl (gitignored; never published — see crawl_defs.py).
This is the highest-value candidate source we have: real crossword definitions mapped to
real answers, curated by the two largest Hebrew crossword-help sites.

CLI:
  python3 solver/defs.py lookup "זמר רגאי"        # definitions containing these words -> answers
  python3 solver/defs.py answer <word>            # reverse: definitions that yield this answer
  python3 solver/defs.py candidates "<clue>" <len> # answers of given length whose definition
                                                    shares words with the clue
"""
import json, os, re, sys, glob

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIN=str.maketrans('ךםןףץ','כמנפצ')
norm=lambda s:re.sub(r'[^א-ת]','',s or '').translate(FIN)
STOP=set('של עם על אל את זה זו הוא היא לא כמו או גם יש אין מי מה'.split())

def load():
    rows=[]
    for f in glob.glob('data/answers/private_defs/*.jsonl'):
        for l in open(f):
            try: rows.append(json.loads(l))
            except Exception: pass
    return rows

def toks(s): return [w for w in re.findall(r'[א-ת]+',s or '') if len(w)>1 and w not in STOP]

def main():
    rows=load()
    if not rows:
        print('(no private defs crawled yet — run scraper/crawl_defs.py)'); return
    cmd=sys.argv[1]
    if cmd=='lookup':
        q=set(toks(sys.argv[2]))
        hits=[]
        for r in rows:
            d=set(toks(r.get('definition','')))
            ov=len(q&d)
            if ov: hits.append((ov,r))
        hits.sort(key=lambda x:-x[0])
        for ov,r in hits[:12]:
            print(f"[{ov}] {r['definition']}  ->  {', '.join(r.get('answers',[])[:8]) or '(see content)'}")
    elif cmd=='answer':
        t=norm(sys.argv[2])
        for r in rows:
            if any(norm(a)==t for a in r.get('answers',[])):
                print(r['definition'])
    elif cmd=='candidates':
        q=set(toks(sys.argv[2])); L=int(sys.argv[3])
        score={}
        for r in rows:
            ov=len(q&set(toks(r.get('definition',''))))
            if not ov: continue
            for a in r.get('answers',[]):
                n=norm(a)
                if len(n)==L: score[n]=max(score.get(n,0),ov)
        for n,ov in sorted(score.items(),key=lambda x:-x[1])[:20]:
            print(f'[{ov}] {n}')
    else:
        print(__doc__)

if __name__=='__main__': main()
