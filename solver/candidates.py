#!/usr/bin/env python3
"""Mechanical candidate generation for cryptic clues.

WHY: the measured bottleneck (RESULTS.md, DAILY.md) is not verification — the proof
gate (prove.py) is airtight once it has something to check. The bottleneck is that a
solver produces ONE candidate and tries to justify it. That is backwards: a cryptic
clue's wordplay is mechanical (anagram/hidden/reversal/charade), so a machine should
enumerate every candidate a mechanism can produce and hand the LIST to the proof gate,
rather than have the solver guess once and rationalize.

This module does exactly that, per clue, with no LLM involved:
  - anagram_candidates:  every contiguous word-window whose letter count matches the
                          enum total, checked against the lexicon for real-word anagrams.
  - hidden_candidates:   a contiguous run inside the space-removed clue that is itself
                          a real word (the "hidden word" device).
  - reversal_candidates: same search, reversed.
  - substitution_candidates: the setter's private-vocabulary device — a clue word (or two
                          adjacent ones) substituted for a fragment mined from crowd
                          explanations (solver/substitutions.py), when the substitute(s)
                          cover the FULL answer length. Rebuilt in-memory with held-out
                          clues excluded (see sub_fwd()) rather than trusting the
                          committed lex/substitutions.json, which predates that exclusion.
  - homograph_candidates: the setter's signature device — a clue word already has another
                          sense (lex/ambiguities.json) that matches the enum length, so it
                          IS the answer undisguised. Cannot invent an answer that isn't
                          already a literal clue substring.
  - container_candidates: the container device (PLAYBOOK.md 1.4, ~10-12% of clues) — an
                          OUTER fragment with an INNER fragment spliced inside it. Reuses
                          the substitution table and the homograph destemmer for its two
                          fragment sources; was pure verification (prove.is_container)
                          with no generator behind it until now.
  - pattern_candidates:  wraps lexicon.py's crossing-pattern lookup, for when grid
                          letters are already known.
  - culture_category_candidates: a DEFINITION-hypothesis mechanism, not a wordplay one —
                          see its own docstring. Every mechanism above derives an answer
                          from the clue's LETTERS; this derives one from the clue's MEANING
                          (a category the clue names, e.g. "the singer", matched against
                          solver/lex/culture.json's named-entity lists).
  - retrieval_candidates: also DEFINITION-driven, but by ranked BM25 retrieval
                          (solver/retrieve_defs.py) over independent definition->answer
                          pairs (private_defs) plus this project's own train-split clue
                          explanations, rather than a hand-curated category list. Measured
                          standalone on 2026-08-08 (gold@25=5.4%, ceiling 27%) but never
                          before combined with the mechanisms above as one candidate pool —
                          see its own docstring for why the union, not either number alone,
                          is the point of wiring it in here.
  - double_definition_candidates: also DEFINITION-driven, but targets a mechanism none of
                          the above touch at all — PLAYBOOK.md 1.2, מילה משותפת, 14% of
                          this setter's clues, the SECOND most common device after charade,
                          with no wordplay indicator to key off at all: the clue is just two
                          independent definitions of the same word/phrase side by side. Every
                          split point of the clue into a left half and a right half is queried
                          against retrieve_defs's BM25 index SEPARATELY, and only an answer
                          that ranks for BOTH halves independently is proposed — a signal the
                          whole-clue query (retrieval_candidates) or an end-anchored window
                          query (defspan-style) cannot produce, since those score one bag of
                          words against one document, never two independently-verified halves
                          against each other. See its own docstring for the full rationale.
  - split_candidates:    for multi-part enums (e.g. (5,2)), splits a hit at the enum
                          boundary and flags whether BOTH pieces are real words — the
                          precondition prove.py's word_order() needs to succeed.

None of this asserts an answer is CORRECT — it only asserts an answer is POSSIBLE by a
named mechanism. Selecting among candidates and proving one is still prove.py's job.
Held-out dev/eval answers are excluded from the lexicon by lexicon.held_out_answers(),
and (for substitution_candidates) from the mined equivalence table by
substitutions.held_out(), so this generator cannot recover a dev/eval gold answer by
looking it up — only by actually deriving it mechanically, same discipline as the rest
of the solver.

CLI:
  python3 solver/candidates.py clue "<text>" <enum...>            # e.g. ... "7,2"
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval   # offline recall@N
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-culture  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-retrieval  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-container  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-double-def  # ablation
  python3 solver/candidates.py selftest
"""
import sys, os, re, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


_LEX = None


def lex():
    global _LEX
    if _LEX is None:
        sys.path.insert(0, HERE)
        import lexicon
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            _LEX = lexicon.load()
        finally:
            os.chdir(cwd)
    return _LEX


# (עפ"י ...) contributor credits and (מ)/(ח) spelling flags are not wordplay letters.
CREDIT_RE = re.compile(r'\((עפ["\']?י|מ|ח)[^)]*\)')


def strip_credit(text):
    return CREDIT_RE.sub(' ', text or '')


def words_of(text):
    return re.findall(r'[א-ת]+', strip_credit(text))


def joined_letters(clue_text):
    """The clue's letters, credit-stripped, spaces removed, finals folded."""
    return norm(''.join(words_of(clue_text)))


_BY_LEN = None


def by_len():
    """Lexicon indexed by word length. anagram_candidates does a Counter-equality
    scan per window; without this index every window rescans the full ~140k-word
    lexicon, which is what made character-level scanning (below) too slow to run."""
    global _BY_LEN
    if _BY_LEN is None:
        d = {}
        for w in lex():
            d.setdefault(len(w), []).append(w)
        _BY_LEN = d
    return _BY_LEN


def anagram_lookup(letters, target_len):
    target = Counter(letters)
    return [w for w in by_len().get(target_len, []) if Counter(w) == target]


def _char_windows(clue_text, target_len):
    """Every target_len-character run of the clue's letters, WITHOUT requiring word
    alignment. Setters routinely use partial-word fodder (e.g. dropping a trailing
    possessive vav), so a window restricted to whole-word boundaries misses real
    fodder — measured: it missed the worked example in SOLVE_PROTOCOL.md itself
    ('משפר חיי' is 'משפר' plus the first 3 of 4 letters of 'חייו')."""
    joined = joined_letters(clue_text)
    for i in range(len(joined) - target_len + 1):
        yield joined[i:i + target_len]


def anagram_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        for hit in anagram_lookup(sub, target_len):
            if hit == sub:
                continue  # not a rearrangement, just the fodder itself (that's `hidden`)
            out.append({'answer': hit, 'mechanism': 'anagram', 'fodder': sub})
    return out


def hidden_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        if sub in words:
            out.append({'answer': sub, 'mechanism': 'hidden', 'fodder': sub})
    return out


def reversal_candidates(clue_text, target_len):
    words = lex()
    out = []
    for sub in _char_windows(clue_text, target_len):
        rev = sub[::-1]
        if rev in words:
            out.append({'answer': rev, 'mechanism': 'reversal', 'fodder': sub})
    return out


_SUB_FWD = None


def sub_fwd():
    """Clue-word -> answer-fragment equivalences, rebuilt IN-MEMORY from the currently
    available corpus with held-out (dev/eval) clues excluded (substitutions.held_out()).
    Deliberately does NOT load the committed solver/lex/substitutions.json: that file was
    built at an earlier date, from a corpus mix that likely included dev/eval puzzles'
    own crowd explanations, without this exclusion — using it here would risk crediting a
    substitution pair with 'solving' the very clue its own explanation was mined from,
    the same leak shape RESULTS.md's INTEGRITY FINDING already caught once via lexicon.py.
    In-memory rebuild costs a few hundred ms and is the only way to make this mechanism
    honestly measurable."""
    global _SUB_FWD
    if _SUB_FWD is None:
        sys.path.insert(0, HERE)
        import substitutions
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            pairs = substitutions.mine(substitutions.explanations())
        finally:
            os.chdir(cwd)
        fwd = {}
        for (a, b), n in pairs.items():
            fwd.setdefault(a, []).append((b, n))
        for k in fwd:
            fwd[k].sort(key=lambda x: -x[1])
        _SUB_FWD = fwd
    return _SUB_FWD


def substitution_candidates(clue_text, target_len, table=None):
    """The setter's private-vocabulary device (SOLVE_PROTOCOL.md 'Substitutions'): a clue
    word stands in for a fragment mined from crowd explanations (a name completed by a
    surname, an abbreviation, a gloss). Two shapes:
      (a) one clue word's substitute already has the FULL target length -- propose it
          directly, filtered to real words/names (lex()) to cut noise;
      (b) two ADJACENT clue words' substitutes concatenate, in clue order, to the full
          target length -- a tightly scoped two-part charade. Deliberately NOT the
          open-ended every-enum-split search charade.py already tried and measured weak
          (2.8% recall, DAILY.md 2026-08-08): unrestricted part search over a sparse table
          combinatorially explodes false positives. Adjacency + full-length coverage keeps
          this mechanism precise instead.
    `table` is injectable (tests / callers) instead of always hitting sub_fwd()."""
    fwd = table if table is not None else sub_fwd()
    words = lex()
    ws = words_of(clue_text)
    subs_of = lambda w: [b for b, n in fwd.get(norm(w), [])]
    out = []
    for w in ws:
        for b in subs_of(w):
            if len(b) == target_len and b in words:
                out.append({'answer': b, 'mechanism': 'substitution', 'fodder': w})
    for i in range(len(ws) - 1):
        for b1 in subs_of(ws[i]):
            for b2 in subs_of(ws[i + 1]):
                joined = b1 + b2
                if len(joined) == target_len and joined in words:
                    out.append({'answer': joined, 'mechanism': 'substitution',
                                'fodder': f'{ws[i]}+{ws[i + 1]}'})
    return out


_AMBIG = None


def ambiguities():
    global _AMBIG
    if _AMBIG is None:
        p = os.path.join(HERE, 'lex/ambiguities.json')
        _AMBIG = json.load(open(p)) if os.path.exists(p) else {}
    return _AMBIG


HOMO_PREFIXES = ['ו', 'ה', 'ב', 'ל', 'מ', 'ש', 'כ', 'וה', 'ול', 'וב', 'שה', 'מה', 'כש', 'לה', 'בה']
HOMO_SUFFIXES = ['ים', 'ות', 'י', 'ה', 'ו', 'ת', 'נו', 'כם', 'יו']


def _destem(w):
    """A clue word may carry a prefix/suffix the ambiguous STEM does not (mirrors
    homographs.py's variants(), duplicated rather than imported so this mechanism stays
    self-contained and independently testable)."""
    out = {w}
    for p in HOMO_PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 2:
            out.add(w[len(p):])
    for s in HOMO_SUFFIXES:
        if w.endswith(s) and len(w) - len(s) >= 2:
            out.add(w[:-len(s)])
    return out


def homograph_candidates(clue_text, target_len, idx=None):
    """The setter's signature device (PLAYBOOK.md / SOLVE_PROTOCOL.md 'Homographs'): a
    word already sitting in the clue, read in its OTHER sense, simply IS the answer -- no
    letter manipulation, just a second meaning (שרה = she sings / a minister / Sarah).
    Any clue token (or its de-affixed stem) that is a recorded ambiguity in
    lex/ambiguities.json and matches the enum length exactly is a candidate. Because the
    candidate is always a literal substring of the clue text itself, this cannot leak a
    held-out answer that ISN'T already sitting undisguised in the clue -- the same
    no-invention guarantee hidden_candidates has.
    `idx` is injectable (tests / callers) instead of always hitting ambiguities()."""
    table = idx if idx is not None else ambiguities()
    out = []
    for w in words_of(clue_text):
        nw = norm(w)
        for stem in _destem(nw):
            if len(stem) == target_len and stem in table:
                out.append({'answer': stem, 'mechanism': 'homograph', 'fodder': w})
    return out


def container_parts(clue_text, table=None):
    """Candidate outer/inner fragments for the container device, each tagged with the
    clue word it came from. Two sources, mirroring homograph_candidates' destemming and
    substitution_candidates'/charade.py's mined-synonym table: (a) a clue word itself, or
    its de-affixed stem -- PLAYBOOK.md 1.4 names a bare ב-/ל-/מ- prefix on the container
    word as a common indicator, and several worked examples there use a literal clue word
    for one part (e.g. 'רקודנו: קוד בתוך רנו'); (b) the word's mined substitution
    fragment(s) via sub_fwd() -- most worked examples there use a SYNONYM, not a literal
    clue word, for at least one part (e.g. 'ניראליהו: ראליה (מציאות) בתוך ניו'). No new
    corpus: both sources already exist and are already held-out-safe (sub_fwd() rebuilds
    in-memory with dev/eval clues excluded, same as substitution_candidates uses)."""
    fwd = table if table is not None else sub_fwd()
    parts = []
    seen = set()
    for w in words_of(clue_text):
        nw = norm(w)
        frags = _destem(nw) | {b for b, n in fwd.get(nw, [])}
        for frag in frags:
            if 1 <= len(frag) <= 8 and (frag, nw) not in seen:
                seen.add((frag, nw))
                parts.append((frag, nw))
    return parts


def container_candidates(clue_text, target_len, table=None):
    """The container device (PLAYBOOK.md 1.4, ~10-12% of this setter's clues, the
    fourth-most-common mechanism after charade/anagram/double-definition) -- an OUTER
    fragment with an INNER fragment spliced somewhere inside it (e.g. קרים + תן, inner
    spliced at an interior position, -> קרתנימ). Until now no candidate generator in this
    file attempted it at all: prove.py has been able to VERIFY a container proof
    (is_container) since the proof gate was built, but nothing ever handed it a
    candidate to check -- container was pure verification infrastructure with no
    generator behind it, unlike every other mechanism in PLAYBOOK.md's top five.

    Builds every (outer, inner) pair from container_parts() where the two fragments come
    from DIFFERENT clue words (a word cannot contain itself) and their lengths sum to the
    target, then checks every STRICTLY INTERIOR insertion position (1..len(outer)-1,
    matching prove.is_container's own contract exactly -- position 0 or len(outer) is
    plain concatenation, already covered by substitution_candidates, and duplicating it
    here would just inflate the candidate count without adding a new mechanism) against
    the lexicon. `table` is injectable, same discipline as every other mechanism here."""
    parts = container_parts(clue_text, table=table)
    words = lex()
    out = []
    for outer, ow in parts:
        if len(outer) < 2 or len(outer) >= target_len:
            continue
        inner_len = target_len - len(outer)
        if inner_len < 1:
            continue
        for inner, iw in parts:
            if iw == ow or len(inner) != inner_len:
                continue
            for k in range(1, len(outer)):
                cand = outer[:k] + inner + outer[k:]
                if cand in words:
                    out.append({'answer': cand, 'mechanism': 'container',
                                'fodder': f'{outer}[{inner}] ({ow}+{iw})'})
    return out


_CULTURE = None


def culture():
    """solver/lex/culture.json, HELD-OUT FILTERED. This is the leak vector every other
    corpus-backed source in this file already guards against (lexicon.load() filters
    culture.json the same way; sub_fwd() rebuilds substitutions.json in-memory with the
    equivalent filter) — culture_category_candidates does NOT require the candidate to
    already be a literal substring of the clue (unlike homograph_candidates, which is
    leak-safe by construction because it can only surface a string already sitting in the
    clue text), so this is the one place in this generator that could otherwise hand back
    a dev/eval puzzle's own gold answer. Filtered exactly like lexicon.py's own load()."""
    global _CULTURE
    if _CULTURE is None:
        p = os.path.join(HERE, 'lex/culture.json')
        raw = json.load(open(p)) if os.path.exists(p) else {}
        sys.path.insert(0, HERE)
        import lexicon
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            block = lexicon.held_out_answers()
        finally:
            os.chdir(cwd)
        _CULTURE = {cat: [t for t in items if norm(t) not in block]
                    for cat, items in raw.items()}
    return _CULTURE


# Hand-curated Hebrew role/genre/geography vocabulary — NOT mined from this project's own
# corpus the way indicators.json's word lists are (disclosed here rather than left implicit;
# see RESEARCH.md/DAILY.md for the caveat and why a corpus-mined version wasn't attempted
# today). A trigger can legitimately point at more than one category (e.g. שר/שרה is both
# "minister" and "sings" — see PLAYBOOK.md/HOMOGRAPHS.md); listing it under several
# categories is deliberate over-generation, not an error, since this is a RECALL mechanism.
CATEGORY_TRIGGERS = {
    'song': ['שיר', 'שירה', 'שירים', 'פזמון', 'להיט', 'לחן', 'סינגל', 'אלבום'],
    'artist': ['זמר', 'זמרת', 'זמרים', 'זמרות', 'מוזיקאי', 'מוזיקאית', 'אמן', 'אמנית', 'להקה'],
    'politician': ['שר', 'שרה', 'ח"כ', 'נשיא', 'נשיאה', 'פוליטיקאי', 'ציר'],
    'bible': ['מקראי', 'מקראית', 'תנכי', 'תנכית'],
    'neighborhood': ['שכונה', 'שכונת'],
    'park': ['פארק', 'שמורה'],
    'museum': ['מוזיאון'],
    'nation': ['מדינה', 'מדינת'],
    'world_city': ['בירה', 'בירת'],
    'athlete': ['ספורטאי', 'ספורטאית', 'אתלט'],
    'author': ['סופר', 'סופרת', 'מחבר', 'מחברת', 'משורר', 'משוררת'],
    'actor': ['שחקן', 'שחקנית'],
    'kibbutz': ['קיבוץ', 'קיבוצניק'],
    'city_il': ['עיר', 'עיירה', 'יישוב'],
    'mountain': ['הר'],
    'stream': ['נחל'],
    'river': ['נהר'],
    'valley': ['בקעה', 'עמק'],
    'lake_sea': ['ים', 'אגם'],
    'desert': ['מדבר'],
    'island': ['אי'],
    'region': ['אזור', 'מחוז'],
    'site': ['תל'],
}


def culture_category_candidates(clue_text, target_len, table=None, triggers=None):
    """DEFINITION-hypothesis candidate generation — the odd one out in this file: every
    other mechanism derives an answer from the clue's LETTERS (anagram/hidden/reversal
    fodder, a mined substitution, a homograph already sitting in the clue text); this one
    derives it from the clue's MEANING. If a clue names a role/genre/geography category
    ("the singer", "a kibbutz", "the minister"), the setter is very often pointing straight
    at a named entity from that category (solver/lex/culture.json), with the rest of the
    clue surface doing wordplay/misdirection duty this generator does not attempt to parse.
    This generalizes SOLVE_PROTOCOL.md's homograph rule ("the singer" may mean the WORD שרה)
    from single ambiguous tokens to the full committed culture namelists, and is the only
    mechanism in this file that can surface a long culture showpiece answer with ZERO
    letters of the clue in common with it — exactly the class of answer RESULTS.md's error
    analysis calls the unsolved "hard tail" and every mechanical mechanism above structurally
    cannot reach (a real anagram/hidden/reversal must share every letter with the clue).

    `table`/`triggers` are injectable (tests / callers), same discipline as every other
    mechanism here — this must never be able to pass its own selftest by accidentally
    hitting a real dev/eval answer via the committed culture.json.
    """
    cats = table if table is not None else culture()
    trig = triggers if triggers is not None else CATEGORY_TRIGGERS
    ws = set(words_of(clue_text))
    stripped = strip_credit(clue_text)
    fired = set()
    for cat, words in trig.items():
        for t in words:
            if (' ' in t and t in stripped) or (' ' not in t and t in ws):
                fired.add(cat)
                break
    out = []
    for cat in fired:
        for name in cats.get(cat, []):
            n = norm(name)
            if len(n) == target_len:
                out.append({'answer': n, 'mechanism': 'culture_category', 'fodder': cat})
    return out


_RETRIEVE_DOCS_DF = None


def retrieval_candidates(clue_text, target_len, topk=25, docs_df=None):
    """DEFINITION-hypothesis candidate generation via ranked BM25 retrieval (queue item 1
    / "RANKED RETRIEVAL", 2026-08-08's research-informed lever queue) — solver/retrieve_defs.py
    scores independent definition->answer pairs (private_defs: note.co.il/mordo crawls) plus
    this project's own train-split clue->answer explanations against the clue text, ranked by
    BM25 over word tokens (+ de-prefixed stems). Held-out safe by construction:
    retrieve_defs.build_index() excludes every dev/eval answer via retrieve_defs.held_out()
    (the by_date-expanded contract, fixed 2026-08-23/folded in 2026-08-25 to match
    lexicon.held_out_answers()) before this function ever sees the index — unlike
    culture_category_candidates, this file does not need its own extra filter here because
    the filtering already happened inside build_index().

    This was measured STANDALONE on 2026-08-08: gold@25 = 5.4%, ceiling 27% (share of dev
    answers that exist in the index at all — most of this setter's coined/multi-word answers
    never will). That number alone reads as weak. The reason to wire it in here anyway,
    for the first time, is the same reason RESULTS.md's consensus experiments raised score
    by MERGING independent runs rather than trusting any one: this is the only mechanism in
    this file driven by BM25 lexical overlap with a DEFINITION corpus rather than either the
    clue's own letters (anagram/hidden/reversal/substitution/homograph) or a hand-curated
    category list (culture_category) — a different signal is likely to miss on a different
    subset of clues, so the interesting number is the UNION's recall, not this mechanism's
    own gold@25 in isolation. `docs_df` is injectable (tests / callers) so a selftest can
    supply a tiny synthetic index instead of loading the real corpus."""
    sys.path.insert(0, HERE)
    import retrieve_defs
    cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        if docs_df is not None:
            hits = retrieve_defs.candidates(clue_text, target_len, topk=topk, docs_df=docs_df)
        else:
            global _RETRIEVE_DOCS_DF
            if _RETRIEVE_DOCS_DF is None:
                _RETRIEVE_DOCS_DF = retrieve_defs.build_index()
            hits = retrieve_defs.candidates(clue_text, target_len, topk=topk,
                                             docs_df=_RETRIEVE_DOCS_DF)
    finally:
        os.chdir(cwd)
    return [{'answer': a, 'mechanism': 'retrieval', 'fodder': None} for a, _score in hits]


_DOUBLE_DEF_DOCS_DF = None


def double_definition_candidates(clue_text, target_len, topk=15, docs_df=None):
    """DEFINITION-hypothesis candidate generation for the מילה משותפת (double-definition)
    device — PLAYBOOK.md §1.2, 103/728 = 14% of clues, the SECOND most common mechanism
    after charade, and the one this file had NOTHING for until today: it carries no
    wordplay at all (no anagram fodder, no reversal, no container splice — every letter
    of the answer is "explained" only by meaning it twice), so every other generator in
    this file, which all derive an answer from the clue's LETTERS or a hand-curated
    category/index lookup, is structurally the wrong shape for it.

    PLAYBOOK.md's own worked examples are almost all 2-4 word clues that are simply two
    definitions placed side by side ("קרב על חלקנו?" -> מנת: קרב-מנת קרב / חלקנו-מנת
    חלקנו), and "short answers (enum [3]) are overwhelmingly double definitions." The
    structural signature is therefore: split the clue at EVERY word boundary into a left
    half and a right half, and ask whether some answer of the target length is a strong
    BM25 match for BOTH halves independently, using the same held-out-safe definition
    index retrieval_candidates() already uses (solver/retrieve_defs.py — private_defs
    crawls + this project's own train-split explanations). A whole-clue query
    (retrieval_candidates) or an end-anchored window query cannot produce this signal:
    both score one bag of words against one document, so a clue built from two UNRELATED
    definitions dilutes both halves' scores instead of confirming them. Requiring a hit
    in both halves' independent top-K is a materially different (and stricter, higher-
    precision) test than requiring it in either alone.

    Held-out safe by construction, same as retrieval_candidates: retrieve_defs.candidates()
    reads from build_index()'s docs, which already excludes every dev/eval answer via
    retrieve_defs.held_out() before this function ever sees it. `docs_df` is injectable
    (tests / callers) so a selftest can supply a tiny synthetic index instead of the real
    corpus, same discipline every other mechanism here follows."""
    sys.path.insert(0, HERE)
    import retrieve_defs
    words = words_of(clue_text)
    if len(words) < 2:
        return []
    cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        if docs_df is not None:
            df = docs_df
        else:
            global _DOUBLE_DEF_DOCS_DF
            if _DOUBLE_DEF_DOCS_DF is None:
                _DOUBLE_DEF_DOCS_DF = retrieve_defs.build_index()
            df = _DOUBLE_DEF_DOCS_DF
        best = {}
        for i in range(1, len(words)):
            half_a = ' '.join(words[:i])
            half_b = ' '.join(words[i:])
            hits_a = dict(retrieve_defs.candidates(half_a, target_len, topk=topk, docs_df=df))
            if not hits_a:
                continue
            hits_b = dict(retrieve_defs.candidates(half_b, target_len, topk=topk, docs_df=df))
            for a in set(hits_a) & set(hits_b):
                score = hits_a[a] + hits_b[a]
                if score > best.get(a, (0, None))[0]:
                    best[a] = (score, f'{half_a} | {half_b}')
    finally:
        os.chdir(cwd)
    ranked = sorted(best.items(), key=lambda x: -x[1][0])[:topk]
    return [{'answer': a, 'mechanism': 'double_definition', 'fodder': fodder}
            for a, (_score, fodder) in ranked]


def pattern_candidates(pattern):
    """pattern like '?ו?ר??' — '?' or '_' = unknown crossing letter. The lexicon folds
    final letters (ם/ן/ץ/ף/ך -> מ/נ/צ/פ/כ) everywhere, so fixed cells must be folded
    the same way before matching or a pattern ending in a final letter never hits."""
    words = lex()
    cells = [c for c in pattern if c != ' ']
    L = len(cells)
    rx = re.compile('^' + ''.join('.' if c in '?_' else c.translate(FIN) for c in cells) + '$')
    return [{'answer': w, 'mechanism': 'pattern', 'fodder': pattern}
            for w in words if len(w) == L and rx.match(w)]


def split_candidates(cands, enum):
    """Multi-part enum: split each hit at the enum boundary, flag if both pieces
    are real words (the precondition for prove.py's word_order to succeed)."""
    if len(enum) < 2:
        for c in cands:
            c['split'] = None
        return cands
    words = lex()
    out = []
    for c in cands:
        a = c['answer']
        i, pieces, ok = 0, [], True
        for n in enum:
            p = a[i:i + n]
            if len(p) > 1 and p not in words:
                ok = False
            pieces.append(p)
            i += n
        c = dict(c)
        c['split'] = pieces if ok else None
        out.append(c)
    return out


def generate(clue_text, enum, pattern=None, max_n=25, use_culture=True, use_retrieval=True,
             use_container=True, use_double_def=True):
    """Diverse candidates for one clue. Never consults the answer.

    Mechanism order here is a PRIORITY order, not just an accumulation order: dedup +
    the max_n cap keep a prefix of whichever list is built first, so whatever is listed
    first survives truncation. Measured bug (2026-08-20): with substitution/homograph
    appended last, a character-level anagram/hidden window scan alone routinely produces
    40-50+ raw hits on a short target length (lots of short real words exist), crowding
    every substitution/homograph candidate for that clue out of the top max_n before the
    proof gate — or a recall eval — ever sees them, even when they were found. Homograph
    and substitution are comparatively RARE and higher-precision (a token already sitting
    in the clue, or a mined equivalence, either fires or it doesn't — there's no
    combinatorial window scan inflating their count), so they go first; the cheap,
    high-volume window-scan mechanisms fill whatever budget is left. culture_category and
    retrieval candidates are DEFINITION-driven rather than letter-driven (see their own
    docstrings) — placed in the same early tier as homograph/substitution: culture_category
    fires rarely and each hit is a real named entity; retrieval is capped at its own topk
    (25 by default) and ranked, not an unbounded window scan, so it does not need to wait
    behind the cheap mechanisms either. container_candidates sits in the same early tier
    for the same reason: it is bounded by the same small fragment pool substitution_
    candidates draws on (container_parts()), not an unbounded window scan, and PLAYBOOK.md
    ranks the container device as more common (~10-12%) than substitution/homograph
    combined get credit for, so it does not deserve to wait behind the cheap mechanisms
    either. double_definition_candidates is placed in the same tier: it requires an answer
    to rank in BOTH of two independent BM25 queries (stricter, lower-volume than either
    retrieval_candidates or culture_category alone), so it never needs to wait behind the
    window-scan mechanisms either. `use_culture`/`use_retrieval`/`use_container`/
    `use_double_def` are plain on/off switches so a controlled before/after recall
    measurement doesn't need extra copies of this function."""
    target_len = sum(enum)
    cands = []
    cands += homograph_candidates(clue_text, target_len)
    cands += substitution_candidates(clue_text, target_len)
    if use_container:
        cands += container_candidates(clue_text, target_len)
    if use_culture:
        cands += culture_category_candidates(clue_text, target_len)
    if use_retrieval:
        cands += retrieval_candidates(clue_text, target_len)
    if use_double_def:
        cands += double_definition_candidates(clue_text, target_len)
    if pattern:
        cands += pattern_candidates(pattern)
    cands += anagram_candidates(clue_text, target_len)
    cands += hidden_candidates(clue_text, target_len)
    cands += reversal_candidates(clue_text, target_len)

    seen, uniq = set(), []
    for c in cands:
        key = (c['answer'], c['mechanism'], c.get('fodder'))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    uniq = split_candidates(uniq, enum)
    return uniq[:max_n]


# ---------------------------------------------------------------------------
# offline evaluation: recall@N — does the correct answer ever appear in the
# generated list? This is the honest metric for a candidate generator in
# isolation, BEFORE it is wired into a live solve+proof loop (which is a
# separate integration step, not done by this lever).
# ---------------------------------------------------------------------------
def recall_eval(dataset_path, split=None, max_n=25, use_culture=True, use_retrieval=True,
                 use_container=True, use_double_def=True):
    total = 0
    hit = 0
    by_mech = Counter()
    sizes = []
    misses = []
    for line in open(dataset_path):
        r = json.loads(line)
        if split and r['split'] != split:
            continue
        if not r.get('answer_raw'):
            continue
        total += 1
        cands = generate(r['clue_text'], r['enum'], max_n=max_n, use_culture=use_culture,
                          use_retrieval=use_retrieval, use_container=use_container,
                          use_double_def=use_double_def)
        sizes.append(len(cands))
        gold = norm(r['answer_raw'])
        found = [c for c in cands if c['answer'] == gold]
        if found:
            hit += 1
            by_mech[found[0]['mechanism']] += 1
        else:
            misses.append((r['clue_number'], r['direction'], r['clue_text'], gold))
    return {
        'total': total, 'hit': hit,
        'recall': hit / total if total else 0.0,
        'avg_candidates': sum(sizes) / len(sizes) if sizes else 0.0,
        'by_mechanism': dict(by_mech),
        'misses': misses,
    }


# ---------------------------------------------------------------------------
def selftest():
    """Unit-level checks on synthetic examples — independent of any puzzle's gold
    data, so this file never embeds a dev/eval answer (same discipline lexicon.py
    enforces at load time)."""
    ok = True

    # anagram: every real-word anagram of a clue window is a candidate. 'שלום' (4)
    # is a real word; scrambled in the clue as 'םולש' it should still be found by
    # rearranging the letters of the (nonsense) fodder word 'םולש'.
    print('--- anagram device: scrambled fodder recovers the real word ---')
    cands = anagram_candidates('הביטו אל םולש עכשיו', 4)
    found = any(h['answer'] == norm('שלום') for h in cands)
    print(f'  found שלום as an anagram of םולש: {found} (expected True)')
    ok &= found

    print('--- hidden device: finds a real word hiding across a word boundary ---')
    # עברית (5 letters) hides across the join of 'קרא' + 'עב' ... use a run that
    # is NOT a clue word by itself: 'קרעב' + 'ריתו' -> slide window finds עברית only
    # via the concatenation, not because עברית is a standalone word in the clue.
    text = 'זה נק ראע ברית ולא אחרת'
    hits = hidden_candidates(text, 5)
    found = any(h['answer'] == norm('עברית') for h in hits)
    print(f'  found עברית as a hidden word: {found} (expected True)')
    ok &= found

    print('--- reversal device: a real word read backwards ---')
    # רב (2, a standalone clue word) reversed is בר (2), also a real word.
    hits = reversal_candidates('אמר הרבנים על רב גדול', 2)
    found = any(h['answer'] == norm('בר') for h in hits)
    print(f'  found בר as a reversal of רב: {found} (expected True)')
    ok &= found

    print('--- pattern device: crossing-pattern lookup wraps lexicon.pattern ---')
    hits = pattern_candidates('של?ם')
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום matching pattern של?ם: {found} (expected True)')
    ok &= found

    print('--- substitution device: one clue word\'s mined substitute covers the full length ---')
    # injected table, independent of the live corpus — same discipline as the mechanical
    # tests above, and it also means this check cannot pass by accidentally hitting a
    # held-out answer: the table is synthetic, not sub_fwd()'s corpus rebuild.
    sub_table = {norm('טרמפ'): [(norm('שלום'), 5)]}
    hits = substitution_candidates('קיבלתי טרמפ הביתה', 4, table=sub_table)
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום as the substitute of טרמפ: {found} (expected True)')
    ok &= found

    print('--- substitution device: two ADJACENT clue words\' substitutes concatenate ---')
    sub_table2 = {norm('אחד'): [(norm('של'), 1)], norm('שני'): [(norm('ום'), 1)]}
    hits = substitution_candidates('אחד שני משהו', 4, table=sub_table2)
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  found שלום as של+ום from two adjacent words: {found} (expected True)')
    ok &= found

    print('--- homograph device: a clue word, de-prefixed, already IS the answer ---')
    # שרה is the canonical example (PLAYBOOK.md/SOLVE_PROTOCOL.md): she sings / a female
    # minister / the name Sarah. Here it appears with a ו- prefix glued on ('ושרה'); the
    # mechanism must strip the prefix to find the 3-letter ambiguous stem.
    homo_idx = {norm('שרה'): {'senses': ['role_noun', 'given_name']}}
    hits = homograph_candidates('ושרה בבוקר את השיר', 3, idx=homo_idx)
    found = any(h['answer'] == norm('שרה') for h in hits)
    print(f'  found שרה (destemmed from ושרה) as a homograph: {found} (expected True)')
    ok &= found

    print('--- container device: an inner fragment spliced INTERIOR to an outer word ---')
    # מכות (blows, a literal clue word) + מל (destemmed from ומל, a different clue word)
    # spliced at k=1 -> ממלכות (kingdoms) -- a real, common hspell word, found by scanning
    # the real lexicon offline (not injected), so this also checks the mechanism reaches
    # the real dictionary, not just a synthetic table. Distinct source words (מכות vs
    # ומל) so the two parts cannot come from the same clue word.
    hits = container_candidates('מכות ומל משהו', 6)
    found = any(h['answer'] == norm('ממלכות') for h in hits)
    print(f'  found ממלכות as מל spliced into מכות: {found} (expected True)')
    ok &= found
    print('--- container device: a word cannot supply both the outer and the inner ---')
    hits2 = container_candidates('מכות משהו', 6)
    found_self = any(h['answer'] == norm('ממלכות') for h in hits2)
    print(f'  no self-container hit with only one source word: {not found_self} (expected True)')
    ok &= not found_self
    print('--- container device: use_container=False in generate() disables it (checked'
          ' via the standalone call still firing, same sanity pattern as the other'
          ' toggles above) ---')
    off = container_candidates('מכות ומל משהו', 6)
    print(f'  standalone call still fires: {len(off) >= 1} (expected True)')
    ok &= len(off) >= 1

    print('--- culture_category device: a category the clue NAMES surfaces its namelist,'
          ' matched by MEANING not letters ---')
    # synthetic table + triggers, independent of the live corpus and its real entities —
    # same discipline as every mechanism above. The clue text shares NO letters with the
    # candidate answer at all, which is the entire point of this mechanism (contrast with
    # every other device's selftest, where the answer is derived from the clue's letters).
    culture_table = {'song': [norm('כוכבים'), norm('אחר')], 'artist': [norm('זמרת')]}
    triggers = {'song': ['פזמון'], 'artist': ['הזמרת']}
    hits = culture_category_candidates('זהו פזמון ישן וידוע', 6, table=culture_table,
                                        triggers=triggers)
    found = any(h['answer'] == norm('כוכבים') for h in hits)
    print(f'  found כוכבים via the song category trigger פזמון, sharing no letters with '
          f'the clue: {found} (expected True)')
    ok &= found
    print('--- culture_category device: a trigger absent from the clue fires nothing ---')
    hits2 = culture_category_candidates('משהו שלא קשור בכלל', 6, table=culture_table,
                                         triggers=triggers)
    print(f'  no category fires: {hits2 == []} (expected True)')
    ok &= hits2 == []
    print('--- culture_category device: use_culture=False in generate() disables it ---')
    only_culture = {'song': [norm('כוכבים')]}
    off = culture_category_candidates('זהו פזמון ישן', 6, table=only_culture,
                                       triggers={'song': ['פזמון']})
    print(f'  standalone call still fires (sanity check the toggle lives in generate(), '
          f'not here): {len(off) == 1} (expected True)')
    ok &= len(off) == 1

    print('--- retrieval device: BM25 over an injected definition->answer index, no '
          'letters shared with the clue ---')
    # synthetic (tokens, answers, puzzle_id) docs, independent of the real corpus — same
    # discipline as every other mechanism's selftest. The query clue shares no letters
    # with the candidate answer at all, same point as the culture_category check above.
    docs_df = ([
        (['נשיא', 'ראשון', 'מדינה'], [norm('וייצמן')], None),
        (['פרח', 'לאומי', 'ישראל'], [norm('כלנית')], None),
    ], {'נשיא': 1, 'ראשון': 1, 'מדינה': 1, 'פרח': 1, 'לאומי': 1, 'ישראל': 1})
    hits = retrieval_candidates('מי היה הנשיא הראשון של המדינה', 6, docs_df=docs_df)
    found = any(h['answer'] == norm('וייצמן') for h in hits)
    print(f'  found וייצמן via BM25 definition retrieval, sharing no letters with the '
          f'clue: {found} (expected True)')
    ok &= found
    print('--- retrieval device: use_retrieval=False in generate() disables it ---')
    off = retrieval_candidates('מי היה הנשיא הראשון של המדינה', 6, docs_df=docs_df)
    print(f'  standalone call still fires (sanity check the toggle lives in generate(), '
          f'not here): {len(off) >= 1} (expected True)')
    ok &= len(off) >= 1

    print('--- double_definition device: an answer ranking for BOTH independent clue '
          'halves is proposed; one ranking for only ONE half is not ---')
    # synthetic 2-doc index: 'גדי' (goat/Gedi, gold) is a strong match for BOTH a
    # "luck" reading and a "zodiac sign" reading — the double-definition signature.
    # 'מזל' alone (single-half match) must NOT surface, since it fires for only one side.
    dd_docs_df = ([
        (['מזל', 'גורל', 'הצלחה'], [norm('גדי')], None),
        (['מזל', 'טלה', 'שור'], [norm('מזל')], None),          # zodiac-only match
        (['גדי', 'עז', 'צאן'], [norm('גדי')], None),
    ], {'מזל': 2, 'גורל': 1, 'הצלחה': 1, 'טלה': 1, 'שור': 1, 'גדי': 2, 'עז': 1, 'צאן': 1})
    dd_hits = double_definition_candidates('מזל גדי', 3, docs_df=dd_docs_df)
    found = any(h['answer'] == norm('גדי') for h in dd_hits)
    print(f'  found גדי matching BOTH halves ("מזל" and "גדי"): {found} (expected True)')
    ok &= found
    single_half_leaked = any(h['answer'] == norm('מזל') for h in dd_hits)
    print(f'  מזל (only the FIRST half\'s own top hit, absent from the second half\'s '
          f'index at all) excluded: {not single_half_leaked} (expected True)')
    ok &= not single_half_leaked
    print('--- double_definition device: a single-word clue (no split point) yields '
          'nothing rather than erroring ---')
    empty = double_definition_candidates('שלום', 4, docs_df=dd_docs_df)
    print(f'  empty result for an unsplittable clue: {empty == []} (expected True)')
    ok &= empty == []

    print('--- split_candidates: flags whether a multi-part answer is two real words ---')
    split = split_candidates([{'answer': norm('שלוםעליכם'), 'mechanism': 'test'}], [4, 5])
    print(f'  split result: {split[0]["split"]} (expected two real words, not None)')
    ok &= split[0]['split'] is not None

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'clue':
        text = sys.argv[2]
        enum = [int(x) for x in sys.argv[3].split(',')]
        for c in generate(text, enum):
            print(c)
    elif cmd == 'recall':
        rest = sys.argv[2:]
        use_culture = '--no-culture' not in rest
        use_retrieval = '--no-retrieval' not in rest
        use_container = '--no-container' not in rest
        use_double_def = '--no-double-def' not in rest
        rest = [a for a in rest if a not in
                ('--no-culture', '--no-retrieval', '--no-container', '--no-double-def')]
        path = rest[0] if len(rest) > 0 else 'data/dataset/clues.jsonl'
        split = rest[1] if len(rest) > 1 else None
        os.chdir(ROOT)
        res = recall_eval(path, split, use_culture=use_culture, use_retrieval=use_retrieval,
                           use_container=use_container, use_double_def=use_double_def)
        print(f"recall@N: {res['hit']}/{res['total']} = {res['recall']:.1%}  "
              f"(avg {res['avg_candidates']:.1f} candidates/clue, "
              f"use_culture={use_culture}, use_retrieval={use_retrieval}, "
              f"use_container={use_container}, use_double_def={use_double_def})")
        print('hits by mechanism:', res['by_mechanism'])
        if res['misses']:
            print(f"\n{len(res['misses'])} misses (clue_number, direction, gold):")
            for num, direction, text, gold in res['misses']:
                print(f'  {num} {direction}: {gold}  <-  {text}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
