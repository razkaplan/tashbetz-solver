#!/usr/bin/env python3
"""Re-wrap already-generated pages in the current site shell (app/brand.py).

app/build_seo.py needs the gitignored corpus, so in a fresh clone the ~5,700
milon pages cannot be rebuilt. This rewrites only their shell: it keeps the
<head> metadata, the breadcrumb JSON-LD, the <h1> and the page body, and
regenerates everything around them (fonts, stylesheet link, header with the
site navigation, page head, promo strip, footer). Body-level markup that the
old templates styled inline is mapped to brand classes.

Idempotent: a page already on the brand shell is re-wrapped from its <main>,
so running it again after a shell change is the whole "rebuild".

Usage: python3 app/rebrand_pages.py [docs/milon ...]   (default: docs/milon)
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, 'app')
import brand  # noqa: E402

BASE = brand.BASE

# old inline styling -> brand classes (same forms build_seo.py now emits)
BODY_FIXES = [
    (re.compile(r'<small style="font-family:monospace;color:#5c5c5c">([^<]*?) · (\d+) אותיות</small>'),
     r'<small class="net">\1</small> <small>\2 אותיות</small>'),
    ('<small style="font-family:monospace;color:#5c5c5c">', '<small class="net">'),
    (re.compile(r'<td style="font-family:monospace">(.*?)</td>'), r'<td><span class="net">\1</span></td>'),
    ('<b style="color:#f22b39">', '<b style="color:var(--accent)">'),
    ('''<span style="font-family:monospace">'+esc(e.n)+'</span>''', '''<span class="net">'+esc(e.n)+'</span>'''),
    ('''<small style="font-family:monospace">'+esc(e.n)+'</small>''', '''<small class="net">'+esc(e.n)+'</small>'''),
    (''' b.style.cssText='font:inherit;padding:.5rem 1rem;border:1.5px solid #121212;border-radius:3px;background:#fff4d6;cursor:pointer';''',
     ''' b.className='btn sun sm';'''),
    ('<input id="q" placeholder=', '<input id="q" class="bigq" placeholder='),
    ('<input id="a" placeholder=', '<input id="a" class="bigq" placeholder='),
    ('<p style="font-size:.9rem">', '<p><small>'),  # letter nav / lengths line...
]
# ...whose closing tag needs the matching </small>
LETTER_NAV = re.compile(r'<p><small>(לפי אות פותחת: |אורכים זמינים: )((?:(?!</small>).)*?)</p>')


def convert(s, path):
    branded = 'class="site-head"' in s
    if branded:
        m = re.search(r'<main class="w[^"]*">\n<div class="pagehead">.*?</div>(?:<div class="promo">.*?</div>)?\n(.*?)\n</main>\n<footer class="site-foot">', s, re.S)
    else:
        m = re.search(r'</header>\n(.*?)\n<footer>', s, re.S)
    if not m:
        return None
    body = m.group(1)
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', s, re.S).group(1))
    canon = re.search(r'<link rel="canonical" href="([^"]+)">', s).group(1)
    meta = re.search(r'<link rel="canonical" href="[^"]+">(.*?)(?:<style>|<link rel="icon"|</head>)', s, re.S).group(1).strip()
    h1 = html.unescape(re.search(r'<h1>(.*?)</h1>', s, re.S).group(1))
    bc = re.search(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "BreadcrumbList".*?\})</script>', meta)
    crumbs = [(it['name'], it['item'].replace(BASE, '') or '/')
              for it in json.loads(bc.group(1))['itemListElement']] if bc else ()
    for a, b in BODY_FIXES:
        body = a.sub(b, body) if hasattr(a, 'sub') else body.replace(a, b)
    body = LETTER_NAV.sub(r'<p><small>\1\2</small></p>', body)
    body = body.replace('</small></small></p>', '</small></p>')
    defs = '/milon/d/' in canon
    return brand.document(
        title=title, desc=desc, canonical=canon, meta=meta,
        kicker=brand.DEFS_KICKER if defs else brand.MILON_KICKER, h1=h1, crumbs=crumbs,
        body=body, note=brand.DEFS_NOTE if defs else brand.MILON_NOTE, current='milon')


def main(dirs):
    n = skipped = 0
    for d in dirs:
        for path in glob.glob(os.path.join(d, '**', 'index.html'), recursive=True):
            s = open(path, encoding='utf-8').read()
            out = convert(s, path)
            if out is None:
                skipped += 1
                print('skip (no template match):', path)
                continue
            if out != s:
                open(path, 'w', encoding='utf-8').write(out)
                n += 1
    print(f'rewrapped {n} pages, skipped {skipped}')


if __name__ == '__main__':
    main(sys.argv[1:] or ['docs/milon'])
