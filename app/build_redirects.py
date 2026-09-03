#!/usr/bin/env python3
"""Write solver/lex/redirects.json into docs/vercel.json as permanent redirects.

redirects.json is the record of every URL this site once published and then
removed, and where it goes now. It is data, kept in the repo, so that a
redirect survives a rebuild and so app/url_guard.py can check that no URL
leaves the sitemap without an entry here.

Sources are stored as the path Vercel matches - percent-decoded - and the
characters path-to-regexp treats as syntax are escaped. Vercel caps the
redirects array at 2,048 entries; this refuses to write more than that
rather than silently truncating.

Rerunnable; touches only the "redirects" key of docs/vercel.json.
"""
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(ROOT, 'solver/lex/redirects.json')
OUT = os.path.join(ROOT, 'docs/vercel.json')
VERCEL_MAX = 2048
SYNTAX = re.compile(r'([()?+*:\[\]{}])')


def load():
    return json.load(open(SRC, encoding='utf-8'))['redirects'] if os.path.exists(SRC) else {}


def source_pattern(path):
    """The decoded path, with path-to-regexp syntax characters escaped."""
    return SYNTAX.sub(r'\\\1', urllib.parse.unquote(path))


def main():
    red = load()
    cfg = json.load(open(OUT, encoding='utf-8'))
    rules = []
    for src in sorted(red):
        dst = red[src]
        if not dst or dst == src:
            continue
        rules.append({'source': source_pattern(src), 'destination': dst, 'permanent': True})
    if len(rules) > VERCEL_MAX:
        print(f'!! {len(rules)} redirects, Vercel allows {VERCEL_MAX}; not writing', file=sys.stderr)
        sys.exit(1)
    cfg['redirects'] = rules
    json.dump(cfg, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(OUT, 'a', encoding='utf-8').write('\n')
    print(f'wrote {len(rules)} redirects into docs/vercel.json')


if __name__ == '__main__':
    main()
