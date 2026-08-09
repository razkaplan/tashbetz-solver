#!/usr/bin/env python3
"""Mechanical charade enumeration (lever 3, from the research queue in DAILY.md).

Charade (שרשור) is the most common mechanism in the corpus yet was solved by pure
LLM reasoning. This tool makes it mechanical: tokens of the clue (in order) are mapped
to answer fragments via the mined substitution table; ordered combinations whose total
length matches the enumeration become candidates, each with a ready-made proof sketch.

CLI:
  python3 solver/charade.py candidates "<clue>" <total_len>   # ranked candidates
  python3 solver/charade.py eval                              # corpus hit-rate report
"""
import json, os, re, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)
_S = json.load(open('solver/lex/substitutions.json'))
SUBS = {}
for d in (_S['rev'], _S['fwd']):           # equivalences clue in both directions
    for k, v in d.items():
        SUBS.setdefault(k, []).extend(v)
PREFIXES = ('וה','שה','כש','מה','לה','בה','ו','ב','ל','מ','ש','כ','ה')

def frags_for(tok):
    """substitution fragments for a clue token, trying bare + de-prefixed stems"""
    t = norm(tok)
    stems = {t}
    for p in PREFIXES:
        if t.startswith(p) and len(t) - len(p) >= 2:
            stems.add(t[len(p):])
    out = {}
    for s in stems:
        for frag, cnt in SUBS.get(s, []):
            out[frag] = max(out.get(frag, 0), cnt)
        if 2 <= len(s) <= 6:            # a token may appear verbatim in the answer
            out.setdefault(s, 0)
    return out

_LEX = None
def lex():
    global _LEX
    if _LEX is None:
        sys.path.insert(0, 'solver'); import lexicon
        _LEX = set(lexicon.load())
    return _LEX

def candidates(clue, total, max_parts=3):
    toks = [w for w in re.findall(r'[א-ת"\']+', clue)]
    tok_frags = [(i, toks[i], frags_for(toks[i])) for i in range(len(toks))]
    results = {}
    def rec(start, parts, length):
        if parts and length == total and len(parts) >= 2:
            ans = ''.join(f for _, f, _ in parts)
            score = sum(c for _, _, c in parts) + len(parts)
            proof = ' + '.join(f'{f}={t}' for t, f, _ in parts)
            if ans not in results or results[ans][0] < score:
                results[ans] = (score, proof)
        if len(parts) >= max_parts or length >= total:
            return
        for i, tok, frs in tok_frags[start:]:
            for frag, cnt in frs.items():
                if length + len(frag) <= total:
                    rec(i + 1, parts + [(tok, frag, cnt)], length + len(frag))
    rec(0, [], 0)
    L = lex()
    ranked = sorted(((s + (20 if a in L else 0), a, p) for a, (s, p) in results.items()), reverse=True)
    return [r for r in ranked if r[1] in L] or ranked

def main():
    if sys.argv[1] == 'candidates':
        for s, a, p in candidates(sys.argv[2], int(sys.argv[3]))[:15]:
            print(f'[{s}] {a}   ({p})')
    elif sys.argv[1] == 'eval':
        tot = hit = 0
        for line in open('data/dataset/clues.jsonl'):
            c = json.loads(line)
            if c.get('split') != 'train': continue
            ans = norm(c.get('answer_raw', ''))
            expl = ' '.join(c.get('explanations_crowd', []))
            if not (3 <= len(ans) <= 9): continue
            if any(k in expl for k in ('אנגר', 'להפך', 'היפוך', 'נשמע', 'משותפת')): continue
            cands = [a for _, a, _ in candidates(c['clue_text'], len(ans))[:25]]
            if not cands: continue
            tot += 1
            hit += ans in cands
        print(f'train charade-ish clues with candidates: {tot}; gold in top-25: {hit} ({hit/max(tot,1):.1%})')

if __name__ == '__main__':
    main()
