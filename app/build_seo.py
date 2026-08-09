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
amb=json.load(open('solver/lex/ambiguities.json'))
cw=json.load(open('solver/crosswordese.json')) if os.path.exists('solver/crosswordese.json') else {}
subs=json.load(open('solver/lex/substitutions.json'))
# corpus-mined: answers that recur across the 362-puzzle sample (our own statistic)
known=set()
for v in cult.values(): known.update(norm(x) for x in v)
cult['common']=sorted(a for a,c in cw.items() if c>=2 and a not in known and 2<=len(a)<=12)

CATS={'song':('שירים','שיר'),'artist':('זמרים ולהקות','זמר/להקה'),
      'politician':('פוליטיקאים','פוליטיקאי/ת'),'place':('ערים בישראל','עיר'),
      'neighborhood':('שכונות','שכונה'),'park':('פארקים ושמורות טבע','פארק/שמורה'),
      'museum':('מוזיאונים','מוזיאון'),'nation':('מדינות','מדינה'),
      'world_city':('ערי בירה','עיר בירה'),'athlete':('ספורטאים','ספורטאי/ת'),
      'bible':('דמויות מהתנ"ך','דמות מקראית'),'author':('סופרים ומשוררים','סופר/משורר'),
      'actor':('שחקנים','שחקן/ית'),'kibbutz':('קיבוצים ומושבים','קיבוץ/מושב'),
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
    ld=f'<script type="application/ld+json">{json.dumps(jsonld,ensure_ascii=False)}</script>' if jsonld else ''
    canon=BASE+'/'+os.path.relpath(path,'docs').replace('index.html','').replace(os.sep,'/')
    open(path,'w').write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<meta name="description" content="{desc}"><link rel="canonical" href="{canon}">{ld}{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>{title}</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div></header>
{body}
<footer>מבוסס על אינדקס פתוח של שמות (ויקיפדיה/שירונט) וניתוח סטטיסטי מקורי · לא מתפרסמות הגדרות מעיתונים ·
<a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a></footer></div></body></html>""")

urls=[]
# ---------- category-length pages ----------
for cat,(plural,single) in CATS.items():
    by_len={}
    for t in cult.get(cat,[]):
        n=norm(t)
        if 2<=len(n)<=12: by_len.setdefault(len(n),[]).append((t,n))
    for L,items in sorted(by_len.items()):
        if len(items)<5: continue
        items.sort()
        slug=f'{cat}-{L}'
        lis=''.join(f'<li>{t}<br><small style="font-family:monospace;color:#5c5c5c">{n}</small></li>' for t,n in items)
        body=f"""<p><b>{len(items)} {plural}</b> שהשם שלהם נכתב ברשת התשבץ ב-<b>{L} אותיות</b>
(בתשבץ אין אותיות סופיות — ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ, והכתיב מוצג מתחת לכל שם).</p>
<ul class="grid">{lis}</ul>"""
        page(f'{OUT}/{slug}/index.html',
             f'{plural} ב-{L} אותיות — רשימה מלאה לתשבץ',
             f'כל ה{plural} שנכתבים ב-{L} אותיות ברשת תשבץ, כולל הכתיב ללא אותיות סופיות. {len(items)} ערכים.',
             body,
             {"@context":"https://schema.org","@type":"ItemList","name":f"{plural} ב-{L} אותיות",
              "numberOfItems":len(items)})
        urls.append(f'/milon/{slug}/')

# ---------- entity pages: only entities with rich data ----------
ent_index=[]
count=0
for cat,(plural,single) in CATS.items():
    for t in cult.get(cat,[]):
        n=norm(t)
        if not (2<=len(n)<=14): continue
        a=amb.get(n); c=cw.get(n,0); sb=subs['fwd'].get(n,[])+subs['rev'].get(n,[])
        rich=bool(a)or c>=2 or bool(sb)
        ent_index.append({'t':t,'n':n,'c':cat,'l':len(n)})
        if not rich or count>=1800: continue
        count+=1
        rows=f'<tr><th>סוג</th><td>{single}</td></tr><tr><th>אורך ברשת</th><td>{len(n)} אותיות</td></tr>'
        rows+=f'<tr><th>כתיב בתשבץ</th><td style="font-family:monospace">{n}</td></tr>'
        if c: rows+=f'<tr><th>הופעות בתשבצים</th><td>{c} פעמים (מתוך מדגם של 362 תשבצים)</td></tr>'
        if a: rows+=f'<tr><th>משמעויות נוספות</th><td>{", ".join(HEBSENSE.get(x,x) for x in a["senses"])}</td></tr>'
        if sb:
            pairs=', '.join(f'{x[0]}' for x in sb[:5])
            rows+=f'<tr><th>תחליפים בתשבצים</th><td>{pairs}</td></tr>'
        letters=' · '.join(sorted(set(n)))
        body=f"""<table>{rows}<tr><th>אותיות (לאנגרם)</th><td style="font-family:monospace">{letters}</td></tr></table>
<p style="margin-top:1rem"><a href="/milon/{urllib.parse.quote(f'{cat}-{len(n)}')}/">עוד {plural} ב-{len(n)} אותיות ←</a></p>"""
        page(f'{OUT}/e/{urllib.parse.quote(t,safe="")}/index.html',
             f'{t} בתשבץ — {len(n)} אותיות',
             f'{t}: {single}, {len(n)} אותיות ברשת התשבץ ({n}). משמעויות, הופעות ותחליפים לפותרי תשבצים.',
             body,
             {"@context":"https://schema.org","@type":"DefinedTerm","name":t,
              "inDefinedTermSet":f"{BASE}/milon/"})
        urls.append(f'/milon/e/{urllib.parse.quote(t,safe="")}/')

# ---------- search hub ----------
json.dump(ent_index,open(f'{OUT}/entities.json','w'),ensure_ascii=False)
cat_links=''
for cat,(plural,_) in CATS.items():
    Ls=sorted({e['l'] for e in ent_index if e['c']==cat and 2<=e['l']<=12})
    links=' '.join(f'<a href="/milon/{cat}-{L}/">{L}</a>' for L in Ls if f'/milon/{cat}-{L}/' in urls)
    cat_links+=f'<p><b>{plural}</b> לפי אורך: {links}</p>'
hub=f"""<p>מנוע חיפוש לפותרי תשבצים: שמות של שירים, זמרים, פוליטיקאים ומקומות — עם הכתיב המדויק ברשת
(ללא אותיות סופיות), אורך, ומשמעויות כפולות. {len(ent_index):,} ערכים.</p>
<input id="q" placeholder="חיפוש שם, או תבנית עם ? (למשל: ?ו?ה)" autocomplete="off">
<div id="res" class="grid" style="margin-top:.8rem"></div>
<h2>עיון לפי קטגוריה ואורך</h2>{cat_links}
<p style="margin-top:1.4rem">חסרה לכם תשובה שלמה? <a href="/solve/">עוזר הפתירה</a> פותר איתכם עם רמזים מדורגים והוכחות.</p>
<script>
let E=null;const q=document.getElementById('q'),res=document.getElementById('res');
fetch('/milon/entities.json').then(r=>r.json()).then(d=>E=d);
const CAT={{song:'שיר',artist:'זמר/להקה',politician:'פוליטיקאי/ת',place:'מקום'}};
q.oninput=()=>{{if(!E)return;const v=q.value.trim();res.innerHTML='';if(v.length<2)return;
let hits;
if(v.includes('?')){{const rx=new RegExp('^'+v.replace(/[א-ת]/g,m=>m).replace(/\\?/g,'.')+'$');
  hits=E.filter(e=>rx.test(e.n));}}
else hits=E.filter(e=>e.t.includes(v)||e.n.includes(v.replace(/[ךםןףץ]/g,m=>({{'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'}})[m])));
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));res.innerHTML=hits.slice(0,60).map(e=>'<li><b>'+esc(e.t)+'</b><br><small>'+esc(CAT[e.c]||'')+' · '+esc(e.l)+' אותיות · <span style="font-family:monospace">'+esc(e.n)+'</span></small></li>').join('');
}};
</script>"""
page(f'{OUT}/index.html','מילון תשבץ — חיפוש שירים, זמרים ואנשים לפי אורך',
     f'מנוע חיפוש לפותרי תשבצים: {len(ent_index):,} שירים, זמרים, פוליטיקאים ומקומות עם כתיב תשבץ מדויק, אורך ותבניות.',
     hub,{"@context":"https://schema.org","@type":"WebSite","name":"מילון תשבץ",
     "url":f"{BASE}/milon/"})
urls.insert(0,'/milon/')

# ---------- sitemap + robots ----------
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in ['/','/solve/','/methods/','/research/','/research/he/']+urls:
    sm+=f'  <url><loc>{BASE}{u}</loc></url>\n'
sm+='</urlset>'
open('docs/sitemap.xml','w').write(sm)
open('docs/robots.txt','w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
print(f'pages: {len(urls)} (entities with rich data: {count}); index entries: {len(ent_index)}')
