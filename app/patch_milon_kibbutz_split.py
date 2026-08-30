#!/usr/bin/env python3
"""One-off surgical patch: split the milon's mixed kibbutz+moshav category.

Why not just rerun build_seo.py: it needs the gitignored corpus assets
(data/culture/descriptions.json, data/shironet_songs.json), so in a fresh
clone a full rebuild destroys descriptions and entity pages (2026-08-28
incident). This script touches ONLY the kibbutz/moshav slice, reusing the
descriptions already published in docs/milon/entities.json plus the committed
solver/lex/descriptions_curated.json for the newly added kibbutzim.

What it does:
  1. entities.json: reclassify the old 'kibbutz' entries into kibbutz/moshav
     (by their own descriptions), move אלון הגליל to city_il, add the curated
     kibbutzim that the original wiki harvest missed (דליה, בארי, עין גדי...).
  2. Regenerate /milon/kibbutz-*/ and build /milon/moshav-*/ list pages with
     the same templates as build_seo.py (verified byte-identical on the old
     data before this shipped); delete kibbutz pages that fall under the
     min-item thresholds after the split.
  3. Patch the type label on existing /milon/e/ pages of these entities.
  4. Rebuild the /milon/ hub (also carries the pattern-search fix: '.', '?'
     and '*' wildcards) and update sitemap.xml.

The next full build_seo.py run (with the real corpus) supersedes all of this;
build_seo.py already carries the same category split and search fix.
"""
import html, json, os, re, shutil, urllib.parse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = 'docs/milon'
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)
BASE = 'https://tashbetz.gtmascode.dev'

cult = json.load(open('solver/lex/culture.json'))
cw = json.load(open('solver/crosswordese.json'))
CURATED = json.load(open('solver/lex/descriptions_curated.json'))
OLD = json.load(open(f'{OUT}/entities.json'))

CATS = {'song': ('שירים', 'שיר'), 'artist': ('זמרים ולהקות', 'זמר/להקה'),
        'politician': ('פוליטיקאים', 'פוליטיקאי/ת'),
        'neighborhood': ('שכונות', 'שכונה'), 'park': ('פארקים ושמורות טבע', 'פארק/שמורה'),
        'museum': ('מוזיאונים', 'מוזיאון'), 'nation': ('מדינות', 'מדינה'),
        'world_city': ('ערים ובירות בעולם', 'עיר בעולם'), 'athlete': ('ספורטאים', 'ספורטאי/ת'),
        'bible': ('דמויות מהתנ"ך', 'דמות מקראית'), 'author': ('סופרים ומשוררים', 'סופר/משורר'),
        'actor': ('שחקנים', 'שחקן/ית'), 'kibbutz': ('קיבוצים', 'קיבוץ'),
        'moshav': ('מושבים', 'מושב'),
        'city_il': ('ערים ויישובים בישראל', 'יישוב'), 'mountain': ('הרים ורכסים', 'הר'),
        'stream': ('נחלים', 'נחל'), 'river': ('נהרות העולם', 'נהר'),
        'valley': ('עמקים ובקעות', 'עמק'), 'lake_sea': ('ימים, אגמים ומפרצים', 'ים/אגם'),
        'desert': ('מדבריות', 'מדבר'), 'island': ('איים', 'אי'),
        'region': ('חבלי ארץ', 'חבל ארץ'), 'site': ('אתרים עתיקים וגנים לאומיים', 'אתר'),
        'military': ('מונחים צבאיים', 'מונח צבאי'),
        'common': ('תשובות נפוצות בתשבצים', 'תשובה נפוצה')}

STYLE = """<style>*{box-sizing:border-box}body{margin:0;background:#fff;color:#121212;font-family:'Frank Ruhl Libre','Arial Hebrew',serif;line-height:1.6}
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


def render(path, title, desc, body, jsonld=None, crumb=None):
    rel = '/' + os.path.relpath(path, 'docs').replace('index.html', '').replace(os.sep, '/')
    crumbs = [("דף הבית", BASE + "/"), ("מילון", BASE + "/milon/")]
    if rel not in ('/milon/', '/'): crumbs.append((crumb or title, BASE + rel))
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]}
    ld = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
    if jsonld: ld += f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
    canon = BASE + '/' + os.path.relpath(path, 'docs').replace('index.html', '').replace(os.sep, '/')
    esc_title = html.escape(title, quote=True)
    esc_desc = html.escape(desc, quote=True)
    og = f"""<meta property="og:type" content="article"><meta property="og:site_name" content="מילון תשבץ">
<meta property="og:title" content="{esc_title}"><meta property="og:description" content="{esc_desc}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{BASE}/milon/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="he_IL"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc_title}"><meta name="twitter:description" content="{esc_desc}">
<meta name="twitter:image" content="{BASE}/milon/og.png">"""
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc_title}</title>
<meta name="description" content="{esc_desc}"><link rel="canonical" href="{canon}">{og}{ld}{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>{esc_title}</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/nativ/">המשחק היומי</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div>
<div class="promo">☀️ <a href="/nativ/">נתיב - המשחק היומי הטוב לחובבי תשבצים</a> · חידה חדשה כל יום, עכשיו גם במצב קל</div></header>
{body}
<footer>מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) וניתוח סטטיסטי מקורי · לא מתפרסמות הגדרות מעיתונים ·
<a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a> · <a href="/nativ/">🪄 נתיב, המשחק היומי</a></footer></div></body></html>"""


def page(path, *a, **kw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(render(path, *a, **kw))


# ---------- the split itself ----------
# description of every entity the old milon filed under 'kibbutz'
old_kib_desc = {e['t']: e.get('d', '') for e in OLD if e['c'] == 'kibbutz'}


def get_desc(t):
    d = old_kib_desc.get(t) or CURATED.get(t, '')
    return d


def classify(t):
    d = old_kib_desc.get(t, '')
    if re.search(r'קיבוץ', d): return 'kibbutz'
    if re.search(r'מושב', d): return 'moshav'
    return 'city_il'  # אלון הגליל (yishuv kehilati)


new_names = [t for t in cult['kibbutz'] if t not in old_kib_desc]
assert all(t in CURATED for t in new_names), 'every added kibbutz needs a curated description'

# items per new category, same shape build_seo uses: (title, grid-spelling)
ITEMS = {cat: [(t, norm(t)) for t in cult[cat]] for cat in ('kibbutz', 'moshav')}

LETTER_ITEMS = {}
LEN_OK = {}   # lengths that actually get a category-length page
for cat in ('kibbutz', 'moshav'):
    _by = {}
    _byl = {}
    for t, n in ITEMS[cat]:
        if 2 <= len(n) <= 12 and n:
            _by.setdefault(n[0], []).append((t, n))
            _byl.setdefault(len(n), []).append(t)
    LETTER_ITEMS[cat] = {ch: it for ch, it in _by.items() if len(it) >= 5}
    LEN_OK[cat] = {L for L, it in _byl.items() if len(it) >= 3}


def letter_nav(cat, here=None):
    chs = [ch for ch in sorted(LETTER_ITEMS.get(cat, {})) if ch != here]
    if not chs: return ''
    ls = ' · '.join(f'<a href="/milon/{urllib.parse.quote(f"{cat}-letter-{ch}")}/">{ch}</a>' for ch in chs)
    return f'<p style="font-size:.9rem">לפי אות פותחת: {ls}</p>\n'


def build_len_page(cat, L, items):
    plural, single = CATS[cat]
    items = sorted(items, key=lambda x: (-cw.get(x[1], 0), x[0]))

    def _li(t, n):
        b = f' <span class="k" style="font-size:.55rem">{cw[n]}×</span>' if cw.get(n, 0) >= 2 else ''
        d = get_desc(t)
        dd = f'<br><small>{d[:90]}</small>' if d else ''
        return f'<li id="{n}"><b>{t}</b>{b}{dd}<br><small style="font-family:monospace;color:#5c5c5c">{n}</small></li>'

    lis = ''.join(_li(t, n) for t, n in items)
    body = f"""<p><b>{len(items)} {plural}</b> שהשם שלהם נכתב ברשת התשבץ ב-<b>{L} אותיות</b>
(בתשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ, והכתיב מוצג מתחת לכל שם).</p>
{letter_nav(cat)}<ul class="grid">{lis}</ul>"""
    return (f'{OUT}/{cat}-{L}/index.html',
            f'{plural} ב-{L} אותיות לתשבץ ותשחץ: {len(items)} פתרונות',
            f'{single} ב-{L} אותיות? הרשימה המלאה לפתרון תשבצים: {len(items)} {plural}, ממוינים לפי שכיחות בתשבצים, עם הכתיב המדויק ללא אותיות סופיות.',
            body,
            {"@context": "https://schema.org", "@type": "ItemList", "name": f"{plural} ב-{L} אותיות",
             "numberOfItems": len(items)})


def build_letter_page(cat, ch, items):
    plural, single = CATS[cat]
    items = sorted(items, key=lambda x: (-cw.get(x[1], 0), x[0]))
    lis = ''.join(
        f'<li id="L{n}"><b>{t}</b>'
        f'{f" <span class=\"k\" style=\"font-size:.55rem\">{cw[n]}×</span>" if cw.get(n, 0) >= 2 else ""}'
        f'{f"<br><small>{get_desc(t)[:90]}</small>" if get_desc(t) else ""}'
        f'<br><small style="font-family:monospace;color:#5c5c5c">{n} · {len(n)} אותיות</small></li>'
        for t, n in items[:400])
    lens = sorted({len(n) for _, n in items})
    body = f"""<p><b>{len(items)} {plural}</b> שמתחילים באות <b>{ch}</b>, עם מספר האותיות של כל אחד
ברשת התשבץ (בתשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ).</p>
<p style="font-size:.9rem">אורכים זמינים: {', '.join(f'<a href="/milon/{urllib.parse.quote(f"{cat}-{L}")}/">{L}</a>' for L in lens if L in LEN_OK[cat])}</p>
{letter_nav(cat, here=ch)}<ul class="grid">{lis}</ul>"""
    return (f'{OUT}/{cat}-letter-{ch}/index.html',
            f'{plural} באות {ch}: {len(items)} תשובות לתשבץ ותשחץ',
            f'{single} שמתחיל באות {ch}? {len(items)} אפשרויות עם מספר האותיות והכתיב המדויק ברשת, '
            f'ממוינות לפי שכיחות בתשבצים. לפתרון תשבצי היגיון ותשחצים.',
            body,
            {"@context": "https://schema.org", "@type": "ItemList",
             "name": f"{plural} באות {ch}", "numberOfItems": len(items)},
            f'{plural} באות {ch}')


def list_pages(cat):
    """(args...) for every kibbutz/moshav list page the split produces"""
    out = []
    by_len = {}
    for t, n in ITEMS[cat]:
        if 2 <= len(n) <= 12: by_len.setdefault(len(n), []).append((t, n))
    for L, items in sorted(by_len.items()):
        if len(items) < 3: continue
        out.append(('len', build_len_page(cat, L, items)))
    for ch, items in sorted(LETTER_ITEMS[cat].items()):
        out.append(('letter', build_letter_page(cat, ch, items)))
    return out


def main():
    # ---------- 1. entities.json ----------
    new_entities = []
    kib_block_done = False
    for e in OLD:
        if e['c'] != 'kibbutz':
            new_entities.append(e)
            continue
        if not kib_block_done:
            # replace the whole old block, in category order, at its position
            kib_block_done = True
            old_by_t = {x['t']: x for x in OLD if x['c'] == 'kibbutz'}
            for cat in ('kibbutz', 'moshav'):
                for t in cult[cat]:
                    n = norm(t)
                    if not (2 <= len(n) <= 14): continue
                    old = old_by_t.get(t)
                    new_entities.append({'t': t, 'n': n, 'c': cat, 'l': len(n),
                                         'd': (old['d'] if old else CURATED[t][:70]),
                                         'p': (old['p'] if old else 0)})
        if classify(e['t']) == 'city_il' and e['t'] not in cult['kibbutz'] and e['t'] not in cult['moshav']:
            new_entities.append({**e, 'c': 'city_il'})
    json.dump(new_entities, open(f'{OUT}/entities.json', 'w'), ensure_ascii=False)
    print(f'entities.json: {len(OLD)} -> {len(new_entities)}')

    # ---------- 2. list pages ----------
    made = []
    for cat in ('kibbutz', 'moshav'):
        for _, args in list_pages(cat):
            page(*args[:5], **({'crumb': args[5]} if len(args) > 5 else {}))
            made.append('/' + os.path.relpath(args[0], 'docs').replace('index.html', ''))
    # kibbutz pages that no longer meet the thresholds
    keep = {p.strip('/').split('/')[-1] for p in made}
    removed = []
    for d in os.listdir(OUT):
        if re.match(r'^kibbutz-', d) and d not in keep:
            shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
            removed.append(d)
    print(f'list pages written: {len(made)}, removed: {removed}')

    # ---------- 3. type label on existing entity pages ----------
    patched = 0
    for e in new_entities:
        if e['c'] not in ('kibbutz', 'moshav') or not e['p']: continue
        plural, single = CATS[e['c']]
        p = f'{OUT}/e/{urllib.parse.quote(e["t"], safe="")}/index.html'
        if not os.path.exists(p): continue
        s = open(p).read()
        s2 = (s.replace('קיבוץ/מושב', single)
                .replace('עוד קיבוצים ומושבים ב-', f'עוד {plural} ב-')
                .replace(f'/milon/kibbutz-{e["l"]}/', f'/milon/{e["c"]}-{e["l"]}/'))
        if s2 != s:
            open(p, 'w').write(s2); patched += 1
    print(f'entity pages patched: {patched}')

    # ---------- 4. hub + sitemap ----------
    patch_hub(new_entities, made)
    patch_sitemap(made)


def patch_hub(entities, made):
    """rebuild the two category lines and the search script inside /milon/index.html"""
    hub_path = f'{OUT}/index.html'
    s = open(hub_path).read()

    def cat_line(cat):
        plural, _ = CATS[cat]
        Ls = sorted({e['l'] for e in entities if e['c'] == cat and 2 <= e['l'] <= 12})
        links = ' '.join(f'<a href="/milon/{cat}-{L}/">{L}</a>' for L in Ls
                         if f'/milon/{cat}-{L}/' in made)
        return f'<p><b>{plural}</b> לפי אורך: {links}</p>' + letter_nav(cat)

    # the old combined kibbutz line (plus its letter-nav <p>) -> two fresh pairs
    m = re.search(r'<p><b>קיבוצים ומושבים</b>.*?</p><p style="font-size:\.9rem">לפי אות פותחת:.*?</p>\n?',
                  s, re.S)
    assert m, 'old kibbutz hub line not found'
    s = s[:m.start()] + cat_line('kibbutz') + cat_line('moshav') + s[m.end():]

    # counts: the hub states the entity total in text, meta and JSON-LD
    old_total, new_total = f'{len(OLD):,}', f'{len(entities):,}'
    s = s.replace(f'{old_total} ערכים', f'{new_total} ערכים')
    s = s.replace(f'{old_total} שירים', f'{new_total} שירים')

    # category label for search results
    s = s.replace('"kibbutz": "קיבוץ/מושב", "city_il"',
                  '"kibbutz": "קיבוץ", "moshav": "מושב", "city_il"')

    # the pattern-search fix (mirrors the build_seo.py template): '.', '?', '*'
    # all act as wildcards and final letters are normalised inside patterns
    old_js = """q.oninput=()=>{if(!E)return;const v=q.value.trim();res.innerHTML='';if(v.length<2)return;
let hits;
if(v.includes('?')){const rx=new RegExp('^'+v.replace(/[א-ת]/g,m=>m).replace(/\\?/g,'.')+'$');
  hits=E.filter(e=>rx.test(e.n));}
else hits=E.filter(e=>e.t.includes(v)||e.n.includes(v.replace(/[ךםןףץ]/g,m=>({'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'})[m])));"""
    new_js = """const FINMAP={'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'},canon=s=>s.replace(/[ךםןףץ]/g,m=>FINMAP[m]);
q.oninput=()=>{if(!E)return;const v=q.value.trim();res.innerHTML='';if(v.length<2)return;
let hits;
if(/[?.*]/.test(v)){const rx=new RegExp('^'+canon(v).split('').map(ch=>ch==='*'?'.*':(ch==='?'||ch==='.')?'.':(/[א-ת]/.test(ch)?ch:'')).join('')+'$');
  hits=E.filter(e=>rx.test(e.n));}
else{const c=canon(v);hits=E.filter(e=>e.t.includes(v)||e.n.includes(c));
const sc=e=>(e.t===v||e.n===c)?2:(e.t.startsWith(v)||e.n.startsWith(c))?1:0;hits.sort((a,b)=>sc(b)-sc(a));}"""
    assert old_js in s, 'search script drifted from the expected template'
    s = s.replace(old_js, new_js)
    s = s.replace('תבנית: ? או . לאות חסרה (למשל: ?ו?ה)',
                  'תבנית: ? או . לאות חסרה (למשל: ד?יה, ?ו?ה)')

    open(hub_path, 'w').write(s)
    print('hub rebuilt')


def patch_sitemap(made):
    sm = open('docs/sitemap.xml').read().splitlines(keepends=True)
    out, inserted = [], False
    new_lines = [f'  <url><loc>{BASE}/milon/{urllib.parse.quote(u.strip("/").split("/")[-1])}/</loc></url>\n'
                 for u in made]
    for line in sm:
        if '/milon/kibbutz-' in line:
            if not inserted:
                out.extend(new_lines); inserted = True
            continue
        out.append(line)
    assert inserted, 'no kibbutz URLs found in sitemap'
    open('docs/sitemap.xml', 'w').writelines(out)
    print(f'sitemap: {len(new_lines)} kibbutz/moshav URLs')


if __name__ == '__main__':
    main()
