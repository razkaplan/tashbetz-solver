#!/usr/bin/env python3
"""One-off audit: does substitution_candidates() leak a dev puzzle's OWN gold answer
through a substitution pair mined from that SAME puzzle's own crowd explanation?

solver/lex/substitutions.json is built (substitutions.py) from ALL crowd explanations
in the corpus, dev/eval puzzles included, with no held-out filtering (unlike
lexicon.py's word list, which does exclude dev/eval answers). A substitution pair
mined from clue X's own explanation and then used to generate a candidate for that
same clue X would be reading the answer key, not deriving wordplay.

Method: rebuild the pair index TWICE — once from the full main corpus (matching what
solver/lex/substitutions.json already contains for the main-corpus portion), once with
the target dev puzzle's own date excluded — and compare substitution_candidates()
output for that puzzle's clues between the two. Any candidate that appears only in the
"with self" version and not the "leave-one-out" version is leak-derived and must be
excluded from any reported recall number.

Usage: python3 scratch_audit_leak.py <clues.jsonl> <puzzle_date e.g. 2026-05-29>
"""
import sys, os, re, json
from collections import Counter, defaultdict

sys.path.insert(0, 'solver')
import candidates as C

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


def explanations(exclude_date=None):
    out = []
    p = 'data/answers/answers_parsed.json'
    d = json.load(open(p))
    for puz in d:
        pd = puz.get('puzzle_date')
        if exclude_date and pd == exclude_date:
            continue
        for c in puz['clues']:
            for e in c.get('explanations', []):
                out.append((e, c.get('answer', '')))
    return out


def mine(expls):
    pairs = Counter()
    for e, ans in expls:
        if not e or len(e) > 200:
            continue
        for m in re.finditer(r'([א-ת]{2,12})\s*\(([א-ת\s]{2,20})\)', e):
            a, b = norm(m.group(1)), norm(m.group(2))
            if a and b and a != b:
                pairs[(a, b)] += 1
        for pat in [r'([א-ת]{2,12})\s*=\s*([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+זה\s+([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+פירושה?\s+([א-ת]{2,15})',
                    r'([א-ת]{2,12})\s+כלומר\s+([א-ת]{2,15})']:
            for m in re.finditer(pat, e):
                a, b = norm(m.group(1)), norm(m.group(2))
                if a and b and a != b:
                    pairs[(a, b)] += 2
    return pairs


def to_index(pairs):
    fwd, rev = defaultdict(list), defaultdict(list)
    for (a, b), n in pairs.items():
        fwd[a].append([b, n])
        rev[b].append([a, n])
    for dd in (fwd, rev):
        for k in dd:
            dd[k].sort(key=lambda x: -x[1])
    return {'fwd': fwd, 'rev': rev}


def main():
    clues_path, puzzle_date_iso = sys.argv[1], sys.argv[2]
    # answers_parsed.json dates are DD/MM/YYYY; clues.jsonl dates are ISO. Convert.
    y, m, d = puzzle_date_iso.split('-')
    legacy_date = f'{d}/{m}/{y}'

    full_pairs = mine(explanations())
    loo_pairs = mine(explanations(exclude_date=legacy_date))
    print(f'full corpus pairs: {len(full_pairs)}, leave-one-out ({puzzle_date_iso}) pairs: {len(loo_pairs)}')
    diff = {k: v for k, v in full_pairs.items() if loo_pairs.get(k, 0) < v}
    print(f'pairs that lose support when this puzzle is excluded: {len(diff)}')
    for k, v in list(diff.items())[:20]:
        print(f'  {k}: full={v} loo={loo_pairs.get(k, 0)}')

    rows = [json.loads(l) for l in open(clues_path)]
    rows = [r for r in rows if r.get('puzzle_date') == puzzle_date_iso and r.get('answer_raw')]
    print(f'\n{len(rows)} clues for {puzzle_date_iso}')

    full_idx = to_index(full_pairs)
    loo_idx = to_index(loo_pairs)

    leaked = []
    for r in rows:
        gold = norm(r['answer_raw'])
        target_len = sum(r['enum'])
        C._SUBS = full_idx
        full_cands = {c['answer'] for c in C.substitution_candidates(r['clue_text'], target_len)}
        C._SUBS = loo_idx
        loo_cands = {c['answer'] for c in C.substitution_candidates(r['clue_text'], target_len)}
        if gold in full_cands and gold not in loo_cands:
            leaked.append((r['clue_number'], r['direction'], r['clue_text'], gold))

    print(f'\nLEAK CHECK: {len(leaked)} gold answers recoverable ONLY with this puzzle\'s own '
          f'explanations included (self-referential leak)')
    for row in leaked:
        print(' ', row)


if __name__ == '__main__':
    main()
