#!/usr/bin/env python3
"""Programmatic-SEO מילון: entity + category/length pages from our own indices.

Competitor gap (measured 2026-08): note.co.il/מורדו index by DEFINITION text;
nobody serves entity pages or the "זמרת 4 אותיות" query shape. We generate:
  /milon/                      search hub (client-side: name/pattern/length)
  /milon/<cat>-<len>/          category-length lists (זמרים ב-4 אותיות...)
  /milon/e/<name>/             entity pages for entities with rich data
All content is derived (names from wikipedia/shironet titles, our own stats).
No newspaper clue text is published — the line the whole project keeps.
"""
import json, os, re, urllib.parse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT='docs/milon'; os.makedirs(OUT,exist_ok=True)
FIN=str.maketrans('ךםןףץ','כמנפצ')
norm=lambda s:re.sub(r'[^א-ת]','',s or '').translate(FIN)
BASE='https://tashbetz.gtmascode.dev'

cult=json.load(open('solver/lex/culture.json'))
DESC=json.load(open('data/culture/descriptions.json')) if os.path.exists('data/culture/descriptions.json') else {}
amb=json.load(open('solver/lex/ambiguities.json'))
cw=json.load(open('solver/crosswordese.json')) if os.path.exists('solver/crosswordese.json') else {}
subs=json.load(open('solver/lex/substitutions.json'))
# corpus-mined: answers that recur across the 362-puzzle sample (our own statistic)
known=set()
for v in cult.values(): known.update(norm(x) for x in v)
cult['common']=sorted(a for a,c in cw.items() if c>=2 and a not in known and 2<=len(a)<=12)

# curated military terms: crossword answers are the gershayim-less spellings (norm handles it)
MIL={
 'טוראי':'הדרגה הראשונה בצה\"ל','רב\"ט':'רב טוראי','סמל':'דרגת סמל','סמ\"ר':'סמל ראשון',
 'רס\"ל':'רב סמל','רס\"ר':'רב סמל ראשון','רס\"מ':'רב סמל מתקדם','רס\"ב':'רב סמל בכיר',
 'רנ\"ג':'רב נגד','סג\"ם':'סגן משנה','סגן':'דרגת קצונה','סרן':'דרגת קצונה',
 'רס\"ן':'רב סרן','סא\"ל':'סגן אלוף','אל\"מ':'אלוף משנה','תא\"ל':'תת אלוף',
 'אלוף':'דרגת האלוף','רב אלוף':'דרגת הרמטכ\"ל',
 'מ\"כ':'מפקד כיתה','מ\"מ':'מפקד מחלקה','מ\"פ':'מפקד פלוגה','סמ\"פ':'סגן מפקד פלוגה',
 'מג\"ד':'מפקד גדוד','סמג\"ד':'סגן מפקד גדוד','מח\"ט':'מפקד חטיבה','מא\"ז':'מפקד אזור',
 'קמ\"ן':'קצין מודיעין','קצי\"ח':'קצין חימוש','שליש':'קצין שלישות','רמטכ\"ל':'ראש המטה הכללי',
 'מטכ\"ל':'המטה הכללי','אג\"ם':'אגף המבצעים','אכ\"א':'אגף כוח אדם','אמ\"ן':'אגף המודיעין',
 'כיתה':'יחידה בסיסית','מחלקה':'יחידת משנה בפלוגה','פלוגה':'יחידת משנה בגדוד',
 'גדוד':'יחידת משנה בחטיבה','חטיבה':'יחידת משנה באוגדה','אוגדה':'עוצבה גדולה','גיס':'עוצבת גיסות',
 'חי\"ר':'חיל רגלים','חת\"ם':'חיל התותחנים','חש\"ן':'חיל השריון (היסטורי)','שריון':'גייסות השריון',
 'צנחן':'לוחם בחטיבת הצנחנים','נגמ\"ש':'נושא גייסות משוריין','זחל\"ם':'רכב חצי זחלי',
 'שק\"ם':'שירות קנטינות ומזנונים','בקו\"ם':'בסיס קליטה ומיון','בה\"ד':'בסיס הדרכה',
 'טירונות':'אימון בסיסי','מיל\"':'שירות מילואים','חוגר':'חייל שאינו קצין','פז\"ם':'פרק זמן מינימלי',
 'רבש\"ץ':'רכז ביטחון שוטף צבאי','מש\"ק':'מפקד שאינו קצין','נ\"מ':'נגד מטוסים','תול\"ר':'תותח ללא רתע',
}
MIL={k.replace('\\"','\"'):v.replace('\\"','\"') for k,v in MIL.items()}
cult['military']=sorted(set(cult.get('military',[]))|set(MIL))

CATS={'song':('שירים','שיר'),'artist':('זמרים ולהקות','זמר/להקה'),
      'politician':('פוליטיקאים','פוליטיקאי/ת'),
      'neighborhood':('שכונות','שכונה'),'park':('פארקים ושמורות טבע','פארק/שמורה'),
      'museum':('מוזיאונים','מוזיאון'),'nation':('מדינות','מדינה'),
      'world_city':('ערים ובירות בעולם','עיר בעולם'),'athlete':('ספורטאים','ספורטאי/ת'),
      'bible':('דמויות מהתנ"ך','דמות מקראית'),'author':('סופרים ומשוררים','סופר/משורר'),
      'actor':('שחקנים','שחקן/ית'),'kibbutz':('קיבוצים ומושבים','קיבוץ/מושב'),
      'city_il':('ערים ויישובים בישראל','יישוב'),'mountain':('הרים ורכסים','הר'),
      'stream':('נחלים','נחל'),'river':('נהרות העולם','נהר'),
      'valley':('עמקים ובקעות','עמק'),'lake_sea':('ימים, אגמים ומפרצים','ים/אגם'),
      'desert':('מדבריות','מדבר'),'island':('איים','אי'),
      'region':('חבלי ארץ','חבל ארץ'),'site':('אתרים עתיקים וגנים לאומיים','אתר'),
      'military':('מונחים צבאיים','מונח צבאי'),
      'common':('תשובות נפוצות בתשבצים','תשובה נפוצה')}
HEBSENSE={'common_word':'מילה מן המילון','given_name':'שם פרטי','surname':'שם משפחה',
 'role_noun':'תפקיד/פועל וגם שם','song':'שם שיר','song_word':'מילה מתוך שיר','artist':'זמר/להקה',
 'politician':'פוליטיקאי/ת','place':'מקום','answer':'הופיעה כתשובה בתשבצים'}

STYLE="""<style>*{box-sizing:border-box}body{margin:0;background:#fff;color:#121212;font-family:'Frank Ruhl Libre','Arial Hebrew',serif;line-height:1.6}
.w{max-width:52rem;margin:0 auto;padding:1rem 1.2rem}header{border-bottom:1px solid #121212;box-shadow:0 3px 0 -1px #121212;padding:.8rem 0}
h1{font-size:1.6rem;margin:.2rem 0}.k{font-family:monospace;font-size:.65rem;letter-spacing:.12em;color:#fff;background:#f22b39;display:inline-block;padding:.12rem .5rem}
a{color:#f22b39}h2{border-bottom:3px solid #f22b39;display:inline-block;font-size:1.1rem;padding-bottom:.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(11rem,1fr));gap:.4rem;padding:0;list-style:none}
.grid li{background:#f6f5f3;padding:.35rem .6rem;border-radius:3px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #dcdcdc;padding:.4rem .5rem;text-align:right}
footer{margin:2.5rem 0 1.5rem;border-top:1px solid #dcdcdc;padding-top:.8rem;font-size:.8rem;color:#5c5c5c}
.crumb{font-size:.8rem;color:#5c5c5c;margin:.6rem 0}input{font:inherit;padding:.5rem;border:1.5px solid #121212;border-radius:3px;width:100%}
@media(prefers-color-scheme:dark){body{background:#161616;color:#f2f0ec}.grid li{background:#222}td,th{border-color:#3a3a3a}}</style>"""

def page(path,title,desc,body,jsonld=None):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    rel='/'+os.path.relpath(path,'docs').replace('index.html','').replace(os.sep,'/')
    crumbs=[("דף הבית",BASE+"/"),("מילון",BASE+"/milon/")]
    if rel not in ('/milon/','/'): crumbs.append((title.split(' — ')[0],BASE+rel))
    bc={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":n,"item":u} for i,(n,u) in enumerate(crumbs)]}
    ld=f'<script type="application/ld+json">{json.dumps(bc,ensure_ascii=False)}</script>'
    if jsonld: ld+=f'<script type="application/ld+json">{json.dumps(jsonld,ensure_ascii=False)}</script>'
    canon=BASE+'/'+os.path.relpath(path,'docs').replace('index.html','').replace(os.sep,'/')
    open(path,'w').write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<meta name="description" content="{desc}"><link rel="canonical" href="{canon}">{ld}{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>{title}</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div></header>
{body}
<footer>מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) וניתוח סטטיסטי מקורי · לא מתפרסמות הגדרות מעיתונים ·
<a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a></footer></div></body></html>""")

# relations: song <-> artist from shironet (titles are public metadata, lyrics never copied)
song_rel={}; artist_rel={}
if os.path.exists('data/shironet_songs.json'):
    for r in json.load(open('data/shironet_songs.json')):
        an=(r.get('artist_name') or '').strip()
        if not an: continue
        for st in r.get('song_titles',[]):
            st=st.strip()
            if not st: continue
            song_rel.setdefault(norm(st),{'artist':an,'url':r.get('product_page_url','')})
            artist_rel.setdefault(norm(an),{'name':an,'prfid':r.get('prfid',''),'songs':[]})
            artist_rel[norm(an)]['songs'].append(st)
WIKI_CATS={c for c in CATS if c not in ('song','artist','common','military')}

def get_desc(cat,t,n):
    if t in DESC: return DESC[t].removeprefix('[ויקימילון] ')
    if cat=='song' and n in song_rel: return f"שיר של {song_rel[n]['artist']}"
    if cat=='artist' and n in artist_rel:
        ss=artist_rel[n]['songs'][:3]
        return 'בין השירים: '+', '.join(f'"{x}"' for x in ss) if ss else ''
    if cat=='military': return MIL.get(t,'')
    if cat=='common':
        prs=subs['fwd'].get(n,[])+subs['rev'].get(n,[])
        if prs:
            uniq=list(dict.fromkeys(x[0] for x in prs))[:3]
            return 'בהסברי תשבצים מקושרת ל: '+', '.join(uniq)
    return ''


urls=[]
# ---------- category-length pages ----------
for cat,(plural,single) in CATS.items():
    by_len={}
    for t in cult.get(cat,[]):
        n=norm(t)
        if 2<=len(n)<=12: by_len.setdefault(len(n),[]).append((t,n))
    for L,items in sorted(by_len.items()):
        if len(items)<3: continue
        items.sort(key=lambda x:(-cw.get(x[1],0),x[0]))     # frequent crossword answers first
        slug=f'{cat}-{L}'
        def _li(t,n):
            b=f' <span class="k" style="font-size:.55rem">{cw[n]}×</span>' if cw.get(n,0)>=2 else ''
            d=get_desc(cat,t,n)
            dd=f'<br><small>{d[:90]}</small>' if d else ''
            return f'<li id="{n}"><b>{t}</b>{b}{dd}<br><small style="font-family:monospace;color:#5c5c5c">{n}</small></li>'
        lis=''.join(_li(t,n) for t,n in items)
        body=f"""<p><b>{len(items)} {plural}</b> שהשם שלהם נכתב ברשת התשבץ ב-<b>{L} אותיות</b>
(בתשבץ אין אותיות סופיות — ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ, והכתיב מוצג מתחת לכל שם).</p>
<ul class="grid">{lis}</ul>"""
        page(f'{OUT}/{slug}/index.html',
             f'{plural} ב-{L} אותיות לתשבץ ותשחץ — {len(items)} פתרונות',
             f'{single} ב-{L} אותיות? הרשימה המלאה לפתרון תשבצים: {len(items)} {plural}, ממוינים לפי שכיחות בתשבצים, עם הכתיב המדויק ללא אותיות סופיות.',
             body,
             {"@context":"https://schema.org","@type":"ItemList","name":f"{plural} ב-{L} אותיות",
              "numberOfItems":len(items)})
        urls.append(f'/milon/{slug}/')

# ---------- entity pages: entities with rich data or references ----------
def refs_for(cat,t,n):
    """at least one reference per entity; internal cross-links resolved later"""
    out=[]
    if cat=='song' and n in song_rel:
        r=song_rel[n]
        out.append(('artist',r['artist']))
        if r['url']: out.append(('ext',('מילות השיר בשירונט',r['url'])))
    if cat=='artist' and n in artist_rel:
        r=artist_rel[n]
        for st in r['songs'][:10]: out.append(('song',st))
        if r['prfid']:
            out.append(('ext',('דף האמן בשירונט',
                f"https://shironet.mako.co.il/artist?type=works&lang=1&prfid={r['prfid']}")))
    if cat=='military' and t in MIL:
        art=MIL[t] if MIL[t] and ' ' in MIL[t] and len(MIL[t])<=22 else t
        out.append(('ext',(f'{art} בוויקיפדיה',
            'https://he.wikipedia.org/wiki/'+urllib.parse.quote(art.replace(' ','_')))))
    if cat in WIKI_CATS:
        out.append(('ext',(f'{t} בוויקיפדיה',
            'https://he.wikipedia.org/wiki/'+urllib.parse.quote(t.replace(' ','_')))))
    if cat=='common' and DESC.get(t,'').startswith('[ויקימילון]'):
        out.append(('ext',(f'{t} בוויקימילון',
            'https://he.wiktionary.org/wiki/'+urllib.parse.quote(t))))
    return out

# pass 1: decide which entities get pages (rich data OR relations), respecting the cap
ent_index=[]; page_set=set(); count=0; CAP=6000
for cat,(plural,single) in CATS.items():
    for t in cult.get(cat,[]):
        n=norm(t)
        if not (2<=len(n)<=14): continue
        a=amb.get(n); c=cw.get(n,0); sb=subs['fwd'].get(n,[])+subs['rev'].get(n,[])
        has_rel=(cat=='song' and n in song_rel) or (cat=='artist' and n in artist_rel) or cat=='military'
        has_desc=bool(get_desc(cat,t,norm(t)))
        signals=sum([bool(a), c>=2, bool(sb), has_rel, has_desc])
        rich=signals>=2
        ent_index.append({'t':t,'n':n,'c':cat,'l':len(n),'d':get_desc(cat,t,n)[:70],'r':rich})
        if rich and count<CAP:
            page_set.add((cat,t)); count+=1
by_norm={}
for cat,t in page_set: by_norm.setdefault(norm(t),(cat,t))
pages_norm={norm(t) for _,t in page_set}
for e in ent_index: e['p']=1 if (e['r'] and e['n'] in pages_norm) else 0
for e in ent_index: e.pop('r',None)

def ref_link(kind,val):
    if kind=='ext':
        label,url=val
        return f'<a href="{url}" rel="noopener">{label}</a>'
    hit=by_norm.get(norm(val))
    if hit:
        return f'<a href="/milon/e/{urllib.parse.quote(hit[1],safe="")}/">{val}</a>'
    return val

# pass 2: build pages
for cat,t in sorted(page_set):
    plural,single=CATS[cat]; n=norm(t)
    a=amb.get(n); c=cw.get(n,0); sb=subs['fwd'].get(n,[])+subs['rev'].get(n,[])
    d=get_desc(cat,t,n)
    rows=(f'<tr><th>הגדרה</th><td><b>{d}</b></td></tr>' if d else '')
    rows+=f'<tr><th>סוג</th><td>{single}</td></tr><tr><th>אורך ברשת</th><td>{len(n)} אותיות</td></tr>'
    if cat=='military' and t in MIL and MIL[t]!=d: rows+=f'<tr><th>פירוש</th><td>{MIL[t]}</td></tr>'
    rows+=f'<tr><th>כתיב בתשבץ</th><td style="font-family:monospace">{n}</td></tr>'
    if c: rows+=f'<tr><th>הופעות בתשבצים</th><td>{c} פעמים (מתוך מדגם של 362 תשבצים)</td></tr>'
    if a: rows+=f'<tr><th>משמעויות נוספות</th><td>{", ".join(HEBSENSE.get(x,x) for x in a["senses"])}</td></tr>'
    if sb:
        pairs=', '.join(f'{x[0]}' for x in sb[:5])
        rows+=f'<tr><th>תחליפים בתשבצים</th><td>{pairs}</td></tr>'
    refs=refs_for(cat,t,n)
    if refs:
        by_kind={}
        for kind,val in refs: by_kind.setdefault(kind,[]).append(val)
        parts=[]
        if 'artist' in by_kind: parts.append('מאת: '+', '.join(ref_link('x',v) for v in by_kind['artist']))
        if 'song' in by_kind: parts.append('שירים: '+', '.join(ref_link('x',v) for v in by_kind['song']))
        if 'ext' in by_kind: parts.append(' · '.join(ref_link('ext',v) for v in by_kind['ext']))
        rows+=f'<tr><th>רפרנסים</th><td>{"<br>".join(parts)}</td></tr>'
    letters=' · '.join(sorted(set(n)))
    related=[t2 for c2,t2 in sorted(page_set) if c2==cat and t2!=t and len(norm(t2))==len(n)][:10]
    rel_html=''
    if related:
        rl=' · '.join(f'<a href="/milon/e/{urllib.parse.quote(t2,safe="")}/">{t2}</a>' for t2 in related)
        rel_html=f'<p style="margin-top:.8rem"><b>ערכים קרובים ({single}, {len(n)} אותיות):</b> {rl}</p>'
    body=f"""<table>{rows}<tr><th>אותיות (לאנגרם)</th><td style="font-family:monospace">{letters}</td></tr></table>
{rel_html}
<p style="margin-top:1rem"><a href="/milon/{urllib.parse.quote(f'{cat}-{len(n)}')}/">עוד {plural} ב-{len(n)} אותיות ←</a>
 · <a href="/milon/anagram/">חיפוש אנגרם</a></p>"""
    ld={"@context":"https://schema.org","@type":"DefinedTerm","name":t,
        "inDefinedTermSet":f"{BASE}/milon/"}
    ext=[v[1] for k,v in refs if k=='ext']
    if ext: ld["sameAs"]=ext
    page(f'{OUT}/e/{urllib.parse.quote(t,safe="")}/index.html',
         f'{t} בתשבץ — {single} ב-{len(n)} אותיות (כתיב: {n})',
         (f'{t}: {get_desc(cat,t,n)}. {single} ב-{len(n)} אותיות, כתיב רשת: {n}. לפותרי תשבצים ותשחצים.' if get_desc(cat,t,n) else
          f'איך כותבים {t} בתשבץ? {single} ב-{len(n)} אותיות, כתיב רשת: {n}. משמעויות, שכיחות ורפרנסים.'),
         body, ld)
    urls.append(f'/milon/e/{urllib.parse.quote(t,safe="")}/')

# ---------- ORPHAN CLEANUP: entity pages whose entity no longer exists ----------
import shutil
live={urllib.parse.quote(t,safe="") for _,t in page_set}
edir=f'{OUT}/e'
removed=0
if os.path.isdir(edir):
    for d in os.listdir(edir):
        if d not in live:
            shutil.rmtree(os.path.join(edir,d),ignore_errors=True); removed+=1
# category-length dirs that no longer get built
live_cats={u.strip('/').split('/')[-1] for u in urls if u.startswith('/milon/') and '/e/' not in u}
for d in os.listdir(OUT):
    full=os.path.join(OUT,d)
    if os.path.isdir(full) and re.match(r'^[a-z_]+-\d+$',d) and d not in live_cats:
        shutil.rmtree(full,ignore_errors=True); removed+=1
print(f'orphan pages removed: {removed}')

# ---------- search hub ----------
json.dump(ent_index,open(f'{OUT}/entities.json','w'),ensure_ascii=False)
cat_links=''
for cat,(plural,_) in CATS.items():
    Ls=sorted({e['l'] for e in ent_index if e['c']==cat and 2<=e['l']<=12})
    links=' '.join(f'<a href="/milon/{cat}-{L}/">{L}</a>' for L in Ls if f'/milon/{cat}-{L}/' in urls)
    cat_links+=f'<p><b>{plural}</b> לפי אורך: {links}</p>'
cat_json=json.dumps({c:v[1] for c,v in CATS.items()},ensure_ascii=False)
hub=f"""<p>מנוע חיפוש לפותרי תשבצים: שמות של שירים, זמרים, פוליטיקאים ומקומות — עם הכתיב המדויק ברשת
(ללא אותיות סופיות), אורך, ומשמעויות כפולות. {len(ent_index):,} ערכים.</p>
<input id="q" placeholder="חיפוש שם, או תבנית: ? או . לאות חסרה (למשל: ?ו?ה)" autocomplete="off">
<p style="margin:.5rem 0"><a href="/milon/anagram/"><b>יש לכם אותיות מבולבלות? → חיפוש אנגרם</b></a></p>
<div id="res" class="grid" style="margin-top:.8rem"></div>
<h2>עיון לפי קטגוריה ואורך</h2>{cat_links}
<p style="margin-top:1.4rem">חסרה לכם תשובה שלמה? <a href="/solve/">עוזר הפתירה</a> פותר איתכם עם רמזים מדורגים והוכחות.</p>
<script>
let E=null;const q=document.getElementById('q'),res=document.getElementById('res');
fetch('/milon/entities.json').then(r=>r.json()).then(d=>E=d);
const CAT={cat_json};
q.oninput=()=>{{if(!E)return;const v=q.value.trim();res.innerHTML='';if(v.length<2)return;
let hits;
if(v.includes('?')){{const rx=new RegExp('^'+v.replace(/[א-ת]/g,m=>m).replace(/\\?/g,'.')+'$');
  hits=E.filter(e=>rx.test(e.n));}}
else hits=E.filter(e=>e.t.includes(v)||e.n.includes(v.replace(/[ךםןףץ]/g,m=>({{'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'}})[m])));
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));res.innerHTML=hits.slice(0,60).map(e=>{{const u=e.p?('/milon/e/'+encodeURIComponent(e.t)+'/'):('/milon/'+e.c+'-'+e.l+'/#'+encodeURIComponent(e.n));return '<li><a href="'+u+'" style="text-decoration:none;color:inherit"><b style="color:#f22b39">'+esc(e.t)+'</b>'+(e.d?'<br><small>'+esc(e.d)+'</small>':'')+'<br><small>'+esc(CAT[e.c]||'')+' · '+esc(e.l)+' אותיות · <span style="font-family:monospace">'+esc(e.n)+'</span></small></a></li>'}}).join('');
}};
</script>"""
page(f'{OUT}/index.html','מילון תשבץ — חיפוש לפי אורך, תבנית ואנגרם',
     f'מנוע חיפוש לפותרי תשבצים: {len(ent_index):,} שירים, זמרים, פוליטיקאים ומקומות עם כתיב תשבץ מדויק, אורך ותבניות.',
     hub,[{"@context":"https://schema.org","@type":"DefinedTermSet","name":"מילון תשבץ",
      "url":f"{BASE}/milon/","description":f"{len(ent_index):,} ערכים לפותרי תשבצים"},
     {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
      {"@type":"Question","name":"איך כותבים שמות בתשבץ בלי אותיות סופיות?",
       "acceptedAnswer":{"@type":"Answer","text":"ברשת תשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ. המילון מציג לכל ערך את כתיב הרשת המדויק."}},
      {"@type":"Question","name":"איך מוצאים תשובה כשידועות רק חלק מהאותיות?",
       "acceptedAnswer":{"@type":"Answer","text":"מקלידים תבנית בשורת החיפוש: סימן שאלה או נקודה במקום אות חסרה, למשל ?ו?ה. מקבלים את כל הערכים המתאימים."}},
      {"@type":"Question","name":"מה עושים עם הגדרת אנגרם?",
       "acceptedAnswer":{"@type":"Answer","text":"בעמוד חיפוש האנגרם מקלידים את האותיות ומקבלים את כל השמות והמילים שהן פרמוטציה שלהן."}}]}])
urls.insert(0,'/milon/')

# ---------- anagram page ----------
ana_body="""<p>הפודר של אנגרם בתשבץ היגיון מופיע מילולית בהגדרה. מקלידים כאן את האותיות (ברצף, בלי רווחים)
ומקבלים כל שם ומילה שהם פרמוטציה מדויקת שלהן. אפשר גם לכלול את לקסיקון המילים המלא (141 אלף מילים).</p>
<input id="a" placeholder="האותיות שיש לכם, למשל: ליבנוצר" autocomplete="off">
<label style="display:block;margin:.5rem 0;font-size:.9rem"><input type="checkbox" id="uselex" style="width:auto"> כלול גם מילים רגילות מהלקסיקון (טעינה חד-פעמית של ~1.5MB)</label>
<div id="ares" class="grid" style="margin-top:.8rem"></div>
<p style="margin-top:1.4rem">רוצים גם הוכחה שהאנגרם נכון? <a href="/solve/">עוזר הפתירה</a> בודק מכנית כל טענה.</p>
<script>
let E=null,LEX=null;const a=document.getElementById('a'),ares=document.getElementById('ares'),ul=document.getElementById('uselex');
fetch('/milon/entities.json').then(r=>r.json()).then(d=>E=d);
const FIN={'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'};
const sig=w=>w.replace(/[ךםןףץ]/g,m=>FIN[m]).split('').sort().join('');
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
ul.onchange=()=>{if(ul.checked&&!LEX)fetch('/solve/data/lexicon.txt').then(r=>r.text()).then(t=>{LEX=t.split('\n');run()});else run()};
function run(){if(!E)return;const v=a.value.replace(/[^א-ת]/g,'');ares.innerHTML='';if(v.length<3)return;
const target=sig(v);let out=[];
for(const e of E){if(e.n.length===v.length&&sig(e.n)===target)out.push('<li><b>'+esc(e.t)+'</b><br><small style="font-family:monospace">'+esc(e.n)+'</small></li>');if(out.length>=40)break}
if(ul.checked&&LEX){for(const w of LEX){if(w.length===v.length&&sig(w)===target)out.push('<li>'+esc(w)+'</li>');if(out.length>=80)break}}
ares.innerHTML=out.join('')||'<li>לא נמצאה פרמוטציה. נסו לכלול את הלקסיקון המלא.</li>'}
a.oninput=run;
</script>"""
page(f'{OUT}/anagram/index.html',
     'חיפוש אנגרם לתשבץ — מי מסתתר באותיות המבולבלות',
     'פותר אנגרמות לתשבצי היגיון: מקלידים את האותיות ומקבלים כל שם, מקום ומילה שהם פרמוטציה שלהן. כולל לקסיקון של 141 אלף מילים וכתיב רשת מדויק.',
     ana_body,{"@context":"https://schema.org","@type":"WebApplication","name":"חיפוש אנגרם לתשבץ",
     "url":f"{BASE}/milon/anagram/","applicationCategory":"Utility"})
urls.insert(1,'/milon/anagram/')

# ---------- sitemap + robots ----------
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in ['/','/solve/','/methods/','/research/','/research/he/']+urls:
    sm+=f'  <url><loc>{BASE}{u}</loc></url>\n'
sm+='</urlset>'
open('docs/sitemap.xml','w').write(sm)
open('docs/robots.txt','w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
print(f'pages: {len(urls)} (entities with rich data: {count}); index entries: {len(ent_index)}')
