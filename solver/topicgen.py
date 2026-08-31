#!/usr/bin/env python3
"""Topic crosswords: give it a topic and a level, get back a finished puzzle.

    generate('biologia', level=2, shape='classic7')

This is the back end behind the topic-crossword pages, the weekly news puzzle
and the by-request puzzles. It is the solver's own knowledge turned around:
the same retrieval index, the same lexicon, the same "an answer without a
proof is a guess" rule, run backwards to SET a puzzle instead of solving one.

Answers come from, in priority order:

  1. the topic's curated bank      solver/lex/topics.json        (theme)
  2. the topic's entity queries    docs/milon/entities.json      (theme)
  3. the topic's curated lists     solver/lex/defs_curated.json  (theme)
  4. the general filler bank       solver/lex/fillbank.json
  5. the entity index, geography and Bible categories, whose one-line
     descriptions make solvable clues
  6. answers our corpus actually saw in real puzzles (solver/lex/ambiguities
     .json, solver/crosswordese.json), clued by wordplay
  7. the rest of the lexicon, clued by wordplay - hard levels only

Two things make a level, and both are measured rather than asserted:

  HOW COMMON the answers are. Levels 1 and 2 fill only from answers that
  really turn up in newspaper puzzles; 3 and 4 open the whole lexicon. This
  matters more than the clue type: an anagram of a word you know is easier
  than a definition of a word you do not.

  HOW HARD the clues are. definition < hidden < reversal < anagram. Each level
  has a difficulty band, and a fill that cannot be clued into its band is
  thrown away rather than published as the wrong level.

Every clue carries a machine-checkable proof. A definition clue names the row
it was copied from, so evals/topicgen_eval.py can re-read that row and refuse
the puzzle if the text drifted; the wordplay clues carry the check itself.

Everything it reads is committed, so this runs in a fresh clone.
Deterministic: the same (topic, level, shape, seed) gives the same puzzle.
"""
import functools
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'solver'))
from grid_tools import slots, check_fill      # noqa: E402
import grids_topic                            # noqa: E402

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
UNFIN = {'כ': 'ך', 'מ': 'ם', 'נ': 'ן', 'פ': 'ף', 'צ': 'ץ'}
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)

# Entity categories whose descriptions are real clues. Songs, artists and
# athletes are excluded on purpose: "שיר של רחלי שביט" identifies the answer
# to nobody, and a board full of those is unsolvable rather than hard.
CLUEABLE_CATS = {'city_il', 'world_city', 'nation', 'island', 'mountain', 'river',
                 'stream', 'lake_sea', 'desert', 'valley', 'region', 'bible',
                 'site', 'park', 'museum', 'military', 'common',
                 'kibbutz', 'moshav', 'neighborhood'}

# What a clue costs the solver, and what an answer costs. The two add up to
# the entry's difficulty; a level is a band on the mean.
MECH_COST = {'definition': 0.0, 'hidden': 1.0, 'reversal': 1.5, 'anagram': 2.0}
COST_COMMON, COST_DEFINED, COST_RARE = 0.0, 0.4, 1.0

# Every level may use every mechanism; what makes a level is the BAND its mean
# difficulty has to land in, plus which answers it may use. Withholding
# mechanisms from the easy levels only starved them: a clue is picked cheapest
# first and raised only to reach the band's floor, so an expensive mechanism
# appears at level 1 exactly when nothing cheaper exists, and the band's
# ceiling stops that from happening often.
MECHANISMS = ['definition', 'hidden', 'reversal', 'anagram']
# A level is a CEILING on mean difficulty, which answers it may use, and how
# its FILLER is clued. It is deliberately not a floor: an earlier version
# raised clues until the mean reached a floor, and since an anagram is the
# cheapest way to raise a mean, a "medium" board came out as fifteen anagrams
# of arbitrary words.
#
# `filler` is the honest version of that ramp. At level 1 a filler answer takes
# its definition if we have one; from level 2 it takes wordplay, cheapest
# mechanism first. A TOPIC answer always keeps its definition at every level -
# the topic is what the board is for, and no level is improved by hiding it.
LEVELS = {
    1: {'name': 'קל', 'mechanisms': MECHANISMS, 'tier': 'common',
        'ceiling': 1.25, 'filler': 'define'},
    2: {'name': 'בינוני', 'mechanisms': MECHANISMS, 'tier': 'common',
        'ceiling': 1.7, 'filler': 'wordplay'},
    3: {'name': 'קשה', 'mechanisms': MECHANISMS, 'tier': 'all',
        'ceiling': 2.5, 'filler': 'wordplay'},
    4: {'name': 'אתגר', 'mechanisms': MECHANISMS, 'tier': 'rare',
        'ceiling': 9.9, 'filler': 'wordplay'},
}
DEFAULT_SHAPE = {1: 'classic7', 2: 'arrow9', 3: 'classic9', 4: 'arrow11'}
THEME_SHARE = 0.55        # of the entries whose length the topic can reach
MIN_THEME_CANDIDATES = 8  # a length with fewer topic answers is not themeable
PHRASE_STOP = {'של', 'עם', 'על', 'או', 'גם', 'תשבץ', 'תשחץ', 'מילון', 'פתרון'}
MAX_THEME_SLOTS = 14      # past this the search spends longer than the gain
PROBE_TRIES = 9000        # search nodes when testing whether a theme count fits
FULL_TRIES = 60000        # nodes for the unconstrained fallback fill
# Whole-board node allowance. A 32-entry board needs several times the search a
# 16-entry one does; giving them the same allowance left the big boards with
# two topic answers in them.
# Calibrated so one board is tens of seconds, not minutes: a node on a
# 32-entry board costs far more than one on a 16-entry board, so the counts do
# not scale with the entry count the way the wall clock did.
WORK = {'classic7': 400_000, 'arrow9': 700_000,
        'classic9': 150_000, 'arrow11': 150_000}
LONG_ENTRY = 5            # an entry this long reads as a theme entry


def final_form(w):
    """Restore the final letter that normalising folded away."""
    return w[:-1] + UNFIN.get(w[-1], w[-1]) if w else w


# ------------------------------------------------------------------ data

@functools.lru_cache(maxsize=1)
def load():
    """Every index the generator needs, read once from committed files."""
    lex = sorted({w.strip() for w in
                  open(os.path.join(ROOT, 'docs/solve/data/lexicon.txt'), encoding='utf-8')
                  if 2 <= len(w.strip()) <= 12})
    lexset = set(lex)

    ents = json.load(open(os.path.join(ROOT, 'docs/milon/entities.json'), encoding='utf-8'))
    shared = {}
    for e in ents:
        d = (e.get('d') or '').strip()
        if d:
            shared[d] = shared.get(d, 0) + 1

    # word -> (clue, proof, display). Sorted input, first writer wins, so the
    # pool is identical on every machine.
    general = {}
    fillbank = json.load(open(os.path.join(ROOT, 'solver/lex/fillbank.json'),
                              encoding='utf-8'))
    for w in sorted(fillbank):
        n = norm(w)
        if n in lexset:
            general[n] = (fillbank[w], {'type': 'definition', 'source': 'fill', 'key': w}, w)
    curated = {k: v for k, v in json.load(
        open(os.path.join(ROOT, 'solver/lex/defs_curated.json'), encoding='utf-8')).items()
        if not k.startswith('_')}
    # Note what is NOT here: entity descriptions and the curated closed lists.
    # Both are proper nouns tied to a subject, and as filler they made a
    # grammar board read like a Bible quiz ("יהורם - בן אחאב" in a לשון
    # puzzle). They stay available to any topic that ASKS for them, through
    # the bank's own entity queries and curated references. General filler is
    # everyday vocabulary, which belongs in any puzzle.

    # Definition pages readers asked for and someone curated: each is a
    # hand-checked list of answers for one clue phrase, which is exactly what a
    # requested crossword on that phrase needs. Keyed by phrase.
    requested = {}
    rpath = os.path.join(ROOT, 'solver/lex/defs_requested.json')
    if os.path.exists(rpath):
        for spec in json.load(open(rpath, encoding='utf-8')).values():
            if isinstance(spec, dict) and spec.get('phrase'):
                for phrase in [spec['phrase']] + list(spec.get('variants', ())):
                    requested.setdefault(phrase.strip(), spec)

    topics = {}
    # topics.json is hand-curated; topics_news.json is written weekly by
    # scraper/news_israel.py. Same shape, one code path, so the news puzzle is
    # generated and checked exactly like a bagrut one.
    for fname in ('topics.json', 'topics_news.json'):
        path = os.path.join(ROOT, 'solver/lex', fname)
        if os.path.exists(path):
            topics.update({k: v for k, v in json.load(open(path, encoding='utf-8')).items()
                           if not k.startswith('_')})

    # Wordplay indices. The word a clue NAMES has to be one the solver could
    # look up: docs/solve/data/lexicon.txt also carries entity names and song
    # titles, folded to letters, and "hidden inside אבאהולכלעבודה" is not a
    # clue anybody can solve. The answer may still be an entity - it gets a
    # definition clue from the index - but the source never is.
    # the "common" tier: answers the corpus actually saw in printed puzzles
    freq = {norm(k): v for k, v in json.load(
        open(os.path.join(ROOT, 'solver/crosswordese.json'), encoding='utf-8')).items()}
    attested = set(json.load(open(os.path.join(ROOT, 'solver/lex/ambiguities.json'),
                                  encoding='utf-8')))
    common = (attested | set(freq) | set(general)) & lexset

    # A wordplay clue NAMES a word, and the solver has to recognise it. The
    # site lexicon folds entity names and song titles to bare letters as well,
    # so "hidden inside אבאהולכלעבודה" came out of it; dictwords.txt is the
    # single-word dictionary alone. Common words are offered first, so a clue
    # says בלדרות rather than an inflection nobody has met.
    dictwords = sorted(
        (w.strip() for w in open(os.path.join(ROOT, 'solver/lex/dictwords.txt'),
                                 encoding='utf-8') if w.strip()),
        key=lambda w: (w not in common, w))
    dictset = set(dictwords)
    groups = {}
    for w in dictwords:            # common first, so the partner picked is common
        groups.setdefault(''.join(sorted(w)), []).append(w)
    # An anagram clue is only a clue if the letters really move. "ידו" from
    # "דיו" and "מדוד" from "מדדו" are one adjacent swap apart and read as a
    # typo rather than as wordplay.
    def one_swap(a, b):
        """A source one adjacent swap - or one letter moved - from the answer
        is an inflection or a typo, not wordplay: חסלי for חיסל."""
        if len(a) != len(b):
            return False
        d = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]:
            return True
        for i in range(len(a)):                 # remove one letter of a and
            rest = a[:i] + a[i + 1:]            # reinsert it somewhere else
            for j in range(len(rest) + 1):
                if rest[:j] + a[i] + rest[j:] == b:
                    return True
        return False

    anagrams = {}
    for w in lex:
        if len(w) < 4:
            continue
        for x in groups.get(''.join(sorted(w)), ()):
            if x != w and not one_swap(w, x):
                anagrams[w] = x
                break
    reversible = {w: w[::-1] for w in lex if w[::-1] != w and w[::-1] in dictset}
    # A hidden clue is only a clue if the answer is genuinely buried. Taking
    # the first carrier that contained the substring gave "צלופן מסתתר בתוך
    # צלופנים" and "יהי חבוי בתוך ליהי" - an inflection of the answer, which
    # tells the solver nothing. 99.5% of the old index was that. The answer now
    # has to sit at least two letters in from both ends of a carrier that is
    # neither answer-plus-suffix nor prefix-plus-answer.
    # ...and the carrier itself has to be a word the reader has met. Without
    # this the fallback carriers were forms like הזדיינויות and היחרשויות:
    # real hspell entries, recognisable to nobody.
    carrier = {}
    for c in dictwords:
        if not 6 <= len(c) <= 11 or c not in common:
            continue
        for L in range(2, len(c) - 3):
            for i in range(2, len(c) - L - 1):
                sub = c[i:i + L]
                if (sub not in carrier and sub in lexset
                        and not c.startswith(sub) and not c.endswith(sub)):
                    carrier[sub] = (c, i)

    # The easy tier: what a casual solver has certainly met - our own defined
    # vocabulary plus the answers the corpus saw more than once.
    easy = (set(general) | set(freq)) & lexset
    return {'lex': lexset, 'general': general, 'topics': topics, 'curated': curated,
            'requested': requested, 'easy': easy, 'dictwords': dictset,
            'shared': shared,
            'ents': ents, 'reversible': reversible, 'carrier': carrier,
            'anagrams': anagrams, 'freq': freq, 'common': common}


# Tails that narrow nothing. "הר באריתריאה" is a clue; "יישוב בישראל" is a
# label - the whole index is in Israel. Kept as an explicit list because the
# distinction is about what the reader can deduce, not about word count.
EMPTY_TAIL = {'בישראל', 'ישראלי', 'ישראלית', 'מקראי', 'מקראית', 'מיקראית',
              'מקראיות', 'מקומית', 'מקומי', 'עתיק', 'עתיקה', 'קדום', 'קדומה',
              'משונעים', 'לשעבר', 'ידוע', 'מפורסם', 'כללי',
              'בתנ"ך', 'בתנך', 'במקרא', 'בתורה'}


# Bare category nouns. A description made only of one of these plus an
# index-wide tail is a label; add one real word and it becomes a clue:
# "יישוב בישראל" identifies nothing, "ההר הגבוה בישראל" identifies חרמון.
CATEGORY_WORD = {'דמות', 'דמויות', 'יישוב', 'עיר', 'כפר', 'מושב', 'קיבוץ',
                 'נהר', 'הר', 'מקום', 'אתר', 'שכונה', 'מועצה', 'חפצים',
                 'ההר', 'העיר', 'הכפר', 'היישוב', 'הנהר'}


def _label_only(words, tail_set):
    """True when the description is a category noun plus an empty tail."""
    if len(words) < 2 or words[-1].strip(',.') not in tail_set:
        return False
    return all(w.strip(',.') in CATEGORY_WORD for w in words[:-1])


def usable_description(d, shared_count):
    """Is this entity description printable as a clue?

    The index carries whatever the source article opened with, so it holds
    truncated prose ("...נכבש ונהרס במהלך מל"), labels that identify nobody
    ("עיר בישראל", attached to hundreds), and stray biography with dates in
    brackets. A clue has to point at ONE answer and read as a clue.
    """
    d = (d or '').strip()
    if not 12 <= len(d) <= 90:
        return False
    if '. ' in d or '(' in d or ')' in d:
        return False
    if shared_count > 1:                 # a description shared with another
        return False                     # entity identifies neither of them
    words = d.split()
    if len(words) < 2:
        return False
    # "דמות מקראית" in a Bible puzzle, "יישוב בישראל" in a geography one: true,
    # unique in the index, and useless as a clue.
    if _label_only(words, EMPTY_TAIL):
        return False
    return True


def topic_terms(ctx, topic):
    """{normalized answer: (clue, proof, display)} for one topic.

    A free Hebrew phrase that is not a bank slug still works: it is matched
    against the entity descriptions the way the milon's clue pages are (every
    content word must appear), so "עיר בהולנד" is a usable topic.
    """
    out = {}
    bank = ctx['topics'].get(topic)
    if bank:
        for w, d in sorted(bank.get('terms', {}).items()):
            n = norm(w)
            if 2 <= len(n) <= 12:
                out.setdefault(n, (d, {'type': 'definition', 'source': 'bank',
                                       'topic': topic, 'key': w}, w))
        for q in bank.get('entities', []):
            cat, rx = q.get('cat'), q.get('rx')
            for e in sorted(ctx['ents'], key=lambda x: x['t']):
                d = (e.get('d') or '').strip()
                if (cat and e['c'] != cat) or (rx and not re.search(rx, d)):
                    continue
                n = norm(e['t'])
                if (usable_description(d, ctx['shared'].get(d, 1))
                        and 2 <= len(n) <= 12 and n not in d and n not in out):
                    out[n] = (d, {'type': 'definition', 'source': 'entity',
                                  'key': e['t']}, e['t'])
        for key in bank.get('curated', []):
            for w, d in sorted(ctx['curated'].get(key, {}).get('items', {}).items()):
                n = norm(w)
                if 2 <= len(n) <= 12 and n not in d and n not in out:
                    out[n] = (d, {'type': 'definition', 'source': 'curated',
                                  'list': key, 'key': w}, w)
        return out
    # A definition page already curated for this exact phrase is the best
    # possible answer: someone checked those answers by hand.
    spec = ctx['requested'].get(topic.strip())
    if spec:
        for w, d in sorted((spec.get('items') or {}).items()):
            n = norm(w)
            if 2 <= len(n) <= 12 and d and n not in d:
                out.setdefault(n, (d, {'type': 'definition', 'source': 'requested',
                                       'phrase': spec['phrase'], 'key': w}, w))
        cat, rx = spec.get('cat'), spec.get('rx')
        if cat:
            for e in sorted(ctx['ents'], key=lambda x: x['t']):
                d = (e.get('d') or '').strip()
                n = norm(e['t'])
                if (e['c'] == cat and (not rx or re.search(rx, d))
                        and usable_description(d, ctx['shared'].get(d, 1))
                        and 2 <= len(n) <= 12 and n not in d):
                    out.setdefault(n, (d, {'type': 'definition', 'source': 'entity',
                                           'key': e['t']}, e['t']))
    # A curated list whose title IS the phrase is the next best:
    # "עיר באיטליה" is already a hand-checked list of 39 answers.
    for key, spec in sorted(ctx['curated'].items()):
        title = (spec.get('title') or '').strip()
        if title and (title == topic.strip() or title in topic or topic in title):
            for w, d in sorted(spec.get('items', {}).items()):
                n = norm(w)
                if 2 <= len(n) <= 12 and n not in d:
                    out.setdefault(n, (d, {'type': 'definition', 'source': 'curated',
                                           'list': key, 'key': w}, w))
    # Then the entity index, matched the way app/drain_requests.py matches it:
    # every content word must appear, with a one-letter prefix stripped, so
    # "עיר באיטליה" also finds a description reading "עיר בצפון איטליה".
    toks = []
    for w in topic.split():
        if len(w) > 3:
            w = re.sub(r'^[בלמהוכש]', '', w)
        if len(w) > 1 and w not in PHRASE_STOP:
            toks.append(re.escape(w))
    if not toks:
        return out
    # AND, not OR (an OR join matched 'דרום אירופה' for 'דרום אמריקה'), and
    # each token has to start a word, optionally behind a one-letter Hebrew
    # prefix - otherwise 'בלה' matched every description with those three
    # letters somewhere inside a longer word.
    rx = ''.join(rf'(?=.*\b[בלמהוכש]?{t})' for t in toks)
    for e in sorted(ctx['ents'], key=lambda x: x['t']):
        d = (e.get('d') or '').strip()
        n = norm(e['t'])
        if (re.search(rx, d) and usable_description(d, ctx['shared'].get(d, 1))
                and 2 <= len(n) <= 12 and n not in d):
            out.setdefault(n, (d, {'type': 'definition', 'source': 'entity',
                                   'key': e['t']}, e['t']))
    return out


# ------------------------------------------------------------------ clues

# Four boards a week on one topic should not all read like one template, so
# each wordplay clue picks its phrasing from the answer itself - deterministic,
# and varied across a board.
HIDDEN_SAYS = ['מסתתר בתוך {}', 'חבוי בתוך {}', 'יושב ברצף בתוך {}',
               'מוסתר בתוך {}', 'אפשר לקרוא אותו בתוך {}']
REVERSAL_SAYS = ['הפוך את {}', '{} מהסוף להתחלה', 'קראו את {} אחורה',
                 '{} בכיוון ההפוך']
ANAGRAM_SAYS = ['סדרו מחדש את האותיות של {}', 'אותן אותיות כמו {}, בסדר אחר',
                'ערבוב האותיות של {}', 'מה שיוצא מן האותיות של {}']


def _say(options, w, arg):
    return options[sum(ord(c) for c in w) % len(options)].format(arg)


def clue_options(ctx, w, terms, allowed):
    """Every clue we could print for this answer, cheapest mechanism first."""
    out = []
    if 'definition' in allowed:
        if w in terms:
            d, proof, disp = terms[w]
            out.append(('definition', d, proof, disp, True))
        elif w in ctx['general']:
            d, proof, disp = ctx['general'][w]
            out.append(('definition', d, proof, disp, False))
    disp = final_form(w)
    if 'hidden' in allowed and w in ctx['carrier']:
        c, at = ctx['carrier'][w]
        out.append(('hidden', _say(HIDDEN_SAYS, w, final_form(c)),
                    {'type': 'hidden', 'carrier': c, 'at': at}, disp, False))
    if 'reversal' in allowed and w in ctx['reversible']:
        src = ctx['reversible'][w]
        out.append(('reversal', _say(REVERSAL_SAYS, w, final_form(src)),
                    {'type': 'reversal', 'from': src}, disp, False))
    if 'anagram' in allowed and w in ctx['anagrams']:
        src = ctx['anagrams'][w]
        out.append(('anagram', _say(ANAGRAM_SAYS, w, final_form(src)),
                    {'type': 'anagram', 'from': src}, disp, False))
    return out


def answer_cost(ctx, w, terms):
    if w in terms or w in ctx['general']:
        return COST_DEFINED if w not in ctx['freq'] else COST_COMMON
    return COST_COMMON if w in ctx['common'] else COST_RARE


def cluable(ctx, terms, allowed, tier):
    """Every answer we could both place and clue at this level.

    Filler has to be a DICTIONARY word or a bank entry. The corpus-attested
    set also holds acronyms and names picked up from printed grids, and as
    filler they read as noise: קק"ל clued as a reversal of לקק is not a clue.
    A topic answer may still be a proper noun - that is the point of it.
    """
    base = {'easy': ctx['easy'], 'common': ctx['common']}.get(tier, ctx['lex'])
    base = (base & ctx['dictwords']) | set(ctx['general']) | set(terms)
    if tier == 'rare':
        # אתגר. Its filler comes from outside the everyday vocabulary, so the
        # answers themselves are what make it hard. Without this, level 4 drew
        # on the same words as level 3 and measured EASIER than it.
        base = (ctx['lex'] & ctx['dictwords']) - ctx['easy'] | set(terms)
    # "הכלב" and "הדירה" are a definite article stuck to a word; as filler
    # they read as a mistake. A bank entry that genuinely starts with ה keeps
    # its place.
    keep = set(terms) | set(ctx['general'])
    base = {w for w in base
            if w in keep or not (w.startswith('ה') and w[1:] in ctx['dictwords'])}
    pool = set()
    if 'definition' in allowed:
        pool |= set(terms) | set(ctx['general'])
    if 'hidden' in allowed:
        pool |= set(ctx['carrier'])
    if 'reversal' in allowed:
        pool |= set(ctx['reversible'])
    if 'anagram' in allowed:
        pool |= set(ctx['anagrams'])
    return (pool & base) | (set(terms) & pool)


# ------------------------------------------------------------------ fill

_POOL_CACHE = {}


def pool_index(ctx, pool, topical, rare_first, cache_key):
    """Constraint index over the cluable pool only.

    Intersecting the full-lexicon index with the pool at every search node is
    what made the first version of this unusably slow; the index is built once
    per (topic, level) and reused across every fill attempt and every shape.
    """
    if cache_key in _POOL_CACHE:
        return _POOL_CACHE[cache_key]
    freq = ctx['freq']
    sign = 1 if rare_first else -1
    rank = {w: (0 if w in topical else 1, sign * freq.get(w, 0), w) for w in pool}
    by_len, idx, topical_len = {}, {}, {}
    for w in sorted(pool, key=rank.get):
        by_len.setdefault(len(w), []).append(w)      # already in preference order
        for p, ch in enumerate(w):
            idx.setdefault((len(w), p, ch), set()).add(w)
    for w in sorted(topical & pool, key=rank.get):
        topical_len.setdefault(len(w), []).append(w)
    out = {'by_len': by_len, 'idx': idx, 'rank': rank,
           'topical': topical & pool, 'topical_len': topical_len}
    _POOL_CACHE.clear()          # one topic/level in flight at a time
    _POOL_CACHE[cache_key] = out
    return out


def fill(grid, pi, rng, theme=frozenset(), budget=None, width=14):
    """Fill every slot from the pool index. Backtracking, most constrained first.

    `theme` names the slots that must take a topic answer. Reserving those
    before the filler gets a look in is what makes the puzzle about its topic:
    left to itself the search takes whatever is cheapest and a biology
    crossword comes out with two biology words in it.

    Candidate lists are cached per slot and refreshed only for the slots that
    cross the one just filled. Recomputing all of them at every node made a
    9x9 board take a minute.

    `budget` is a one-element list of search nodes, SHARED with the caller and
    decremented here, so one board's whole search is bounded by a count rather
    than by a clock. That is what makes a seed reproducible: a wall-clock
    deadline crosses at a different point on a busy machine and the same seed
    then walks a different plan.
    """
    sl = slots(grid)
    keys = sorted(sl)
    cells_of = {k: sl[k] for k in keys}
    crossing = {k: sorted({k2 for k2 in keys if k2 != k
                           and set(cells_of[k]) & set(cells_of[k2])}) for k in keys}
    board, assigned = {}, {}
    rank, topical = pi['rank'], pi['topical']

    def candidates(k):
        L = len(cells_of[k])
        known = [(p, board[c]) for p, c in enumerate(cells_of[k]) if c in board]
        if not known:
            return (pi['topical_len'] if k in theme else pi['by_len']).get(L, [])
        sets = sorted((pi['idx'].get((L, p, ch), frozenset()) for p, ch in known), key=len)
        out = set(sets[0])
        for s in sets[1:]:
            out &= s
            if not out:
                break
        if k in theme:
            out &= topical
        return sorted(out, key=rank.get)

    cands = {k: candidates(k) for k in keys}

    def recurse(budget):
        rest = [k for k in keys if k not in assigned]
        if not rest:
            return True
        best = min(rest, key=lambda k: (len(cands[k]), k))
        if not cands[best]:
            return False
        # top slice by preference, shuffled inside it. Sorting AFTER the
        # shuffle (the first version) made every retry identical and useless.
        head = list(cands[best][:max(width * 4, 60)])
        first = [w for w in head if w in topical]
        rest_w = [w for w in head if w not in topical]
        rng.shuffle(first)
        rng.shuffle(rest_w)
        used = set(assigned.values())
        for w in (first + rest_w)[:width]:
            budget[0] -= 1
            if budget[0] <= 0:
                return False
            if w in used:
                continue
            touched, ok = [], True
            for c, ch in zip(cells_of[best], w):
                if c in board:
                    if board[c] != ch:
                        ok = False
                        break
                else:
                    board[c] = ch
                    touched.append(c)
            if ok:
                assigned[best] = w
                saved = {}
                for k2 in crossing[best]:
                    if k2 not in assigned:
                        saved[k2] = cands[k2]
                        cands[k2] = candidates(k2)
                if recurse(budget):
                    return True
                cands.update(saved)
                del assigned[best]
            for c in touched:
                del board[c]
        return False

    return dict(assigned) if recurse(budget if budget is not None else [30000]) else None


# ------------------------------------------------------------------ build

def _clue_the_fill(ctx, sol, terms, allowed, ceiling, filler):
    """Give every answer its EASIEST clue, and reject the board if that is
    still harder than the level allows.

    There is deliberately no attempt to reach a minimum: making a clue harder
    than it needs to be is not a feature of an easy level, it is a worse clue.
    """
    hi = ceiling
    chosen, options = {}, {}
    for key, w in sorted(sol.items()):
        opts = clue_options(ctx, w, terms, allowed)
        if not opts:
            return None
        options[key] = opts
        chosen[key] = 0                      # cheapest
        if filler == 'wordplay' and w not in terms:
            # the cheapest clue that is NOT a definition, if there is one
            for i, o in enumerate(opts):
                if o[0] != 'definition':
                    chosen[key] = i
                    break
    acost = {key: answer_cost(ctx, sol[key], terms) for key in sol}

    def mean():
        return sum(MECH_COST[options[k][chosen[k]][0]] + acost[k]
                   for k in chosen) / len(chosen)

    if mean() > hi:
        return None                          # too hard even at its easiest
    out = {}
    for key in chosen:
        mech, clue, proof, disp, _ = options[key][chosen[key]]
        out[key] = {'answer': sol[key], 'display': disp, 'clue': clue,
                    'mechanism': mech, 'topical': sol[key] in terms, 'proof': proof}
    return out


def generate(topic, level=1, shape=None, seed=None, attempts=3, work=None):
    """The back-end call: (topic, level) in, a finished puzzle out, or None.

    `work` is the search-node allowance for the whole board. Something has to
    bound it - a nearly fillable board holds the plan open indefinitely, and a
    40-board rebuild has to be something a person will actually run - and a
    COUNT is the only bound that keeps a seed reproducible.
    """
    if level not in LEVELS:
        raise ValueError(f'level must be one of {sorted(LEVELS)}')
    shape = shape or DEFAULT_SHAPE[level]
    if shape not in grids_topic.SHAPES:
        raise ValueError(f'shape must be one of {sorted(grids_topic.SHAPES)}')
    kind, grid = grids_topic.SHAPES[shape]
    spec = LEVELS[level]
    allowed = set(spec['mechanisms'])
    ctx = load()
    terms = topic_terms(ctx, topic)
    if not terms:
        return None
    pool = cluable(ctx, terms, allowed, spec['tier'])
    pi = pool_index(ctx, pool, set(terms), level == 4, (topic, level))

    sl = slots(grid)
    # Theme slots: the longest entries whose LENGTH the topic can actually
    # supply. Forcing the single 9-letter slot to be topical when the bank has
    # six 9-letter terms just makes the board unfillable.
    # Theme slots. Two orderings, tried in turn, because they fail in
    # different ways:
    #   long-first  the entries a solver reads as the theme are the long ones,
    #               so those are reserved first and given up last
    #   supported   if the long entries cannot all be filled from the bank,
    #               fall back to the slots the bank has most answers for
    def support(k):
        return len(pi['topical_len'].get(len(sl[k]), ()))
    # A 32-term weekly news bank cannot offer eight answers at any one length,
    # so a fixed threshold made every news board unthemeable and it shipped
    # with nothing on topic in its long entries. The bar scales with the bank.
    need = max(3, min(MIN_THEME_CANDIDATES, len(terms) // 12))
    themeable = [k for k in sl if support(k) >= need]
    # Long entries first, and WITHIN those by how many topic answers of that
    # length the bank holds. Ordering the long slots by length alone spent the
    # reservation on the two 6-letter slots, which are the scarcest length in
    # every bank, and left the twelve 5-letter slots to the filler.
    long_first = sorted(themeable,
                        key=lambda k: (0 if len(sl[k]) >= LONG_ENTRY else 1,
                                       -support(k), -len(sl[k]), k))
    supported = sorted(themeable,
                       key=lambda k: (-(min(support(k), 30) + 3 * len(sl[k])), k))
    base_seed = seed if seed is not None else 20260830
    left = [int(work if work is not None else WORK.get(shape, 400_000))]

    # Walk the theme count down from the maximum and take the first count that
    # fills: that is the most of the board the topic can honestly carry. The
    # walk is affordable because a hopeless count is rejected on a short node
    # budget - the first version gave every count the full search and spent the
    # whole time allowance proving that fourteen was too many.
    def attempt_at(order, k, per_attempt, reserve=0):
        for attempt in range(attempts):
            if left[0] - reserve < per_attempt:
                return None
            rng = random.Random(base_seed * 1000 + k * 97 + attempt)
            slice_ = [min(per_attempt, left[0] - reserve)]
            sol = fill(grid, pi, rng, theme=frozenset(order[:k]), budget=slice_)
            left[0] -= per_attempt - slice_[0]
            if not sol or check_fill(grid, sol, None)[0]:
                continue
            entries = _clue_the_fill(ctx, sol, terms, allowed, spec['ceiling'],
                                     spec.get('filler', 'define'))
            if not entries:
                continue
            texts = [e['clue'] for e in entries.values()]
            if len(set(texts)) != len(texts):
                continue
            # A clue must not give its answer away - except a hidden clue,
            # where naming the carrier IS the mechanism.
            if any(norm(e['answer']) in norm(e['clue'])
                   for e in entries.values() if e['mechanism'] != 'hidden'):
                continue
            return entries, sol
        return None

    def theme_score(got):
        """How well this board carries its topic: the long entries first."""
        entries = got[0]
        long_ent = [e for e in entries.values() if len(e['answer']) >= LONG_ENTRY]
        long_share = (sum(1 for e in long_ent if e['topical']) / len(long_ent)
                      if long_ent else 1.0)
        share = sum(1 for e in entries.values() if e['topical']) / len(entries)
        return (long_share, share)

    k0 = min(len(long_first), MAX_THEME_SLOTS, max(2, round(THEME_SHARE * len(sl))))
    # Each ordering gets its own walk down from the maximum, and the two
    # winners are compared. Interleaving them took whichever ordering happened
    # to survive one slot longer, which was usually the one that themes the
    # short entries and leaves the long ones to the filler.
    # A third of the allowance is held back for the unconstrained fallback, so
    # a topic that cannot carry any theme slot still gets a board.
    reserve = FULL_TRIES
    candidates = []
    for order in (long_first, supported):
        for k in range(k0, 0, -1):
            got = attempt_at(order, k, PROBE_TRIES, reserve)
            if got:
                candidates.append(got)
                break
    found = max(candidates, key=theme_score) if candidates else None
    if not found:
        # No theme count fits: fall back to an unconstrained fill so the caller
        # gets a board rather than nothing. It will be short on topic answers,
        # which is exactly what the eval's floors are there to catch.
        found = attempt_at(long_first, 0, FULL_TRIES)

    if found:
        entries, sol = found
        bank = ctx['topics'].get(topic, {})
        out = {
            'topic': topic, 'title': bank.get('title', topic),
            'blurb': bank.get('blurb', ''), 'tags': bank.get('tags', []),
            'level': level, 'level_name': spec['name'],
            'shape': shape, 'kind': kind, 'grid': grid, 'seed': base_seed,
            'entries': [dict(num=key[0], dir=key[1], **entries[key])
                        for key in sorted(entries, key=lambda x: (x[0], x[1]))],
        }
        if kind == 'arrow':
            out['hosts'] = {f'{key[0]}{key[1]}': list(v) for key, v
                            in sorted(grids_topic.arrow_hosts(grid).items())}
        n = len(out['entries'])
        out['topicality'] = round(sum(1 for e in out['entries'] if e['topical']) / n, 3)
        out['difficulty'] = round(sum(
            MECH_COST[e['mechanism']] + answer_cost(ctx, e['answer'], terms)
            for e in out['entries']) / n, 3)
        return out
    return None


def theme_share(p, long_entry=LONG_ENTRY):
    """(share of long entries on topic, share of all entries on topic)."""
    long_ent = [e for e in p['entries'] if len(e['answer']) >= long_entry]
    return ((sum(1 for e in long_ent if e['topical']) / len(long_ent)) if long_ent else 1.0,
            p['topicality'])


# When the big board of a family cannot be made to carry the topic, the small
# board of the same family is used instead. A 32-entry board with three topic
# answers in it is not a topic crossword; a 16-entry one with seven is.
SMALLER = {'classic9': 'classic7', 'arrow11': 'arrow9'}
MIN_LONG_SHARE = 0.35     # of the entries a solver reads as the theme


def generate_best(topic, level, shape=None, seeds=(20260830, 7, 12345), effort=1.0):
    """The board a reader should get: best of a few seeds.

    One seed is a lottery - measured spread on the same topic and level was 6%
    to 33% of entries on topic - and the published board is written once and
    read many times, so it is worth three searches. `effort` scales each
    seed's node allowance.
    """
    want = shape or DEFAULT_SHAPE[level]
    work = int(WORK.get(want, 400_000) * effort)
    made = [p for p in (generate(topic, level, want, seed=s, work=work)
                        for s in seeds) if p]
    best = max(made, key=theme_share) if made else None
    if (best is None or theme_share(best)[0] < MIN_LONG_SHARE) and want in SMALLER:
        alt = generate_best(topic, level, SMALLER[want], seeds, effort)
        if alt and (best is None or theme_share(alt) > theme_share(best)):
            return alt
    return best


def main():
    import argparse
    ap = argparse.ArgumentParser(description='generate a topic crossword')
    ap.add_argument('topic')
    ap.add_argument('--level', type=int, default=1)
    ap.add_argument('--shape', default=None)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    p = generate(a.topic, a.level, a.shape, a.seed)
    if not p:
        sys.exit('could not generate a puzzle for that topic and level')
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=1))
        return
    print(f"{p['title']} | {p['level_name']} | {p['shape']} | "
          f"topical {p['topicality']:.0%} | difficulty {p['difficulty']}")
    print('\n'.join(p['grid']))
    for e in p['entries']:
        print(f" {'*' if e['topical'] else ' '}{e['num']:>2}{e['dir'][0]}  "
              f"{e['display']:<14} {e['clue']}")


if __name__ == '__main__':
    main()
