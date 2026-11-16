#!/usr/bin/env python3
"""Hebrew lexicon tools for the solver — pattern match, anagram, contains.

Wordlist = hspell (129k headwords) + hebrew-words-db (67k, inflected noun/verb/adjective
forms hspell doesn't enumerate) + private_defs (other crosswords' attested answers) + all
corpus answers (crosswordese/names the dict lacks), all normalized to final-form-folded,
space-free Hebrew letters.

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

def held_out_answers(clues_path='data/dataset/clues.jsonl', by_date_dir='data/answers/by_date'):
    """Normalized answers belonging to dev/eval puzzles — these MUST NOT enter the lexicon,
    or a pattern lookup silently hands the solver the gold answer (measured: this inflated
    a run to 96%). Train-split answers are legitimate priors.

    Blocks every gold answer for a held-out puzzle DATE, not just clues that happen to have
    a transcribed row in clues.jsonl. A puzzle can be dev/eval with only SOME of its clues
    transcribed — e.g. an image missing across 1-13 (documented in DAILY.md, confirmed
    across 4 different weeks). Before this fix, an untranscribed slot's gold answer stayed
    fully exposed in the corpus/culture lexicon tiers, because the old block set was built
    by iterating clues.jsonl rows, which only exist for transcribed clues — a real leak
    vector any future run that pattern-matches an untranscribed slot's crossing letters
    would have walked straight into (flagged but not fixed in the 2026-08-16 log entry).
    Once a puzzle date is known to be dev/eval (from any one transcribed row), every answer
    in that puzzle's full answer key (`data/answers/by_date/<date>.json`, independent of
    transcription) is blocked, closing the gap without needing the grid at all."""
    out = set()
    dates = set()
    if os.path.exists(clues_path):
        for line in open(clues_path):
            r = json.loads(line)
            if r.get('split') in ('dev', 'eval'):
                dates.add(r['puzzle_date'])
                if r.get('answer_raw'):
                    out.add(norm(r['answer_raw']))
    for d in dates:
        af = os.path.join(by_date_dir, f'{d}.json')
        if not os.path.exists(af):
            continue
        for c in json.load(open(af)).get('clues', []):
            w = c.get('answer')
            if w:
                out.add(norm(w))
    return out


def load(clues_path='data/dataset/clues.jsonl', by_date_dir='data/answers/by_date',
         include_private_defs=True, private_defs_glob='data/answers/private_defs/*.jsonl',
         include_hwdb=True, hwdb_path=None):
    """WHY include_private_defs (added 2026-09-19): candidates.py's own
    `lexicon_coverage_eval` diagnostic (2026-09-15/16) measured that only 28.6%/32.1%
    of two dev puzzles' gold answers are members of THIS function's output at all —
    a ceiling every mechanical generator in candidates.py (anagram/hidden/reversal/
    homograph/container/...) inherits directly, since none of them can ever propose a
    string that is not already a lexicon member, no matter how correct its fodder is
    (measured concretely: 8A's anagram fodder on 2026-06-05 had the exact right letter
    multiset for gold `גדישמני`, but `anagram_candidates` still could not propose it,
    because `גדישמני` itself was not a lex() member). Wiring in a corpus-mined "prefix
    stripping" fix for this was tried and deliberately NOT shipped (2026-09-16, see
    DAILY.md) because short stripped stems are coincidence-prone, not genuine recoveries.
    This source is different in kind: `data/answers/private_defs/` (scraper/crawl_defs.py,
    note.co.il + pitaronfree/מורדו, already crawled and used by retrieve_defs.py's BM25
    index as RETRIEVAL documents) is a large, independently-sourced list of definition->
    ANSWER pairs from OTHER crosswords. Every entry on the answer side is, by construction
    of its source, an attested real Hebrew crossword answer (word, name, or phrase) —
    not a guessed morphological form — so adding it as a LEXICON MEMBERSHIP source (not
    just a retrieval document) needs no invented rule the way prefix-stripping did.

    Held-out safety: filtered through the SAME BLOCK set as the corpus/culture tiers
    below, unlike retrieve_defs.py's build_index() (which deliberately does NOT held-out
    filter private_defs, on the reasoning that it is independent external knowledge, "like
    a crossword dictionary," and only ranks as ONE of many candidates a human/proof-gate
    still has to verify). This function feeds `is_word()`-style boolean membership checks
    used by every mechanical generator — a false membership there would silently
    manufacture a candidate that can pass the proof gate, a stronger leak risk than
    appearing in a ranked retrieval list, so it gets the stricter, not the looser, of the
    project's two existing disciplines.

    WHY include_hwdb (added 2026-09-20): 2026-09-19's private_defs tier measured a clean
    negative (0/38 overlap on 2 puzzles) because it attacks the coverage gap from the
    ATTESTED-ANSWER side (other crosswords' answers) — this setter's specific idioms
    simply weren't among them. RESEARCH.md's 2026-09-16 entry independently flagged the
    other side of the same gap and left it explicitly untested: `hspell_simple.txt`
    (bootstrap.sh's only general dictionary source) is a HEADWORD list, not a full-form
    one — it does not enumerate most Hebrew productive prefix forms (confirmed directly:
    כן is a headword, וכן is not) and, per that research note, likely under-enumerates
    SUFFIXED forms (plurals, construct states, possessive suffixes) even more, since
    those inflect far more combinations per headword than prefixes do. Prefix-stripping
    was tried and deliberately not shipped as a lexicon fix (short residual stems are
    coincidence-prone); a full-form Hebrew lexicon needs no such invented rule because
    each inflected form is already a real, independently-listed headword-equivalent, not
    a guess. `github.com/roni5604/hebrew-words-db` (CC0 public domain, confirmed real and
    fetchable this run — see RESEARCH.md's 2026-09-20 entry) is exactly this: 67,008
    words built from noun/verb/adjective inflection tables (plurals, verb conjugations
    across tenses/persons, adjective gender/number agreement), not just headwords.

    Treated like hspell (the SAME general-dictionary tier, priority 1, NOT held-out
    filtered) rather than like private_defs/culture: hwdb is not derived from any
    newspaper crossword or from this project's own puzzles, so an ordinary word it
    contributes that happens to coincide with a held-out gold answer is the same
    legitimate case RESULTS.md's own INTEGRITY FINDING already ruled acceptable for
    hspell ("ordinary dictionary words that happen to be answers... legitimately
    remain, as they would in any real solver's dictionary") — filtering it would treat
    a general-purpose wordlist as if it were corpus-derived, which it is not."""
    words = {}  # word -> priority (3 culture, 2 corpus/private_defs, 1 dict/hwdb)
    BLOCK = held_out_answers(clues_path, by_date_dir)
    hp = os.path.join(HERE, 'lex/hspell.txt')
    if os.path.exists(hp):
        for line in open(hp, encoding='utf-8'):
            w = norm(line)
            if w:
                words.setdefault(w, 1)
    if include_hwdb:
        wp = hwdb_path or os.path.join(HERE, 'lex/hwdb.txt')
        if os.path.exists(wp):
            for line in open(wp, encoding='utf-8'):
                w = norm(line)
                if w:
                    words.setdefault(w, 1)
    # corpus answers (high priority — names, slang, multiword grid entries)
    for pat in ['data/answers/answers_parsed.json']:
        if os.path.exists(pat):
            for p in json.load(open(pat)):
                for c in p['clues']:
                    w = norm(c.get('answer'))
                    if w and w not in BLOCK:
                        words[w] = 2
    for f in glob.glob('data/answers/extra/*.json'):
        d = json.load(open(f))
        for p in d.get('puzzles', []):
            for c in p['clues']:
                w = norm(c.get('answer'))
                if w and w not in BLOCK:
                    words[w] = 2
    # private definitions corpus (note.co.il + מורדו): independently-sourced crossword
    # answers, gitignored, rebuilt fresh by scraper/crawl_defs.py — see the docstring
    # above for why this belongs here now. Same priority tier as our own corpus answers.
    if include_private_defs:
        for f in glob.glob(private_defs_glob):
            for line in open(f, encoding='utf-8'):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                for a in r.get('answers', []):
                    w = norm(a)
                    if w and w not in BLOCK:
                        words[w] = 2
    # culture entities (song titles, artists, politicians, places) from he-wikipedia.
    # Highest priority: these are exactly the answers the solver cannot invent.
    cp = os.path.join(HERE, 'lex/culture.json')
    if os.path.exists(cp):
        for kind, items in json.load(open(cp)).items():
            for t in items:
                w = norm(t)
                if w and w not in BLOCK:
                    words[w] = 3
    return words

def rank(words, matches):
    return sorted(matches, key=lambda w: (-words[w], len(w), w))[:60]

def selftest():
    """Unit-level checks on synthetic fixture files in a temp dir — never touches real
    puzzle data, same discipline candidates.py/defspan.py enforce for their own selftests."""
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

        block = held_out_answers(clues_p, by_date_dir)
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

        print('--- a held-out date with no by_date file at all does not crash ---')
        block2 = held_out_answers(clues_p, os.path.join(tmp, 'nonexistent'))
        found = norm('שלום') in block2
        print(f'  falls back to dataset-row blocking, no crash: {found} (expected True)')
        ok &= found

        print('--- load(): private_defs answers enter the lexicon, held-out ones do not ---')
        # Deliberately unreal strings (a repeated letter 4-5x is not a Hebrew headword)
        # so this test is not accidentally satisfied by hspell/corpus/culture already
        # containing the word for an unrelated reason — isolates what THIS source does.
        safe_word = 'ממממ'      # only ever sourced from the private_defs fixture below
        leak_word = 'ששששש'    # ALSO this fixture's own dev-puzzle gold answer (BLOCK)
        with open(clues_p, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'puzzle_date': '2099-01-01', 'clue_number': 2,
                                 'direction': 'across', 'split': 'dev',
                                 'answer_raw': leak_word}, ensure_ascii=False) + '\n')
        pd_dir = os.path.join(tmp, 'private_defs')
        os.makedirs(pd_dir)
        with open(os.path.join(pd_dir, 'fixture.jsonl'), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'definition': 'fixture leak probe', 'answers': [leak_word]},
                                ensure_ascii=False) + '\n')
            f.write(json.dumps({'definition': 'fixture safe probe', 'answers': [safe_word]},
                                ensure_ascii=False) + '\n')
        words_on = load(clues_p, by_date_dir, include_private_defs=True,
                         private_defs_glob=os.path.join(pd_dir, '*.jsonl'))
        safe_in = safe_word in words_on
        print(f'  safe private_defs answer enters lex(): {safe_in} (expected True)')
        ok &= safe_in
        leak_blocked = leak_word not in words_on
        print(f"  this fixture's own held-out gold stays OUT even though a private_defs "
              f'doc names it: {leak_blocked} (expected True)')
        ok &= leak_blocked

        words_off = load(clues_p, by_date_dir, include_private_defs=False,
                          private_defs_glob=os.path.join(pd_dir, '*.jsonl'))
        toggle_off = safe_word not in words_off
        print(f'  include_private_defs=False excludes it: {toggle_off} (expected True)')
        ok &= toggle_off

        print('--- load(): hwdb answers enter the lexicon at dict priority, NOT held-out '
              'filtered (treated like hspell, see docstring) ---')
        hwdb_word = 'קקקקק'      # only ever sourced from the hwdb fixture below
        hwdb_leak = 'צצצצצ'      # this fixture's own dev-puzzle gold answer (BLOCK)
        with open(clues_p, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'puzzle_date': '2099-01-01', 'clue_number': 3,
                                 'direction': 'across', 'split': 'dev',
                                 'answer_raw': hwdb_leak}, ensure_ascii=False) + '\n')
        hwdb_p = os.path.join(tmp, 'hwdb.txt')
        with open(hwdb_p, 'w', encoding='utf-8') as f:
            f.write(hwdb_word + '\n' + hwdb_leak + '\n')
        words_hwdb_on = load(clues_p, by_date_dir, include_private_defs=False,
                              private_defs_glob=os.path.join(pd_dir, '*.jsonl'),
                              include_hwdb=True, hwdb_path=hwdb_p)
        hwdb_in = hwdb_word in words_hwdb_on
        print(f'  hwdb word enters lex() at priority 1: '
              f'{hwdb_in and words_hwdb_on.get(hwdb_word) == 1} (expected True)')
        ok &= hwdb_in and words_hwdb_on.get(hwdb_word) == 1
        # NOT held-out filtered by design (treated as a general dictionary, like hspell —
        # see the load() docstring for why this differs from private_defs/culture).
        hwdb_unfiltered = hwdb_leak in words_hwdb_on
        print(f'  hwdb is NOT held-out filtered (an ordinary-word coincidence, same rule '
              f'as hspell): {hwdb_unfiltered} (expected True)')
        ok &= hwdb_unfiltered

        words_hwdb_off = load(clues_p, by_date_dir, include_private_defs=False,
                               private_defs_glob=os.path.join(pd_dir, '*.jsonl'),
                               include_hwdb=False, hwdb_path=hwdb_p)
        hwdb_toggle_off = hwdb_word not in words_hwdb_off
        print(f'  include_hwdb=False excludes it: {hwdb_toggle_off} (expected True)')
        ok &= hwdb_toggle_off
    finally:
        shutil.rmtree(tmp)

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        sys.exit(0 if selftest() else 1)
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
