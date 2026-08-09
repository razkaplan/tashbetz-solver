#!/usr/bin/env python3
"""PRIVATE corpus crawler: definition->answers pairs from public crossword-help sites.

POLICY (do not change): output lives under data/answers/private_defs/ which is
gitignored and must NEVER be published, deployed, or baked into the public milon.
It feeds the solver only: retrieval, candidate generation, substitution mining.
Republishing these sites' curated databases would be infringement, not competition.

Usage: python3 scraper/crawl_defs.py note|mordo
"""
import json, re, sys, time, html, os, urllib.request, urllib.parse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT='data/answers/private_defs'; os.makedirs(OUT,exist_ok=True)
UA={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def get(u, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read().decode('utf-8','replace')
        except Exception:
            time.sleep(3*(i+1))
    return ''

def parse_answers(txt):
    """'פתרון של 3 אותיות: פול' segments -> list of answers."""
    out=[]
    for m in re.finditer(r'פתרון של \d+ (?:אותיות|מילים):\s*(.+?)(?=פתרון של \d+|$)', txt):
        for a in re.split(r'[,;]| ו(?=[א-ת]{2})', m.group(1)):
            a=re.sub(r'\([^)]*\)','',a).strip(' .[]')
            if 1<len(a)<=25 and re.search(r'[א-ת]',a):
                out.append(a)
    return out

def crawl_note():
    fn=f'{OUT}/note.jsonl'
    seen=set()
    if os.path.exists(fn):
        for l in open(fn): seen.add(json.loads(l).get('url'))
    letters='אבגדהוזחטיכלמנסעפצקרשת'
    urls=[]
    for L in letters:
        page=1
        while True:
            u=f'https://www.note.co.il/abc/{urllib.parse.quote(L)}/' + (f'page/{page}/' if page>1 else '')
            p=get(u)
            found=re.findall(r'href="(https://www\.note\.co\.il/solution/[^"]+)"',p)
            found=[x for x in dict.fromkeys(found)]
            if not found: break
            urls+= [x for x in found if x not in seen]
            if f'/page/{page+1}/' not in p and 'next' not in p: break
            page+=1; time.sleep(0.4)
        print(f'letter {L}: total urls {len(urls)}', flush=True)
    urls=list(dict.fromkeys(urls))
    print(f'note: {len(urls)} new solution pages to fetch', flush=True)
    with open(fn,'a') as f:
        for i,u in enumerate(urls):
            p=get(u)
            t=re.search(r'<h2 class="the_title single">(.*?)</h2>',p,re.S)
            c=re.search(r'<div class="dictionary entry_content">(.*?)</article>',p,re.S)
            if t and c:
                txt=html.unescape(re.sub(r'<[^>]+>',' ',c.group(1)))
                txt=re.sub(r'\s+',' ',txt)
                ans=parse_answers(txt)
                cats=re.findall(r'rel="tag">([^<]+)</a>',p)
                f.write(json.dumps({'src':'note','url':u,
                    'definition':html.unescape(re.sub(r'<[^>]+>','',t.group(1))).strip(),
                    'answers':ans,'cats':cats[:4]},ensure_ascii=False)+'\n')
                if i%100==0: f.flush(); print(f'  {i}/{len(urls)}', flush=True)
            time.sleep(0.5)
    print('note done', flush=True)

def crawl_mordo():
    """Blogspot bulk feed: all posts, 150 at a time — far gentler than page scraping."""
    fn=f'{OUT}/mordo.jsonl'
    start=1
    with open(fn,'a') as f:
        while True:
            u=(f'https://pitaronfree.blogspot.com/feeds/posts/default?alt=json'
               f'&start-index={start}&max-results=150')
            try:
                d=json.loads(get(u))
            except Exception:
                break
            entries=d.get('feed',{}).get('entry',[])
            if not entries: break
            for e in entries:
                title=e.get('title',{}).get('$t','')
                content=html.unescape(re.sub(r'<[^>]+>',' ',e.get('content',{}).get('$t','')))
                content=re.sub(r'\s+',' ',content)[:4000]
                f.write(json.dumps({'src':'mordo','definition':title.strip(),
                    'content':content},ensure_ascii=False)+'\n')
            print(f'mordo: {start}+{len(entries)}', flush=True)
            start+=150; time.sleep(1)
    print('mordo done', flush=True)

if __name__=='__main__':
    {'note':crawl_note,'mordo':crawl_mordo}[sys.argv[1]]()

# Mordo (pitaronfree) posts use "פתרון N אותיות:" sections without "של".
# Re-parse saved content in place (crawl saves content, so no re-crawl needed):
#   python3 -c "import crawl_defs; crawl_defs.reparse_mordo()"
import re as _re
_SEC=_re.compile(r'פתרון (?:של )?(\d+|שתי מילים) (?:אותיות|מילים)?\s*(?:ומעלה)?\s*:\s*')
def parse_mordo_answers(content):
    cut=content.find('ביטויים דומים')
    body=content[:cut] if cut>0 else content
    ans=[]
    parts=_SEC.split(body)
    for i in range(1,len(parts)-1,2):
        n,seg=parts[i],parts[i+1].strip()
        if not seg: continue
        if ',' in seg: ans+=[a.strip() for a in seg.split(',') if a.strip()]
        elif n.isdigit():
            toks=seg.split()
            ans+= toks if toks and all(len(t)==int(n) for t in toks) else [seg]
        else: ans.append(seg)
    return [a for a in ans if _re.search(r'[א-ת]',a)]

def reparse_mordo(path='data/answers/private_defs/mordo.jsonl'):
    import json
    rows=[json.loads(l) for l in open(path)]
    for r in rows:
        if not r.get('answers'): r['answers']=parse_mordo_answers(r.get('content',''))
    with open(path,'w') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
