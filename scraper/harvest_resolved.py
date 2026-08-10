#!/usr/bin/env python3
"""Harvest via RESOLVED category names (he-wiki uses 'X: Y' naming; never guess again).
For each kind: search namespace-14, keep categories with real content, harvest depth-1."""
import json, time, os, re, sys, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harvest_culture import members, clean

def api(params):
    u='https://he.wikipedia.org/w/api.php?'+urllib.parse.urlencode(dict(params,format='json'))
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'tashbetz-milon/1.0 (raz.kaplan@gmail.com)'}),timeout=25))

def resolve(term, need=r'.'):
    """search categories for term; keep contentful ones whose name matches `need`"""
    try: d=api({'action':'query','list':'search','srsearch':term,'srnamespace':14,'srlimit':10})
    except Exception: return []
    names=[r['title'] for r in d['query']['search']]
    if not names: return []
    d2=api({'action':'query','titles':'|'.join(names),'prop':'categoryinfo'})
    out=[]
    for p in d2['query']['pages'].values():
        n=p['title'].replace('קטגוריה:','')
        ci=p.get('categoryinfo',{})
        if (ci.get('pages',0)>=8 or ci.get('subcats',0)>=5) and re.search(need,n):
            out.append(n)
    return out[:6]

KINDS={
 'neighborhood':[('שכונות',r'שכונות')],
 'museum':[('מוזיאונים בישראל',r'מוזיאונים'),('מוזיאונים',r'ישראל.*מוזיאונים|מוזיאונים בישראל')],
 'park':[('גנים לאומיים',r'גנים לאומיים'),('שמורות טבע בישראל',r'שמורות טבע')],
 'world_city':[('ערי בירה',r'ערי בירה')],
 'author':[('סופרים ישראלים',r'^סופרים ישראלים$|^משוררים ישראלים$'),('משוררים ישראלים',r'^משוררים ישראלים$')],
 'actor':[('שחקני קולנוע וטלוויזיה ישראלים',r'שחקני .*ישראלים')],
 'kibbutz':[('קיבוצים',r'^קיבוצים$|^מושבים$'),('מושבים',r'^מושבים$')],
 'mountain':[('הרים',r'הרים$|: הרים'),('הרי ישראל',r'^הרי ')],
 'stream':[('נחלים',r'נחלי')],
 'river':[('נהרות',r'נהרות$|: נהרות')],
 'valley':[('בקעות ועמקים',r'עמקים|בקעות')],
 'desert':[('מדבריות',r'מדבריות')],
 'region':[('חבלי ארץ',r'חבלי ארץ|חבל ')],
 'site':[('אתרים ארכאולוגיים',r'אתרים ארכאולוגיים'),('תלים',r'תל(ים)? ')],
}
cult=json.load(open('solver/lex/culture.json'))
for kind,queries in KINDS.items():
    cats=[]
    for term,need in queries:
        cats+= [c for c in resolve(term,need) if c not in cats]
        time.sleep(1.5)
    seen=set(cult.get(kind,[]))
    before=len(seen)
    print(f'{kind}: categories -> {cats}', flush=True)
    for c in cats:
        try:
            for t in members(c):
                ct=clean(t)
                if 1<len(ct)<=40 and re.search(r'[א-ת]',ct): seen.add(ct)
        except Exception as e: print('  skip',c,e, flush=True)
        time.sleep(2)
    cult[kind]=sorted(seen)
    print(f'{kind}: {before} -> {len(seen)}', flush=True)
    json.dump(cult,open('solver/lex/culture.json','w'),ensure_ascii=False,indent=0)
print('total:',sum(len(v) for v in cult.values()))
