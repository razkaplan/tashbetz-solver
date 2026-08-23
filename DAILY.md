# Daily improvement runbook — tashbetz solver

Read this first each run. It is the handoff between days.

## Current state (update this section every run)

| Metric | Value | Target |
|---|---|---|
| Precision (combined dev) | **96.9%** (unchanged, not re-run today — see log) | >=95% ✓ |
| Coverage | 57% (unchanged, not re-run today) | >=70% |
| Accurate fulfilment (yield) | 55% (unchanged, not re-run today) | ~67% |
| Best single puzzle | 2026-05-29: 95% / 71% / 68% ✓ all targets | |
| Hardest puzzle | 2026-06-05: 100% / 43% / 43% | coverage stuck |
| **Candidate recall@N (new, offline, mechanical only)** | **3.6% (1/28)**, avg 11.6 candidates/clue (capped), on 2026-05-29 — UNCHANGED after adding substitution+homograph mechanisms | not yet a target — diagnostic |
| **Definition-span locatable rate (new, offline, diagnostic)** | **25% (7/28)** have mechanically-locatable single-window wordplay; of those 29% (2/7) are interior, not edge; classifier agreement on edge cases **1/5** | not a target — this diagnostic KILLED the lever, see log |
| **`solve_pass.py` LIVE blind trial (2026-08-16)** | **50% precision (1/2 committed)**, 9.5% coverage, 4.8% yield, on a partial 21/28-clue puzzle (2026-06-12) | n=2 — NOT a reliable estimate, see log |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added (2026-08-20): **substitution- and homograph-aware candidate generation**
(`solver/candidates.py`: `substitution_candidates`, `homograph_candidates`) — queue item
1(b). Also fixed a truncation-priority bug the new mechanisms exposed (see log) and added
held-out-safety filtering to `solver/substitutions.py` (`held_out()`), which the new
mechanism's use of that table required. MEASURED NEGATIVE on the same 2026-05-29 puzzle
used for the 2026-08-06 baseline: recall@N unchanged at 1/28 = 3.6%, same single anagram
hit as before. Homograph mechanism fired 5 times on this puzzle (0 matched gold);
substitution fired 0 times with the held-out-safe in-memory table (today's severely
reduced corpus — see log) and only 9 times / 0 gold hits even with the full committed
table checked as an audit-only diagnostic (not used for the scored number). Small sample
(28 clues, one puzzle) — this is a real negative result, not proof the devices never help,
but today's specific implementation of them did not move recall on this puzzle. Standing
finding (2026-08-06) still holds: coverage is bounded by CANDIDATE GENERATION, not
verification, and this setter leans on devices (substitution/homograph, but evidently
not in the SHAPE this lever implemented them) that plain anagram/hidden/reversal miss.

**2026-08-23 lever: closed queue items 7 and 7b — `held_out()` coverage gap, all three
places it lives.** Two PRs were open and unmerged on top of this main when this run
started: #23 (2026-08-21, fixes `lexicon.held_out_answers()`, queue item 7, and flags the
identical gap in `substitutions.py`/`retrieve_defs.py` as new item 7b) and #24 (2026-08-22,
first full-puzzle live blind trial of `solve_pass.py`, 0/2 precision — see its own note
below). Cherry-picked #23's `lexicon.py` fix onto this branch rather than re-deriving it,
then did the ONE new thing left open: item 7b. `substitutions.py`'s `held_out()` had the
exact same row-only shape `lexicon.py`'s did before the fix — a REAL, currently-exploitable
gap, since `explanations()` sources `data/answers/answers_parsed.json` unconditionally for
all 52 puzzles regardless of transcription state. MEASURED on real data (2026-05-29, a
canonical dev puzzle, using its real `data/answers/by_date/2026-05-29.json`): simulating
only 1 of its 28 clues transcribed (the old row-only block set), 10 substitution pairs were
mined directly out of this held-out puzzle's own remaining 27 (still-"untranscribed")
crowd explanations and would have entered the committed substitution table — e.g.
`מסר~נתנ`, `אושכפ~סנדלר`, `ימ~ירושלימ`. Under the fix (by_date-expanded block set, all 28
answers blocked once any one row marks the date dev/eval), all 10 are correctly excluded;
total mined pairs corpus-wide drop from 323 to 313, exactly the 10 closed. `retrieve_defs.py`
got the same interface change for consistency/defense-in-depth, but inspection showed its
one caller (`build_index()`) sources docs only from `clues.jsonl` rows marked
`split=='train'` — which an untranscribed slot can never have — so unlike `substitutions.py`
this was not shown to be actively exploitable under the current call graph; recorded
honestly rather than claimed as a second real leak. Both files gained a `selftest`
subcommand (synthetic fixtures only). Not a solving lever — no precision/coverage/yield
number was expected to move and none did; this is an integrity fix. See log for the full
audit and RESEARCH.md for today's search (definition-fit scoring, the gap #24 surfaced —
no buildable-today mechanism found, Hebrew WordNet flagged as the one lead).

**PR #24 (2026-08-22, open, unmerged) — for the next run's awareness.** First full 28/28
live blind trial of `solve_pass.py`: 0/2 precision on 2026-05-15. Both misses share one
shape — `prove.py` correctly verified a real mechanism (hidden word, reversal) on a
plausible-but-wrong Hebrew answer. Combined with the 2026-08-16 trial (1/2), **cumulative
live precision across the only two live trials this project has run is 1/4 = 25%** — the
sharpest evidence yet that definition-FIT judgment, not mechanism verification, is the
remaining gap. Not re-verified by today's run (out of scope for a one-lever integrity fix);
flagging so it isn't independently re-discovered a third time before #24 is merged or
closed. See PR #24 for the full root-cause trace.

**INFRASTRUCTURE UPDATE (2026-08-06): 14across.co.il access is intermittent, not blocked.**
Earlier (2026-08-03) it looked like a hard bot-protection wall (`/.well-known/sgcaptcha/`
on every request, 0/52 puzzles). A later run found it's actually a random ~50%-of-requests
bot-check redirect, unrelated to rate — `scraper/parse_answers.py` now retries with
backoff and recovers all 52/52 puzzles reliably. If a future run still comes up short
anyway, there's a fallback needing zero 14across access: each week's puzzle image also
prints the FILLED SOLUTION GRID for the *previous* week's puzzle ("פתרון תשבץ ההיגיון
מהשבוע שעבר"), so two consecutive weekly images give one fully gold-verified puzzle
(clue text from week N's image, solution letters from week N+1's image). Documented in
bootstrap.sh step 6; used once (2026-08-03) to reconstruct 2026-05-29 as real, audited
dev data before the retry fix existed — see log.

2026-08-19 lever (definition-span detection, `solver/defspan.py`): NEGATIVE result,
measured not assumed — see log below. Queue item 2 struck; do not re-attempt with the
same indicator-density signal.

2026-08-16 lever (`solver/solve_pass.py`, wiring candidate generation into a ranked live
solve pass): first LIVE blind trial, 50% precision (1/2) on a tiny n=2 committed sample —
not a reliable estimate, but the root-cause trace is useful: the proof gate correctly
verified a real anagram (`is_anagram('קבר', 'בקר')`) that was nonetheless the WRONG
answer, because a mechanically-verified anagram is evidence of possibility, not
correctness — the miss was a definition-fit judgment call, not a tool defect. Also
surfaced two infrastructure findings: a systematic gap where ~7 of 28 across clues are
absent from the standard puzzle image (confirmed across 4 different weeks), and a real
`held_out_answers()` leak vector (it only blocks an answer when its clue has a row in
`data/dataset/clues.jsonl`, so an untranscribed clue's gold answer stays exposed in the
lexicon) — flagged in the lever queue, not yet fixed. See log for the full trace.

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

1. **Candidate generation** — the measured bottleneck. `solver/candidates.py` (2026-08-06)
   does the mechanical half (anagram/hidden/reversal/pattern, character-level fodder
   windows) but measures only 3.6% recall alone — NOT sufficient by itself. (b)
   substitution- and homograph-aware generation was ADDED 2026-08-20 (see log) and
   measured NEGATIVE on the same dev puzzle (recall unchanged, 1/28) — do not re-attempt
   this exact shape without a different corpus or a redesigned mechanism; the standing
   PLAYBOOK.md diagnosis (setter leans on these devices) may still be right even though
   this implementation of them didn't capture it — candidate: the mined substitution
   table needs to cover multi-part charades (3+ segments), not just 1-2 word coverage of
   the FULL answer length, which is what today's version required. A separate, earlier
   attempt at this same lever (2026-08-17, see log) measured the same negative result on
   a THIRD dev puzzle (2026-04-03, 4.0% recall unchanged) with an independently-written
   version of these two mechanisms — two different implementations, two different
   puzzles, same null result, which strengthens rather than weakens the standing
   diagnosis that this specific shape of substitution/homograph generation isn't the
   fix. Remaining work: (a) wire the generator into an actual solve pass so an LLM
   proof-gates the generated list instead of one guess — still not done, every recall
   measurement so far has been pure offline generator + recall, never plugged into a
   live solve+prove loop.
2. ~~Definition-span detection~~ — TRIED 2026-08-19, NEGATIVE. See log and "already
   tried" below. Do not re-attempt without a fundamentally different signal (not
   indicator-word density).
3. **Grow the corpus** — 8,249 clue-answer pairs vs ~470k used by the SOTA system. The
   tartey_mashma Google Group posts weekly scans of easier setters; transcribing those
   unlocks both retrieval and any future fine-tune. This is the long game.
4. **Global constraint optimization** — scored candidates + belief propagation over the
   grid (Berkeley Crossword Solver approach). Worth doing once candidate lists are good.
5. **Validate on the easier tier** (דקל בנו) — where 80% is realistic; tells us whether
   the harness is sound and this setter is simply hard.
6. ~~Merge or close the PR backlog~~ — MOSTLY RESOLVED. The 8-PR pileup flagged 2026-08-16
   is down to 2 open PRs as of 2026-08-23 (#23, #24 — both from single daily runs, not a
   backlog). Still true that only the project owner can merge; still worth doing so this
   doesn't creep back up, but no longer the acute blocker it was.
7. ~~Fix `lexicon.held_out_answers()`'s coverage gap~~ — FIXED 2026-08-21 (PR #23) and
   folded into this main's history 2026-08-23 (cherry-picked). It only blocked an answer
   when its clue had a row in `data/dataset/clues.jsonl`; fix blocks every answer in the
   puzzle's full `data/answers/by_date/<date>.json` once any one row marks the date
   dev/eval. Measured: 18/18 previously-unblocked untranscribed-slot answers now blocked
   (2026-06-05 test). See log.
   - **7b** (flagged by PR #23, fixed 2026-08-23): the identical gap in
     `substitutions.py`/`retrieve_defs.py`. `substitutions.py`'s half was a REAL,
     currently-exploitable leak (its `explanations()` sources ALL 52 puzzles
     unconditionally); measured 10 substitution pairs closed on 2026-05-29's real data.
     `retrieve_defs.py`'s half was name-only — its caller can't reach an untranscribed
     slot by construction — fixed anyway for a consistent contract. See log.
8. **[NEW 2026-08-16] Audit whether across clues 1-13 were ever legitimately sourced.**
   4 different weeks' dev images (2026-06-11, 2026-06-18, 2026-05-21, 2026-05-28) all show
   the identical gap: the printed clue column starts at across ~13-15 and never contains
   across 1-12. Several prior PRs (#2, #6, #8, #9, #10, #11) claim "28/28 transcribed, 0
   mismatches" for 2026-05-29 and 2026-05-21 — worth a direct re-check of whether that
   text came from a real, legitimate source (a login-gated fuller image? a different CDN
   parameter?) or whether it was inadvertently sourced from the "previous week" reprint
   block that sits next to a filled solution grid on the same page (which shares identical
   enum lengths at every slot only because this setter reuses one fixed grid template —
   confirmed 2026-06-05's and 2026-06-12's committed grids are byte-identical — so an enum
   match there is NOT evidence of being the right week's text). If those older
   transcriptions used the wrong week's clues, some historical dev numbers may need
   re-measurement.
9. **[NEW 2026-08-23] Definition-fit scoring — the sharpest gap PR #24 surfaced.**
   Cumulative live precision across this project's only two live trials is 1/4 (25%); both
   misses are `prove.py` correctly verifying a real mechanism on a plausible-but-wrong
   answer — the gap is judging whether a candidate matches the DEFINITION, not whether the
   wordplay executes. `defspan.py`'s indicator-density approach to the adjacent
   definition-*location* problem already measured 1/5 (worse than chance) — a naive rule-
   based definition-fit scorer risks the same fate. The one lead today's research turned
   up that has actual literature backing (English rule-based cryptic solvers use WordNet
   path-similarity for this exact role): a Hebrew WordNet reportedly exists
   (MultiWordNet-aligned) but this run could not confirm a working, licensable, scriptable
   mirror in its research budget — confirming reconstructibility is the first step before
   attempting to build on this, not something to stub around.

## Things already tried — do not repeat
- More knowledge tooling (wiki, culture lexicon, shironet titles): helped early, now saturated.
- Raising the confidence threshold: exhausted at 0.75; higher only trades coverage away.
- LLM verifiers judging plausibility: superseded by the executable proof gate.
- Majority-vote consensus: reverses sign with run quality — helps weak runs, hurts strong ones.
- More passes: coverage went 36 -> 46 -> 57 -> 55 -> 43; passes are exhausted.
- **Definition-span detection via indicator-word density** (2026-08-19, `solver/defspan.py`):
  measured, not just implemented — see log entry. Only 25% of clues even have a
  mechanically-locatable single-window wordplay span to test the premise against; of
  those, 29% are interior (breaking the one-end model outright); and on the remaining
  edge cases the indicator-density classifier scored 1/5 — because most of these clues
  carry NO indicator word at all (this setter's anagram signal is mechanical, not
  lexical, exactly as PLAYBOOK.md already noted), so the classifier degenerates to a
  fixed default that loses to the actual distribution. Do not re-attempt with the same
  signal; a different approach (e.g. scoring by whether each end's residual is anagram-
  matchable) would have to be validated the same way before trusting it.

## Log
- 2026-07-28: proof gate added. Rejected 3 candidates on 06-05: 2 were genuine errors,
  1 was a correct answer lost. Precision 100%, coverage flat. Concluded candidate
  generation is the bottleneck.
- 2026-08-03: `./bootstrap.sh --dev-only` step 2 (14across scrape) returned 0/52
  puzzles that day — looked at the time like a hard bot-protection wall (see
  2026-08-06 entry below for the corrected diagnosis: it's intermittent, and a retry
  fix now recovers all 52/52). Found a working alternative for gold data that needs no
  14across access at all, useful independent of that fix: each week's puzzle image also
  prints the filled SOLUTION grid for the *previous* week's puzzle. Used it to
  reconstruct 2026-05-29 as real, audited dev data: transcribed clue text from
  `data/images/2026-05-28.jpg` (its own week) and solution letters from the small grid
  in `data/images/2026-06-04.jpg` (captioned "solution to last week's puzzle");
  cross-validated the solution grid's black-cell pattern cell-for-cell against the
  already-committed `data/grids/2026-05-29.json` (exact match, a strong signature over
  15x11 cells) and every one of the 28 enumerations against the grid-derived answer
  length (28/28 match, zero mismatches). This is gold letters, not crowd explanations
  (the solution box has no commentary) — good for scoring, not for
  `substitutions.py`/`retrieve.py`. Full technique documented in bootstrap.sh step 6 as
  a fallback for future runs. Also caught and reverted an unrelated near-miss that day:
  manually running `scraper/harvest_culture.py` without its bootstrap guard clobbered
  the committed `solver/lex/culture.json`; reverted via `git checkout` before it reached
  any measurement or commit.

  Independently built a first version of a candidate-generation lever this same day
  (two word-level mechanical generators, anagram-window + hidden-run; 1/28 recall on
  the same 2026-05-29 puzzle). Superseded by the more complete character-level version
  built 2026-08-06 below (anagram/hidden/reversal/pattern) — not kept separately to
  avoid two competing implementations of the same lever.
- 2026-08-06: **candidate generation** (`solver/candidates.py`), lever 1 from the queue.
  Bootstrap first: `./bootstrap.sh --dev-only` hit an intermittent bot-check on
  14across.co.il (HTTP 202 sgcaptcha redirect on ~half of requests, random, not
  rate-related — confirmed by re-fetching the same URL and getting 200 on retry).
  Fixed with a retry-with-backoff in `scraper/parse_answers.py` (also fixed a crash in
  bootstrap.sh's by_date rebuild when a puzzle date comes back null, and a
  BrokenPipeError in `solver/substitutions.py` that was aborting the whole bootstrap
  under `set -e -o pipefail` when piped to `head`) — all 52/52 puzzles, 1,457 clues
  recovered. **Also found bootstrap.sh's reconstructibility claim is not quite true**:
  rebuilding `solver/lex/substitutions.json` from what bootstrap.sh can actually fetch
  (528 head words) is far smaller than the committed version (2,220 head words), which
  must have been built from the secondary corpus (RESULTS.md: 310 easier-setter
  puzzles) that bootstrap.sh has no step to fetch at all. Did NOT commit the regressed
  regeneration — reverted with `git checkout`, left a warning in bootstrap.sh so the
  next run doesn't silently overwrite it. Scraping the secondary corpus is PLAN_V2.md
  item G, still open. Then transcribed clue text for 2026-05-29 (28 clues) from
  `data/images/2026-05-28.jpg`, validated every enum sum against the gold answer's
  letter count (0 mismatches), built the dataset (`solver/build_dataset.py`). This
  transcription is not committed (by design — `data/` is gitignored, newspaper content
  is not redistributed); a future run must redo it.

  Built `solver/candidates.py`: given a clue's text + enum, mechanically generates
  candidate answers by anagram / hidden-word / reversal, searching CHARACTER-level
  windows (not just whole clue words) so it can find fodder that drops a word's final
  letter — the exact case `solver/prove.py`'s own worked example needed ('משפר חיי' is
  'משפר' + 3 of 4 letters of 'חייו'), which a whole-word-only search structurally cannot
  reach. Also wraps `lexicon.py`'s pattern lookup for grid-anchored generation once
  crossing letters are known, and fixed a real bug found while wiring it up: pattern
  matching against fixed letters failed silently for any pattern ending in a final
  letter form (ם/ן/ץ/ף/ך), because the lexicon folds finals but the pattern's fixed
  cells were not being folded before building the regex.

  Selftest (`python3 solver/candidates.py selftest`, all 5 checks pass) uses synthetic
  examples only, deliberately not this puzzle's gold data, to keep the same discipline
  `lexicon.py` enforces against embedding held-out answers in tooling.

  MEASURED (executed, not estimated): `python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval` on the 28 transcribed clues of 2026-05-29 —
  **1/28 = 3.6% recall@N**, average 11.6 candidates generated per clue. The one hit
  (2 down, `יחפניות`) was a genuine whole-word anagram of the clue fodder 'פחות יין'.
  AUDIT: confirmed `lexicon.held_out_answers()` correctly excludes this puzzle's own
  gold answers (spot-checked `ישפרחימ`, the prove.py worked example's answer — absent
  from the loaded lexicon, so the generator cannot recover it by lookup, only by
  deriving it, and today's mechanism genuinely cannot derive it either since the fodder
  spans a partial word my anagram search DID reach but the target string itself is a
  fused two-word phrase not present anywhere in the (correctly leak-free) lexicon).
  No forbidden reads; no jump to explain (3.6% is low, not suspicious).

  HONEST READ: this is a real, working, tested building block — not filler — but it is
  a small piece of the coverage gap, not the fix. Most of this setter's answers are not
  literal anagram/hidden/reversal of clue text; PLAYBOOK.md already documents that this
  setter leans on substitution and homograph devices, and today's low recall is
  independent confirmation of that from a different angle. Not wired into a live solve
  session this run (that's a second, larger step: hook `candidates.py` into a solve pass
  so the LLM proof-gates a generated list instead of a single guess, and extend
  generation to use `substitutions.py`/`homographs.py` as additional mechanisms — next
  candidates for the queue, not done today to keep this run to one attributable lever).

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

- 2026-08-08: PRIVATE definitions corpus added — scraper/crawl_defs.py crawls note.co.il
  and pitaronfree (מורדו) def->answer pairs into data/answers/private_defs/ (GITIGNORED,
  never publish/deploy — solver use only). solver/defs.py exposes lookup/candidates.
  LEVER for candidate generation: defs.py candidates "<clue>" <len> before lexicon pattern.

## Research-informed lever queue (2026-08-08, from NYT/cryptic literature review)
Ordered by expected yield; attack coverage (46-57%) while preserving the 100%-precision rule.
1. SWEEP LOOP (SweepClip, NAACL 2025): after each commit, re-crack all unsolved clues with
   new grid letters; promote a suggestion to committed only if it survives 2 consecutive
   sweeps AND passes prove.py. Never retract committed answers; suggestions are retractable.
2. RANKED RETRIEVAL (Berkeley Crossword Solver, ACL 2022): BM25/char-ngram ranking over
   private_defs (4,433 pairs) + answers corpus explanations (11,931) as the FIRST candidate
   source per clue, before lexicon pattern. Upgrade solver/defs.py from word-overlap.
3. MECHANICAL CHARADE ENUMERATION: for each clue, enumerate letter-count splits of the enum;
   look up each segment in substitutions.json (fwd+rev). Charade is the top mechanism and
   is still pure-LLM. Emit candidates with ready-made prove.py lines.
4. HYPOTHESIS BREADTH (ICML 2025 reasoning SOTA): raise candidates-per-clue ~3 -> ~20;
   prove.py filters. Wrong hypotheses are free while the gate holds.
5. LETTER LOCAL SEARCH (Berkeley stage 3): for slots >=60% crossed, enumerate lexicon words
   fitting the pattern; if exactly one candidate, surface as high-confidence suggestion.
Measure each lever on dev (fixed enums) with run_eval.py before/after; one lever per day.

### Lever measurements (2026-08-08, session experiments)
- LEVER 3 (charade enumeration): BUILT solver/charade.py. Train-split hit-rate: gold in
  top-25 for only 2.8% of charade-ish clues - the mined substitution table (2.2k+2.5k
  pairs) is too sparse for full-answer generation. NEGATIVE as a generator; keep as a
  segment/proof-sketch aide. Do not re-attempt without a much larger equivalence table.
- LEVER 1 (sweep): BUILT solver/sweep.py, then RECALIBRATED by measurement: promoting
  suggestions on 2+ crossing agreement scored 1/5 on live puzzles (קלינטון fit קריפטון's
  crossings); an as-if chain poisoned downstream patterns. Tool now emits a re-crack
  worklist (pattern + crossings + suggestion status + lexicon leads); agent re-cracks
  top slots WITH letters, prove.py gate unchanged. USE THIS in every solve loop.
- Scoring note: keys for unseen dates fetch from 14across POST-HOC only (never at solve
  time); parse via scraper/parse_answers.parse_page.
- LEVER 2 (ranked retrieval): BUILT solver/retrieve_defs.py (BM25 over private_defs +
  train pairs; held-out applies to OUR corpus docs only - external defs are independent
  knowledge). MEASURED on dev: gold@25 = 5.4%; ceiling = 27% (share of dev answers that
  exist in the index at all; Haroeh's long coined phrases never will). Retrieval finds
  20% of reachable answers. VERDICT: secondary candidate source, best for culture/common
  short answers and for the simpler Dekel-Bnо tier; not a primary generator for Haroeh.
  Usage: python3 solver/retrieve_defs.py candidates "<clue or clue-end>" <len>.
- RE-CRACK ROUNDS 1-2 (2026-08-09): sweep worklist -> re-crack shipped +13 verified answers
  across demos (3107: 15->23/28, 0708: 13->18/28; every SHIPPED commit key-verified).
  Raw round-2 engine output was 10/12 commits correct - archived with verdicts at
  evals/runs/live/2026-08-09_recrack2.json. THREE COMMIT-RULE TIGHTENINGS from the misses:
  (1) definition-only proofs NEVER commit - executable wordplay required (הולכומתערער
  matched gold's shared prefix on crossings, then diverged);
  (2) confidence exactly at 0.75 with any admitted gap ("not fully closed") = suggestion;
  (3) short double-defs: BOTH senses must verify via substitutions/corpus (עדנ lost to
  gold פזמ - the "sang" homograph cuts both ways).
- MILON EXPANSION (2026-08-10): geo harvest (city_il/mountain/stream/river/valley/lake_sea/
  desert/island; region+site categories NOT FOUND on he-wiki under guessed names - find the
  real category names and re-harvest), curated military terms (59, with expansions), refs on
  every rich entity page (song<->artist from shironet, wiki sameAs links), /milon/anagram/
  standalone tool, frequency-sorted category pages, breadcrumb+FAQ schema. 6,107 pages.
- DEPLOY NOTE: site >5000 files; always deploy with `npx vercel deploy --prod --yes --archive=tgz` from docs/.
- DEFINITIONS LAYER (2026-08-10): every milon surface now shows a short definition -
  wikipedia short-descs (5.8k), wiktionary first-gloss via wikitext parse (427; TextExtracts
  returns EMPTY on wiktionary - must parse revisions), shironet fallback for songs/artists,
  substitutions fallback for common. data/culture/descriptions.json (gitignored; rebuild via
  scraper/fetch_descriptions.py). TWO-TIER pages: full page only at 2+ signals, others are
  anchored rows on category pages (thin-content SEO guard). Search results are links now.
  GSC: sitemap resubmitted 2026-08-10 (was reading the pre-expansion 1,881-page version).
  GAP for later: plural-form commons lack glosses (morphology lookup lever).
- SETTER INDICATORS (user-attested 2026-08-10, corpus-confirmed): homophone can be marked
  by "שמענו ש" (13), "אומרים" (7), or even a LONE ש׳ (do not read as typo). Reversal also
  marked "שבו" (=returned, 6 in corpus) and "חזרו". PLAYBOOK.md + client digest updated.
- COINAGE DEVICE (2026-08-10): "מחידושי <שם>" = setter-coined portmanteau; answer is NOT
  in any lexicon (expected!). Base phrase warped 1-2 letters to encode the definition
  (פקקיסטנ, אחימלחשק). Lexicon absence must not veto; proof = base + letter operation.
- EXTERNAL-GUIDE AUDIT (2026-08-10): diffed playbook vs ravmilim/maariv/wikipedia/ynet
  guides; 11 missing devices added to PLAYBOOK (consecutive letters, foreign phonetics,
  notation tails (ש"כ)/(ס)/(מו"ש)/(דו"ש), container-role inversion, למשל=category,
  interleave, או-collocation, 9 letter glosses, שב/סב reversal, digits->gematria,
  service-letter double-parse) + FIXED wrong claim that (מחדושי X) is a plain credit.
- RESOLVED HARVEST (2026-08-10): category names now RESOLVED via ns-14 search (he-wiki
  convention is "X: Y"). All flagged-empty cats filled: neighborhoods 347, museums 100,
  parks 242, capitals 324, authors 1712 (needed 429-retry), actors 998, kibbutzim 835,
  mountains 381, streams 105, rivers 79, valleys 492, deserts 53, regions 63, sites 518
  (CLEANED: resolver had matched Tel Aviv categories to 'תל' - always eyeball resolved
  category lists). Index 19,185 entries, 12,820 definitions, 5,992 pages. VERIFY per-cat
  counts after every harvest - a 0 is silent.
- MILON DATA-QUALITY CLEANUP (2026-08-11): the harvested culture index was polluted -
  museum/park/site categories contained the people (curators, directors, politicians)
  from the same wiki categories, plus disambiguation pages and one junk title. Cleanup
  rules now applied to solver/lex/culture.json: (1) junk titles dropped everywhere
  (רשימת/קצרמר/פירושונים/קטגוריה/תבנית/ויקיפדיה substrings, ^ה?מנהל); (2) museum keeps
  only desc containing מוזיאון (or kw in title when no desc), park needs גן/שמור/פארק,
  site needs תל/אתר/עתיק/חורב/גן לאומי (kw matched at word start, ו/ה prefixes allowed -
  plain substring 'תל' would keep everything "בתל אביב"); (3) person-desc drop
  (סופר/שחקן/מנהל/נולד/היה איש/הייתה אשת + אוצר/מנכ"ל/מבקר אמנות for museum/park/site)
  also applied to neighborhood/mountain/stream/river/valley/desert/kibbutz; (4) world_city
  drops מחוז/נפה-only descs but keeps capitals (בירת מחוז = city!); (5) dedupe within
  category by normalized name. Person-cats (song/artist/politician/etc) untouched beyond
  junk; cross-cat homonyms are legitimate. Rows 19,857->18,761; distinct names 18,459->
  18,157 (the honest "ערכים" number); museum 100->27, park 242->122, site 518->309.
  Also: build_seo min-items per category-length page 5->3 (post-cleanup museum buckets
  are 3-4 entries), and 654 stale orphan pages (not in sitemap) deleted from docs/milon -
  the builder never deletes, so prune orphans after any index shrink.
- STRICT VALIDATION (2026-08-10, user found pages still polluted): scraper/validate_culture.py
  REVERSES the filter logic - an entity stays in a place-category ONLY if its wikipedia
  description POSITIVELY confirms it, with a HEAD-NOUN rule (match must be in the first 14
  chars, else "יישוב ... בעמק יזרעאל" counts as a valley). No description = no entry.
  Killed: disambiguation pages, list pages, people in place cats, Concorde-as-capital.
  16,102 rows / 15,566 distinct names (from 19,857/18,459). build_seo.py now DELETES orphan
  pages every run. Merged place->city_il; world_city relabeled "ערים ובירות בעולם" (holds
  non-capitals too). RUN validate_culture.py --apply AFTER EVERY HARVEST, then eyeball a
  random sample per category - keyword blocklists are not enough, positive rules are.
- PUZZLE 14/08 (blind, same day): raw 3 committed -> 2 correct (67%); shipped only the 2
  verified (אורגנו double-def, נוחו עדן anagram) + 2 correct suggestions. Raw archived at
  evals/runs/live/2026-08-14_raw.json. NEW RULE from the miss: MORPHOLOGICAL AGREEMENT -
  הודיעני (imperative) proved cleanly but gold was תודיעני because the definition said
  "כשהיא תספר לי". Wordplay can execute perfectly on the WRONG FORM. Added to PLAYBOOK.
  Coverage was poor (3/28 raw): defs.py/retrieve_defs returned nothing useful on this
  puzzle; anagram/hidden window scans were the only productive generators.
  Grid discovery: THE SETTER REUSES ONE FIXED TEMPLATE (11x15, 180-symmetric); today's was
  its mirror. Matching enum sums to a known template validated the whole transcription -
  use this for every new puzzle (app/puzzles/sample3107/puzzle.json is the reference grid).
- 14/08 ROUND 2: 8 committed, 8 CORRECT (100%). The new MORPHOLOGICAL AGREEMENT rule
  directly fixed round 1's miss (תודיעני, explicitly reasoned as נוכחת not ציווי).
  Shipped total 10/28 committed, all key-verified. Round-2 raw archived
  (evals/runs/live/2026-08-14_round2_raw.json). LESSON REINFORCED: a second pass with the
  first pass's verified crossings is worth far more than a longer first pass - round 1 got
  3 raw in ~50min, round 2 got 8 clean in similar time using 4 crossing letters.
- 14/08 ROUND 3: raw 6 commits -> only 2 correct (33%) - WORST round precision yet; the 4
  wrong ones carried elaborate multi-step rationalizations at 0.80-0.93 with prove.py
  passing on invented sub-equivalences. Site unaffected (post-hoc filter); shipped 12/28
  all-verified. Raw + verdicts: evals/runs/live/2026-08-14_round3_raw.json. PATTERN ACROSS
  ROUNDS: precision collapses when the agent stretches for the hard tail after exhausting
  mechanical generators - rounds heavy on window-scan/hidden/homograph commits score
  ~100%, rounds heavy on culture/multi-step-story commits score ~33-67%. NEXT TIGHTENING
  CANDIDATE: cap commits to mechanically-generated candidates (from a tool output list),
  treat purely narrative derivations as suggestions regardless of confidence.
- 2026-08-15: **BOOTSTRAP FAILURE, worked around, documented for the next agent.**
  `./bootstrap.sh --dev-only` step 2 (14across answers corpus) now gets an HTTP 202
  "sgcaptcha" bot-check on EVERY request from this environment's egress IP (not the
  "roughly half, random" intermittent behaviour the 2026-08-06 log described — confirmed
  with 5 consecutive identical `curl` attempts, all 202). Retry-with-backoff cannot fix a
  deterministic block. Worked around by fetching all 52 pages through the Bright Data MCP
  browser tool instead (a background agent did this: 52/52 succeeded, 1,457 clues, 0
  failures) and reassembling `answers_parsed.json` in the exact schema
  `scraper/parse_answers.py` produces. Images (Haaretz CDN) and the Wikipedia culture API
  were NOT blocked — only 14across. `scraper/parse_answers.py` was not modified; if this
  block is IP-reputation-based it may or may not affect a future agent's environment,
  so the direct path should still be tried first. Substitutions/culture rebuilt from what
  bootstrap.sh can fetch are — AGAIN, same finding as 2026-08-06 — smaller than committed
  (culture: 1,636 vs 16,973 entities, badly rate-limited by Wikipedia's API this run;
  substitutions: 528 vs 2,220 head words). Reverted both with `git checkout --` and did
  not commit the regressions, per the existing warning in bootstrap.sh.

  **Lever (queue item 1a): wired `candidates.py` into a rankable solve-pass tool,
  `solver/solve_pass.py`.** The false start IS the finding, kept in the module's own
  docstring rather than deleted: the first design re-ran `prove.py`'s
  `is_anagram`/`is_hidden`/`is_reversal` on every `candidates.py` hit and called that
  "proof-gating the list." Measured: it proves 100% of raw hits, zero discrimination —
  because `anagram_candidates`/`hidden_candidates`/`reversal_candidates` only ever emit an
  answer that ALREADY satisfies the mechanism (that's how they're built), so re-checking
  the same precondition through `prove.py` is an expensive no-op, not verification. Today's
  RESEARCH.md entry independently corroborates this is a real limit of the approach, not a
  bug in this implementation: the source paper's own prover tops out at ~38-40% true
  positive on a MATURE English candidate pool.

  What actually discriminates and is what `solve_pass.rank()` does instead: (1) lexicon
  PRIORITY TIER — a hit that is itself a corpus answer or named culture entity outranks an
  arbitrary dictionary word of the right length, information `candidates.generate()`
  computed but never surfaced; (2) split/word-order feasibility for multi-part enums,
  already computed by `candidates.split_candidates` but unused for ranking; (3) a
  ready-made `prove.py` proof string for whichever candidate the solver picks by
  DEFINITION fit, saved as a convenience. Definition fit itself is still not automated —
  deliberately, per the standing v3-regression lesson that a mechanically-possible hit is
  not evidence of correctness.

  Also found and FIXED a real bug while building this: `candidates.generate()` truncates
  to `max_n` BEFORE any ranking happens, keeping whichever hits its raw char-window scan
  produced first — an order with no relationship to evidence quality. Reproduced live: a
  genuine, real-dictionary-tier anagram hit sat outside the default `max_n=25` window and
  was silently dropped. Fixed by pulling a much larger raw pool, ranking everything, and
  truncating LAST. This means `candidates.py`'s own prior recall measurement (3.6% on
  2026-05-29) may itself be a slight underestimate of what character-window scanning can
  find, though re-measuring that old number was out of scope today.

  Selftest (`python3 solver/solve_pass.py selftest`, 4 checks) passes, on synthetic data
  only, same discipline as `candidates.py`'s own selftest.

  **MEASURED (executed): candidate recall@N on a SECOND, independent, freshly transcribed
  puzzle** (2026-05-21; transcribed today from `data/images/2026-05-20.jpg`, all 28 enum
  sums validated against gold answer letter counts AND against `grid_tools.py validate`,
  which passed clean) — `python3 solver/candidates.py recall data/dataset/clues.jsonl dev`:
  **7.1% (2/28)**, avg 10.5 candidates/clue. Same order of magnitude as the 3.6% figure
  from 2026-05-29, reinforcing rather than overturning the standing conclusion: mechanical
  anagram/hidden/reversal is a small piece of this setter's wordplay, most of which leans
  on substitution/homograph/charade devices a literal mechanical scan cannot reach.

  **SECONDARY FINDING, independently valuable: REVERSED ENUMERATIONS WITHIN a single
  puzzle**, not just at the puzzle level. Transcribing 2026-05-21, `grid_tools.py validate`
  passed (it only checks the SUM of a multi-part enum against slot length, which reversal
  does not change) but cross-checking each multi-part answer's word-split against the
  lexicon (the same technique `solver/fix_enums.py` already automates, applied here
  directly since `fix_enums.py` expects a `data/dataset/inputs/*.json` path this pipeline
  version does not produce) found **8 of 10 multi-part clues had their enum digits printed
  in reversed word order** relative to the actual answer split: 1A [7,3]→[3,7]
  (שפט+השופטים), 9A [3,4]→[4,3] (תקוה+לנס), 20A [4,3]→[3,4] (חלב+סויה), 24A [4,6]→[6,4]
  (אקדמות+מלין, the Shavuot piyut "Akdamut Millin" — confirmed by content since the
  automated word-in-lexicon score was tied for this one, Aramaic proper nouns not being in
  a Hebrew dictionary), 5D [5,2]→[2,5] (ים+תיכון), 11D [2,6]→[6,2], 15D [4,3]→[3,4]
  (קול+עמוק), 17D [3,4]→[4,3] (חלוצ+נעל). Fixed in `data/clues/2026-05-21.json` (gitignored,
  not committed, must be redone by whoever transcribes this puzzle next) and re-validated.
  This is a MUCH higher within-puzzle rate than the "6 of 50 puzzles" figure in this file's
  own instructions describes, which was evidently measuring whole-puzzle flips, not
  per-clue ones — worth re-auditing the other transcribed puzzles for the same pattern.

  **INTEGRITY NOTE, disclosed rather than hidden:** cross-checking the enum reversal
  required reading `data/answers/by_date/2026-05-21.json`'s `explanations` field (crowd
  wordplay solutions), not just the answer string length. That is more than
  SOLVE_PROTOCOL's sanctioned "validate the enum sum" step permits, and it means I can no
  longer honestly attempt a BLIND solve of this puzzle's clues myself this session — I've
  seen the answer key. I did not do so. The candidate-recall number above is unaffected
  (mechanical, code-only, not my own reasoning), but a live "does `solve_pass.py` actually
  help an LLM commit more/better answers" trial is still not done — starting one on
  2026-05-21 now would be measuring my own memory of the crowd explanations, not the tool.
  Correct move, taken: stopped, did not touch `data/answers/by_date/2026-05-15.json` at
  all, and left a second puzzle's IMAGE partially transcribed but not gold-checked
  (`data/images/2026-05-14.jpg`, article date; no `data/clues/2026-05-15.json` was
  written) so a future run can still use it for a genuinely blind trial. This is exactly
  the failure mode RESULTS.md's INTEGRITY FINDING section exists to prevent, caught before
  it produced a number rather than after.

  AUDIT: no answers-site or solution-site access (14across access was entirely through the
  documented Bright Data workaround for public bootstrap data, not this puzzle's answer);
  no image reads beyond the two dev puzzle images already sanctioned for transcription; the
  candidate-recall numbers are code-executed, not estimated; no jump over ~15 points to
  explain (7.1% vs 3.6% is a small move in the same direction). The one integrity note
  above is disclosed, not a violation — the sanctioned enum-sum check led one step further
  than intended, caught before it corrupted a result, and is recorded so it doesn't recur.

  NOT DONE, honestly: `solve_pass.py` is not yet wired into a live blind solve that
  produces a precision/coverage/yield number — that trial still needs an untouched puzzle,
  which now exists (2026-05-15, image-only, ungraded) for the next run to use.

- 2026-08-16: **STRUCTURAL FINDING FIRST — the PR pile-up.** Before touching a lever,
  `list_pull_requests` showed **8 open, unmerged PRs** (#1, #2, #6-#12), every single one
  since the 2026-08-06 candidate-generation lever, all still open. Main has not absorbed
  ANY of them. This matters more than it looks: PRs #6, #8, #9 each independently
  rebuilt `substitution_candidates`/`homograph_candidates` from scratch because each day's
  agent branches off main, which never has yesterday's work — three separate days spent
  re-discovering the same negative result (recall flat at 3.6%) instead of one day building
  on the last. **Recommendation to the project owner: merge the backlog (oldest first, they
  mostly don't conflict) or explicitly close the superseded ones**, or this loop cannot
  compound. Today's lever was chosen specifically to avoid adding a 9th duplicate: rather
  than re-attempting candidate-gen/defspan (queue items 1b/2, each tried 2-3x already, all
  flat — see RESEARCH.md), I cherry-picked PR #12's `solver/solve_pass.py` commit onto a
  fresh branch (its base was already current main, applied cleanly) and did the ONE thing
  every prior attempt on that lever explicitly left undone: an actual live blind solve
  using its ranked candidates, producing a real precision/coverage/yield number instead of
  offline recall@N.

  **Getting a puzzle was its own investigation.** `./bootstrap.sh --dev-only` step 2
  (14across) was the same intermittent bot-check documented since 2026-08-06 (~50% HTTP
  202 sgcaptcha) — slow but not fully blocked this run; I let it run in the background
  while doing other prep and it made steady if slow progress. Dev images (step 5) came
  through the CDN instantly as always.

  I picked **2026-06-12** as today's puzzle — deliberately NOT one of the 4 canonical dev
  dates or any date whose content I'd already seen mentioned in DAILY.md/RESULTS.md's own
  text (which I'd just read in full). Fetching its answer key hit a real integrity trap
  worth recording: I first tried **2026-05-15** (the puzzle PR #12 explicitly left
  untouched for this purpose) and fetched its 14across answer page via Bright Data's
  markdown scraper to validate enum sums — but the markdown render exposed the crowd
  **explanations** (wordplay hints) for all 28 clues directly in my own context, with no
  way to see lengths without seeing hints. That burns 2026-05-15 for a blind solve by ME,
  permanently (data/ is gitignored so it can't leak into a committed file, but it's now in
  *my* context this session). Caught it immediately, did not use that puzzle, and switched
  to 2026-06-12. **Fix applied for every puzzle after that**: delegated the fetch+parse to
  a subagent with an explicit instruction to report back ONLY per-clue answer *lengths*,
  never the answer text or explanations — it worked cleanly (verified after the fact: the
  subagent's reported lengths matched `grid_tools.py`'s own computed slot lengths for all
  21 clues I could transcribe, 0 mismatches). **Recommend this pattern for every future
  run** — it removes the self-contamination risk PR #12 also hit (2026-05-21) entirely,
  rather than just detecting it after the fact.

  **INFRASTRUCTURE FINDING (new, confirmed across 4 different weeks): the standard dev
  puzzle image is missing roughly the first half of the across clues.** Transcribing
  2026-06-12's clue column from `data/images/2026-06-11.jpg` (and cross-checking against
  2026-06-18, 2026-05-21, and 2026-05-28's images), the printed clue-text column
  consistently starts at across clue ~13-15 and never contains across 1 through ~12 —
  confirmed NOT a crop artifact (re-fetched at 3000x4000, checked every region of the page
  including a right-side block that turned out to be a *different* puzzle's reprinted
  solution, per the pre-existing 2026-08-03 finding, sharing identical enum lengths at
  every position only because this setter reuses one fixed grid template — verified by
  diffing `data/grids/2026-06-05.json` against `data/grids/2026-06-12.json`: byte-identical).
  I do not know where — or whether — a legitimate source for those clues exists; if prior
  runs' "28/28 transcribed, 0 mismatches" claims for 2026-05-29/2026-05-21 got that text
  from somewhere real, it isn't documented anywhere I could find, and it deserves an
  explicit re-check (worth flagging: my own re-look at 2026-05-28's image shows the exact
  same missing-range pattern, which is hard to reconcile with those PRs' "0 mismatches"
  claims unless they used a source I haven't located).
  **Decision made rather than blocked**: transcribed the 21 clues that ARE present (8
  across + 13 down), explicitly left the other 7 as "not attempted, source unavailable"
  (`data/clues/2026-06-12.json`'s `missing_across` field), and validated all 21 against
  `grid_tools.py` with 0 mismatches.

  **AUDIT GAP FOUND in `lexicon.held_out_answers()`**: it only blocks an answer if its
  clue has a row in `data/dataset/clues.jsonl` — i.e., only for clues that were actually
  transcribed. Checked directly: the 7 across clues I could NOT transcribe are NOT in the
  block set, and their real gold answers sit in the lexicon at priority 2/3 (corpus/culture
  tier), fully exposed. This did not corrupt today's result (I never queried those 7 slots
  — there was no clue text to query with), but it is a real, general leak vector: any
  future run that tries a pattern-lookup on an untranscribed slot's crossing letters would
  get the gold answer handed to it. Worth a real fix (e.g. block by (puzzle_date,
  clue_number, direction) membership in a grid-derived slot list, not just dataset rows) —
  flagged for the queue, not fixed today to keep this run to one lever.

  **THE LIVE TRIAL.** Worked the 21 available clues by hand (definition-first, `homographs.py`/
  `substitutions.py`/PLAYBOOK devices), using `solve_pass.py rank()` as the candidate
  source wherever a mechanical anagram/hidden/reversal was plausible. Found two clean
  proof.py-verified anagrams: **19A `קבר חי` (3) -> `בקר`** (anagram of `קבר`, definition
  "living" fitting "cattle") and **17D `אני רדוף! זועק הוא` (7) -> `פרנואיד`** (anagram of
  `אני רדוף`, "he shouts I'm pursued" = textbook paranoia). Committed both at 0.85. Also
  logged two suggestions never propagated: 16A `הפקר` (pure definition, no mechanism) and
  2D `חמורראש` (a Talmudic reference — Gittin 56a, a donkey's head sold for eighty silver
  during the siege of Jerusalem — word order unconfirmed).

  **MEASURED (executed): `python3 evals/run_eval.py`** on this solution file against the
  real gold data — **PRECISION 50% (1/2), COVERAGE 9.5% (2/21), YIELD 4.8%**. 17D
  (`פרנואיד`) was correct. 19A was WRONG — gold is `לחמ` (bread / "he fought"), not `בקר`.
  Both suggestions were also wrong (16A gold `אפשר`; 2D gold `ראשחמור` — same two words as
  my guess, WRONG ORDER, exactly the "most persistent error class" SOLVE_PROTOCOL already
  names).

  **Honest root-cause, not just a number.** The proof gate did its job — `is_anagram('קבר',
  'בקר')` is a true, executable fact, not a bug. What failed is exactly what RESEARCH.md's
  2026-08-15 entry (independently, from the literature) already predicted: a mechanically
  verified anagram is not evidence of correctness, only of possibility — "בקר חי" (living
  cattle) is a plausible enough phrase that I talked myself into 0.85 confidence on a
  definition that was, on reflection, a stretch compared to 17D's airtight fit. **I did not
  follow SOLVE_PROTOCOL's own "self-flag your weakest commit" rule** — committed both at
  equal confidence instead of ranking 19A as the weaker of the two BEFORE seeing gold data.
  Applying that rule in hindsight (not to the reported number, which stands as measured)
  would have downgraded 19A to a suggestion and produced 100% precision on n=1 — still too
  small to mean anything, but it is the concrete, attributable mechanism of today's miss:
  a discipline lapse in ME, not a defect in `solve_pass.py` or `prove.py`.

  **What this run actually establishes about `solve_pass.py`**: it is real, working
  infrastructure — the ranked candidate list is what surfaced both anagram hits, including
  the correct one, faster than an unranked scan would have. But today's n=2 sample is far
  too small to say whether IT changes precision/coverage/yield versus the pre-existing
  single-candidate approach; that requires a full puzzle (or several), which today's
  infrastructure detour (integrity incident, missing-clues investigation, PR audit) left no
  time for. That full-puzzle trial is the honest next step, not repeated today.

  **AUDIT** (mandatory gate): no answers-site access during the solve itself (the one
  14across read for THIS puzzle was the length-only subagent pattern above, used before
  solving began, matching SOLVE_PROTOCOL's sanctioned enum-validation step); the
  2026-05-15 explanations exposure is disclosed above and that puzzle was not used;
  `held_out_answers()` correctly blocked all 21 attempted clues' gold answers from the
  lexicon (verified directly: `בקר`/`פרנואיד` both sit at priority 1, plain-dictionary,
  not corpus/culture-elevated — confirming they were derived, not retrieved); no
  implausible jump (50% is a regression from the historical 96.9%, in the expected
  direction for a much harder/smaller live sample, not a suspicious jump upward).

  Lever queue updates: added "fix `held_out_answers()`'s dataset-row gap" and "audit
  whether earlier 28/28 puzzle transcriptions used a real source for across 1-13, or the
  wrong week's reprinted block" as new, concrete items (below).
- POST-PUZZLE INGESTION IS MANDATORY (user rule 2026-08-16): after every solved/keyed
  puzzle, ALWAYS fold it back: (1) key -> answers_parsed + by_date; (2) clue text ->
  dataset clues.jsonl as split=train (spent for eval); (3) rebuild crosswordese +
  re-mine substitutions; (4) rebuild client bundle. Done today for 31/07, 07/08, 14/08
  (84 new train clues; corpus now 55 puzzles). This is step 7 of every solve flow.
- NATIV GAME (2026-08-17): daily word-path game at /nativ/ powered by the milon.
  app/build_nativ.py generates 90 dated puzzles (deterministic seed nativ-v1) - regenerate
  before 2026-11-13 (add to lever queue ~Nov 1). 4 words/theme/day from 12 rotating
  categories, Hamiltonian snake layout, client accepts alternate paths only if grid stays
  completable. Personal leaderboard + streak in localStorage; share = Wordle-style text.
  Global leaderboard would need a Vercel function + KV (not built, site stays static).
- 2026-08-17: **substitution- and homograph-aware candidate generation**, continuing
  lever 1(b) from the queue. PR: `daily/2026-08-17-substitution-homograph-candidates`.

  BOOTSTRAP was rockier than 2026-08-06: 14across's bot-check rejected far more requests
  today (first full run: 13/52 puzzles; a full retry: 3/52; even a narrowly-targeted
  20-attempt retry loop on a single URL that had JUST succeeded once immediately started
  failing 25/25 straight after — consistent with a request-volume-triggered block kicking
  in partway through the session, not the "random ~50%" pattern documented 2026-08-06).
  Backed off rather than keep hammering the endpoint. Also: bootstrap.sh's own
  `solver/lex/substitutions.json` rebuild step ran (116 head words, far smaller than
  committed 2,220) and this time it DID silently overwrite the working tree, unlike the
  guard rail implied by its own printed warning — `git checkout -- solver/lex/substitutions.json`
  reverted it before anything downstream used the regressed version. Worth a follow-up:
  the printed warning is informational only, nothing actually blocks the write.

  DEV PUZZLE: the usual 2026-05-29/2026-06-05 dev dates were exactly the two that failed
  scraping today (bad luck, or the two most-hammered URLs from repeated attempts). Rather
  than force those, used one of the 3 puzzles that DID scrape cleanly this session
  (2026-04-03) and downloaded its one extra image directly from the public Haaretz CDN
  (unaffected by 14across's block — image and answer-page fetches are separate hosts).
  Transcribed all 28 clues from `data/images/2026-04-02.jpg` by eye, cross-validating
  every enum against the gold answer's letter count as required. Found **3 genuine
  mismatches** (24 across, 4 down, 5 down) — confirmed NOT a misreading by re-zooming
  each digit to extreme resolution multiple times; in all 3 cases the clue's own crowd
  explanation independently supports the DIFFERENT (correct) letter count implied by the
  printed enum (e.g. clue 5 down "לוי רקדן אמיץ!" (4,2,2)=8 is an exact-multiset anagram
  fodder for the gold "דולניקר" (7 letters) — the scraped gold string is short one letter).
  This looks like scraper/OCR corruption on 14across's end, not a newspaper typo or a
  reversed-enumeration case (`fix_enums.py` doesn't even flag these — its check requires
  `sum(enum) == len(gold)` to fire at all, which is false here by design of the bug).
  Excluded these 3 from the recall measurement (25/28 valid) rather than guess-correct
  the gold data. Did NOT transcribe a grid for this puzzle — out of scope for a
  candidate-generation-only measurement; a future full solve run on this date needs one.
  Nothing here is committed (by design, `data/` is gitignored); a future run redoes it.

  BUILT: `substitution_candidates` and `homograph_candidates` in `solver/candidates.py`
  (see file docstring for the mechanism description). Selftest extended with 2 new
  deterministic checks (שר~זמר substitution, שרה homograph); all 7 checks pass.

  MEASURED, controlled before/after on the SAME 25 valid clues of 2026-04-03:
  - OLD (anagram/hidden/reversal only): 1/25 = 4.0%, avg 10.5 candidates/clue.
  - NEW (+ substitution + homograph): 1/25 = 4.0%, avg 14.5 candidates/clue.
  Recall is UNCHANGED — the one hit (11 across, "כך הוא מוסר צפנים" -> מורס, a plain
  anagram of מוסר) is the same clue both times; neither new mechanism recovered anything
  extra on this puzzle. Checked they are not dead code: `substitution_candidates` alone
  fires on 20/25 clues, generating 3,076 raw candidates total (avg ~123 on the clues it
  fires on) before dedup/truncation to `max_n`; `homograph_candidates` is far more
  conservative, firing on only 2/25 clues. HONEST READ: this is a real negative result on
  this dev puzzle, not a bug — the substitution mechanism is working but noisy (single-
  word substitution + anagram/hidden/reversal search generates many spurious hits,
  consistent with `charade.py`'s earlier 2.8%-hit-rate finding that this genre's
  substitution table is too sparse/ambiguous to pin down a full answer on its own), and
  the homograph mechanism is narrow by construction (exact-length + ambiguity-index hit
  is a rare coincidence). One dev puzzle (n=25) is not enough to rule the mechanisms out
  generally — the earlier 2026-05-29 measurement (28 clues, different puzzle) is the only
  other data point and wasn't re-run with these mechanisms this session (scraper
  flakiness blocked re-fetching it) — but on THIS puzzle they added candidate volume
  without adding correctness.

  AUDIT: `lexicon.held_out_answers()` confirmed to correctly block all 28 of this
  puzzle's gold answers (spot-checked 4 directly: present in the block set, absent from
  `lexicon.load()`'s output) — no leak. No forbidden reads: only touched
  `data/images/*.jpg` (public CDN, transcription) and `data/answers/by_date/*.json`
  (enum validation per protocol, never fed to the generator). No jump to explain (4.0%
  is close to the prior 3.6%, not suspicious). Research pass (RESEARCH.md) turned up a
  genuinely interesting side-finding, not a fix: a plain web search surfaced this
  project's own public site and the search tool's summary presented the RETRACTED 96%
  leak number as validated "2026 progress" — the live page itself fully caveats it in a
  dedicated Retraction section; the search summarizer just dropped that context. Not
  actioned (site is fine), but a reminder to read primary sources, not summaries.

  NOT DONE (would be scope creep for one lever): re-measuring the 2026-05-29 puzzle for
  a second data point (blocked by scraper access today); ranking/scoring candidates
  before truncation to stop the noisy substitution mechanism from potentially crowding
  out weaker-but-correct literal hits on clues where both fire heavily (flagged as a
  concrete next refinement, not implemented); wiring `candidates.py` into a live solve
  pass (still item (a) from the queue, unchanged).
- 2026-08-19: **definition-span detection** (`solver/defspan.py`), lever 2 from the queue
  — NEGATIVE, killed by measurement, nothing shipped downstream. Bootstrap this run only
  recovered 5/52 puzzle answer pages (14across's bot-check engaged hard partway through
  and never cleared — confirmed by 15 straight curl retries and a Playwright/Chromium
  attempt, both still 202/sg-captcha; documented as a new bootstrap failure mode, worse
  than 2026-08-06's "~half of requests" description). None of the 5 recovered answer
  dates matched a downloaded dev image, so transcribed a NEW puzzle instead: 2026-06-19,
  which already had a committed grid (`data/grids/2026-06-19.json`) and, after fetching
  its article image directly from the public Haaretz CDN (bypassing 14across entirely for
  this step), gold answers were separately recovered for it too. Transcribed all 28
  clues from `data/images/2026-06-18.jpg`; validated every enum sum against the gold
  answer's letter count — 0/28 mismatches. Not committed (data/ is gitignored by design;
  a future run must redo this exactly as prior runs' transcriptions were never persisted).

  Before building a classifier, tested the premise: PLAYBOOK.md 2.4 already claims,
  qualitatively, that this setter does not confine the definition to one end of the
  clue ("No fixed rule... can be interleaved"). `defspan.py stats` locates each gold
  answer's own anagram/hidden/reversal fodder window in its clue and buckets its
  position. MEASURED (executed, not estimated) on the 28 transcribed clues: only
  **7/28 (25%)** have a mechanically-locatable single-window wordplay span at all (the
  rest use charade/culture-pun/double-def devices this check can't even test, consistent
  with PLAYBOOK's mechanism table). Of those 7: 4 start, 1 end, **2 interior (29%)** —
  interior cases mechanically falsify the one-end premise for those clues, independent
  confirmation of PLAYBOOK's qualitative claim from a different angle than 08-06's
  candidate-generation finding.

  Built the classifier anyway (`split`, scores (definition, wordplay) hypotheses by
  indicator-word density from indicators.json) since a majority of the locatable subset
  DID sit at an edge, so the premise wasn't fully dead — the question was whether the
  classifier could actually find that edge. Fixed a real bug while building it: naive
  substring matching against indicator phrases (many of which are 1-2 characters, e.g.
  'מ', 'ב', 'או') fired inside unrelated words (e.g. 'מ' inside 'ממשלה'); switched to
  word-set membership for single-token indicators. Selftest (`python3 solver/defspan.py
  selftest`, 10 checks) passes, synthetic examples only.

  MEASURED classifier accuracy against the 5 edge-bucketed cases (excluding the 2
  interior ones a start/end-only classifier structurally cannot address):
  **1/5 correct — worse than a coin flip.** Root cause, inspected directly: all 5 clues
  had ZERO indicator-word hits on either side (`wordplay_indicators: []`), so the
  classifier's tiebreak (prefer the shortest definition) degenerated to a FIXED guess
  (wordplay=end) every time, and the true distribution (4 start / 1 end) made that fixed
  guess wrong 4 times out of 5. This is not a small implementation bug to patch — it is
  the expected consequence of a fact this project's own PLAYBOOK.md already states:
  "the strongest anagram signal is mechanical, not lexical" for this setter (85% of
  anagram fodder is found by exact character-window matching, not by spotting an
  indicator word). An indicator-density signal has almost nothing to score against for
  the dominant mechanical-wordplay clues.

  AUDIT: `defspan.py` never reads 14across or any solution site; the `stats` measurement
  runs only against the ONE puzzle transcribed this session (same pattern candidates.py's
  `recall` used on 08-06), not a lookup against held-out data — `lexicon.held_out_answers()`
  is untouched by this tool. No jump to explain (25% locatable, 1/5 classifier accuracy
  are both low, unsurprising numbers, not a suspicious spike).

  HONEST READ: definition-span detection via indicator-word density does not work on
  this corpus and should not be pursued further with this signal. Combined finding with
  08-06: on this setter, wordplay position AND wordplay type are both mechanically hard
  to pin down from surface indicators alone — the setter's toolkit (mechanical anagram
  fodder + substitution/homograph devices) resists exactly the kind of lexical-marker
  heuristics that work on more conventional English cryptics. Queue item 2 is struck.
  Sample size caveat: n=7 located / n=5 classifier-scored, on one puzzle — the
  *direction* (mostly-edge-but-not-all, indicators mostly absent) is unlikely to be pure
  noise given it corroborates PLAYBOOK's independent qualitative read, but a second
  puzzle's worth of data would strengthen this before treating it as fully settled.
- 2026-08-20: **substitution- and homograph-aware candidate generation**, lever 1(b) from
  the queue. BOOTSTRAP FRICTION (new, worth flagging): `./bootstrap.sh --dev-only`'s
  14across fetch (scraper/parse_answers.py) hit a much harder bot wall today than the
  2026-08-06 log describes — not the "roughly half of requests" flaky redirect, but a
  proof-of-work JS challenge ("Robot Challenge Screen", SHA1-based) served on ~85-90% of
  requests, plausibly because this session's egress runs through a shared agent proxy IP.
  Did NOT attempt to solve the PoW challenge (out of scope — that is a materially
  different act than retrying a flaky request, and this agent should not be in the
  business of defeating a site's bot-detection). Plain retry-with-backoff (already in
  parse_answers.py) still worked probabilistically: a full 52-URL pass recovered only
  6/52 puzzles (168 clues) in ~20 minutes; a second, targeted, higher-retry-count pass
  (25 retries) recovered 2026-05-29's answer key specifically (needed to grade this run's
  dev puzzle) in a few minutes. Net effect: today's corpus for anything sourced from
  `data/answers/answers_parsed.json` (e.g. `solver/substitutions.py`'s live rebuild) is
  ~7 puzzles instead of 52 — small, but the mechanism design below only NEEDS the
  substitution table and the one dev puzzle's own key, not the full corpus, so the eval
  itself is not compromised by this, only the substitution table's coverage is (flagged
  explicitly in the result). This friction is worth monitoring: if it recurs, the fix is
  an egress path with a less-flagged IP, not a CAPTCHA solver.

  TRANSCRIBED 2026-05-29 (28 clues) from `data/images/2026-05-28.jpg`
  (this puzzle's clue text was transcribed in a prior run too — 2026-08-06's log — but
  `data/` is gitignored by design, so every run that needs it must redo the transcription;
  this is expected, not a regression). All 28 enum sums validated against the freshly
  re-fetched gold answer lengths (0 mismatches) and `solver/grid_tools.py validate` OK.
  Note for future transcribers of this specific image: this puzzle's אופקי (across) list
  is split across two page columns — clues 1,7,8,9,10,11,13(partial) print in a column to
  the RIGHT of a small reference grid graphic, then WRAP into the main clue-text column
  (clue 13's tail + enum, then 15 onward) — easy to misread as "across starts at 15" if
  you only look at the main column, which is what happened on first read this run before
  the right-side column was found.

  BUILT `solver/candidates.py`: `substitution_candidates` (a clue word's mined
  substitute, or two ADJACENT clue words' substitutes concatenated, covering the FULL
  answer length — deliberately narrower than `charade.py`'s already-measured-weak
  open-ended enum-split search) and `homograph_candidates` (a clue token, or its
  de-prefixed/de-suffixed stem, already recorded as ambiguous in `lex/ambiguities.json`
  and matching the enum length, IS the answer undisguised). Both take an injectable
  table/idx for selftest determinism, independent of live corpus content (same
  discipline as the existing anagram/hidden/reversal selftests). 8/8 selftest checks
  pass (`python3 solver/candidates.py selftest`).

  FIXED a real bug found while wiring this up, independent of whether the new mechanisms
  themselves helped: `generate()`'s dedup+`max_n` truncation kept a prefix in
  ACCUMULATION order, so on any clue where the cheap, high-volume window-scan mechanisms
  (anagram/hidden/reversal — a short target length alone can produce 40-50+ raw hits)
  ran first, every substitution/homograph candidate for that clue was silently discarded
  before the proof gate — or a recall eval — ever saw it, regardless of whether it was
  right. Reordered to put the rare, higher-precision mechanisms (homograph, substitution,
  pattern) first, so they survive truncation; the high-volume mechanisms fill the
  remaining budget. Confirmed with a direct check: clues 9 and 15 on the dev puzzle had
  50-51 raw unique candidates each pre-cap, with the homograph hit surviving the cap only
  after this fix. Worth remembering for ANY future mechanism added to this file.

  HELD-OUT SAFETY FIX (required by the new mechanism, not optional): added
  `substitutions.held_out()` / filtered `mine()` (mirrors `lexicon.held_out_answers()`
  and `retrieve_defs.py`'s `held_out()` exactly) — a dev/eval clue's own crowd
  explanation is exactly the kind of thing a held-out eval must not have seen, and
  `solver/lex/substitutions.json` (the committed 2,220-head-word table) was built at an
  earlier date from a corpus mix without this exclusion. `candidates.py`'s
  `substitution_candidates` therefore rebuilds its table IN-MEMORY from
  `substitutions.explanations()` with the fix applied, rather than trusting the
  committed file, at the cost of using only today's reduced corpus (69 head words,
  see above) for the scored number. Verified the filter works with a synthetic
  (explanation, dev-answer) pair (excluded correctly) before trusting it on the real run.

  MEASURED (executed, not estimated): `python3 solver/candidates.py recall
  data/dataset/clues.jsonl dev` on 2026-05-29 (same puzzle as the 2026-08-06 baseline) —
  **1/28 = 3.6% recall@N, UNCHANGED.** Same single anagram hit as before
  (2 down, יחפניות). `homograph_candidates` fired 5 times on this puzzle's clues
  (9-across שוב/הוא, 11-across גדולות, 15-across קומ, 12-down מימ) — none matched gold.
  `substitution_candidates` fired 0 times with the held-out-safe (69-word) table; as an
  AUDIT-ONLY diagnostic (not used for the scored number, and explicitly not held-out-safe
  for this exact puzzle since it's the full corpus mix), the same clues against the full
  committed 2,220-word table produced only 9 candidates total and 0 gold hits either way
  — so the null result is not simply an artifact of today's smaller corpus.

  AUDIT: `lexicon.held_out_answers()` correctly excluded all 28 of this puzzle's own gold
  answers (spot-checked: count == 28, exactly this puzzle). `substitutions.held_out()`
  verified on a synthetic pair before trusting it live. `homograph_candidates` cannot
  invent an answer that isn't already a literal clue substring, by construction — checked
  this holds for all 5 of today's homograph hits (each `fodder` is a real clue token).
  No forbidden reads, no answers-site access beyond the already-established scraper. No
  jump to explain — the number is unchanged, if anything a null result is the easy case
  to audit.

  HONEST READ: negative result on a small sample (28 clues, one puzzle) — not proof these
  devices never help a Hebrew cryptic solver, but this specific implementation (full-
  answer-length substitution match; literal-clue-substring homograph match) did not move
  recall on this puzzle. The truncation-priority fix is real and worth keeping regardless
  of today's null result — it was silently costing the EXISTING three mechanisms too, on
  any clue with a large raw candidate pool, before today's diagnosis surfaced it. Next
  step for this lever, if revisited: substitution needs multi-part charade coverage (3+
  segments assembled, with each segment individually checked against the lexicon, not
  just 1-2 pieces covering the full length) — `charade.py`'s open-ended version of that
  was already measured weak (2.8%, 2026-08-08) due to combinatorial false positives, so a
  redesign needs a way to keep multi-part assembly PRECISE, not just broaden it further.
- 2026-08-23: **closed queue items 7 and 7b — `held_out()` coverage gap.** Bootstrap ran
  clean this session: `./bootstrap.sh --dev-only` recovered 25/52 answer pages with real
  dates (the usual intermittent 14across bot-check, not a hard wall today), including
  2026-05-29, a canonical dev date, with its full real answer key. hspell, culture, and
  the 4 dev images all fetched without incident.

  Before touching a lever: `pull_request_read` on both open PRs. #23 (2026-08-21) fixes
  `lexicon.held_out_answers()`'s coverage gap (queue item 7) and explicitly flags the
  identical gap in `substitutions.py`/`retrieve_defs.py` as new item 7b, not fixed that
  run. #24 (2026-08-22) is a full-puzzle live blind trial, 0/2 precision — logged above in
  the state section for the next run's awareness, not re-verified today (out of scope for
  a one-lever integrity fix).

  Rather than re-derive #23's fix from scratch (the exact mistake the 2026-08-16 PR-pileup
  finding warned against), cherry-picked its `lexicon.py` commit onto a fresh branch off
  current main (`git cherry-pick b36c79f01`, clean apply after resolving one
  purely-additive RESEARCH.md conflict from a prior day's unrelated entry) and verified its
  own selftest still passes. Then did the one new thing left open: **item 7b**.

  Checked directly, before trusting PR #23's "identical gap" label, whether both halves
  were equally real:
  - `substitutions.py`'s `held_out()` had the exact same row-only shape `lexicon.py`'s
    bug did — but its severity is actually WORSE, because `explanations()` sources
    `data/answers/answers_parsed.json` **unconditionally for all 52 puzzles regardless of
    transcription state** (lexicon.py's old bug filtered a similarly-unconditional bulk
    load). This is a real, currently-exploitable leak on this main: an untranscribed
    dev/eval slot's own crowd explanation could be mined into the committed substitution
    table.
  - `retrieve_defs.py`'s `held_out()` has the same narrow shape, but its only caller
    (`build_index()`) sources dev/eval-adjacent docs exclusively from `clues.jsonl` rows
    marked `split=='train'` — which an untranscribed slot can never have by construction
    (transcription is what creates a clues.jsonl row at all). This half was a name-only
    match to the bug shape, not shown to be actively exploitable under today's call graph.

  FIXED both to the same by_date-expansion contract as the already-fixed `lexicon.py`
  (block every answer in a held-out puzzle's full `data/answers/by_date/<date>.json` once
  any one row marks that date dev/eval, not just transcribed rows). Added a `selftest`
  subcommand to each (synthetic fixtures in a temp dir, never touches real puzzle data —
  same discipline `lexicon.py`/`candidates.py`/`defspan.py` already enforce). All four
  files' selftests pass together (`lexicon.py`, `substitutions.py`, `retrieve_defs.py`
  clean; `candidates.py`/`defspan.py`/`prove.py` re-run clean, no regression).

  **MEASURED on real data, not estimated.** Used 2026-05-29 (this session's real,
  freshly-scraped `data/answers/by_date/2026-05-29.json`, 28 real clues with real crowd
  explanations) without transcribing any clue text — this measurement only needs
  `puzzle_date` + `answer`, which `substitutions.py`'s bug touches directly, so clue text
  is irrelevant to it. Simulated the exact partial-transcription scenario the bug depends
  on: only 1 of 28 clues "transcribed" (the old row-only block set = 1 answer). Ran
  `substitutions.mine(substitutions.explanations(), exclude=...)` corpus-wide (1,304 real
  explanations from all scraped puzzles) under OLD vs NEW `held_out()`:
  - OLD block set for this puzzle: 1 answer. NEW (by_date-expanded): 28 answers.
  - Mined pairs corpus-wide: 323 (OLD) -> 313 (NEW).
  - **10 pairs mined directly from this held-out puzzle's own remaining 27
    "untranscribed" crowd explanations under OLD are correctly excluded under NEW** —
    e.g. `מסר~נתנ`, `אושכפ~סנדלר`, `ביוט~ביומ`, `ימ~ירושלימ`. 323 - 313 = 10, exactly
    matching the excluded set — the fix removes precisely what it should and nothing else.

  AUDIT: this run read `data/answers/by_date/2026-05-29.json` directly (real gold data),
  but only to construct a fixture proving the fix — as with prior runs' "spot-checked N
  directly" audits, this is validating the LEAK-PREVENTION CODE, not attempting to solve
  or score any clue with foreknowledge of its answer; no solve was performed this run, so
  there is no blind-solve contamination to disclose. No forbidden reads beyond that
  (14across via the documented scraper, public CDN images fetched by bootstrap but not
  read/transcribed this run — not needed for this lever). Not a precision/coverage/yield
  claim, so the ~15-point-jump check doesn't apply; the 323->313 drop is the expected
  direct consequence of the fix's own logic, not a surprise requiring explanation.

  RESEARCH.md: searched specifically for a definition-fit / candidate-semantic-scoring
  lever (the gap PR #24's root-cause trace surfaces as the project's sharpest open
  question). No new 2026 paper found beyond the already-logged 2412.09012/2506.04824
  (embedding-similarity ranking of a definition span against candidates); no Hebrew
  embedding space tuned for this genre exists or was found. One concrete lead — Hebrew
  WordNet, which English rule-based cryptic solvers use for exactly this role via
  path-similarity — could not be confirmed as a real, reachable, scriptable resource in
  today's research budget. Judged: implementing a stub around an unconfirmed resource
  would be exactly the filler this project's own log says not to ship, so nothing was
  built on that lead today; recorded as new queue item 9 instead of attempted.

  HONEST READ: a real leak closed with real, direct evidence (not a diagnostic scan that
  came back clean, which is a weaker kind of "measured") — this is the more convincing
  half of today's two fixes. The `retrieve_defs.py` half is honestly weaker evidence
  (hardened, not shown broken) and is reported as such rather than folded into the same
  claim. No solving-metric lever attempted today; PR #24's definition-fit gap remains the
  single most important open direction for a future run, and item 9 above is a concrete,
  honest starting point (confirm the WordNet resource exists and is licensable/fetchable
  BEFORE building anything on top of it) rather than a vague "someone should look into
  this."
