#!/usr/bin/env python3
"""Scrape 14across answers+explanations for additional (simpler) logic crosswords.

For each crossword id: fetch the base page, read its date dropdown, take the most
recent MAX_DATES dates, fetch each, parse with the same block parser as parse_answers.py.
Output: data/answers/extra/<id>_<name>.json
"""
import urllib.request, urllib.parse, re, json, time, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse_answers import parse_page

CROSSWORDS = {
    12: 'תרתי משמע, דקל בנו',
    5: 'הפוך על הפוך, דקל בנו',
    2: 'ידיעות יום שני, דקל בנו',
    3: 'ידיעות יום רביעי, דקל בנו',
    49: 'לאישה, דקל בנו',
    62: 'גלובס, היגיון פשוט, ליאור ליאני',
}
MAX_DATES = 60
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode('utf-8', 'replace')

def main():
    os.makedirs('data/answers/extra', exist_ok=True)
    for cid, name in CROSSWORDS.items():
        base = f'https://www.14across.co.il/answers.php?crossword={cid}&name=' + urllib.parse.quote(name, safe=',')
        page = fetch(base)
        dates = re.findall(r'date=(\d{1,2}/\d{1,2}/\d{4})', page)
        seen = []
        for d in dates:
            if d not in seen:
                seen.append(d)
        dates = seen[:MAX_DATES]
        out = []
        for i, d in enumerate(dates):
            try:
                p = fetch(base + '&date=' + d)
                pdate, clues = parse_page(p)
                if clues:
                    out.append({'puzzle_date': pdate or d, 'clues': clues})
            except Exception as e:
                print(f'  {d}: ERR {e}', flush=True)
            time.sleep(1.0)
            if (i + 1) % 10 == 0:
                print(f'  [{cid}] {i+1}/{len(dates)}', flush=True)
        fn = f'data/answers/extra/{cid}.json'
        json.dump({'crossword_id': cid, 'name': name, 'puzzles': out}, open(fn, 'w'), ensure_ascii=False, indent=1)
        total = sum(len(p["clues"]) for p in out)
        print(f'[{cid}] {name}: {len(out)} puzzles, {total} clues -> {fn}', flush=True)

if __name__ == '__main__':
    main()
