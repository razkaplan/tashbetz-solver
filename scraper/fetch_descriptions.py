#!/usr/bin/env python3
"""Short definitions for every milon entity.
wikipedia prop=description (the Wikidata short-desc, e.g. 'זמרת ישראלית') batched 50/req;
wiktionary first-line gloss for 'common' dictionary words. Output: data/culture/descriptions.json
"""
import json, os, re, sys, time, urllib.parse, urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs('data/culture', exist_ok=True)
OUT='data/culture/descriptions.json'
desc=json.load(open(OUT)) if os.path.exists(OUT) else {}

def api(host, params):
    params=dict(params, format='json')
    u=f'https://{host}/w/api.php?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(u, headers={'User-Agent':'tashbetz-milon/1.0 (raz.kaplan@gmail.com)'})
    return json.load(urllib.request.urlopen(req, timeout=30))

def batch(titles, host='he.wikipedia.org', extra=None):
    p={'action':'query','titles':'|'.join(titles),'redirects':1}
    p.update(extra or {'prop':'description'})
    try: d=api(host,p)
    except Exception as e:
        print('  skip batch:',str(e)[:50],flush=True); time.sleep(10); return {}
    out={}
    rmap={}
    for r in d.get('query',{}).get('redirects',[]): rmap[r['to']]=r['from']
    for pg in d.get('query',{}).get('pages',{}).values():
        t=pg.get('title'); orig=rmap.get(t,t)
        val=pg.get('description') or (pg.get('extract','').split('।')[0][:160] if pg.get('extract') else '')
        if t and val: out[orig]=val.strip()
    return out

cult=json.load(open('solver/lex/culture.json'))
wiki_cats=[c for c in cult if c not in ('song','common')]
todo=[]
for c in wiki_cats:
    for t in cult.get(c,[]):
        if t not in desc: todo.append(t)
todo=list(dict.fromkeys(todo))
print(f'wikipedia descriptions to fetch: {len(todo)}',flush=True)
for i in range(0,len(todo),50):
    got=batch(todo[i:i+50])
    desc.update(got)
    if i%500==0:
        json.dump(desc,open(OUT,'w'),ensure_ascii=False)
        print(f'  {i}/{len(todo)} (+{len(got)})',flush=True)
    time.sleep(1.2)
json.dump(desc,open(OUT,'w'),ensure_ascii=False)

# wiktionary glosses for common crosswordese (dictionary words)
cw=json.load(open('solver/crosswordese.json'))
common=[a for a,c in cw.items() if c>=2 and 2<=len(a)<=12 and a not in desc]
print(f'wiktionary glosses to fetch: {len(common)}',flush=True)
for i in range(0,len(common),20):
    got=batch(common[i:i+20],'he.wiktionary.org',
              {'prop':'extracts','explaintext':1,'exintro':1,'exsentences':1,'exlimit':20})
    for k,v in got.items():
        v=re.sub(r'\s+',' ',v).strip()
        if 8<=len(v)<=200: desc[k]='[ויקימילון] '+v
    if i%400==0:
        json.dump(desc,open(OUT,'w'),ensure_ascii=False)
        print(f'  {i}/{len(common)}',flush=True)
    time.sleep(1.2)
json.dump(desc,open(OUT,'w'),ensure_ascii=False)
print('total descriptions:',len(desc),flush=True)
