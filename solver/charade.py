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
PREFIXES = ('וה','שה','כש','מה','לה','בה','ו','ב','ל','מ','ש','כ','ה')

_SUBS = None
def default_subs():
    """Lazily loads the COMMITTED solver/lex/substitutions.json. NOT held-out safe: that
    file predates substitutions.held_out()'s 2026-08-23 fix and was built from a corpus
    mix that may include dev/eval puzzles' own crowd explanations. Fine for the CLI's own
    ad-hoc `candidates`/`eval` use against train-split data, but a caller scoring a
    held-out puzzle (candidates.py's recall_eval(), 2026-11-25) MUST pass its own
    `subs=` built from substitutions.mine()'s in-memory, held-out-excluding rebuild
    instead — see candidates.py's charade_candidates() for the safe wiring."""
    global _SUBS
    if _SUBS is None:
        s = json.load(open('solver/lex/substitutions.json'))
        subs = {}
        for d in (s['rev'], s['fwd']):           # equivalences cited in both directions
            for k, v in d.items():
                subs.setdefault(k, []).extend(v)
        _SUBS = subs
    return _SUBS

def frags_for(tok, subs=None):
    """substitution fragments for a clue token, trying bare + de-prefixed stems"""
    t = norm(tok)
    stems = {t}
    for p in PREFIXES:
        if t.startswith(p) and len(t) - len(p) >= 2:
            stems.add(t[len(p):])
    table = subs if subs is not None else default_subs()
    out = {}
    for s in stems:
        for frag, cnt in table.get(s, []):
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

def candidates(clue, total, max_parts=3, subs=None):
    """`subs` is injectable (tests / callers, e.g. candidates.py's held-out-safe rebuild)
    instead of always falling back to the committed, NOT held-out-safe default_subs()."""
    toks = [w for w in re.findall(r'[א-ת"\']+', clue)]
    tok_frags = [(i, toks[i], frags_for(toks[i], subs)) for i in range(len(toks))]
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

def selftest():
    """Unit-level checks on an injected synthetic subs table — never touches the
    committed lex/substitutions.json or any puzzle's gold data, same discipline
    candidates.py/lexicon.py/substitutions.py enforce for theirs."""
    ok = True

    print('--- charade: two tokens\' injected fragments concatenate to the full length ---')
    # 'אחד' -> 'של' (2), 'שני' -> 'ום' (2): שלום (4) via a 2-part charade.
    subs = {norm('אחד'): [(norm('של'), 3)], norm('שני'): [(norm('ום'), 2)]}
    hits = [a for _, a, _ in candidates('אחד שני דברים', 4, subs=subs)]
    found = norm('שלום') in hits
    print(f'  found שלום as של+ום from an injected table: {found} (expected True)')
    ok &= found

    print('--- charade: an injected table is used INSTEAD of default_subs() (held-out '
          'safety) ---')
    # same clue, but with an EMPTY injected table: the real committed substitutions.json
    # must not be consulted, so the same charade must NOT be found.
    hits_empty = [a for _, a, _ in candidates('אחד שני דברים', 4, subs={})]
    not_found = norm('שלום') not in hits_empty
    print(f'  with subs={{}} (no fallback to the committed file): {not_found} '
          f'(expected True — proves a caller\'s own table, not the committed file, '
          f'controls what this function can find)')
    ok &= not_found

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif sys.argv[1] == 'candidates':
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
