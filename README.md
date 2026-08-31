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
- `scraper/` — answer-corpus parsers, the grid image extractor, and the weekly
  news harvest (`news_israel.py`).
- `evals/` — the scoring harness (`run_eval.py`) and the topic-crossword gate
  (`topicgen_eval.py`).
- `PLAN.md`, `RESULTS.md` — methodology and the honest iteration log (v1–v4).

## Setting, not just solving

The same machinery runs backwards to *set* crosswords: `solver/grids_topic.py`
(two crossword and two arrowword templates, validated at import) and
`solver/topicgen.py` (`generate(topic, level, shape)`), which fills a board from
a topic's term bank and clues every entry with a machine-checkable proof.
Difficulty is measured rather than labelled: the easy levels fill only from
answers the corpus actually saw in printed puzzles, and
`evals/topicgen_eval.py` re-derives every judgement from the committed data
before a board may be published. Output: subject crosswords for bagrut revision,
a weekly news board, and boards built on request.

## Method in one paragraph
Answers + crowd explanations come from a community solutions site; clue text and
grid geometry come from newspaper images, transcribed and validated by letter
count. The solver couples LLM wordplay reasoning with hard grid constraints, a
Hebrew lexicon, corpus retrieval, and best-of-N consensus, and never sees the
answers at solve time. The grid layer is airtight (every answer is length-valid);
accuracy plateaus at 25–57% per puzzle, gated by Israeli-culture reference clues
that need external knowledge.

## Use it as a Claude Code skill

The solving methodology installs as a skill for any Claude Code user:

```bash
git clone https://github.com/razkaplan/tashbetz-solver ~/tashbetz-solver
cp -r ~/tashbetz-solver/skills/tashbetz-solver ~/.claude/skills/
cd ~/tashbetz-solver && ./bootstrap.sh --dev-only
```

Then drop any תשבץ היגיון image into a Claude Code session and ask it to solve.
The skill enforces the precision-first protocol and the executable proof gate that
produced two consecutive blind 100%-precision solves.

## Data note
The raw scraped corpus (newspaper images, full answer database) is **not** included
in this repo out of respect for the sources' copyright. Only a two-puzzle excerpt
is embedded in the site for the interactive demo.
