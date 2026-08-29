#!/usr/bin/env python3
"""Programmatic-SEO מילון: entity + category/length pages from our own indices.

Competitor gap (measured 2026-08): note.co.il/מורדו index by DEFINITION text.
The original bet here was the "זמרת 4 אותיות" length shape, and 90 days of
Search Console says that bet was wrong: of 31 Hebrew queries, ZERO searched by
length, while four searched by starting letter and one by "<word> פירוש".
Length pages stay (they are cheap and they do rank), but the letter index and
the פירוש framing below exist because the query log asked for them.

  /milon/                      search hub (client-side: name/pattern/length)
  /milon/<cat>-<len>/          category-length lists (זמרים ב-4 אותיות...)
  /milon/<cat>-letter-<א>/     category-letter lists (ערים באות א...)
  /milon/e/<name>/             entity pages for entities with rich data
All content is derived (names from wikipedia/shironet titles, our own stats).
No newspaper clue text is published: the line the whole project keeps.
"""
import html, json, os, re, urllib.parse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT='docs/milon'; os.makedirs(OUT,exist_ok=True)
FIN=str.maketrans('ךםןףץ','כמנפצ')
norm=lambda s:re.sub(r'[^א-ת]','',s or '').translate(FIN)
BASE='https://tashbetz.gtmascode.dev'

cult=json.load(open('solver/lex/culture.json'))
# HARD GUARD (added after the 2026-08-28 incident): descriptions.json is
# gitignored, so a fresh clone doesn't have it. Running this builder without it
# silently strips 12K+ descriptions from entities.json and then the orphan
# cleanup below deletes thousands of "poor" entity pages that were actually
# rich. Refuse to run rather than publish a degraded milon; pass
# ALLOW_BARE_MILON=1 only if a description-less build is truly intended.
if not os.path.exists('data/culture/descriptions.json') and not os.environ.get('ALLOW_BARE_MILON'):
    raise SystemExit('build_seo: data/culture/descriptions.json missing (gitignored corpus '
                     'asset). Rebuilding without it destroys entity pages. Restore the data '
                     'or set ALLOW_BARE_MILON=1 to override.')
DESC=json.load(open('data/culture/descriptions.json')) if os.path.exists('data/culture/descriptions.json') else {}
# Source descriptions occasionally carry an em-dash; the project publishes none,
# so normalise at load rather than trusting upstream data to stay clean.
DESC={k:(v or '').replace('\u2014','-').replace('\u2013','-') for k,v in DESC.items()}
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
# Sense labels are shown to readers (entity tables and meta descriptions), so
# every key in ambiguities.json needs Hebrew. Most are category ids that CATS
# already names, so derive those and only spell out the ones CATS has no entry
# for; an unmapped key used to fall through and print raw English ("bible")
# in the middle of a Hebrew sentence.
HEBSENSE={k:single for k,(plural,single) in CATS.items()}
HEBSENSE.update({'common_word':'מילה מן המילון','given_name':'שם פרטי','surname':'שם משפחה',
 'role_noun':'תפקיד/פועל וגם שם','song':'שם שיר','song_word':'מילה מתוך שיר','artist':'זמר/להקה',
 'politician':'פוליטיקאי/ת','place':'מקום','answer':'הופיעה כתשובה בתשבצים'})

STYLE="""<style>*{box-sizing:border-box}body{margin:0;background:#fff;color:#121212;font-family:'Frank Ruhl Libre','Arial Hebrew',serif;line-height:1.6}
.w{max-width:52rem;margin:0 auto;padding:1rem 1.2rem}header{border-bottom:1px solid #121212;box-shadow:0 3px 0 -1px #121212;padding:.8rem 0}
h1{font-size:1.6rem;margin:.2rem 0}.k{font-family:monospace;font-size:.65rem;letter-spacing:.12em;color:#fff;background:#f22b39;display:inline-block;padding:.12rem .5rem}
a{color:#f22b39}h2{border-bottom:3px solid #f22b39;display:inline-block;font-size:1.1rem;padding-bottom:.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(11rem,1fr));gap:.4rem;padding:0;list-style:none}
.grid li{background:#f6f5f3;padding:.35rem .6rem;border-radius:3px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #dcdcdc;padding:.4rem .5rem;text-align:right}
footer{margin:2.5rem 0 1.5rem;border-top:1px solid #dcdcdc;padding-top:.8rem;font-size:.8rem;color:#5c5c5c}
.crumb{font-size:.8rem;color:#5c5c5c;margin:.6rem 0}input{font:inherit;padding:.5rem;border:1.5px solid #121212;border-radius:3px;width:100%}
.promo{background:#fff4d6;border:1.5px solid #121212;border-radius:3px;padding:.45rem .7rem;margin:.7rem 0 0;font-size:.9rem}
.promo a{font-weight:700}
@media(prefers-color-scheme:dark){body{background:#161616;color:#f2f0ec}.grid li{background:#222}td,th{border-color:#3a3a3a}.promo{background:#3a3115;border-color:#f2f0ec}}</style>"""

def page(path,title,desc,body,jsonld=None,crumb=None):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    rel='/'+os.path.relpath(path,'docs').replace('index.html','').replace(os.sep,'/')
    crumbs=[("דף הבית",BASE+"/"),("מילון",BASE+"/milon/")]
    # crumb is passed explicitly: deriving it by splitting the title on a
    # separator silently breaks the moment a title's punctuation changes.
    if rel not in ('/milon/','/'): crumbs.append((crumb or title,BASE+rel))
    bc={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":n,"item":u} for i,(n,u) in enumerate(crumbs)]}
    ld=f'<script type="application/ld+json">{json.dumps(bc,ensure_ascii=False)}</script>'
    if jsonld: ld+=f'<script type="application/ld+json">{json.dumps(jsonld,ensure_ascii=False)}</script>'
    canon=BASE+'/'+os.path.relpath(path,'docs').replace('index.html','').replace(os.sep,'/')
    # Escape before interpolating: entry names legitimately contain quotes
    # (song titles like "ציפור נדירה"), which silently truncated the meta
    # description mid-attribute and left Google with no snippet to read.
    esc_title=html.escape(title,quote=True)
    esc_desc=html.escape(desc,quote=True)
    # Social cards: every generated page carries og/twitter tags. Without them a
    # shared link renders as a bare URL, which is most of these pages' first
    # impression. Titles and descriptions are already per page, so only the
    # image is shared.
    og=f"""<meta property="og:type" content="article"><meta property="og:site_name" content="מילון תשבץ">
<meta property="og:title" content="{esc_title}"><meta property="og:description" content="{esc_desc}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{BASE}/milon/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="he_IL"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc_title}"><meta name="twitter:description" content="{esc_desc}">
<meta name="twitter:image" content="{BASE}/milon/og.png">"""
    open(path,'w').write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc_title}</title>
<meta name="description" content="{esc_desc}"><link rel="canonical" href="{canon}">{og}{ld}{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>{esc_title}</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/nativ/">המשחק היומי</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div>
<div class="promo">☀️ <a href="/nativ/">נתיב - המשחק היומי הטוב לחובבי תשבצים</a> · חידה חדשה כל יום, עכשיו גם במצב קל</div></header>
{body}
<footer>מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) וניתוח סטטיסטי מקורי · לא מתפרסמות הגדרות מעיתונים ·
<a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a> · <a href="/nativ/">🪄 נתיב, המשחק היומי</a></footer></div></body></html>""")

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
        ss=list(dict.fromkeys(artist_rel[n]['songs']))[:3]   # the source list repeats titles
        return 'בין השירים: '+', '.join(f'"{x}"' for x in ss) if ss else ''
    if cat=='military': return MIL.get(t,'')
    if cat=='common':
        prs=subs['fwd'].get(n,[])+subs['rev'].get(n,[])
        if prs:
            uniq=list(dict.fromkeys(x[0] for x in prs))[:3]
            return 'בהסברי תשבצים מקושרת ל: '+', '.join(uniq)
    return ''


SNIPPET_MAX=155   # Google truncates around here; anything past it is wasted.

def meta_desc(t,n,single,d,c,a,sb,related=()):
    """Per-entry snippet built from whatever signals THIS word actually has.

    The old line was one template with a fixed tail ("לפותרי תשבצים ותשחצים"),
    which made 4,912 of 5,301 descriptions end identically and left a ~90 char
    median against a ~155 char budget. Google rewrites boilerplate snippets,
    and the search console queries showed why it matters: people arrive on
    "<word> פירוש" (what does it mean) and on clue-shaped queries (what is the
    N-letter answer). So: definition first, because that is the intent, then
    the crossword facts, then whichever extra signal this entry carries, so
    two entries never read the same.
    """
    facts=[]
    lead=f'{t}: {d}.' if d else f'איך כותבים {t} בתשבץ?'
    facts.append(f'{single} ב-{len(n)} אותיות, כתיב ברשת: {n}.')
    if c>=2: facts.append(f'הופיע {c} פעמים במדגם של 362 תשבצים.')
    if sb:
        uniq=list(dict.fromkeys(x[0] for x in sb))[:3]
        if uniq: facts.append('מרומז בתשבצים גם כ: '+', '.join(uniq)+'.')
    if a and a.get('senses'):
        extra=[HEBSENSE.get(x,x) for x in a['senses']][:3]
        if extra: facts.append('משמעויות נוספות: '+', '.join(extra)+'.')
    out=lead[:SNIPPET_MAX]
    for f in facts:
        if len(out)+1+len(f)>SNIPPET_MAX: break
        out=f'{out} {f}'
    # Sparse entries (a bare definition and nothing else) would otherwise sit
    # at ~55 chars and waste two thirds of the snippet. Same-length neighbours
    # fill it with something that both varies per entry and is the next thing
    # a stuck solver wants anyway.
    if len(out)<110 and related:
        room=SNIPPET_MAX-len(out)-len(' ערכים באותו אורך: .')
        picks=[]
        for r in related:
            if sum(len(x)+2 for x in picks)+len(r)>room: break
            picks.append(r)
        if picks: out=f'{out} ערכים באותו אורך: '+', '.join(picks)+'.'
    return out


urls=[]

# Which category-letter pages will exist. Computed before the length pages so
# those can link to them: #17 shipped 248 letter pages with no inbound internal
# link anywhere on the site, discoverable only through the sitemap. They took 0
# impressions in the two days after deploy while the length pages kept absorbing
# the letter-shaped queries at position ~57.
LETTER_ITEMS={}
for cat in CATS:
    _by={}
    for t in cult.get(cat,[]):
        n=norm(t)
        if 2<=len(n)<=12 and n: _by.setdefault(n[0],[]).append((t,n))
    LETTER_ITEMS[cat]={ch:it for ch,it in _by.items() if len(it)>=5}

def letter_nav(cat,here=None):
    """links to the sibling category-letter pages; '' when the category has none"""
    chs=[ch for ch in sorted(LETTER_ITEMS.get(cat,{})) if ch!=here]
    if not chs: return ''
    ls=' · '.join(f'<a href="/milon/{urllib.parse.quote(f"{cat}-letter-{ch}")}/">{ch}</a>' for ch in chs)
    return f'<p style="font-size:.9rem">לפי אות פותחת: {ls}</p>\n'

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
(בתשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ, והכתיב מוצג מתחת לכל שם).</p>
{letter_nav(cat)}<ul class="grid">{lis}</ul>"""
        page(f'{OUT}/{slug}/index.html',
             f'{plural} ב-{L} אותיות לתשבץ ותשחץ: {len(items)} פתרונות',
             f'{single} ב-{L} אותיות? הרשימה המלאה לפתרון תשבצים: {len(items)} {plural}, ממוינים לפי שכיחות בתשבצים, עם הכתיב המדויק ללא אותיות סופיות.',
             body,
             {"@context":"https://schema.org","@type":"ItemList","name":f"{plural} ב-{L} אותיות",
              "numberOfItems":len(items)})
        urls.append(f'/milon/{slug}/')

# ---------- category-LETTER pages ----------
# Search Console (90d, measured 2026-08-17) says the length premise this file
# was built on is wrong: of 31 Hebrew queries, ZERO searched by word length,
# while four searched by starting letter ("עיר באות א בישראל", "עיר בישראל
# באות מ"). Those queries currently land on a length page that does not answer
# them, at position ~60. Index the dimension people actually type.
for cat,(plural,single) in CATS.items():
    for ch,items in sorted(LETTER_ITEMS[cat].items()):
        items.sort(key=lambda x:(-cw.get(x[1],0),x[0]))
        slug=f'{cat}-letter-{ch}'
        lis=''.join(
            f'<li id="L{n}"><b>{t}</b>'
            f'{f" <span class=\"k\" style=\"font-size:.55rem\">{cw[n]}×</span>" if cw.get(n,0)>=2 else ""}'
            f'{f"<br><small>{get_desc(cat,t,n)[:90]}</small>" if get_desc(cat,t,n) else ""}'
            f'<br><small style="font-family:monospace;color:#5c5c5c">{n} · {len(n)} אותיות</small></li>'
            for t,n in items[:400])
        lens=sorted({len(n) for _,n in items})
        body=f"""<p><b>{len(items)} {plural}</b> שמתחילים באות <b>{ch}</b>, עם מספר האותיות של כל אחד
ברשת התשבץ (בתשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ).</p>
<p style="font-size:.9rem">אורכים זמינים: {', '.join(f'<a href="/milon/{urllib.parse.quote(f"{cat}-{L}")}/">{L}</a>' for L in lens if L>=2)}</p>
{letter_nav(cat,here=ch)}<ul class="grid">{lis}</ul>"""
        page(f'{OUT}/{slug}/index.html',
             f'{plural} באות {ch}: {len(items)} תשובות לתשבץ ותשחץ',
             f'{single} שמתחיל באות {ch}? {len(items)} אפשרויות עם מספר האותיות והכתיב המדויק ברשת, '
             f'ממוינות לפי שכיחות בתשבצים. לפתרון תשבצי היגיון ותשחצים.',
             body,
             {"@context":"https://schema.org","@type":"ItemList",
              "name":f"{plural} באות {ch}","numberOfItems":len(items)},
             crumb=f'{plural} באות {ch}')
        urls.append(f'/milon/{urllib.parse.quote(slug)}/')

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
    # "אבוס פירוש" is a real query that lands here, so entries that actually
    # carry a definition say so in the title; the rest keep the crossword framing.
    page(f'{OUT}/e/{urllib.parse.quote(t,safe="")}/index.html',
         (f'{t}: פירוש ומשמעות, {single} ב-{len(n)} אותיות בתשבץ' if d else
          f'{t} בתשבץ: {single} ב-{len(n)} אותיות (כתיב: {n})'),
         meta_desc(t,n,single,d,c,a,sb,related),
         body, ld, crumb=t)
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
    cat_links+=f'<p><b>{plural}</b> לפי אורך: {links}</p>'+letter_nav(cat)
cat_json=json.dumps({c:v[1] for c,v in CATS.items()},ensure_ascii=False)
hub=f"""<p>מנוע חיפוש לפותרי תשבצים: שמות של שירים, זמרים, פוליטיקאים ומקומות, עם הכתיב המדויק ברשת
(ללא אותיות סופיות), אורך, ומשמעויות כפולות. {len(ent_index):,} ערכים.</p>
<input id="q" placeholder="חיפוש שם, או תבנית: ? או . לאות חסרה (למשל: ?ו?ה)" autocomplete="off">
<p style="margin:.5rem 0"><a href="/milon/anagram/"><b>יש לכם אותיות מבולבלות? → חיפוש אנגרם</b></a></p>
<div id="res" class="grid" style="margin-top:.8rem"></div>
<h2>עיון לפי קטגוריה, אורך ואות פותחת</h2>{cat_links}
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
page(f'{OUT}/index.html','מילון תשבץ: חיפוש לפי אורך, תבנית ואנגרם',
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
# The interactive script lives in a PLAIN (non-f, non-raw) triple-quoted
# string, so every backslash meant for JavaScript must be doubled. A bare
# '\n' here once shipped as a real newline inside a JS string literal,
# which was a SyntaxError that silently killed the whole page script.
ana_body="""<style>.how{background:#f6f5f3;border-radius:3px;padding:.7rem 1rem;margin:.8rem 0}
.how ol{margin:.4rem 0 0;padding-inline-start:1.2rem}.how li{margin:.3rem 0}
.bar{display:flex;justify-content:space-between;gap:1rem;font-size:.85rem;color:#5c5c5c;margin:.35rem 0;flex-wrap:wrap}
#st.ok{color:#1a7f37}
.chip{font:inherit;font-family:monospace;background:#f6f5f3;border:1.5px solid #121212;border-radius:3px;padding:.15rem .6rem;cursor:pointer;margin-inline-end:.35rem;color:inherit}
.chip:hover{background:#fff4d6}.hint{color:#5c5c5c}
@media(prefers-color-scheme:dark){.how{background:#222}.chip{background:#222;border-color:#f2f0ec}.chip:hover{background:#3a3115}#st.ok{color:#5fc57d}}</style>
<p>בתשבץ היגיון, הגדרת אנגרם מסתירה את אותיות הפתרון בתוך ההגדרה עצמה, רק בסדר מבולבל.
הכלי הזה עושה את העבודה: מקלידים את האותיות ומקבלים מיד כל שם, מקום ומילה שמורכבים בדיוק מהן.
כל המאגר, שמות, ביטויים ומילות מילון, נטען אוטומטית ברקע ברגע שהעמוד נפתח. אין מה להפעיל ואין על מה ללחוץ.</p>
<div class="how"><b>איך משתמשים? שלושה צעדים:</b><ol>
<li>מאתרים בהגדרה את המילה או המילים שמהן מערבבים. רמזים נפוצים לאנגרם: "בבלגן", "מבולבל", "הרוס", "מפוזר", "השתגע", "אחרת".</li>
<li>מקלידים כאן את האותיות, בכל סדר שהוא. רווחים לא מפריעים, ואותיות סופיות (ם ן ץ ף ך) מיושרות אוטומטית לכתיב רשת.</li>
<li>התוצאות מופיעות מיד תוך כדי ההקלדה, החל מ-3 אותיות. בלי כפתור חיפוש ובלי המתנה.</li>
</ol></div>
<label for="a" style="display:block;font-weight:700;margin-top:1rem">האותיות שבידיכם:</label>
<input id="a" placeholder="למשל: ליבנוצר" autocomplete="off">
<div class="bar"><span id="cnt"></span><span id="st">טוען את המאגר ברקע... אפשר כבר להקליד.</span></div>
<p style="font-size:.9rem;margin:.5rem 0">אין אותיות ביד? נסו דוגמה:
<button type="button" class="chip">ליבנוצר</button><button type="button" class="chip">הצלרישאמ</button><button type="button" class="chip">שמיוילר</button></p>
<div id="ares" style="margin-top:.8rem"></div>
<p style="margin-top:1.4rem">רוצים גם הוכחה שהאנגרם נכון? <a href="/solve/">עוזר הפתירה</a> בודק מכנית כל טענה.</p>
<script>
const a=document.getElementById('a'),ares=document.getElementById('ares'),st=document.getElementById('st'),cnt=document.getElementById('cnt');
let EIDX=null,LIDX=null,EN=0,LN=0;
const CAT=__CATJSON__;
const FIN={'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'};
const sig=w=>w.replace(/[ךםןףץ]/g,m=>FIN[m]).split('').sort().join('');
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function upd(){if(EIDX&&LIDX){st.textContent='המאגר טעון במלואו: '+EN.toLocaleString()+' שמות וביטויים ו-'+LN.toLocaleString()+' מילות מילון.';st.className='ok'}}
function fail(){st.textContent='חלק מהמאגר לא נטען. רעננו את העמוד ונסו שוב.';st.className=''}
fetch('/milon/entities.json').then(r=>r.json()).then(d=>{EIDX=new Map();for(const e of d){const s=sig(e.n);const l=EIDX.get(s);l?l.push(e):EIDX.set(s,[e])}EN=d.length;upd();run()}).catch(fail);
fetch('/solve/data/lexicon.txt').then(r=>r.text()).then(t=>{LIDX=new Map();for(const w of t.split(/\\r?\\n/)){if(!w)continue;LN++;const s=sig(w);const l=LIDX.get(s);l?l.push(w):LIDX.set(s,[w])}upd();run()}).catch(fail);
function run(){const v=a.value.replace(/[^א-ת]/g,'');
cnt.textContent=v?'הוקלדו '+v.length+' אותיות':'';
if(v.length<3){ares.innerHTML=v?'<p class="hint">המשיכו להקליד, החיפוש מתחיל מ-3 אותיות.</p>':'';return}
if(!EIDX){ares.innerHTML='<p class="hint">המאגר עוד בטעינה, התוצאות יופיעו כאן אוטומטית בעוד רגע.</p>';return}
const t=sig(v),seen=new Set(),ents=[];
for(const e of (EIDX.get(t)||[])){const k=e.t+'|'+e.n;if(seen.has(k))continue;seen.add(k);ents.push(e)}
ents.sort((x,y)=>(y.p||0)-(x.p||0));
const shown=new Set(ents.map(e=>e.n));
const words=LIDX?(LIDX.get(t)||[]).filter(w=>!shown.has(w)):[];
let h='';
if(ents.length){h+='<h2>שמות וביטויים ('+ents.length+')</h2><ul class="grid">'+ents.slice(0,60).map(e=>{const u=e.p?('/milon/e/'+encodeURIComponent(e.t)+'/'):('/milon/'+e.c+'-'+e.l+'/#'+encodeURIComponent(e.n));return '<li><a href="'+u+'" style="text-decoration:none;color:inherit"><b style="color:#f22b39">'+esc(e.t)+'</b><br><small>'+esc(CAT[e.c]||'')+' · <span style="font-family:monospace">'+esc(e.n)+'</span></small></a></li>'}).join('')+'</ul>'}
if(words.length){h+='<h2>מילים מהמילון ('+words.length+')</h2><ul class="grid">'+words.slice(0,60).map(w=>'<li>'+esc(w)+'</li>').join('')+'</ul>'}
if(!h)h='<p class="hint">'+(LIDX?'לא נמצאה אף מילה או שם שמורכבים בדיוק מהאותיות האלה. בדקו שהוקלדו כל האותיות, בלי אות מיותרת.':'אין התאמה בשמות, והמילון המלא עוד בטעינה. התוצאות יתעדכנו אוטומטית כשיסתיים.')+'</p>';
ares.innerHTML=h}
a.oninput=run;
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{a.value=b.textContent;a.focus();run()});
</script>""".replace('__CATJSON__',cat_json)
page(f'{OUT}/anagram/index.html',
     'חיפוש אנגרם לתשבץ: מי מסתתר באותיות המבולבלות',
     'פותר אנגרמות לתשבצי היגיון: מקלידים את האותיות המבולבלות ומקבלים מיד כל שם, מקום ומילה שהם ערבוב מדויק שלהן. כל המאגר נטען אוטומטית, בלי כפתורים ובלי המתנה.',
     ana_body,[{"@context":"https://schema.org","@type":"WebApplication","name":"חיפוש אנגרם לתשבץ",
     "url":f"{BASE}/milon/anagram/","applicationCategory":"Utility"},
     {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
      {"@type":"Question","name":"איך מזהים הגדרת אנגרם בתשבץ היגיון?",
       "acceptedAnswer":{"@type":"Answer","text":"מחפשים בהגדרה מילת ערבוב כמו בבלגן, מבולבל, הרוס, מפוזר או השתגע. המילה שלידה מכילה בדיוק את אותיות הפתרון, בסדר אחר."}},
      {"@type":"Question","name":"איך משתמשים בחיפוש האנגרם?",
       "acceptedAnswer":{"@type":"Answer","text":"מקלידים את האותיות בכל סדר שהוא, והתוצאות מופיעות מיד תוך כדי הקלדה, החל מ-3 אותיות. אין צורך ללחוץ על כפתור, וכל המאגר נטען אוטומטית ברקע."}},
      {"@type":"Question","name":"מה עושים עם רווחים ואותיות סופיות?",
       "acceptedAnswer":{"@type":"Answer","text":"שום דבר. רווחים מסוננים אוטומטית, ואותיות סופיות (ם ן ץ ף ך) מיושרות לכתיב רשת (מ נ צ פ כ) כמקובל בתשבצים."}}]}])
urls.insert(1,'/milon/anagram/')

# ---------- sitemap + robots ----------
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
# Trainer pages (app/build_trainer.py) join the same sitemap rather than a
# second competing one; missing file just means the trainer has not been built.
trainer=[]
if os.path.isdir('docs/tirgul'):
    trainer=['/tirgul/']+[f'/tirgul/{d}/' for d in sorted(os.listdir('docs/tirgul'),
             key=lambda x:(not x.isdigit(), int(x) if x.isdigit() else x))
             if os.path.exists(f'docs/tirgul/{d}/index.html')]
for u in ['/','/nativ/','/solve/','/methods/','/research/','/research/he/']+trainer+urls:
    sm+=f'  <url><loc>{BASE}{u}</loc></url>\n'
sm+='</urlset>'
open('docs/sitemap.xml','w').write(sm)
open('docs/robots.txt','w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
print(f'pages: {len(urls)} (entities with rich data: {count}); index entries: {len(ent_index)}')
