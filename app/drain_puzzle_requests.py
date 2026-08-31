#!/usr/bin/env python3
"""Drain the personal-crossword request queue into real published boards.

Flow (weekly, same shape as app/drain_requests.py for definitions):
  1. Read the queue: the committed snapshot first, a live GET only if there
     is no snapshot and egress allows one.
  2. For each requested topic, try to build it MECHANICALLY: the generator
     already accepts a free Hebrew phrase and retrieves its answers from the
     entity index, so "כדורגל ישראלי" needs no new data. A topic that yields
     enough answers is generated at the requested level and appended to
     docs/nosim/puzzles.json.
  3. Print what it could not build. Those need a curated bank in
     solver/lex/topics.json first (CLAUDE.md content rules apply: verified
     facts only, no newspaper clue text, plain hyphens).
  4. --resolve clears the shipped topics from the server queue.
  5. Caller then runs app/build_topics.py, commits and merges to main.

REVIEW BEFORE PUBLISHING. These topics are reader-written text that ends up
in a page title, so read every one before it ships; the queue API deliberately
publishes nothing by itself.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'solver'))
import topicgen                                    # noqa: E402

API = 'https://tashbetz.gtmascode.dev/api/puzzle-request'
SNAP = 'solver/lex/pzreq_queue_snapshot.json'
PUZZLES = 'docs/nosim/puzzles.json'
MIN_ANSWERS = 25          # below this a free phrase cannot carry a board
SLUG_OK = re.compile(r'^[א-ת0-9-]{2,60}$')


def slugify(topic):
    s = re.sub(r'\s+', '-', topic.strip())
    s = re.sub(r'[^א-ת0-9-]', '', s)
    return s if SLUG_OK.match(s) else None


def load_queue(args):
    if args and os.path.exists(args[0]):
        return json.load(open(args[0], encoding='utf-8'))['items']
    if os.path.exists(SNAP):
        # An EMPTY snapshot is an answer, not a miss: it means Saturday's
        # mirror ran and nobody asked for anything. Falling through to the
        # network here made the weekly run fail in a sandbox with no egress
        # every week until the first request arrived.
        items = json.load(open(SNAP, encoding='utf-8')).get('items') or []
        print(f'using committed snapshot {SNAP}: {len(items)} requests')
        return items
    try:
        with urllib.request.urlopen(API, timeout=30) as r:
            return json.load(r)['items']
    except Exception as e:
        sys.exit(f'queue fetch failed ({e}) and no snapshot available; '
                 f'fetch the JSON another way and pass it as a file')


def main():
    do_resolve = '--resolve' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--resolve']
    queue = load_queue(args)
    ctx = topicgen.load()

    puzzles = json.load(open(PUZZLES, encoding='utf-8')) if os.path.exists(PUZZLES) else []
    have = {(p['topic'], p['level']) for p in puzzles}

    shipped, needs_bank = [], []
    for item in queue:
        topic = item['topic'] if isinstance(item, dict) else str(item)
        level = int(item.get('lv') or item.get('level') or 2) if isinstance(item, dict) else 2
        level = level if level in topicgen.LEVELS else 2
        slug = slugify(topic)
        if not slug:
            print(f'SKIP  {topic!r}: cannot be a URL')
            continue
        if (slug, level) in have or (topic, level) in have:
            shipped.append(topic)
            continue
        terms = topicgen.topic_terms(ctx, topic)
        if len(terms) < MIN_ANSWERS:
            needs_bank.append((item.get('count', 1) if isinstance(item, dict) else 1,
                               topic, len(terms)))
            continue
        # same best-of-seeds search the published boards get: a requested
        # board is written once and read many times too
        p = topicgen.generate_best(topic, level)
        if not p:
            needs_bank.append((item.get('count', 1) if isinstance(item, dict) else 1,
                               topic, len(terms)))
            continue
        p['topic'] = slug
        p['title'] = topic
        p['blurb'] = (f'תשבץ לפי בקשה על {topic}. התשובות נאספו מאינדקס המילון '
                      f'של הפרויקט, וכל הגדרה מגיעה עם ההוכחה שלה.')
        p['requested'] = True
        puzzles.append(p)
        have.add((slug, level))
        shipped.append(topic)
        print(f"BUILT {topic} (level {level}, {len(terms)} candidate answers) -> "
              f"/nosim/{slug}/{level}/ topical {p['topicality']:.0%}")

    json.dump(puzzles, open(PUZZLES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\npuzzle file: {len(puzzles)} boards; shipped now: {len(shipped)}')

    if needs_bank:
        needs_bank.sort(reverse=True)
        print('\nNEEDS A BANK (add to solver/lex/topics.json following the CLAUDE.md')
        print('content rules, most-requested first):')
        for c, t, n in needs_bank:
            print(f'  {c}x  {t}   (only {n} answers found automatically)')

    if do_resolve and shipped:
        body = json.dumps({'resolve': shipped}).encode()
        req = urllib.request.Request(API, data=body,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            print('resolved on server:', json.load(r))


if __name__ == '__main__':
    main()
