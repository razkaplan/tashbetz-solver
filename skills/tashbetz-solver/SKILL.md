---
name: tashbetz-solver
description: >
  Solve Hebrew logic crosswords (תשבץ היגיון) precision-first: transcribe a puzzle
  from an image, validate the grid, and solve with executable wordplay proofs.
  Trigger when the user shares a Hebrew crossword image or asks to solve/help with
  a תשבץ היגיון, tashbetz higayon, or Hebrew cryptic clue.
---

# Tashbetz Higayon Solver

Solve Hebrew logic crosswords the way this engine does on record: two consecutive
unseen Haaretz puzzles solved blind at **100% precision** (15/15 and 13/13 committed
answers correct against the published keys).

## Setup (once)

The engine lives in a repo with its tools; data rebuilds from public sources:

```bash
[ -d ~/tashbetz-solver ] || git clone https://github.com/razkaplan/tashbetz-solver ~/tashbetz-solver
cd ~/tashbetz-solver && ./bootstrap.sh --dev-only
```

## The one governing rule

**A wrong answer is worse than a blank.** Wrong letters poison every crossing slot;
a blank is recoverable. Tag every answer `committed` / `suggestion` / `blank`, and
commit ONLY what you can prove. Never pad to look complete.

## Workflow

1. **Transcribe** the image: every clue (number, direction אופקי/אנכי, full Hebrew
   text, enumeration as int list, first word first — the RTL layout sometimes prints
   tuples reversed) and the grid pattern ('.'/'#', row 0 = top, index 0 = RIGHTMOST cell).
2. **Validate before solving** — this is non-negotiable:
   `python3 solver/grid_tools.py validate <grid.json> <clues.json>` must print OK
   (it recomputes the numbering and checks every slot length against the enums).
3. **Solve precision-first** per `solver/SOLVE_PROTOCOL.md`:
   - `solver/homographs.py scan "<clue>"` first — unvocalized Hebrew collapses words
     (שרה = zamarit/minister/name); a role word often stands for a person's name.
   - Mechanical anagram window-scan: a contiguous run of clue words whose letters
     match the enum total is near-proof (`solver/lexicon.py anagram <letters>`).
   - `solver/substitutions.py <word>` when a surface word is unaccounted for —
     3,141 equivalences these setters actually use.
   - `solver/lexicon.py pattern '?ו?ר?'` on any slot with crossing letters.
4. **The proof gate** — a commit must EXECUTE, not persuade:
   `python3 solver/prove.py check "<assert lines>" --answer <ans>` must exit 0.
   Multi-word answers require a passing `word_order` assertion (right letters in
   the wrong order is the most common error). If you cannot express the wordplay
   as assertions, you do not understand the clue well enough to commit.
5. **Propagate only committed answers** as crossing constraints; attack the most
   constrained slot next; repeat.

## Answer format

Unspaced, no final letter forms (ם/ן/ץ/ף/ך → מ/נ/צ/פ/כ), exact enum length.
Present results as: committed (with proofs), suggestions (clearly unverified), blanks.
