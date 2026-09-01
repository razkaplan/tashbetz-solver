#!/usr/bin/env python3
"""Build the trainer: playable pages for the generated practice crosswords.

Reads docs/tirgul/puzzles.json (solver/puzzlegen.py) and writes:
  /tirgul/            hub, puzzles grouped by level
  /tirgul/<id>/       one playable puzzle, with a per-clue explanation

Every puzzle here is generated from our own lexicon, never from newspaper
clues, so it is ours to publish. The teaching value is the explanation: each
answer shows the mechanism that produces it and the check that proves it,
which is the habit the solver itself is built on.

build_seo.py discovers these pages by globbing docs/tirgul/*/ so they land in
the one sitemap, with no extra manifest file to drift out of date.
"""
import html, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solver'))
from grid_tools import slots   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
BASE = 'https://tashbetz.gtmascode.dev'
OUT = 'docs/tirgul'

MECH_HE = {
    'definition': 'הגדרה',
    'reversal': 'היפוך',
    'anagram': 'אנגרמה',
    'hidden': 'מילה מוסתרת',
}
MECH_EXPLAIN = {
    'definition': 'הגדרה ישירה מתוך אינדקס המילון של הפרויקט.',
    'reversal': 'קוראים את המילה {frm} מהסוף להתחלה ומקבלים את התשובה.',
    'anagram': 'אותן אותיות בדיוק כמו {frm}, בסדר אחר.',
    'hidden': 'התשובה יושבת ברצף בתוך המילה {carrier}, החל מהאות ה-{at}.',
}

import brand

NOTE = ('תשבצי האימון נוצרו אוטומטית מהלקסיקון של הפרויקט (hspell) ומאינדקס ההגדרות '
        '(ויקימילון/ויקיפדיה, CC BY-SA). לא מתפרסמות הגדרות מעיתונים. '
        '<a href="https://www.linkedin.com/in/razkaplan/" rel="me">פרויקט של רז קפלן</a>.')

# Page-specific rules only; the shell comes from docs/assets/brand.css.
STYLE = """<style>.exp b{font-family:var(--display)}.clues h2{font-size:1.2rem;margin:.2rem 0 .3rem}</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def page(path, title, desc, body, jsonld=None, crumb=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rel = '/' + os.path.relpath(path, 'docs').replace('index.html', '').replace(os.sep, '/')
    crumbs = [('דף הבית', BASE + '/'), ('תרגול', BASE + '/tirgul/')]
    if rel != '/tirgul/':
        crumbs.append((crumb or title, BASE + rel))
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]}
    ld = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
    if jsonld:
        ld += f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
    # Social card per puzzle: title and description already differ per page, so
    # only the image is shared. A shared trainer link with no card is a bare URL.
    og = f"""<meta property="og:type" content="article"><meta property="og:site_name" content="תרגול תשבץ">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{rel}"><meta property="og:image" content="{BASE}/tirgul/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="he_IL"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/tirgul/og.png">"""
    open(path, 'w', encoding='utf-8').write(brand.document(
        title=title, desc=desc, canonical=f'{BASE}{rel}', meta=og + ld, style=STYLE,
        kicker='🏋️ תרגול תשבץ · פותרים ביחד', kicker_class='pop',
        crumbs=[(n, u.replace(BASE, '') or '/') for n, u in crumbs],
        body=body, note=NOTE, current='tirgul'))


def cell_numbers(grid):
    """{'r,c': number} for cells that start a slot (same numbering as the solver)."""
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
board.style.gridTemplateColumns = `repeat(${PZ.grid[0].length}, 2.6rem)`;
const inputs = {};
PZ.grid.forEach((row, r) => {
  [...row].forEach((ch, c) => {
    const d = document.createElement('div');
    d.className = 'cell' + (ch === '#' ? ' black' : '');
    if (ch !== '#') {
      const n = PZ.nums[r + ',' + c];
      if (n) { const s = document.createElement('span'); s.className = 'n'; s.textContent = n; d.appendChild(s); }
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
function focusEntry(idx) {
  const e = PZ.entries[idx]; active = e;
  const [r, c] = e.cells[0]; inputs[r + ',' + c].focus();
}
document.querySelectorAll('.clues li').forEach(li => li.onclick = () => focusEntry(+li.dataset.i));
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


def build():
    pz = json.load(open('docs/tirgul/puzzles.json', encoding='utf-8'))
    urls = ['/tirgul/']
    by_level = {}
    for p in pz:
        by_level.setdefault(p['level'], []).append(p)

    for p in pz:
        sl = slots(p['grid'])
        entries = []
        for e in p['entries']:
            cells = sl[(e['num'], e['dir'])]
            entries.append({**e, 'cells': [[r, c] for r, c in cells]})
        data = {'grid': p['grid'], 'nums': cell_numbers(p['grid']),
                'entries': [{'num': e['num'], 'dir': e['dir'], 'answer': e['answer'],
                             'cells': e['cells']} for e in entries]}

        def clue_list(d):
            items = [(i, e) for i, e in enumerate(entries) if e['dir'] == d]
            items.sort(key=lambda x: x[1]['num'])
            out = []
            for i, e in items:
                pr = e['proof']
                expl = MECH_EXPLAIN[e['mechanism']].format(
                    frm=pr.get('from', ''), carrier=pr.get('carrier', ''), at=pr.get('at', 0) + 1)
                out.append(
                    f'<li data-i="{i}"><b>{e["num"]}.</b> {esc(e["clue"])} '
                    f'<small>({len(e["answer"])})</small>'
                    f'<div class="exp"><b>{esc(e["answer"])}</b> · {MECH_HE[e["mechanism"]]}: '
                    f'{esc(expl)}</div></li>')
            return '\n'.join(out)

        mechs = sorted({e['mechanism'] for e in entries})
        mech_he = ', '.join(MECH_HE[m] for m in mechs)
        prev_n = p['id'] - 1 if p['id'] > 1 else None
        next_n = p['id'] + 1 if p['id'] < len(pz) else None
        nav = ' · '.join(filter(None, [
            f'<a href="/tirgul/{prev_n}/">← תשבץ {prev_n}</a>' if prev_n else '',
            '<a href="/tirgul/">כל התשבצים</a>',
            f'<a href="/tirgul/{next_n}/">תשבץ {next_n} →</a>' if next_n else '']))
        body = f"""<p>רמת <b>{esc(p['level'])}</b> · רשת {p['size']}x{p['size']} · {len(entries)} הגדרות ·
מנגנונים: {esc(mech_he)}</p>
<div class="board" id="board"></div>
<div class="bar">
  <button class="act" id="check">בדקו אותי</button>
  <button class="act ghost" id="explain">הראו את ההסברים</button>
  <button class="act ghost" id="clear">נקו</button>
</div>
<div class="msg" id="msg"></div>
<div class="clues">
  <div><h2>מאוזן</h2><ol>{clue_list('across')}</ol></div>
  <div><h2>מאונך</h2><ol>{clue_list('down')}</ol></div>
</div>
<p style="margin-top:1.2rem">{nav}</p>
<script type="application/json" id="pz">{json.dumps(data, ensure_ascii=False)}</script>{PLAYER}"""

        title = f'תרגול תשבץ #{p["id"]}: רמת {p["level"]}, רשת {p["size"]}x{p["size"]}'
        desc = (f'תשבץ אימון מספר {p["id"]} ברמת {p["level"]}: רשת {p["size"]}x{p["size"]}, '
                f'{len(entries)} הגדרות, מנגנוני {mech_he}. פותרים ישירות בדפדפן, '
                f'וכל תשובה מגיעה עם ההסבר וההוכחה שלה.')
        page(f'{OUT}/{p["id"]}/index.html', title, desc, body,
             {'@context': 'https://schema.org', '@type': 'LearningResource',
              'name': title, 'learningResourceType': 'תרגול תשבץ',
              'inLanguage': 'he', 'educationalLevel': p['level'],
              'teaches': mech_he, 'isAccessibleForFree': True},
             crumb=f'תשבץ {p["id"]}')
        urls.append(f'/tirgul/{p["id"]}/')

    # Puzzles are generated level by level, so insertion order is difficulty order.
    order = list(by_level)
    secs = []
    for lv in order:
        items = sorted(by_level[lv], key=lambda x: x['id'])
        links = ''.join(f'<li><a href="/tirgul/{p["id"]}/">{p["id"]}</a></li>' for p in items)
        secs.append(f'<h2>{esc(lv)}</h2><p>{len(items)} תשבצים · רשת {items[0]["size"]}x{items[0]["size"]}</p>'
                    f'<ul class="lvl">{links}</ul>')
    hub_body = f"""<p>{len(pz)} תשבצי אימון לפתירה ישירה בדפדפן, מסודרים לפי רמה. הם נבנו אוטומטית
מהלקסיקון של הפרויקט, ולכן אפשר לפרסם אותם: אלה לא תשבצים מהעיתון.</p>
<p>ההבדל מתשבץ רגיל: <b>כל תשובה מגיעה עם ההוכחה שלה</b>. אחרי הפתירה אפשר לפתוח את
ההסברים ולראות בדיוק איזה מנגנון מייצר כל מילה: הגדרה, היפוך, אנגרמה או מילה מוסתרת.
זו בדיוק השיטה שבה עובד <a href="/solve/">עוזר הפתירה</a>.</p>
{''.join(secs)}
<p>רוצים לחפש מילה לפי אורך, תבנית או אנגרם? <a href="/milon/">מילון התשבץ</a> מכיל
אלפי ערכים עם הכתיב המדויק ברשת.</p>"""
    page(f'{OUT}/index.html', 'תרגול תשבצים: 100 תשבצי אימון עם הסבר לכל תשובה',
         f'{len(pz)} תשבצי אימון בעברית לפתירה בדפדפן, מדורגים לפי רמה. כל תשובה מגיעה עם '
         f'המנגנון וההוכחה שמאחוריה: הגדרה, היפוך, אנגרמה ומילה מוסתרת.',
         hub_body,
         {'@context': 'https://schema.org', '@type': 'ItemList',
          'name': 'תשבצי אימון', 'numberOfItems': len(pz)})

    print(f'trainer pages: {len(urls)} (puzzles: {len(pz)})')
    return urls


if __name__ == '__main__':
    build()
