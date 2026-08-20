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
