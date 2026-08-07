#!/usr/bin/env python3
"""Fetch 14across answers pages and parse clue/answer/explanations.

Complements the Scraper Studio collector (c_mrti1oa41uj3sd86bn) whose published
version drops the data-content answer attribute. Output: data/answers/answers_parsed.json
"""
import urllib.request, re, json, time, sys, html as htmllib

def parse_page(page):
    m = re.search(r'פתרונות לתשבץ היגיון[^<]*?(\d{2}/\d{2}/\d{4})', page)
    date = m.group(1) if m else None
    clues = []
    # each clue block: question_number span ... actual-answer data-content ... help-texts ul
    block_re = re.compile(
        r"question_number'>([^<]+)</span>.*?actual-answer' data-content='([^']*)'(.*?)(?=question_number'>|$)",
        re.S)
    for num_txt, answer, rest in block_re.findall(page):
        num_m = re.match(r'\s*(\d+)\s+(מאוזן|מאונך)', num_txt)
        if not num_m:
            continue
        expl = []
        ul = re.search(r"<ul>(.*?)</ul>", rest, re.S)
        if ul:
            expl = [htmllib.unescape(x.strip()) for x in re.findall(r'<li>(.*?)</li>', ul.group(1), re.S)]
        clues.append({
            'clue_number': int(num_m.group(1)),
            'direction': 'across' if num_m.group(2) == 'מאוזן' else 'down',
            'answer': htmllib.unescape(answer),
            'explanations': expl,
        })
    return date, clues

def fetch(u, retries=5, base_delay=2.5):
    """14across intermittently serves a bot-check redirect (HTTP 202, sgcaptcha) instead
    of the page — observed on roughly half of requests in one run, at random, unrelated
    to request rate. A plain retry with a short delay reliably gets a real 200 within a
    few attempts, so retry here rather than let one unlucky request drop a whole puzzle."""
    for attempt in range(retries):
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
        try:
            page = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
        except Exception:
            time.sleep(base_delay * (attempt + 1))
            continue
        date, clues = parse_page(page)
        if date is not None:
            return date, clues
        time.sleep(base_delay * (attempt + 1))
    return None, []

def main():
    urls = [u.strip() for u in open('data/answer_urls.txt') if u.strip()]
    out = []
    failed = []
    for i, u in enumerate(urls):
        date, clues = fetch(u)
        out.append({'puzzle_date': date, 'source_url': u, 'clues': clues})
        if date is None:
            failed.append(u)
        print(f'{i+1}/{len(urls)} {date}: {len(clues)} clues', flush=True)
        time.sleep(1.2)
    json.dump(out, open('data/answers/answers_parsed.json', 'w'), ensure_ascii=False, indent=1)
    total = sum(len(p['clues']) for p in out)
    empty = sum(1 for p in out for c in p['clues'] if not c['answer'])
    print(f'DONE: {len(out)} puzzles, {total} clues, {empty} empty answers')
    if failed:
        print(f'WARNING: {len(failed)} puzzle(s) still failed after retries (bot-check did not '
              f'clear) and are recorded with puzzle_date=null — the by_date rebuild step skips '
              f'these; re-run this script later to fill them in:')
        for u in failed:
            print(f'  {u}')

if __name__ == '__main__':
    main()
