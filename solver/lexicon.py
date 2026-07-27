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

def load():
    words = {}  # word -> priority (2 corpus, 1 dict)
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
                    if w:
                        words[w] = 2
    for f in glob.glob('data/answers/extra/*.json'):
        d = json.load(open(f))
        for p in d.get('puzzles', []):
            for c in p['clues']:
                w = norm(c.get('answer'))
                if w:
                    words[w] = 2
    # culture entities (song titles, artists, politicians, places) from he-wikipedia.
    # Highest priority: these are exactly the answers the solver cannot invent.
    cp = os.path.join(HERE, 'lex/culture.json')
    if os.path.exists(cp):
        for kind, items in json.load(open(cp)).items():
            for t in items:
                w = norm(t)
                if w:
                    words[w] = 3
    return words

def rank(words, matches):
    return sorted(matches, key=lambda w: (-words[w], len(w), w))[:60]

def main():
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
