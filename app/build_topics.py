#!/usr/bin/env python3
"""Topic crosswords: /nosim/ hub, a page per subject, a playable page per level.

Reads docs/nosim/puzzles.json (written by --generate, which calls
solver/topicgen.py) and writes:

  /nosim/                     hub, every subject
  /nosim/<topic>/             one subject, its four levels
  /nosim/<topic>/<level>/     one playable crossword

Two board families are rendered from the same data (solver/grids_topic.py):

  תשבץ   numbered board, clues listed beside it
  תשחץ   the clues are printed INSIDE the board, in the cell the entry starts
         next to, with an arrow: ← for an entry running leftwards across the
         row, ↓ for one running down. That is what makes it an arrowword and
         not a crossword with the numbers hidden.

Everything here is built from committed data, so it is safe in a fresh clone.
"""
import argparse
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'solver'))
from grid_tools import slots           # noqa: E402
import grids_topic                     # noqa: E402
import topicgen                        # noqa: E402

BASE = 'https://tashbetz.gtmascode.dev'
OUT = 'docs/nosim'
DATA = f'{OUT}/puzzles.json'

# What makes a board publishable, mirrored from evals/topicgen_eval.py. The
# build searches for a board that MEETS these rather than producing one and
# letting the gate reject it: a gate that only says no leaves the previous,
# worse boards published, which is the outcome that matters least.
# A margin inside the gate's own numbers, so a board that just scrapes past the
# build does not then fail the gate on a rounding boundary - 3 of 26 entries is
# 11.5%, which prints as "12%" and is below a 12% floor.
MIN_LONG, MIN_ALL = 0.38, 0.12
CEILING = {1: 1.15, 2: 1.6, 3: 2.4, 4: 9.9}
RETRY_SEEDS = (7, 12345, 99, 555, 2024, 31337, 8080, 4242)


def publishable(p, floor_difficulty):
    """Floors, ceiling, and no easier than the level below it."""
    return (topicgen.theme_share(p)[0] >= MIN_LONG
            and p['topicality'] >= MIN_ALL
            and p['difficulty'] <= CEILING[p['level']] + 1e-9
            and p['difficulty'] >= floor_difficulty - 1e-9)

MECH_HE = {'definition': 'הגדרה', 'reversal': 'היפוך',
           'anagram': 'אנגרמה', 'hidden': 'מילה מוסתרת'}
MECH_EXPLAIN = {
    'definition': 'הגדרה ישירה מתוך מאגר הנושא של הפרויקט.',
    'reversal': 'קוראים את {frm} מהסוף להתחלה ומקבלים את התשובה.',
    'anagram': 'אותן אותיות בדיוק כמו {frm}, בסדר אחר.',
    'hidden': 'התשובה יושבת ברצף בתוך {carrier}, החל מהאות ה-{at}.',
}

STYLE = """<style>*{box-sizing:border-box}body{margin:0;background:#fff;color:#121212;font-family:'Frank Ruhl Libre','Arial Hebrew',serif;line-height:1.6}
.w{max-width:56rem;margin:0 auto;padding:1rem 1.2rem}header{border-bottom:1px solid #121212;box-shadow:0 3px 0 -1px #121212;padding:.8rem 0}
h1{font-size:1.6rem;margin:.2rem 0}.k{font-family:monospace;font-size:.65rem;letter-spacing:.12em;color:#fff;background:#f22b39;display:inline-block;padding:.12rem .5rem}
a{color:#f22b39}h2{border-bottom:3px solid #f22b39;display:inline-block;font-size:1.1rem;padding-bottom:.1rem}
.crumb{font-size:.8rem;color:#5c5c5c;margin:.6rem 0}
footer{margin:2.5rem 0 1.5rem;border-top:1px solid #dcdcdc;padding-top:.8rem;font-size:.8rem;color:#5c5c5c}
.scroll{overflow-x:auto;padding-bottom:.4rem}
.board{display:grid;direction:rtl;gap:2px;background:#121212;padding:2px;width:max-content;margin:1rem 0;border:2px solid #121212}
.cell{width:var(--cs,2.6rem);height:var(--cs,2.6rem);background:#fff;position:relative}
.cell.black{background:#121212}
.cell input{width:100%;height:100%;border:0;text-align:center;font-size:1.25rem;font-family:inherit;background:transparent;padding:0}
.cell input:focus{outline:0;background:#ffe9a8}
.cell.hl{background:#fff4d6}.cell.ok input{color:#1a7f37}.cell.bad input{color:#f22b39}
.cell .n{position:absolute;top:1px;right:3px;font-size:.6rem;color:#5c5c5c;font-family:monospace}
.cell.clue{background:#f0eee9;display:flex;flex-direction:column;justify-content:space-evenly;padding:1px}
.cell.clue .ac{font-size:.5rem;line-height:1.12;color:#121212;overflow:hidden;display:flex;gap:1px}
.cell.clue .ar{font-weight:700;color:#f22b39}
.clues{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.2rem}
.clues ol{padding-inline-start:1.2rem;margin:.3rem 0}
.clues li{margin:.35rem 0;cursor:pointer}
.clues li.done{color:#5c5c5c;text-decoration:line-through}
.bar{display:flex;gap:.5rem;flex-wrap:wrap;margin:.8rem 0}
button.act{font:inherit;background:#121212;color:#fff;border:0;border-radius:4px;padding:.45rem 1rem;cursor:pointer}
button.act.ghost{background:#fff;color:#121212;border:1.5px solid #121212}
.exp{background:#f6f5f3;border-radius:4px;padding:.7rem .9rem;margin:.5rem 0;font-size:.9rem;display:none}
.exp.on{display:block}
.msg{font-weight:700;margin:.5rem 0;min-height:1.4rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));gap:.6rem;padding:0;list-style:none;margin:.8rem 0 1.4rem}
.grid li{background:#f6f5f3;border-radius:3px;padding:.6rem .7rem}
.grid li b{display:block;font-size:1.02rem}
.grid li small{color:#5c5c5c}
.lv{display:flex;gap:.4rem;flex-wrap:wrap;padding:0;list-style:none;margin:.5rem 0}
.lv a{display:block;background:#f6f5f3;border-radius:3px;padding:.4rem .9rem;text-decoration:none}
.promo{background:#fff4d6;border:1.5px solid #121212;border-radius:3px;padding:.45rem .7rem;margin:.7rem 0 0;font-size:.9rem}
.promo a{font-weight:700}
.ask{background:#f6f5f3;border-radius:4px;padding:.7rem .9rem;margin:1.2rem 0;font-size:.92rem}
@media(prefers-color-scheme:dark){body{background:#161616;color:#f2f0ec}.cell input{color:#f2f0ec}
.promo{background:#3a3115;border-color:#f2f0ec}.grid li,.exp,.lv a,.ask{background:#222}
.cell{background:#3c3c3c}.cell.black{background:#0a0a0a}.cell.clue{background:#2a2a2a}
.cell.clue .ac{color:#f2f0ec}
.cell.hl{background:#5a4c22}.cell input:focus{background:#6b5a26}
.cell .n{color:#b9b9b9}.cell.ok input{color:#5fd28a}.cell.bad input{color:#ff7b84}}</style>"""

esc = lambda s: html.escape(str(s), quote=True)


def page(path, title, desc, body, jsonld=None, crumb=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rel = '/' + os.path.relpath(path, 'docs').replace('index.html', '').replace(os.sep, '/')
    crumbs = [('דף הבית', BASE + '/'), ('תשבצי נושא', BASE + '/nosim/')]
    if rel != '/nosim/':
        crumbs.append((crumb or title, BASE + rel))
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
        for i, (n, u) in enumerate(crumbs)]}
    ld = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
    if jsonld:
        ld += f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
    og = f"""<meta property="og:type" content="article"><meta property="og:site_name" content="תשבצי נושא">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{rel}"><meta property="og:locale" content="he_IL">
<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">"""
    open(path, 'w', encoding='utf-8').write(
        f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}{rel}">{og}{ld}{STYLE}</head>
<body><div class="w">
<header><span class="k">תשבצי נושא · לפי נושא ולפי רמה</span><h1>{esc(title)}</h1>
<div class="crumb"><a href="/nosim/">תשבצי נושא</a> · <a href="/tirgul/">תרגול</a> ·
<a href="/nativ/">המשחק היומי</a> · <a href="/milon/">מילון</a> ·
<a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div>
<div class="promo">☀️ <a href="/nativ/">נתיב - המשחק היומי הטוב לחובבי תשבצים</a> ·
חידה חדשה כל יום, עכשיו גם במצב קל</div></header>
{body}
<footer>התשבצים נוצרו אוטומטית ממאגרי הנושא של הפרויקט, מהלקסיקון העברי ומאינדקס
ההגדרות (ויקימילון/ויקיפדיה, CC BY-SA). לא מתפרסמות הגדרות מעיתונים ·
<a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a></footer></div></body></html>""")


def cell_numbers(grid):
    out = {}
    for (num, _d), cells in slots(grid).items():
        r, c = cells[0]
        out[f'{r},{c}'] = num
    return out


PLAYER = """
<script>
const PZ = JSON.parse(document.getElementById('pz').textContent);
const board = document.getElementById('board');
const msg = document.getElementById('msg');
board.style.gridTemplateColumns = `repeat(${PZ.grid[0].length}, var(--cs))`;
const inputs = {};
PZ.grid.forEach((row, r) => {
  [...row].forEach((ch, c) => {
    const d = document.createElement('div');
    const inCell = PZ.cellclues[r + ',' + c];
    d.className = 'cell' + (ch === '#' ? (inCell ? ' clue' : ' black') : '');
    if (ch === '#') {
      if (inCell) inCell.forEach(x => {
        const s = document.createElement('div');
        s.className = 'ac';
        s.innerHTML = '<span class="ar">' + (x.dir === 'across' ? '\\u2190' : '\\u2193') +
                      '</span><span>' + x.html + '</span>';
        d.appendChild(s);
      });
    } else {
      const n = PZ.nums[r + ',' + c];
      if (n && PZ.numbered) { const s = document.createElement('span'); s.className = 'n'; s.textContent = n; d.appendChild(s); }
      const i = document.createElement('input');
      i.maxLength = 1; i.dataset.rc = r + ',' + c; i.autocomplete = 'off';
      i.addEventListener('input', () => { i.value = i.value.replace(/[^\\u05d0-\\u05ea]/g, ''); if (i.value) advance(i); });
      i.addEventListener('focus', () => highlight(r, c));
      inputs[r + ',' + c] = i; d.appendChild(i);
    }
    board.appendChild(d);
  });
});
let active = null;
function highlight(r, c) {
  const e = PZ.entries.find(e => e.cells.some(x => x[0] === r && x[1] === c)) || null;
  active = e;
  Object.values(inputs).forEach(i => i.parentNode.classList.remove('hl'));
  if (e) e.cells.forEach(([a, b]) => inputs[a + ',' + b].parentNode.classList.add('hl'));
}
function advance(i) {
  if (!active) return;
  const [r, c] = i.dataset.rc.split(',').map(Number);
  const at = active.cells.findIndex(x => x[0] === r && x[1] === c);
  const nx = active.cells[at + 1];
  if (nx) inputs[nx[0] + ',' + nx[1]].focus();
}
document.querySelectorAll('.clues li').forEach(li => li.onclick = () => {
  const e = PZ.entries[+li.dataset.i]; active = e;
  const [r, c] = e.cells[0]; inputs[r + ',' + c].focus();
});
document.getElementById('check').onclick = () => {
  let right = 0, filled = 0;
  PZ.entries.forEach((e, idx) => {
    let all = true;
    e.cells.forEach(([r, c], k) => {
      const i = inputs[r + ',' + c];
      i.parentNode.classList.remove('ok', 'bad');
      if (!i.value) { all = false; return; }
      filled++;
      if (i.value === e.answer[k]) i.parentNode.classList.add('ok');
      else { i.parentNode.classList.add('bad'); all = false; }
    });
    const li = document.querySelector(`.clues li[data-i="${idx}"]`);
    if (li) li.classList.toggle('done', all);
    if (all) right++;
  });
  msg.textContent = filled === 0 ? 'מלאו כמה משבצות ואז בדקו.'
    : `${right} מתוך ${PZ.entries.length} הגדרות נכונות.`;
};
document.getElementById('explain').onclick = () => {
  document.querySelectorAll('.exp').forEach(x => x.classList.add('on'));
  msg.textContent = 'ההסברים נפתחו: כל תשובה עם המנגנון וההוכחה שלה.';
};
document.getElementById('clear').onclick = () => {
  Object.values(inputs).forEach(i => { i.value = ''; i.parentNode.classList.remove('ok', 'bad'); });
  document.querySelectorAll('.clues li').forEach(li => li.classList.remove('done'));
  msg.textContent = '';
};
</script>
"""

REQUEST_FORM = """
<div class="ask">
<label for="rtopic"><b>הנושא</b> (בעברית, עד 60 תווים)</label>
<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin:.4rem 0">
<input id="rtopic" maxlength="60" placeholder="למשל: כדורגל ישראלי, כיתה ז2, מאכלים"
 style="flex:1 1 16rem;font:inherit;padding:.45rem .6rem;border:1.5px solid #121212;border-radius:4px">
<select id="rlevel" style="font:inherit;padding:.45rem .6rem;border:1.5px solid #121212;border-radius:4px">
<option value="1">קל</option><option value="2" selected>בינוני</option>
<option value="3">קשה</option><option value="4">אתגר</option></select>
<select id="rkind" style="font:inherit;padding:.45rem .6rem;border:1.5px solid #121212;border-radius:4px">
<option value="any" selected>כל סוג לוח</option><option value="regular">תשבץ</option>
<option value="arrow">תשחץ</option></select>
</div>
<label for="rnote"><b>משהו שכדאי שנדע</b> (לא חובה, עד 200 תווים)</label>
<input id="rnote" maxlength="200" placeholder="למשל: לכיתה ה, בלי שמות של אנשים"
 style="width:100%;font:inherit;padding:.45rem .6rem;border:1.5px solid #121212;border-radius:4px;margin:.4rem 0">
<button class="act" id="rsend">שלחו בקשה</button>
<div class="msg" id="rmsg"></div>
</div>
<script>
document.getElementById('rsend').onclick = async () => {
  const t = document.getElementById('rtopic').value.trim();
  const m = document.getElementById('rmsg');
  if (!/[\u05d0-\u05ea]{2}/.test(t)) { m.textContent = 'כתבו נושא בעברית.'; return; }
  m.textContent = 'שולח...';
  try {
    const r = await fetch('/api/puzzle-request', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: t, level: +document.getElementById('rlevel').value,
                             kind: document.getElementById('rkind').value,
                             note: document.getElementById('rnote').value.trim() })
    });
    const j = await r.json();
    m.textContent = r.ok
      ? (j.count > 1 ? 'נרשם. ' + j.count + ' אנשים כבר ביקשו את הנושא הזה.'
                     : 'נרשם. נבנה את הלוח ונפרסם אותו כאן.')
      : (j.error || 'לא הצלחנו לרשום את הבקשה.');
  } catch (e) { m.textContent = 'לא הצלחנו לרשום את הבקשה. נסו שוב מאוחר יותר.'; }
};
</script>"""

REQUEST_BOX = """<div class="ask"><b>רוצים תשבץ על נושא אחר?</b>
בקשו אותו ואנחנו נבנה אותו: כיתה, יום הולדת, מקום עבודה או כל נושא שתבחרו.
<p><a href="/bakasha/">לבקשת תשבץ אישי →</a></p></div>"""


# ---------------------------------------------------------------- generate

def generate_set(levels=(1, 2, 3, 4), topics=None, effort=1.0):
    """Regenerate boards. Slow (seconds per board), so the result is committed
    and the page build reads the JSON.

    With --topic it MERGES into the existing file rather than replacing it, so
    the set can be rebuilt a few subjects at a time and so the weekly news run
    does not wipe the bagrut boards.
    """
    banks = [t for t in topicgen.load()['topics'] if not t.startswith('_')]
    replace_all = topics is None and tuple(levels) == (1, 2, 3, 4)
    topics = topics or banks
    out = []
    if not replace_all and os.path.exists(DATA):
        out = [p for p in json.load(open(DATA, encoding='utf-8'))
               if not (p['topic'] in topics and p['level'] in levels)]
    for topic in topics:
        # levels ascend, so each board can be required to be no easier than the
        # one before it: that is the ramp, built rather than hoped for
        prev_difficulty = 0.0
        for level in sorted(levels):
            p = topicgen.generate_best(topic, level, effort=effort)
            if not p:
                print(f'  !! {topic} level {level}: no puzzle')
                continue
            out.append(p)
            # Re-roll until the board is publishable. The seed is a lottery -
            # measured spread on one topic and level was 6% to 33% of entries
            # on topic - so this is a search, not a retry.
            if not publishable(p, prev_difficulty):
                for seed in RETRY_SEEDS:
                    alt = topicgen.generate(topic, level, p['shape'], seed=seed)
                    if not alt:
                        continue
                    if publishable(alt, prev_difficulty):
                        p = alt
                        break
                    if topicgen.theme_share(alt) > topicgen.theme_share(p):
                        p = alt
            prev_difficulty = p['difficulty']
            long_share, _ = topicgen.theme_share(p)
            print(f"  {topic:11s} L{level} {p['shape']:9s} "
                  f"{len(p['entries'])} entries, topical {p['topicality']:.0%} "
                  f"(long {long_share:.0%}), difficulty {p['difficulty']}")
    os.makedirs(OUT, exist_ok=True)
    out.sort(key=lambda p: (p['topic'], p['level']))
    json.dump(out, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'wrote {DATA}: {len(out)} puzzles')
    return out


# ------------------------------------------------------------------- build

def clue_html(e):
    return esc(e['clue'])


def build():
    pz = json.load(open(DATA, encoding='utf-8'))
    by_topic = {}
    for p in pz:
        by_topic.setdefault(p['topic'], []).append(p)
    urls = ['/nosim/']

    for topic, plist in by_topic.items():
        plist.sort(key=lambda x: x['level'])
        for p in plist:
            urls.append(build_puzzle(p, plist))
        urls.append(build_topic(topic, plist))

    # hub
    cards = []
    for topic, plist in sorted(by_topic.items(), key=lambda kv: kv[1][0]['title']):
        p0 = plist[0]
        cards.append(f'<li><b><a href="/nosim/{topic}/">{esc(p0["title"])}</a></b>'
                     f'<small>{esc(p0["blurb"])}</small><br>'
                     f'<small>{len(plist)} רמות · {len(p0["entries"])} הגדרות בלוח הקל</small></li>')
    news = 'hadashot' in by_topic
    news_line = ('<p><b>חדש כל שבוע:</b> <a href="/nosim/hadashot/">תשבץ החדשות</a>, '
                 'על מי ומה היו בכותרות השבוע.</p>' if news else '')
    body = f"""<p>תשבצים ותשחצים בעברית לפי <b>נושא</b> ולפי <b>רמה</b>, לפתירה ישירה בדפדפן.
כל לוח נבנה אוטומטית ממאגר מונחים של הנושא, ולכן הוא שלנו לפרסם: אלה לא תשבצים מהעיתון.</p>
<p>הרמה איננה תווית. היא נמדדת: ברמות הקלות כל התשובות הן מילים שבאמת מופיעות
בתשבצים, וההגדרות ישירות; ברמות הקשות נפתח כל הלקסיקון ונכנסים מנגנוני היפוך,
מילה מוסתרת ואנגרמה. אחרי הפתירה אפשר לפתוח את ההסבר של כל תשובה.</p>
{news_line}
<h2>נושאים</h2>
<p>עשרת המקצועות של <b>הכנה לבחינות הבגרות</b>, כל אחד בארבע רמות:</p>
<ul class="grid">{''.join(cards)}</ul>
{REQUEST_BOX}
<p>מחפשים מילה לפי אורך, תבנית או אנגרם? <a href="/milon/">מילון התשבץ</a>.
רוצים ללמוד את המנגנונים עצמם? <a href="/tirgul/">תשבצי האימון</a>.</p>"""
    page(f'{OUT}/index.html',
         'תשבצי נושא: הכנה לבגרות בתשבץ, לפי מקצוע ולפי רמה',
         f'{len(pz)} תשבצים ותשחצים בעברית לפי נושא: תנ"ך, היסטוריה, אזרחות, ביולוגיה, '
         f'כימיה, פיזיקה, מתמטיקה, ספרות, גאוגרפיה ולשון. ארבע רמות לכל מקצוע, '
         f'פתירה בדפדפן והסבר לכל תשובה.',
         body, {'@context': 'https://schema.org', '@type': 'ItemList',
                'name': 'תשבצי נושא', 'numberOfItems': len(pz)})
    urls.append(build_request())
    update_sitemap(urls)
    print(f'topic pages: {len(urls)} (puzzles: {len(pz)}, subjects: {len(by_topic)})')
    return urls


def update_sitemap(urls):
    """Rewrite our own block of docs/sitemap.xml, idempotently.

    app/build_seo.py regenerates the whole sitemap and picks these pages up by
    walking the directory, but it needs the gitignored corpus to run at all;
    this keeps the committed sitemap correct after a pages-only rebuild.
    """
    import re
    path = 'docs/sitemap.xml'
    if not os.path.exists(path):
        return
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'  <url><loc>%s/(nosim|bakasha)/[^<]*</loc></url>\n' % re.escape(BASE), '', s)
    s = re.sub(r'  <url><loc>%s/bakasha/</loc></url>\n' % re.escape(BASE), '', s)
    block = ''.join(f'  <url><loc>{BASE}{u}</loc></url>\n' for u in sorted(set(urls)))
    s = s.replace('</urlset>', block + '</urlset>')
    open(path, 'w', encoding='utf-8').write(s)


def build_request():
    """/bakasha/: ask for a board on a subject of your own."""
    body = f"""<p>אנחנו בונים תשבצים ותשחצים לפי נושא, ואפשר לבקש נושא משלכם:
כיתה, מקום עבודה, יום הולדת, קבוצת ספורט, סדרה אהובה או כל דבר אחר.
הבקשה נכנסת לתור, ואחת לשבוע אנחנו עוברים עליו ובונים את הלוחות.</p>
<h2>איך זה עובד</h2>
<p>הגנרטור שלנו מרכיב לוח מתוך מאגר מונחים של הנושא: הוא מחפש בכל האינדקס של
המילון מי ומה שייך לנושא שביקשתם, ממלא את הרשת סביב התשובות האלה, ומצמיד לכל
תשובה הגדרה עם הוכחה. אם הנושא קיים כבר במאגר, הלוח נבנה מיד; אם לא, מישהו
מאיתנו מרכיב את המאגר קודם.</p>
<p><b>מה לא קורה כאן:</b> שום דבר לא מתפרסם אוטומטית. הבקשות נקראות לפני שהן
הופכות ללוח, ואנחנו לא מבקשים ולא שומרים פרטי קשר. הלוח מתפרסם בעמוד
<a href="/nosim/">תשבצי הנושא</a>, ומשם אפשר לשתף אותו בקישור.</p>
<h2>בקשת תשבץ</h2>
{REQUEST_FORM}
<h2>מה כבר יש</h2>
<p>עשרה מקצועות בגרות בארבע רמות, ותשבץ שבועי על החדשות:
<a href="/nosim/">כל תשבצי הנושא</a>.</p>"""
    page('docs/bakasha/index.html',
         'בקשת תשבץ אישי: לוח על הנושא שלכם',
         'בקשו תשבץ או תשחץ בעברית על נושא משלכם: כיתה, מקום עבודה, יום הולדת או '
         'כל תחום שתבחרו. הבקשה נכנסת לתור שבועי, והלוח מתפרסם באתר.',
         body, {'@context': 'https://schema.org', '@type': 'WebPage',
                'name': 'בקשת תשבץ אישי', 'inLanguage': 'he'},
         crumb='בקשת תשבץ')
    return '/bakasha/'


def build_topic(topic, plist):
    p0 = plist[0]
    rows = ''.join(
        f'<li><a href="/nosim/{topic}/{p["level"]}/">{esc(p["level_name"])}</a></li>'
        for p in plist)
    # A board built from a reader request has no curated bank behind it: its
    # answers came straight out of the entity index, so there is no term list
    # to show.
    terms = topicgen.load()['topics'].get(topic, {}).get('terms', {})
    bankline = ''
    if terms:
        sample = ', '.join(list(terms)[:14])
        bankline = (f'<p>מה יש במאגר של המקצוע הזה: {esc(len(terms))} מונחים, בהם '
                    f'{esc(sample)} ועוד. כל מונח מגיע עם הגדרה קצרה, וההגדרה היא '
                    f'שמתפרסמת כהגדרת התשבץ.</p>')
    body = f"""<p>{esc(p0['blurb'])}</p>
<h2>הרמות</h2><ul class="lv">{rows}</ul>
{bankline}
{REQUEST_BOX}
<p><a href="/nosim/">כל הנושאים</a></p>"""
    page(f'{OUT}/{topic}/index.html',
         f'תשבץ {p0["title"]}: הכנה לבגרות ב{p0["title"]} דרך תשבץ',
         f'תשבצים ותשחצים ב{p0["title"]} לפי רמה, לפתירה בדפדפן. {esc(p0["blurb"])}',
         body, {'@context': 'https://schema.org', '@type': 'LearningResource',
                'name': f'תשבצי {p0["title"]}', 'inLanguage': 'he',
                'educationalUse': 'הכנה לבגרות', 'isAccessibleForFree': True},
         crumb=p0['title'])
    return f'/nosim/{topic}/'


def build_puzzle(p, plist):
    sl = slots(p['grid'])
    entries = []
    for e in p['entries']:
        cells = sl[(e['num'], e['dir'])]
        entries.append({**e, 'cells': [[r, c] for r, c in cells]})

    # arrowword: the clue text goes in the cell that introduces the entry
    cellclues = {}
    if p['kind'] == 'arrow':
        hosts = grids_topic.arrow_hosts(p['grid'])
        for e in entries:
            r, c = hosts[(e['num'], e['dir'])]
            cellclues.setdefault(f'{r},{c}', []).append(
                {'dir': e['dir'], 'html': clue_html(e)})

    data = {'grid': p['grid'], 'nums': cell_numbers(p['grid']),
            'numbered': p['kind'] == 'regular', 'cellclues': cellclues,
            'entries': [{'num': e['num'], 'dir': e['dir'], 'answer': e['answer'],
                         'cells': e['cells']} for e in entries]}

    def clue_list(d):
        items = sorted(((i, e) for i, e in enumerate(entries) if e['dir'] == d),
                       key=lambda x: x[1]['num'])
        out = []
        for i, e in items:
            pr = e['proof']
            expl = MECH_EXPLAIN[e['mechanism']].format(
                frm=topicgen.final_form(pr.get('from', '')),
                carrier=topicgen.final_form(pr.get('carrier', '')),
                at=pr.get('at', 0) + 1)
            mark = ' <small>·נושא</small>' if e['topical'] else ''
            out.append(f'<li data-i="{i}"><b>{e["num"]}.</b> {esc(e["clue"])} '
                       f'<small>({len(e["answer"])})</small>{mark}'
                       f'<div class="exp"><b>{esc(e["display"])}</b> · '
                       f'{MECH_HE[e["mechanism"]]}: {esc(expl)}</div></li>')
        return '\n'.join(out)

    kind_he = 'תשחץ' if p['kind'] == 'arrow' else 'תשבץ'
    cs = '4.4rem' if p['kind'] == 'arrow' else '2.6rem'
    rows, cols = len(p['grid']), len(p['grid'][0])
    others = ' · '.join(
        f'<a href="/nosim/{p["topic"]}/{q["level"]}/">{esc(q["level_name"])}</a>'
        if q['level'] != p['level'] else f'<b>{esc(q["level_name"])}</b>' for q in plist)
    topical = sum(1 for e in entries if e['topical'])
    intro = ('ההגדרות מודפסות בתוך הלוח, והחץ מראה לאן נמשכת התשובה: '
             '← לשורה, ↓ לטור.' if p['kind'] == 'arrow'
             else 'ההגדרות מודפסות לצד הלוח, לפי מספרי המשבצות.')
    # An arrowword carries its clues in the board, so the list below it is a
    # text version: for a small screen, for a screen reader, and for the
    # explanations. A crossword's list is the clues themselves.
    list_head = ('רשימת ההגדרות (גרסת טקסט של הלוח)' if p['kind'] == 'arrow'
                 else 'ההגדרות')
    body = f"""<p>{kind_he} ב{esc(p['title'])} · רמת <b>{esc(p['level_name'])}</b> ·
לוח {rows}x{cols} · {len(entries)} הגדרות, מהן {topical} על הנושא עצמו.</p>
<p>{intro}</p>
<div class="scroll"><div class="board" id="board" style="--cs:{cs}"></div></div>
<div class="bar">
  <button class="act" id="check">בדקו אותי</button>
  <button class="act ghost" id="explain">הראו את ההסברים</button>
  <button class="act ghost" id="clear">נקו</button>
</div>
<div class="msg" id="msg"></div>
<h2>{list_head}</h2>
<div class="clues">
  <div><h3>מאוזן</h3><ol>{clue_list('across')}</ol></div>
  <div><h3>מאונך</h3><ol>{clue_list('down')}</ol></div>
</div>
<p style="margin-top:1.2rem">רמות נוספות ב{esc(p['title'])}: {others} ·
<a href="/nosim/{p['topic']}/">דף המקצוע</a> · <a href="/nosim/">כל הנושאים</a></p>
{REQUEST_BOX}
<script type="application/json" id="pz">{json.dumps(data, ensure_ascii=False)}</script>{PLAYER}"""

    title = f'{kind_he} {p["title"]} ברמת {p["level_name"]}: {len(entries)} הגדרות'
    desc = (f'{kind_he} ב{p["title"]} ברמת {p["level_name"]}, {len(entries)} הגדרות '
            f'ו-{topical} תשובות על הנושא. פותרים בדפדפן, וכל תשובה מגיעה עם ההסבר '
            f'וההוכחה שלה. מתאים להכנה לבגרות ב{p["title"]}.')
    page(f'{OUT}/{p["topic"]}/{p["level"]}/index.html', title, desc, body,
         {'@context': 'https://schema.org', '@type': 'LearningResource',
          'name': title, 'learningResourceType': kind_he, 'inLanguage': 'he',
          'educationalLevel': p['level_name'], 'about': p['title'],
          'educationalUse': 'הכנה לבגרות', 'isAccessibleForFree': True},
         crumb=f'{p["title"]} · {p["level_name"]}')
    return f'/nosim/{p["topic"]}/{p["level"]}/'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--generate', action='store_true',
                    help='regenerate docs/nosim/puzzles.json first (slow)')
    ap.add_argument('--topic', action='append',
                    help='limit --generate to these topics and merge into the set')
    ap.add_argument('--effort', type=float, default=1.0,
                    help='multiplier on each board\'s search-node allowance')
    ap.add_argument('--level', type=int, action='append',
                    help='limit --generate to these levels and merge into the set')
    ap.add_argument('--pages', action='store_true', default=True)
    a = ap.parse_args()
    if a.generate:
        generate_set(levels=tuple(a.level) if a.level else (1, 2, 3, 4),
                     topics=a.topic, effort=a.effort)
    build()
