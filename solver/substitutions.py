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

Build:    python3 solver/substitutions.py build
Query:    python3 solver/substitutions.py <word>        # what this word can stand for
          python3 solver/substitutions.py --to <word>   # what stands for this word
Selftest: python3 solver/substitutions.py selftest
"""
import json, re, os, sys, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def held_out(clues_path=None, by_date_dir=None):
    """Dev/eval gold answers (same rule as lexicon.py / retrieve_defs.py). A clue's own
    crowd explanation is exactly what a held-out eval would need to NOT have seen — mining
    a substitution pair from a dev/eval clue's own explanation and then crediting that pair
    with recovering the SAME clue's answer is circular, not solving power.

    Blocks every gold answer for a held-out puzzle DATE, not just clues that happen to have
    a transcribed row in clues.jsonl — mirrors lexicon.held_out_answers()'s 2026-08-21 fix
    (queue item 7), applied here to close the identical gap flagged (not fixed) that same
    run as item 7b. explanations() below sources from `data/answers/answers_parsed.json`
    UNCONDITIONALLY for every one of the 52 puzzles regardless of transcription state — the
    exact same unconditional-corpus shape that made lexicon.py's old row-only block set a
    real leak, so a dev/eval puzzle with any untranscribed clue would, before this fix, let
    mine() mine a substitution pair directly out of that untranscribed slot's own crowd
    explanation, unblocked."""
    out = set()
    dates = set()
    p = clues_path or os.path.join(ROOT, 'data/dataset/clues.jsonl')
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            if r.get('split') in ('dev', 'eval'):
                dates.add(r['puzzle_date'])
                if r.get('answer_raw'):
                    out.add(norm(r['answer_raw']))
    bd = by_date_dir or os.path.join(ROOT, 'data/answers/by_date')
    for d in dates:
        af = os.path.join(bd, f'{d}.json')
        if not os.path.exists(af):
            continue
        for c in json.load(open(af)).get('clues', []):
            w = c.get('answer')
            if w:
                out.add(norm(w))
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

def selftest():
    """Unit-level checks on synthetic fixture files in a temp dir — never touches real
    puzzle data, same discipline lexicon.py/candidates.py/defspan.py enforce for theirs."""
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

        block = held_out(clues_p, by_date_dir)
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

        print('--- mine() actually excludes an explanation whose answer is held out ---')
        expls = [('הפתרון הוא שלום', 'שלום'), ('אמת זה נכון', 'נכון')]
        pairs = mine(expls, exclude=block)
        leaked = any(a == norm('שלום') or b == norm('שלום') for a, b in pairs)
        print(f'  held-out clue mined into a pair: {leaked} (expected False)')
        ok &= not leaked
    finally:
        shutil.rmtree(tmp)

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok

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
    elif sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
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
