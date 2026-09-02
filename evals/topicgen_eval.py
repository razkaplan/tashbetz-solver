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
    ramp          across levels 1..4 of one topic, the WORK (mean clue
                  difficulty times entries) does not fall - the mean alone
                  cannot order boards of different sizes. Was: the mean difficulty (clue
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
# entries, and the all-entry floor is deliberately low - on a 26-entry
# arrowword an 85-term bank tops out near four on-topic answers however long
# the search runs, and pretending otherwise only blocks rebuilds.
#
# The numbers are calibrated to what the banks can actually carry: 80 to 190
# curated terms against boards of 16 to 33 entries, where the topic answers
# also have to cross each other. Measured range at the time of writing is 36%
# to 88% of long entries and 15% to 44% of all entries. The lever for raising
# them is not the search, which is already at the point of diminishing return
# - it is more terms in solver/lex/topics.json.
MIN_TOPICALITY = 0.10        # per puzzle, over all entries
MIN_TOPICALITY_MEAN = 0.20   # across the matrix
MIN_LONG_TOPICALITY = 0.35   # over the entries a solver reads as the theme
LONG_ENTRY = 5               # letters
MIN_COMMON_SHARE = 0.9       # levels 1-2: answers people have actually met
MIN_CLUE_LEN = 6
STUB = ('פירושונים', 'דף פירושונים', 'ראו ערך')
# see solver/topicgen.py: tails that identify nothing
EMPTY_TAIL = {'בישראל', 'ישראלי', 'ישראלית', 'מקראי', 'מקראית', 'מיקראית',
              'מקראיות', 'מקומית', 'מקומי', 'עתיק', 'עתיקה', 'קדום', 'קדומה',
              # a category noun plus one of these is a label, not a clue
              'משונעים', 'לשעבר', 'ידוע', 'מפורסם', 'כללי',
              'בתנ"ך', 'בתנך', 'במקרא', 'בתורה'}
CATEGORY_WORD = {'דמות', 'דמויות', 'יישוב', 'עיר', 'כפר', 'מושב', 'קיבוץ',
                 'נהר', 'הר', 'מקום', 'אתר', 'שכונה', 'מועצה', 'חפצים',
                 'ההר', 'העיר', 'הכפר', 'היישוב', 'הנהר'}

# A level is a CEILING on mean difficulty, not a list of permitted mechanisms
# and not a floor. A floor would be a demand that easy boards be made harder
# than they need to be; the ramp is checked separately, across a subject's
# four boards, where it belongs.
# The ceiling stops a level being absurd. What makes a level MEAN something
# is the ramp below - each of a subject's boards harder than the last - so
# the ceilings are deliberately loose rather than fitted to a sample.
LEVEL_CEILING = {1: 1.25, 2: 1.7, 3: 2.5, 4: 9.9}
KNOWN_MECHANISMS = {'definition', 'hidden', 'reversal', 'anagram'}
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
    # the same two files solver/topicgen.py merges: the curated banks and the
    # weekly news bank. Reading only the first left every news board with no
    # pool, so the gate could not judge the one board that ships unattended.
    banks = {}
    for fname in ('solver/lex/topics.json', 'solver/lex/topics_news.json'):
        if os.path.exists(fname):
            banks.update({k: v for k, v in json.load(open(fname, encoding='utf-8')).items()
                          if not k.startswith('_')})
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
    dictwords = set()
    if os.path.exists('solver/lex/dictwords.txt'):
        dictwords = {w.strip() for w in open('solver/lex/dictwords.txt', encoding='utf-8')
                     if w.strip()}
    # The three difficulty tiers, rebuilt here from the same files the
    # generator reads but independently of it. They had drifted: 'defined' was
    # a SUBSET of 'common' below, so the 0.4 tier was unreachable and the gate
    # scored every answer 0 or 1 while the build scored it 0, 0.4 or 1. The
    # build then enforced a level ramp on its own numbers and the gate
    # rejected the boards on different ones - 43 of 44 published boards
    # disagreed. Free means the corpus printed it; 0.4 means we define it.
    # clipped to the site lexicon exactly as the generator clips it: an
    # attested string that is not a lexicon word is a folded entity name,
    # never an answer, and leaving it free here made the models differ on
    # 222 words for no reason a solver would notice. The length window is
    # the generator's own: nothing outside it can be an answer either.
    known = {w for w in (attested | crosswordese) & lex if 2 <= len(w) <= 12}
    cost_defined = set(defined)
    cost_defined |= {norm(w) for b in banks.values() for w in (b.get('terms') or {})}
    return {'lex': lex, 'ents': ents, 'ent_by_norm': ent_by_norm, 'ent_descs': ent_descs,
            'fillbank': fillbank, 'dictwords': dictwords,
            'fill_norms': {norm(w) for w in fillbank}, 'requested': requested,
            'banks': banks, 'curated': curated, 'news': news,
            'common': (attested | crosswordese | defined), 'defined': defined,
            'known': known, 'cost_defined': cost_defined}


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
        src = pr.get('from', '')
        if sorted(src) != sorted(a):
            return 'anagram proof letters do not match'
        if src == a:
            return 'anagram of itself'
        if src not in ref['lex']:
            return f'anagram source {src!r} is not a word'
        # One adjacent swap, or one letter moved, is an inflection or a typo
        # rather than wordplay: "ידו" from "דיו", "חסלי" from "חיסל".
        moved = [i for i, (x, y) in enumerate(zip(a, src)) if x != y]
        if (len(moved) == 2 and moved[1] == moved[0] + 1
                and a[moved[0]] == src[moved[1]] and a[moved[1]] == src[moved[0]]):
            return f'anagram source {src!r} is one adjacent swap from the answer'
        for i in range(len(a)):
            rest = a[:i] + a[i + 1:]
            for j in range(len(rest) + 1):
                if rest[:j] + a[i] + rest[j:] == src:
                    return f'anagram source {src!r} is the answer with one letter moved'
        return None
    if t == 'hidden':
        c, at = pr.get('carrier', ''), pr.get('at', -1)
        if c[at:at + len(a)] != a:
            return 'answer is not at the stated position in the carrier'
        if c == a or c not in ref['lex']:
            return f'carrier {c!r} is not a longer word'
        # A hidden clue has to actually hide. "צלופן מסתתר בתוך צלופנים" and
        # "יהי חבוי בתוך ליהי" name an inflection of the answer and tell the
        # solver nothing; 99.5% of the first carrier index was that.
        if c.startswith(a) or c.endswith(a):
            return f'carrier {c!r} is the answer plus an affix, not a hiding place'
        if at < 2 or len(c) - at - len(a) < 2:
            return f'answer sits at the edge of {c!r} rather than inside it'
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
    filler_wordplay = 0
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
        # A short clue ending in an index-wide qualifier narrows nothing:
        # every entity in the index is "בישראל" and every Bible name is a
        # "דמות מקראית".
        cw = clue.split()
        if (len(cw) >= 2 and cw[-1].strip(',.') in EMPTY_TAIL
                and all(w.strip(',.') in CATEGORY_WORD for w in cw[:-1])):
            bad.append(f'{key}: clue {clue!r} narrows nothing')
        if '. ' in clue or '(' in clue:
            bad.append(f'{key}: clue is truncated prose, not a clue')
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
        # Filler must be topic-neutral. A proper noun defined from the entity
        # index or a curated closed list is subject matter, and as filler it
        # turned a לשון board into a Bible quiz ("יהורם - בן אחאב").
        if (a not in pool and a not in ref['fill_norms']
                and a.startswith('ה') and a[1:] in ref['dictwords']):
            bad.append(f'{key}: {a!r} is a definite article stuck to a word')
        if (e.get('mechanism') == 'definition' and a not in pool
                and (e.get('proof') or {}).get('source') not in ('fill',)):
            bad.append(f"{key}: off-topic proper noun as filler "
                       f"(source {(e.get('proof') or {}).get('source')!r})")
        if e.get('mechanism') not in KNOWN_MECHANISMS:
            bad.append(f"{key}: unknown mechanism {e.get('mechanism')!r}")
        mechs[e.get('mechanism')] = mechs.get(e.get('mechanism'), 0) + 1
        if a in pool:
            topical += 1
        if len(a) >= LONG_ENTRY:
            long_total += 1
            long_topical += a in pool
        if a in pool or a in ref['common']:
            common += 1
        cost += (MECH_COST.get(e.get('mechanism'), 2.0)
                 + (0.0 if a in ref['known']
                    else (0.4 if a in ref['cost_defined'] else 1.0)))
        # An easy board clues its filler with a definition wherever it holds
        # one. "מעש מהסוף להתחלה" for שעם on the easiest civics board was
        # reported as a clue with nothing to do with the topic - and it is
        # worse than that, it is not a definition of anything. A wordplay
        # clue on a word the fillbank defines is the generator ignoring the
        # definition it has.
        if (p['level'] <= 2 and e.get('mechanism') != 'definition'
                and a in ref['fill_norms']):
            bad.append(f"{key}: wordplay on {a!r} although the fillbank defines it")
        if e.get('mechanism') != 'definition' and not e.get('topical'):
            filler_wordplay += 1

    n = max(1, len(got))
    long_topicality = long_topical / long_total if long_total else 1.0
    if long_topicality < MIN_LONG_TOPICALITY:
        bad.append(f'only {long_topicality:.0%} of the {LONG_ENTRY}+ letter entries '
                   f'are on topic (floor {MIN_LONG_TOPICALITY:.0%})')
    if p['level'] <= 2 and common / n < MIN_COMMON_SHARE:
        bad.append(f'level {p["level"]} promises common answers but only '
                   f'{common / n:.0%} are (floor {MIN_COMMON_SHARE:.0%})')
    mean_cost = cost / n
    # The build searches for a board inside the level's ceiling and no easier
    # than the level below, using ITS difficulty; the gate then checks those
    # same properties using THIS one. If the two numbers are not the same
    # number, neither check means anything - which is how a build that
    # enforced the ramp handed the gate boards that failed it.
    if abs(mean_cost - p.get('difficulty', mean_cost)) > 0.01:
        bad.append(f'published difficulty {p.get("difficulty")} is not the '
                   f'{mean_cost:.3f} measured here: the build and the gate are '
                   f'not measuring the same thing')
    ceiling = LEVEL_CEILING[p['level']]
    if mean_cost > ceiling + 0.01:
        bad.append(f'mean difficulty {mean_cost:.2f} above level '
                   f'{p["level"]}\'s ceiling of {ceiling}')
    stats = {'entries': len(got), 'topical': topical, 'topicality': topical / n,
             'filler_wordplay': filler_wordplay / n,
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
            by_topic.setdefault(p['topic'], {})[p['level']] = (
                stats['difficulty'] * stats['entries'], stats['difficulty'])

    # the ramp is a property of a subject's four boards, not of one board
    for topic, levels in by_topic.items():
        # On the WORK, mean clue difficulty times entries, not the mean: the
        # mean is per clue and cannot order boards of different sizes. A
        # 26-entry arrowword whose filler is everyday attested words had a
        # lower mean than the 16-entry crossword below it (lashon 0.47
        # against 0.51) and is plainly more to solve. The level ceiling stays
        # on the mean, since that is what it says.
        seq = [levels[L][0] for L in sorted(levels)]
        if any(b < a - 1e-9 for a, b in zip(seq, seq[1:])):
            failures.append(f'{topic}: work falls as the level rises: '
                            + ', '.join(f'{x:.1f}' for x in seq) + '  (mean '
                            + ', '.join(f'{levels[L][1]:.2f}' for L in sorted(levels)) + ')')

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
              f'filler wordplay {sum(r["filler_wordplay"] for r in rs) / len(rs):.0%}, '
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
