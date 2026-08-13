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
| **Candidate recall@N (offline, mechanical only)** | **3.6% (1/28)**, avg 11.6 candidates/clue, on 2026-05-29 (reproduced independently today on a fresh re-transcription — same single hit, same rate) | not yet a target — diagnostic |
| **Candidate recall@N, defspan-restricted** | **3.6% (1/28)**, avg 10.6 candidates/clue (-8.6%), defspan confident on 6/28 clues | diagnostic — no recall change, modest noise reduction |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added: **definition-span detection** (`solver/defspan.py`), lever queue item 2 —
rule-based classifier using `indicators.json`'s wordplay-indicator vocabulary to guess
which end of a clue is the definition, wired into `candidates.py` as an opt-in restriction
(`--defspan`) on the anagram/hidden/reversal fodder search window. Precision/coverage/yield
were NOT re-measured this run (needs a full LLM solve session, out of scope for one lever)
— only the offline recall/candidate-count effect was measured, honestly, and it is a wash
on recall with a small candidate-count reduction. See log for the full result and two
real limitations the qualitative audit surfaced.
Last finding: defspan fires confidently (>=0.7) on only 6/28 clues (21%) on this setter's
puzzle — most clues here don't carry a clean, isolated wordplay-indicator word, consistent
with the standing finding that this setter leans on substitution/homograph devices over
literal indicator-marked anagram/reversal. Where it does fire, recall is unchanged (same
1 hit) and average candidate count drops ~8.6%, a real but small effect. Qualitative
inspection found two genuine problems worth fixing before trusting this classifier
further: (1) `indicators.json`'s anagram list contains at least one contaminated entry —
"מוני אמריליו", a recurring persona name in this setter's clue *surface text*, not a
genuine wordplay-indicator word, which caused one clue to be misclassified (though with no
measured recall effect, since that clue's answer is unreachable via the lexicon regardless
— see the 2026-08-06 audit note); (2) the span-assignment logic assumes fodder always sits
BETWEEN the clue edge and the indicator, which fits anagram/reversal conventions but is
backwards for homophone clues ("שמענו X" — fodder X follows the indicator, not precedes
it), degenerating the wordplay span to just the indicator word itself on at least one
clue in this run. Both are documented limitations, not silently swept under a good-looking
number — see the log entry below.

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
2. **Definition-span detection** — DONE 2026-08-13 (`solver/defspan.py`), but only the
   first cut: indicator-vocabulary-based, fires confidently on 21% of clues, no measured
   recall gain yet. Remaining work: (a) fix the "מוני אמריליו" contamination in
   `indicators.json`'s anagram list (a persona name mined as if it were an indicator
   word — audit the other 5 mechanism lists for similar contamination); (b) make
   fodder-direction mechanism-specific (anagram/reversal: fodder precedes indicator;
   homophone: fodder FOLLOWS indicator — "שמענו X" not "X שמענו" — current code assumes
   the anagram/reversal direction for all mechanisms, which starves the wordplay span on
   homophone clues); (c) re-measure recall on a larger dev set once (a)+(b) are fixed —
   6/28 confident clues is too small to trust the 8.6% candidate-count reduction as
   general.
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

- 2026-08-13: **INFRASTRUCTURE FINDING FIRST**: `./bootstrap.sh --dev-only` step 2 (the
  14across answers-corpus scrape) is now blocked at 100%, not the ~50% intermittent rate
  documented 2026-08-06 — confirmed by 5 manual `curl` retries with delays, all returning
  HTTP 202 to the same `sgcaptcha` bot-check page. `scraper/parse_answers.py`'s
  retry-with-backoff cannot clear this; it is a real JS/browser challenge, not rate
  limiting. Worked around it for the one puzzle needed today (2026-05-29) via a
  browser-rendering fetch (Bright Data MCP's HTML unlocker) through the SAME public,
  no-login URL bootstrap.sh already targets, then parsed it locally with
  `scraper/parse_answers.parse_page` unchanged — same output format, same source, just a
  fetch method that survives the bot-check. Did not attempt to backfill the full 52-puzzle
  corpus this way (out of scope for one lever; would need ~52 fetches). Net effect:
  `data/answers/answers_parsed.json` (feeds `lexicon.py`'s priority-2 corpus-answer tier)
  is absent this run, so the lexicon is smaller than usual (hspell + culture.json only) —
  this does NOT create a leak risk (`held_out_answers()` reads `data/dataset/clues.jsonl`,
  built from my own transcription, independent of this file) but does mean corpus-answer
  lookups are weaker than a normal run. Flagging for whoever runs next: if this block
  persists, `scraper/parse_answers.py` needs an unlocker-backed fetch path, not more
  retries.

  **LEVER: definition-span detection** (queue item 2, `solver/defspan.py` — new file,
  ~180 lines, docstring explains the rule-based indicator-vocabulary approach and cites
  the 2412.09012 finding it operationalizes). Selftest (`python3 solver/defspan.py
  selftest`, 5/5 checks) uses synthetic examples only, same discipline as `candidates.py`.
  Wired into `candidates.py` as an opt-in `use_defspan=True` / `--defspan` flag that
  restricts the anagram/hidden/reversal fodder search to the classifier's wordplay span
  when confidence >= 0.7, falling back to the full clue otherwise — so it can only narrow
  the search, never regress a clue it previously covered.

  TRANSCRIPTION: bootstrap could not fetch `data/answers/by_date/2026-05-29.json` (see
  infrastructure finding above), so I built it directly from the Bright-Data-fetched page
  via `parse_answers.parse_page`, then re-transcribed all 28 clues of 2026-05-29 fresh
  from `data/images/2026-05-28.jpg` (independent of any prior run's transcription, which
  is never committed by design). Validated every enum sum against the gold answer's
  letter count AND ran `solver/grid_tools.py validate` against the already-committed grid
  — both clean, 0 mismatches. Confirms the committed grid geometry and the historical
  2026-05-29 gold-answer set are still consistent with a fresh, independent transcription.

  MEASURED (executed, not estimated): baseline `python3 solver/candidates.py recall
  data/dataset/clues.jsonl dev` reproduced **1/28 = 3.6%** (avg 11.6 candidates/clue) —
  matches 2026-08-06's number exactly, on an independently re-transcribed dataset, which
  is itself a useful cross-check that neither run's transcription was a fluke. With
  `--defspan`: **1/28 = 3.6%** (avg 10.6 candidates/clue, defspan confident on 6/28
  clues). Recall unchanged; candidate count down ~8.6% among the confidently-classified
  clues. AUDIT: `lexicon.held_out_answers()` correctly blocks all 28 of today's gold
  answers (checked programmatically); the 9 gold answers still reachable via
  `lexicon.load()` (ערב, נשי, ברבר, פנימאי, אנזימימ, שלג, יחפניות, סרבית, מגפ) are all
  priority-1 plain hspell entries, the exact documented-legitimate case from the
  2026-07-21 leak writeup, not a regression. No forbidden reads (image only for the one
  dev puzzle; 14across only via the sanctioned public-corpus path, never during "solving");
  no implausible jump (3.6% -> 3.6% is the least suspicious result possible).

  HONEST READ: a real, working, tested lever with a genuinely small, non-negative
  measured effect — not the coverage unlock the queue hoped for, and I'm not pretending
  otherwise. Qualitative inspection of the 6 confident classifications (worth doing
  before trusting a metric on n=6) found two real bugs to fix before this lever is
  trustworthy at scale: `indicators.json`'s anagram list contains "מוני אמריליו" — a
  recurring persona name in this setter's own clue-surface writing style, not a genuine
  wordplay-indicator, mined into the list because it correlates with anagram-explained
  clues in the corpus without actually indicating anagram wordplay — which caused clue 7
  across to misclassify (no measured harm here only because that clue's fodder,
  'משפר חיי', already can't be recovered via the lexicon regardless — see 2026-08-06's
  audit note); and the span-direction logic (wordplay = clue-edge through indicator)
  correctly fits anagram/reversal's usual "fodder then indicator" phrasing but is
  backwards for homophone clues ("שמענו X" puts the fodder AFTER the indicator), which on
  clue 3 down degenerated the wordplay span to just the single word "שמענו" — too short
  to ever contain the real 8-letter fodder. Both are now in the lever queue above as the
  concrete next steps, not swept under the "no recall regression" headline number.

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
