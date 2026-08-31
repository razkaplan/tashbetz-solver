#!/usr/bin/env python3
"""Which things in our index were in the Israeli news this week.

Writes solver/lex/topics_news.json, a topic bank that solver/topicgen.py picks
up like any other, so the weekly news crossword is built by the same generator
as every other topic puzzle.

What it stores, and what it deliberately does not
------------------------------------------------
It reads the public RSS feeds of Israeli news sites and keeps ONE thing: which
entities ALREADY IN docs/milon/entities.json were mentioned, and how often.
The description published as the clue is OUR description of that entity, from
our own index. No headline, standfirst or article text is stored, and none is
published. That is the same rule the rest of the site runs on (see README): we
publish our own words about public facts, never a newspaper's text.

An entity that is not already in our index is dropped rather than described
from the headline, so the bank cannot fill up with invented facts.

Egress: news sites are unreachable from the agent sandbox, so this normally
runs on a GitHub runner (.github/workflows/news-weekly.yml) which commits the
snapshot; every downstream step reads the committed file.

  python3 scraper/news_israel.py              fetch, write the bank
  python3 scraper/news_israel.py --dry-run    fetch, print, write nothing
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Verified reachable from a GitHub runner on 2026-08-31. israelhayom returned
# 403 to the runner and kan's news feed 404s, so they are out; a feed that
# starts failing is skipped, not fatal.
FEEDS = [
    'https://www.ynet.co.il/Integration/StoryRss2.xml',
    'https://www.ynet.co.il/Integration/StoryRss1854.xml',   # politics
    'https://www.ynet.co.il/Integration/StoryRss3.xml',      # world
    'https://rss.walla.co.il/feed/1?type=main',
    'https://rss.walla.co.il/feed/22?type=main',             # sport
    'https://www.maariv.co.il/Rss/RssFeedsMivzakiChadashot',
    'https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=942',
]
OUT = 'solver/lex/topics_news.json'
MIN_MENTIONS = 1
MAX_TERMS = 90
MIN_TERMS = 20        # below this there is not enough for a board
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

# Categories whose one-line description is a usable clue. Same rule as
# solver/topicgen.py: "שיר של X" identifies the answer to nobody.
CLUEABLE = {'city_il', 'world_city', 'nation', 'island', 'mountain', 'river',
            'stream', 'lake_sea', 'desert', 'valley', 'region', 'bible', 'site',
            'park', 'museum', 'military', 'common', 'politician', 'athlete'}
# Politicians and athletes are in: in a news puzzle "שר האוצר" is exactly the
# clue you want. Their descriptions are still required to be specific below.


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'tashbetz-news/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def feed_text(xml):
    """Feed text, read once to count names and then thrown away.

    Titles alone gave two matches across a whole week's feeds, which is not a
    board; descriptions roughly quadruple the text without changing what is
    kept, since nothing from here is ever stored or published.
    """
    parts = re.findall(r'<title>(.*?)</title>', xml, re.S)
    parts += re.findall(r'<description>(.*?)</description>', xml, re.S)
    return [unescape(re.sub(r'<[^>]+>', ' ', m)) for m in parts]


def index():
    ents = json.load(open('docs/milon/entities.json', encoding='utf-8'))
    shared = {}
    for e in ents:
        d = (e.get('d') or '').strip()
        if d:
            shared[d] = shared.get(d, 0) + 1
    out = {}
    for e in ents:
        d = (e.get('d') or '').strip()
        n = norm(e['t'])
        # 3 letters or fewer matches far too much inside running text
        if (e['c'] in CLUEABLE and len(d) >= 12 and shared[d] <= 3
                and 4 <= len(n) <= 11 and n not in d):
            out.setdefault(e['t'], {'n': n, 'd': d, 'c': e['c'],
                                    'rx': mention_rx(e['t'])})
    return out


def mention_rx(name):
    """Match the name as a word, tolerating one attached Hebrew prefix.

    A plain substring test missed "באיראן" and "מתל אביב", which is most of
    how a name actually appears in a headline, and matched names sitting
    inside longer words. Both ends are anchored on a non-letter.
    """
    body = r'\s+'.join(re.escape(w) for w in name.split())
    return re.compile(rf'(?<![א-ת])[בלמהוכשׁו]?{body}(?![א-ת])')


def harvest(feeds=FEEDS, verbose=True):
    ents = index()
    counts, seen_feeds = {}, 0
    for url in feeds:
        try:
            xml = fetch(url)
        except Exception as e:                      # a dead feed is not a failure
            if verbose:
                print(f'  skip {url}: {e}')
            continue
        seen_feeds += 1
        blob = ' ' + re.sub(r'\s+', ' ', ' '.join(feed_text(xml))) + ' '
        for name, meta in ents.items():
            hits = len(meta['rx'].findall(blob))
            if hits:
                counts[name] = counts.get(name, 0) + hits
    if verbose:
        print(f'feeds read: {seen_feeds}/{len(feeds)}; entities mentioned: {len(counts)}')
    return counts, ents


def build_bank(counts, ents, when=None):
    when = when or dt.date.today()
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    terms, used = {}, set()
    for name, c in top:
        if c < MIN_MENTIONS or len(terms) >= MAX_TERMS:
            continue
        meta = ents[name]
        if meta['n'] in used:
            continue
        used.add(meta['n'])
        terms[name] = meta['d']
    year, week, _ = when.isocalendar()
    return {
        '_comment': 'Generated by scraper/news_israel.py. Entities from our own '
                    'index that Israeli news feeds mentioned this week, with OUR '
                    'descriptions. No newspaper text is stored or published.',
        'hadashot': {
            'title': 'חדשות השבוע',
            'subject': 'שבועי',
            'tags': ['חדשות', 'שבועי'],
            'blurb': f'התשבץ השבועי על מי ומה היו בחדשות, שבוע {week} של {year}. '
                     f'התשובות הן שמות ומקומות שהופיעו השבוע בכותרות, וההגדרות '
                     f'הן ההגדרות שלנו מן המילון, לא טקסט מן העיתון.',
            'week': f'{year}-W{week:02d}',
            'generated': when.isoformat(),
            'terms': terms,
            'entities': [],
            'curated': [],
        },
    }


def main():
    dry = '--dry-run' in sys.argv
    counts, ents = harvest()
    if not counts:
        sys.exit('no feed could be read; nothing written (the snapshot on disk stands)')
    bank = build_bank(counts, ents)
    terms = bank['hadashot']['terms']
    print(f"week {bank['hadashot']['week']}: {len(terms)} terms")
    for name in list(terms)[:15]:
        print(f'  {counts[name]:>3}x  {name:<22} {terms[name][:50]}')
    if dry:
        return
    if len(terms) < MIN_TERMS:
        sys.exit(f'only {len(terms)} terms (need {MIN_TERMS}): too thin for a '
                 f'board, keeping the old bank')
    json.dump(bank, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
