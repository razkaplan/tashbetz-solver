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
| **Candidate recall@N (offline, mechanical only, anagram/hidden/reversal)** | 3.6% (1/28) on 2026-05-29 (2026-08-06) | not yet a target — diagnostic |
| **Candidate recall@N with substitution+homograph mechanisms added** | **NOT MEASURED today — 14across access blocked, see log** | — |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added: **substitution- and homograph-aware candidate generation**
(`solver/candidates.py`: `substitution_candidates`, `homograph_candidates`), extending
the mechanical generator from 2026-08-06 (anagram/hidden/reversal/pattern) with the
two devices PLAYBOOK.md says this setter actually favors. Code is built, selftested
(8/8 checks pass — 2 new checks against real committed substitution/ambiguity data),
and audited for the leak mode this project has been burned by before (see log). It is
**NOT wired into a live recall measurement today**: 14across.co.il returned a hard
bot-check (sgcaptcha redirect) on every answer-page request all run, so no dev puzzle's
gold answers could be fetched — recall@N for the new mechanisms is unmeasured, not
zero, not estimated. 2026-05-29's clue text WAS fully transcribed and independently,
mechanically validated against the committed grid (`grid_tools.py validate` -> OK,
28/28 clues, enum sums match slot lengths exactly) — the transcription is ready; only
the gold-answer join is blocked. Re-run `python3 solver/candidates.py recall
data/dataset/clues.jsonl eval` once 14across is reachable and `data/answers/by_date/
2026-05-29.json` exists (transcription is in the session but data/ is gitignored by
design, so a future run must either redo it or reuse this PR's description of the
clue text to save re-transcribing).

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
   windows) but measures only 3.6% recall alone — NOT sufficient by itself. Remaining
   work, roughly in order: (a) wire it into an actual solve pass so an LLM proof-gates
   the generated list instead of one guess — not done yet, this was pure offline
   generator + recall measurement; (b) add substitution- and homograph-aware generation
   (`substitutions.py`, `homographs.py` as additional mechanisms) — the setter leans on
   these, not literal anagram/hidden/reversal, per the 3.6% result and PLAYBOOK.md.
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

- 2026-08-08: **substitution- and homograph-aware candidate generation**, lever 1(b)
  from the queue (explicitly the next item flagged 2026-08-06). Bootstrap ran but
  degraded: `./bootstrap.sh --dev-only` fetched the hspell lexicon (129,574 words) and
  the 4 dev puzzle images fine, but the 14across answers scrape got hit far harder than
  2026-08-06's transient bot-check — **51 of 52 puzzle pages returned a hard sgcaptcha
  redirect even after 12 retries with backoff** (only 2026-01-16, a train-split puzzle,
  came through). A targeted extra retry pass on just the 4 dev-puzzle URLs (12 more
  attempts each, longer backoff) still got zero — direct inspection showed every
  request being redirected to `/.well-known/sgcaptcha/`, i.e. a real challenge page, not
  a rate-limit that backoff can outlast. This is an external site-availability issue,
  not a bug in this repo's retry code (which already worked on 2026-08-06). Per its own
  warning, bootstrap's substitutions.json rebuild (step 4/6) was even more degraded than
  the 2026-08-06 finding (14 pairs from 1 puzzle vs 528 from 52) — reverted with
  `git checkout`, not committed, same as before.

  Despite the blocked scrape, transcribed 2026-05-29's clues in full anyway (28/28,
  from `data/images/2026-05-28.jpg`) and validated them the one way still available
  without the answer key: **`solver/grid_tools.py validate` against the committed grid
  — OK, every enum sum matches its slot's actual length, numbering matches** (this
  catches transcription errors — number/text/enum boundary mistakes, reversed enums —
  independent of knowing the gold answers; it does not catch a wrong clue-text
  transcription that happens to sum to the right length, which is why this is not a
  substitute for the answer-key check, only a partial one). Mid-transcription, caught
  and fixed my own error: initially misread the column reading order for the two
  side-by-side clue-text columns (assumed each column's rightmost-to-leftmost line was
  independent instead of reading the WHOLE right-hand column top-to-bottom before
  starting the left column, per correct RTL multi-column flow) — this had scrambled
  several clue-number/enum boundaries (e.g. an anagram fodder I could independently
  cross-check against PLAYBOOK.md's own worked example, 'פחות יין' -> יחפניות,
  confirmed which clue number it actually belonged to and exposed the ordering bug).
  Re-transcribed with the corrected column order; all 28 clues then validated clean.
  Could not complete the join to gold answers (`build_dataset.py` skips a puzzle
  outright when `data/answers/by_date/<date>.json` is absent), so **no recall number
  for the new mechanisms was produced or estimated this run** — the code lever is
  built and unit-tested but its real-world effect on recall@N remains queued for the
  next run that can reach 14across.

  Built `substitution_candidates()` and `homograph_candidates()` in `candidates.py`,
  wired into `generate()`. Selftest extended to 8 checks (6 prior + 2 new), all pass:
  a real committed substitution pair (טומי->לפיד) recovers לפיד as a hidden word after
  the swap; a real ambiguous token (שרה) is proposed as itself; a real name-component
  (אבא -> אבא חושי) is expanded to its full culture-sourced entity.

  AUDIT (the part of this lever that took the most care): both new mechanisms read
  data built from the FULL answers corpus (substitutions.json from crowd explanations,
  ambiguities.json partly from corpus answers), unlike lexicon.py's word list, which
  already excludes held-out dev/eval answers via `held_out_answers()`. Two distinct
  leak risks, handled differently:
  1. `homograph_candidates` could leak a held-out gold answer through
     `ambiguities.json`'s 'answer' sense (set whenever a token was EVER a crossword
     answer anywhere in the 52-puzzle corpus, dev/eval included, unfiltered). Fixed by
     construction: the function only ever consults tokens that literally appear in the
     CLUE TEXT being solved (never a corpus-wide scan by length), and explicitly
     excludes the 'answer' sense from the set of senses that justify emitting a
     candidate (`_SAFE_SENSES` in candidates.py) — only dictionary membership, curated
     role nouns, and Wikipedia-sourced culture entities can trigger a candidate. This
     is a structural fix, not a runtime filter, so it cannot regress silently.
  2. `substitution_candidates` draws on `substitutions.json`, mined from crowd
     EXPLANATIONS (not just answers) of all 52 puzzles including dev/eval, with no
     held-out filtering at all — this is a genuine, pre-existing gap (also shared by
     `prove.py`'s `means()`, unaudited until now) since a pair mined from a dev clue's
     own explanation and then used to generate a candidate for that same clue would be
     reading the answer key. Wrote `scratch_audit_leak.py`, a leave-one-out check:
     rebuild the pair index excluding a target puzzle's own explanations and compare
     candidate output with/without. **Could not run it this session** — it needs the
     same blocked answer corpus as the recall measurement. It is committed, ready to
     run the moment 14across is reachable, and should be run BEFORE trusting any
     substitution-mechanism hit in a future recall number. Flagging this explicitly
     rather than either skipping the concern or asserting it's clean without evidence.
  No forbidden reads or solution-site access this run (bootstrap's own fetches are the
  documented public sources; the sgcaptcha page was inspected only to confirm it was a
  challenge redirect, never followed or solved).

  HONEST READ: the code lever is complete, sound-by-construction against one leak mode,
  and honestly flagged as unaudited against a second, real one — but it shipped with
  ZERO measured effect on recall, purely because of an external outage. That is a
  materially weaker result than 2026-08-06's (which at least got a real, if low, number)
  and should be treated as unproven until the next run measures it for real.

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
