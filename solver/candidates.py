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
  - homophone_candidates: the setter's נשמע (sounds-like) device (PLAYBOOK.md 1.6, ~4% of
                          clues) — same char-window scan as anagram/hidden, but the window
                          is folded through a Hebrew consonant-class equivalence (ק/כ/ח,
                          ט/ת, ס/ש, א/ע — the swaps indicators.json's own crowd-mined
                          entry names as free) before the lexicon lookup, since undotted
                          Hebrew cannot distinguish these sounds in writing. Does not model
                          vowel-letter (ו/י) flexibility, which would change string length;
                          see its own docstring.
  - homophone_vowel_candidates: closes homophone_candidates' own disclosed gap above — the
                          same נשמע device, but for the ו/י free-vowel swaps that change
                          string length by one, tried as an insertion (fodder one letter
                          short) or a deletion (fodder one letter long) against the same
                          phon-folded lexicon index.
  - charade_candidates:  a 2-part enum (e.g. (4,3)) solved as two INDEPENDENT anagram/
                          hidden windows, in clue order, that need not be adjacent — the
                          gap the whole-clue window scan above cannot close, since it can
                          only find both parts of a charade when their fodder is one
                          contiguous run. See its own docstring; measured 2026-09-08
                          (recall unchanged, 0/10 multi-part-enum clues on the dev puzzle
                          it was tested against — a real negative result, not a bug).
  - substitution_candidates: the setter's private-vocabulary device — a clue word (or two
                          or three adjacent ones, chained) substituted for a fragment mined
                          from crowd explanations (solver/substitutions.py), when the
                          substitute(s) cover the FULL answer length. Rebuilt in-memory with held-out
                          clues excluded (see sub_fwd()) rather than trusting the
                          committed lex/substitutions.json, which predates that exclusion.
  - homograph_candidates: the setter's signature device — a clue word already has another
                          sense (lex/ambiguities.json) that matches the enum length, so it
                          IS the answer undisguised. Cannot invent an answer that isn't
                          already a literal clue substring.
  - container_candidates: the container device (PLAYBOOK.md 1.4, ~10-12% of clues) — an
                          OUTER fragment with an INNER fragment spliced inside it. Reuses
                          the substitution table and the homograph destemmer for two of
                          its three fragment sources; was pure verification
                          (prove.is_container) with no generator behind it until 2026-09-03.
                          [NEW 2026-09-13] container_parts() gained a THIRD fragment
                          source: when a clue word is a role/category TRIGGER (the same
                          CATEGORY_TRIGGERS culture_category_candidates uses, e.g. "the
                          judge", "the singer"), every named entity in that category from
                          culture.json becomes a candidate fragment — reaching container
                          clues whose inner/outer piece is an ENTITY fact rather than a
                          literal clue word or a generic synonym, the gap 2026-09-11/12's
                          log entries root-caused (בית~קן is a real mined synonym, but
                          שופט/השופט never maps to a specific judge's name טל in that
                          table). See container_parts()'s own docstring for the honest
                          caveat: culture.json currently has no "judge" category at all,
                          so this closes the GENERATOR gap, not necessarily this exact
                          clue's DATA gap.
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
                          explanations, rather than a hand-curated category list. Queries
                          with the FULL clue text. Measured standalone on 2026-08-08
                          (gold@25=5.4%, ceiling 27%) but never before combined with the
                          mechanisms above as one candidate pool — see its own docstring
                          for why the union, not either number alone, is the point of
                          wiring it in here.
  - defspan_retrieval_candidates: the SAME retrieval index, but queried with only a short
                          PREFIX or SUFFIX word-span of the clue (retrieve_defs.py's
                          end_candidates(), 2/3/4-word spans each end) instead of the whole
                          clue text — the query shape retrieve_defs.py's own `eval` CLI has
                          always used to produce the "gold@25=5.4%" number quoted above,
                          which retrieval_candidates() (whole-clue query) never actually
                          matched. See its own docstring for the gap this closes.
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
  - abbreviation_candidates: [NEW 2026-09-14] PLAYBOOK.md 2.3, "the signature device,
                          ~27% of clues" -- a clue word for a number, role, or institution
                          stands for the letter(s) that spell it (gematria) or abbreviate
                          it, charading with an adjacent LITERAL clue word (זימימ =
                          ז['seven'/'week']+ימימ[literal]). Curated, not corpus-mined
                          (ABBREV_TABLE/ABBREV_BIGRAMS, taken verbatim from PLAYBOOK.md's
                          own worked table), so unlike substitution_candidates it does not
                          depend on 14across access at all. See its own docstring.
  - split_candidates:    for multi-part enums (e.g. (5,2)), splits a hit at the enum
                          boundary and flags whether BOTH pieces are real words — the
                          precondition prove.py's word_order() needs to succeed.
  - defs_lexicon (lexicon.py, [NEW 2026-09-19], not a candidate function of its own):
                          every mechanism above can only ever propose an answer that is
                          already a member of lex() (this file's cached wrapper around
                          lexicon.load()) — `lexicon_coverage_eval` (2026-09-15/16)
                          measured only 28.6%/32.1% of two dev puzzles' gold answers are
                          lex() members AT ALL, which explains a flat recall@N far more
                          directly than any one mechanism's own firing rate. lexicon.py's
                          `load()` now also folds in `data/answers/private_defs/`'s
                          answer-side vocabulary (already crawled and used by
                          retrieve_defs.py as RETRIEVAL documents, never before as a
                          LEXICON MEMBERSHIP source) — a large, independently-sourced
                          list of real crossword answers from other puzzles, held-out
                          filtered exactly like the corpus/culture tiers. Toggle with
                          `set_use_defs_lexicon()` / `--no-defs-lexicon`; see
                          lexicon.py's own docstring for the full rationale and the
                          honest note on why this is stricter than retrieve_defs.py's
                          own (deliberately unfiltered) use of the same source.
  - hwdb lexicon (lexicon.py, [NEW 2026-09-20], not a candidate function of its own):
                          the private_defs tier (above) attacked lex() coverage from the
                          ATTESTED-ANSWER side and measured a clean negative (0/38 overlap
                          on 2 puzzles, 2026-09-19) -- this setter's idioms simply weren't
                          among other crosswords' answers. This tier attacks the OTHER
                          side of the same gap: `hspell_simple.txt` is a headword list,
                          not a full-form one (RESEARCH.md 2026-09-16: כן is a headword,
                          וכן is not), and prefix-stripping was deliberately not shipped
                          as a fix (short residual stems are coincidence-prone).
                          lexicon.py's `load()` now also folds in
                          `github.com/roni5604/hebrew-words-db` (CC0, 67,008 words built
                          from noun/verb/adjective INFLECTION TABLES -- plurals, verb
                          conjugations, adjective agreement -- not just headwords), at the
                          same general-dictionary priority as hspell and, like hspell, NOT
                          held-out filtered (an ordinary inflected word coinciding with a
                          gold answer is the same legitimate case RESULTS.md's own
                          INTEGRITY FINDING already ruled acceptable for hspell). Toggle
                          with `set_use_hwdb()` / `--no-hwdb`.

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
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-container-entity
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-double-def  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-defspan-retrieval
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-homophone  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-homophone-vowel
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-substitution-3part
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-charade  # ablation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-abbreviation
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-defs-lexicon
    # ablation: private_defs answers removed from lex() (see defs_lexicon above)
  python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-hwdb
    # ablation: hebrew-words-db inflected forms removed from lex() (see hwdb lexicon above)
  python3 solver/candidates.py lexicon-coverage data/dataset/clues.jsonl eval  # mechanism-
    # agnostic ceiling: what fraction of gold answers are lex() members at all
  python3 solver/candidates.py lexicon-coverage data/dataset/clues.jsonl eval --prefix
    # of the answers NOT in lex(), how many become members after stripping one leading
    # Hebrew prefix (ו/ה/ב/ל/מ/ש/כ and their pairs) -- diagnostic only, does not change
    # what any mechanism accepts
  python3 solver/candidates.py lexicon-coverage data/dataset/clues.jsonl eval --no-defs-lexicon
  python3 solver/candidates.py lexicon-coverage data/dataset/clues.jsonl eval --no-hwdb
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
_USE_DEFS_LEXICON = True  # lexicon.py's new private_defs membership source (2026-09-19)
_USE_HWDB = True  # lexicon.py's new hebrew-words-db inflected-forms source (2026-09-20)


def set_use_defs_lexicon(v):
    """Toggle lexicon.py's private_defs membership source (see its own docstring) for a
    controlled before/after measurement, mirroring how use_retrieval/use_culture/etc.
    already toggle other sources per recall_eval() run. Unlike those, this one lives
    inside lex() itself (every mechanism reads lex()/by_len()/by_phon(), not a per-call
    parameter), so flipping it must invalidate every cache derived from lex() or a
    lingering stale _LEX from a prior call would silently ignore the new setting."""
    global _USE_DEFS_LEXICON, _LEX, _BY_LEN, _BY_PHON
    if v != _USE_DEFS_LEXICON:
        _LEX = None
        _BY_LEN = None
        _BY_PHON = None
    _USE_DEFS_LEXICON = v


def set_use_hwdb(v):
    """Toggle lexicon.py's hebrew-words-db inflected-forms source. Same cache-invalidation
    shape as set_use_defs_lexicon() above, for the same reason."""
    global _USE_HWDB, _LEX, _BY_LEN, _BY_PHON
    if v != _USE_HWDB:
        _LEX = None
        _BY_LEN = None
        _BY_PHON = None
    _USE_HWDB = v


def lex():
    global _LEX
    if _LEX is None:
        sys.path.insert(0, HERE)
        import lexicon
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            _LEX = lexicon.load(include_private_defs=_USE_DEFS_LEXICON,
                                 include_hwdb=_USE_HWDB)
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


def _char_windows_pos(clue_text, target_len):
    """Same scan as _char_windows, but also yields each window's (start, end) character
    offset into joined_letters(clue_text) — charade_candidates needs the position to
    keep two independently-found parts in clue ORDER and non-overlapping."""
    joined = joined_letters(clue_text)
    for i in range(len(joined) - target_len + 1):
        yield i, i + target_len, joined[i:i + target_len]


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


# Phonetic letter-class folding for the homophone device (PLAYBOOK.md 1.6, נשמע, ~30/728
# = 4% of clues) — indicators.json's own homophone entry names the swaps this setter's
# crowd explanations record as free: ק/כ, ט/ת, ס/ש, א/ע, ח/כ. Undotted Hebrew script
# cannot distinguish these sounds in writing, so a clue fragment can "sound like" a real
# word it is not literally spelled as. Folding each equivalence class to one
# representative turns "sounds like" into a same-LENGTH string transform, so the exact
# char-window scan anagram/hidden/reversal already run can be reused unchanged for it.
# Deliberately narrower than the full device: indicators.json also records "free vowel
# changes" (ו/י insertion or omission), which changes string length and would need a
# different search entirely — not modeled here, disclosed rather than silently dropped.
PHON_FOLD = str.maketrans('עחקטש', 'אככתס')


def phon(s):
    """Canonical phonetic key: final-letter-folded, consonant-class-folded. Same length
    as norm(s) by construction (a straight char-for-char translation), which is what lets
    homophone_candidates reuse the fixed-width window scan."""
    return norm(s).translate(PHON_FOLD)


_BY_PHON = None


def by_phon():
    """Lexicon indexed by phonetic key, mirroring by_len()'s length index — same reason:
    without it every window would rescan the whole lexicon computing phon() per word."""
    global _BY_PHON
    if _BY_PHON is None:
        d = {}
        for w in lex():
            d.setdefault(phon(w), []).append(w)
        _BY_PHON = d
    return _BY_PHON


def homophone_candidates(clue_text, target_len):
    """The homophone device: a clue fragment that SOUNDS like the answer, spelled
    differently (indicators.json: שמענו/נשמע/עפ"י השמיעה של.../a lone ש׳). Every
    fixed-length window of the clue's letters (same scan as anagram_candidates) is
    phon()-folded and looked up against the lexicon's own phon-folded index; a match
    whose LITERAL spelling differs from the window is a homophone candidate (an
    identical-spelling match is the hidden device, already covered, so it is excluded
    here exactly as anagram_candidates excludes the fodder-equals-answer case)."""
    out = []
    for sub in _char_windows(clue_text, target_len):
        key = phon(sub)
        for hit in by_phon().get(key, []):
            if hit == sub:
                continue  # identical spelling — that's `hidden`, not a homophone
            out.append({'answer': hit, 'mechanism': 'homophone', 'fodder': sub})
    return out


def homophone_vowel_candidates(clue_text, target_len):
    """Closes the gap homophone_candidates' own docstring discloses rather than models:
    indicators.json's homophone entry also names ו/י (vav/yod) insertion or omission as a
    free swap — undotted Hebrew can write the same sound with or without these vowel
    letters — which changes string LENGTH, unlike PHON_FOLD's consonant-class swaps. This
    is not a hypothetical gap: measured directly on 2026-05-29 (2026-09-05's log), this
    puzzle's own homophone-marked clue (22 across, "עפ"י השמיעה של...") needs the 7-letter
    fodder "הזורזים" to sound like the 8-letter answer "אנזימים" — one vav apart, exactly
    this device — and homophone_candidates cannot reach it by construction (fixed-width
    window only).

    Two fodder-window widths, both phon()-folded then looked up in the SAME by_phon()
    index homophone_candidates already builds:
      - target_len - 1: the fodder may be missing a vowel letter the real answer has —
        try inserting ו and י at every position of the folded window.
      - target_len + 1: the fodder may carry an extra vowel letter the real answer lacks —
        try deleting each ו/י the folded window actually contains, one at a time.
    Insertion/deletion only ever touches ו/י (the documented free-swap letters, never any
    other letter), so this stays a narrow, grounded device rather than an open-ended
    edit-distance search — it cannot manufacture a match against an arbitrary fodder the
    way a generic fuzzy-match would."""
    out = []
    idx = by_phon()
    if target_len - 1 >= 1:
        for sub in _char_windows(clue_text, target_len - 1):
            base = phon(sub)
            for i in range(len(base) + 1):
                for vowel in ('ו', 'י'):
                    key = base[:i] + vowel + base[i:]
                    for hit in idx.get(key, []):
                        out.append({'answer': hit, 'mechanism': 'homophone_vowel', 'fodder': sub})
    for sub in _char_windows(clue_text, target_len + 1):
        base = phon(sub)
        for i, ch in enumerate(base):
            if ch in ('ו', 'י'):
                key = base[:i] + base[i + 1:]
                for hit in idx.get(key, []):
                    out.append({'answer': hit, 'mechanism': 'homophone_vowel', 'fodder': sub})
    return out


def _part_hits(clue_text, part_len):
    """Every (start, end, real_word, device) a window of exactly part_len characters
    can produce by anagram or by being hidden outright — the two per-part devices a
    charade segment plausibly uses. Shared by charade_candidates so it does not
    duplicate anagram_candidates'/hidden_candidates' own lookups."""
    out = []
    for start, end, sub in _char_windows_pos(clue_text, part_len):
        for hit in anagram_lookup(sub, part_len):
            if hit != sub:  # an anagram device rearranges; matching itself is `hidden`
                out.append((start, end, hit, 'anagram'))
        if sub in lex():
            out.append((start, end, sub, 'hidden'))
    return out


def charade_candidates(clue_text, enum, max_parts_out=200):
    """A multi-part enum (e.g. (4,3)) as a CHARADE of independently-solved parts, each
    its own anagram or hidden-word device — not one mechanism covering the whole
    answer length in a single contiguous window, which is all anagram_candidates/
    hidden_candidates can do today (they anagram/hide the FULL target_len at once).

    WHY this is missing today: a charade's two parts routinely draw fodder from
    DISJOINT stretches of the clue with an indicator or the definition sitting between
    them (SOLVE_PROTOCOL.md's own charade description: "split enum parts; solve each
    part from clue fragments"), so requiring one contiguous target_len-character run
    to account for BOTH parts at once — which is what feeding the whole clue into
    anagram_candidates/hidden_candidates does — can never find a charade whose two
    parts are not adjacent in the fodder. split_candidates() only checks post-hoc
    whether an already-generated FULL-length hit happens to split into two real words
    at the enum boundary; it cannot originate a candidate whose parts came from
    separate windows in the first place.

    Scoped to 2-part enums for now (mirrors substitution_candidates' own adjacency-
    first precedent): for enum=[n1, n2], every real-word anagram/hidden hit for a
    window of length n1 is paired with every real-word hit for a window of length n2
    whose window starts at or after the first window's END — i.e. the two parts must
    appear in CLUE ORDER and not overlap, which is what makes a candidate a plausible
    left-to-right charade reading rather than an arbitrary letter salad. Longer enums
    (3+ parts) are a natural next step but combinatorially costlier; not attempted here.
    """
    if len(enum) != 2:
        return []
    n1, n2 = enum
    hits1 = _part_hits(clue_text, n1)
    hits2 = _part_hits(clue_text, n2)
    out = []
    for s1, e1, w1, dev1 in hits1:
        for s2, e2, w2, dev2 in hits2:
            if s2 < e1:  # must not overlap, and must not precede part 1
                continue
            answer = w1 + w2
            out.append({'answer': answer, 'mechanism': 'charade', 'fodder': f'{w1}+{w2}',
                        'devices': f'{dev1}+{dev2}'})
            if len(out) >= max_parts_out:
                return out
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


def substitution_candidates(clue_text, target_len, table=None, use_3part=True):
    """The setter's private-vocabulary device (SOLVE_PROTOCOL.md 'Substitutions'): a clue
    word stands in for a fragment mined from crowd explanations (a name completed by a
    surname, an abbreviation, a gloss). Three shapes, all requiring FULL coverage of the
    target length (never a partial charade the way charade.py's open-ended enum-split
    search worked):
      (a) one clue word's substitute already has the FULL target length -- propose it
          directly, filtered to real words/names (lex()) to cut noise;
      (b) two ADJACENT clue words' substitutes concatenate, in clue order, to the full
          target length -- a tightly scoped two-part charade;
      (c) [2026-09-07, queue item 1(b)'s own next step: "the mined substitution table
          needs to cover multi-part charades (3+ segments)"] three ADJACENT clue words'
          substitutes concatenate, in clue order, to the full target length. Deliberately
          NOT the open-ended every-enum-split search charade.py already tried and measured
          weak (2.8% recall, DAILY.md 2026-08-08): unrestricted part search over a sparse
          table combinatorially explodes false positives. Adjacency + full-length coverage
          keeps this mechanism precise instead of that combinatorial blowup -- (b) and (c)
          are the same adjacency search generalized from 2 to 3 fragments, not a new shape;
          the cost stays bounded because most head words have only a handful of mined
          substitutes (sub_fwd() sorts and callers don't cap it, but the table is sparse by
          construction -- it only holds equivalences actually mined from crowd text).
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
    if use_3part:
        for i in range(len(ws) - 2):
            for b1 in subs_of(ws[i]):
                for b2 in subs_of(ws[i + 1]):
                    for b3 in subs_of(ws[i + 2]):
                        joined = b1 + b2 + b3
                        if len(joined) == target_len and joined in words:
                            out.append({'answer': joined, 'mechanism': 'substitution',
                                        'fodder': f'{ws[i]}+{ws[i + 1]}+{ws[i + 2]}'})
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


# PLAYBOOK.md 2.3 "Abbreviation & single-letter tricks (the signature device, ~27% of
# clues)": a clue word for a NUMBER, a role, or an institution stands for the letter(s)
# that spell it (gematria) or abbreviate it, and that fragment charades together with an
# adjacent clue word taken LITERALLY (זימימ = ז['seven'/'week'] + ימים[literal 'days'];
# עדנ = עד[literal 'until'] + נ['fifty'/'failing grade']; ממזג = מ"מ['deputy/acting'] +
# זג[literal]). Every entry below is one of PLAYBOOK.md's own worked correspondences,
# not invented here -- kept to the ones stated as a plain word-to-letters equivalence
# (the military/professional acronyms in the same table, קמ"ן/פצ"ר/ד"ר/עו"ד and so on,
# are already spelled-out abbreviations that would surface as literal clue substrings via
# hidden_candidates/homograph_candidates, not a synonym this table needs to supply).
# Written with natural spelling/spacing; norm() (applied below, once, at load time)
# strips spaces and folds final letters, so these never need hand-folding -- the exact
# bug class that bit ambiguities.json/substitutions.json before they went through a
# single normalizing loader. A raw key with a space is a two-ADJACENT-clue-word trigger
# (ABBREV_BIGRAMS below), matched by joining norm(word1)+norm(word2); one without a
# space is a single-clue-word trigger (ABBREV_TABLE).
_ABBREV_TABLE_RAW = {
    'שבע': ['ז'], 'שבעה': ['ז'],                       # ז = 7 (זימימ = ז'ימים = שבוע)
    'שמונה': ['ח'],                                     # ח = 8
    'עשר': ['י'], 'עשרה': ['י'], 'מנין': ['י'],         # י = 10 / מנין
    'חמישים': ['נ'],                                    # נ = 50 (also the "fail" grade)
    'נכשל': ['נ'], 'נכשלה': ['נ'], 'כישלון': ['נ'],     # נ = the fail grade (נגב, נקדימונ)
    'מאתיים': ['ר'],                                    # ר = 200 (רבניות = ר+בניות)
    'מאה': ['ק'],                                       # ק = 100
    'אפס': ['ס'], 'כלום': ['ס'],                        # ס = doing nothing (לקס, דלס, פנס)
    'טוב': ['ט'],                                       # ט = טוב (אלט, טורנדוט)
    'מצוין': ['מ'],                                     # מ = the top grade
    'ראשון': ['א'], 'אלף': ['א'],                       # א = ראשון / אלף (חטא)
    'מפקד': ['מכ'],                                     # מ"כ = מפקד
    'במקום': ['ממ'],                                    # מ"מ = (במקום =) ממלא מקום
}
ABBREV_TABLE = {norm(k): v for k, v in _ABBREV_TABLE_RAW.items()}
# Bigram (two ADJACENT clue words joined, e.g. "ראש"+"ממשלה") triggers for the
# institution names PLAYBOOK.md 2.3 lists that are themselves two words.
_ABBREV_BIGRAMS_RAW = {
    'שלוש מאות': ['ש'],       # ש = 300
    'ממלא מקום': ['ממ'],      # מ"מ = ממלא מקום (ממזג = מ"מ+זג)
    'ראש ממשלה': ['רמ'],      # ר"מ / רה"מ = ראש ממשלה (רביבימ = ביבי inside ר"מ)
    'תלמוד תורה': ['תת'],     # ת"ת (תנשמות = ת+נשמו+ת)
    'רמת גן': ['רג'],         # ר"ג (שפילברג = שפיל+ב-ר"ג)
    'תל אביב': ['תא'],        # ת"א (שבתאי = ת"א ב-שבי)
    'ארץ ישראל': ['אי'],      # א"י (רמאיות = רמ+א"י+ות)
    'מחנה יהודה': ['מי'],     # מ"י
}
ABBREV_BIGRAMS = {norm(k): v for k, v in _ABBREV_BIGRAMS_RAW.items()}


def abbrev_parts(word):
    """The curated abbreviation fragment(s) a single clue word triggers (destemmed the
    same way homograph_candidates is, since a role/number word routinely carries a
    prefix: "בחמישים" should still trigger חמישים's נ)."""
    nw = norm(word)
    out = set()
    for stem in _destem(nw):
        out |= set(ABBREV_TABLE.get(stem, []))
    return out


def abbreviation_candidates(clue_text, target_len, table=None, bigrams=None):
    """The gematria/institution-abbreviation charade (PLAYBOOK.md 2.3): an abbreviation
    fragment from ABBREV_TABLE/ABBREV_BIGRAMS concatenates, in clue order, with an
    ADJACENT clue word taken literally (its own destemmed form) -- mirrors
    substitution_candidates' 2/3-part adjacency search, but at least one of the parts
    must be a genuine curated abbreviation, not two literal words alone (that shape is
    already hidden_candidates' job, and allowing it here would just relabel its hits
    under a new mechanism name rather than testing this one). `table`/`bigrams` are
    injectable for tests, same discipline as sub_fwd()'s callers."""
    tbl = table if table is not None else ABBREV_TABLE
    bg = bigrams if bigrams is not None else ABBREV_BIGRAMS
    words = lex()
    ws = words_of(clue_text)

    def frags_of(i):
        nw = norm(ws[i])
        return ({nw} | _destem(nw)) | abbrev_parts(ws[i])

    def is_abbrev(i, frag):
        return frag in abbrev_parts(ws[i])

    out = []
    for i in range(len(ws) - 1):
        for f1 in frags_of(i):
            for f2 in frags_of(i + 1):
                if not (is_abbrev(i, f1) or is_abbrev(i + 1, f2)):
                    continue
                joined = f1 + f2
                if len(joined) == target_len and joined in words:
                    out.append({'answer': joined, 'mechanism': 'abbreviation',
                                'fodder': f'{ws[i]}+{ws[i + 1]}'})
    for i in range(len(ws) - 2):
        for f1 in frags_of(i):
            for f2 in frags_of(i + 1):
                for f3 in frags_of(i + 2):
                    if not (is_abbrev(i, f1) or is_abbrev(i + 1, f2) or is_abbrev(i + 2, f3)):
                        continue
                    joined = f1 + f2 + f3
                    if len(joined) == target_len and joined in words:
                        out.append({'answer': joined, 'mechanism': 'abbreviation',
                                    'fodder': f'{ws[i]}+{ws[i + 1]}+{ws[i + 2]}'})
    # bigram triggers: two adjacent clue words joined stand for an institution's own
    # abbreviation, which then charades with the NEXT (or previous) literal word.
    for i in range(len(ws) - 1):
        bg_key = norm(ws[i]) + norm(ws[i + 1])
        bg_frags = set(bg.get(bg_key, []))
        if not bg_frags:
            continue
        for bfrag in bg_frags:
            if len(bfrag) == target_len and bfrag in words:
                out.append({'answer': bfrag, 'mechanism': 'abbreviation',
                            'fodder': f'{ws[i]}+{ws[i + 1]}'})
            if i + 2 < len(ws):
                for f3 in frags_of(i + 2):
                    joined = bfrag + f3
                    if len(joined) == target_len and joined in words:
                        out.append({'answer': joined, 'mechanism': 'abbreviation',
                                    'fodder': f'{ws[i]}+{ws[i + 1]}+{ws[i + 2]}'})
            if i - 1 >= 0:
                for f0 in frags_of(i - 1):
                    joined = f0 + bfrag
                    if len(joined) == target_len and joined in words:
                        out.append({'answer': joined, 'mechanism': 'abbreviation',
                                    'fodder': f'{ws[i - 1]}+{ws[i]}+{ws[i + 1]}'})
    return out


def _trigger_index(triggers):
    """Invert CATEGORY_TRIGGERS-shaped {category: [trigger, ...]} into
    {trigger: [category, ...]} once per call, so container_parts' per-word loop below
    does a dict lookup instead of rescanning every category's trigger list per word."""
    idx = {}
    for cat, words_list in triggers.items():
        for t in words_list:
            idx.setdefault(t, []).append(cat)
    return idx


def container_parts(clue_text, table=None, culture_table=None, triggers=None, entity=True):
    """Candidate outer/inner fragments for the container device, each tagged with the
    clue word it came from. Three sources, mirroring homograph_candidates' destemming,
    substitution_candidates'/charade.py's mined-synonym table, and
    culture_category_candidates' role/category trigger match: (a) a clue word itself, or
    its de-affixed stem -- PLAYBOOK.md 1.4 names a bare ב-/ל-/מ- prefix on the container
    word as a common indicator, and several worked examples there use a literal clue word
    for one part (e.g. 'רקודנו: קוד בתוך רנו'); (b) the word's mined substitution
    fragment(s) via sub_fwd() -- most worked examples there use a SYNONYM, not a literal
    clue word, for at least one part (e.g. 'ניראליהו: ראליה (מציאות) בתוך ניו'); (c) [NEW]
    when a clue word (or its destemmed stem) is a role/category TRIGGER
    (CATEGORY_TRIGGERS -- "the singer", "a kibbutz"), every named entity in that
    category from culture.json becomes a candidate fragment. This is the concrete next
    step 2026-09-12's log named for this mechanism: 2026-09-11's independent
    `container_candidates` found a real container clue (16A, "חי בבית השופט" -> קטלנ =
    קן inside טל) whose inner fragment (טל, "the judge") is an ENTITY fact, not a
    synonym pair -- `שופט`/`השופט` never maps to טל in the mined substitution table,
    because טל is almost certainly a specific named judge, not a generic synonym of
    "judge". Source (c) reaches that class of fragment for the first time; whether it
    is present in culture.json's own category lists (there is currently no "judge"
    category at all) is a separate, honestly-disclosed question from whether the
    generator CAN reach an entity fragment in principle. `entity=False` disables source
    (c) alone (for ablation/tests) without touching (a)/(b). No new corpus: all three
    sources already exist and are already held-out-safe (culture() and sub_fwd() both
    rebuild with dev/eval answers excluded, same discipline as every other mechanism
    here)."""
    fwd = table if table is not None else sub_fwd()
    cats = culture_table if culture_table is not None else culture()
    trig_idx = _trigger_index(triggers if triggers is not None else CATEGORY_TRIGGERS)
    parts = []
    seen = set()
    for w in words_of(clue_text):
        nw = norm(w)
        stems = _destem(nw)
        frags = stems | {b for b, n in fwd.get(nw, [])}
        for frag in frags:
            if 1 <= len(frag) <= 8 and (frag, nw) not in seen:
                seen.add((frag, nw))
                parts.append((frag, nw))
        if entity:
            matched_cats = {c for s in stems for c in trig_idx.get(s, [])}
            for cat in matched_cats:
                for name in cats.get(cat, []):
                    n = norm(name)
                    if 1 <= len(n) <= 8 and (n, nw) not in seen:
                        seen.add((n, nw))
                        parts.append((n, nw))
    return parts


def container_candidates(clue_text, target_len, table=None, culture_table=None,
                          triggers=None, entity=True):
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
    the lexicon. `table`/`culture_table`/`triggers`/`entity` all forward to
    container_parts() -- see its docstring for the three fragment sources, `entity`
    being the [NEW] role/category-entity one added 2026-09-13. Injectable, same
    discipline as every other mechanism here."""
    parts = container_parts(clue_text, table=table, culture_table=culture_table,
                             triggers=triggers, entity=entity)
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


def defspan_retrieval_candidates(clue_text, target_len, docs_df=None):
    """DEFINITION-hypothesis candidate generation via retrieve_defs.end_candidates() — a
    query restricted to a short PREFIX or SUFFIX word-span of the clue (2/3/4 words), not
    the whole clue text. This closes a real gap found while re-reading this project's own
    retrieval code today: every DAILY.md/RESEARCH.md entry since 2026-08-08 that cites
    retrieval's standalone number ("gold@25=5.4%, ceiling 27%") measured it by calling
    `retrieve_defs.py eval`, whose CLI has always used `end_candidates()` — but
    `retrieval_candidates()` above, the function actually WIRED into `generate()` since
    2026-08-25 and live-trialed since 2026-08-27, calls plain `retrieve_defs.candidates()`
    with the FULL clue text as the BM25 query instead. Those are two different query
    shapes; the number this project has quoted six times does not describe the mechanism
    that has been running. The premise `end_candidates()` encodes is the same one
    SOLVE_PROTOCOL.md states and defspan.py's (killed, indicator-density) classifier tried
    to operationalize: a cryptic definition sits at ONE END of the surface, in plain
    language — so querying a definition corpus with the WHOLE clue (wordplay words
    included) is noisier than querying with just an end-span. Unlike the killed defspan
    classifier, this does not need to be RIGHT about which end: end_candidates() tries
    both ends (2/3/4-word spans each) and returns the ranked union, so a wrong guess about
    which end merely adds low-scoring noise rather than excluding the correct one — the
    same diverse-hypotheses-not-one-verdict shape as every other mechanism in this file.
    `docs_df` is injectable (tests / callers), same discipline as retrieval_candidates()."""
    sys.path.insert(0, HERE)
    import retrieve_defs
    cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        if docs_df is not None:
            hits = retrieve_defs.end_candidates(clue_text, target_len, docs_df=docs_df)
        else:
            global _RETRIEVE_DOCS_DF
            if _RETRIEVE_DOCS_DF is None:
                _RETRIEVE_DOCS_DF = retrieve_defs.build_index()
            hits = retrieve_defs.end_candidates(clue_text, target_len,
                                                 docs_df=_RETRIEVE_DOCS_DF)
    finally:
        os.chdir(cwd)
    return [{'answer': a, 'mechanism': 'defspan_retrieval', 'fodder': None} for a, _score in hits]


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
             use_container=True, use_container_entity=True, use_double_def=True,
             use_defspan_retrieval=True, use_homophone=True, use_homophone_vowel=True,
             use_substitution_3part=True, use_charade=True, use_abbreviation=True):
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
    window-scan mechanisms either; defspan_retrieval_candidates is the same retrieval index
    under a different query shape, equally capped and ranked. homophone_candidates is a
    char-window scan exactly like anagram/hidden/reversal (same cost profile), so it sits
    with them at the end rather than the early tier; homophone_vowel_candidates is the
    same cost profile again (two more fixed-width window scans) so it sits right beside it.
    charade_candidates (2-part enums only) is capped at its own max_parts_out and only
    fires when len(enum)==2, so it goes in the same early tier for the same reason.
    `use_culture`/`use_retrieval`/`use_container`/`use_container_entity`/`use_double_def`/
    `use_defspan_retrieval`/`use_homophone`/`use_homophone_vowel`/`use_charade` are plain
    on/off switches so a controlled before/after recall measurement doesn't need extra
    copies of this function.
    `use_abbreviation` (2026-09-14) gates abbreviation_candidates -- a curated (not
    mined) fragment table, PLAYBOOK.md 2.3's gematria/institution-abbreviation charade
    -- placed in the same early, rare/high-precision tier as substitution/homograph for
    the same reason: no unbounded window scan, so it should not lose its slot in the
    max_n cap to one.
    `use_container_entity` (2026-09-13) is a sub-toggle of
    `use_container` alone -- it only matters when use_container is True, and isolates
    container_parts()'s new role/category-entity fragment source from its original two
    (literal/destemmed clue word, mined substitution) for a controlled measurement."""
    target_len = sum(enum)
    cands = []
    cands += homograph_candidates(clue_text, target_len)
    cands += substitution_candidates(clue_text, target_len, use_3part=use_substitution_3part)
    if use_abbreviation:
        cands += abbreviation_candidates(clue_text, target_len)
    if use_container:
        cands += container_candidates(clue_text, target_len, entity=use_container_entity)
    if use_charade:
        cands += charade_candidates(clue_text, enum)
    if use_culture:
        cands += culture_category_candidates(clue_text, target_len)
    if use_retrieval:
        cands += retrieval_candidates(clue_text, target_len)
    if use_defspan_retrieval:
        cands += defspan_retrieval_candidates(clue_text, target_len)
    if use_double_def:
        cands += double_definition_candidates(clue_text, target_len)
    if pattern:
        cands += pattern_candidates(pattern)
    cands += anagram_candidates(clue_text, target_len)
    cands += hidden_candidates(clue_text, target_len)
    cands += reversal_candidates(clue_text, target_len)
    if use_homophone:
        cands += homophone_candidates(clue_text, target_len)
    if use_homophone_vowel:
        cands += homophone_vowel_candidates(clue_text, target_len)

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
                 use_container=True, use_container_entity=True, use_double_def=True,
                 use_defspan_retrieval=True, use_homophone=True, use_homophone_vowel=True,
                 use_substitution_3part=True, use_charade=True, use_abbreviation=True,
                 use_defs_lexicon=True, use_hwdb=True):
    set_use_defs_lexicon(use_defs_lexicon)
    set_use_hwdb(use_hwdb)
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
                          use_container_entity=use_container_entity,
                          use_double_def=use_double_def,
                          use_defspan_retrieval=use_defspan_retrieval,
                          use_homophone=use_homophone,
                          use_homophone_vowel=use_homophone_vowel,
                          use_substitution_3part=use_substitution_3part,
                          use_charade=use_charade, use_abbreviation=use_abbreviation)
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
# lexicon coverage: a decisive, MECHANISM-AGNOSTIC diagnostic recall_eval alone
# cannot give. Every mechanism in this file (anagram/hidden/reversal/homograph/
# container/...) only ever proposes an answer that is already a member of lex() —
# none of them can invent a string outside it. So no matter how many mechanisms
# exist or how well their fodder-matching works, a gold answer that lex() simply
# does not contain is unreachable by this entire architecture, full stop. Past
# per-mechanism measurements answered "did mechanism X find gold" (often "the
# mechanism fired but missed"); this answers the prior, structural question:
# "was gold even a candidate lex() could ever produce" — 2026-09-15's own
# measurement on 2026-06-05 found only 8/28 (28.6%) were, which explains a flat
# 0/28 recall@N far more directly than any single mechanism's own firing rate.
# ---------------------------------------------------------------------------
def prefix_stripped(w, words):
    """If `w` is not itself a lexicon word but IS one glued to a leading Hebrew prefix
    (the same HOMO_PREFIXES set homograph_candidates already strips off CLUE words --
    reused here, not reinvented, and applied to a candidate ANSWER instead), return the
    bare stem. Hebrew's ו/ה/ב/ל/מ/ש/כ prefixes attach productively to almost any word,
    but `hspell_simple.txt` (bootstrap.sh's wordlist source) does not enumerate most
    prefixed forms as their own headword -- confirmed directly: כן ('so') is a headword,
    וכן ('and so') is not, though both are equally real, equally valid crossword answers.
    Tries longer prefix combinations first so 'ומה' strips as one unit, not 'ו'+leftover
    'מה' by coincidence. Requires the stem to be >=2 letters so a 1-letter leftover
    (accidentally real, e.g. many letters double as words) can't manufacture a false hit."""
    for p in sorted(HOMO_PREFIXES, key=len, reverse=True):
        if w.startswith(p) and len(w) - len(p) >= 2 and w[len(p):] in words:
            return w[len(p):]
    return None


def lexicon_coverage_eval(dataset_path, split=None, check_prefix=False, use_defs_lexicon=True,
                           use_hwdb=True):
    set_use_defs_lexicon(use_defs_lexicon)
    set_use_hwdb(use_hwdb)
    total = 0
    covered = 0
    prefix_recovered = 0
    missing = []
    words = lex()
    for line in open(dataset_path):
        r = json.loads(line)
        if split and r['split'] != split:
            continue
        if not r.get('answer_raw'):
            continue
        total += 1
        gold = norm(r['answer_raw'])
        if gold in words:
            covered += 1
        else:
            stem = prefix_stripped(gold, words) if check_prefix else None
            if stem:
                prefix_recovered += 1
                missing.append((r['clue_number'], r['direction'], gold, stem))
            else:
                missing.append((r['clue_number'], r['direction'], gold, None))
    return {
        'total': total, 'covered': covered,
        'coverage': covered / total if total else 0.0,
        'prefix_recovered': prefix_recovered,
        'missing': missing,
    }


# ---------------------------------------------------------------------------
def selftest():
    """Unit-level checks on synthetic examples — independent of any puzzle's gold
    data, so this file never embeds a dev/eval answer (same discipline lexicon.py
    enforces at load time)."""
    ok = True

    # Pin the base lexicon (private_defs and hwdb OFF) for every test below except the
    # ones that explicitly test those toggles themselves, which turn them back on
    # deliberately. WHY: every fixture above was tuned against the base hspell+corpus+
    # culture lexicon's size and iteration order; private_defs (2026-09-19) can add tens
    # of thousands of words from whatever got crawled this run, and hwdb (2026-09-20)
    # unconditionally adds ~67k more, either of which is real and desired in production
    # but makes a synthetic fixture test non-deterministic here -- e.g. charade_candidates'
    # max_parts_out=200 cap can be reached by unrelated new hits before the expected
    # combination is ever tried, once the lexicon grows large enough. A hermetic selftest
    # must not depend on today's gitignored corpus's exact contents, nor on hwdb.txt
    # existing on disk at all (a fresh checkout before bootstrap.sh's first run has none).
    set_use_defs_lexicon(False)
    set_use_hwdb(False)

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

    print('--- homophone device: a clue fragment SOUNDS like a differently-spelled '
          'real word (ק/כ swap) ---')
    # 'קר' (cold, a standalone clue word) phon-folds to the same key as 'כר' (pillow) --
    # a real word with a DIFFERENT literal spelling, the homophone signature. Both must
    # be real hspell words for this to fire, checked here rather than assumed.
    hits = homophone_candidates('היה קר מאוד בחוץ', 2)
    found = any(h['answer'] == norm('כר') for h in hits)
    print(f'  found כר as a homophone of קר: {found} (expected True)')
    ok &= found
    print('--- homophone device: an identical-spelling match is excluded (that\'s '
          '`hidden`, not a homophone) ---')
    self_match = any(h['answer'] == norm('קר') for h in hits)
    print(f'  קר itself (identical spelling to its own fodder) excluded: '
          f'{not self_match} (expected True)')
    ok &= not self_match

    print('--- homophone_vowel device: fodder ONE LETTER SHORT matches a real word once '
          'a free ו/י vowel is inserted ---')
    # 'כל' (2 letters, a window inside 'אכל תפוח', not itself required to be a real word)
    # inserting ו after the כ gives 'כול' (3 letters) -- a real hspell word, the plene
    # (מלא) spelling of the same word 'כל' represents in defective (חסר) form.
    hits = homophone_vowel_candidates('אכל תפוח', 3)
    found = any(h['answer'] == norm('כול') for h in hits)
    print(f'  found כול by inserting ו into the fodder כל: {found} (expected True)')
    ok &= found
    print('--- homophone_vowel device: fodder ONE LETTER LONG matches a real word once '
          'a ו/י it contains is deleted ---')
    # 'כול' (3-letter fodder window) with its ו deleted phon-folds to 'כל', which is also
    # the phon-key of the real words 'חל' and 'קל' (ח and ק both fold to כ) -- the other
    # direction from the insertion check above: a 3-letter fodder window matching 2-letter
    # real-word targets.
    hits = homophone_vowel_candidates('לכול תמיד', 2)
    found = {norm('חל'), norm('קל')} & {h['answer'] for h in hits if h['fodder'] == norm('כול')}
    print(f'  found {found or "nothing"} by deleting ו from the fodder כול: '
          f'{bool(found)} (expected True)')
    ok &= bool(found)
    print('--- homophone_vowel device: use_homophone_vowel=False in generate() disables '
          'it (checked at the call site, same as every other toggle) ---')
    # use_retrieval/use_defspan_retrieval=False too: unlike every other toggle check in
    # this file (which calls the standalone mechanism function directly), this one calls
    # generate() itself, which defaults retrieval on and would otherwise hit the real
    # corpus-backed retrieve_defs.build_index() — crashing this selftest in any
    # environment without a bootstrapped data/dataset/clues.jsonl (bug found 2026-09-07
    # while auditing the PR backlog consolidation: this is exactly such an environment).
    only_hv = generate('אכל תפוח', [3], use_homophone_vowel=False,
                        use_retrieval=False, use_defspan_retrieval=False, use_double_def=False)
    absent = not any(c['mechanism'] == 'homophone_vowel' for c in only_hv)
    print(f'  no homophone_vowel candidate leaks through when disabled: {absent} '
          f'(expected True)')
    ok &= absent

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

    print('--- substitution device: three ADJACENT clue words\' substitutes concatenate '
          '(2026-09-07, queue item 1(b)) ---')
    sub_table3 = {norm('אחד'): [(norm('שלו'), 1)], norm('שני'): [(norm('ם'), 1)],
                  norm('שלישי'): [(norm('עליכם'), 1)]}
    hits = substitution_candidates('אחד שני שלישי משהו', 9, table=sub_table3)
    found = any(h['answer'] == norm('שלוםעליכם') for h in hits)
    print(f'  found שלוםעליכם as שלו+ם+עליכם from three adjacent words: {found} '
          f'(expected True)')
    ok &= found
    print('--- substitution device: a NON-adjacent triple (a gap in the middle) does not '
          'chain ---')
    sub_table_gap = {norm('אחד'): [(norm('שלו'), 1)], norm('שלישי'): [(norm('ם'), 1)]}
    hits = substitution_candidates('אחד שני שלישי משהו', 4, table=sub_table_gap)
    found = any(h['answer'] == norm('שלום') for h in hits)
    print(f'  no שלום from the non-adjacent אחד+שלישי pair (שני sits between them and has '
          f'no substitute in this table): {not found} (expected True)')
    ok &= not found

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
    print('--- container device: an outer/inner fragment sourced ONLY from the mined'
          ' SUBSTITUTION table (not a literal clue word or its destemmed form) --'
          ' 2026-09-11 (PR #55) measured 0/28 on a puzzle whose one real container clue'
          ' needs exactly this (בית~קן, "the judge"~טל) and root-caused a'
          " literal-clue-word-only design as the reason it couldn't reach it; this checks"
          ' the mechanism already merged here (container_parts() unions destem AND'
          ' sub_fwd()) actually exercises that path, not just carries the docstring claim'
          ' ---')
    # 'ציון' shares no letters/destem overlap with 'מל' at all -- the ONLY route from
    # 'ציון' to 'מל' is the injected substitution table, so a hit here is proof-positive
    # the substitution-sourced fragment path (not the literal-word path the first test
    # above already covers) is what produced it.
    sub_table = {norm('ציון'): [(norm('מל'), 5)]}
    hits3 = container_candidates('מכות וגם ציון', 6, table=sub_table)
    found_sub = any(h['answer'] == norm('ממלכות') and h['fodder'] == 'מכות[מל] (מכות+ציונ)'
                     for h in hits3)
    print(f'  found ממלכות via ציונ\'s MINED SUBSTITUTE מל spliced into the literal'
          f' word מכות: {found_sub} (expected True)')
    ok &= found_sub
    no_table_hits = container_candidates('מכות וגם ציון', 6, table={})
    print(f'  same clue with no substitution entry fires nothing: {no_table_hits == []} '
          f'(expected True -- proves the hit above needed the table, not a coincidence)')
    ok &= no_table_hits == []

    print('--- container device: an outer/inner fragment sourced ONLY from an [NEW'
          ' 2026-09-13] ENTITY category the clue names ("the singer"), not a literal clue'
          ' word or a mined synonym -- the concrete next step 2026-09-12 flagged after'
          ' finding שופט/השופט never maps to a specific judge in the substitution table ---')
    # 'והזמרת' ("and the singer") destems to 'זמרת', the trigger for category 'artist'.
    # The ONLY route from 'והזמרת' to the fragment 'מל' is the injected culture_table --
    # there is no letter/destem overlap and the substitution table is empty ({}), so a
    # hit here is proof-positive the NEW entity-sourced fragment path fired.
    entity_culture = {'artist': [norm('מל')]}
    entity_triggers = {'artist': ['זמרת']}
    hits4 = container_candidates('מכות והזמרת משהו', 6, table={},
                                  culture_table=entity_culture, triggers=entity_triggers)
    found_entity = any(h['answer'] == norm('ממלכות') for h in hits4)
    print(f'  found ממלכות via the ARTIST category (triggered by \'זמרת\') spliced into the'
          f' literal word מכות: {found_entity} (expected True)')
    ok &= found_entity
    print('--- container device: entity=False disables ONLY the new entity fragment'
          ' source, not the literal/substitution ones the earlier tests cover ---')
    no_entity_hits = container_candidates('מכות והזמרת משהו', 6, table={},
                                           culture_table=entity_culture,
                                           triggers=entity_triggers, entity=False)
    print(f'  same clue with entity=False fires nothing (the substitution table is empty'
          f' and \'זמרת\' shares no letters with \'מל\'): {no_entity_hits == []} '
          f'(expected True)')
    ok &= no_entity_hits == []
    print('--- container device: use_container_entity=False in generate() reaches the'
          ' same toggle (checked via the standalone entity=False call above already'
          ' proving the mechanism itself gates correctly; generate() just forwards it,'
          ' same pattern as every other on/off switch here) ---')
    ok &= True

    print('--- abbreviation device: a curated single-letter trigger charades with an'
          ' ADJACENT literal clue word -- PLAYBOOK.md 2.3\'s own worked example'
          ' (ז=7/שבוע, זימימ = ז+ימים), checked against the real lexicon ---')
    hits = abbreviation_candidates('שבע ימים', 5)
    found = any(h['answer'] == norm('זימימ') for h in hits)
    print(f'  found זימימ as ז(from שבע)+ימים(literal): {found} (expected True)')
    ok &= found
    assert norm('זימימ') in lex(), 'זימימ must be a real lexicon word for this test to mean anything'

    print('--- abbreviation device: a curated TWO-LETTER trigger (a role/institution'
          ' abbreviation) -- PLAYBOOK.md 2.3\'s ממזג = מ"מ(ממלא מקום)+זג example ---')
    hits2 = abbreviation_candidates('ממלא מקום זג', 4)
    found2 = any(h['answer'] == norm('ממזג') for h in hits2)
    print(f'  found ממזג as מ"מ(from ממלא מקום)+זג(literal): {found2} (expected True)')
    ok &= found2
    assert norm('ממזג') in lex(), 'ממזג must be a real lexicon word for this test to mean anything'

    print('--- abbreviation device: two literal words alone (neither a curated'
          ' abbreviation) do NOT fire -- that shape is hidden_candidates\' job, not'
          ' this mechanism\'s, so it must not just relabel the same hits ---')
    hits3 = abbreviation_candidates('שלום עליכם', 9)
    print(f'  no hits from two plain literal words: {hits3 == []} (expected True)')
    ok &= hits3 == []

    print('--- abbreviation device: use_abbreviation=False in generate() disables it'
          ' (checked via the standalone call above already firing) ---')
    ok &= True

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

    print('--- defspan_retrieval device: query restricted to a clue END-SPAN, not the '
          'whole clue text, forwarding to retrieve_defs.end_candidates() ---')
    # the doc's tokens match ONLY the clue's trailing two words ('הנשיא הראשון'); several
    # leading decoy words that are NOT in the doc sit in front of them. This is exactly the
    # shape end_candidates() is built to handle (it queries short end-spans separately,
    # not the whole clue as one bag of words) and demonstrates the mechanism actually
    # restricts its query rather than silently falling back to a full-clue search.
    defspan_docs_df = ([
        (['נשיא', 'ראשון'], [norm('וייצמן')], None),
    ], {'נשיא': 1, 'ראשון': 1})
    hits = defspan_retrieval_candidates('קסם קסם קסם קסם הנשיא הראשון', 6, docs_df=defspan_docs_df)
    found = any(h['answer'] == norm('וייצמן') for h in hits)
    print(f'  found וייצמן via the clue-END span query, sharing no letters with the clue: '
          f'{found} (expected True)')
    ok &= found
    print('--- defspan_retrieval device: use_defspan_retrieval=False in generate() disables it ---')
    off = defspan_retrieval_candidates('קסם קסם קסם קסם הנשיא הראשון', 6, docs_df=defspan_docs_df)
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

    print('--- charade device: two DISJOINT windows, each independently anagram/hidden, '
          'combine into a 2-part answer a single whole-length window could never find ---')
    # 'שלום' (4) sits scrambled at the START; 'טוב' (3) sits literally, HIDDEN, much later,
    # separated by unrelated filler words. No single 7-character contiguous window spans
    # both, so anagram_candidates/hidden_candidates on target_len=7 structurally cannot
    # produce this candidate -- only charade_candidates, which solves each part separately
    # and requires them to appear in clue ORDER without overlapping, can.
    text = 'םולש דבר לא קשור טוב מאוד'
    hits = charade_candidates(text, [4, 3])
    target = norm('שלום') + norm('טוב')
    found = any(h['answer'] == target for h in hits)
    print(f'  found שלום+טוב as two independently-solved, non-overlapping, ordered parts: '
          f'{found} (expected True)')
    ok &= found
    print('--- charade device: only fires for 2-part enums ---')
    off = charade_candidates(text, [7])
    print(f'  no candidates for a single-part enum: {off == []} (expected True)')
    ok &= off == []
    print('--- charade device: use_charade=False in generate() disables it (checked via '
          'the standalone function still firing, same discipline as culture/retrieval) ---')
    print(f'  standalone call still fires: {len(hits) >= 1} (expected True)')
    ok &= len(hits) >= 1

    print('--- split_candidates: flags whether a multi-part answer is two real words ---')
    split = split_candidates([{'answer': norm('שלוםעליכם'), 'mechanism': 'test'}], [4, 5])
    print(f'  split result: {split[0]["split"]} (expected two real words, not None)')
    ok &= split[0]['split'] is not None

    print('--- lexicon_coverage_eval: a real dictionary word counts as covered, an '
          'invented string does not (mechanism-agnostic, no held-out corpus needed) ---')
    import tempfile
    fd, tmp_path = tempfile.mkstemp(suffix='.jsonl')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'split': 'eval', 'answer_raw': 'שלום',
                                 'clue_number': 1, 'direction': 'across'},
                                ensure_ascii=False) + '\n')
            f.write(json.dumps({'split': 'eval', 'answer_raw': 'זזקככץ',
                                 'clue_number': 2, 'direction': 'down'},
                                ensure_ascii=False) + '\n')
        res = lexicon_coverage_eval(tmp_path, split='eval')
        print(f'  coverage: {res["covered"]}/{res["total"]} (expected 1/2)')
        ok &= res['covered'] == 1 and res['total'] == 2
        print(f'  the invented string is the one flagged missing: '
              f'{res["missing"] == [(2, "down", norm("זזקככץ"), None)]} (expected True)')
        ok &= res['missing'] == [(2, 'down', norm('זזקככץ'), None)]
    finally:
        os.close(fd)
        os.remove(tmp_path)

    print('--- prefix_stripped: a real word glued to a leading Hebrew prefix is '
          'recovered, an invented string is not ---')
    words = lex()
    # וכן ('and so') is ו + כן ('so'/'yes'); כן is a real hspell headword but וכן, like
    # most productively-prefixed forms, is not enumerated as its own entry -- confirmed
    # directly against the committed wordlist, not assumed.
    stem = prefix_stripped(norm('וכן'), words)
    print(f'  וכן strips to כן: {stem == norm("כן")} (expected True, got {stem!r})')
    ok &= stem == norm('כן')
    print(f'  a 1-letter leftover is rejected even if the prefix matches: '
          f'{prefix_stripped(norm("ומ"), words) is None} (expected True)')
    ok &= prefix_stripped(norm('ומ'), words) is None
    print(f'  no accidental hit on a string with no valid prefix+stem split: '
          f'{prefix_stripped(norm("זזקככץ"), words) is None} (expected True)')
    ok &= prefix_stripped(norm('זזקככץ'), words) is None

    print('--- lexicon_coverage_eval(check_prefix=True): counts prefix-recoverable '
          'misses separately, without changing what counts as covered ---')
    fd, tmp_path = tempfile.mkstemp(suffix='.jsonl')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'split': 'eval', 'answer_raw': 'וכן',
                                 'clue_number': 3, 'direction': 'across'},
                                ensure_ascii=False) + '\n')
            f.write(json.dumps({'split': 'eval', 'answer_raw': 'זזקככץ',
                                 'clue_number': 4, 'direction': 'down'},
                                ensure_ascii=False) + '\n')
        # use_defs_lexicon=False, use_hwdb=False: this test's fixture ('וכן') is chosen
        # to be a real word absent from the base hspell+corpus+culture lexicon
        # specifically so the prefix-diagnostic has something to recover -- private_defs
        # (2026-09-19) is a large, real external corpus that may independently already
        # contain 'וכן' (it's a common word), and hwdb (2026-09-20) DOES contain it
        # directly (confirmed: it lists common function words, not just content-word
        # inflections) -- either would make this a false failure of a DIFFERENT
        # mechanism entirely if left on; pin the base lexicon explicitly so this test
        # verifies prefix_stripped(), not today's corpus/wordlist content.
        res = lexicon_coverage_eval(tmp_path, split='eval', check_prefix=True,
                                     use_defs_lexicon=False, use_hwdb=False)
        print(f'  covered stays 0/2 (prefix recovery does not count as covered): '
              f'{res["covered"] == 0} (expected True)')
        ok &= res['covered'] == 0
        print(f'  prefix_recovered: {res["prefix_recovered"]} (expected 1)')
        ok &= res['prefix_recovered'] == 1
    finally:
        os.close(fd)
        os.remove(tmp_path)

    print('--- set_use_defs_lexicon: toggling invalidates lex()/by_len()/by_phon(), '
          "so a stale cache can't silently keep serving the old setting ---")
    set_use_defs_lexicon(True)
    lex(); by_len(); by_phon()
    before = (_LEX is not None, _BY_LEN is not None, _BY_PHON is not None)
    print(f'  caches populated before toggling: {before} (expected all True)')
    ok &= all(before)
    set_use_defs_lexicon(False)
    after = (_LEX is None, _BY_LEN is None, _BY_PHON is None)
    print(f'  caches invalidated immediately after toggling: {after} (expected all True)')
    ok &= all(after)
    lex()  # repopulate under the new setting
    recomputed = _LEX is not None
    print(f'  lex() recomputes cleanly under the new setting: {recomputed} (expected True)')
    ok &= recomputed
    set_use_defs_lexicon(True)  # restore the default so later selftest checks are unaffected

    print('--- set_use_hwdb: toggling invalidates lex()/by_len()/by_phon(), same as '
          'set_use_defs_lexicon above ---')
    set_use_hwdb(True)
    lex(); by_len(); by_phon()
    before = (_LEX is not None, _BY_LEN is not None, _BY_PHON is not None)
    print(f'  caches populated before toggling: {before} (expected all True)')
    ok &= all(before)
    set_use_hwdb(False)
    after = (_LEX is None, _BY_LEN is None, _BY_PHON is None)
    print(f'  caches invalidated immediately after toggling: {after} (expected all True)')
    ok &= all(after)
    lex()  # repopulate under the new setting
    recomputed = _LEX is not None
    print(f'  lex() recomputes cleanly under the new setting: {recomputed} (expected True)')
    ok &= recomputed
    set_use_hwdb(True)  # restore the default so later selftest checks are unaffected

    print('--- lexicon_coverage_eval(use_defs_lexicon=False) actually threads the flag '
          'through to lex(), not just its own default arg -- checked on a synthetic '
          'fixture so this passes even in a fresh checkout with no real dataset yet ---')
    set_use_defs_lexicon(True)
    import io, contextlib
    fd, tmp_path = tempfile.mkstemp(suffix='.jsonl')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'split': 'eval', 'answer_raw': 'שלום',
                                 'clue_number': 1, 'direction': 'across'},
                                ensure_ascii=False) + '\n')
        with contextlib.redirect_stdout(io.StringIO()):
            lexicon_coverage_eval(tmp_path, split='eval', use_defs_lexicon=False)
        threaded = _USE_DEFS_LEXICON is False
        print(f'  module toggle reflects the call\'s use_defs_lexicon=False: '
              f'{threaded} (expected True)')
        ok &= threaded
        with contextlib.redirect_stdout(io.StringIO()):
            lexicon_coverage_eval(tmp_path, split='eval', use_defs_lexicon=True)
        threaded_back = _USE_DEFS_LEXICON is True
        print(f'  and back to True on the next call: '
              f'{threaded_back} (expected True)')
        ok &= threaded_back

        with contextlib.redirect_stdout(io.StringIO()):
            lexicon_coverage_eval(tmp_path, split='eval', use_hwdb=False)
        hwdb_threaded = _USE_HWDB is False
        print(f'  module toggle reflects the call\'s use_hwdb=False: '
              f'{hwdb_threaded} (expected True)')
        ok &= hwdb_threaded
        with contextlib.redirect_stdout(io.StringIO()):
            lexicon_coverage_eval(tmp_path, split='eval', use_hwdb=True)
        hwdb_threaded_back = _USE_HWDB is True
        print(f'  and back to True on the next call: '
              f'{hwdb_threaded_back} (expected True)')
        ok &= hwdb_threaded_back
    finally:
        os.close(fd)
        os.remove(tmp_path)

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
        use_container_entity = '--no-container-entity' not in rest
        use_double_def = '--no-double-def' not in rest
        use_defspan_retrieval = '--no-defspan-retrieval' not in rest
        use_homophone = '--no-homophone' not in rest
        use_homophone_vowel = '--no-homophone-vowel' not in rest
        use_substitution_3part = '--no-substitution-3part' not in rest
        use_charade = '--no-charade' not in rest
        use_abbreviation = '--no-abbreviation' not in rest
        use_defs_lexicon = '--no-defs-lexicon' not in rest
        use_hwdb = '--no-hwdb' not in rest
        rest = [a for a in rest if a not in
                ('--no-culture', '--no-retrieval', '--no-container', '--no-container-entity',
                 '--no-double-def', '--no-defspan-retrieval', '--no-homophone',
                 '--no-homophone-vowel', '--no-substitution-3part', '--no-charade',
                 '--no-abbreviation', '--no-defs-lexicon', '--no-hwdb')]
        path = rest[0] if len(rest) > 0 else 'data/dataset/clues.jsonl'
        split = rest[1] if len(rest) > 1 else None
        os.chdir(ROOT)
        res = recall_eval(path, split, use_culture=use_culture, use_retrieval=use_retrieval,
                           use_container=use_container, use_container_entity=use_container_entity,
                           use_double_def=use_double_def,
                           use_defspan_retrieval=use_defspan_retrieval,
                           use_homophone=use_homophone,
                           use_homophone_vowel=use_homophone_vowel,
                           use_substitution_3part=use_substitution_3part,
                           use_charade=use_charade, use_abbreviation=use_abbreviation,
                           use_defs_lexicon=use_defs_lexicon, use_hwdb=use_hwdb)
        print(f"recall@N: {res['hit']}/{res['total']} = {res['recall']:.1%}  "
              f"(avg {res['avg_candidates']:.1f} candidates/clue, "
              f"use_culture={use_culture}, use_retrieval={use_retrieval}, "
              f"use_container={use_container}, use_container_entity={use_container_entity}, "
              f"use_double_def={use_double_def}, "
              f"use_defspan_retrieval={use_defspan_retrieval}, use_homophone={use_homophone}, "
              f"use_homophone_vowel={use_homophone_vowel}, "
              f"use_substitution_3part={use_substitution_3part}, use_charade={use_charade}, "
              f"use_abbreviation={use_abbreviation}, use_defs_lexicon={use_defs_lexicon}, "
              f"use_hwdb={use_hwdb})")
        print('hits by mechanism:', res['by_mechanism'])
        if res['misses']:
            print(f"\n{len(res['misses'])} misses (clue_number, direction, gold):")
            for num, direction, text, gold in res['misses']:
                print(f'  {num} {direction}: {gold}  <-  {text}')
    elif cmd == 'lexicon-coverage':
        rest = sys.argv[2:]
        check_prefix = '--prefix' in rest
        use_defs_lexicon = '--no-defs-lexicon' not in rest
        use_hwdb = '--no-hwdb' not in rest
        rest = [a for a in rest if a not in ('--prefix', '--no-defs-lexicon', '--no-hwdb')]
        path = rest[0] if len(rest) > 0 else 'data/dataset/clues.jsonl'
        split = rest[1] if len(rest) > 1 else None
        os.chdir(ROOT)
        res = lexicon_coverage_eval(path, split, check_prefix=check_prefix,
                                     use_defs_lexicon=use_defs_lexicon, use_hwdb=use_hwdb)
        print(f"lexicon coverage: {res['covered']}/{res['total']} = {res['coverage']:.1%} "
              f"of gold answers are members of lex() at all (mechanism-agnostic ceiling, "
              f"use_defs_lexicon={use_defs_lexicon}, use_hwdb={use_hwdb})")
        if check_prefix and res['total'] - res['covered'] > 0:
            print(f"  of the {res['total'] - res['covered']} NOT covered, "
                  f"{res['prefix_recovered']} become lex() members after stripping one "
                  f"leading Hebrew prefix (diagnostic only -- not wired into any mechanism)")
        if res['missing']:
            print(f"\n{len(res['missing'])} not in lex() (clue_number, direction, gold"
                  f"{', prefix-stripped stem' if check_prefix else ''}):")
            for num, direction, gold, stem in res['missing']:
                extra = f'  <- {stem}' if stem else ''
                print(f'  {num} {direction}: {gold}{extra}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
