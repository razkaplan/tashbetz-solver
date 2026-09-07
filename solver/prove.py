#!/usr/bin/env python3
"""Executable wordplay proofs — a mechanical verifier for Hebrew cryptic answers.

Adapted from the formalise-and-verify approach in "A Reasoning-Based Approach to
Cryptic Crossword Clue Solving" (Cryptonite SOTA), which turns informal wordplay
into Python assertions and treats an answer as *proved* only when the program runs
with zero assertion failures.

Why this matters here: every previous verifier was an LLM judging plausibility, and
plausibility is exactly what kept re-committing wrong answers (one slot was answered
wrongly three times, each with a fresh convincing justification). An assertion either
executes or it does not. It cannot be talked into agreeing.

The DSL is grounded in THIS corpus rather than generic wordlists:
  is_synonym / means      -> substitutions.json (3,141 equivalences mined from the
                             setters' own crowd explanations) + the lexicon
  is_word                 -> hspell + corpus answers + culture entities (141k)
  is_anagram / reversal / container / hidden / concat -> pure string mechanics

Usage as a library (what a solver writes):
    from prove import *
    def proof():
        assert is_anagram('משפרחיי', 'שיפרחימ')      # letters check out
        assert means('מוניאמריליו', 'anagram-signal')  # indicator accounted for
        assert concat('שי', 'פרחים') == 'שיפרחימ'
    check(proof)

CLI:
  python3 solver/prove.py selftest
  python3 solver/prove.py check '<python proof body>' --answer <answer>
"""
import json, os, re, sys, ast
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

# ---------- grounded resources ----------
_LEX = None
_SUB = None

def lex():
    global _LEX
    if _LEX is None:
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            sys.path.insert(0, HERE)
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
        p = os.path.join(HERE, 'lex/substitutions.json')
        _SUB = json.load(open(p)) if os.path.exists(p) else {'fwd': {}, 'rev': {}}
    return _SUB

# ---------- DSL ----------
class ProofError(AssertionError):
    """Carries a hint about *why* a step failed, so the solver can repair it."""

def is_word(w):
    """Is this a real Hebrew word / name / corpus answer?"""
    return norm(w) in lex()

def is_anagram(fodder, answer):
    """Do the letters of `fodder` rearrange to exactly `answer`?"""
    a, b = norm(fodder), norm(answer)
    if Counter(a) != Counter(b):
        raise ProofError(
            f"is_anagram: letters differ. fodder '{a}' has {dict(Counter(a) - Counter(b)) or '{}'} "
            f"extra, answer '{b}' has {dict(Counter(b) - Counter(a)) or '{}'} extra")
    return True

def is_reversal(src, answer):
    a, b = norm(src), norm(answer)
    if a[::-1] != b:
        raise ProofError(f"is_reversal: '{a}' reversed is '{a[::-1]}', not '{b}'")
    return True

def is_container(outer, inner, answer):
    """outer split around inner: e.g. קרים + תן -> קרתנים."""
    o, i, ans = norm(outer), norm(inner), norm(answer)
    for k in range(1, len(o)):
        if o[:k] + i + o[k:] == ans:
            return True
    raise ProofError(f"is_container: inserting '{i}' anywhere in '{o}' never yields '{ans}'")

def is_hidden(text, answer):
    t, a = norm(text), norm(answer)
    if a not in t:
        raise ProofError(f"is_hidden: '{a}' is not a contiguous run inside '{t}'")
    return True

# Consonant-class folding for the homophone device (נשמע) — mirrors candidates.py's
# PHON_FOLD/phon(), duplicated rather than imported so this file stays self-contained
# (same discipline candidates.py's own _destem() duplication follows). Grounded in
# indicators.json's own crowd-mined homophone entry: ק/כ/ח, ט/ת, ס/ש, א/ע swap freely
# in undotted Hebrew. Does not model vowel-letter (ו/י) flexibility — disclosed, not
# silently assumed away.
PHON_FOLD = str.maketrans('עחקטש', 'אככתס')

def is_homophone(fodder, answer):
    """Does `fodder`, read by SOUND rather than by spelling, give `answer`? Grounded in
    the same consonant-class folding candidates.py's homophone_candidates() uses to
    generate the hypothesis in the first place, so a live solve pass can PROVE one."""
    a, b = norm(fodder), norm(answer)
    if a.translate(PHON_FOLD) != b.translate(PHON_FOLD):
        raise ProofError(
            f"is_homophone: '{a}' and '{b}' do not fold to the same phonetic key "
            f"('{a.translate(PHON_FOLD)}' vs '{b.translate(PHON_FOLD)}')")
    return True

def means(phrase, target):
    """Grounded synonym/substitution: is `target` a recorded reading of `phrase`?
    Uses the setters' own vocabulary, which is stricter and more honest than a
    generic thesaurus."""
    p, t = norm(phrase), norm(target)
    s = subs()
    for b, _ in s['fwd'].get(p, []):
        if b == t:
            return True
    for b, _ in s['rev'].get(p, []):
        if b == t:
            return True
    if p == t:
        return True
    raise ProofError(
        f"means: no recorded substitution '{p}' ~ '{t}'. "
        f"known for '{p}': {[b for b, _ in s['fwd'].get(p, [])][:6] or 'none'}")

def concat(*parts):
    return ''.join(norm(p) for p in parts)

def has_length(answer, *enum):
    """Enumeration check: word lengths must match the printed enum exactly."""
    a = norm(answer)
    if sum(enum) != len(a):
        raise ProofError(f"has_length: enum {list(enum)} sums to {sum(enum)} but '{a}' has {len(a)}")
    return True

def word_order(answer, *words):
    """The words, in this order, must spell the answer. Catches right-letters-wrong-order,
    which has been the most persistent error class in this project."""
    a = norm(answer)
    joined = ''.join(norm(w) for w in words)
    if joined != a:
        raise ProofError(
            f"word_order: {[norm(w) for w in words]} concatenates to '{joined}', not '{a}'. "
            f"Check the ORDER of the words.")
    return True

DSL = dict(is_word=is_word, is_anagram=is_anagram, is_reversal=is_reversal,
           is_container=is_container, is_hidden=is_hidden, is_homophone=is_homophone,
           means=means, concat=concat, has_length=has_length, word_order=word_order)

# ---------- verifier ----------
def check(proof_src, answer=None, verbose=True):
    """Execute a proof body line by line; report the first failing assertion with a hint."""
    env = dict(DSL)
    lines = [l for l in proof_src.strip().splitlines() if l.strip() and not l.strip().startswith('#')]
    for n, line in enumerate(lines, 1):
        try:
            exec(line.strip(), env)
        except ProofError as e:
            if verbose:
                print(f'FAIL line {n}: {line.strip()}\n  hint: {e}')
            return False, f'line {n}: {e}'
        except AssertionError:
            if verbose:
                print(f'FAIL line {n}: {line.strip()}\n  hint: assertion evaluated false')
            return False, f'line {n}: assertion false'
        except Exception as e:
            if verbose:
                print(f'ERROR line {n}: {line.strip()}\n  {type(e).__name__}: {e}')
            return False, f'line {n}: {type(e).__name__}: {e}'
    if verbose:
        print(f'PROVED ({len(lines)} assertions passed)' + (f' -> {answer}' if answer else ''))
    return True, 'proved'

def selftest():
    print('--- a TRUE proof (7a, the anagram whose word order was wrong) ---')
    ok, _ = check("""
assert is_anagram('משפר חיי', 'ישפרחימ')
assert word_order('ישפרחימ', 'יש', 'פרחים')
assert has_length('ישפרחימ', 2, 5)
""", 'ישפרחימ')
    print(f'  => {ok} (expected True)\n')

    print('--- the WRONG word order the solver committed at 0.95 ---')
    ok2, _ = check("""
assert is_anagram('משפר חיי', 'שיפרחימ')
assert word_order('שיפרחימ', 'יש', 'פרחים')
""", 'שיפרחימ')
    print(f'  => {ok2} (expected False — this is the error we could not catch before)\n')

    print('--- a container proof (11a) ---')
    ok3, _ = check("""
assert is_container('קרים', 'תן', 'קרתנימ')
""", 'קרתנימ')
    print(f'  => {ok3}\n')

    print('--- an UNGROUNDED synonym claim (the 4d failure mode) ---')
    ok4, _ = check("""
assert means('ההרמות', 'תרומות')
""")
    print(f'  => {ok4} (expected False — invented synonyms are now rejected)')

    print('\n--- a homophone proof (ק/כ swap: קר "sounds like" כר) ---')
    ok5, _ = check("""
assert is_homophone('קר', 'כר')
""", 'כר')
    print(f'  => {ok5} (expected True)')

    print('--- a FALSE homophone claim (letters outside any recorded swap class) ---')
    ok6, _ = check("""
assert is_homophone('קר', 'גל')
""")
    print(f'  => {ok6} (expected False)')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        selftest()
    elif len(sys.argv) > 2 and sys.argv[1] == 'check':
        ans = sys.argv[sys.argv.index('--answer') + 1] if '--answer' in sys.argv else None
        ok, msg = check(sys.argv[2], ans)
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
