#!/usr/bin/env python3
"""Mine the setter's substitution vocabulary from crowd explanations.

The 8,249 crowd explanations encode, in shorthand, the equivalences this genre relies on:
a name completed by a surname, a word standing for a fragment, an abbreviation.
Recurring patterns in the explanation text:

  "טומי (לפיד) ב-אנה(זק)"   -> טומי~לפיד, אנה~זק   (parenthetical completion)
  "מנה=ספר"                  -> מנה~ספר             (explicit equals)
  "ל קס איש דת אתיופי"       -> קס~איש דת אתיופי    (gloss run)
  "אפיל זה מאוחר"            -> אפיל~מאוחר          ("זה" copula)

We extract only high-confidence shapes, count them across the whole corpus, and expose
lookup both ways. Used at solve time to answer "what can this clue word stand for?" —
the question that leaves surfaces unaccounted for when it goes unanswered.

Build:  python3 solver/substitutions.py build
Query:  python3 solver/substitutions.py <word>        # what this word can stand for
        python3 solver/substitutions.py --to <word>   # what stands for this word
"""
import json, re, os, sys, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def held_out():
    """Dev/eval gold answers (same rule as lexicon.py / retrieve_defs.py). A clue's own
    crowd explanation is exactly what a held-out eval would need to NOT have seen — mining
    a substitution pair from a dev/eval clue's own explanation and then crediting that pair
    with recovering the SAME clue's answer is circular, not solving power."""
    out = set()
    p = os.path.join(ROOT, 'data/dataset/clues.jsonl')
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            if r.get('split') in ('dev', 'eval') and r.get('answer_raw'):
                out.add(norm(r['answer_raw']))
    return out

def explanations():
    out = []
    p = 'data/answers/answers_parsed.json'
    if os.path.exists(p):
        for puz in json.load(open(p)):
            for c in puz['clues']:
                for e in c.get('explanations', []):
                    out.append((e, c.get('answer', '')))
    for f in glob.glob('data/answers/extra/*.json'):
        d = json.load(open(f))
        for puz in d.get('puzzles', []):
            for c in puz['clues']:
                for e in c.get('explanations', []):
                    out.append((e, c.get('answer', '')))
    return out

def mine(expls, exclude=None):
    ho = held_out() if exclude is None else exclude
    pairs = Counter()
    for e, ans in expls:
        if norm(ans) in ho:
            continue  # held-out clue's own explanation — would leak its answer, see held_out()
        if not e or len(e) > 200:
            continue
        # 1. parenthetical completion:  word (completion)
        for m in re.finditer(r'([א-ת]{2,12})\s*\(([א-ת\s]{2,20})\)', e):
            a, b = norm(m.group(1)), norm(m.group(2))
            if a and b and a != b:
                pairs[(a, b)] += 1
        # 2. explicit equals / copula
        for pat in [r'([א-ת]{2,12})\s*=\s*([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+זה\s+([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+פירושה?\s+([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+כלומר\s+([א-ת]{2,15})']:
            for m in re.finditer(pat, e):
                a, b = norm(m.group(1)), norm(m.group(2))
                if a and b and a != b:
                    pairs[(a, b)] += 2   # explicit statements weigh more
    return pairs

def build():
    os.chdir(ROOT)
    expls = explanations()
    pairs = mine(expls)
    fwd, rev = defaultdict(list), defaultdict(list)
    for (a, b), n in pairs.items():
        if n >= 1:
            fwd[a].append([b, n])
            rev[b].append([a, n])
    for d in (fwd, rev):
        for k in d:
            d[k].sort(key=lambda x: -x[1])
    os.makedirs(os.path.join(HERE, 'lex'), exist_ok=True)
    json.dump({'fwd': fwd, 'rev': rev},
              open(os.path.join(HERE, 'lex/substitutions.json'), 'w'),
              ensure_ascii=False)
    print(f'explanations mined: {len(expls)}')
    print(f'distinct substitution pairs: {len(pairs)}')
    print(f'head words: {len(fwd)}')
    print('\nmost frequent substitutions:')
    for (a, b), n in pairs.most_common(20):
        print(f'  {a} ~ {b}   (x{n})')

def query(w, reverse=False):
    p = os.path.join(HERE, 'lex/substitutions.json')
    if not os.path.exists(p):
        print('run: python3 solver/substitutions.py build'); return
    d = json.load(open(p))
    idx = d['rev'] if reverse else d['fwd']
    k = norm(w)
    hits = idx.get(k, [])
    if not hits:
        print(f'{w}: (no recorded substitution)')
        return
    label = 'can be written as' if not reverse else 'can stand for'
    print(f'{w} {label}:')
    for b, n in hits[:15]:
        print(f'   {b}   (seen {n}x)')

if __name__ == '__main__':
  try:
    if len(sys.argv) < 2:
        print(__doc__)
    elif sys.argv[1] == 'build':
        build()
    elif sys.argv[1] == '--to':
        query(sys.argv[2], reverse=True)
    else:
        query(sys.argv[1])
  except BrokenPipeError:
    # e.g. `... | head -3` in bootstrap.sh closes stdout early; that is not a real
    # failure and must not make bootstrap.sh (set -euo pipefail) abort mid-run.
    sys.stderr.close()
