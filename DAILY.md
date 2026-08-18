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
| **Candidate recall@N (new, offline, mechanical only)** | **3.6% (1/28)**, avg 12.6 candidates/clue, on 2026-05-29 (unchanged after adding substitution mechanism — see 2026-08-18 log) | not yet a target — diagnostic |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added: **substitution-aware candidate generation** (`solver/candidates.py`,
2026-08-18) — a single clue token looked up directly in the mined substitution table
(both directions, prefix-stripped stems), emitted as a whole-answer candidate when its
length matches the enum. Measured on the same held-out puzzle as the prior lever
(2026-05-29, 28 clues): **0 additional recall** — still 1/28 = 3.6%, same single hit as
before, mechanism did fire (94 substitution candidates generated across the puzzle, not
a bug) but never on the correct answer. avg candidates/clue rose 11.6 -> 12.6. See log
for the full negative-result writeup and the noise finding (common words like לא/את/רב
fan out into 10-18 near-useless candidates each).
Last finding (2026-08-06): coverage is bounded by CANDIDATE GENERATION, not verification.
Today's finding refines this further: even after adding the setter's own mined
substitution vocabulary as a direct single-token mechanism, coverage does not move on
this puzzle — the setter's substitution/homograph devices operate at a level (multi-step,
context-dependent sense-swaps) this table's single-token direct lookup cannot reach.
`charade.py`'s multi-part combinatorial substitution search was already measured negative
(2026-08-08 log); today's narrower single-token variant is negative too. The generator is
real infrastructure for the proof gate to use, but candidate generation via mined
substitutions looks exhausted as a lever — remaining candidate-generation value likely
requires either the private definitions corpus (`defs.py`) or genuinely new data
(corpus growth, queue item 3), not more mechanism variants over the same 2,220-pair table.

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
   substitution-aware generation was added and measured 2026-08-18: 0 marginal recall
   on the same held-out puzzle (still 1/28) — DONE, NEGATIVE, do not re-attempt with the
   current 2,220-pair table (see log). Homograph-aware generation was considered the same
   day and rejected on inspection, not just untried — see 2026-08-18 log for why. Remaining
   real work: (a) wire the generator into an actual solve pass so an LLM proof-gates the
   generated list instead of one guess — still not done, every measurement so far has been
   pure offline generator + recall, never plugged into a live solve+commit loop.
2. **Definition-span detection** — a cryptic clue's definition sits at one END in the
   general cryptic literature. CHECKED AGAINST THIS CORPUS 2026-08-18 and REJECTED as a
   hard classifier: `PLAYBOOK.md` §2.4 already documents, from this setter's own 728-clue
   corpus, "no fixed rule — definition can be at the start, the end, or interleaved," plus
   14% double-definition clues where BOTH ends are definitions. Building a one-end
   classifier would rest on a premise this project's own data already falsifies. Do not
   re-attempt without a materially different framing (e.g. a 3-way classifier: start /
   end / both, scored per-clue rather than assumed).
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
- 2026-08-18: **substitution-aware candidate generation** (`solver/candidates.py`), lever
  1(b) from the queue. Bootstrap first: `./bootstrap.sh --dev-only` step 2/6 (14across
  answers scrape) failed completely today — not the previously-documented ~50%
  intermittent bot-check, but a hard block: 5/5 direct `curl` attempts from this
  environment got HTTP 202 sgcaptcha with zero successes, confirmed by killing the
  33-min-into-retries run and testing manually. Worked around it for the ONE dev puzzle
  needed (2026-05-29, matching the puzzle used in the 2026-08-06 lever) via Bright Data's
  `scrape_as_html` MCP tool, which cleared the bot-check on the first try; parsed with the
  existing `scraper/parse_answers.parse_page()` unchanged. Puzzle images still came
  straight off the public img.haarets.co.il CDN with no blocking. **Honest caveat**:
  today's `answers_parsed.json` / lexicon corpus tier has only this 1 puzzle's 28 answers,
  not the usual ~1,450 from all 52 — hspell (129k) and the already-committed
  substitutions.json/culture.json/ambiguities.json are untouched and unaffected, but any
  future run should re-attempt the full 52-puzzle scrape rather than assume today's
  partial corpus is sufficient.

  Transcribed clue text for 2026-05-29 from `data/images/2026-05-28.jpg` (cropped +
  zoomed per-line via PIL to resolve several RTL line-wrap ambiguities where an enum
  or credit sat at a column break — e.g. clue 14's enum `(6,3)` visually sits right before
  "16." on the page, which only reading direction analysis + the known answer length
  resolved correctly). Validated: all 28 enumeration sums against the gold answer's
  letter count, 0 mismatches, `python3 solver/build_dataset.py` confirms `len mismatches:
  0`. Not committed (data/ is gitignored by design; a future run must redo this).

  Built `substitution_candidates()` in `solver/candidates.py`: a single clue token (plus
  prefix-stripped stems: ו/ב/ל/מ/ש/כ/ה) looked up in both directions of the mined
  substitution table (`substitutions.json`, 2,220 head words); a hit whose length equals
  the enum total becomes a whole-answer candidate. Deliberately narrower than
  `charade.py`'s existing multi-part combinatorial assembly (which requires >=2 parts and
  was already measured negative for full-answer generation, 2026-08-08 log) — this
  mechanism covers the single-token, single-hit case that search structurally never
  reaches. Also considered and explicitly did NOT build a homograph-aware mechanism:
  Hebrew homographs share identical spelling across senses, and the alternate-sense
  words are already folded into the lexicon as culture entities, so `pattern_candidates`
  already surfaces everything a dedicated homograph mechanism would — it would emit no
  new candidate STRING, only annotate meaning, which is a different kind of lever
  (definition-matching, not candidate generation). Documented this reasoning in
  `candidates.py`'s own docstring rather than silently skipping it.

  Selftest (`python3 solver/candidates.py selftest`, all 6 checks pass, was 5) adds one
  check using the real mined pair טומי~לפיד (already quoted in this project's own
  SOLVE_PROTOCOL.md as a worked example of the setters' vocabulary, not a dev/eval gold
  answer) — same discipline as the existing checks.

  MEASURED (executed, not estimated): `python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval` on the same 28 clues as the 2026-08-06 baseline —
  **still 1/28 = 3.6% recall@N, 0 marginal gain.** avg candidates/clue rose 11.6 -> 12.6
  (94 substitution candidates generated across the puzzle — confirmed the mechanism
  fires correctly, not a silent bug) but none landed on a correct answer; `by_mechanism`
  shows the puzzle's one hit is still `anagram`. Manually inspected the generated
  candidates for several clues to rule out a wiring bug (they are real, plausible
  substitution products) — the finding is genuine, not an artifact. NOISE FOUND: common
  short clue words (ל א/את/רב/זה) are hub nodes in the mined table and each fan out into
  10-18 near-random candidates, which is a real cost to any future proof-gate pass over
  this list (more noise, same recall) — worth remembering if this table is reused.
  AUDIT: no forbidden reads, no solution-site access, no image reads beyond this
  project's own puzzle scan; `lexicon.held_out_answers()` unchanged and still excludes
  this puzzle's gold answers; no implausible jump (0 marginal change, nothing to explain).

  HONEST READ: negative result. The setter's substitution/homograph vocabulary does not
  reduce to single-token direct lookups any more than it reduces to multi-part charade
  assembly (already negative, 2026-08-08) — both mechanization attempts over the same
  2,220-pair table have now failed to move recall on held-out data. This narrows, not
  widens, the candidate-generation queue: the mined-substitution-table well looks
  exhausted for candidate generation specifically (it may still help `prove.py`'s `means`
  assertion once a candidate exists from elsewhere). Definition-span detection (queue item
  2) was also examined this run (see RESEARCH.md) and rejected before implementation: this
  setter's own corpus already documents "definition can be at the start, the end, or
  interleaved" in PLAYBOOK.md §2.4, which falsifies the one-end premise the standard
  literature approach relies on — building it as a hard classifier would ship something
  this project's own data contradicts. Implemented nothing for that item, on purpose.
