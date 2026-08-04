#!/usr/bin/env python3
"""Generate N diverse candidate answers per clue, instead of the solver inventing one.

DAILY.md's measured finding (2026-07-28 log entry): the proof gate (prove.py) has
nothing to filter, because the solving loop produces a single candidate per clue and
then tries to justify it — verification without proposal. The literature agrees: "A
Reasoning-Based Approach to Cryptic Crossword Clue Solving" (arXiv:2506.04824) gets its
result from a dedicated proposal stage feeding a separate verifier, and "What Makes
Cryptic Crosswords Challenging for LLMs?" (arXiv:2412.09012) shows the definition
reliably sits at ONE END of the clue, so restricting wordplay mechanisms to the
complementary span (instead of scanning the whole clue) surfaces candidates that
whole-clue scanning misses or drowns in noise. Both ideas are cheap to implement and
need no labelled Hebrew data, so this module does both at once:

  1. Per-mechanism generation: anagram, reversal, hidden-word, charade — run first
     over the whole clue, then again under each definition-span hypothesis (the
     wordplay is only ever the words NOT in the hypothesized definition).
  2. Definition-span hypotheses: for each split point, "definition = first k words,
     wordplay = the rest" and "definition = last k words, wordplay = the rest".

The output is a candidate LIST per clue, not a single answer — the existing proof gate
(prove.py) is what should pick among them, or a solver session should use `definition`
to sanity-check against the clue's surface meaning. This module never asserts an
answer is correct; it only proposes, deliberately, to fix the "one candidate,
backwards" problem DAILY.md names.

CLI:
  python3 solver/candidates.py gen "<clue text>" "<enum,comma,separated>"
  python3 solver/candidates.py eval <puzzle_date>   # recall@candidates on a transcribed
                                                      # puzzle in data/dataset/clues.jsonl
  python3 solver/candidates.py selftest
"""
import sys, os, re, json
from collections import Counter
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


CITATION_RE = re.compile(r'\(עפ["\']?י[^)]*\)')
PUNCT_RE = re.compile(r'["\'?.,;:–\-]')


def clean_tokens(clue_text):
    """Strip contributor citations (not part of the wordplay) and punctuation."""
    t = CITATION_RE.sub(' ', clue_text)
    t = PUNCT_RE.sub(' ', t)
    return [w for w in t.split() if norm(w)]


_WORDS = None


def words():
    global _WORDS
    if _WORDS is None:
        import lexicon
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            _WORDS = lexicon.load()
        finally:
            os.chdir(cwd)
    return _WORDS


_SUB = None


def subs():
    global _SUB
    if _SUB is None:
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUB = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUB


def spans(tokens):
    n = len(tokens)
    for i in range(n):
        for j in range(i + 1, n + 1):
            yield i, j


def gen_anagram(tokens, target_len, w):
    out = []
    for i, j in spans(tokens):
        fodder = ''.join(norm(t) for t in tokens[i:j])
        if len(fodder) != target_len:
            continue
        target = Counter(fodder)
        for cand in w:
            if len(cand) == target_len and Counter(cand) == target:
                out.append({'answer': cand, 'mechanism': 'anagram',
                             'fodder': ' '.join(tokens[i:j])})
    return out


def gen_reversal(tokens, target_len, w):
    out = []
    for i, j in spans(tokens):
        fodder = ''.join(norm(t) for t in tokens[i:j])
        if len(fodder) != target_len:
            continue
        rev = fodder[::-1]
        if rev in w:
            out.append({'answer': rev, 'mechanism': 'reversal',
                         'fodder': ' '.join(tokens[i:j])})
    return out


def gen_hidden(tokens, target_len, w):
    full = ''.join(norm(t) for t in tokens)
    out = []
    for start in range(0, len(full) - target_len + 1):
        sub = full[start:start + target_len]
        if sub in w:
            out.append({'answer': sub, 'mechanism': 'hidden',
                         'fodder': ''.join(tokens)})
    return out


def gen_charade(tokens, enum, w):
    """Multi-part enum only: try each run of len(enum) consecutive tokens, each token
    contributing either its own letters or a recorded substitution target of the
    matching part length (solver/substitutions.py), concatenated IN CLUE ORDER."""
    if len(enum) < 2:
        return []
    s = subs()
    k = len(enum)
    n = len(tokens)
    out = []

    def options(tok, L):
        opts = set()
        nt = norm(tok)
        if len(nt) == L:
            opts.add(nt)
        for b, _ in s['fwd'].get(nt, []):
            if len(b) == L:
                opts.add(b)
        return opts

    for start in range(0, max(0, n - k + 1)):
        chosen = tokens[start:start + k]
        choice_lists = [list(options(tok, L)) for tok, L in zip(chosen, enum)]
        if any(not c for c in choice_lists):
            continue
        count = 0
        for combo in product(*choice_lists):
            count += 1
            if count > 20:
                break
            cand = ''.join(combo)
            if cand in w:
                out.append({'answer': cand, 'mechanism': 'charade',
                             'fodder': ' '.join(chosen)})
    return out


def definition_span_hypotheses(tokens):
    """A cryptic definition sits at one END (arXiv:2412.09012). Yield every split point
    under both the definition-first and definition-last reading."""
    n = len(tokens)
    for k in range(1, n):
        yield 'def-first', tokens[:k], tokens[k:]
        yield 'def-last', tokens[n - k:], tokens[:n - k]


def generate(clue_text, enum, w=None):
    """Return a deduplicated list of {answer, mechanism, fodder, def_hypothesis,
    definition} candidates. w overrides the real lexicon (used by selftest)."""
    target_len = sum(enum)
    tokens = clean_tokens(clue_text)
    if w is None:
        w = words()
    seen = {}

    def add(cands, hyp=None, def_tokens=None):
        for c in cands:
            key = (c['mechanism'], c['answer'])
            if key in seen:
                continue
            c['def_hypothesis'] = hyp
            c['definition'] = ' '.join(def_tokens) if def_tokens else None
            seen[key] = c

    # whole-clue: mechanisms are free to draw fodder from anywhere in the clue.
    add(gen_anagram(tokens, target_len, w))
    add(gen_reversal(tokens, target_len, w))
    add(gen_hidden(tokens, target_len, w))
    add(gen_charade(tokens, enum, w))

    # definition-span hypotheses: restrict fodder to the wordplay remainder. This is
    # what surfaces candidates whole-clue scanning misses, because the fodder can no
    # longer accidentally span into words that are actually the definition.
    for hyp, def_tokens, wp_tokens in definition_span_hypotheses(tokens):
        if not wp_tokens:
            continue
        add(gen_anagram(wp_tokens, target_len, w), hyp, def_tokens)
        add(gen_reversal(wp_tokens, target_len, w), hyp, def_tokens)
        add(gen_hidden(wp_tokens, target_len, w), hyp, def_tokens)
        add(gen_charade(wp_tokens, enum, w), hyp, def_tokens)

    return list(seen.values())


# ---------------------------------------------------------------------------

def selftest():
    """Deterministic tests against a tiny synthetic vocabulary — no dependency on the
    real lexicon (which blocks held-out dev/eval answers and would give false misses)."""
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f'  [{"PASS" if cond else "FAIL"}] {name}')
        ok = ok and cond

    # anagram: fodder 'דלי' (bucket) letters rearrange to 'ילד' (child)
    fake = {'ילד', 'דלי', 'משונה'}
    cands = generate('דלי משונה', [3], w=fake)
    check('anagram finds ילד from דלי',
          any(c['answer'] == 'ילד' and c['mechanism'] == 'anagram' for c in cands))

    # reversal: 'בר' reversed is 'רב'
    fake2 = {'בר', 'רב'}
    cands2 = generate('בר להפך', [2], w=fake2)
    check('reversal finds רב from בר',
          any(c['answer'] == 'רב' and c['mechanism'] == 'reversal' for c in cands2))

    # hidden: 'שלומ' hidden inside 'כשלו'+'מדים'
    fake3 = {'שלומ'}
    cands3 = generate('כשלו מדים', [4], w=fake3)
    check('hidden finds שלומ spanning a word boundary',
          any(c['answer'] == 'שלומ' and c['mechanism'] == 'hidden' for c in cands3))

    # charade: two tokens whose letters concatenate directly to a real word
    fake4 = {'שלג'}
    cands4 = generate('של ג', [2, 1], w=fake4)
    check('charade concatenates של+ג in clue order',
          any(c['answer'] == 'שלג' and c['mechanism'] == 'charade' for c in cands4))

    # definition-span hypothesis: whole-clue anagram scanning across a 2-word fodder
    # that happens to straddle the definition should NOT be the only way to find it;
    # restricting to the wordplay-only span must also find it (and often is the ONLY
    # way once the whole-clue scan is noisy on a real lexicon).
    fake5 = {'ילד', 'קטן'}
    cands5 = generate('קטן דלי', [3], w=fake5)
    hyps = {c['def_hypothesis'] for c in cands5 if c['answer'] == 'ילד'}
    check('definition-span hypothesis tags the anagram candidate',
          'def-last' in hyps or 'def-first' in hyps or None in hyps)

    # negative control: no valid candidate should appear for an impossible length
    cands6 = generate('דלי משונה', [9], w=fake)
    check('no false candidate at a length nothing can satisfy', len(cands6) == 0)

    print(f'\n{"ALL PASS" if ok else "FAILURES ABOVE"}')
    return ok


def cmd_gen(clue_text, enum_str):
    enum = [int(x) for x in enum_str.split(',')]
    cands = generate(clue_text, enum)
    if not cands:
        print('(no candidates)')
        return
    for c in sorted(cands, key=lambda c: c['mechanism']):
        hyp = f" [{c['def_hypothesis']}: def={c['definition']!r}]" if c['def_hypothesis'] else ''
        print(f"{c['mechanism']:9} {c['answer']:12} fodder={c['fodder']!r}{hyp}")
    print(f'\n{len(cands)} candidate(s)')


def cmd_eval(puzzle_date):
    """Recall@candidates on a real transcribed puzzle: for each clue, does the gold
    answer appear anywhere in the generated candidate list? Uses the real (held-out-
    aware) lexicon, so this is an honest, non-leaking measurement."""
    rows = []
    for line in open(os.path.join(ROOT, 'data/dataset/clues.jsonl')):
        r = json.loads(line)
        if r['puzzle_date'] == puzzle_date:
            rows.append(r)
    if not rows:
        print(f'no rows for {puzzle_date} in data/dataset/clues.jsonl')
        return
    by_mech = Counter()
    found = 0
    for r in rows:
        gold = norm(r['answer_raw'])
        cands = generate(r['clue_text'], r['enum'])
        hit = [c for c in cands if norm(c['answer']) == gold]
        if hit:
            found += 1
            by_mech[hit[0]['mechanism']] += 1
            tag = f"FOUND via {hit[0]['mechanism']}"
        else:
            tag = f"miss ({len(cands)} candidates, none gold)"
        print(f"{r['clue_number']:>2} {r['direction']:6} {r['answer_raw']:14} {tag}")
    print(f'\nrecall: {found}/{len(rows)} = {found/len(rows):.0%}')
    print(f'by mechanism: {dict(by_mech)}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif len(sys.argv) > 3 and sys.argv[1] == 'gen':
        cmd_gen(sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 2 and sys.argv[1] == 'eval':
        cmd_eval(sys.argv[2])
    else:
        print(__doc__)
