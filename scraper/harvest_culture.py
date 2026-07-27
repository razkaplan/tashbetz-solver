#!/usr/bin/env python3
"""Harvest Israeli culture entities (song titles, artists, politicians, places) from
Hebrew Wikipedia categories into solver/lex/culture.json.

These become (a) lexicon entries so `lexicon.py pattern/anagram` can surface a song
title or a person's name as a candidate answer, and (b) a browsable prior for the
solver's culture-reference clues.

Titles/names only — no article bodies, no lyrics.
"""
import json, time, urllib.parse, urllib.request, os, re

API = 'https://he.wikipedia.org/w/api.php'
UA = 'tashbetz-solver/1.0 (research)'

CATS = {
    'song':      ['שירים בעברית', 'זמר עברי'],
    'artist':    ['זמרים ישראלים', 'זמרות ישראליות', 'להקות רוק ישראליות', 'פזמונאים ישראלים'],
    'politician':['חברי הכנסת'],
    'place':     ['ערים במחוז הצפון', 'ערים במחוז המרכז', 'ערים במחוז הדרום', 'ערים במחוז חיפה'],
    'bible':     ['אישים בתנ"ך'],
}
MAX_PER_CAT = 700

def call(params):
    params = dict(params); params['format'] = 'json'
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))

def members(cat, depth=1, budget=MAX_PER_CAT):
    """Return page titles in a category, descending one level into subcategories."""
    out, subcats, cont = [], [], None
    while len(out) < budget:
        p = {'action': 'query', 'list': 'categorymembers',
             'cmtitle': f'קטגוריה:{cat}', 'cmlimit': 500}
        if cont: p['cmcontinue'] = cont
        try:
            d = call(p)
        except Exception as e:
            print('   retry/skip:', str(e)[:40], flush=True); time.sleep(8); break
        for m in d.get('query', {}).get('categorymembers', []):
            t = m['title']
            if t.startswith('קטגוריה:'):
                subcats.append(t.split(':', 1)[1])
            elif m['ns'] == 0:
                out.append(t)
        cont = d.get('continue', {}).get('cmcontinue')
        if not cont: break
        time.sleep(1.2)
    if depth > 0:
        for sc in subcats[:25]:
            if len(out) >= budget: break
            out.extend(members(sc, depth - 1, budget - len(out)))
            time.sleep(1.0)
    return out

def clean(t):
    # drop parenthetical disambiguators: "שיר (אלבום)" -> "שיר"
    return re.sub(r'\s*\([^)]*\)\s*$', '', t).strip()

def main():
    os.makedirs('solver/lex', exist_ok=True)
    out = {}
    for kind, cats in CATS.items():
        seen = set()
        for c in cats:
            for t in members(c):
                ct = clean(t)
                if 1 < len(ct) <= 40 and re.search(r'[א-ת]', ct):
                    seen.add(ct)
            print(f'  {kind}/{c}: {len(seen)} so far', flush=True)
        out[kind] = sorted(seen)
        print(f'{kind}: {len(out[kind])}', flush=True)
    json.dump(out, open('solver/lex/culture.json', 'w'), ensure_ascii=False, indent=0)
    print('total entities:', sum(len(v) for v in out.values()))

if __name__ == '__main__':
    main()
