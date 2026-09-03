#!/usr/bin/env python3
"""Word pages: /milon/w/<word>/ for crossword answers people look for.

Which words: solver/lex/words.json, fed by app/drain_missed.py from the
demand signals (the 404 page's missed-path counter, a Search Console export,
the git history of removed pages). A page is built only for a word we hold a
DEFINITION for - the fillbank, a curated list, or an override in words.json -
because a word page without a definition is the thin page that got these
URLs removed in the first place.

Everything else on the page comes from committed data: the crossword
spelling, the senses the corpus saw, the substitutes printed puzzles used
(solver/lex/substitutions.json), the clue-phrase pages (/milon/d/) that list
the word, and same-length neighbours. No newspaper clue text is published.

Why not /milon/e/: app/build_seo.py removes any entity directory it did not
generate, and it needs the gitignored corpus to run. This builder uses
committed data only and is safe anywhere.

Rerunnable: overwrites its own pages, rewrites its own sitemap block and the
words section on /milon/. Usage: python3 app/build_words.py
"""
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import brand  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'docs/milon/w')
BASE = brand.BASE
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
UNFIN = {'כ': 'ך', 'מ': 'ם', 'נ': 'ן', 'פ': 'ף', 'צ': 'ץ'}
SENSE_HE = {'answer': 'הופיעה כתשובה בתשבצים', 'common_word': 'מילה מן המילון',
            'given_name': 'שם פרטי', 'surname': 'שם משפחה', 'song': 'שם שיר',
            'song_word': 'מילה מתוך שיר', 'place': 'שם מקום', 'entity': 'ערך במילון'}
HUB_START = '<!-- words-hub-start -->'
HUB_END = '<!-- words-hub-end -->'


def esc(s):
    return html.escape(str(s), quote=True)


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


def load(rel):
    p = os.path.join(ROOT, rel)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def definitions():
    """word-norm -> (definition, display spelling, source)."""
    out = {}
    fb = load('solver/lex/fillbank.json')
    for w, d in fb.items():
        out.setdefault(norm(w), (d.strip(), w.strip(), 'fillbank'))
    for key, spec in load('solver/lex/defs_curated.json').items():
        if key.startswith('_'):
            continue
        for w, d in (spec.get('items') or {}).items():
            out.setdefault(norm(w), (d.strip(), w.strip(), f'curated:{key}'))
    return out


def clue_pages():
    """word-norm -> [(slug, phrase)] of /milon/d/ pages that list it."""
    out = {}
    for key, spec in load('solver/lex/defs_curated.json').items():
        if key.startswith('_') or not spec.get('slug'):
            continue
        for w in (spec.get('items') or {}):
            out.setdefault(norm(w), []).append((spec['slug'], spec.get('title', key)))
    for spec in load('solver/lex/defs_requested.json').values():
        if not isinstance(spec, dict) or not spec.get('slug'):
            continue
        for w in (spec.get('items') or {}):
            out.setdefault(norm(w), []).append((spec['slug'], spec.get('phrase', '')))
    return out


def page(word, d, src, ctx):
    n = norm(word)
    L = len(n)
    senses = [SENSE_HE[s] for s in (ctx['amb'].get(n) or {}).get('senses', []) if s in SENSE_HE]
    subs = [s for s, _ in (ctx['subs'].get(n) or [])[:6] if s != n]
    rows = f'<tr><th>הגדרה</th><td>{esc(d)}</td></tr>'
    rows += f'<tr><th>אורך ברשת</th><td>{L} אותיות</td></tr>'
    rows += f'<tr><th>כתיב בתשבץ</th><td><span class="net">{esc(n)}</span></td></tr>'
    if senses:
        rows += f'<tr><th>איפה פגשנו אותה</th><td>{esc(", ".join(dict.fromkeys(senses)))}</td></tr>'
    if subs:
        rows += f'<tr><th>תחליפים בתשבצים</th><td>{esc(", ".join(subs))}</td></tr>'
    if ctx['freq'].get(n, 0) >= 2:      # a count of one says nothing
        rows += f'<tr><th>שכיחות כתשובה</th><td>נראתה {ctx["freq"][n]} פעמים בתשבצים שנותחו</td></tr>'
    rows += f'<tr><th>אותיות (לאנגרם)</th><td><span class="net">{" · ".join(sorted(set(n)))}</span></td></tr>'
    extra = ''
    cps = ctx['clue_pages'].get(n) or []
    if cps:
        links = ' · '.join(f'<a href="/milon/d/{s}/">{esc(t)}</a>' for s, t in cps[:6])
        extra += f'<p style="margin-top:.8rem"><b>הגדרות שהמילה עונה עליהן:</b> {links}</p>'
    near = [w2 for w2 in ctx['words_by_len'].get(L, []) if w2 != word][:10]
    if near:
        links = ' · '.join(f'<a href="/milon/w/{urllib.parse.quote(w2, safe="")}/">{esc(w2)}</a>' for w2 in near)
        extra += f'<p style="margin-top:.8rem"><b>עוד מילים ב-{L} אותיות:</b> {links}</p>'
    body = (f'<table>{rows}</table>{extra}'
            f'<p style="margin-top:1rem"><a href="/milon/common-{L}/">תשובות נפוצות ב-{L} אותיות ←</a>'
            f' · <a href="/milon/anagram/">חיפוש אנגרם</a> · <a href="/milon/">המילון</a></p>')
    title = f'{word}: פירוש ומשמעות, תשובה ב-{L} אותיות בתשבץ'
    desc = f'{word} - {d}. {L} אותיות, כתיב בתשבץ {n}.' + (f' תחליפים: {", ".join(subs[:3])}.' if subs else '')
    url = f'/milon/w/{urllib.parse.quote(word, safe="")}/'
    ld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": word,
          "description": d, "inDefinedTermSet": f"{BASE}/milon/"}
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "דף הבית", "item": f"{BASE}/"},
        {"@type": "ListItem", "position": 2, "name": "מילון", "item": f"{BASE}/milon/"},
        {"@type": "ListItem", "position": 3, "name": word, "item": f"{BASE}{url}"}]}
    meta = (f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:url" content="{BASE}{url}"><meta property="og:type" content="article">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
            f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>')
    doc = brand.document(title=title, desc=desc, canonical=f'{BASE}{url}', meta=meta,
                         kicker=brand.MILON_KICKER, h1=title,
                         crumbs=[('דף הבית', '/'), ('מילון', '/milon/'), (word, url)],
                         body=body, note=brand.MILON_NOTE, current='milon')
    d_out = os.path.join(OUT, urllib.parse.quote(word, safe=''))
    os.makedirs(d_out, exist_ok=True)
    open(os.path.join(d_out, 'index.html'), 'w', encoding='utf-8').write(doc)
    return url


def hub(words_by_len, urls):
    secs = ''
    for L in sorted(words_by_len):
        items = ' · '.join(f'<a href="/milon/w/{urllib.parse.quote(w, safe="")}/">{esc(w)}</a>'
                           for w in words_by_len[L])
        secs += f'<h2>{L} אותיות</h2><p>{items}</p>'
    body = ('<p>מילים שפותרים מחפשים: כל אחת עם הגדרה, הכתיב ברשת, התחליפים שתשבצים משתמשים בהם '
            'וההגדרות שהיא עונה עליהן. הרשימה גדלה לפי מה שמחפשים באתר.</p>' + secs)
    title = 'מילים בתשבץ: פירוש, אורך ותחליפים'
    doc = brand.document(title=title, desc='מילים שפותרי תשבצים מחפשים, עם הגדרה, כתיב ברשת ותחליפים.',
                         canonical=f'{BASE}/milon/w/', kicker=brand.MILON_KICKER, h1=title,
                         crumbs=[('דף הבית', '/'), ('מילון', '/milon/'), ('מילים', '/milon/w/')],
                         body=body, note=brand.MILON_NOTE, current='milon')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(doc)
    urls.insert(0, '/milon/w/')


def update_sitemap(urls):
    p = os.path.join(ROOT, 'docs/sitemap.xml')
    s = open(p, encoding='utf-8').read()
    s = re.sub(r'  <url><loc>%s/milon/w/[^<]*</loc></url>\n' % re.escape(BASE), '', s)
    block = ''.join(f'  <url><loc>{BASE}{u}</loc></url>\n' for u in urls)
    s = s.replace('</urlset>', block + '</urlset>')
    open(p, 'w', encoding='utf-8').write(s)


def update_milon_hub(count):
    p = os.path.join(ROOT, 'docs/milon/index.html')
    s = open(p, encoding='utf-8').read()
    block = (f'{HUB_START}<h2>מילים שמחפשים</h2><p>{count} מילים עם הגדרה, כתיב ברשת ותחליפים - '
             f'<a href="/milon/w/"><b>כל המילים</b></a>.</p>{HUB_END}')
    if HUB_START in s:
        s = re.sub(re.escape(HUB_START) + '.*?' + re.escape(HUB_END), block, s, flags=re.S)
    elif '<!-- defs-hub-end -->' in s:
        s = s.replace('<!-- defs-hub-end -->', '<!-- defs-hub-end -->\n' + block)
    else:
        s = s.replace('</main>', block + '\n</main>')
    open(p, 'w', encoding='utf-8').write(s)


def main():
    words = load('solver/lex/words.json')
    words = {k: v for k, v in words.items() if not k.startswith('_')}
    defs = definitions()
    ctx = {'amb': load('solver/lex/ambiguities.json'),
           'freq': {norm(k): v for k, v in load('solver/crosswordese.json').items()},
           'subs': {norm(k): v for k, v in (load('solver/lex/substitutions.json').get('fwd') or {}).items()},
           'clue_pages': clue_pages()}
    built, skipped, urls = {}, [], []
    for w, spec in sorted(words.items()):
        n = norm(w)
        d = (spec or {}).get('d') or (defs.get(n) or ('', '', ''))[0]
        if not d:
            skipped.append(w)
            continue
        display = w if any(ch in 'ךםןףץ' for ch in w) or w[-1] not in UNFIN else w
        built[display] = (d, (spec or {}).get('src') or (defs.get(n) or ('', '', 'override'))[2])
    ctx['words_by_len'] = {}
    for w in sorted(built):
        ctx['words_by_len'].setdefault(len(norm(w)), []).append(w)
    for w, (d, src) in sorted(built.items()):
        urls.append(page(w, d, src, ctx))
    hub(ctx['words_by_len'], urls)
    update_sitemap(urls)
    update_milon_hub(len(built))
    print(f'word pages: {len(built)} built, {len(skipped)} skipped for lack of a definition'
          + (': ' + ', '.join(skipped[:12]) if skipped else ''))


if __name__ == '__main__':
    main()
