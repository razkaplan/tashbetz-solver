#!/usr/bin/env python3
"""Mechanical candidate generation — N diverse candidates per clue, not one.

Why this exists: the measured bottleneck (DAILY.md log, 2026-07-28) is that the solver
proposes a single answer and tries to justify it after the fact. That is backwards for a
cryptic: the setter builds the answer from parts, so a machine should propose every
mechanically-derivable string that fits the enum, and let the executable proof gate
(prove.py) throw out the ones that don't check out. This module does the proposing.

It scans the clue text mechanically for three of the highest-yield mechanisms in
PLAYBOOK.md (anagram 16%, reversal 7%, hidden ~2%, and together the majority of clues
where the fodder is a *literal, contiguous run of clue words* rather than a synonym
substitution — the PLAYBOOK's own empirical finding is that 85% of anagram clues work
this way). For every hit it also reports which end of the clue is left over once the
fodder is removed — a mechanical answer to "which end holds the definition" (the other
lever in the queue): whichever side of the fodder window has text remaining is the
definition-span hypothesis for that candidate.

Charade/container/double-definition are NOT attempted here: they usually route through a
synonym (means() in prove.py), which needs semantic judgement this script does not have.
Sliding a window and checking a dictionary is comparatively rare to be wrong; guessing
synonyms mechanically is not.

CLI:
  python3 solver/candidates.py "<clue text>" <enum_total> [N]
  python3 solver/candidates.py selftest
"""
import sys, os, re, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
MAXWIN = 5  # PLAYBOOK: anagram/reversal fodder is empirically 1-5 clue words

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def tokenize(clue):
    """Words in reading order, with parenthetical credits/enum notes stripped —
    "(עפ"י X)" and similar are never part of the wordplay surface."""
    stripped = re.sub(r'\([^)]*\)', ' ', clue or '')
    return [w for w in re.findall(r'[א-ת]+', stripped)]

_WORDS = None
_ANAG_IDX = None

def words():
    global _WORDS
    if _WORDS is None:
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            import lexicon
            _WORDS = lexicon.load()
        finally:
            os.chdir(cwd)
    return _WORDS

def anagram_index():
    """(length, sorted-letters) -> [word, ...], built once. Makes anagram lookup O(1)
    per window instead of O(vocab) — vocab is ~140k words, windows are ~dozens per clue."""
    global _ANAG_IDX
    if _ANAG_IDX is None:
        idx = {}
        for w in words():
            key = (len(w), ''.join(sorted(w)))
            idx.setdefault(key, []).append(w)
        _ANAG_IDX = idx
    return _ANAG_IDX

def _def_span(tokens, i, j):
    """i:j is the fodder window (token indices, half-open). Whichever side still has
    words is the definition-span hypothesis; PLAYBOOK confirms a cryptic definition
    sits at one END, so a fodder window touching only one edge is the strong case."""
    left, right = tokens[:i], tokens[j:]
    if left and not right:
        return 'end', ' '.join(left)      # fodder is the clue's tail -> definition leads
    if right and not left:
        return 'start', ' '.join(right)   # fodder is the clue's head -> definition trails
    if left and right:
        return 'middle', ' '.join(left) + ' ... ' + ' '.join(right)
    return 'whole', ''

def anagram_candidates(tokens, total_len):
    out = []
    idx = anagram_index()
    for i in range(len(tokens)):
        acc = Counter()
        for j in range(i, min(i + MAXWIN, len(tokens))):
            acc += Counter(norm(tokens[j]))
            n = sum(acc.values())
            if n > total_len:
                break
            if n == total_len:
                fodder = ' '.join(tokens[i:j + 1])
                fodder_joined = norm(fodder)
                key = (total_len, ''.join(sorted(fodder_joined)))
                for w in idx.get(key, []):
                    if w == fodder_joined:
                        continue  # identity, not a rearrangement
                    span, dtext = _def_span(tokens, i, j + 1)
                    out.append({'mechanism': 'anagram', 'answer': w, 'fodder': fodder,
                                'def_span': span, 'def_text': dtext, 'lex_tier': words()[w]})
    return out

def reversal_candidates(tokens, total_len):
    out = []
    w = words()
    for i in range(len(tokens)):
        acc = Counter()
        buf = ''
        for j in range(i, min(i + MAXWIN, len(tokens))):
            piece = norm(tokens[j])
            buf += piece
            n = len(buf)
            if n > total_len:
                break
            if n == total_len:
                rev = buf[::-1]
                if rev in w and rev != buf:
                    span, dtext = _def_span(tokens, i, j + 1)
                    out.append({'mechanism': 'reversal', 'answer': rev,
                                'fodder': ' '.join(tokens[i:j + 1]),
                                'def_span': span, 'def_text': dtext, 'lex_tier': w[rev]})
    return out

def hidden_candidates(clue_text, total_len):
    """Answer runs contiguously through the clue's letters, crossing word boundaries —
    no fodder window to remove, so the whole clue does double duty as the definition."""
    out = []
    w = words()
    text = norm(clue_text)
    seen = set()
    for i in range(len(text) - total_len + 1):
        sub = text[i:i + total_len]
        if sub in w and sub not in seen:
            seen.add(sub)
            out.append({'mechanism': 'hidden', 'answer': sub, 'fodder': sub,
                        'def_span': 'hidden', 'def_text': clue_text, 'lex_tier': w[sub]})
    return out

MECH_PRIOR = {'anagram': 3, 'reversal': 2, 'hidden': 1}  # rough order-of-magnitude from
                                                          # PLAYBOOK's frequency counts

def generate(clue_text, total_len, n=20):
    tokens = tokenize(clue_text)
    cands = (anagram_candidates(tokens, total_len)
             + reversal_candidates(tokens, total_len)
             + hidden_candidates(clue_text, total_len))
    # dedup: keep the single best-evidenced hit per (answer, mechanism)
    best = {}
    for c in cands:
        key = (c['answer'], c['mechanism'])
        score = (c['lex_tier'], MECH_PRIOR[c['mechanism']], -len(c['fodder']))
        if key not in best or score > best[key][0]:
            best[key] = (score, c)
    ranked = sorted(best.values(), key=lambda kv: kv[0], reverse=True)
    return [c for _, c in ranked[:n]]

def selftest():
    """Anagram and hidden are real PLAYBOOK.md worked examples (train corpus, already
    published in the repo). Reversal is a CONSTRUCTED sanity check (אבן/נבא, both plain
    hspell words), not a corpus example: every documented reversal in this genre routes
    through a synonym first (PLAYBOOK 1.5 — e.g. "פתח" clued, "החל" is the word actually
    reversed), which this mechanical scanner cannot do since it has no synonym step. The
    puzzle's own literal reversal this run (2026-06-05 7-across, נכו -> וכנ) can't be used
    here either: as a dev-split answer it's correctly excluded from the lexicon by
    held_out_answers(), so this test would silently stop meaning anything the day someone
    promotes that puzzle out of dev. Verify literal reversal separately with:
      python3 solver/candidates.py "פרעה נכו, מלבד זאת" 3
    (answer will be missing from the printed candidates while 2026-06-05 stays dev/eval —
    that IS the leak guard working, not a bug)."""
    cases = [
        ('anagram', 'רם וגבוה בעיר מרחצאות בגרמניה', 7, 'הומבורג'),
        ('reversal', 'אבן, להפך', 3, 'נבא'),
        ('hidden', 'שחקן צרפתי מברוקלין', 3, 'ברו'),
    ]
    ok_all = True
    for mech, clue, total_len, gold in cases:
        cands = generate(clue, total_len)
        hit = next((c for c in cands if c['answer'] == gold and c['mechanism'] == mech), None)
        ok = hit is not None
        ok_all &= ok
        print(f'{"PASS" if ok else "FAIL"} [{mech}] "{clue}" ({total_len}) -> expected {gold}: '
              + (f'found, def_span={hit["def_span"]!r} def_text={hit["def_text"]!r}' if hit
                 else f'NOT in {len(cands)} candidates: {[c["answer"] for c in cands][:10]}'))
    print(f'\n{"ALL PASS" if ok_all else "SOME FAILED"}')
    return ok_all

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
    clue = sys.argv[1]
    total_len = int(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    cands = generate(clue, total_len, n)
    if not cands:
        print('(no mechanical candidates — try charade/container/culture by hand)')
        return
    for c in cands:
        print(f"{c['mechanism']:<9} {c['answer']:<12} fodder={c['fodder']!r:<30} "
              f"def_span={c['def_span']:<7} def_text={c['def_text']!r} lex_tier={c['lex_tier']}")

if __name__ == '__main__':
    main()
