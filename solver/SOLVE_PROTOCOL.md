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
- `python3 solver/wiki.py search|summary|whois|links "<entity>"` — Hebrew Wikipedia facts.
  THE tool for culture clues: who sang X, a politician's real name/nickname, a place, a Bible
  figure. Query the ENTITY, never the clue text.
- The lexicon now also contains ~4,800 culture entities from he-wikipedia (1,794 song titles,
  1,799 artists, 998 politicians, 239 places). So `lexicon.py pattern` on a crossing pattern can
  surface a SONG TITLE or a PERSON'S NAME directly — always run it on long unsolved slots, which
  are exactly where the culture showpieces live.

## PRECISION FIRST (v10) — a blank beats a wrong answer
Policy from the project owner, and the highest-priority rule here. A wrong answer is worse
than no answer: it scores zero AND writes wrong letters into every crossing slot, corrupting
clues you would otherwise have solved. Blank is recoverable. Wrong is contagious.

Every answer you output carries a `tier`:
- `"committed"` — you are prepared to assert this is correct. Requires BOTH: the definition
  clearly fits, AND every letter is accounted for by a stated mechanism, AND nothing
  contradicts a crossing. Only committed answers are propagated onto the grid.
- `"suggestion"` — plausible, unverified. Recorded for a human or a later pass. NEVER
  propagated as a crossing constraint. Use this freely; it costs nothing.
- `"blank"` — leave `answer` empty. Use when you have nothing you would defend.

Do NOT pad. Do NOT invent a plausible-looking string to fill a slot. If the only thing you
have is "a word of the right length", that is a `suggestion` at best, more likely a `blank`.

You are scored on:
  PRECISION = correct committed / all committed   <- the number that matters most
  COVERAGE  = committed / all clues
  YIELD     = correct committed / all clues       <- accurate fulfilment
A run that commits 12 and gets 12 right beats a run that answers 28 and gets 15.
Target: precision >= 95%, then push coverage up without losing precision.

## PROOF GATE (v16) — a commit must EXECUTE, not merely persuade
Method adapted from the current SOTA on English cryptics (formalise wordplay as code,
verify by execution). Every previous verifier here was an LLM judging plausibility, and
plausibility is exactly what re-committed a wrong answer three times with three different
convincing justifications. An assertion either runs or it does not.

BEFORE COMMITTING any answer, write its wordplay as assertions and run them:

  python3 solver/prove.py check "
  assert is_anagram('משפר חיי', 'ישפרחימ')
  assert word_order('ישפרחימ', 'יש', 'פרחים')
  assert has_length('ישפרחימ', 2, 5)
  " --answer ישפרחימ

Exit code 0 = PROVED, commit permitted. Non-zero = the proof failed and prints WHY;
either repair the derivation or downgrade to suggestion. Available assertions:
  is_anagram(fodder, answer)      is_reversal(src, answer)
  is_container(outer, inner, ans) is_hidden(text, answer)
  means(phrase, target)           <- grounded in the setters' own 3,141 substitutions;
                                     an invented synonym FAILS here, by design
  word_order(answer, w1, w2, ...) <- catches right-letters-wrong-order, our worst error class
  has_length(answer, *enum)       is_word(w)   concat(*parts)

Rules:
- A multi-word answer REQUIRES a passing `word_order` assertion.
- If you cannot express the wordplay as assertions at all, you do not understand the clue
  well enough to commit it. That is information, not an obstacle.
- `means` failing tells you the substitution is not one these setters use. Do not work
  around it by rewording; find the reading they actually intended.

## Self-flag your weakest commit (v15) — nearly free precision
At the end of a run, name the ONE committed answer you would bet against if exactly one of
them were wrong: the one with the thinnest mechanism, an unexplained surface word, or a
definition you had to stretch. Set its tier to "suggestion" and say why in its explanation.

This is empirically the cheapest precision available. Measured on a real run: the solver's
own weakest-commit flag identified the actual error, and demoting it moved precision
90.5% -> 95.0% while coverage fell only 75% -> 71%. You know which of your answers is
shakiest; act on it instead of hoping.

## Word ORDER of a multi-word answer (v15) — a recurring, costly error
Getting the right letters in the wrong order has been the single most persistent error class.
An anagram or charade that yields the correct letter multiset does NOT tell you the word order.
Before committing a multi-word answer:
- state which crossing letter FORCES each word into its position; if no crossing forces it,
  you are guessing between orderings and must not commit above 0.6;
- check both orderings against the enum: [2,5] and [5,2] are different answers;
- prefer the ordering that makes idiomatic Hebrew, but treat idiom as weaker evidence than a
  crossing letter.

## Substitutions (v14) — the setter's private vocabulary
`python3 solver/substitutions.py <word>` / `--to <word>` — 3,141 equivalences mined from
11,931 crowd explanations of real clues by these setters. This is what they actually use:
a first name completed by a surname, a word standing for a fragment, an abbreviation.
Examples from the data: אפ~גמ, קנ~בית, בל~לא, ספר~מנה, יו~גרנט, גרנ~חצי, קו~גבול.
39% of clue words in this genre have a recorded substitution.

Use it whenever a clue fragment is UNACCOUNTED FOR. The commonest cause of a failed
commit is "I have most of the answer but one word of the surface does nothing" — that
leftover word is usually a substitution. Query it before you settle for a partial account.

## Homographs (v7) — RUN THIS ON EVERY CLUE FIRST
`python3 solver/homographs.py scan "<clue text>"` lists every word in the clue that has more
than one sense, and `python3 solver/homographs.py <word>` explains one token.

Unvocalized Hebrew is the setter's main weapon: one letter sequence, several words.
  שרה = she sings / a female minister / the name Sarah
  שר  = a minister / he sings
  רב  = a rabbi / many / he quarrelled / the surname Rav
  פרס = a prize / Persia / the surname Peres
  גפן = a vine / the surname Geffen
  אור = light / the given name Or
Whenever a clue mentions a profession, a role, a title, or a common noun, suspect it is
standing in for a PERSON'S NAME (or the reverse). "The singer" may mean the word שרה;
"the minister" may mean the same letters. This resolves a large share of the culture clues:
the answer is often the OTHER reading of a word already sitting in the clue.

## Grid discipline (v6) — do NOT poison the board
- Fill a clue's letters into the shared grid ONLY when confidence >= 0.6. Low-confidence guesses
  stay in your answer file but are NEVER propagated as crossing constraints.
- Rationale (measured): on hard puzzles, propagating weak guesses locked the grid into wrong
  letters and dragged accuracy below the no-tools baseline. Sparse-but-correct anchors beat a
  full board of guesses. Leave cells unknown; unknown is recoverable, wrong is not.

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

## Controlled fact lookup (v5) — for the culture-reference tail
The ceiling is long clues built on a specific Israeli song / politician / place pun. You MAY
use web search to resolve FACTS, under strict anti-leakage rules:
- ALLOWED: entity/fact queries — "who sang <song>", "<politician> full name", "capital of X",
  "Hebrew name of <place>", "songs by <artist>", discography/filmography/Bible lookups.
- FORBIDDEN, always: (a) the answers site 14across.co.il or ANY crossword-solution site;
  (b) searching the clue text verbatim or near-verbatim; (c) any query containing
  "תשבץ"/"crossword"/"פתרון"/"solution"; (d) the puzzle images. If a search result looks like
  a crossword answer key, discard it and do not use it.
- Use lookups to turn "I don't know this reference" into a candidate, THEN still verify the
  wordplay and crossings before committing. A looked-up fact does not bypass confidence discipline.

## Hard rules
- Never consult 14across.co.il or any answers/solution site. Searching the clue verbatim is NOT
  allowed. Only entity-fact lookups per the section above.
- Answer in unspaced form (as grid letters), e.g. שלומעלישראל. The grid NEVER uses final
  letter forms (ם/ן/ץ/ף/ך -> מ/נ/צ/פ/כ everywhere, including word-final position).
- Try the mechanical anagram detector first: a contiguous run of clue words whose letter
  multiset (finals normalized) equals the enum total is almost certainly anagram fodder.
