# Solving תשבץ היגיון — a grid-constrained harness for the Hebrew cryptic crossword

An autonomous build: data pipeline, solver, and evaluation loop for the Haaretz
weekly logic crossword by יורם הרועה (reputedly the hardest cryptic in Hebrew).

**Live research note + interactive failure-review tool:** see the deployed site.

## What's here
- `docs/` — the research note (methodology, results) and the interactive
  review-and-fix UI (also what GitHub Pages serves).
- `solver/` — the solving toolkit: `grid_tools.py` (grid validator + slot/crossing
  model), `lexicon.py` (129k-word Hebrew pattern/anagram lookup), `retrieve.py`
  (similar-clue retrieval), `consensus.py` (best-of-N merge), `fill_state.py`,
  and the data-derived `PLAYBOOK.md` / `SOLVE_PROTOCOL.md`.
- `scraper/` — answer-corpus parsers and the grid image extractor.
- `evals/` — the scoring harness (`run_eval.py`).
- `PLAN.md`, `RESULTS.md` — methodology and the honest iteration log (v1–v4).

## Method in one paragraph
Answers + crowd explanations come from a community solutions site; clue text and
grid geometry come from newspaper images, transcribed and validated by letter
count. The solver couples LLM wordplay reasoning with hard grid constraints, a
Hebrew lexicon, corpus retrieval, and best-of-N consensus, and never sees the
answers at solve time. The grid layer is airtight (every answer is length-valid);
accuracy plateaus at 25–57% per puzzle, gated by Israeli-culture reference clues
that need external knowledge.

## Data note
The raw scraped corpus (newspaper images, full answer database) is **not** included
in this repo out of respect for the sources' copyright. Only a two-puzzle excerpt
is embedded in the site for the interactive demo.
