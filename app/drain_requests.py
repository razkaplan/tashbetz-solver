#!/usr/bin/env python3
"""Drain the reader definition-request queue into /milon/d/ page specs.

Flow (weekly Routine + CLAUDE.md):
  1. GET the queue from /api/define-request (phrases readers asked for).
  2. For each phrase, try MECHANICAL fulfillment: map the head word to a
     category and grep the rest against entity descriptions. >=5 matches ->
     append a spec to solver/lex/defs_requested.json (data, no code).
  3. Print what it could NOT fulfill - the running agent hand-curates those
     into the same file as "items" specs (CLAUDE.md content rules apply:
     verified facts only, no newspaper clue text, plain hyphens).
  4. --resolve marks fulfilled phrases done on the server.
  5. Caller then runs app/build_defs.py and commits.

Network note: needs direct egress (or run inside a session whose proxy allows
the site; in the remote agent sandbox use the Bright Data MCP for the GET and
skip --resolve until egress exists).
"""
import json, os, re, sys, urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = 'https://tashbetz.gtmascode.dev/api/define-request'
SPECS = 'solver/lex/defs_requested.json'
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

E = json.load(open('docs/milon/entities.json', encoding='utf-8'))

# head word of a requested phrase -> candidate entity categories
HEAD_CATS = {
    'עיר': ['world_city', 'city_il'], 'יישוב': ['city_il'], 'כפר': ['city_il'],
    'מדינה': ['nation'], 'בירה': ['world_city'],
    'נהר': ['river', 'stream'], 'נחל': ['stream'],
    'הר': ['mountain'], 'אי': ['island'], 'מדבר': ['desert'],
    'עמק': ['valley'], 'ים': ['lake_sea'], 'אגם': ['lake_sea'],
    'קיבוץ': ['kibbutz'], 'מושב': ['moshav'], 'שכונה': ['neighborhood'],
    'זמר': ['artist'], 'זמרת': ['artist'], 'להקה': ['artist'],
    'שחקן': ['actor'], 'שחקנית': ['actor'],
    'סופר': ['author'], 'סופרת': ['author'], 'משורר': ['author'],
    'ספורטאי': ['athlete'], 'כדורגלן': ['athlete'], 'כדורסלן': ['athlete'],
    'פוליטיקאי': ['politician'], 'שר': ['politician'],
    'דמות': ['bible'], 'מלך': ['bible'], 'נביא': ['bible'],
    'שיר': ['song'], 'אתר': ['site'], 'פארק': ['park'], 'מוזיאון': ['museum'],
}
STOP = {'של', 'ב', 'עם', 'על', 'או', 'גם', 'תשבץ', 'תשחץ', 'מילון', 'פתרון'}


def mechanical(phrase):
    """(cat, rx, matches) for the best category match, or None."""
    words = phrase.split()
    if not words:
        return None
    head = words[0]
    cats = HEAD_CATS.get(head)
    if not cats:
        return None
    # content tokens: everything after the head, prefixes stripped
    toks = []
    for w in words[1:]:
        w = re.sub(r'^[בלמהוכש]', '', w) if len(w) > 3 else w
        if w and w not in STOP:
            toks.append(re.escape(w))
    if not toks:
        return None
    # AND semantics: every content token must appear in the description.
    # OR-joining matched 'מדינה בדרום אירופה' for 'מדינה בדרום אמריקה'.
    rx = ''.join(f'(?=.*{t})' for t in toks)
    best = None
    for cat in cats:
        hits = [e for e in E if e['c'] == cat and e.get('d') and re.search(rx, e['d'])]
        if len(hits) >= 5 and (best is None or len(hits) > best[2]):
            best = (cat, rx, len(hits))
    return best


def main():
    do_resolve = '--resolve' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--resolve']
    SNAP = 'solver/lex/defs_queue_snapshot.json'
    if args and os.path.exists(args[0]):
        # explicit file (e.g. fetched via Bright Data MCP)
        queue = json.load(open(args[0], encoding='utf-8'))['items']
    elif os.path.exists(SNAP) and json.load(open(SNAP, encoding='utf-8'))['items']:
        # committed mirror (.github/workflows/defreq-mirror.yml, Saturdays) -
        # the egress-free default for sandboxed drain runs
        queue = json.load(open(SNAP, encoding='utf-8'))['items']
        print(f'using committed snapshot {SNAP}')
    else:
        try:
            with urllib.request.urlopen(API, timeout=30) as r:
                queue = json.load(r)['items']
        except Exception as e:
            sys.exit(f'queue fetch failed ({e}) and no snapshot available; '
                     f'fetch the JSON another way and pass it as a file')

    specs = json.load(open(SPECS, encoding='utf-8'))
    existing_phrases = {s['phrase'] for s in specs.values()}
    fulfilled, needs_curation = [], []

    for item in queue:
        phrase = item['q']
        if phrase in existing_phrases:
            fulfilled.append(phrase)
            continue
        m = mechanical(phrase)
        if m:
            cat, rx, n = m
            slug = phrase.replace(' ', '-')  # Hebrew slugs are fine (arrowword-style)
            specs[slug] = {'phrase': phrase, 'cat': cat, 'rx': rx}
            existing_phrases.add(phrase)
            fulfilled.append(phrase)
            print(f'AUTO  {phrase} -> {cat} /{rx}/ ({n} answers)')
        else:
            needs_curation.append((item.get('count', 1), phrase))

    json.dump(specs, open(SPECS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\nspecs file: {len(specs)} total; fulfilled now: {len(fulfilled)}')

    if needs_curation:
        needs_curation.sort(reverse=True)
        print('\nNEEDS CURATION (add as "items" specs in defs_requested.json,')
        print('following CLAUDE.md content rules; most-requested first):')
        for c, p in needs_curation:
            print(f'  {c}x  {p}')

    if do_resolve and fulfilled:
        body = json.dumps({'resolve': fulfilled}).encode()
        req = urllib.request.Request(API, data=body,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            print('resolved on server:', json.load(r))


if __name__ == '__main__':
    main()
