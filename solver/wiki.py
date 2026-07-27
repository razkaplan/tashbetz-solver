#!/usr/bin/env python3
"""Hebrew Wikipedia lookup for culture-reference clues (MediaWiki API, no key needed).

CLI:
  python3 solver/wiki.py search "יהונתן גפן"        # matching article titles
  python3 solver/wiki.py summary "יהונתן גפן"       # first-paragraph summary
  python3 solver/wiki.py whois "גנדי"               # disambiguation-aware: who/what is this
  python3 solver/wiki.py songs "יהודה פוליקר"       # song/album titles linked from an artist page
  python3 solver/wiki.py links "שייקה אופיר"        # outgoing article links (entities)

Use for FACTS ONLY (who sang X, a politician's real name, a place's Hebrew name).
Never search the clue text verbatim; never use crossword-solution sources.
"""
import sys, json, re, urllib.parse, urllib.request

API = 'https://he.wikipedia.org/w/api.php'
UA = 'tashbetz-solver/1.0 (research; contact via repo)'

def call(params):
    params = dict(params); params['format'] = 'json'
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req, timeout=25).read().decode('utf-8'))

def search(q, n=8):
    d = call({'action': 'query', 'list': 'search', 'srsearch': q, 'srlimit': n})
    return [(h['title'], re.sub(r'<[^>]+>', '', h.get('snippet', ''))) for h in d['query']['search']]

def summary(title, chars=600):
    d = call({'action': 'query', 'prop': 'extracts', 'exintro': 1, 'explaintext': 1,
              'redirects': 1, 'titles': title})
    pages = d['query']['pages']
    out = []
    for p in pages.values():
        if 'extract' in p:
            out.append((p['title'], p['extract'][:chars]))
    return out

def links(title, n=60):
    d = call({'action': 'query', 'prop': 'links', 'pllimit': n, 'redirects': 1, 'titles': title})
    out = []
    for p in d['query']['pages'].values():
        for l in p.get('links', []):
            t = l['title']
            if not t.startswith(('קטגוריה:', 'תבנית:', 'ויקיפדיה:', 'עזרה:')):
                out.append(t)
    return out

def main():
    cmd = sys.argv[1]; q = sys.argv[2]
    if cmd == 'search':
        for t, s in search(q):
            print(f'{t}  —  {s[:110]}')
    elif cmd == 'summary':
        for t, e in summary(q):
            print(f'== {t} ==\n{e}\n')
    elif cmd == 'whois':
        hits = search(q, 5)
        for t, _ in hits[:3]:
            for tt, e in summary(t, 320):
                print(f'== {tt} ==\n{e}\n')
    elif cmd in ('songs', 'links'):
        ls = links(q)
        # crude filter: song/album-ish titles are short and often quoted in he-wiki
        print('\n'.join(ls[:60]) or '(none)')
    else:
        print(__doc__)

if __name__ == '__main__':
    main()
