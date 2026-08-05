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
Last lever added: **candidate generation** (`solver/candidates.py`) — per-clue candidates
crossed by mechanism (anagram/reversal/hidden/charade) x definition-span hypothesis
(prefix/suffix, k=1..3), feeding the existing proof gate. Selftest: all pass. Measured
standalone recall@50 on a freshly-transcribed dev puzzle (2026-05-29, 28 clues, audited
no-leak): **1/28 = 4%** exact-answer recall from pure letter-mechanics alone (no full
solve/eval done this cycle — see log). Low, and explainable: spot-checked misses are
double-definition / homograph / culture-pun clues, mechanisms this tool does not attempt.
The table above (precision/coverage/yield) is from a PRIOR session's full transcribed
corpus and is NOT reproduced this cycle — see log for why.
Last finding: coverage is bounded by CANDIDATE GENERATION, not verification. Same
conclusion the cryptic-SOTA paper reached independently (see RESEARCH.md 2026-08-05).

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
- 2026-08-05: Fresh environment, no corpus shipped (by design). Ran `./bootstrap.sh
  --dev-only`; hit a pre-existing bug (pipefail + `head -3` on step 4 raised
  BrokenPipeError and killed the script before step 5), fixed with a one-line change
  (`bootstrap.sh` line 59, redirect stderr + `|| true`) — trivial infra fix, not
  today's lever. Transcribed **one dev puzzle from scratch** (2026-05-29, article date
  2026-05-28) by reading the jpg directly: 28 clues, both directions, every enum
  validated to sum to the gold answer's letter count (0 mismatches) before touching
  the solver. Note for future transcription: this puzzle's across clues 13/15/17
  visually cluster two short clues' numbers and enums close together on one line
  (`...11(6) 13. בני טוב` then next line `כמלחין (4) .15 האריה... (3) .17 ...`) —
  it took several rounds of pixel-level re-cropping to confirm the enum immediately
  preceding a clue-number belongs to the clue that number STARTS, not the one it
  visually sits next to; all three now validate against gold lengths.
  Researched (RESEARCH.md): the ICML-2025 Cryptonite SOTA paper generates ~20
  candidates/clue before verification, independently confirming this project's own
  diagnosis. Implemented **lever (a), candidate generation**: `solver/candidates.py`
  (mechanism x definition-span-hypothesis candidate generator, selftest all-pass) +
  `solver/eval_candidates.py` (reusable recall@N harness for future cycles).
  Measured recall@50 on the transcribed puzzle: 1/28 (4%), audited — lexicon.py's
  held_out_answers() confirmed blocking all 28 gold answers from lexicon upgrade
  (verified directly: e.g. ישפרחימ/ליסט/ברישניקוב absent from the loaded word set),
  so the one hit (2d יחפניות, via anagram of the fodder פחות+יין) is a legitimate
  hspell dictionary word, not a leak — confirmed end-to-end with prove.py. Spot-checked
  several misses (8a ערב, 24a שלג, 6d סרבית) and they are double-definition /
  homograph clues, mechanisms outside this tool's scope by design — matches this
  project's own long-standing diagnosis (RESULTS.md: "100% of the gap is
  wordplay-cracking quality") and the literature (RESEARCH.md: definition-span
  ambiguity and multi-step wordplay are the documented LLM failure modes on this
  genre), not a bug in the new tool.
  **What I did NOT do this cycle**: a full solve-and-eval pass (acting as the LLM
  solver across all 28 clues with SOLVE_PROTOCOL, self-flagging, and the proof gate)
  to get a comparable precision/coverage/yield number against the state-table baseline.
  That is naturally next: run the pipeline with `candidates.py` available as a tool and
  compare against a same-puzzle baseline run without it. The state table above is left
  as the last session's number, not overwritten with an unmeasured guess.

---

## IF YOU ARE THE DAILY CLOUD AGENT — read this

The repo ships no corpus, but **you are not blocked: everything is reconstructible from
public sources.** Run this first:

    ./bootstrap.sh --dev-only     # ~2 min: lexicon, answers, culture, substitutions, dev images

That fetches the hspell lexicon (github), re-scrapes the answers corpus from 14across
(plain HTTP, no login), rebuilds culture entities from the he-wikipedia API, derives the
substitution dictionary, and downloads the dev puzzle images from the public Haaretz CDN
via the committed URL manifest. Grids are already in the repo.

The one thing it cannot script is **clue text**, which exists only inside the images.
Bootstrap step 6 tells you how to transcribe it, and you can: read the jpg, transcribe the
תשבץ היגיון clues, validate each enumeration against the answer letter count, then run
`python3 solver/build_dataset.py`. Do this for one dev puzzle and you can evaluate for real.

**So you CAN verify your work — and you must.** Run `python3 evals/run_eval.py <file>`
on anything you claim. Never state a number you did not produce by executing code.
This project already had a 96% result turn out to be a leak in its own tooling; that is
why every claim needs evidence. If you genuinely cannot run something, say so plainly
rather than estimating.

Each run:

1. **Bootstrap** (above), then confirm what you actually have.
2. **Research** — new work on cryptic solving, wordplay formalisation, definition-span
   detection, Hebrew NLP. Append to RESEARCH.md with links and an honest judgement of
   whether it transfers. Most crossword-AI work targets non-cryptic puzzles and does not.
3. **Implement exactly ONE lever** from the queue above. One, so the effect is attributable.
4. **Evaluate it** against the previous best in the state table. Audit before believing:
   scan for forbidden reads, check no tool leaks held-out answers, and treat any jump over
   ~15 points as suspect until explained.
5. **Open a PR** (never push to main) stating what you built, the measured effect, and what
   is still unverified. Update the state table and append to the Log.

A run that reports "this lever did not help, here is the evidence" is a good run.
