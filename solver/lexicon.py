#!/usr/bin/env python3
"""Hebrew lexicon tools for the solver — pattern match, anagram, contains.

Wordlist = hspell (129k) + all corpus answers (crosswordese/names the dict lacks),
all normalized to final-form-folded, space-free Hebrew letters.

CLI:
  python3 solver/lexicon.py pattern '?ו?ר'       # words matching (?=any letter), exact length
  python3 solver/lexicon.py anagram שמיגנדי       # real words that are anagrams of the letters
  python3 solver/lexicon.py contains ניב 5        # 5-letter words containing ניב as substring
  python3 solver/lexicon.py sub שראל               # words that contain this substring (any len)
Every command prints up to 60 matches, corpus/crosswordese matches first.
"""
import sys, os, re, json, glob
from collections import Counter

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
HERE = os.path.dirname(__file__)

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def held_out_answers(clues_path='data/dataset/clues.jsonl', by_date_dir='data/answers/by_date'):
    """Normalized answers belonging to dev/eval puzzles — these MUST NOT enter the lexicon,
    or a pattern lookup silently hands the solver the gold answer (measured: this inflated
    a run to 96%). Train-split answers are legitimate priors.

    Blocks every gold answer for a held-out puzzle DATE, not just clues that happen to have
    a transcribed row in clues.jsonl. A puzzle can be dev/eval with only SOME of its clues
    transcribed — e.g. an image missing across 1-13 (documented in DAILY.md, confirmed
    across 4 different weeks). Before this fix, an untranscribed slot's gold answer stayed
    fully exposed in the corpus/culture lexicon tiers, because the old block set was built
    by iterating clues.jsonl rows, which only exist for transcribed clues — a real leak
    vector any future run that pattern-matches an untranscribed slot's crossing letters
    would have walked straight into (flagged but not fixed in the 2026-08-16 log entry).
    Once a puzzle date is known to be dev/eval (from any one transcribed row), every answer
    in that puzzle's full answer key (`data/answers/by_date/<date>.json`, independent of
    transcription) is blocked, closing the gap without needing the grid at all."""
    out = set()
    dates = set()
    if os.path.exists(clues_path):
        for line in open(clues_path):
            r = json.loads(line)
            if r.get('split') in ('dev', 'eval'):
                dates.add(r['puzzle_date'])
                if r.get('answer_raw'):
                    out.add(norm(r['answer_raw']))
    for d in dates:
        af = os.path.join(by_date_dir, f'{d}.json')
        if not os.path.exists(af):
            continue
        for c in json.load(open(af)).get('clues', []):
            w = c.get('answer')
            if w:
                out.add(norm(w))
    return out


def load():
    words = {}  # word -> priority (3 culture, 2 corpus, 1 dict)
    BLOCK = held_out_answers()
    hp = os.path.join(HERE, 'lex/hspell.txt')
    if os.path.exists(hp):
        for line in open(hp, encoding='utf-8'):
            w = norm(line)
            if w:
                words.setdefault(w, 1)
    # corpus answers (high priority — names, slang, multiword grid entries)
    for pat in ['data/answers/answers_parsed.json']:
        if os.path.exists(pat):
            for p in json.load(open(pat)):
                for c in p['clues']:
                    w = norm(c.get('answer'))
                    if w and w not in BLOCK:
                        words[w] = 2
    for f in glob.glob('data/answers/extra/*.json'):
        d = json.load(open(f))
        for p in d.get('puzzles', []):
            for c in p['clues']:
                w = norm(c.get('answer'))
                if w and w not in BLOCK:
                    words[w] = 2
    # culture entities (song titles, artists, politicians, places) from he-wikipedia.
    # Highest priority: these are exactly the answers the solver cannot invent.
    cp = os.path.join(HERE, 'lex/culture.json')
    if os.path.exists(cp):
        for kind, items in json.load(open(cp)).items():
            for t in items:
                w = norm(t)
                if w and w not in BLOCK:
                    words[w] = 3
    return words

def rank(words, matches):
    return sorted(matches, key=lambda w: (-words[w], len(w), w))[:60]

def selftest():
    """Unit-level checks on synthetic fixture files in a temp dir — never touches real
    puzzle data, same discipline candidates.py/defspan.py enforce for their own selftests."""
    import tempfile, shutil
    ok = True
    tmp = tempfile.mkdtemp()
    try:
        clues_p = os.path.join(tmp, 'clues.jsonl')
        by_date_dir = os.path.join(tmp, 'by_date')
        os.makedirs(by_date_dir)
        with open(clues_p, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'puzzle_date': '2099-01-01', 'clue_number': 1,
                                 'direction': 'across', 'split': 'dev',
                                 'answer_raw': 'שלום'}, ensure_ascii=False) + '\n')
            f.write(json.dumps({'puzzle_date': '2099-06-01', 'clue_number': 1,
                                 'direction': 'across', 'split': 'train',
                                 'answer_raw': 'תפוח'}, ensure_ascii=False) + '\n')
        with open(os.path.join(by_date_dir, '2099-01-01.json'), 'w', encoding='utf-8') as f:
            json.dump({'clues': [
                {'clue_number': 1, 'direction': 'across', 'answer': 'שלום'},   # transcribed
                {'clue_number': 2, 'direction': 'across', 'answer': 'ערב'},    # NOT transcribed — the gap this fix closes
            ]}, f, ensure_ascii=False)

        block = held_out_answers(clues_p, by_date_dir)
        print('--- transcribed dev-puzzle answer is blocked (pre-existing behaviour) ---')
        found = norm('שלום') in block
        print(f'  שלום blocked: {found} (expected True)')
        ok &= found

        print('--- untranscribed dev-puzzle SLOT answer is ALSO blocked (the fix) ---')
        found = norm('ערב') in block
        print(f'  ערב blocked even with no clues.jsonl row: {found} (expected True)')
        ok &= found

        print('--- train-split puzzle answer is NOT blocked ---')
        found = norm('תפוח') not in block
        print(f'  תפוח left unblocked: {found} (expected True)')
        ok &= found

        print('--- a held-out date with no by_date file at all does not crash ---')
        block2 = held_out_answers(clues_p, os.path.join(tmp, 'nonexistent'))
        found = norm('שלום') in block2
        print(f'  falls back to dataset-row blocking, no crash: {found} (expected True)')
        ok &= found
    finally:
        shutil.rmtree(tmp)

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
    words = load()
    cmd = sys.argv[1]
    if cmd == 'pattern':
        pat = norm(sys.argv[2].replace('?', '\x00')).replace('\x00', '.')
        # keep ? positions: rebuild regex honoring length
        raw = sys.argv[2]
        rx = '^' + ''.join('.' if ch in '?_' else ch for ch in norm(raw.replace('?', '\x01').replace('_', '\x01'))) + '$'
        # norm strips \x01; do it manually
        cells = [ch for ch in raw if ch not in ' ']
        rx = '^' + ''.join('.' if ch in '?_' else ch for ch in cells) + '$'
        L = len(cells)
        r = re.compile(rx)
        out = [w for w in words if len(w) == L and r.match(w)]
        print('\n'.join(rank(words, out)) or '(no match)')
    elif cmd == 'anagram':
        target = Counter(norm(sys.argv[2]))
        L = sum(target.values())
        out = [w for w in words if len(w) == L and Counter(w) == target]
        print('\n'.join(rank(words, out)) or '(no match)')
    elif cmd == 'contains':
        sub = norm(sys.argv[2]); L = int(sys.argv[3])
        out = [w for w in words if len(w) == L and sub in w]
        print('\n'.join(rank(words, out)) or '(no match)')
    elif cmd == 'sub':
        sub = norm(sys.argv[2])
        out = [w for w in words if sub in w]
        print('\n'.join(rank(words, out)) or '(no match)')
    else:
        print('usage: pattern|anagram|contains|sub')

if __name__ == '__main__':
    main()
