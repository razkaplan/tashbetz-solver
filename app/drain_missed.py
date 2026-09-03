#!/usr/bin/env python3
"""Turn demand for pages we do not have into pages, or redirects.

Demand comes from three places, all optional:
  --snapshot   solver/lex/missed_snapshot.json - the 404 page's counter of
               paths people actually reached (mirrored weekly by
               .github/workflows/defreq-mirror.yml); default when present
  --gsc FILE   a Search Console export (CSV with a URL column and an
               impressions or clicks column) - the same signal from Google
  --from-git   every /milon/e/ page that ever existed in git history and is
               gone now (the August cleanups removed 1,474 of them)

For each dead path it decides, in this order:
  1. a live page has the same letters (finals folded)  -> redirect to it
  2. we hold a definition for the word (fillbank, curated list)
                                                       -> a /milon/w/ page,
                                                          and a redirect to it
  3. the entity still exists but has no page of its own -> redirect to its
                                                          category page anchor
  4. nothing                                            -> NEEDS-CURATION,
                                                          most-hit first

It writes solver/lex/words.json and solver/lex/redirects.json; then run
  python3 app/build_words.py && python3 app/build_redirects.py
and commit. NEEDS-CURATION words are hand-added to solver/lex/fillbank.json
(a verified definition, content rules in CLAUDE.md) and the drain rerun.

--resolve clears the fulfilled paths from the live counter (needs egress).
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), '..')
API = 'https://tashbetz.gtmascode.dev/api/missed'
SNAP = os.path.join(ROOT, 'solver/lex/missed_snapshot.json')
WORDS = os.path.join(ROOT, 'solver/lex/words.json')
REDIRECTS = os.path.join(ROOT, 'solver/lex/redirects.json')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
UNFIN = {'כ': 'ך', 'מ': 'ם', 'נ': 'ן', 'פ': 'ף', 'צ': 'ץ'}
PAGE_RX = re.compile(r'^/milon/(e|w)/([^/]+)/?$')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


def load(rel, default):
    p = os.path.join(ROOT, rel)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def demand_from_snapshot():
    snap = load('solver/lex/missed_snapshot.json', None)
    if not snap:
        return {}
    return {i['p']: int(i.get('count', 1)) for i in snap.get('items', [])}


def demand_from_gsc(path):
    out = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return out
    keys = {k.lower(): k for k in rows[0]}
    ukey = next((keys[k] for k in keys if k in ('url', 'page', 'top pages', 'address', 'כתובת')), None)
    nkey = next((keys[k] for k in keys if k in ('impressions', 'clicks', 'חשיפות', 'קליקים')), None)
    if not ukey:
        sys.exit('gsc: no URL column found')
    for r in rows:
        u = (r.get(ukey) or '').strip()
        p = urllib.parse.urlparse(u).path if '://' in u else u
        if p:
            out[p] = out.get(p, 0) + (int(float(r.get(nkey) or 1)) if nkey else 1)
    return out


def demand_from_git():
    """Every /milon/e/ page deleted at some point in history and absent now."""
    log = subprocess.run(['git', 'log', '--all', '--diff-filter=D', '--name-only', '--format=',
                          '--', 'docs/milon/e'], cwd=ROOT, capture_output=True, text=True).stdout
    gone = set()
    for line in log.split('\n'):
        m = re.match(r'docs/milon/e/([^/]+)/index\.html$', line.strip())
        if m:
            gone.add(m.group(1))
    live = set(os.listdir(os.path.join(ROOT, 'docs/milon/e')))
    return {f'/milon/e/{d}/': 1 for d in sorted(gone - live)}


def display_form(n):
    """Restore the final letter the crossword spelling folded away."""
    return n[:-1] + UNFIN.get(n[-1], n[-1]) if n else n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gsc', help='Search Console CSV export')
    ap.add_argument('--from-git', action='store_true', help='seed from pages deleted in git history')
    ap.add_argument('--resolve', action='store_true', help='clear fulfilled paths from the live counter')
    ap.add_argument('--min-hits', type=int, default=1)
    a = ap.parse_args()

    demand, why = {}, 'missed'
    if a.gsc:
        demand.update(demand_from_gsc(a.gsc)); why = 'gsc'
    if a.from_git:
        for p, c in demand_from_git().items():
            demand[p] = demand.get(p, 0) + c
        why = 'dead-url'
    if not demand:
        demand = demand_from_snapshot()
    if not demand:
        print('nothing requested: no snapshot, no --gsc, no --from-git')
        return

    ents = load('docs/milon/entities.json', [])
    by_norm = {}
    for e in ents:
        by_norm.setdefault(norm(e['t']), e)
    live_e = {norm(urllib.parse.unquote(d)): d for d in os.listdir(os.path.join(ROOT, 'docs/milon/e'))}
    wdir = os.path.join(ROOT, 'docs/milon/w')
    live_w = {norm(urllib.parse.unquote(d)): d for d in os.listdir(wdir)} if os.path.isdir(wdir) else {}
    fb = {norm(w): w for w in load('solver/lex/fillbank.json', {})}
    for key, spec in load('solver/lex/defs_curated.json', {}).items():
        if not key.startswith('_'):
            for w in (spec.get('items') or {}):
                fb.setdefault(norm(w), w)

    words = load('solver/lex/words.json', {})
    red_doc = load('solver/lex/redirects.json', {'redirects': {}})
    red = red_doc.setdefault('redirects', {})
    added_words, added_red, needs, fulfilled = 0, 0, [], []

    for path, hits in sorted(demand.items(), key=lambda kv: -kv[1]):
        if hits < a.min_hits:
            continue
        m = PAGE_RX.match(path)
        if not m:
            needs.append((hits, path, 'not a word page'))
            continue
        kind, seg = m.group(1), urllib.parse.unquote(m.group(2))
        n = norm(seg)
        src = f'/milon/{kind}/{urllib.parse.quote(seg, safe="")}/'
        if not n:
            continue
        if kind == 'e' and n in live_e and live_e[n] == urllib.parse.quote(seg, safe=''):
            fulfilled.append(path)          # the page is live; a stale report
            continue
        if kind == 'w' and n in live_w:
            fulfilled.append(path)
            continue
        if n in live_e:                                            # 1
            red[src] = f'/milon/e/{live_e[n]}/'
            added_red += 1
            fulfilled.append(path)
        elif n in live_w or n in fb:                               # 2
            word = urllib.parse.unquote(live_w[n]) if n in live_w else fb[n]
            if word not in words:
                words[word] = {'why': why, 'hits': hits}
                added_words += 1
            target = f'/milon/w/{urllib.parse.quote(word, safe="")}/'
            if src != target:
                red[src] = target
                added_red += 1
            fulfilled.append(path)
        elif n in by_norm:                                         # 3
            e = by_norm[n]
            red[src] = f'/milon/{e["c"]}-{len(n)}/#{urllib.parse.quote(n, safe="")}'
            added_red += 1
            fulfilled.append(path)
        else:                                                      # 4
            needs.append((hits, display_form(n), 'no definition held'))

    words = {'_note': 'Words that get a /milon/w/ page (app/build_words.py). A page is built only '
                      'when a definition exists: the fillbank, a curated list, or "d" here. '
                      'Fed by app/drain_missed.py.', **{k: v for k, v in words.items() if not k.startswith('_')}}
    json.dump(words, open(WORDS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    red_doc['_note'] = ('Dead URLs and where they go now. Fed by app/drain_missed.py, hand-editable; '
                        'app/build_redirects.py writes it into docs/vercel.json; app/url_guard.py '
                        'requires an entry for any URL that leaves the sitemap.')
    json.dump(red_doc, open(REDIRECTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print(f'demand: {len(demand)} paths. words added: {added_words}, redirects added: {added_red}, '
          f'needs curation: {len(needs)}')
    if needs:
        print('\nNEEDS-CURATION (most requested first; add a verified definition to '
              'solver/lex/fillbank.json and rerun):')
        for hits, w, why in needs[:40]:
            print(f'  {hits:4d}  {w}   ({why})')
        if len(needs) > 40:
            print(f'  ... and {len(needs) - 40} more')
    print('\nnext: python3 app/build_words.py && python3 app/build_redirects.py')

    if a.resolve and fulfilled:
        body = json.dumps({'resolve': fulfilled}).encode()
        req = urllib.request.Request(API, data=body, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print('resolved on the server:', json.load(r))
        except Exception as e:
            print('resolve failed (no egress?):', e)


if __name__ == '__main__':
    main()
