#!/usr/bin/env python3
"""Free competitor-keyword research CLI (no paid API, no signup).

The paid-tool suggestions in the usual roundups (Ahrefs/Semrush/Ubersuggest)
are login-gated freemium; none has a free keyless API. What IS free and
machine-readable is the competitors' own output:

  mordo   pitaronfree.blogspot.com labels every post with the exact query
          phrasings it targets ("X פירוש", "X 5 אותיות", "מה זה X?"...).
          The Blogspot JSON feed exposes the full label vocabulary - the
          market leader's complete keyword-targeting playbook (~76K terms
          on 2026-08-28).
  yo-yoo  /crossword/popular/1 is their own popularity ranking - their top
          keywords by internal traffic, published.
  arrow   arrowword.co.il's "כל הפתרונות" page lists every page they chose
          to build - a curated inventory from the niche's fastest climber.

Usage:
  python3 scraper/keyword_research.py            # fetch all, print summary
  python3 scraper/keyword_research.py --out F    # also write raw JSON

Results feed marketing_kb/competitor_keywords.{json,md}. In the remote agent
sandbox direct fetches may be proxy-blocked; there, fetch the same URLs via
the Bright Data MCP tools and reuse the parsing functions below.
"""
import argparse, collections, json, re, sys, urllib.request

MORDO_FEED = ('https://pitaronfree.blogspot.com/feeds/posts/summary'
              '?alt=json&max-results=1')
YOYO_POPULAR = 'https://www.yo-yoo.co.il/crossword/popular/1'
ARROW_ALL = 'https://arrowword.co.il/%D7%9B%D7%9C-%D7%94%D7%A4%D7%AA%D7%A8%D7%95%D7%A0%D7%95%D7%AA/'
UA = {'User-Agent': 'Mozilla/5.0 (keyword-research; tashbetz-solver)'}


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read().decode('utf-8')


def mordo_terms(feed_text):
    """All label terms from the Blogspot feed - mordo's keyword vocabulary."""
    terms = re.findall(r'\{"term":"((?:[^"\\]|\\.)*)"\}', feed_text)
    return [t.replace('\\"', '"') for t in terms]


def classify(terms):
    """Bucket mordo's phrasings into the query patterns they target."""
    pat = collections.Counter()
    for t in terms:
        if re.search(r'\d+ אותיות', t): pat['<X> N אותיות'] += 1
        elif t.startswith('איך נקרא'): pat['איך נקרא X'] += 1
        elif 'מילה נרדפת' in t or 'מילים נרדפות' in t: pat['X מילה נרדפת'] += 1
        elif t.endswith('?') or t.startswith('מה '): pat['שאלה (מה זה X?)'] += 1
        elif 'תשבץ' in t or 'תשחץ' in t: pat['X תשבץ/תשחץ'] += 1
        elif 'פירוש' in t or 'מילון' in t: pat['X פירוש/מילון'] += 1
        else: pat['הגדרה חשופה'] += 1
    return pat


def md_links(html_text, must, must_not=()):
    """Anchor texts of links whose URL contains `must` (and none of must_not)."""
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.S):
        url, txt = m.group(1), re.sub(r'<[^>]+>|\s+', ' ', m.group(2)).strip()
        if txt and must in url and not any(x in url for x in must_not):
            out.append(txt)
    return out


def core(t):
    """Strip modifier suffixes to the core definition phrase."""
    t = re.sub(r'\s*[-–|].*$', '', t)
    t = re.sub(r'\s*(תשחץ|תשבץ|מילון|פירוש|מילה נרדפת|\d+ אותיות)\s*$', '', t)
    return t.strip(' ?"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--max-mordo', type=int, default=1,
                    help='feed max-results; labels come with any value')
    args = ap.parse_args()

    data = {}
    try:
        data['mordo_terms'] = mordo_terms(fetch(MORDO_FEED))
    except Exception as e:
        print(f'mordo fetch failed ({e}); use Bright Data MCP instead', file=sys.stderr)
        data['mordo_terms'] = []
    try:
        data['yoyo_popular'] = md_links(fetch(YOYO_POPULAR), '/crossword/solution/')
    except Exception as e:
        print(f'yo-yoo fetch failed ({e})', file=sys.stderr)
        data['yoyo_popular'] = []
    try:
        data['arrowword_all'] = md_links(fetch(ARROW_ALL), 'arrowword.co.il',
                                         ('/category/', 'wp-content'))
    except Exception as e:
        print(f'arrowword fetch failed ({e})', file=sys.stderr)
        data['arrowword_all'] = []

    print(f"mordo label terms: {len(data['mordo_terms'])}")
    for k, v in classify(data['mordo_terms']).most_common():
        print(f'  {k}: {v}')
    print(f"yo-yoo top entries: {len(data['yoyo_popular'])}")
    print(f"arrowword inventory: {len(data['arrowword_all'])}")

    cores = collections.Counter(core(t) for t in data['mordo_terms'] if core(t))
    consensus = []
    for a in dict.fromkeys(core(t) for t in data['arrowword_all']):
        if not a:
            continue
        n = cores.get(a, 0)
        inyo = any(a in core(y) or core(y) in a for y in data['yoyo_popular'])
        if n or inyo:
            consensus.append({'keyword': a, 'mordo_variants': n, 'yoyo_top': inyo})
    consensus.sort(key=lambda x: (-x['mordo_variants'], -x['yoyo_top']))
    data['consensus'] = consensus
    print(f'consensus keywords: {len(consensus)}')
    for c in consensus[:20]:
        print(f"  {c['keyword']}: mordo×{c['mordo_variants']}"
              + (' · yoyo-top' if c['yoyo_top'] else ''))

    if args.out:
        json.dump(data, open(args.out, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f'wrote {args.out}')


if __name__ == '__main__':
    main()
