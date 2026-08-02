# Daily improvement runbook — tashbetz solver

Read this first each run. It is the handoff between days.

## Current state (update this section every run)

| Metric | Value | Target |
|---|---|---|
| Precision (combined dev) | **96.9%** | >=95% ✓ |
| Coverage | 57% | >=70% |
| Accurate fulfilment (yield) | 55% | ~67% |
| Best single puzzle | 2026-05-29: 95% / 71% / 68% ✓ all targets | |
| Hardest puzzle | 2026-06-05: 100% / 43% / 43% | coverage stuck |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added: **proof gate** (`solver/prove.py`) — commits must execute as assertions.
Last finding: coverage is bounded by CANDIDATE GENERATION, not verification. Same
conclusion the cryptic-SOTA paper reached independently.

## The policy that governs everything
A blank beats a wrong answer. Wrong letters corrupt crossings and poison later passes.
Three tiers: `committed` (asserted, proof must execute), `suggestion` (unverified, never
propagated), `blank`. Score with `python3 evals/run_eval.py <file>`.

## Each run, in order

1. **Check for a new puzzle.** A new Haaretz puzzle publishes weekly (Fri). If one exists
   that is not in `data/images/`, harvest it: the article is paywalled to anonymous
   scrapers, so the image URL must come from a logged-in browser session (see
   `project_tashbetz_solver` memory). Then transcribe clues + grid, and validate:
   every enum sum must equal the answer letter count, and `solver/grid_tools.py validate`
   must print OK. Watch for REVERSED enumerations — 6 of 50 puzzles had them.
2. **Run the current best pipeline** on a dev puzzle: precision-first pass, then
   anchor-propagating passes (`solver/pass2_patterns.py`), every commit proof-gated.
3. **Score and AUDIT.** Never report a number without: transcript scan for forbidden
   reads / solution sites / images; a tool-leak check (is any held-out answer reachable
   through a tool?); and an implausibility check — a jump over ~15 points is suspect
   until explained. This caught a 96% result that was pure leak.
4. **Try exactly ONE new lever** per run, from the queue below. One at a time, or you
   cannot attribute the change.
5. **Update the table above and append to the log.** Then stop.

## Lever queue (highest expected value first)

1. **Candidate generation** — the measured bottleneck. Generate N diverse candidates per
   clue (per mechanism, per definition-span hypothesis), then let the proof gate filter.
   Currently the solver produces one candidate and tries to justify it; that is backwards.
2. **Definition-span detection** — a cryptic clue's definition sits at one END. Classify
   which end, then solve the wordplay from the remainder. Standard in the literature,
   never tried here.
3. **Grow the corpus** — 8,249 clue-answer pairs vs ~470k used by the SOTA system. The
   tartey_mashma Google Group posts weekly scans of easier setters; transcribing those
   unlocks both retrieval and any future fine-tune. This is the long game.
4. **Global constraint optimization** — scored candidates + belief propagation over the
   grid (Berkeley Crossword Solver approach). Worth doing once candidate lists are good.
5. **Validate on the easier tier** (דקל בנו) — where 80% is realistic; tells us whether
   the harness is sound and this setter is simply hard.

## Things already tried — do not repeat
- More knowledge tooling (wiki, culture lexicon, shironet titles): helped early, now saturated.
- Raising the confidence threshold: exhausted at 0.75; higher only trades coverage away.
- LLM verifiers judging plausibility: superseded by the executable proof gate.
- Majority-vote consensus: reverses sign with run quality — helps weak runs, hurts strong ones.
- More passes: coverage went 36 -> 46 -> 57 -> 55 -> 43; passes are exhausted.

## Log
- 2026-07-28: proof gate added. Rejected 3 candidates on 06-05: 2 were genuine errors,
  1 was a correct answer lost. Precision 100%, coverage flat. Concluded candidate
  generation is the bottleneck.

---

## IF YOU ARE THE DAILY CLOUD AGENT — read this

You cloned the public repo. **The data is not here and that is intentional**: the corpus,
grids, clue inputs, gold answers and the hspell lexicon are gitignored so this repo does not
republish Haaretz content. Therefore:

**You CANNOT run the solver or the eval loop. Do not try, and do not fabricate scores.**
`data/` is absent. Any number you cannot produce by running code, you must not report.

What you CAN do, and what your job is:

1. **Research.** Search for new work on cryptic-crossword solving, wordplay parsing,
   constrained generation, Hebrew NLP. The field moves; the last survey found the
   formalise-and-verify approach that became `solver/prove.py`. Record findings in
   `RESEARCH.md` with links, and say plainly whether each is applicable here and why.
2. **Implement exactly ONE code-only lever** from the queue in this file. Priority is
   candidate generation, then definition-span detection. These are pure code and need no
   corpus. Write them so they degrade gracefully when `data/` is missing.
3. **Write tests that run without data.** `solver/prove.py selftest` is the model: it
   exercises real logic on inlined examples. Any new module should ship one.
4. **Open a pull request** with the change, and in the description state exactly what
   remains unverified because you had no data. Do not merge to main.
5. **Append to the Log** below: date, what you researched, what you built, what is untested.

Verification of your work happens locally, where the data lives. Your job is to arrive with
a well-argued, tested-where-possible change — not with claimed results.
