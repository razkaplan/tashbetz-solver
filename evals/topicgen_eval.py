#!/usr/bin/env python3
"""Eval for the topic-crossword generator (solver/topicgen.py).

Written BEFORE the generator, and deliberately not sharing its code: every
check here re-derives its own answer from the committed data files, so a bug
in the generator cannot make the eval agree with it. The generator is only
allowed to hand over a puzzle; the verdict is computed from the puzzle.

What a published topic crossword has to be true of:

  GATES (any failure blocks publishing)
    grid          entries match the template's slots; crossing letters agree;
                  no white cell outside every entry
    answers       every answer is a real word: lexicon, topic bank, entity
                  index or curated list. No answer twice in one puzzle
    clues         one clue per entry, >= 6 chars, never contains its own
                  answer, never repeated inside a puzzle, no disambiguation
                  stub, no em-dash (house style), no newspaper clue text
    proofs        every clue carries a machine-checkable proof that holds
    arrows        on a תשחץ, every entry is hosted by a clue cell, one across
                  and one down clue per cell (recomputed here from the grid)
    determinism   same (topic, level, shape, seed) -> byte-identical puzzle

  SCORES (reported, with a floor)
    topicality    share of answers that are actually in the topic's pool,
                  recomputed here rather than believed. A "topic crossword"
                  whose answers are not about the topic is the failure mode
                  this whole eval exists to catch.
    ramp          across levels 1..4 of one topic, the mean difficulty (clue
                  mechanism plus how obscure the answer is, scored here) must
                  not go down. Levels 1 and 2 additionally have to keep 90% of
                  their answers inside the common tier they promise

Usage:
  python3 evals/topicgen_eval.py               # every published board + a probe
  python3 evals/topicgen_eval.py --no-matrix   # published boards only, seconds
  python3 evals/topicgen_eval.py --topic tanach --quick
"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'solver'))

from grid_tools import slots                      # noqa: E402
import grids_topic                                # noqa: E402
import topicgen                                   # noqa: E402

PUBLISHED = 'docs/nosim/puzzles.json'

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

# The theme of a crossword lives in its long entries: a 3-letter filler is not
# what makes a board "about biology". So the floor that matters is on the long
# entries, and the all-entry floor is deliberately low.
#
# The numbers are calibrated to what the banks can actually carry: 80 to 190
# curated terms against boards of 16 to 33 entries, where the topic answers
# also have to cross each other. Measured range at the time of writing is 36%
# to 88% of long entries and 15% to 44% of all entries. The lever for raising
# them is not the search, which is already at the point of diminishing return
# - it is more terms in solver/lex/topics.json.
MIN_TOPICALITY = 0.12        # per puzzle, over all entries
MIN_TOPICALITY_MEAN = 0.20   # across the matrix
MIN_LONG_TOPICALITY = 0.35   # over the entries a solver reads as the theme
LONG_ENTRY = 5               # letters
MIN_COMMON_SHARE = 0.9       # levels 1-2: answers people have actually met
MIN_CLUE_LEN = 6
STUB = ('פירושונים', 'דף פירושונים', 'ראו ערך')

EXPECTED_MECHANISMS = {
    1: {'definition', 'hidden'},
    2: {'definition', 'hidden', 'reversal'},
    3: {'definition', 'hidden', 'reversal', 'anagram'},
    4: {'definition', 'hidden', 'reversal', 'anagram'},
}
# What a clue costs the solver, and what an answer costs. The eval scores
# difficulty itself rather than reading the generator's number, so a level
# that quietly stopped ramping shows up here.
MECH_COST = {'definition': 0.0, 'hidden': 1.0, 'reversal': 1.5, 'anagram': 2.0}


# ---------------------------------------------------------------- own data

def load_reference():
    """Everything the eval needs to judge, loaded independently."""
    lex = {w.strip() for w in open('docs/solve/data/lexicon.txt', encoding='utf-8')
           if w.strip()}
    ents = json.load(open('docs/milon/entities.json', encoding='utf-8'))
    ent_by_norm, ent_descs = {}, {}
    for e in ents:
        ent_by_norm.setdefault(norm(e['t']), e)
        # Several entities can share a spelling once finals are folded, so a
        # definition proof is checked against ALL of that spelling's rows
        # rather than whichever one happens to be first in the file.
        if (e.get('d') or '').strip():
            ent_descs.setdefault(norm(e['t']), set()).add(e['d'].strip())
    banks = {k: v for k, v in json.load(open('solver/lex/topics.json', encoding='utf-8')).items()
             if not k.startswith('_')}
    fillbank = json.load(open('solver/lex/fillbank.json', encoding='utf-8'))
    requested = {}
    if os.path.exists('solver/lex/defs_requested.json'):
        requested = json.load(open('solver/lex/defs_requested.json', encoding='utf-8'))
    curated = {k: v for k, v in json.load(open('solver/lex/defs_curated.json',
                                               encoding='utf-8')).items()
               if not k.startswith('_')}
    # The newspaper clue corpus is gitignored; when a working tree has it, no
    # generated clue may match one of its clues.
    news = set()
    p = 'data/dataset/clues.jsonl'
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            try:
                news.add(re.sub(r'\s+', ' ', json.loads(line).get('clue', '')).strip())
            except ValueError:
                pass
    # the "common" tier the easy levels promise: answers the corpus actually
    # saw in printed puzzles, plus everything we hold a definition for
    attested = set(json.load(open('solver/lex/ambiguities.json', encoding='utf-8')))
    crosswordese = {norm(k) for k in
                    json.load(open('solver/crosswordese.json', encoding='utf-8'))}
    defined = {norm(w) for w in fillbank}
    defined |= {norm(w) for c in curated.values() for w in c.get('items', {})}
    defined |= {n for n, e in ent_by_norm.items() if (e.get('d') or '').strip()}
    return {'lex': lex, 'ents': ents, 'ent_by_norm': ent_by_norm, 'ent_descs': ent_descs,
            'fillbank': fillbank, 'requested': requested,
            'banks': banks, 'curated': curated, 'news': news,
            'common': (attested | crosswordese | defined), 'defined': defined}


def topic_pool(ref, topic):
    """The set of normalized answers the eval considers on-topic.

    Recomputed from the committed data, NOT taken from the generator: the
    bank's own terms, the entity rows the topic's entity queries select, and
    any curated list the topic names.
    """
    bank = ref['banks'].get(topic)
    pool = set()
    if not bank:
        return pool
    for term in bank.get('terms', {}):
        pool.add(norm(term))
    for q in bank.get('entities', []):
        cat, rx = q.get('cat'), q.get('rx')
        for e in ref['ents']:
            if cat and e['c'] != cat:
                continue
            if rx and not re.search(rx, e.get('d') or ''):
                continue
            pool.add(norm(e['t']))
    for key in bank.get('curated', []):
        pool |= {norm(w) for w in ref['curated'].get(key, {}).get('items', {})}
    return {w for w in pool if len(w) >= 2}


# ---------------------------------------------------------------- checks

def check_proof(entry, ref):
    """Re-verify the clue's proof from the data, not from the generator."""
    pr = entry.get('proof') or {}
    a = entry['answer']
    t = pr.get('type')
    if t == 'definition':
        # the clue text must be the description the source actually carries
        src, key = pr.get('source'), pr.get('key')
        if src == 'bank':
            bank = ref['banks'].get(pr.get('topic'), {})
            got = bank.get('terms', {}).get(key)
        elif src == 'entity':
            got = ref['ent_descs'].get(norm(key), set())
        elif src == 'curated':
            got = ref['curated'].get(pr.get('list'), {}).get('items', {}).get(key)
        elif src == 'fill':
            got = ref['fillbank'].get(key)
        elif src == 'requested':
            got = None
            for spec in ref['requested'].values():
                if spec.get('phrase') == pr.get('phrase'):
                    got = (spec.get('items') or {}).get(key)
                    break
        else:
            return f'unknown definition source {src!r}'
        if not got:
            return f'definition proof points at {src}:{key!r}, which has no description'
        if norm(key) != a:
            return f'definition proof key {key!r} is not the answer'
        texts = got if isinstance(got, set) else {got}
        if entry['clue'].strip() not in {t.strip() for t in texts}:
            return 'clue text does not match the description it cites'
        return None
    if t == 'reversal':
        if pr.get('from', '')[::-1] != a:
            return 'reversal proof does not reverse to the answer'
        if pr['from'] not in ref['lex']:
            return f"reversal source {pr['from']!r} is not a word"
        return None
    if t == 'anagram':
        if sorted(pr.get('from', '')) != sorted(a):
            return 'anagram proof letters do not match'
        if pr['from'] == a:
            return 'anagram of itself'
        if pr['from'] not in ref['lex']:
            return f"anagram source {pr['from']!r} is not a word"
        return None
    if t == 'hidden':
        c, at = pr.get('carrier', ''), pr.get('at', -1)
        if c[at:at + len(a)] != a:
            return 'answer is not at the stated position in the carrier'
        if c == a or c not in ref['lex']:
            return f'carrier {c!r} is not a longer word'
        return None
    return f'unknown proof type {t!r}'


def check_puzzle(p, ref, pool):
    """Returns (problems, stats) for one generated puzzle."""
    bad = []
    grid = p['grid']
    sl = slots(grid)
    got = {(e['num'], e['dir']): e for e in p['entries']}

    if set(got) != set(sl):
        bad.append('entries do not match the template slots')
    else:
        board = {}
        for key, e in got.items():
            cells = sl[key]
            if len(e['answer']) != len(cells):
                bad.append(f'{key}: answer length {len(e["answer"])} != slot {len(cells)}')
                continue
            for c, ch in zip(cells, e['answer']):
                if c in board and board[c] != ch:
                    bad.append(f'{key}: crossing conflict at {c}')
                board[c] = ch
        white = sum(row.count('.') for row in grid)
        if len(board) != white:
            bad.append(f'{white - len(board)} white cells belong to no entry')

    if p['kind'] == 'arrow':
        try:
            hosts = grids_topic.arrow_hosts(grid)
        except AssertionError as e:
            bad.append(f'arrow hosting: {e}')
            hosts = {}
        for key, h in hosts.items():
            declared = p.get('hosts', {}).get(f'{key[0]}{key[1]}')
            if declared is not None and tuple(declared) != tuple(h):
                bad.append(f'{key}: declared host {declared} != {list(h)}')

    seen_ans, seen_clue = set(), {}
    topical = long_total = long_topical = common = 0
    cost = 0.0
    mechs = {}
    for key, e in sorted(got.items()):
        a = e['answer']
        if a in seen_ans:
            bad.append(f'{key}: answer {a!r} appears twice')
        seen_ans.add(a)
        if a not in ref['lex'] and a not in pool and a not in ref['ent_by_norm']:
            bad.append(f'{key}: {a!r} is not a word we can defend')
        clue = (e.get('clue') or '').strip()
        if len(clue) < MIN_CLUE_LEN:
            bad.append(f'{key}: clue too short: {clue!r}')
        if any(s in clue for s in STUB):
            bad.append(f'{key}: clue is a disambiguation stub')
        # A hidden clue names the carrier the answer sits inside, so it
        # contains the answer by construction; that is the mechanism, and the
        # proof checks it. Every other clue type giving its answer away is a
        # broken clue.
        if e.get('mechanism') != 'hidden' and norm(a) and norm(a) in norm(clue):
            bad.append(f'{key}: clue gives away its own answer')
        if '—' in clue or '–' in clue:
            bad.append(f'{key}: em-dash in published text')
        if clue in seen_clue:
            bad.append(f'{key}: clue repeats {seen_clue[clue]}')
        seen_clue[clue] = key
        if clue in ref['news']:
            bad.append(f'{key}: clue matches a newspaper clue')
        err = check_proof(e, ref)
        if err:
            bad.append(f'{key}: {err}')
        allowed = EXPECTED_MECHANISMS[p['level']]
        if e.get('mechanism') not in allowed:
            bad.append(f"{key}: mechanism {e.get('mechanism')!r} not allowed at level {p['level']}")
        mechs[e.get('mechanism')] = mechs.get(e.get('mechanism'), 0) + 1
        if a in pool:
            topical += 1
        if len(a) >= LONG_ENTRY:
            long_total += 1
            long_topical += a in pool
        if a in pool or a in ref['common']:
            common += 1
        cost += (MECH_COST.get(e.get('mechanism'), 2.0)
                 + (0.0 if a in ref['common'] else (0.4 if a in ref['defined'] else 1.0)))

    n = max(1, len(got))
    long_topicality = long_topical / long_total if long_total else 1.0
    if long_topicality < MIN_LONG_TOPICALITY:
        bad.append(f'only {long_topicality:.0%} of the {LONG_ENTRY}+ letter entries '
                   f'are on topic (floor {MIN_LONG_TOPICALITY:.0%})')
    if p['level'] <= 2 and common / n < MIN_COMMON_SHARE:
        bad.append(f'level {p["level"]} promises common answers but only '
                   f'{common / n:.0%} are (floor {MIN_COMMON_SHARE:.0%})')
    stats = {'entries': len(got), 'topical': topical, 'topicality': topical / n,
             'long_topicality': long_topicality, 'common_share': common / n,
             'difficulty': cost / n,
             'wordplay': 1 - mechs.get('definition', 0) / n, 'mechanisms': mechs}
    return bad, stats


# ---------------------------------------------------------------- runner

def run(topics=None, quick=False, matrix=True):
    """Two passes, because they answer different questions.

    PUBLISHED  every board in docs/nosim/puzzles.json, which is what readers
               actually get. No generation, so it is fast enough to run on
               every change.
    MATRIX     a small generation run, which is the only way to check that the
               generator is deterministic and that a fresh board still clears
               the gates. Generating the full 10x4x4 matrix here would take
               hours and would only re-measure what the published set already
               shows.
    """
    ref = load_reference()
    rows, failures = [], []
    pools = {}

    def pool_for(topic):
        if topic not in pools:
            pools[topic] = topic_pool(ref, topic)
        return pools[topic]

    def judge(p, tag, extra=()):
        pool = pool_for(p['topic'])
        if not pool:
            failures.append(f'{tag}: the eval finds no topic pool at all')
            return None
        bad, stats = check_puzzle(p, ref, pool)
        bad = list(bad) + list(extra)
        if stats['topicality'] < MIN_TOPICALITY:
            bad.append(f"topicality {stats['topicality']:.0%} below the "
                       f'{MIN_TOPICALITY:.0%} floor')
        rows.append({'source': tag.split(' ')[0], 'topic': p['topic'],
                     'level': p['level'], 'shape': p['shape'],
                     'ok': not bad, 'problems': bad, **stats})
        failures.extend(f'{tag}: {b}' for b in bad)
        return stats

    published = []
    if os.path.exists(PUBLISHED):
        published = json.load(open(PUBLISHED, encoding='utf-8'))
    if not published:
        failures.append(f'{PUBLISHED} is missing or empty: nothing is published')
    by_topic = {}
    for p in published:
        if topics and p['topic'] not in topics:
            continue
        stats = judge(p, f"published {p['topic']} L{p['level']} {p['shape']}")
        if stats:
            by_topic.setdefault(p['topic'], {})[p['level']] = stats['difficulty']

    # the ramp is a property of a subject's four boards, not of one board
    for topic, levels in by_topic.items():
        seq = [levels[L] for L in sorted(levels)]
        if any(b < a - 1e-9 for a, b in zip(seq, seq[1:])):
            failures.append(f'{topic}: difficulty falls as the level rises: '
                            + ', '.join(f'{x:.2f}' for x in seq))

    if matrix:
        bank_names = [t for t in ref['banks']]
        probe = (topics or bank_names)[:1 if quick else 2]
        for topic in probe:
            for level in (1, 2, 3, 4):
                # Determinism is a property of one search, so it is checked on
                # generate(); the gates are checked on generate_best(), which
                # is what actually produces a published board. Judging a
                # single-seed board against the published floors would be
                # measuring something nobody ships.
                one = topicgen.generate(topic, level, seed=4242)
                again = topicgen.generate(topic, level, seed=4242)
                if json.dumps(one, sort_keys=True, ensure_ascii=False) != \
                   json.dumps(again, sort_keys=True, ensure_ascii=False):
                    failures.append(f'matrix {topic} L{level}: '
                                    f'not deterministic for a fixed seed')
                p = topicgen.generate_best(topic, level)
                if not p:
                    failures.append(f'matrix {topic} L{level}: generator returned nothing')
                    continue
                judge(p, f'matrix {topic} L{level} {p["shape"]}')

    done = [r for r in rows if r.get('entries')]
    mean_topicality = sum(r['topicality'] for r in done) / max(1, len(done))
    if done and mean_topicality < MIN_TOPICALITY_MEAN:
        failures.append(f'mean topicality {mean_topicality:.0%} below the '
                        f'{MIN_TOPICALITY_MEAN:.0%} floor')
    return {'when': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
            'puzzles': len(rows), 'passed': sum(1 for r in rows if r['ok']),
            'mean_topicality': round(mean_topicality, 3),
            'failures': failures, 'rows': rows}


def main():
    args = sys.argv[1:]
    quick = '--quick' in args
    topics = None
    if '--topic' in args:
        topics = [args[args.index('--topic') + 1]]
    res = run(topics, quick, matrix='--no-matrix' not in args)
    print(f"boards checked: {res['puzzles']}  passed: {res['passed']}  "
          f"mean topicality: {res['mean_topicality']:.0%}")
    by_level = {}
    for r in res['rows']:
        if r.get('entries'):
            by_level.setdefault(r['level'], []).append(r)
    for L in sorted(by_level):
        rs = by_level[L]
        print(f'  level {L}: {sum(1 for r in rs if r["ok"])}/{len(rs)} ok, '
              f'topicality {sum(r["topicality"] for r in rs) / len(rs):.0%} '
              f'(long {sum(r["long_topicality"] for r in rs) / len(rs):.0%}), '
              f'difficulty {sum(r["difficulty"] for r in rs) / len(rs):.2f}, '
              f'common {sum(r["common_share"] for r in rs) / len(rs):.0%}')
    if res['failures']:
        print(f"\nFAILURES ({len(res['failures'])}):")
        for f in res['failures'][:40]:
            print('  ', f)
        if len(res['failures']) > 40:
            print(f"   ... and {len(res['failures']) - 40} more")
    out = f"evals/runs/topicgen/{dt.date.today().isoformat()}.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nwrote', out)
    return 1 if res['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
