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
Last lever added: **mechanical candidate generation** (`solver/candidates.py`) — sliding-
window anagram/reversal/hidden scanner with definition-span tagging. Full pipeline
precision/coverage numbers above are UNCHANGED this run (no new blind full-pipeline
score — see 2026-08-07 log entry for why).
Last finding (2026-08-07): pure string-mechanical candidate generation has a LOW recall
ceiling on this setter specifically — only 3/28 gold answers in the one transcribed dev
puzzle are literal anagram/reversal/hidden instances; the other 25 route through a
synonym first (charade/culture/homophone), which string mechanics alone cannot reach.
Previous finding still stands: coverage is bounded by CANDIDATE GENERATION, not
verification — same conclusion the cryptic-SOTA paper reached independently (see
RESEARCH.md 2026-08-07) — but the fix needs to be SYNONYM-AWARE generation, not pure
string mechanics, to move the number on this setter.

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

1. **Synonym-aware candidate generation** — `solver/candidates.py` (2026-08-07) does
   pure string mechanics (anagram/reversal/hidden sliding window) and measures 0/8 live
   recall on 2026-06-05: this setter's clues almost always route the fodder through a
   SYNONYM first (charade/culture/homophone, ~75% of clues per PLAYBOOK.md), which
   string mechanics alone cannot reach. Extend the same sliding-window approach so the
   fodder can be `substitutions.py`'s recorded synonym of a clue word, not only the
   literal word — this is now the highest-expected-value next step, not a new lever.
   Definition-span detection is folded into this generator already (each hit is tagged
   with which end of the clue is left over); the literature review (RESEARCH.md,
   2026-08-07) found no cryptic solver, including current SOTA, that uses a standalone
   definition-boundary classifier instead of this enumerate-both-ends approach.
2. **Grow the corpus** — 8,249 clue-answer pairs vs ~470k used by the SOTA system. The
   tartey_mashma Google Group posts weekly scans of easier setters; transcribing those
   unlocks both retrieval and any future fine-tune. This is the long game.
3. **Global constraint optimization** — scored candidates + belief propagation over the
   grid (Berkeley Crossword Solver approach). Worth doing once candidate lists are good.
4. **Validate on the easier tier** (דקל בנו) — where 80% is realistic; tells us whether
   the harness is sound and this setter is simply hard.

## Things already tried — do not repeat
- More knowledge tooling (wiki, culture lexicon, shironet titles): helped early, now saturated.
- Raising the confidence threshold: exhausted at 0.75; higher only trades coverage away.
- LLM verifiers judging plausibility: superseded by the executable proof gate.
- Majority-vote consensus: reverses sign with run quality — helps weak runs, hurts strong ones.
- More passes: coverage went 36 -> 46 -> 57 -> 55 -> 43; passes are exhausted.
- Pure string-mechanical candidate generation (anagram/reversal/hidden sliding window,
  no synonym step): built and measured 2026-08-07, 0/8 live recall on 2026-06-05's
  lexicon-reachable answers. Don't rebuild this in isolation again — extend it with a
  synonym-aware pass (queue item 1) instead of a second from-scratch string-only version.

## Log
- 2026-07-28: proof gate added. Rejected 3 candidates on 06-05: 2 were genuine errors,
  1 was a correct answer lost. Precision 100%, coverage flat. Concluded candidate
  generation is the bottleneck.
- 2026-08-07: bootstrapped from scratch (repo ships no corpus). `scraper/parse_answers.py`
  needed a retry-with-backoff fix first — 14across sits behind an intermittent bot
  challenge (SG-Captcha) that silently returned a 318-byte stub for ~35-60% of requests;
  without retries, bootstrap crashed rebuilding `by_date/`. Fixed (checkpointed,
  resumable, retries transient connection resets too) — infra, not today's lever.
  Transcribed clue text for 2026-06-05 from its image (bootstrap step 6) — the ONE dev
  puzzle usable this run. Two enum-transcription bugs caught and fixed by cross-
  validating against grid slot lengths AND independently-scraped gold answer lengths
  (both agreed, both disagreed with parts of my first OCR pass): 8-across and 10-across
  enums were swapped (7 vs 3) in my first reading, 11-across was off by one. Given the
  demonstrated unreliability of reading small multi-digit enum groups at this image
  resolution, used single-group enums (total length only) throughout rather than risk
  propagating a wrong word-split; grid_tools.py validate passes.
  Researched cryptic-solving literature (RESEARCH.md) — strongly supports candidate
  generation as today's lever, and specifically supports folding definition-span
  detection into it as an axis (enumerate both ends, let the proof gate arbitrate)
  rather than building a separate classifier — no cryptic solver in the literature,
  including current SOTA, uses a standalone definition-boundary classifier.
  Built `solver/candidates.py`: sliding-window anagram/reversal/hidden-word generator,
  each hit tagged with a definition-span hypothesis (whichever side of the fodder window
  still has clue text). Selftest 3/3 (`python3 solver/candidates.py selftest`).
  MEASURED (execution, not estimation): of the 28 gold answers in 2026-06-05, only 3
  (7-across, 8-across, 11-down) are literal instances of the 3 implemented mechanisms per
  the crowd explanations. All 3 are correctly UNREACHABLE through the tool as shipped,
  because `lexicon.py`'s `held_out_answers()` — the leak guard from the 2026-07-21
  incident — strips this puzzle's own answers from the word list the tool checks
  candidates against. A bypass diagnostic (temporarily re-adding just those 3 words,
  clearly marked as a code-correctness check, not a solve) confirms the string mechanics
  are exactly right for all 3. Of the 8/28 gold answers that ARE reachable (ordinary
  dictionary words or answers from other puzzles), live recall is **0/8** — none of them
  are literal anagrams/reversals/hidden-runs of their own clue text; every one routes
  through a synonym first (charade, culture-pun, or homophone), matching PLAYBOOK.md's
  own frequency table (charade ~35-40%, double-def 14%, culture 6-8% vs anagram+reversal
  +hidden ~25% combined — and PLAYBOOK 1.5's own worked reversal examples show even most
  of that 25% needs a synonym step, e.g. פתח clued but החל is the word actually reversed).
  AUDIT: no answers-site access, no forbidden reads; the 0/8 and 3/28 numbers came from
  running `solver/candidates.py` against real clue text and real (separately-scraped)
  gold answers, not estimated. No number here jumps implausibly — it's a small, honest,
  mostly-negative result.
  Did NOT attempt a fresh full blind solve+eval this run: I had already read
  2026-06-05's gold-answer file while repairing the enum-transcription bugs above, which
  disqualifies me from blind-solving that puzzle myself; a legitimate blind run would
  need a SECOND puzzle transcribed while staying unread of its answers, which did not
  fit in this run's time budget. Flagged rather than papered over — the state table
  above is unchanged, not padded with a same-puzzle rerun.
  CONCLUSION: candidate generation is still the right lever, but pure string mechanics
  (today's implementation) has a low ceiling on this specific setter. Next highest-value
  step: extend `candidates.py` with a synonym-aware pass over `substitutions.py`'s 3,141
  mined equivalences before sliding the anagram/reversal window, so fodder can be a
  SYNONYM of a clue word, not only the literal word itself.

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
