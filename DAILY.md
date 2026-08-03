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
Last lever added: **candidate generation** (`solver/candidates.py`, 2026-08-03) — two
mechanical generators (anagram-window, hidden-run). Measured: 1/28 blind recall on a
newly-reconstructed real dev puzzle (2026-05-29) — see log. Full-pipeline
precision/coverage/yield above are NOT re-measured today (14across is down; see log).
Last finding: coverage is bounded by CANDIDATE GENERATION, not verification. Same
conclusion the cryptic-SOTA paper reached independently.

**⚠ INFRASTRUCTURE (2026-08-03): 14across.co.il is blocked for scripted access.**
Every request (including the bare homepage) now redirects to a bot-protection
challenge (`/.well-known/sgcaptcha/`). `bootstrap.sh` step 2 gets 0/52 puzzles until
this changes; do not try to script around a deliberate anti-bot wall. This blocks the
answers corpus, hence `data/dataset` gold labels, hence `evals/run_eval.py`, for every
puzzle reachable only that way. Workaround (now documented in bootstrap.sh step 6):
each week's puzzle image also prints the FILLED SOLUTION GRID for the *previous*
week's puzzle ("פתרון תשבץ ההיגיון מהשבוע שעבר"), so two consecutive weekly images
give one fully gold-verified puzzle (clue text from week N's image, solution letters
from week N+1's image) with zero 14across access. Used today to reconstruct
2026-05-29 as real, audited dev data — see log.

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
- 2026-08-03: `./bootstrap.sh --dev-only` step 2 (14across scrape) returned 0/52
  puzzles — the site now serves a bot-protection challenge page
  (`/.well-known/sgcaptcha/`) on every request, confirmed on the bare homepage too, not
  just `answers.php`. Did not attempt to defeat it (no headless-browser CAPTCHA bypass
  attempted; web.archive.org was also tried as a non-evasive alternative but is
  unreachable from this environment). This crashed the rest of bootstrap.sh (unhandled
  exception on `puzzle_date.split('/')` with `puzzle_date=None`) — fixed so it degrades
  and continues to steps 3-6 instead. Also caught and reverted an unrelated near-miss:
  manually running `scraper/harvest_culture.py` without its bootstrap guard clobbered
  the committed `solver/lex/culture.json` (6,771 songs / 2,431 artists / 998
  politicians / 239 places) with a rate-limited partial rebuild (1,791 / 1,807 / 0 / 0);
  reverted via `git checkout`. Added a matching guard to bootstrap.sh step 4
  (`substitutions.py build`) so a future 0-clue run can't do the same to
  `substitutions.json`.

  Found a working alternative for gold data that needs no 14across access at all: each
  week's puzzle image also prints the filled SOLUTION grid for the *previous* week's
  puzzle. Used it to reconstruct 2026-05-29 as real, audited dev data: transcribed
  clue text from `data/images/2026-05-28.jpg` (its own week) and solution letters from
  the small grid in `data/images/2026-06-04.jpg` (captioned "solution to last week's
  puzzle"); cross-validated the solution grid's black-cell pattern cell-for-cell
  against the already-committed `data/grids/2026-05-29.json` (exact match, a strong
  signature over 15x11 cells) and every one of the 28 enumerations against the
  grid-derived answer length (28/28 match, zero mismatches). This is gold letters, not
  crowd explanations (the solution box has no commentary) — good for scoring, not for
  `substitutions.py`/`retrieve.py`. Full technique now documented in bootstrap.sh step 6
  for future runs; `data/clues/` and `data/answers/by_date/` stay gitignored as before
  (matches the existing no-corpus-redistribution policy), so a future agent must redo
  this transcription (or extend it to more weeks) rather than finding it committed.

  **Lever: candidate generation** (queue item (a), highest priority). Built
  `solver/candidates.py`: two blind, mechanical generators — anagram-window scan
  (every contiguous run of clue words whose letter count matches the target, checked
  for a real-word anagram) and hidden-run scan (every contiguous letter run of target
  length in the space-free clue, checked for realness). Chosen because these are
  exactly the two mechanisms `prove.py` already verifies unambiguously
  (`is_anagram`/`is_hidden`); charade/container generation needs synonym knowledge to
  do more than blind substring search and was left out rather than shipped half-working
  (see RESEARCH.md 2026-08-03 for why — no Hebrew WordNet to lean on).

  **Measured** (`python3 solver/candidates.py selftest`, 3/3 pass; then run over all 28
  clues of the newly-built 2026-05-29 dev set, blind — clue text + enum only, no
  crossings, no gold access): **1/28 (3.6%) recall** — the gold answer appears in the
  generated pool for exactly one clue (2d, `יחפניות`, anagram of "פחות יין"). Mean pool
  size 2.9 candidates/clue; 13/28 clues produced an empty pool. AUDITED before trusting
  this low number, not just a high one: verified by hand that clue 25a
  (`ליבנו צר` -> `צרנוביל`/Chernobyl) IS a letter-perfect anagram the generator's logic
  correctly identifies as a fodder window, but the candidate is invisible because
  `צרנוביל` is neither in hspell nor the (Israel-only) culture-places list, and is
  correctly excluded from the corpus tier by `lexicon.held_out_answers()` now that this
  puzzle is `dev`-split gold — the same guard that caught the 2026-07-21 leak, working
  as intended, not a bug. So the ceiling here is bounded by two independent things: (a)
  most of this puzzle's 28 clues are not anagram/hidden mechanism at all (charade,
  culture-reference, double-definition — consistent with PLAN_V2's error profile), and
  (b) even correct mechanism hits need a broader real-word/proper-noun recognizer than
  hspell + Israel-scoped culture entities to confirm a candidate as real. Full jump
  check: 1/28 is a *drop* in absolute terms from nothing (there was no prior number to
  compare against — this is the first candidate-pool-recall measurement taken), so no
  ~15-point-jump implausibility concern applies either way.

  **Honest read**: this is a small, real, mechanically-sound piece (selftest 3/3,
  including a documented anti-leak interaction) that is not yet pulling its weight
  end-to-end. It does not move today's precision/coverage/yield numbers (not wired into
  the solve pipeline; that integration plus a broader realness dictionary is the
  natural next step, not attempted today to keep this run's change attributable to one
  thing). Full-pipeline numbers in the state table above are last measured
  2026-07-28/29 and were not re-run today (no full blind solve was performed against
  the new 2026-05-29 corpus this run — only the candidate-generation-recall
  measurement).

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
