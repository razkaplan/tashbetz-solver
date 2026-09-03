#!/usr/bin/env python3
"""No published URL disappears silently.

Compares docs/sitemap.xml as committed (HEAD) with the working tree. Every
URL that left the sitemap must be accounted for: a redirect in
solver/lex/redirects.json, or an explicit tombstone in
solver/lex/tombstones.json with a reason. Otherwise this exits 1.

Why: in August 2026 three cleanups removed 1,474 entity pages that Google had
already indexed, with no redirect and no 404 page, and one of them was still
ranking three weeks later. The sitemap is the record of what we published;
a URL leaving it is a decision, and this makes it an explicit one.

Run it before committing any build that touches the sitemap (the rebuild
workflows do). `--base <ref>` compares against another commit.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
BASE = 'https://tashbetz.gtmascode.dev'
LOC = re.compile(r'<loc>([^<]+)</loc>')


def urls_of(text):
    return {u.replace(BASE, '') for u in LOC.findall(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='HEAD', help='git ref to compare the sitemap against')
    a = ap.parse_args()
    try:
        before = subprocess.run(['git', 'show', f'{a.base}:docs/sitemap.xml'], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        print('url_guard: no committed sitemap to compare against; nothing to check')
        return
    after = open(os.path.join(ROOT, 'docs/sitemap.xml'), encoding='utf-8').read()
    gone = urls_of(before) - urls_of(after)
    if not gone:
        print(f'url_guard: no URL left the sitemap ({len(urls_of(after))} URLs)')
        return
    red = {}
    p = os.path.join(ROOT, 'solver/lex/redirects.json')
    if os.path.exists(p):
        red = json.load(open(p, encoding='utf-8')).get('redirects', {})
    tomb = {}
    p = os.path.join(ROOT, 'solver/lex/tombstones.json')
    if os.path.exists(p):
        tomb = json.load(open(p, encoding='utf-8')).get('tombstones', {})
    bad = sorted(u for u in gone if u not in red and u not in tomb)
    print(f'url_guard: {len(gone)} URLs left the sitemap; '
          f'{len(gone) - len(bad)} have a redirect or a tombstone')
    if bad:
        for u in bad[:40]:
            print('   ', u)
        if len(bad) > 40:
            print(f'    ... and {len(bad) - 40} more')
        print('\nEach needs an entry in solver/lex/redirects.json (where it goes now) or\n'
              'solver/lex/tombstones.json (why it is gone). Then rerun.')
        sys.exit(1)


if __name__ == '__main__':
    main()
