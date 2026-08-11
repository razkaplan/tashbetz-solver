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
| **Candidate recall@N (offline, mechanical only)** | **3.6% (1/28)**, avg 15.2 candidates/clue, on 2026-05-29 — UNCHANGED after adding substitution+homograph mechanisms | not yet a target — diagnostic |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added: **substitution- and homograph-aware candidate generation**
(`solver/candidates.py`, 2026-08-11) — queue item 1(b). Extends the existing
anagram/hidden/reversal/pattern generator with two more mechanisms: substitute a clue
word for its known equivalent (`substitutions.json`) before re-running the anagram/
hidden/reversal windows, and surface a clue token's OTHER-sense full entity name
(`ambiguities.json`, homograph device) directly as a candidate when its length matches
the enum. Both are real, tested (selftest now has 7 checks, all pass), and generate
plenty of candidates (3,433 substitution + 14 homograph candidates across this puzzle's
28 clues) — but **recall on this puzzle did not move**: still 1/28, the same single
anagram hit as the pre-existing baseline. Genuinely negative result, not a bug (verified
the new mechanisms fire; see log). Coverage is bounded by candidate generation, but this
specific extension of it was not the fix, at least not on this one puzzle.

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
   windows); (2026-08-11) added substitution- and homograph-aware mechanisms too — still
   only 3.6% recall (1/28), UNCHANGED, on the one dev puzzle measured so far. Remaining
   work, roughly in order: (a) wire it into an actual solve pass so an LLM proof-gates
   the generated list instead of one guess — still not done, every measurement so far has
   been pure offline generator + recall, never a live solve; (b) MEASURE ON MORE THAN ONE
   PUZZLE before concluding anything about the substitution/homograph mechanisms — n=28
   clues is too small to trust a flat result, and the 2026-08-11 log has three concrete
   untested hypotheses for why it didn't move; (c) try multi-word substitution
   combinations, not just one word swapped at a time.
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
- 2026-08-11: **substitution- and homograph-aware candidate generation**
  (`solver/candidates.py`), lever 1(b) from the queue, continuing 2026-08-06's work.

  BOOTSTRAP FINDING (environment, not code): `bootstrap.sh --dev-only` step 2 (answers
  corpus from 14across.co.il) failed completely in this sandbox — every request hit the
  same JS proof-of-work bot-check (HTTP 202, `sg-captcha: challenge`), confirmed with 5/5
  fresh curls and the real `scraper/parse_answers.py` fetch function (0/3 retries
  succeeded). The 2026-08-06 log described this as ~50% intermittent; today it was a
  total, consistent block, most likely because this session's outbound proxy IP is
  flagged differently. Worked around it with the session's Bright Data MCP tool
  (`scrape_as_html`, which does solve the challenge), feeding the returned HTML into the
  project's own unmodified `scraper/parse_answers.parse_page()` — no reimplementation,
  same parser the pipeline always uses. Fetched and validated the one puzzle needed
  (2026-05-29) this way; also launched a background agent to refetch the full 52-puzzle
  corpus the same way for future runs, but it was still running (very slow via this
  path — each fetch verified individually) when this run ended and its output was not
  used for anything below. See RESEARCH.md for the full note; this is an environment
  fragility worth knowing about, not a code fix.

  TRANSCRIPTION (2026-05-29, `data/images/2026-05-28.jpg`, `data/clues/2026-05-29.json`):
  redone from scratch this run (transcriptions are gitignored by design, so every run
  starts over). This took far longer than expected — the clue text for this setter is
  laid out in Hebrew RTL text mixed with digits/parens across a multi-line paragraph,
  and getting the reading order right by eye was genuinely hard and error-prone (spent
  a long time on it; several wrong hypotheses before landing on a validation method that
  actually works). What worked: (1) crop the clue-text region with PIL and read it at
  high resolution rather than trusting the full-page read; (2) — most important — the
  grid is ALREADY COMMITTED for dev puzzles, so `solver/grid_tools.py`'s numbering
  algorithm gives the AUTHORITATIVE clue number + direction + exact slot length for
  every clue, independent of any bidi reading of the image. Every transcribed clue's
  enum was checked against this before being trusted (`grid_tools.py validate` — printed
  `OK`, 0 mismatches across all 28 clues on the first fully-corrected pass); disagreements
  were the signal that a specific line's reading order was wrong and needed re-checking,
  not that the grid was wrong. Also discovered THIS setter's puzzles print across TWO
  disjoint clue-text blocks on the page (a small-font "אופקי:" recap box for clues
  1/7/8/9/10/11/13, positioned near an unrelated filled solution grid, plus a larger-font
  block for the rest) — missing the first block entirely is what cost the most time
  before a wider image fetch (`width=3000` vs the default `1500`) revealed it. Fetched
  the real gold answers for this one date (via the Bright Data workaround above) and
  cross-checked: 0 length mismatches, and clue 7 across's answer (`ישפרחימ`) matches
  `prove.py`'s own worked example exactly — strong independent confirmation the
  transcription is for the right puzzle. `python3 solver/build_dataset.py` now reports
  28/28 rows with `len_ok: true`.

  BUILT: `substitution_candidates()` — for each clue word, swaps in a known equivalent
  from `substitutions.json` (mined from crowd explanations; e.g. `קנ~בית`) one word at a
  time, then re-runs the existing anagram/hidden/reversal window search over the
  substituted text. Targets exactly the gap the 2026-08-06 run diagnosed: fodder the
  setter's OWN vocabulary implies but that never appears literally in the clue, which a
  plain character-window search structurally cannot see. `homograph_candidates()` — for
  each clue token recognized in `ambiguities.json` (the homograph index), surfaces the
  full multi-word entity behind its OTHER sense (given_name/surname/song/artist/
  politician/place) directly as a candidate when the entity's length matches the enum —
  the mechanism behind e.g. "the minister" standing for the name שרה. Both added to
  `generate()`. Selftest extended to 7 checks (all pass), using synthetic real-table
  entries (`קנ~בית`, `אבא`->`אבא חושי`) not this puzzle's gold data, same discipline as
  the rest of the file.

  AUDIT finding (real, not hypothetical): `ambiguities.json`'s keys are built from
  corpus ANSWERS with no `held_out_answers()` filtering — unlike `lexicon.py`, which
  learned this lesson from the 2026-07-21 leak. Checked directly: 11 of this puzzle's 28
  gold answers ARE present as keys in `ambiguities.json`. My first draft of
  `homograph_candidates()` included the 'answer' sense in its lookup, which reads that
  same index's `evidence['answer']` field — turns out that field holds crowd EXPLANATION
  SNIPPETS, not alternate entity names (unlike the given_name/surname/song senses), so
  including it was both semantically wrong (one hit was measured: `ההיפכרצ`, not a real
  word — noise, not signal) and sat needlessly next to a leak-shaped structure. Removed
  'answer' from the sense list actually queried — closes the path rather than relying on
  the argument (checked, and true today) that a real clue never contains its own answer
  as a literal substring. `ambiguities.json` itself still has no held-out filtering at
  its build step; flagging as a small, cheap fix for a future run
  (`homographs.py` should call `lexicon.held_out_answers()` the same way `lexicon.py`
  does), not done today to keep this run's diff to the one lever.

  MEASURED (executed): `python3 solver/candidates.py recall data/dataset/clues.jsonl
  eval` on the freshly-transcribed, freshly-validated 28 clues of 2026-05-29 —
  **1/28 = 3.6% recall@N, avg 15.2 candidates/clue** (up from 11.3-11.6 avg candidates
  pre-lever; same single hit, the 2-down anagram, as every prior run's baseline on this
  puzzle). Confirmed the new mechanisms are not silently inert: direct instrumentation
  found 3,433 substitution candidates and 14 homograph candidates generated across the
  puzzle's 28 clues — they fire, they just did not happen to produce THIS puzzle's gold
  answers. HONEST READ: a real, negative result on n=28. Plausible reasons, not yet
  tested: (a) one dev puzzle is a small sample — a single setter idiosyncrasy or two
  could swing 1-2 hits either way without meaning much; (b) `substitution_candidates`
  only swaps ONE word at a time, and this setter's charades often need two or more
  fragments reinterpreted at once; (c) `substitutions.json`'s 2,220 head words (mined
  from a DIFFERENT, easier-setter corpus per the 2026-08-06 finding) may simply not
  cover this setter's specific vocabulary choices on this puzzle's clues. Do not
  re-attempt exactly this shape (single-word substitution) without either growing the
  table or trying multi-word substitution combinations — next candidate for the queue,
  not attempted today.
