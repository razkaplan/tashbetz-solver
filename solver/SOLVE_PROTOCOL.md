# Solver Protocol v1

Input per puzzle: clue list (number, direction, text, enum). No answers, no 14across access.
Output: solutions JSON: [{puzzle_date, clue_number, direction, answer, explanation, confidence}]

## Method

1. **First pass — classify each clue** by likely mechanism using the playbook indicators
   (see PLAYBOOK.md): anagram, reversal, container, double-definition, charade, pun-definition,
   culture-reference. A clue can have 2 candidate mechanisms.
2. **Candidate generation per mechanism:**
   - The enumeration constrains total letters exactly (finals count as regular letters).
   - anagram: find fodder substring in the clue with exactly matching letter count; rearrange
     to a real Hebrew word/phrase.
   - reversal: indicator להפך / חוזר / מימין; reverse a clue word or its synonym.
   - container: X בתוך Y phrasing; assemble.
   - double definition: one word answering both halves of the clue.
   - charade: split enum parts; solve each part from clue fragments (synonyms, names).
   - culture reference: Israeli politics, Bible, classic Hebrew songs are the setter's staples.
     NOTE: a (עפ"י <name>) credit at the end of a clue is the CONTRIBUTOR's name (a reader who
     sent the clue in) — it is NOT part of the wordplay. Exception: "עפ"י השמיעה של X" marks a
     homophone. See PLAYBOOK.md for the full empirical rules.
3. **Self-check before answering:** the answer must (a) match enum lengths exactly,
   (b) be a real Hebrew word/phrase/name, (c) have a full wordplay account — every letter
   justified — AND a definition/pun account of the remaining clue surface. If you cannot
   justify every letter, lower confidence and reconsider mechanism.
4. **Cross-letter pass (v2+, when grid available):** iterative propagation rounds —
   (a) fill only high-confidence answers into the grid (one letter per white cell, dark
   cells stay empty; any crossing conflict means one of the answers is wrong — resolve by
   confidence and wordplay strength before locking);
   (b) next, attempt the unsolved clue with the HIGHEST fraction of known crossing letters,
   using the pattern (e.g. ?ו?ר??) as a hard filter on candidates;
   (c) repeat until a full round adds nothing. A locked letter that contradicts a tempting
   candidate is evidence the candidate is wrong — trust the grid.
5. **Explanation format:** one line, in the crowd style: e.g. "אנגרם טרמפ שלילי",
   "טומי (לפיד) ב-אנה(זק)", "מילה משותפת", "להפך פינו קיר".

## Tools (v3) — use these instead of guessing
- `python3 solver/lexicon.py pattern '?ו?ר??'` — real Hebrew words (hspell + corpus)
  matching a crossing pattern (?=unknown), exact length. Use the moment crossings give
  you >=2 letters — the answer is almost always in this list.
- `python3 solver/lexicon.py anagram <letters>` — real words that anagram the fodder.
  Run this on every candidate anagram fodder window; a hit is near-proof.
- `python3 solver/lexicon.py contains <sub> <len>` / `sub <substr>` — words containing a
  known fragment (for container/charade assembly).
- `python3 solver/retrieve.py "<clue text>" 8` — most similar SOLVED train clues with their
  answers + crowd explanations; use them to identify the mechanism and imitate the reasoning.

Loop: classify → generate candidates (lexicon/anagram) → fill high-confidence into grid →
fill_state.py → for each remaining clue, `lexicon.py pattern` on its ?-pattern → pick the
candidate whose wordplay you can fully justify. Repeat until no clue gains letters.

CONFIDENCE DISCIPLINE (critical — a wrong high-confidence anchor poisons the whole grid):
- An anagram/word merely EXISTING is NOT evidence it is the answer. Multi-word answers have
  many letter-orderings that each form real words (e.g. יש פרחים vs פרחים יש). The lexicon
  tells you a candidate is *possible*, never that it is *correct*.
- Assign confidence >=0.7 (grid-anchoring level) ONLY when BOTH hold: (a) the definition part
  of the clue clearly maps to the answer's meaning, AND (b) it agrees with every crossing
  letter already on the board. Wordplay-fit alone caps confidence at ~0.4.
- Prefer solving the definition first; use wordplay/lexicon to CONFIRM, not to originate.
- When a fresh candidate conflicts with an existing anchor, suspect the ANCHOR too — re-derive
  it; do not blindly keep the earlier one just because it came first.

## Hard rules
- Never consult 14across.co.il or any answers site. Web lookups for cultural facts
  (song lyrics, politician names) are allowed; searching the clue text verbatim is NOT.
- Answer in unspaced form (as grid letters), e.g. שלומעלישראל. The grid NEVER uses final
  letter forms (ם/ן/ץ/ף/ך -> מ/נ/צ/פ/כ everywhere, including word-final position).
- Try the mechanical anagram detector first: a contiguous run of clue words whose letter
  multiset (finals normalized) equals the enum total is almost certainly anagram fodder.
