#!/usr/bin/env python3
"""Per-clue candidate generation — diverse hypotheses for the proof gate to filter.

Why this exists: the measured bottleneck (DAILY.md, PLAN_V2.md) is not verification —
prove.py already catches bad justifications reliably. It is that the solver produces
ONE candidate and tries to justify it, backwards from how the field's SOTA works. The
ICML-2025 Cryptonite system (see RESEARCH.md, 2026-08-05 entry) generates ~20 candidate
answers per clue BEFORE any commitment to a parse, then verifies each independently.
This module is that step for Hebrew: given a clue and its enumeration, enumerate
candidates by MECHANISM (anagram / reversal / hidden / charade) crossed with
DEFINITION-SPAN HYPOTHESIS (the definition sits at one end; try each end, each length),
so the downstream solver has a ranked list to run through prove.py instead of one guess
to defend.

This tool does not decide anything. It proposes. A human or LLM solver still applies
SOLVE_PROTOCOL's confidence discipline and prove.py's executable checks before any
candidate becomes a `committed` answer — that gate is unchanged and this does not weaken
it. Candidates are always checked against the lexicon (which already excludes held-out
dev/eval answers, see lexicon.held_out_answers) so this cannot leak gold answers into its
own output.

CLI:
  python3 solver/candidates.py "<clue text>" "<enum e.g. 5,2>" [--pattern '?ו?ר??'] [--top 15]
  python3 solver/candidates.py selftest
"""
import sys, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')

sys.path.insert(0, HERE)

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

CREDIT_RE = re.compile(r'\(עפ["\']?["״]?י[^)]*\)')
SPELL_FLAG_RE = re.compile(r'\((?:מ|ח)\)')
ENUM_RE = re.compile(r'\([\d,\s]+\)\s*$')

def tokenize(clue_text):
    """Strip the contributor credit, the (מ)/(ח) spelling flag, and any trailing
    enumeration, then split into bare word tokens (punctuation stripped)."""
    t = CREDIT_RE.sub(' ', clue_text)
    t = SPELL_FLAG_RE.sub(' ', t)
    t = ENUM_RE.sub(' ', t)
    words = re.findall(r"[א-ת\"']+", t)
    return [w for w in words if norm(w)]

# ---------- grounded resources (lazy-loaded, shared with the rest of the solver) ----------
_LEX = None
_SUB = None
_IND = None

def lex():
    global _LEX
    if _LEX is None:
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            import lexicon
            _LEX = lexicon.load()
        except Exception:
            _LEX = {}
        finally:
            os.chdir(cwd)
    return _LEX

def subs():
    global _SUB
    if _SUB is None:
        import json
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUB = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUB

def indicators():
    global _IND
    if _IND is None:
        import json
        p = os.path.join(HERE, 'indicators.json')
        _IND = json.load(open(p)) if os.path.exists(p) else {}
    return _IND

def has_indicator(tokens, kind):
    """Does any indicator phrase for this mechanism appear as a substring of the
    (space-joined) leftover tokens? Substring, not exact-token match, because
    indicators inflect (בלבול / מבולבל / התבלבלה all share the same root cue)."""
    text = norm(' '.join(tokens))
    for phrase in indicators().get(kind, []):
        if norm(phrase) and norm(phrase) in text:
            return phrase
    return None

# ---------- definition-span hypotheses ----------
def def_span_hypotheses(tokens, max_def_len=3):
    """A cryptic clue's definition sits at ONE END. Yield every (side, k) split with
    the definition 1..max_def_len tokens long at the front or the back, leaving at
    least one token as wordplay material on the other side."""
    n = len(tokens)
    out = []
    for k in range(1, min(max_def_len, n - 1) + 1):
        out.append({'side': 'prefix', 'definition': tokens[:k], 'wordplay': tokens[k:]})
        out.append({'side': 'suffix', 'definition': tokens[n - k:], 'wordplay': tokens[:n - k]})
    return out

def windows(tokens):
    """All contiguous, non-empty sub-spans of tokens, as (start, end, window_tokens)."""
    n = len(tokens)
    for i in range(n):
        for j in range(i + 1, n + 1):
            yield i, j, tokens[i:j]

# ---------- mechanisms ----------
def anagram_matches(fodder_norm, L, words):
    target = Counter(fodder_norm)
    return [w for w in words if len(w) == L and w != fodder_norm and Counter(w) == target]

def reversal_matches(fodder_norm, words):
    rev = fodder_norm[::-1]
    return [rev] if rev != fodder_norm and rev in words else []

def hidden_matches(full_norm, L, words):
    out = []
    for i in range(len(full_norm) - L + 1):
        sub = full_norm[i:i + L]
        if sub in words:
            out.append(sub)
    return out

def charade_matches(tokens, enum_parts, words, sub_index):
    """Split the wordplay fodder, character-wise, into len(enum_parts) contiguous
    chunks matching the enum's own part lengths (in printed order, and reversed —
    setters do not guarantee the enum order matches surface order). A chunk counts
    as resolved if it is itself a real word, OR a recorded substitution target of
    one of the tokens it overlaps (the setter's private vocabulary, mined into
    substitutions.json). Returns whole concatenations, not individual parts."""
    if len(enum_parts) < 2:
        return []
    fodder = norm(' '.join(tokens))
    out = []
    for parts in (list(enum_parts), list(reversed(enum_parts))):
        if sum(parts) != len(fodder):
            continue
        chunks, pos, ok = [], 0, True
        for p in parts:
            chunk = fodder[pos:pos + p]
            pos += p
            resolved = None
            if chunk in words:
                resolved = chunk
            else:
                for tok in tokens:
                    for cand, _n in sub_index.get(norm(tok), []):
                        if len(cand) == p and cand in words:
                            resolved = cand
                            break
                    if resolved:
                        break
            if not resolved:
                ok = False
                break
            chunks.append(resolved)
        if ok:
            out.append(''.join(chunks))
    return out

# ---------- ranking ----------
MECH_BASE = {'anagram': 0.5, 'reversal': 0.55, 'hidden': 0.4, 'charade': 0.45}

def add(bucket, answer, mechanism, definition, fodder, indicator, side):
    score = MECH_BASE[mechanism]
    if indicator:
        score += 0.3
    if definition is not None and len(definition) <= 2:
        score += 0.1
    key = (answer, mechanism, tuple(definition) if definition else None)
    prev = bucket.get(key)
    if prev is None or score > prev['score']:
        bucket[key] = {'answer': answer, 'mechanism': mechanism,
                        'definition': ' '.join(definition) if definition else None,
                        'fodder': fodder, 'indicator': indicator, 'side': side,
                        'score': round(score, 2)}

def generate(clue_text, enum, pattern=None, top=20):
    L = sum(enum)
    tokens = tokenize(clue_text)
    words = lex()
    full_norm = norm(''.join(tokens))
    bucket = {}

    # hidden: does not need a definition/wordplay split, the surface is its own cover
    for m in hidden_matches(full_norm, L, words):
        add(bucket, m, 'hidden', None, clue_text, has_indicator(tokens, 'hidden'), None)

    for hyp in def_span_hypotheses(tokens):
        wp = hyp['wordplay']
        for i, j, win in windows(wp):
            fodder_norm = norm(''.join(win))
            if len(fodder_norm) != L:
                continue
            rest = wp[:i] + wp[j:]
            ind_a = has_indicator(rest, 'anagram')
            for m in anagram_matches(fodder_norm, L, words):
                add(bucket, m, 'anagram', hyp['definition'], ''.join(win), ind_a, hyp['side'])
            ind_r = has_indicator(rest, 'reversal')
            for m in reversal_matches(fodder_norm, words):
                add(bucket, m, 'reversal', hyp['definition'], ''.join(win), ind_r, hyp['side'])

        if len(enum) > 1:
            for m in charade_matches(wp, enum, words, subs()['fwd']):
                add(bucket, m, 'charade', hyp['definition'], ' '.join(wp), None, hyp['side'])

    out = list(bucket.values())
    if pattern:
        cells = [ch for ch in pattern if ch not in ' ']
        rx = re.compile('^' + ''.join('.' if ch in '?_' else ch for ch in cells) + '$')
        out = [c for c in out if len(c['answer']) == len(cells) and rx.match(c['answer'])]
    out.sort(key=lambda c: -c['score'])
    return out[:top]

# ---------- CLI / selftest ----------
def selftest():
    ok_all = True

    def check(name, clue_text, enum, mechanism, expect):
        nonlocal ok_all
        cands = generate(clue_text, enum, top=50)
        hit = next((c for c in cands if c['answer'] == norm(expect) and c['mechanism'] == mechanism), None)
        status = 'PASS' if hit else 'FAIL'
        ok_all = ok_all and bool(hit)
        print(f'[{status}] {name}: "{clue_text}" enum={enum} -> expect {expect} via {mechanism}'
              + (f'  (found: {hit})' if hit else f'  (got {len(cands)} candidates, none matched)'))

    print('--- synthetic clues, dictionary words only (no corpus/held-out data) ---')
    check('anagram', 'ספר בבלבול לגמרי', [3], 'anagram', 'פרס')
    check('reversal', 'בר בהיפוך', [2], 'reversal', 'רב')
    check('hidden', 'כבש לומדים בהסתר', [4], 'hidden', 'שלום')

    print('\n--- charade mechanism (direct, both part orders) ---')
    words = lex()
    out = charade_matches(['רב', 'שנה'], [2, 3], words, subs()['fwd'])
    got = 'רבשנה' in out
    ok_all = ok_all and got
    print(f"[{'PASS' if got else 'FAIL'}] charade: ['רב','שנה'] enum=[2,3] -> expect רבשנה  (got {out})")

    print('\n--- definition-span hypotheses cover both ends ---')
    hyps = def_span_hypotheses(['א', 'ב', 'ג', 'ד'])
    sides = {h['side'] for h in hyps}
    got = sides == {'prefix', 'suffix'}
    ok_all = ok_all and got
    print(f"[{'PASS' if got else 'FAIL'}] both prefix and suffix hypotheses generated: {sorted(sides)}")

    print(f"\n{'ALL PASS' if ok_all else 'SOME FAILED'}")
    return ok_all

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    clue_text = sys.argv[1]
    enum = [int(x) for x in sys.argv[2].split(',')]
    pattern = None
    top = 20
    if '--pattern' in sys.argv:
        pattern = sys.argv[sys.argv.index('--pattern') + 1]
    if '--top' in sys.argv:
        top = int(sys.argv[sys.argv.index('--top') + 1])
    cands = generate(clue_text, enum, pattern=pattern, top=top)
    if not cands:
        print('(no candidates)')
        return
    for c in cands:
        ind = f" indicator={c['indicator']!r}" if c['indicator'] else ''
        defn = f" def={c['definition']!r}" if c['definition'] else ''
        print(f"{c['score']:.2f}  {c['answer']}  [{c['mechanism']}{defn} fodder={c['fodder']!r}{ind}]")

if __name__ == '__main__':
    main()
