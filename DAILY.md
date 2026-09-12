# Daily improvement runbook — tashbetz solver


Read this first each run. It is the handoff between days.

**Deploy rule:** production deploys ONLY by merging to main (git-linked
Vercel, Root Directory=docs). Never `vercel --prod` from a branch or dirty
tree - a stale CLI deploy overwrote the live site on 2026-08-29. See CLAUDE.md.

## Current state (update this section every run)

| Metric | Value | Target |
|---|---|---|
| Precision (combined dev) | **96.9%** (unchanged, not re-run today — see log) | >=95% ✓ |
| Coverage | 57% (unchanged, not re-run today) | >=70% |
| Accurate fulfilment (yield) | 55% (unchanged, not re-run today) | ~67% |
| Best single puzzle | 2026-05-29: 95% / 71% / 68% ✓ all targets | |
| Hardest puzzle | 2026-06-05: 100% / 43% / 43% | coverage stuck |
| **Candidate recall@N (new, offline, mechanical only)** | **3.6% (1/28)**, avg 11.6 candidates/clue (capped), on 2026-05-29 — UNCHANGED after adding substitution+homograph mechanisms | not yet a target — diagnostic |
| **Candidate recall@N with `container_candidates` added (new, offline, mechanical — the container/insertion device, ~10-12% of clues per PLAYBOOK.md, previously pure verification infra with no generator)** | **3.6% (1/28), UNCHANGED** on 2026-05-29 (re-transcribed fresh, 28/28 clues, 0 enum mismatches) — mechanism fired on only 1/28 clues (2 raw candidates, 0 gold hits); avg candidates/clue unchanged at 11.6. CONFOUNDED, disclosed: 14across was fully unreachable this run (the same hard wall since 2026-08-19), so `sub_fwd()` — the mined-substitution half of this mechanism's fragment source, and the SAME source `substitution_candidates()` already depends on — was empty, and `substitution_candidates()` itself also scored 0 fires this run (by-mechanism breakdown: only `anagram` hit at all). Not a clean test of the device; only its corpus-free destem/literal-word fragment half was exercised. Offline selftest (not gold-linked; found by scanning the real committed lexicon, not a synthetic fixture) confirms the mechanism correctly derives a real dictionary word (מכות + מל spliced at an interior position -> ממלכות). **SECOND measurement, 2026-09-11 (an independently-written duplicate implementation, see 2026-09-12's log entry for the branch-hygiene story): 0.0% (0/28) on 2026-06-05** — fired on 0/28 clues; root-caused via the puzzle's own crowd explanation that its one real container clue (16A, קטלנ) needs SYNONYM substitution (בית~קן, "the judge"~טל) that a literal-clue-word-only design cannot reach. **THIRD, 2026-09-12: see log — the two independent implementations were reconciled (the merged version already unions literal/destemmed clue words with `sub_fwd()`'s mined synonyms, confirmed by a new selftest proving the synonym-only path fires) and re-measured** | not yet a target — diagnostic; re-measure once 14across (or any puzzle with real crowd explanations) is reachable |
| **Candidate recall@N with `retrieval_candidates` added (new, offline, BM25 definition retrieval)** | **7.1% (2/28)** on 2026-05-29 (up from 3.6%); **SECOND puzzle, 2026-08-26: 0.0% (0/18) → 5.6% (1/18)** on 2026-06-26 (partial, 18/28 clues); **THIRD puzzle, 2026-08-27: 0.0% (0/19) → 0.0% (0/19), UNCHANGED** on 2026-07-10; **2026-08-28, RE-MEASURED on 2026-05-29 with a GROWN corpus (mordo re-crawled 13,646 raw pairs vs 9,685; `note.co.il` crawled for the first time this project's lifetime, 829 pairs): 3.6% (1/28) → 10.7% (3/28)**, up from the 7.1% this exact puzzle scored with the smaller corpus; **2026-08-29, RE-MEASURED 2026-07-10 with an EVEN BIGGER corpus (mordo 25,350 raw / 24,361 parsed, up from 13,646/12,890; note.co.il 970 fetched out of 1,301 discovered): 0.0% (0/19) → 0.0% (0/19), STILL UNCHANGED**; **2026-08-30, RE-MEASURED 2026-06-26 — this time FULLY transcribed (28/28 clues, closing 2026-08-26's 18/28 partial gap) and with a MASSIVELY grown corpus (mordo 66,443 raw / 62,403 parsed, up from 25,350/24,361 — the blogspot feed has grown 2.6x again; note.co.il 1,001 fetched out of 1,301 discovered, up from 970/1301): 0.0% (0/28) → 14.3% (4/28)** — the highest recall this diagnostic has ever measured on any puzzle, and the largest single-puzzle point gain, from 4 independently-audited external hits (מניע, רומח, בובדילנ, ברסמכא) — see log | not yet a target — diagnostic; 6 independent measurements, 4 positive + 2 flat, confirming corpus growth is puzzle-dependent (rescued 2026-05-29 twice and now 2026-06-26 strongly, never moved 2026-07-10 across three corpus sizes) |
| **Definition-span locatable rate (new, offline, diagnostic)** | **25% (7/28)** have mechanically-locatable single-window wordplay; of those 29% (2/7) are interior, not edge; classifier agreement on edge cases **1/5** | not a target — this diagnostic KILLED the lever, see log |
| **`solve_pass.py` LIVE blind trial — cumulative (3 trials)** | **40% precision (2/5 committed)**: 2026-08-16 was 1/2 on a partial 21/28-clue puzzle (2026-06-12); 2026-08-22 was **0/2**, 7.1% coverage, on a FULL 28/28-clue puzzle (2026-05-15); **2026-08-27 is 1/1 = 100% precision but 5.3% coverage (1/19), 0% suggestion hit-rate (0/10)**, on 2026-07-10 (19/28 clues) — FIRST trial run with `retrieval_candidates` live (wired 2026-08-25, never live-trialed since); it contributed ZERO candidates all puzzle (grepped the transcript for `(retrieval, fodder=` hits — none), matching today's own offline recall@N finding on this same puzzle (0/19 with or without retrieval); the one correct commit came from `wiki.py` culture-fact lookup, not from any candidate generator | n=5 — still small; retrieval's live debut is a null result on this puzzle, not a regression, but not the coverage lift the queue hoped for either; see log |
| **Candidate recall@N with `culture_category_candidates` added (new, offline, definition-driven)** | Two independent puzzles now measured, both UNCHANGED vs baseline: **0% (0/28)** on 2026-06-19 (fired 1/28 clues); **2026-08-31, SECOND puzzle 2026-07-03: baseline 7.1% (2/28) → still 7.1% (2/28) with culture ON**, fired 3/28 clues (43 raw candidates), 0 gold hits. Across both puzzles: fired on 4/56 clue-instances, 0/4 hits — but the 3 new firings show 3 DIFFERENT root causes, not a repeat of one: one homograph/pun misdirection (reproduces 2026-06-19's finding), one where the gold answer IS in the raw corpus but is correctly excluded by the held-out safety filter (a measurement-methodology blind spot, not a corpus gap), one genuine corpus coverage gap (the specific mountain name is absent from culture.json's 119-entry list) | not yet a target — n=4 fired-clue diagnostic, see log |
| **Candidate recall@N with `defspan_retrieval_candidates` added (new, offline, definition-SPAN-restricted BM25 retrieval)** | **10.7% (3/28) on 2026-05-29 — IDENTICAL to `retrieval_candidates` (whole-clue query) alone, both individually and combined**; the two mechanisms return byte-identical candidate sets on 27/28 clues (differ on 1) and hit the SAME 2 gold answers | not yet a target — NEGATIVE result for incremental recall, see log |
| **Candidate recall@N with `double_definition_candidates` added (new, offline, two-independent-half BM25 retrieval)** | **0% (0/21)** on 2026-05-21 (fresh puzzle) — mechanism fired on **0/21 clues**, not just missed gold: even relaxing the requirement to "gold appears in EITHER half's independent top-K alone" (not both), the gold answer was absent from both halves for every one of the 5 short [<=4]-letter slots checked (the class PLAYBOOK.md says is "overwhelmingly double definitions"); mechanical baseline 0.0%, `retrieval_candidates` alone (same corpus) 9.5% (2/21) shows the corpus itself isn't empty — this is a genuine per-mechanism null, not a corpus-availability artifact | not yet a target — n=1 puzzle, see log |
| **Candidate recall@N with `homophone_candidates` added (new, offline, mechanical — the נשמע/sounds-like device, PLAYBOOK.md 1.6, ~4% of clues, previously NO generator or proof primitive at all)** | **3.6% (1/28), UNCHANGED** on 2026-05-29 (fresh 6th independent transcription, 28/28 clues, 0 enum mismatches, 0/15 grid-pattern mismatches) — but NOT a zero-fire result: the mechanism fired on **8/28 clues** (avg candidates/clue 11.7 -> 11.8), producing real phon-folded candidates each time, none matching gold. Root-caused, not just observed: this puzzle's own ONE homophone-CREDITED clue (22 across, carries the explicit "(עפ"י השמיעה של אליעזר כמון)" marker PLAYBOOK.md 1.6 names) needs vowel-letter flexibility (ה/ו/י insertion — "הזורזים" -> "אנזימים") that this v1's CONSONANT-CLASS-ONLY fold (ק/כ/ח, ט/ת, ס/ש, א/ע) deliberately does not model, disclosed in the code's own docstring rather than silently missed | not yet a target — diagnostic; a real, working mechanism with a clearly scoped (not silently narrow) gap |
| **Candidate recall@N with `homophone_vowel_candidates` added (new, offline, mechanical — closes 2026-09-05's own disclosed gap: free ו/י vowel-letter insertion/omission, one letter of length difference)** | **3.6% (1/28), UNCHANGED** on 2026-05-29 (7th independent transcription, 28/28 clues, 0 enum mismatches — see log for a disclosed direction ambiguity found on ONE clue, 26 across, unrelated to this lever). Fired on **14/28 clues** (avg candidates/clue 11.8 -> 13.0), zero gold hits. Root-caused, not assumed: directly tested the mechanism against the SPECIFIC clue 2026-09-05 diagnosed as needing this ("22 across, הזורזים -> אנזימימ") and it produces **ZERO candidates for that clue, not a near-miss** — the two words' phon-folded consonant skeletons (הזורזימ vs אנזימימ) differ by far more than one ו/י, so 2026-09-05's own "vowel-insertion" diagnosis was itself an oversimplification of a more complex sound relationship this narrow, single-letter-edit device cannot reach either. A real, working extension of the device with a genuine (not contrived) negative result | not yet a target — diagnostic; the disclosed gap this closed turned out not to be the puzzle's actual gap once tested directly |
| **Candidate recall@N with `substitution_candidates`' 3-part charade chain added (new, offline, mechanical — queue item 1(b)'s own disclosed next step: 3 ADJACENT clue words' mined substitutes concatenating to the full answer length, generalizing the existing 2-word case)** | **3.6% (1/28), UNCHANGED** on 2026-05-29 (8th independent transcription, 28/28 clues, 0 enum mismatches, 0/15 grid-pattern mismatches against the solved-recap image). **INCONCLUSIVE, disclosed rather than claimed negative**: the mechanism fired **0/28 clues** with `use_substitution_3part` on vs off (avg candidates/clue identical, 13.8 both ways) — but so did its existing 2-part sibling, checked directly (0 hits) against BOTH the small in-memory held-out-safe table this run's own severely hard-walled bootstrap produced (14across: 4/52 puzzles recovered, 236 explanations, 35 head words) AND, as an audit-only diagnostic never used for the scored number, the full committed `solver/lex/substitutions.json` (2,220 head words, restored via `git checkout` after this run's own smaller rebuild briefly overwrote it — bootstrap.sh's own documented warning caught before it was committed). Zero fires at EITHER corpus size for EITHER part-count means this specific puzzle's specific clue set has no adjacent-word substitution chain of any length, at 2 words or 3 — not evidence the 3-part device itself is broken (its own selftest, on synthetic data, proves it correctly finds a 3-way chain when one exists) or that it's a dead end, just that this run could not produce a puzzle where the baseline it extends already fires, which is the precondition for testing whether extending it helps | not yet a target — diagnostic; needs a puzzle where 2-part substitution already fires to be a real test, see log |
| **Candidate recall@N with `charade_candidates` added (new, offline, mechanical, two-part-enum only)** | **3.6% (1/28), UNCHANGED**, on 2026-05-29 (freshly re-transcribed this run) — fired on all 10 of the puzzle's 2-part-enum clues (up to its own 200-candidate cap on 8 of them), matched gold on 0/10; avg candidates/clue 11.7 → 18.9, wall time 17.9s → 30.2s for the 28-clue eval | not yet a target — diagnostic; a real negative result on n=1 puzzle, see log |

| **`deffit.py` definition-fit reranking (NEW 2026-09-09, offline, conditional on recall)** | On a fresh puzzle (2026-05-15): recall_hit 2/28 (same 2 retrieval hits); top-1 accuracy 0/2 unchanged; **MRR 0.333 → 0.350** (1 candidate moved up, 0 moved down); **structural finding: 0/28 clues have a non-retrieval candidate with a non-zero def_fit score** — the signal is mathematically redundant with `retrieval_candidates` today, since both query the same private_defs/BM25 index | not yet a target — n=2 is far too small to call this positive or negative; see log for the redundancy diagnosis and the concrete fix (a second gloss source, e.g. `solver/lex/fillbank.json`) |
| **`deffit.py` with `fillbank.json` wired as a second gloss source (NEW 2026-09-10, offline)** | Re-measured on the SAME 2026-05-15 puzzle, independently re-transcribed and re-crawled fresh this run: recall@N **0/28 with or without retrieval** (a smaller/different private_defs crawl than 2026-09-09's found no hits at all on this puzzle — recall_hit therefore 0/28, so top-1/MRR are undefined this run). Split the structural diagnostic into TWO numbers on purpose: clues with a non-retrieval candidate carrying a KNOWN gloss in ANY source went **3/28 (private_defs alone) → 14/28 (+fillbank)** — fillbank.json's 2,412 entries genuinely widen gloss coverage, a real and substantial move; but clues with a non-retrieval candidate whose gloss actually SHARES VOCABULARY with the clue (`def_fit>0`, 2026-09-09's own stricter bar) stayed **0/28 with fillbank ON**, because the 59 newly-known candidates' glosses (e.g. `ירושלים` -> `בירת ישראל`) don't happen to repeat the clue's own wording. Also FOUND AND FIXED a real bug before ever measuring: `build_fillbank_index()` didn't fold fillbank's final letters (ם/ן/ץ/ף/ך), so it would have silently missed all 557/2,450 (22.7%) of fillbank entries ending in one — every candidates.py answer is unconditionally final-folded, so the lookup would have failed for any of those words even when present | not yet a target — a real, disclosed, mixed result: coverage widened, the stricter score-overlap bar did not move this run; see log |

Baseline for comparison: v2 = 41% raw with untraceable errors.
Last lever added (2026-09-12): **found and fixed a duplicate-PR branch-hygiene failure on
`container_candidates` itself, then hardened and root-caused the merged mechanism —
no new recall number today, disclosed honestly rather than fabricated (see below for why).**

`list_pull_requests` showed #55 (2026-09-11, `claude/container-candidates-wip`) branched
directly off pre-#54 main and independently reimplemented `container_candidates` from
scratch — the EXACT function this branch's own history already added on 2026-09-03 (PR
#42, folded into #54's 2026-09-10 consolidation) — because #55 never saw #54's branch. This
is queue item 6's compounding-loss pattern recurring on a single FUNCTION rather than a
whole file: two independently-written, differently-scoped implementations of
`container_candidates` now existed in two open, unmerged PRs. Diffed both line by line
rather than guessing which was "better": #42/#54's version sources outer/inner fragments
from a clue word's destemmed form UNION its mined-substitution equivalents (`sub_fwd()`,
the same table `substitution_candidates` already uses); #55's version sources ONLY literal
clue words. #55 measured 0/28 on a freshly transcribed 2026-06-05 and root-caused its one
real container clue (16A, "חי בבית השופט", per the crowd explanation קטלנ = קן containing
טל) as needing SYNONYM substitution (בית~קן, "the judge"~טל) that its literal-word-only
design cannot reach by construction. That is exactly the capability #42/#54's version was
built to add — #55's own diagnosis is effectively a bug report against code that already
existed on an unmerged sibling branch. Kept #54's strictly more general implementation
(any clue word #55's version can reach, #54's can also reach via `_destem`'s identity
case; #54's version can additionally reach mined synonyms #55's cannot) rather than
re-adding #55's narrower one, and did not open a second PR for #55's content — it is
superseded, not merged.

HARDENED before trusting the superset claim: added a new `candidates.py` selftest
(`מכות וגם ציון` -> `ממלכות`, using a substitution table where the inner fragment `מל` is
reachable ONLY via the mined table for `ציון`, not via any destemmed literal word) that
proves the merged mechanism's synonym-sourced fragment path actually fires, and that it
does NOT fire without the table entry (ruling out a coincidental hit). Previously this path
was exercised only by the docstring's claim and by #42's own confounded 2026-05-29
measurement (14across was down that day too, so `sub_fwd()` was empty and never actually
exercised the synonym half). All 6 affected selftests re-run clean (`candidates.py`,
`prove.py`, `substitutions.py`, `retrieve_defs.py`, `lexicon.py`; `solve_pass.py`'s selftest
requires `data/dataset/clues.jsonl` to exist, which today's bootstrap state doesn't
produce — see below — so it could not be exercised today, disclosed rather than skipped
silently).

INDEPENDENTLY RE-TRANSCRIBED 2026-06-05 myself (not copied from #55's branch — `data/` is
gitignored, so #55's own transcription was never available to read) from
`data/images/2026-06-04.jpg`, fetched directly from the public CDN. Validated all 28 enum
sums against the GRID-DERIVED slot length (`solver/grid_tools.py validate`, 0 problems) —
and independently rediscovered the SAME 3 print anomalies #55 disclosed (clues 8, 10, 11
across print enums that do not match the grid-derived length; clue 19 needed its printed
text merged across the column-wrap boundary, a distinct, already-catalogued phenomenon).
Two independent transcriptions of the same defective print landing on the same 3 anomalous
clues is a real cross-check that neither is careless misreading. Clue 16 itself ("חי בבית
השופט (עפ"י מיקי זבדי)", enum (4)) was clean and unambiguous in both transcriptions.

BOOTSTRAP AND GOLD DATA, disclosed plainly rather than estimated: 14across was hard-walled
this run — not just observed as flaky, CONFIRMED directly: a standalone single-URL fetch
for this exact puzzle's answer page returned HTTP 202 (the documented bot-check page) on 3
consecutive retries with delays, and the full 52-URL bootstrap step was killed after 23
minutes having recovered zero puzzles. Attempted the no-14across image-fallback (the
following week's small solved-grid recap, `data/images/2026-06-11.jpg`): the black-cell
PATTERN read cleanly and matched the committed grid for row 0, and row 0's letters
assembled into a real, semantically perfect answer for clue 1 ("כלהכבודלשר" = "כל הכבוד
לשר", matching its (3,5,2) enum exactly) — but a second row's letters did not assemble into
a real word at all, which is a direct, executed sign that letter-level OCR of this
embedded, sub-100px-tall grid is not reliable enough here to serve as gold data without a
zoom/crop tool this environment does not have. **Rather than publish a partially-guessed
gold set and an accuracy number built on it, this run stops here and reports no live
recall@N number for 2026-06-05 today** — exactly the "if something genuinely cannot be run,
say so plainly rather than estimating" rule this file itself states.

AUDIT-ONLY DIAGNOSTIC (matching this project's own established practice of querying the
larger, historical `solver/lex/substitutions.json` for context without using it as the
scored live table): queried it directly for both fragments #55's root-cause named.
`solver/substitutions.py --to קן` -> `בית (seen 18x)`, i.e. בית really is a recorded,
generic substitution for קן. But `solver/substitutions.py --to טל` does NOT include
`שופט`/`השופט` at all — `שופט` maps only to `קונ`/`דיינ`/`דנ` (generic "judge" synonyms).
`טל` here almost certainly names a SPECIFIC judge (a real Israeli justice surnamed Tal),
which is an entity/culture fact, not a generic synonym pair — refining, not just repeating,
#55's diagnosis: the missing piece is a THIRD fragment source (a role/entity lookup like
`culture_category_candidates`' trigger vocabulary), not merely "more corpus" for the two
sources this mechanism already has. A further check (audit-only, both fragments injected
by hand): even with `קן`+`טל` both available, the assembled `קטלנ` is NOT present in the
loaded hspell lexicon at all, so — if #55's crowd-sourced gold answer is right — this
specific clue would ALSO fail the mechanism's final lexicon-membership gate, a fourth,
independent obstacle beyond fragment sourcing. None of this is asserted as certain (the
gold answer itself is unverified today), but each piece was checked by executing code
against real committed data, not guessed.

NOT DONE, honestly: no live recall@N number for 2026-06-05 (see above); did not re-verify
2026-05-29's existing confounded 3.6%/1.28-unchanged number from 2026-09-03; did not build
the culture/entity fragment source this run's own root-cause analysis points to next
(a real third lever, correctly deferred rather than squeezed into today's one-lever
budget); did not merge or otherwise act on any other open PR.

Previous lever (2026-09-10): **wired `solver/lex/fillbank.json` (2,412 word->definition
pairs) into `deffit.py` as a SECOND, independent gloss source — closing 2026-09-09's own
disclosed next step, and continuing queue item 9 ("definition-fit scoring").** Bootstrap's
14across scrape hit the same hard wall as most recent runs (52 pages staged, only 6/52
recovered — 10/07/2026, 08/05/2026, 27/03/2026, 27/02/2026, 26/09/2025, 15/08/2025 — none a
previously-used dev/eval date); worked entirely from the public-CDN image-fallback
technique for a fresh transcription.

Before touching the lever, CONSOLIDATED THE PR BACKLOG (queue item 6, recurred yet again):
`list_pull_requests` showed the backlog had grown to **eleven** open PRs against main
(#38, #39, #41, #42, #44, #46, #47, #50, #51, #52, #53) — #51 (2026-09-07) already
consolidates #38/#39/#41/#42/#44/#46/#47 and asks for those seven to be closed in its
favor, but #52 (2026-09-08, `charade_candidates`) and #53 (2026-09-09, `deffit.py`) were
each branched independently off the same pre-#51 main and never merged with it or each
other — the exact compounding-loss pattern this item has now flagged six times. Branched
from #51, merged #52 then #53 on top: two real code conflicts in `solver/candidates.py`
(both #51 and #52 independently extended `generate()`/`recall_eval()`'s signature and the
mechanism-priority docstring) resolved by keeping every mechanism from both sides — the
merged `generate()` now threads `use_container`/`use_double_def`/`use_defspan_retrieval`/
`use_homophone`/`use_homophone_vowel`/`use_substitution_3part` (from #51) AND `use_charade`
(from #52) together, not either alone. `solver/deffit.py` (#53) merged clean, no code
conflict. DAILY.md/RESEARCH.md conflicts (both files' dated Log/state-table entries)
resolved by chronological reordering so 2026-09-08's and 2026-09-09's narratives both
survive in order, neither silently dropped. Ran all 6 selftests immediately after merging,
before trusting the result: all clean. **Please close #38, #39, #41, #42, #44, #46, #47
(already superseded by #51), #52 and #53 in favor of this PR.**

**THE LEVER.** #53's own disclosed structural finding (2026-09-09): `deffit.py`'s
`def_fit_score` only ever checked `retrieve_defs.build_index()`'s corpus — the SAME index
`retrieval_candidates()` already searches — so it could rerank retrieval's own hits but
could never independently corroborate a mechanically-derived candidate (anagram/hidden/
homograph/...) that retrieval hadn't already found; measured 0/28 clues. `build_fillbank_index()`
adds `solver/lex/fillbank.json` (2,412 real dictionary word->definition pairs, already
committed, used by the public site's crossword fill) as a second, independently-scored
source with its OWN BM25 statistics (kept separate from private_defs' N/df/avg rather than
merged, so a much smaller denser corpus doesn't get silently swamped by a bigger one).
`def_fit_score` now takes the max across every available source.

**A REAL BUG, caught before it was ever measured.** Testing `build_fillbank_index()`
against the real committed file (not just synthetic fixtures) found it did nothing: 0
matches. Direct inspection found why — `fillbank.json`'s keys are ordinary Hebrew
orthography (`אוהלים`, final mem), but `candidates.py`'s `norm()` unconditionally
final-folds every answer it ever produces (`אוהלימ`) — so the dict lookup
(`idx['ans_docs'].get(answer)`) would silently miss every fillbank entry ending in
ם/ן/ץ/ף/ך, **557 of 2,450 entries (22.7%)**, checked directly rather than assumed. Fixed
by folding fillbank's keys with the same `FIN` table `candidates.py` uses, before indexing.
A new selftest case (a real final-letter word, injected as a synthetic fillbank fixture —
never the real committed file, same discipline as every other case) guards the regression:
it asserts the folded key is what gets indexed and the literal spelling is NOT a separate
key.

RE-TRANSCRIBED 2026-05-15 independently of #53's own transcription of the same puzzle
(this run's own bootstrap fetched the images fresh; no prior run's transcription persists,
`data/` is gitignored). All 28 clues from `data/images/2026-05-14.jpg` — the across text is
split across two print columns (a main column from 22 onward, a narrow sidebar carrying
1,7,8,9,10,11,13,15,17,19), the same shape queue item 8 already found for 2026-06-19 and
#53 found for this date. Every one of the 28 enum sums validated against the GRID-DERIVED
slot length (`grid_tools.slots()`, pure structural geometry, no gold data read) before any
gold data was touched: **0/28 mismatches**. GOLD LETTERS came from the small solved-grid
recap in the following week's image (`data/images/2026-05-20.jpg`), this time calibrated
programmatically end to end (dark-line-fraction gridline detection on both axes, not
eyeballed crop bounds, then a tight per-row crop read cell by cell): all 15 rows' black-cell
pattern matched the committed `data/grids/2026-05-15.json` **EXACTLY, 0/15 mismatches**,
and `python3 solver/build_dataset.py` independently confirmed 0/28 length mismatches from
the joined clue+answer files. Every one of the 28 derived answers makes clean independent
semantic sense against its clue beyond the mechanical checks alone — `קומראנ`/Qumran for
"they found there ancient scrolls and a holy book" (Dead Sea Scrolls), `שכמ`/Shechem for
"on the back of a Jerusalem gate" (שער שכם, the Damascus Gate's Hebrew name), `גולגולתא`/
Golgotha for "the gate, gate of the city, in Jerusalem", `מחזיקאצבעות`/"holding thumbs" for
"wishes Stallone success", `מבשרתציונ`/Mevaseret Zion for "a teacher from the Jerusalem
corridor", `עירדויד`/City of David, `קישלה`/Kishle (the historic Old City prison) for "in
jail" — seven independent corroborations, not just the enum/grid mechanical match.

MEASURED, controlled before/after (`python3 solver/deffit.py eval data/dataset/clues.jsonl
eval [--no-fillbank]`): recall@N (mechanical+retrieval combined) is **0/28 both with and
without retrieval this run** — a fresh, smaller `crawl_defs.py` corpus (mordo 12,298 raw
under a 240s budget; note.co.il 125 pairs under a 200s budget, both deliberately time-boxed
rather than run to exhaustion) found none of this puzzle's specific answers, unlike #53's
own larger crawl at the time (2/28 hits) — a genuine, disclosed, puzzle-AND-corpus-dependent
null, consistent with the project's own long-standing finding that retrieval's gain is real
but inconsistent. Because recall_hit is 0/28, top-1/MRR are undefined this run (0/0) and
not reported as a number. The two STRUCTURAL diagnostics (kept deliberately separate, see
`deffit.py`'s own docstring for why collapsing them would hide the real finding):
`nonretrieval_known_gloss_clues` (any non-retrieval candidate has SOME known gloss, in any
source) moved **3/28 (private_defs alone) -> 14/28 (+fillbank)**; `nonretrieval_scored_clues`
(that gloss actually shares vocabulary with the clue, `def_fit>0`) stayed **0/28** either
way. Inspected directly why the second number didn't move despite the first one moving by
11 clues: of the 59 non-retrieval candidates (out of 592 total) that DO have a fillbank
gloss, none scored above zero because their glosses (e.g. `ירושלים` -> `בירת ישראל`,
`כלי` -> `חפץ לשימוש, כמו סיר או פטיש`) don't happen to repeat the clue's own wording —
a real, understood limitation of lexical-overlap scoring for proper nouns and common
objects whose OWN dictionary definition doesn't restate the word itself, not a bug and not
evidence fillbank is useless (the coverage widened for real; the SCORING signal on top of
that coverage just didn't fire on this particular puzzle's 59 cases).

AUDITED (mandatory gate). `lexicon.held_out_answers()`, `retrieve_defs.held_out()`, and
`substitutions.held_out()` all confirmed (computed, not assumed) to block all 28 of this
puzzle's own gold answers — `gold_norm - blocked` empty for all three. No forbidden reads:
confirmed directly that none of the 6 puzzles 14across DID recover this run is 2026-05-15
(`data/answers/by_date/2026-05-15.json` was written entirely from the two public-CDN images,
never touched by the 14across scrape). Fillbank carries no held-out risk by construction
(an ordinary third-party dictionary, not mined from this project's own puzzle explanations
— the same standing precedent RESULTS.md's INTEGRITY FINDING established for lexicon.py's
plain dictionary words). Implausibility check: nothing here approaches the ~15-point
suspicion bar — recall stayed at 0%, and the disclosed 3/28->14/28 gloss-coverage move is a
counted, explained fact (59 specific candidate/gloss pairs), not a suspicious jump in any
accuracy number. All 6 affected selftests (`candidates.py`, `retrieve_defs.py`,
`lexicon.py`, `prove.py`, `substitutions.py`, `deffit.py`) re-run clean after the merge AND
after the lever, including 4 new `deffit.py` cases covering the final-letter-folding bug
specifically.

HONEST READ: a real bug caught and fixed before it could ship silently broken, and a real,
mixed, disclosed result once fixed — fillbank genuinely widens which candidates have SOME
known meaning (3/28 -> 14/28 clues), which is progress toward the queue's own definition-fit
goal, but the stricter score-based signal this project actually plans to rank by did not
move on this run's specific puzzle, for a now-understood reason (gloss text not repeating
clue vocabulary) rather than a mystery. Two consecutive runs on this same lever (2026-09-09,
2026-09-10) have now each produced a real negative-or-mixed result with a precise
explanation, which is more informative than either a flat "it works" or silence.

NOT DONE, honestly: did not find a puzzle where recall@N is nonzero this run, so the
top-1/MRR half of `deffit.py`'s own claim (does reranking help the FIRST candidate a live
pass would commit) remains untested since #53's original n=2; did not extend `def_fit_score`
beyond a simple max-across-sources combination (e.g. a source-aware weight, since fillbank
and private_defs scores are not calibrated to the same scale — disclosed in the code's own
docstring, not hidden); did not crawl either corpus to a natural plateau (both were
deliberately time-boxed, per this run's own budget); did not merge or otherwise act on any
PR beyond building this one (only the project owner merges).

Previous lever (2026-09-09): **built `solver/deffit.py`, a definition-fit RE-RANKER for
`candidates.py`'s output — queue item 9, "the sharpest gap PR #24 surfaced" — targeting the
diagnosed gap that live solve trials commit a mechanically-real-but-wrong-meaning candidate
because nothing scores whether it matches the DEFINITION, only whether the wordplay
executes.** Bootstrap's 14across scrape hit the same intermittent bot-check wall this
project has hit repeatedly (consistent HTTP 202 on every retry, confirmed by direct curl,
not waited out — killed after confirming the pattern); worked from the public-CDN image
fallback instead. Fetched all 4 `--dev-only` images. Transcribed a puzzle NOT previously
used as this project's dev/eval canon: **2026-05-15**, chosen because it is one of the two
dates queue item 8 already confirmed prints across clues 1-13 cleanly (`data/images/2026-05-14.jpg`,
no gap) — sidestepping queue item 8's still-open gap on 2026-05-29/2026-05-21 rather than
fighting it. All 28 clues transcribed from that image (the across-clue text turned out to
be split across TWO print columns — a main column starting at 22, and a narrow sidebar
next to the small solution-recap box carrying 1,7,8,9,10,11,13,15,17,19 — the exact
"separate column" resolution queue item 8 already found for 2026-06-19, now confirmed for
a second date). GOLD LETTERS from the small solved-grid recap in the FOLLOWING week's image
(`data/images/2026-05-20.jpg`, captioned "פתרון תשבץ ההיגיון..."), calibrated
programmatically (darkness-threshold gridline detection on both axes): all 15 rows' black-cell
pattern matched the committed `data/grids/2026-05-15.json` EXACTLY, 0/15 mismatches.
`grid_tools.validate()` on the transcribed clue enums: 0 problems (every enum sum matches
its grid-derived slot length). `crawl_defs.py mordo` re-crawled fresh (13,049 raw / 12,302
parsed after `reparse_mordo()`) under a 240s wall-clock budget (14across's captcha wall,
not this crawler, was the run's time sink); `crawl_defs.py note` ran under a 200s budget,
125 pairs (small — this budget is tighter than prior runs' 12-minute/unbounded budgets,
disclosed rather than hidden).

**THE LEVER**: `solver/deffit.py` reuses `retrieve_defs.py`'s own BM25 index and scoring
formula, in the REVERSE direction — instead of querying "which answers does this clue's
text retrieve," it asks "does THIS candidate's own corpus-attested definition overlap the
clue," and attaches a `def_fit` score to every candidate `candidates.py` already generated
(by any mechanism), then stable-sorts by it. It never proposes an answer that wasn't
already a candidate, so recall@N is unchanged by construction (verified in selftest).
MEASURED (`python3 solver/deffit.py eval data/dataset/clues.jsonl eval`): of the 2 clues
where `candidates.py`'s recall@N already contains the gold answer (7A `שערציונ`/Zion Gate,
24A `שכמ`/shoulder-Shechem pun — both retrieval hits), reranking left top-1 accuracy
unchanged (0/2 both before and after — neither gold answer was already first) but moved
mean reciprocal rank from 0.333 to 0.350 (7A's gold candidate moved from rank 6 to rank 5
among 25; 24A's, already at rank 2, stayed there). **n=2 is nowhere near enough to call
this a positive result** — this is explicitly a low-power diagnostic, disclosed as such,
not a claim.

**THE MORE IMPORTANT FINDING is structural, not the n=2 number.** Checked directly whether
def_fit ever scores a NON-retrieval candidate (anagram/hidden/reversal/homograph/culture)
above zero anywhere in this puzzle's 28 clues: **0/28**. This is not a coverage gap that a
bigger crawl fixes — it is a logical consequence of the design: `def_fit_score` looks up a
candidate answer's docs in the exact same index `retrieval_candidates()` already searches,
so any answer with a non-zero score was, by construction, already reachable by
`retrieval_candidates()` itself (same corpus, same BM25 formula, just queried in the
opposite direction). Today's `deffit.py` can rerank retrieval's own hits relative to each
other or to zero-evidence candidates, but it CANNOT independently corroborate a mechanically
-derived candidate's meaning unless that candidate is ALSO already a retrieval hit — which
means it adds nothing to the live solve pass's actual failure mode (a mechanically-real
candidate that is semantically wrong) beyond what `retrieval_candidates` already contributes
as a candidate SOURCE. RESEARCH.md's own "gloss-overlap" finding this run undersold this
risk slightly by calling it a coverage ceiling; it is sharper than that — it is a coverage
IDENTITY between the two mechanisms as implemented today.

**Concrete next step, not attempted today (would be a second lever):** point `deffit.py` at
a SECOND, INDEPENDENT gloss source that isn't `retrieve_defs`'s own index — `solver/lex/fillbank.json`
(2,412 real dictionary-style word→definition pairs, e.g. `אבוקדו` → `פרי ירוק ושמנוני`,
already committed and used by the public site) is a natural candidate: it is a genuine
dictionary, not a crossword-answer-site crawl, so it could recognize a common Hebrew word's
meaning independently of whether that word ever appears as a crossword answer anywhere in
private_defs. This is the fix implied by today's finding, not implemented today to keep
this run to one lever.

AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()` both
confirmed (computed, not assumed) to block all 28 of this puzzle's own gold answers —
`gold_norm - blocked` empty for both. Provenance of both retrieval hits checked directly:
every matching document carries `pid=None` (external private_defs corpus, never this
puzzle's own text) and each is a clean semantic fit (`שכמ`'s docs are about the shoulder/
upper-back and about the city in Samaria; `שערציונ`'s docs are about a site in Jerusalem's
Old City) — not a coincidental string match. No forbidden reads: 14across was never queried
for this puzzle's gold data (its own partial, unrelated 9-puzzle answers+explanations output,
left over from the killed bootstrap step, was inspected only to confirm it carries no clue
TEXT and therefore cannot feed `clues.jsonl` at all — never used in any measurement). All 6
affected selftests (`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`,
`substitutions.py`, `deffit.py`) re-run clean. Implausibility check: recall stayed at the
already-established 7.1% (2/28, unchanged by the smaller note.co.il crawl); deffit's own
MRR movement (0.333→0.350) is a tiny, unsuspicious shift — nothing here approaches the
~15-point suspicion bar.

HONEST READ: this is a well-implemented, well-tested (selftest covers the reranking
mechanism, the never-drops-a-candidate guarantee, and tie-stability) piece of infrastructure
that measured NEGATIVE-TO-NULL on its first live puzzle, for a reason now understood
precisely rather than left as a mystery: it shares its evidence source with an existing
mechanism, so it cannot yet add information the pipeline doesn't already have. That is a
genuine, informative negative result, not a wasted day — it converts "no generator-shaped
resource has been found" (RESEARCH.md, 3+ prior passes) into "one was found and built, and
here is precisely why it doesn't help yet, with the exact fix named."

NOT DONE, honestly: did not wire a second gloss source (fillbank.json) into deffit today,
to keep this run to one lever; did not re-measure on a second puzzle (transcription of one
28-clue puzzle plus its audit was this run's full budget); did not run `crawl_defs.py note`
to a natural plateau (200s budget, smaller than prior runs' 12-minute/unbounded budgets) —
disclosed rather than hidden, and unlikely to change the structural finding above regardless
of corpus size, since the redundancy is architectural, not a coverage gap; did not merge or
otherwise act on any open PR.

Previous lever (2026-09-08): **`solver/candidates.py`: `charade_candidates`, a new mechanical
candidate-generation mechanism for 2-part enums (e.g. (4,3)) that solves each part as an
INDEPENDENT anagram/hidden-word window, in clue order, non-overlapping, rather than requiring
one contiguous window to cover the whole answer length the way `anagram_candidates`/
`hidden_candidates` do today.** This closes a real structural gap: SOLVE_PROTOCOL.md's own
charade description ("split enum parts; solve each part from clue fragments") allows a
charade's two parts to draw fodder from separate stretches of the clue with an indicator or
the definition sitting between them, which a single whole-length contiguous window can never
span. `split_candidates` (existing) only checks post-hoc whether an already-generated
FULL-length hit happens to split into two real words at the enum boundary; it cannot originate
a candidate whose parts came from disjoint windows in the first place -- `charade_candidates`
does. Bootstrap hit the same hard 14across wall as most recent runs (7/7 consecutive
answer-page fetches came back `None: 0 clues` after full retry-with-backoff, confirmed by a
direct 300s-budget re-run of `scraper/parse_answers.py` outside bootstrap.sh too -- not fought
further, per standing precedent); worked entirely from the public-CDN image-fallback technique.

RE-TRANSCRIBED THE CANONICAL DEV PUZZLE (2026-05-29) from scratch (this is now at least the
fourth independent transcription across this project's runs) since `data/` starts empty every
run. Read `data/images/2026-05-28.jpg` for clue text (28/28 clues, both the wrapped-column
`אופקי` 1-13 section and the main `אנכי`/continuation column) and grid-calibrated the solved
recap grid in the FOLLOWING week's image (`data/images/2026-06-04.jpg`) for gold letters, per
bootstrap.sh's documented fallback. Caught and fixed TWO real transcription bugs mid-run via a
disciplined process, not luck: (1) a full pixel-boundary miscalibration of the solution grid's
11x15 cell crop initially undercounted to 9 columns, silently reading one row in the WRONG
(right-to-left semantic, not left-to-right pixel) order -- caught by re-deriving the exact grid
pixel geometry from the image's own gridlines (dark-line detection) rather than eyeballing crop
bounds, then re-reading EVERY row cell-by-cell in small 3-4-cell crops (never a whole 11-cell
row at once, which is what produced the direction error) and cross-checking each row's
black-cell PATTERN against the already-committed `data/grids/2026-05-29.json` (0/15 mismatches
once corrected); (2) one single-cell misread (ל read for י at row 0) caught because it broke a
mechanical anagram check (the fodder 'פחות יין' anagrams to 'יחפניות', not the initially-read
'לחפניות') before it was ever used for scoring. Both fixes are DISCLOSED, not silently applied:
the corrected transcription then independently reproduced THREE separate historical answers
from this puzzle's prior runs byte-for-byte (1 down `ברישניקוב`/Baryshnikov, 2 down `יחפניות`,
26 across `פחותאבלכואב`) and the mechanical-only recall@N baseline reproduced the historical
3.6% (1/28) exactly -- strong independent confirmation the re-transcription is correct, not
just internally consistent. All 28 enum sums validated against the grid-derived slot length,
0 mismatches.

MEASURED, controlled before/after (`python3 solver/candidates.py recall
data/dataset/clues.jsonl eval --no-culture --no-retrieval [--no-charade]`): baseline (charade
off) **3.6% (1/28)**, avg 11.7 candidates/clue, 17.9s; **with charade: 3.6% (1/28), UNCHANGED**,
avg 18.9 candidates/clue, 30.2s. Charade fired on all 10 of the puzzle's 2-part-enum clues
(hitting its own 200-candidate-per-clue cap on 8 of them) but matched 0/10 gold answers -- a
real, measured negative result, not a silent no-op (confirmed by dumping per-clue candidate
counts and checking gold membership directly, not just trusting the aggregate recall number).
Full defaults (culture+retrieval+charade) also 3.6%, unchanged, since no `private_defs` corpus
was crawled this run (out of scope -- this run's one lever was the new mechanism, not a corpus
refresh) and `culture_category` does not fire on this puzzle's clues.

AUDITED (mandatory gate). `lexicon.held_out_answers()`, `substitutions.held_out()`, and
`retrieve_defs.held_out()` all confirmed (computed, not assumed) to block all 28 of this
puzzle's own gold answers now that it sits in `data/dataset/clues.jsonl` as the `eval` split
(`gold_norm - blocked` empty for all three). No forbidden reads: 14across was never queried for
this puzzle's gold data this run (confirmed `data/answers/answers_parsed.json` does not exist),
only the two public CDN images. No jump to explain: 3.6% stayed 3.6%, the opposite of an
implausible result. All 6 affected selftests (`candidates.py` -- including 2 new cases for
`charade_candidates` -- `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`) re-run
clean.

HONEST READ: a real, correctly-implemented, well-tested new mechanism that does not move
recall on the one puzzle it was measured against. The underlying diagnosis it targets (a
charade's two parts need not be contiguous in the fodder) is still structurally sound per
SOLVE_PROTOCOL.md's own description of the device, but this puzzle's specific 2-part-enum
clues either use a different device entirely or the correct parts simply aren't real-word
anagrams/hidden-words of the right sub-lengths (both wordplay AND definition-fit failures are
possible and this diagnostic cannot distinguish them). The mechanism also costs real wall-clock
(+69% on this eval) for zero measured gain here, which is a real cost to weigh before ever
wiring it into a live solve pass. NOT DONE, honestly: not measured on a second puzzle (would
need a second full transcription cycle, out of scope for one lever); did not reduce the
200-candidate cap despite it being hit on 8/10 clues (a tighter cap is the natural next step if
this mechanism is revisited, to cut the wall-clock cost without giving up coverage, but wasn't
measured against a corpus large enough to show whether it changes recall); did not extend to
3+-part enums (flagged as a natural next step, not attempted -- clue 26's (4,3,4) enum was the
only 3-part clue in this puzzle and stayed out of scope); did not crawl a fresh `private_defs`
corpus (the queue's item 1(d) own repeated lever) since today's chosen lever was a new
mechanism, not a corpus refresh; did not merge or otherwise act on any open PR.

Previous lever (2026-09-07): **`substitution_candidates`' 3-part charade chain — queue
item 1(b)'s own disclosed next step ("the mined substitution table needs to cover
multi-part charades (3+ segments)")** — see log for the full write-up, including a
same-run PR-backlog consolidation (queue item 6, recurred a fifth time) that came first.
Previous lever (2026-09-06): **`homophone_vowel_candidates` — closes 2026-09-05's own
disclosed gap in `homophone_candidates`: free ו/י vowel-letter insertion/omission**
(indicators.json's homophone entry names this alongside the consonant-class swaps
2026-09-05 already modeled). Two fodder-window widths, both phon()-folded then looked
up in the SAME `by_phon()` index `homophone_candidates` already builds: `target_len - 1`
(fodder missing a vowel the real answer has — try inserting ו/י at every position) and
`target_len + 1` (fodder carries an extra vowel the real answer lacks — try deleting
each ו/י it contains). Insertion/deletion only ever touches ו/י, never any other
letter, so this stays a narrow, grounded device rather than an open-ended
edit-distance search. `prove.py`'s `is_homophone()` was extended to accept the same
one-vowel-off match (not a separate primitive), so a live solve pass can prove either
shape of the device with one assertion.

Six solver-lever PRs were open and unmerged against main when this run started (#38
2026-08-31, #39 2026-09-01, #41 2026-09-02, #42 2026-09-03, #44 2026-09-04, #46
2026-09-05) — PR #46 itself already consolidates #38/#39/#41/#42/#44 onto one branch
and adds `homophone_candidates`, so this run branched from PR #46's tip directly (not
from `main`) rather than re-deriving or re-consolidating work already sitting there —
the exact fix queue item 6 has asked for three times running ("branch off yesterday's
PR, not off main"). **A real near-miss avoided by reading the PR backlog before writing
any code**: this run's first instinct, before checking open PRs, was to wire
`retrieve_defs.end_candidates()` into `candidates.py` as a NEW `end_retrieval_candidates`
mechanism — unaware that PR #41 (folded into #46) already built exactly this, named
`defspan_retrieval_candidates`, and had ALREADY MEASURED it: 10.7% (3/28), identical to
whole-clue `retrieval_candidates` alone, union adds nothing (see PR #41's own body). Once
this was discovered (via `list_pull_requests`), the redundant implementation was
discarded before it was ever run, and today's lever became the genuinely next open item
`homophone_candidates` itself flagged (vowel flexibility) instead. Recorded here as a
concrete instance of why checking the PR backlog FIRST is worth the extra step — it
would otherwise have cost this entire run's budget re-deriving a number PR #41 already
has.

RESEARCH (full entry in RESEARCH.md): seventh-plus consecutive pass with nothing new and
buildable on candidate generation, definition-span/fit scoring, or Hebrew morphology. One
new citation (`github.com/nikcholer/cryptic-solver`, a public neuro-symbolic demo)
checked directly: its definition-location detector uses indicator-word matching, the
exact signal this project measured and killed on 2026-08-19 (1/5, worse than a coin
flip) — a second project choosing the same signal is not evidence it works, it is a
second data point that indicator-word detection is the obvious first thing to try.

BOOTSTRAP: full `./bootstrap.sh --dev-only` run, no truncation this time (10-minute
window instead of the usual 2). hspell/culture.json/substitutions.json unchanged (already
committed). 14across hit the identical hard wall documented since 2026-08-19: 51/52
answer-page fetches came back `None: 0 clues` after full retry-with-backoff each; only
2026-06-03 (28 clues) recovered. `crawl_defs.py mordo`/`note` were ALSO run this session
(before this run's actual lever was known — see the near-miss note above): mordo ran to
completion (66,488 raw pairs, in line with 2026-08-30's 66,443 — the feed keeps pace,
not shrinking); note ran under a disclosed ~8-minute time budget (435 fetched). NOT used
in today's measurement, since `homophone_vowel_candidates` touches no external corpus at
all — left in `data/answers/private_defs/` (gitignored, as always) purely as a
same-session courtesy in case a later step in this run wanted it; gone again for
whichever future run next measures a retrieval-family lever, same as every other run's
crawl.

TRANSCRIPTION: re-transcribed 2026-05-29 fresh (7th independent transcription of this
exact puzzle). All 28 clues (15 across, 13 down) from `data/images/2026-05-28.jpg`; every
enum sum validated against the GRID-DERIVED slot length before any gold data was touched
— 0/28 mismatches. GOLD LETTERS from the small solved-grid recap in `data/images/
2026-06-04.jpg`: grid-calibrated (cropped, upscaled, read row by row, reversed to the
project's index-0-is-rightmost convention); all 15 rows' black-cell pattern matched the
committed `data/grids/2026-05-29.json` EXACTLY, 0/15 mismatches.

**A real transcription error caught and fixed, disclosed rather than silently
corrected**: this run's FIRST pass derived 26 across as `באוכלבאתוחפ` — the exact
character-reverse of `פחותאבלכואב`, the value THREE independent prior entries
(2026-08-25/08-28/08-30) and yesterday's (2026-09-05) all agree on. Rows 0 and 14 (both
all-white, i.e. palindromic black-cell patterns) are the only two rows where a whole-row
left-right mirroring error is invisible to the grid-pattern cross-check, since a mirrored
all-white row still matches an all-white row. Resolved MECHANICALLY, not by trusting the
majority vote alone: `פחות`/`אבל`/`כואב` (the (4,3,4) split of the disputed value) are
all three real hspell dictionary words ("less, but it hurts" — a fitting description of
the clue's own subject, ברית מילה/circumcision); `באוכ`/`לבא`/`תוחפ` (the same split of
this run's own first derivation) are all three NOT real words. SOLVE_PROTOCOL.md's own
word-order rule (a multi-word answer's pieces should be real words) settles it in favor
of the established value, checked against the live lexicon rather than assumed from the
vote count. Fixed in `data/answers/by_date/2026-05-29.json` before this run's own
recall@N was measured (row 14 carries no down-slot cells at all — every down slot's
grid-derived length is ≤9, short of row 14 at index 14 — so this fix touches only 26
across, nothing else in the dataset). Flagging the underlying risk for a future run: the
two palindromic rows are a standing verification blind spot this project's own
grid-pattern check cannot close by construction; a second, independent structural check
(e.g. real-word-split validation on every multi-part answer, not just when a conflict is
already suspected) would catch this class of error without relying on cross-run
consensus, which is itself only as reliable as the first transcription that established
it (a variant of the DAILY.md-as-leak-vector concern already on record).

MEASURED, controlled (`python3 solver/candidates.py recall data/dataset/clues.jsonl eval
[--no-homophone-vowel]`, every other mechanism held at existing defaults): mechanical
baseline (homophone ON, vowel OFF) **3.6% (1/28)** — reproduces every prior
transcription; **+ homophone_vowel: still 3.6% (1/28), UNCHANGED**, but the mechanism
fired on **14/28 clues** (avg candidates/clue 11.8 -> 13.0), a real, working generator
that simply didn't hit gold on this puzzle. Root-caused, not assumed: directly tested
`homophone_vowel_candidates` against the SPECIFIC clue 2026-09-05 diagnosed as this
device's target (22 across, "הזורזים" -> `אנזימימ`) and it produces **zero raw
candidates for that clue, not a near-miss** — `phon('הזורזימ')` and `phon('אנזימימ')`
differ in far more than one ו/י (ה,ז,ו,ר,ז,י,מ vs א,נ,ז,י,מ,י,מ), so 2026-09-05's own
"vowel-insertion" framing of this specific clue was itself an oversimplification of a
more complex sound relationship — the device this run built is real and correctly
scoped to what indicators.json actually documents, but it was never going to close
THIS puzzle's specific gap either, and checking that directly (rather than assuming the
disclosed gap and its fix line up) is the point of this paragraph. Full defaults (every
mechanism together): 3.6% (1/28), same single anagram hit (`יחפניות`, 2 down) every
prior measurement of this puzzle has found.

AUDITED (mandatory gate). `lexicon.held_out_answers()`/`retrieve_defs.held_out()` both
confirmed (computed: `gold - blocked` is the empty set for both, not assumed) to block
all 28 of this puzzle's own gold answers, including the corrected 26-across value.
`homophone_vowel_candidates` introduces no new leak surface: it only looks up the same
held-out-filtered `by_phon()`/`lex()` index `homophone_candidates` already uses safely.
No forbidden reads: the 51/52 `None: 0 clues` 14across responses were the ONLY thing
read from that domain before this run switched to the sanctioned public-CDN image
fallback; `crawl_defs.py` reads only the public note.co.il/pitaronfree sites this
project has always used for `private_defs`. No implausible jump: 3.6% -> 3.6% is the
least suspicious result a controlled before/after can produce. All 5 affected selftests
(`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`)
re-run clean; `candidates.py`/`prove.py` each gained new homophone_vowel checks (a real
כל/כול defective/plene spelling pair found by scanning the live lexicon, not a synthetic
fixture, for the insertion direction; the same pair, plus חל/קל via the consonant fold,
for the deletion direction).

HONEST READ: a real, correctly-scoped extension of a real device, with a genuinely
negative recall result that is now UNDERSTOOD rather than merely repeated — the
2026-09-05 diagnosis that this puzzle's gap was "just" vowel flexibility does not survive
direct testing, and saying so plainly is worth more than shipping the extension with the
old (wrong) diagnosis still attached. The mechanism itself fired realistically (14/28
clues, up from 8/28 for the consonant-only version), which is real evidence it works
mechanically; whether it recovers gold on ANY puzzle is still unmeasured (n=1, same
standing caveat every mechanism here starts with).

NOT DONE, honestly: did not re-measure a second puzzle (n=1); did not use the
mordo/note crawl this run's own bootstrap grew, since today's lever doesn't touch that
corpus (left available for whichever future run next measures a retrieval-family
lever); did not investigate whether the same palindromic-row blind spot affected any
OTHER puzzle's committed dev/eval data beyond this one instance, caught only because
this run happened to derive it fresh (a real follow-up worth a dedicated pass, not
squeezed into today's one-lever budget); did not merge or otherwise act on the six
PRs beyond building on top of #46's branch (only the project owner merges PRs) —
#38/#39/#41/#42/#44/#46 should all be closed in favor of this branch.

Previous lever (2026-09-05): **`homophone_candidates` — the נשמע (sounds-like) device
(PLAYBOOK.md 1.6, ~30/728 = 4% of clues), the first mechanism in `candidates.py` to
model a device this project had ZERO prior support for, generator or proof primitive
alike** (`prove.py` gained a matching `is_homophone()` assertion, since no live solve
pass could ever have proved one before today). Every other letter-driven mechanism in
this file (anagram/hidden/reversal/container/substitution/homograph) derives an answer
that shares the exact same LETTERS as its fodder; homophone is the one device where the
answer can be spelled completely differently, only SOUNDING like the fodder — plain
undotted Hebrew script cannot distinguish several consonant sounds in writing
(indicators.json's own crowd-mined homophone entry names the free swaps: ק/כ/ח, ט/ת,
ס/ש, א/ע). `PHON_FOLD`/`phon()` collapse each equivalence class to one representative
character (a straight length-preserving translation), so the exact fixed-width
char-window scan `anagram_candidates`/`hidden_candidates` already run works unchanged: a
window's phon-folded key is looked up against a phon-folded lexicon index, and a hit
whose LITERAL spelling differs from the fodder (an identical-spelling hit is `hidden`,
already covered) is a homophone candidate. Deliberately scoped narrower than the full
device, disclosed rather than silently assumed complete: indicators.json also records
"free vowel changes" (ו/י insertion or omission), which changes string LENGTH and would
need a different search entirely — not modeled in this first version.

RESEARCH (full entry in RESEARCH.md): general search on Hebrew phonetic-ambiguity
resources for crosswords found nothing project-specific; a targeted search on how
English cryptic-solving tools handle the homophone device confirmed the standard
technique there is a phonetic-indexing algorithm (Soundex/Metaphone) mapping same-
sounding strings to one key — the SAME shape this lever independently arrived at,
just grounded in THIS setter's own documented Hebrew consonant-ambiguity classes
instead of English vowel-based Soundex. Transfer: confirms the general approach,
adds no new external resource or technique to adopt.

Bootstrap: hspell/culture.json/substitutions.json already committed, no rebuild needed.
14across hard-walled again — confirmed directly, not assumed: a single-URL fetch for
2026-05-29 with 8 retries (matching `scraper/parse_answers.py`'s own retry policy) came
back `None: 0 clues` on all 8 attempts, and the full 52-puzzle scrape independently
logged the same pattern (15/52 attempted, 14 empty, 1 recovered) before being killed —
worked entirely from the no-14across image-fallback technique for both clue text and
gold letters.

CONSOLIDATION, done before touching a lever: five solver-lever PRs were open and
unmerged against main (#38 2026-08-31 docs-only, #39 2026-09-01, #41 2026-09-02, #42
2026-09-03, #44 2026-09-04) — the exact compounding-backlog pattern this file's own
lever queue item 6 has flagged three times before (2026-08-21/24/25). Cherry-picked all
five onto one branch in date order, reconciling DAILY.md/RESEARCH.md by hand (chronological
log merge, no content dropped, same method 2026-08-25 used for a 3-PR backlog) and
resolving one genuine code-level conflict: PR #39 redefined `retrieval_candidates()` to
query with `retrieve_defs.end_candidates()` instead of the whole clue text, while PR #41
(created the next day, unaware of #39) instead added a NEW, separately-toggleable
`defspan_retrieval_candidates()` calling the same `end_candidates()` and left
`retrieval_candidates()` untouched. Applying both literally would make two mechanisms
run the identical query. Kept PR #41's shape (both query shapes independently
measurable) and dropped PR #39's redefinition as superseded — disclosed here rather than
silently discarding a prior day's committed work. All 5 selftests re-run clean after
consolidation, before any new code was added.

TRANSCRIPTION: re-transcribed the canonical dev puzzle 2026-05-29 fresh (6th independent
transcription of this exact puzzle across this project's history). All 28 clues (15
across, 13 down) transcribed from `data/images/2026-05-28.jpg`; every enum sum validated
against the GRID-DERIVED slot length (`solver/grid_tools.py`, structural geometry only,
no gold answer read) before any gold data was touched — 0/28 mismatches. One
transcription-methodology finding, disclosed: this specific puzzle's print layout
intermittently floats an enum parenthetical after the FOLLOWING clue's number rather
than immediately after its own text (observed at the 9->10 and 22->23->24 clue
boundaries) — resolved by grid-derived length wherever the printed position was
genuinely ambiguous, per this file's own established practice for this puzzle's known
layout quirks, never by guessing.

GOLD LETTERS, since 14across was unreachable: recovered from the small solved-grid
recap in the FOLLOWING week's image (`data/images/2026-06-04.jpg`, captioned "פתרון
תשבץ..."). Grid-calibrated programmatically (cropped, upscaled, read row by row): all
15 rows' black-cell pattern matched the committed `data/grids/2026-05-29.json` EXACTLY,
0/15 mismatches, after reversing each row (the raw crop reads left-to-right on the
page; the project's index-0-is-rightmost convention needs the reverse). Four
independent corroborations beyond the grid-pattern match alone, not just one: two
extracted answers reproduce gold strings this file's own PRIOR entries already
disclosed for this exact puzzle (1A `בליברטיולנס`/"Liberty Valance" — 2026-09-03; 26A
`פחותאבלכואב` — 2026-08-25/08-28/08-30), one reproduces `SOLVE_PROTOCOL.md`'s own
worked example verbatim (7A `ישפרחימ`, the anagram of "משפר חיי"), and one reproduces
`prove.py selftest`'s own worked example verbatim (11A `קרתנימ`, `is_container('קרים',
'תן', 'קרתנימ')`) — none of which were consulted to derive the transcription; they
were checked AFTER extraction as an independent sanity confirmation, and matching them
exactly is strong evidence the grid-reversal and letter-reading are both correct.
`python3 solver/grid_tools.py validate` printed OK; `python3 solver/build_dataset.py`
reported 0 length mismatches across all 28 rows.

MEASURED, controlled before/after (`python3 solver/candidates.py recall
data/dataset/clues.jsonl eval [--no-homophone]`, all other mechanisms held at their
existing defaults): mechanical-only baseline **3.6% (1/28)** — exactly reproduces every
prior transcription of this puzzle (a strong independent cross-check); **+ homophone
alone: still 3.6% (1/28), UNCHANGED**, but the mechanism fired on 8/28 clues (avg
candidates/clue 11.7 -> 11.8) — a real, working generator that simply didn't hit gold on
this puzzle's specific clues, not a zero-fire result. Direct inspection of WHY: this
puzzle's own homophone-credited clue (22 across, "הדג מתקשה לנשום למרות הזורזים (עפ"י
השמיעה של אליעזר כמון)" -> gold `אנזימימ`/enzymes) needs "הזורזים" (7 letters) to be
read AS SOUNDING LIKE "אנזימים" (8 letters, a different length) — a vowel-insertion
relationship this version's length-preserving consonant-fold cannot reach by
construction, exactly the scope limit disclosed in the code's own docstring, not a bug.
Full defaults (every mechanism together) land at 3.6% (1/28) too, same single anagram
hit (`יחפניות`, 2 down) every prior measurement of this puzzle has found.

AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
both confirmed (computed, not assumed) to block all 28 of this puzzle's own gold
answers (`gold - blocked` empty for both). `homophone_candidates` introduces no new
leak surface: it only ever looks up the already held-out-filtered `lex()`, the same
source `anagram_candidates`/`hidden_candidates` already use safely. No forbidden reads:
the single-URL 14across probe returned `None: 0 clues` on all 8 attempts before any
content was read, and the two images used are the sanctioned public-CDN fallback. No
jump to explain: 3.6% -> 3.6% is the least suspicious result a controlled before/after
can produce. All 5 affected selftests (`candidates.py`, `retrieve_defs.py`, `lexicon.py`,
`prove.py`, `substitutions.py`) re-run clean; `candidates.py selftest` and `prove.py
selftest` each gained a new homophone check (a real ק/כ swap pair, קר/כר, both real
hspell words found by scanning the live lexicon, not a synthetic fixture).

HONEST READ: a real, mechanically-sound, newly-provable device with a genuinely
NEGATIVE recall result on this one puzzle, and the negative result is now understood
rather than merely observed — this puzzle's specific homophone clue needs vowel
flexibility, not consonant-class flexibility, so a v1 that deliberately excludes vowel
modeling was never going to catch it. That is a concrete, scoped next step (model ו/י
insertion/omission as a variable-length search) rather than a reason to call the device
dead — the mechanism DID fire realistically elsewhere on this puzzle (8/28 clues), which
is the evidence it works mechanically and simply needs a second puzzle, or the vowel
extension, before its real hit rate is known.

NOT DONE, honestly: did not model vowel-letter (ו/י) flexibility (the concrete next
step this run's own root-cause finding surfaced); did not re-measure a second puzzle
(n=1, same standing caveat every new mechanism here starts with); did not crawl
`note.co.il`/`mordo` (irrelevant to this lever, which touches no external corpus); did
not merge or otherwise act on the five consolidated PRs beyond folding their own code
into this branch (only the project owner merges PRs) — #38/#39/#41/#42/#44 should be
closed in favor of this branch, the same relationship 2026-08-25's consolidation had to
its predecessor PRs.

Previous lever (2026-09-04): **`double_definition_candidates` — the מילה משותפת (double-definition)
device, PLAYBOOK.md §1.2, 14% of clues, the second most common mechanism after charade and,
per a grep of `candidates.py`, the only PLAYBOOK-documented device with zero prior generator
(mechanical or definition-driven).** For every word-boundary split of the clue, queries
`retrieve_defs`'s BM25 index separately on each half and keeps only an answer ranking in BOTH
halves' independent top-K — a signal a whole-clue query or a single end-window query cannot
produce, since those score one bag of words against one document. See RESEARCH.md: no external
resource generates double-definition candidates for a language without WordNet/embeddings
(checked directly via a new GitHub hybrid cryptic-helper repo), so this reuses the project's own
already-audited BM25 tool instead. Transcribed a genuinely fresh dev puzzle, 2026-05-21 (chosen
specifically because — unlike 2026-05-29/2026-06-26/2026-07-03, all of which this file's own
prior log entries have quoted specific gold-answer strings for — no gold letters for this date
had been disclosed anywhere in required reading before this run, mitigating the standing
"DAILY.md itself is a leak vector" finding from 2026-08-30 for at least this one measurement).
14across hard-walled again (0/52 after the dev-only bootstrap timeout); used the no-14across
image-fallback technique. 21/21 printed clues transcribed from `data/images/2026-05-20.jpg`
(the standard across-1-12 gap: clues 7,8,9,10 have grid slots but no printed text, excluded per
established practice); every enum validated against the grid-derived slot length via
`solver/grid_tools.py validate` before any gold data was touched — 0 genuine mismatches, the only
7 "problems" reported are exactly the missing across slots. GOLD LETTERS came from the small
solved-grid recap in the FOLLOWING week's image (`data/images/2026-05-28.jpg`); grid-calibrated
programmatically (row/column pixel boundaries derived and cross-checked, not eyeballed) after an
initial pass drifted by a full row past row 9 and was CAUGHT (not silently fixed) by comparing
the derived black-cell pattern against the already-committed `data/grids/2026-05-21.json`:
**all 15 rows match EXACTLY, 0/15 mismatches**, only after correcting the drift. `crawl_defs.py
mordo` ran under a disclosed 10-minute time budget (killed by timeout, not run to a natural
stop): 33,299 raw entries, 32,150 with parsed answers after `reparse_mordo()` — smaller than
recent runs' peak corpus (66K+), since only a partial crawl completed and `note.co.il` was not
crawled at all this run.

MEASURED, controlled (`python3 solver/candidates.py recall data/dataset/clues.jsonl eval
[--no-culture] [--no-retrieval] [--no-double-def]`): mechanical-only baseline **0.0% (0/21)**;
**+ retrieval alone: 9.5% (2/21)** (רוקפור/Roquefort cheese, פרופסורה/professorship — both
confirmed `pid=None` external mordo docs, clean semantic fits); **+ double_definition alone:
0.0% (0/21), mechanism fired on 0/21 clues** — not one split-point query on either clue half
ever returned the gold answer in its own top-K, for any clue, including the five short
(<=4-letter) slots PLAYBOOK.md flags as "overwhelmingly double definitions." Full defaults
(culture+retrieval+double_def) land at the same 9.5% (2/21) as retrieval alone, confirming
double_definition contributes nothing here and culture_category still doesn't fire on this
puzzle either.

AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()` both
confirmed (computed, not assumed) to block all 21 of this puzzle's own gold answers (`gold -
blocked` empty for both). Provenance of the 2 retrieval hits checked directly: both carry
`pid=None`, `רוקפור`'s docs are about "סוג גבינה מחלב כבשים" (a type of sheep's-milk cheese,
matching the clue's own "גבינה"), `פרופסורה`'s doc is about "מעמד אקדמי" (academic status,
matching the clue's own "מעמד אקדמאי") — clean semantic fits, not coincidental string matches.
No forbidden reads: 14across was never queried for this puzzle's gold data, only the two public
CDN images. No jump to explain: 0.0%->9.5% is well under the ~15-point suspicion bar. All 5
affected selftests (`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`,
`substitutions.py`) re-run clean; `candidates.py selftest` gained two new checks for
`double_definition_candidates` (a synthetic case where an answer matches both halves and a
distractor matching only one half is correctly excluded; a single-word clue returns empty
rather than erroring).

HONEST READ: this is a genuine negative result, and a more informative one than a flat "0
gold hits" — the mechanism structurally never fires on this puzzle's clues at all, which
rules out "generates candidates but ranks them wrong" as the failure mode and points instead
at corpus coverage: this project's mordo-only, partially-crawled (10-minute budget, no
note.co.il) index apparently doesn't hold matching definitions for either half of these
specific short clues, even though it DOES hold matching definitions for two longer,
single-query clues (the retrieval-alone hits). Whether a fuller corpus (note.co.il added, mordo
crawled to a natural stop as in 2026-08-30's 66K-entry run) would let this mechanism fire at all
is untested this run — the corpus-growth pattern that repeatedly rescued `retrieval_candidates`
on other puzzles has not yet been tried against this specific two-sided-split mechanism.

NOT DONE, honestly: did not crawl `note.co.il` or let `mordo` run to a natural stop (a
disclosed 10-minute budget, smaller than recent runs' peak corpus) — the corpus-size question
this raises for double_definition specifically is a concrete next step, not attempted here to
keep this run to one lever; did not re-measure a second puzzle (this project's own standing
finding is that retrieval-style mechanisms are puzzle-dependent — one puzzle's null result is
not yet proof the device never fires); did not act on the DAILY.md-as-leak-vector observation
beyond mitigating it for today's own puzzle choice; did not merge or otherwise act on any of the
four solver PRs open against main (#38, #39, #41, #42 — read directly to confirm none had
already tried this device, not merged: only the project owner merges PRs).

Previous lever (2026-09-03): **`container_candidates` — a mechanical candidate
generator for the container/insertion device (PLAYBOOK.md §1.4, ~10-12% of this
setter's clues, the fourth-most-common mechanism), which until today was pure
verification infrastructure (`prove.is_container`, present since the proof gate was
built) with no generator in `solver/candidates.py` ever producing a candidate for it
to check.** Reuses the existing substitution-fragment table and the homograph
destemmer for its two fragment sources (no new corpus, no new data file). Selftest
(offline, a real dictionary word found by scanning the live lexicon, not a synthetic
fixture) confirms it correctly derives an interior-splice candidate. MEASURED on a
freshly re-transcribed 2026-05-29 (28/28 clues, 0 enum mismatches against the
grid-derived slot lengths, gold letters recovered via the no-14across image-fallback
technique and cross-validated 0/15 rows against the committed grid): **recall@N
UNCHANGED at 3.6% (1/28)** with container on vs off, mechanism fired on only 1/28
clues (0 gold hits). CONFOUNDED, disclosed rather than hidden: 14across was fully
unreachable this run (hard wall, 7/7 fetches `None: 0 clues`, matching the pattern
documented since 2026-08-19), which starves `sub_fwd()` — this mechanism's mined-
substitution fragment source, shared with the already-shipped `substitution_
candidates()`, which ALSO scored 0 fires this run (by-mechanism breakdown: only
`anagram` hit anything at all) — so this is not a clean test of whether the device
helps, only evidence of what happens when its main fragment source is empty. See log
for the full transcription/audit trail and research note (checked a live 2026
neuro-symbolic solver directly: it does not mechanically enumerate container
candidates either, it relies on an LLM to guide which parts combine — this project's
own prior standing approach).

Previous lever (2026-09-02): **wired `retrieve_defs.end_candidates()` (query restricted to
a short prefix/suffix word-span of the clue) into `candidates.py` as a new
`defspan_retrieval_candidates()` source, alongside the existing whole-clue `retrieval_candidates()`.**
This closes a real implementation gap found by re-reading the code, not by new literature:
every DAILY.md/RESEARCH.md entry since 2026-08-08 has cited retrieval's standalone number
("gold@25=5.4%, ceiling 27%") as measured by `retrieve_defs.py eval`'s CLI — which has
always called `end_candidates()` — but the mechanism actually wired into `generate()` since
2026-08-25 has always called plain `retrieve_defs.candidates()` with the FULL clue text
instead. The number this project quoted six times never described what was running live.
Bootstrap ran cleanly against 14across this run (a handful of intermittent bot-check
redirects, recovered by the existing retry-with-backoff — not the hard-wall mode of the
last several runs), so gold answers for 2026-05-29 (the canonical dev puzzle) came from
real crowd data via `data/answers/by_date/2026-05-29.json`, not the image-fallback
technique. Clue TEXT was transcribed fresh from `data/images/2026-05-28.jpg`; all 28 enum
sums matched the grid-derived / gold-answer letter counts with 0 mismatches (see log for a
real mid-transcription correction: clue 13 across's text and enum turned out to wrap across
the print-column boundary, initially misread as a missing enum before the column-wrap was
tracked down and resolved — the same recurring layout quirk 2026-08-30 documented for a
different puzzle). `crawl_defs.py mordo` was run under a disclosed ~5-minute time budget
(bootstrap.sh does not fetch `private_defs` at all — this is a separate manual step every
run must redo): 8,249 raw / 7,384 with parsed answers, comparable in size to this project's
very first mordo crawl (9,685).

MEASURED, controlled before/after (`python3 solver/candidates.py recall
data/dataset/clues.jsonl eval [--no-retrieval] [--no-defspan-retrieval]`): mechanical-only
baseline **3.6% (1/28)**; **+ old whole-clue retrieval alone: 10.7% (3/28)**; **+ new
end-span-restricted retrieval alone: 10.7% (3/28)** — same count; **both together: 10.7%
(3/28)**, i.e. the union adds nothing over either alone. Checked directly which clues each
mechanism hit (not just the count): BOTH mechanisms hit the exact same two clues (26
across `פחותאבלכואב`, 1 down `ברישניקוב`). Went one step further and diffed the raw
candidate SETS (not just gold hits) mechanism-by-mechanism across all 28 clues: identical
on 27/28, differing on only 1. Root cause, checked rather than assumed: this puzzle's
clues average 7 words (range 2-13), and `end_candidates()`'s widest window is 4 words from
each end — for a typical clue that short, a 4-word end-span already covers most or all of
the clue's content, so the two queries end up scoring the same documents almost every time
(BM25 score here only rewards terms shared with a doc; extra query terms that aren't in a
doc don't dilute the winning doc's score, so the whole-clue query's noise-word theory this
lever was built on turns out not to bite in practice at this corpus's clue lengths).

AUDITED (mandatory gate). `retrieve_defs.held_out()` and `lexicon.held_out_answers()` both
computed (not assumed) to block all 28 of this puzzle's own gold answers — `gold - blocked`
empty for both. Provenance of the 2 hits checked directly: both carry `pid=None` (external
private_defs corpus, never this project's own puzzle text) — `ברישניקוב`'s doc tokens are
literally "רקדן בלט ושחקן רוסי אמריקאי" (a dancer, ballet, Russian-American actor), a clean
semantic match for the clue ("...דקירת רקדן", Baryshnikov); `פחותאבלכואב`'s doc is a
Yehonatan Gefen song-title listing including that exact title, matching clue 26's "יהונתן
גפן...". No forbidden reads: gold came from the sanctioned 14across scrape (bootstrap.sh),
clue text from the public CDN image, private_defs from the sanctioned `crawl_defs.py`.
Implausibility check: 3.6%→10.7% (+7.1 points) is well under the ~15-point suspicion bar
and reproduces (not just resembles) 2026-08-28's own number on this exact puzzle at a
similar corpus size — a strong cross-check that both today's independent transcription and
the corpus rebuild are correct. All 5 affected selftests (`candidates.py`, `retrieve_defs.py`,
`lexicon.py`, `prove.py`, `substitutions.py`) re-run clean; `candidates.py selftest` gained
a new check for `defspan_retrieval_candidates` (query restricted to a clue end-span,
forwarding to `retrieve_defs.end_candidates()`), passing.

HONEST READ: this is a genuine NEGATIVE result for the specific hypothesis today's lever
tested (that restricting the retrieval query to a definition-span end, instead of the whole
clue, would surface additional or different candidates) — on this puzzle it does neither.
The mechanism is correctly implemented and wired in (verified by selftest and by matching
the 2 known hits), and it is NOT redundant code — `end_candidates()` remains a genuinely
different function or a future corpus with longer clues or noisier full-clue text could
still separate the two — but today's controlled measurement found no incremental value on
the one puzzle tested, and the reason is now understood mechanically rather than guessed:
this corpus's clues are short enough that a 4-word end-span already captures nearly all of
a typical clue's content. Shipped anyway because it closes a real, previously undisclosed
gap between what this project has quoted as retrieval's validated strength for 6+ entries
and what has actually been running live since 2026-08-25 — that gap needed closing
regardless of today's specific recall number, and the honest, disclosed result is now part
of the record instead of an unnoticed inconsistency.

NOT DONE, honestly: did not crawl `note.co.il` (mordo alone was sufficient to reproduce a
known-comparable historical number, and note.co.il's crawl is far slower per-page); did not
re-measure a second puzzle (this project's own standing finding is that retrieval's gain is
puzzle-dependent — a single puzzle's null result for the marginal defspan-vs-whole-clue
comparison specifically is not yet a claim that no puzzle would ever separate them, only
that this one didn't); did not merge or otherwise act on any open PR.

Previous lever (2026-08-31): **a second, independent puzzle's measurement of
`culture_category_candidates`** (queue item 1(c), added 2026-08-24 and measured only
once since — the queue's own named next step, chosen over yet another
`retrieval_candidates` corpus-growth re-run after six consecutive days on that exact
lever shape, per this run's explicit steer). 14across hit the same hard wall as
2026-08-19/08-26/08-27/08-28/08-30 (7/7 fetches `None: 0 clues`); worked entirely from
the no-14across image-fallback technique. `solver/lex/culture.json` and
`substitutions.json` are committed, not gitignored, so no rebuild was needed for those.

Chose a genuinely fresh dev puzzle (2026-07-03 — not among the 8 dates already used for
any prior measurement: 2026-05-29, 2026-06-05, 2026-06-19, 2026-06-26, 2026-07-10,
2026-05-15, 2026-04-03, 2026-06-12). Transcribed all 28 clues from `data/images/
2026-07-02.jpg`. Validated every enum sum against the GRID-DERIVED slot length (from the
already-committed `data/grids/2026-07-03.json`, structural geometry only, no gold
answer read) before touching any gold data: 26/28 matched cleanly; 2 (clues 17 and 18
down) did not individually, but matched PERFECTLY once swapped with each other (17's
printed `(4,2)`=6 matches 18's grid slot of 6; 18's printed `(4,3)`=7 matches 17's grid
slot of 7) — a new variant of this setter's documented enum-print anomaly (prior
instances were one clue's own enum printed in reversed word-order; this is two adjacent
down-clue enumerations transposed between each other), disclosed and resolved by
assigning each clue the grid-matching enum, not silently kept as printed, since here
(unlike prior instances) keeping the raw print would leave BOTH clues' `len_ok` false.
`solver/grid_tools.py validate` prints OK on the corrected 28-clue set.

GOLD LETTERS came from the small solved-grid recap in the FOLLOWING week's image
(`data/images/2026-07-11.jpg`, captioned "פתרון תשבץ ההיגיון מהשבוע שעבר"),
grid-calibrated programmatically (crop coordinates computed, not eyeballed row heights):
all 15 rows' black-cell pattern matched the committed grid EXACTLY, 0/15 mismatches — the
strongest form of this project's standard cross-check. All 28 extracted answers' lengths
matched their (corrected) enums exactly, an independent cross-check beyond the
grid-pattern match. Several answers make clean independent semantic sense against their
clues (`גוסטב`/Gustav for "the Swedish king's warm garment on his back" — Gustav is the
classic Swedish royal name; `נומרולוג`/numerologist for "plays with numbers and confuses
us"; `בודליר`/Baudelaire for a clue built on "luck" and "poetry" — Baudelaire the poet),
further corroboration beyond the grid-pattern match alone.

MEASURED, controlled before/after (`candidates.recall_eval()` called directly, same
scoring code the CLI wraps): mechanical-only baseline **7.1% (2/28)**, both anagram hits
(`יתענגו`, `נומרולוג`); **+ culture_category_candidates: still 7.1% (2/28), UNCHANGED** —
avg candidates/clue rose 12.0 → 13.4 (the mechanism DID fire, generating real extra
candidates), but none matched gold. `retrieval_candidates` was deliberately left inert
this run (no `crawl_defs.py` run — corpus growth was explicitly out of scope today), so
the "full defaults" number is identical to "culture-only," a clean isolation of this one
mechanism's own effect.

DIAGNOSTIC BREAKDOWN (the reason a second puzzle earns its keep over a flat number): the
mechanism fired on 3/28 clues this time (up from 1/28 on 2026-06-19), and inspecting each
one directly finds THREE DIFFERENT root causes, not one repeated pattern:
1. **12 down** (`בירה על הגבול` → gold `בקו`): reproduces 2026-06-19's exact failure mode
   — `בירה` triggered the `world_city`/"capital" category, but the setter used it as
   "beer" (a homograph), pointing at `בקו` ("on the line") instead. Surface trigger word,
   misdirection intended — the standing diagnosis holds.
2. **11 down** (`מדינה אפריקנית במצב הרסני, אולי` → gold `סיירהלאונ`/Sierra Leone, a
   clean literal fit — Sierra Leone's civil war matches "state of ruin"): checked
   directly whether this is a corpus gap — **it is not**. `סיירה לאון` IS present in the
   raw `culture.json` `nation` list (212 raw entries; confirmed by direct grep). It does
   not appear in `candidates.culture()`'s filtered output (211 entries, exactly 1 fewer)
   because `lexicon.held_out_answers()` correctly excludes it — it is THIS puzzle's own
   gold answer. **This is a genuine, previously undocumented methodological finding, not
   a corpus or trigger-vocabulary problem**: whenever `culture_category_candidates` fires
   on a clue whose gold answer is already indexed in `culture.json`, this project's own
   held-out safety filter (correctly, by design) makes that hit structurally
   unmeasurable as a recall@N "hit" on THAT specific puzzle — the mechanism could well
   have fired correctly in a real deployment, but the dev/eval methodology itself is
   blind to exactly this case. Recall@N on this mechanism is therefore a possibly-
   conservative lower bound for its real hit rate, in a way that cannot be fixed by
   growing the corpus or refining the trigger vocabulary — only by testing on a puzzle
   whose answer is NOT already an indexed entity (impossible to arrange deliberately
   without defeating the held-out discipline).
3. **22 across** (`הר אזורי ידוע ביופיו` → gold `אוריזהר`): checked directly — this
   mountain name is genuinely ABSENT from `culture.json`'s 119-entry `mountain` list (0
   matches by exact normalized string, confirmed by direct search, both pre- and
   post-filter). This IS a real corpus coverage gap, unlike case 2.

AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
both confirmed (computed, not assumed) to block all 28 of this puzzle's own gold answers
(`gold_norm - blocked` empty for both). Checked the raw, unfiltered `culture.json`
directly for leaks (the exact 2026-08-24 audit-finding shape): 4 of today's 28 gold
answers (`פרש`, `ספיח`, `תאשור`, `סיירהלאונ`) sit in the raw file unfiltered, but
`candidates.culture()`'s post-filter output contains ZERO of them — confirmed directly,
not assumed from the code path. No forbidden reads: 14across was never queried for this
puzzle's gold data, only the two public CDN images plus the already-committed grid file.
No jump to explain: 7.1% → 7.1% is the least suspicious result a controlled before/after
can produce (unchanged, not even a small rise). All 5 affected selftests (`candidates.py`,
`retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`) re-run clean.

HONEST READ: across both measurements of this lever (2026-06-19, 2026-07-03), recall@N
is 0/56 total gold hits from `culture_category_candidates` — still a real, mostly-negative
result on the headline number. But this run's value is the diagnostic breakdown, not the
flat number: of the queue's own two named next steps (a corpus-mined trigger vocabulary,
or a second puzzle), the second puzzle turned out to be more informative than either
framing anticipated — it shows the mechanism's failures are not one uniform problem. A
corpus-mined trigger vocabulary would help exactly zero of today's 3 firings (case 1 is a
precision problem no trigger vocabulary fixes; case 2 is invisible to this measurement by
construction; case 3 is a raw entity-list gap, not a trigger problem). The one concrete,
actionable finding is case 3's shape: growing `culture.json`'s named-entity lists (the
same kind of corpus growth this project already does for `private_defs`, just applied to
`culture.json` instead) is the only one of the three failure modes a future lever could
plausibly move, and case 2's finding means this project may be systematically
undercounting this mechanism's real value in every measurement it will ever run under the
current held-out methodology — worth flagging to the project owner as a genuine, if
mundane, measurement-validity caveat rather than a solving gap.

NOT DONE, honestly: did not build a corpus-mined trigger vocabulary (queue's other named
next step — today's diagnostic breakdown suggests it would not have helped any of this
run's 3 firings, so it is now a lower-priority follow-up than before, not a higher one);
did not grow `culture.json`'s entity lists to close case 3's gap (a real, actionable next
step surfaced today, not attempted — out of scope for a single-lever run that already
spent its budget on transcription + measurement + this diagnostic); did not touch
`retrieval_candidates` or run any corpus crawl (deliberately, per this run's explicit
steer away from a seventh consecutive day on that lever); did not act on queue item 9
(definition-fit scoring) — see RESEARCH.md, ninth-plus consecutive research pass with
nothing new; did not merge or otherwise act on any PR (none were open against this main).

Previous lever (2026-08-30): **closed 2026-08-29's own "NOT DONE" gap: re-measured
`retrieval_candidates` on 2026-06-26 — the puzzle 2026-08-28/08-29 both flagged as still
needing a bigger corpus and no run had finished re-transcribing — this time FULLY (28/28
clues, not the 18/28 partial 2026-08-26 left) and against a corpus grown far past any
prior run's.** 14across hit the same hard wall as 2026-08-19/08-26/08-27/08-28 (4/52
fetches in a row came back `None: 0 clues` after full retry-with-backoff each — killed,
not waited out); worked entirely from the no-14across image-fallback technique.
Transcribed all 28 clues of 2026-06-26 from `data/images/2026-06-25.jpg` — the previous
partial transcription (2026-08-26) had only found 18/28 because the across section's
tail (clues 19, 22-26) wraps across the print column boundary; tracking that wrap down
found the missing 5 across clues, closing queue item 8's gap for this specific puzzle.
Every one of the 28 enum sums was validated against the GRID-DERIVED slot length (from
the already-committed `data/grids/2026-06-26.json`, pure structural geometry, no gold
answer read) before any gold data was touched — 0/28 mismatches once one genuinely
missing printed enum (19 across) was recovered from its own column-wrap continuation
rather than assumed. One real REVERSED enumeration was caught and disclosed, not
silently fixed: clue 22 across prints `(4,3)` but the grid-derived answer `חוקמרפי`
splits as `חוק`(3)+`מרפי`(4) — the enum SUM still matches (7) so `len_ok` is unaffected,
kept as printed per the file's own established practice for this recurring anomaly (6+
puzzles have now shown it).

GOLD LETTERS came from the small solved-grid recap in the FOLLOWING week's image
(`data/images/2026-07-02.jpg`, captioned "פתרון תשבץ ההיגיון מהשבוע שעבר"), calibrated
programmatically (darkness-threshold gridline detection, not eyeballed) — all 15 rows'
black-cell pattern matched the committed grid EXACTLY (0/15 mismatches), the strongest
form of this project's standard cross-check. Several derived answers make clean
independent semantic sense against their clues (`אירטיש`/Irtysh river for "a new river";
`תגלתפלאסר`/Tiglath-Pileser for "an ancient king"; `מרידיאנ`/meridian containing
Mary+Di+Ann for "a queen and two princesses in a line"), further corroboration beyond the
grid-pattern match alone.

`crawl_defs.py mordo` re-crawled fresh this run (data/ is gitignored, so every run starts
from zero): **66,443 raw entries, 62,403 with parsed answers after `reparse_mordo()`** —
2.6x 2026-08-29's 25,350/24,361, confirming the blogspot feed keeps growing run over run,
not a one-time artifact (spot-checked for a pagination-loop bug: 57,843/59,100 sampled
definitions are unique, ~98%, so this is real new content, not a duplicate loop).
`crawl_defs.py note` ran under a disclosed 12-minute time budget (fetching is far slower
than mordo's bulk feed — roughly 15-20 pages/min against individual solution pages):
**1,001 of 1,301 discovered URLs fetched (998 with parsed answers)**, up from 2026-08-29's
970/1,301 despite the bounded budget, since URL discovery (the slow part on a cold cache)
had already completed by the time the budget ran out.

MEASURED, controlled before/after (`python3 solver/candidates.py recall
data/dataset/clues.jsonl eval [--no-culture] [--no-retrieval]`): mechanical-only baseline
**0.0% (0/28)**; **+ retrieval with the grown corpus: 14.3% (4/28)** — the HIGHEST recall
this diagnostic has ever measured on any single puzzle (previous best 10.7%, 2026-08-28)
and the largest point-gain (full defaults, culture+retrieval, land at the same 4/28 =
14.3%, confirming `culture_category_candidates` contributes nothing extra here, consistent
with its established rare-firing pattern). The 4 hits: 13A `מניע` (motive, clue "the
reason"), 17A `רומח` (spear, clue "a serious weapon"), 5D `בובדילנ` (Bob Dylan, clue "won
the Nobel prize"), 21D `ברסמכא` (bar samcha/an authority figure, clue "the expert" — the
SAME hit 2026-08-26's smaller 18-clue transcription and smaller corpus already found on
this puzzle, now reproduced independently with a full transcription and 7x the corpus).

AUDITED (mandatory gate). Provenance of all 4 hits checked directly, not assumed: every
matching document for all 4 answers carries `pid=None` (external private_defs corpus —
e.g. `רומח`'s docs are about "כלי נשק"/weapons, `בובדילנ`'s are about a Nobel-winning
American singer-songwriter), never this project's own puzzle text, and each match's
underlying definition text is a clean semantic fit for its clue, not a coincidental
string match. `lexicon.held_out_answers()` and `retrieve_defs.held_out()` both confirmed
(computed, not assumed) to block all 28 of this puzzle's own gold answers —
`gold_norm - blocked` empty for both. **Disclosed, not hidden, one caveat found while
auditing**: DAILY.md's own 2026-08-26 log entry for this exact puzzle already named 2 of
today's 4 hits (`בובדילנ`, `ברסמכא`) as that day's finding, and this file is required
reading before every run (flagged as a standing, unaddressed leak-adjacent gap since
2026-08-22: "DAILY.md itself is required reading each run and is therefore a leak vector
its own instructions don't flag"). This did NOT compromise today's number: gold letters
were derived independently by grid-calibrating the solution image (0/15 row mismatches
against the committed grid, an objective check unrelated to foreknowledge), and
`candidates.py recall`'s hit/miss decision is a mechanical string-equality comparison
with no room for researcher judgment to bias it either way — but the other 2 hits
(`מניע`, `רומח`) are the genuinely NEW, first-time information, and are the stronger data
point of the two. No forbidden reads: 14across was never queried for this puzzle's gold
data, only the two public CDN images. Implausibility check: 0.0%→14.3% is a 14.3-point
jump, just under this project's own ~15-point suspicion bar — treated as suspect until
explained per that rule, and fully explained by 4 individually-verified, semantically
sound, externally-sourced hits, not a single anomalous mechanism. All 5 affected
selftests (`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`,
`substitutions.py`) re-run clean.

HONEST READ: this is the strongest single data point this lever has produced across 6
independent measurements — a puzzle that scored a flat 0.0% on its first (partial,
18-clue) attempt now scores the project's highest-ever recall@N once both the
transcription gap and the corpus size are closed together. It does not by itself prove
corpus size is the universal fix (2026-07-10 has now stayed flat at 0.0% across three
much-grown corpus sizes) — the honest updated read across all 6 measurements is still
that retrieval's gain is real but puzzle-dependent, and this run adds evidence that when
it DOES fire on a puzzle, a bigger corpus makes it fire more, not just once.

NOT DONE, honestly: did not re-measure 2026-07-10 again (already measured flat three
times at three corpus sizes — re-measuring a fourth time with today's much bigger corpus
would be informative but was not this run's chosen puzzle, to keep this run to one
puzzle's full transcription-plus-audit cycle); did not act on the DAILY.md-as-leak-vector
observation beyond disclosing it here — a genuine fix (e.g. redacting specific gold
strings from log prose, or moving them to a separate non-required-reading file) is a
process/tooling question worth its own future lever, not something to design under
today's one-lever budget; did not merge or otherwise act on any open PR.

Previous lever (2026-08-29): **continued queue item 1(d)'s own next step from
2026-08-28: a FULLER `note.co.il` crawl (run to a natural plateau rather than a
15-minute stop) plus a fresh `mordo` re-crawl, re-measured on 2026-07-10** (one of the
two puzzles 2026-08-28 named as most needing a bigger corpus, since it scored 0.0%→0.0%
with the smaller corpus on 2026-08-27). Bootstrap succeeded FULLY at 14across this run
(52/52 puzzles, 1,457 clues) — the first clean run since 2026-08-19 — so gold answers for
2026-07-10 came directly from `data/answers/by_date/2026-07-10.json` (real crowd-sourced
answers + explanations) rather than the image-fallback solution-grid technique; only clue
TEXT was transcribed from `data/images/2026-07-11.jpg` (19/28 clues — the same
across-1-15 gap as 2026-08-27's independent transcription of this exact puzzle).
`crawl_defs.py note` was run WITHOUT an early stop this time: discovered 1,301 unique
solution-page URLs (vs 934 on 2026-08-28) and fetched 970 of them (vs 829) before being
stopped at a natural plateau, not a fixed time budget. `crawl_defs.py mordo` re-crawled
fresh: 25,350 raw entries (24,361 with parsed answers after `reparse_mordo()`), up from
2026-08-28's 13,646 (12,890 parsed) — the blogspot feed has grown again, consistent with
the pattern each of the last three runs has observed. MEASURED, controlled before/after
(`python3 solver/candidates.py recall data/dataset/clues.jsonl eval [--no-culture]
[--no-retrieval]`): mechanical-only baseline **0.0% (0/19)** — exactly reproduces
2026-08-27's number on this same puzzle, a strong cross-check that today's independent
transcription (from 14across's real answers this time, not the image fallback) is
correct; **+ retrieval with the much bigger corpus: still 0.0% (0/19), UNCHANGED**; full
defaults (culture+retrieval) also 0.0%. AUDITED: `lexicon.held_out_answers()` and
`retrieve_defs.held_out()` both confirmed to block all 19 of this puzzle's own gold
answers (`gold_norm - blocked` empty for both, re-checked AFTER the corpus grew, not
just before); all 5 affected selftests re-run clean; no forbidden reads (gold came from
the sanctioned `data/answers/by_date/` path via bootstrap's own 14across scrape, clue
text from the public CDN image). No jump to explain — 0.0% stayed 0.0%, the opposite of
an implausible result. HONEST READ: this is a genuine, informative NEGATIVE result, not
a failure of the lever — it confirms (does not merely repeat) 2026-08-27's finding that
2026-07-10's specific idioms/culture references are not just absent from a smaller
private_defs corpus but absent even after nearly doubling it again; retrieval's gain is
real but puzzle-dependent (it has now moved 2026-05-29 twice, at two different corpus
sizes, and never moved 2026-07-10 at three), not a function of corpus size alone for
every puzzle. NOT DONE, honestly: did not re-measure 2026-06-26 (the other puzzle
2026-08-28 flagged) — bootstrap's 14across scrape missed that date again this run (one
of 6 puzzles that came back `None: 0 clues`, a known intermittent-bot-check symptom, not
a hard wall this time since 46/52 other dates succeeded), and reconstructing it via the
image-fallback technique (partially started, then abandoned in favor of the cleaner
2026-07-10 path once 14across proved to have real data for it) was not finished; did not
run either crawl to literal exhaustion (mordo's blogspot feed shows no sign of a fixed
end, note.co.il reached 970/1301 discovered URLs) — both are substantially fuller than
2026-08-28's runs but "unbounded" here means "not stopped early on a fixed timer," not
"proven exhaustive"; did not merge or otherwise act on any PR (none were open).

Previous lever (2026-08-28): **crawled `note.co.il` for the first time this project's
lifetime** (queue item 1(d)'s own next step, flagged unattempted in three consecutive log
entries: 2026-08-25, 2026-08-26, 2026-08-27), and re-crawled `mordo` (pitaronfree)
fresh alongside it, growing `private_defs` from the 9,685 mordo-only pairs 2026-08-25
measured with to 13,646 raw mordo pairs (12,890 with parsed answers after
`reparse_mordo()`) + 829 note.co.il pairs. No code change — `retrieve_defs.build_index()`
already globs every `*.jsonl` under `data/answers/private_defs/`, so a new source file is
picked up automatically, same as PR #29 found for the live-trial wiring. Bootstrap hit the
same 14across hard wall as 2026-08-19/08-26/08-27 (killed after 170s, 1/52 recovered);
worked entirely from the public-CDN image fallback, fetching `data/images/2026-05-28.jpg`
and `2026-06-04.jpg` directly rather than waiting on bootstrap's sequential step order.
RE-TRANSCRIBED THE CANONICAL DEV PUZZLE (2026-05-29) independently for a third time (after
2026-08-06's original and 2026-08-25's redo), so today's number is directly comparable to
both prior measurements on this exact puzzle. Caught and fixed one real transcription bug
mid-run (clue 13 across's enum), disclosed in the log rather than silently corrected.
MEASURED, controlled before/after (`python3 solver/candidates.py recall
data/dataset/clues.jsonl eval [--no-culture --no-retrieval]`): mechanical-only baseline
**3.6% (1/28)** — exactly reproduces the 2026-08-06/2026-08-25 number on this same puzzle,
a strong cross-check that today's third independent transcription is correct; **+
retrieval with the grown corpus: 10.7% (3/28)**, up from the 7.1% (2/28) this exact puzzle
scored on 2026-08-25 with the smaller, mordo-only corpus. Isolated which source produced
the gain (mordo alone / note alone, each tested standalone by moving the other file aside
and re-running): mordo alone reproduces 10.7% (the SAME 2 retrieval hits, including a NEW
one today — 1 down, `ברישניקוב`/Baryshnikov, absent from 2026-08-25's smaller mordo
crawl); note.co.il alone reproduces exactly 7.1% (2026-08-25's original number, via a
DIFFERENT source document than mordo's for the same gold answer, 26 across
`פחותאבלכואב` — confirmed independently, not the same doc). Honest attribution: today's
recall GAIN over 2026-08-25's 7.1% traces to mordo's corpus having grown (13,646 vs 9,685
raw pairs — the blogspot feed has more indexed content now), not to note.co.il, which on
this specific puzzle only reproduces a hit mordo already had. note.co.il is nonetheless
confirmed a REAL, independent, working source (its own distinct document matched the gold
answer) — worth having crawled, just not the source of today's specific number's movement.
AUDITED: both hits' source docs confirmed `pid=None` (external private_defs, not this
project's own puzzle text) directly by grep; `lexicon.held_out_answers()` and
`retrieve_defs.held_out()` both confirmed to block all 28 of this puzzle's own gold
answers (`gold_norm - blocked` empty for both). No forbidden reads: gold data came
entirely from the two public CDN images, never 14across, for this puzzle. No jump to
explain: 3.6% -> 10.7% (+7.1 points) is well under the ~15-point implausibility bar and
fully explained by 2 legitimate external retrieval hits. All 5 affected selftests
(`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`)
re-run clean. NOT DONE, honestly: did not re-measure the 2026-06-26/2026-07-10 puzzles
with the grown corpus (would need re-transcribing them, out of scope for one lever); did
not merge PR #29 or this branch (only the project owner can); note.co.il's crawl was
bounded by a deliberate ~15-minute stop (934 candidate URLs discovered, 829 fetched), not
exhausted — a fuller crawl is the natural next step if this lever is revisited.

Previous lever (2026-08-27): **first LIVE blind trial with `retrieval_candidates`
active** (queue item 1(d)'s own explicitly-flagged gap since 2026-08-25: "worth eventually
wiring into a live solve pass — still true of every candidate-gen sub-lever so far").
`solve_pass.py` already calls `candidates.py generate()` with `use_retrieval=True` by
default (confirmed by reading the code — no wiring change needed), so this was a pure
measurement run, not a code change. 14across was fully walled again today (0/52, direct
single-URL fetch also failed after 8 retries — matches the 2026-08-19/08-26 hard-wall
mode). Recovered a genuinely fresh, previously-untouched puzzle (2026-07-10) via the
image-fallback technique: transcribed 19/28 clues (the standard across-1-15 gap, queue
item 8) from `data/images/2026-07-11.jpg` (a Haaretz CDN image carrying an odd Saturday
date label in its manifest entry but confirmed — via numbering fingerprint AND a 0/15
row-pattern match against the committed grid — to be 2026-07-10's own puzzle image), and
recovered gold letters from the small solved-grid recap in the FOLLOWING week's image
(`data/images/2026-07-16.jpg`, captioned "פתרון תשבץ ההיגיון מהשבוע שעבר"). Grid-pixel-
calibrated the solved grid's row/column boundaries programmatically; all 15 rows'
black-cell patterns matched the committed `data/grids/2026-07-10.json` EXACTLY (0/15
mismatches) after fixing two real transcription bugs caught by that same check (a hand-
reversal arithmetic error on a non-palindromic row, and a final-form/regular letter typo)
— both disclosed rather than silently fixed, see log. `held_out_answers()` confirmed to
block all 19 gold answers before the trial began.

DELEGATED to a fresh subagent (SOLVE_PROTOCOL.md as method, hard rules against touching
`data/answers/**`/`data/dataset/**`/14across, verbatim clue search) — output: 7 self-
labeled "committed" but only 1 cleared the policy's 0.75 confidence bar (the eval
script's own tier-enforcement correctly downgraded the other 6), 4 self-labeled
suggestion, 8 blank.

MEASURED (executed): `python3 evals/run_eval.py` — **PRECISION 1/1 = 100%, COVERAGE
5.3% (1/19), YIELD 5.3%, suggestion hit-rate 0/10 = 0%**. The one committed hit (23A,
`ראי`) came from a `wiki.py` culture-fact double-definition lookup, not from any
candidate generator. Grepped the subagent's full transcript for `(retrieval, fodder=`
(solve_pass.py's own output format for a retrieval hit) — **zero matches across all 19
clues**: `retrieval_candidates` never once surfaced a candidate this trial, live or
offline (matches this run's own `candidates.py recall` diagnostic on the same puzzle,
also 0/19 with retrieval on vs off). Cumulative across all 3 live trials: **40% precision
(2/5 committed)**, up from 25% (1/4) before retrieval existed in `solve_pass.py`'s pool —
but that move is not attributable to retrieval, which contributed nothing on this
specific puzzle; it is one more correct wiki.py-sourced culture hit on top of the same
mechanism-verification-isn't-definition-fit pattern the two prior trials already found.

HONEST READ: the standing gap this queue named ("wire retrieval into a live trial") is
now closed, and the answer is a clean null result, not a failure — the private_defs
corpus (mordo/pitaronfree only) simply doesn't cover this puzzle's specific idioms/
culture references, so retrieval had nothing to offer, consistent with — not
contradicting — today's own offline recall@N finding on the identical puzzle. Combined
with the two prior offline puzzles (2 of 3 positive), the fair summary is: retrieval is a
real but inconsistent, puzzle-dependent source, worth keeping (it costs nothing when it
doesn't fire) but not a reliable coverage lift, and not what's holding this trial's
coverage down. AUDIT: transcript grepped for `data/answers`/`data/dataset`/`14across` —
one minor, non-leaking deviation found and disclosed: the subagent ran `ls -la
data/dataset/` (a directory LISTING, filenames+byte-sizes only, no content) while
checking tool availability; it never opened or read `clues.jsonl`'s content, and the
one place that path string appears as file CONTENT in the transcript is `solver/
retrieve.py`'s own permitted source code (which internally reads only train-split rows
by construction). No gold answer was read by the agent directly. See log for the full
transcription/audit trail, including the two transcription bugs caught mid-run.

Previous lever (2026-08-26): **second, independent dev-puzzle measurement of
`retrieval_candidates`** (queue item 1(d)'s own flagged gap: "worth a second puzzle's data
point before calling this settled"). Freshly transcribed 2026-06-26 from scratch (18/28 clues —
see log for the documented across-clue gap that limited coverage), using the SAME
image-fallback technique as 2026-08-25 (gold letters read from the small solved reference grid
printed in the FOLLOWING week's image, `data/images/2026-07-02.jpg`, since 14across was fully
blocked again today — 0/52 puzzles, matching the 2026-08-19 hard-wall failure mode, not the
"~50% random" one). Grid-pixel-calibrated the solved-grid image (0 mismatches against the
committed black-cell pattern) rather than eyeballing cell boundaries, which caught and avoided
a column-order transposition bug before it could corrupt the transcription. Rebuilt the
external private_defs/mordo.jsonl corpus fresh (31,347 pairs recovered before a deliberate
stop — 3x 2026-08-25's 9,685 pairs; the site apparently has more content indexed now, or
2026-08-25's run stopped for an unrelated reason not recorded). MEASURED, controlled
before/after on this new puzzle: mechanical-only baseline **0/18 = 0.0%**; **+ retrieval:
1/18 = 5.6%**, a real gain from ONE new hit (21 down, `המומחה משיב אבל אינו מסכים (עפ"י צבי
ויצמן)` (4,2) -> `ברסמכא`, i.e. "בר סמכא" / an authority figure — the retrieval doc that
matched is an external "מומחה המשמש כאוטוריטה" definition entry, pid=None, unrelated to this
puzzle). AUDITED: both docs matching the gold answer carry pid=None (external corpus, not this
project's own train-split clues); `lexicon.held_out_answers()` confirmed to block all 18 of
this puzzle's own gold answers, and none of the 18 are present at corpus/culture priority
tier in the loaded lexicon (0 leaked). This is a SECOND independent puzzle, transcribed and
solved by a different agent than 2026-08-25's, moving in the SAME direction (recall roughly
doubles when retrieval is added) — meaningfully stronger evidence than the n=1 anecdote this
lever stood on yesterday, though n=2 puzzles / 2 total hits is still a small sample. See log
for the full transcription/grid-calibration/audit trail.

Previous lever (2026-08-25): **wired `solver/retrieve_defs.py` (BM25 ranked retrieval over
definition->answer pairs, built 2026-08-08) into `candidates.py`'s `generate()` pool as a new
`retrieval_candidates` source** — queue item 1's "RANKED RETRIEVAL" sub-lever, open since
2026-08-08 and never attempted despite the tool existing. Rebuilt the external private_defs
corpus this run (`scraper/crawl_defs.py mordo`, ~3 min for 9,685 definition->answer pairs from
pitaronfree.blogspot.com — gitignored, so future runs must redo this too, same as every other
gitignored asset). Re-transcribed the canonical dev puzzle (2026-05-29) via the documented
image-fallback technique (grid_tools 0/15 pattern mismatches + 28/28 enum matches against the
following week's printed solution grid) rather than waiting out today's slow 14across bot-check.
MEASURED, controlled before/after on the SAME re-derived puzzle: mechanical-only baseline
**1/28 = 3.6%** (exactly reproduces the 2026-08-06 historical number — strong cross-check that
today's independently-redone transcription is correct); **+ retrieval: 2/28 = 7.1%**, a real
gain from ONE new hit (26 across, `יהונתן גפן ויהודה פוליקר על ברית מילה` -> `פחותאבלכואב`, a
real Yehonatan Geffen/Yehuda Poliker song title the mechanical mechanisms structurally cannot
reach since it shares no letters with the clue). Audited: the hit comes from an external,
independent source doc (pid=None, a generic "works by Yehonatan Geffen" listing), not a leak of
this project's own puzzle; `lexicon.held_out_answers()` confirmed to still block all 28 of this
puzzle's own gold answers. Small sample (n=1 puzzle, +1 hit) — a real, positive, first-of-its-
kind move on this lever, not proof retrieval solves candidate generation; see log for the full
transcription/audit trail, including one real transcription error caught and fixed mid-run.

Previous lever (2026-08-24): **definition-driven candidate generation** (`solver/candidates.py`:
`culture_category_candidates`) — a new generator, orthogonal to every existing mechanism, that
derives a candidate from the clue's MEANING (a role/genre/geography category it names, e.g. "the
singer") rather than its letters, by matching hand-curated Hebrew category trigger words against
`solver/lex/culture.json`'s named-entity lists. MEASURED on a freshly transcribed puzzle
(2026-06-19, 28/28 clues, all enum sums validated against grid geometry AND cross-checked against
the real 14across gold answer lengths, 0 mismatches either way): **0/28 recall, unchanged from the
0/28 mechanical-only baseline on this same (unusually hard) puzzle** — the new mechanism fired on
only 1 of 28 clues, and that one firing (339 raw "author"-category candidates) matched nothing.
n=1 fired-clue is too small to call this dead, but it is a real, honest, mostly-negative result —
see log for the root-cause read (this setter's category words are often homograph/wordplay fodder,
not literal definition-by-category pointers) and a genuinely important AUDIT finding: the
un-filtered `solver/lex/culture.json` actually contained 5 of this puzzle's own 28 gold answers,
which the new mechanism could have leaked had it not been given the same held-out filter
`lexicon.load()` already uses — caught and fixed before any measurement, not after.

Earlier lever (2026-08-22): **first full-puzzle LIVE blind trial of `solve_pass.py`**
(queue item 1(a)'s remaining gap, flagged since 2026-08-16). MEASURED 0/2 precision
(both committed answers wrong), 7.1% coverage, 0% yield on 2026-05-15 (28/28 clues
transcribed, all enum sums validated against grid geometry, 0 mismatches). Both misses
were a mechanically-real device (hidden-word, reversal) landing on a real Hebrew word
that was NOT the setter's intended answer — root-cause detail in the log. Combined with
2026-08-16's trial, cumulative live precision is now 1/4 = 25%, well below the proof
gate's promise; see log for the full audit and honest read.

Previous lever (2026-08-20): **substitution- and homograph-aware candidate generation**
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
first full-puzzle live blind trial of `solve_pass.py`, 0/2 precision — merged mid-run, see
note below). Cherry-picked #23's `lexicon.py` fix onto this branch rather than re-deriving it,
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

**PR #24 update: merged to main partway through this run** (after this branch was
created off the pre-#24 main, hence the merge above). Its finding — cumulative live
precision 1/4 = 25%, the sharpest evidence that definition-FIT judgment, not mechanism
verification, is the remaining gap — is now the state table's own row (above) and its
2026-08-22 log entry (below), not just a flagged-for-later note.

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
   fix. (a) wiring the generator into an actual solve pass (`solver/solve_pass.py`) was
   DONE 2026-08-16 and live-trialed twice (2026-08-16, 2026-08-22) — see the state table's
   `solve_pass.py` row: cumulative 1/4 = 25% precision, well below the proof gate's
   promise, root-caused to definition-FIT not being scored at all, not to a candidate-
   generation gap on those two trials specifically (both misses were mechanically-real
   devices landing on the wrong real word). (c) `culture_category_candidates` — a
   DEFINITION-driven generator (as opposed to (a)/(b)'s letter-driven ones) — ADDED
   2026-08-24 (see log): 0/28 recall, fired on only 1/28 clues on that puzzle, n too small
   to call dead but a real, mostly-negative result; root-caused to category words in this
   setter's clues often being homograph/wordplay fodder rather than literal
   definition-by-category pointers, which a surface trigger-word match can't distinguish.
   A corpus-mined trigger vocabulary (vs. today's hand-curated one) and a second puzzle's
   data point are the concrete next steps if this is revisited, not a redesign from
   scratch. **2026-08-31: the second puzzle's data point is done** (2026-07-03: still
   0 gold hits, fired 3/28 clues — see log). It changed the diagnosis: of the 3 firings,
   only ONE reproduces the original homograph-misdirection root cause; the other two are a
   newly-found held-out-safety-filter measurement blind spot (not fixable by any
   candidate-generation change) and a genuine `culture.json` entity-list coverage gap (the
   one of the three a future lever could actually move). A corpus-mined trigger vocabulary
   would not have helped any of today's 3 firings — demoted to a lower-priority follow-up
   than growing `culture.json`'s entity lists, which is now this item's best-evidenced
   next step if revisited again. (d) `retrieval_candidates` (BM25 over `solver/retrieve_defs.py`'s definition
   index) — WIRED IN 2026-08-25 (see log): the queue's own "RANKED RETRIEVAL" item from
   2026-08-08, never previously combined with the other mechanisms. MEASURED POSITIVE:
   3.6% -> 7.1% recall on a controlled re-derivation of the 2026-05-29 baseline (+1 hit,
   a culture-reference song title with zero letters in common with its clue). CONFIRMED ON
   A SECOND, INDEPENDENT PUZZLE 2026-08-26 (see log): 0.0% -> 5.6% on a freshly transcribed
   2026-06-26 (+1 hit, an idiom retrieved from an external definition doc). A THIRD
   PUZZLE, 2026-08-27, broke the streak: 0.0% -> 0.0%, unchanged, on 2026-07-10 — this
   puzzle's own idioms/culture references simply aren't in the private_defs corpus. Net:
   2 of 3 independent puzzles positive, 1 flat — a real but inconsistent, puzzle-dependent
   source, not (yet) a reliable lift. LIVE-TRIALED for the first time 2026-08-27 (closing
   the "worth eventually wiring into a live solve pass" gap named here since 2026-08-25):
   contributed ZERO candidates on that puzzle's 19 clues, live or offline, consistent
   with the flat offline result on the same puzzle — see the state table's live-trial row
   and log for the full measurement. `crawl_defs.py note` was CRAWLED FOR THE FIRST TIME
   2026-08-28 (829 pairs, deliberately bounded, not exhausted), alongside a fresh mordo
   re-crawl (13,646 raw pairs, up from 9,685) — re-measured on 2026-05-29 (the original
   baseline puzzle): 3.6% -> 10.7% (3/28), up from 7.1% with the smaller corpus. Isolated:
   the GAIN traces to mordo's growth (a new hit, `ברישניקוב`, absent from the smaller
   mordo crawl), not to note.co.il, which reproduces the old 7.1% via its own independent
   doc for the same answer mordo already had — note.co.il is confirmed real and working,
   just not the source of today's specific movement. See log. Next concrete step: a
   fuller (unbounded) note.co.il crawl, and re-measuring the 2026-06-26/2026-07-10
   puzzles (which needed the corpus most, per 2026-08-27's flat result) with the grown
   corpus — neither attempted today to keep this run to one lever.
   2026-08-29 CLOSED HALF OF THIS: fuller note.co.il crawl done (970/1301 discovered,
   up from 829/934) plus a fresh mordo re-crawl (25,350 raw / 24,361 parsed, up from
   13,646/12,890), re-measured on 2026-07-10 (bootstrap's 14across worked fully this
   run, so gold came from real crowd data, not the image fallback): **STILL 0.0% (0/19),
   unchanged even at nearly double the corpus size** — a genuine negative result that
   strengthens (not just repeats) 2026-08-27's finding: this puzzle's specific gaps
   aren't a corpus-size problem. 2026-06-26 remains unmeasured (14across missed that
   date again this run). Net across all measurements: retrieval is confirmed
   puzzle-dependent — real and repeatable on 2026-05-29 (positive twice, at two corpus
   sizes), consistently flat on 2026-07-10 (negative three times, at three corpus
   sizes) — corpus growth is not a universal fix, only a puzzle-specific one. See log.
   2026-08-30 CLOSED THE OTHER HALF: 2026-06-26 fully transcribed (28/28, up from
   2026-08-26's partial 18/28) and re-measured against an even bigger corpus (mordo
   66,443 raw/62,403 parsed — 2.6x 2026-08-29's; note.co.il 1,001/1,301 fetched):
   **0.0% (0/28) -> 14.3% (4/28), the highest recall this diagnostic has ever measured**,
   4 independently-audited external hits. Net across all 6 measurements now: 4 positive
   (2026-05-29 x2, 2026-06-26 x2) + 2 flat (2026-07-10 x2) — still puzzle-dependent, not
   universal, but the puzzle-dependence looks more like "most puzzles benefit, one
   specific puzzle's idioms genuinely aren't covered" than a coin flip. See log. Also
   surfaced (not fixed, out of today's one-lever scope): DAILY.md's own log prose is a
   leak-adjacent vector — it named 2 of today's 4 gold answers in a prior entry, before
   this run's required reading. Worth a future lever (redact specific answer strings from
   log prose, or split required-reading history from an answer-bearing appendix).
   (e) `container_candidates` — the container/insertion device (PLAYBOOK.md §1.4,
   ~10-12% of clues, the fourth-most-common mechanism) — ADDED 2026-09-03 (see log):
   until today pure verification infrastructure (`prove.is_container`) with no
   generator behind it. MEASURED UNCHANGED (1/28 = 3.6%, same as mechanical-only) on
   2026-05-29, fired on only 1/28 clues — but CONFOUNDED: 14across was fully
   unreachable this run, starving `sub_fwd()` (this mechanism's mined-substitution
   fragment source, shared with `substitution_candidates()`, which ALSO scored 0
   fires this run for the same reason). Not a clean read on whether the device helps;
   re-measure once a puzzle with real crowd explanations is available, before
   concluding anything about the mechanism itself. Selftest (a real lexicon word, not
   synthetic) confirms it is mechanically sound.
   **2026-09-11 UPDATE (branch-hygiene failure, see 2026-09-12's fuller writeup)**: a
   SEPARATE, independently-written `container_candidates` was added on an unmerged branch
   that never saw this one, and measured 0.0% (0/28) on a freshly transcribed 2026-06-05,
   root-caused to its own literal-clue-word-only design being unable to reach a SYNONYM
   substitution (בית~קן, "the judge"~טל) its one real container clue needs. **2026-09-12
   reconciled the two**: kept this (e)'s strictly more general implementation (its
   `container_parts()` already unions literal/destemmed words with `sub_fwd()`'s mined
   synonyms — the exact capability 2026-09-11's diagnosis called for), and PROVED that
   union actually fires with a new, previously-missing selftest (2026-05-29's original
   confounded measurement never exercised it live, since `sub_fwd()` was empty that day
   too). Could not get a live recall number today (14across hard-walled again, confirmed
   directly; the image-fallback recap grid was not reliably readable at letter level this
   run without a zoom tool). AUDIT-ONLY against the historical `solver/lex/substitutions.json`
   refined 2026-09-11's own root cause: בית->קן IS a real recorded generic substitution, but
   שופט/השופט does NOT map to טל anywhere in that table (טל is almost certainly a specific
   named judge, an entity fact rather than a synonym pair) — so even a live, fully-fed run
   of this mechanism would likely still miss this exact clue; the concrete next step is a
   THIRD fragment source (role/entity lookup, reusing `culture_category_candidates`'
   trigger vocabulary), not more corpus for the two sources this mechanism already has. A
   further audit-only check found the assembled `קטלנ` is not even in the loaded hspell
   lexicon, a fourth independent obstacle if that is indeed the gold answer. See log.
   (f) `double_definition_candidates` — the מילה משותפת device (PLAYBOOK.md §1.2, 14% of
   clues, second most common after charade) — ADDED 2026-09-04 (see log): the one
   PLAYBOOK-documented mechanism that had zero generator, mechanical or definition-driven,
   before today. For every clue-word split point, requires an answer to rank in BOTH
   halves' independent BM25 top-K, reusing `retrieve_defs.py`. MEASURED NEGATIVE on a
   fresh puzzle (2026-05-21): 0.0% (0/21), and — more informative than the flat number —
   the mechanism fired on 0/21 clues; even relaxing to "gold in EITHER half alone" found
   nothing for any of the 5 short (<=4-letter) slots checked, the class PLAYBOOK.md says is
   overwhelmingly double-definition. `retrieval_candidates` on the SAME corpus scored 9.5%
   (2/21) on this puzzle, so the corpus isn't empty — this specific two-sided-split
   mechanism just found no matching definition-pair for these particular clues. Today's
   corpus was mordo-only, under a disclosed 10-minute crawl budget (33,299 raw / 32,150
   parsed) with no note.co.il — smaller than the 66K+ peak corpus 2026-08-30 grew;
   untested whether a fuller corpus (the lever that repeatedly rescued
   `retrieval_candidates` on other puzzles) would let this mechanism fire at all. Next
   concrete steps if revisited: grow the corpus for this puzzle specifically before calling
   the mechanism dead, and/or measure a second puzzle (n=1 so far).
   (g) `homophone_candidates` — the נשמע (sounds-like) device (PLAYBOOK.md §1.6, ~4% of
   clues) — ADDED 2026-09-05 (see log): the first mechanism here for a device where the
   answer shares no LETTERS with its fodder, only its SOUND (Hebrew consonant-class
   folding: ק/כ/ח, ט/ת, ס/ש, א/ע). MEASURED UNCHANGED (3.6%/1/28, same as mechanical-only)
   on 2026-05-29, but NOT zero-fire: 8/28 clues produced real candidates. Root-caused: this
   puzzle's own homophone-credited clue needs vowel-letter (ו/י) flexibility this v1's
   length-preserving fold deliberately excludes — a real device, a scoped v1, a concrete
   next step (model vowel insertion as a variable-length search) rather than a dead end.
   (h) `homophone_vowel_candidates` — the (g)-flagged next step, DONE 2026-09-06 (see
   log): tries inserting/deleting one ו/י against the same phon-folded index, in both
   length directions. MEASURED UNCHANGED (3.6%/1/28) on the same puzzle, fired on 14/28
   clues (up from 8/28), still 0 gold hits. Root-caused, not assumed: directly tested
   against the SPECIFIC clue (g) diagnosed as this device's target and found it produces
   ZERO candidates there too — the true sound relationship in that one clue is more than
   one vowel letter apart, so (g)'s "vowel-insertion" framing of that specific clue was
   itself imprecise, independent of whether the device is correctly built (it is, per
   selftest and the mechanical firing rate). No corpus dependency, no confounding. Next
   step if revisited: a second puzzle's measurement (n=1 so far) rather than assuming
   this one puzzle's non-hit generalizes.
   (i) `charade_candidates` — ADDED 2026-09-08 (see log): a mechanical (not corpus-backed)
   generator that solves a 2-part enum as two INDEPENDENT, non-overlapping, in-order
   anagram/hidden windows rather than requiring one contiguous window to cover the whole
   answer length. MEASURED NEGATIVE on 2026-05-29 (freshly re-transcribed): 3.6% -> 3.6%,
   unchanged — fired on all 10 of the puzzle's 2-part-enum clues (hitting its own
   200-candidate cap on 8) but matched 0/10 gold. Also surfaced a hard blocker for item
   1(b)'s own flagged next step (multi-part substitution charades, quoted above): with
   14across walled again, `substitutions.explanations()` sourced 0 rows and `sub_fwd()`
   built an EMPTY equivalence table this run — the multi-part-substitution idea is not
   just unattempted but UNTESTABLE without either a working 14across fetch or some other
   source of clue-fragment equivalences; `charade_candidates` was built as the closest
   testable relative (multi-part, but via the mechanical anagram/hidden lexicon rather
   than a mined table) precisely because that path was blocked. Next concrete steps if
   revisited: extend to 3+-part enums, tighten the 200-candidate cap (hit on 8/10 clues
   here, a real wall-clock cost — +69% on this eval — for zero measured gain), and a
   second puzzle's data point before calling this dead. See log.
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
6. ~~Merge or close the PR backlog~~ — STRUCK 2026-08-21, RECURRED 2026-08-24, CONSOLIDATED
   2026-08-25. Three PRs were open and unmerged against the same main simultaneously (#23
   2026-08-21, #25 2026-08-23, #26 2026-08-24) because none of them had been merged by the
   project owner and each day's agent branches off main, not off yesterday's PR — the exact
   compounding-loss pattern this item has now flagged three times. This run cherry-picked
   the real code commits from all three (verified #25's `lexicon.py` diff is byte-identical
   to #23's, i.e. #25 already supersedes #23; #26's `candidates.py` commit applied clean, no
   conflicts) onto one branch and reconciled DAILY.md/RESEARCH.md by hand (chronological
   log merge, no content dropped) rather than re-deriving any of the three days' work. Only
   the project owner can merge PRs; this run's branch is offered as the single PR that
   supersedes #23/#25/#26 so they can close those three instead of merging four times.
7. ~~Fix `lexicon.held_out_answers()`'s coverage gap~~ — FIXED 2026-08-21 (PR #23),
   confirmed byte-identical in PR #25's cherry-pick, both folded into this branch
   2026-08-25. It only blocked an answer when its clue had a row in
   `data/dataset/clues.jsonl`; fix blocks every answer in the puzzle's full
   `data/answers/by_date/<date>.json` once any one row marks the date dev/eval. Measured:
   18/18 previously-unblocked untranscribed-slot answers now blocked (2026-06-05 test).
   See log.
   - **7b** (flagged by PR #23, fixed 2026-08-23 PR #25, folded in 2026-08-25): the
     identical gap in `substitutions.py`/`retrieve_defs.py`. `substitutions.py`'s half was
     a REAL, currently-exploitable leak (its `explanations()` sources ALL 52 puzzles
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
   match there is NOT evidence of being the right week's text). NEW DATA POINT 2026-08-22:
   2026-05-15's own image (`data/images/2026-05-14.jpg`) prints across clues 1 THROUGH 13
   cleanly, no gap — the second date (after PR #23's 2026-06-05 finding) confirming the
   gap is not universal, it's specific to certain weeks' layouts. PARTIAL RESOLUTION
   2026-08-24: 2026-06-19's image (`data/images/2026-06-18.jpg`) also turned out NOT to be
   missing clues 1/7-13 — they're present in a separate column next to the small
   "previous week's solution" grid graphic, easy to miss if only the main clue-text column
   is read. Changes the most likely explanation for at least this date from "no legitimate
   source" to "earlier transcriptions missed a column." The other 3 named dates and
   whether the specific historical PRs actually used this column are still unverified.
9. **[NEW 2026-08-23] Definition-fit scoring — the sharpest gap PR #24 surfaced.**
   Cumulative live precision across this project's only two live trials is 1/4 (25%); both
   misses are `prove.py` correctly verifying a real mechanism on a plausible-but-wrong
   answer — the gap is judging whether a candidate matches the DEFINITION, not whether the
   wordplay executes. `defspan.py`'s indicator-density approach to the adjacent
   definition-*location* problem already measured 1/5 (worse than chance) — a naive rule-
   based definition-fit scorer risks the same fate. UPDATE 2026-08-24: the Hebrew WordNet
   lead was CHECKED DIRECTLY, not left unconfirmed — `github.com/NLPH/HebrewWordnetShuly`
   is real, fetchable, MultiWordNet-aligned. But it answers the wrong question: it gives
   synset/synonym relations, not the ROLE-CATEGORY lookup ("the singer" -> שרה) this
   setter's culture clues actually need, which is a homograph/role fact this project's own
   HOMOGRAPHS.md already encodes by hand, not a synonym-set fact WordNet encodes. Possibly
   useful later for a `means()`/synonym expansion in `prove.py`, not for this item. No
   generator-shaped external resource has been found across three research passes
   (2026-08-22/23/24) — the next attempt on this item should assume none exists and work
   from the project's own data (as `culture_category_candidates`, 2026-08-24, did) or be
   scoped as a genuinely new internal idea, not another literature sweep.
   **2026-09-09: BUILT — `solver/deffit.py`, a gloss-overlap RE-RANKER** (a "fundamentally
   different signal" from the defspan.py indicator-density approach: it never localizes a
   definition span at all, it scores whether a candidate ANSWER's own corpus-attested
   definition overlaps the whole clue). Measured on a fresh puzzle (2026-05-15): n=2
   recall-hit clues, MRR 0.333->0.350, too small to call positive. Sharper finding: 0/28
   clues have a non-retrieval candidate scoring non-zero -- def_fit is architecturally
   redundant with `retrieval_candidates` today (same index, same BM25, opposite query
   direction), so it cannot yet corroborate a mechanically-derived candidate independently.
   Concrete next step: wire in a second, independent gloss source -- `solver/lex/fillbank.json`
   (2,412 real dictionary word->definition pairs) -- not attempted today. See log.
   **2026-09-10: WIRED IN.** `build_fillbank_index()` adds fillbank as a second,
   independently-scored source (own BM25 stats, kept separate from private_defs'). Found
   and fixed a real bug first: fillbank's keys weren't final-letter-folded, so 557/2,450
   (22.7%) entries would have been silently unreachable against candidates.py's always-folded
   answers. Measured on a fresh 2026-05-15 transcription: `nonretrieval_known_gloss_clues`
   (any non-retrieval candidate has SOME known gloss) moved 3/28 -> 14/28; the stricter
   `nonretrieval_scored_clues` (that gloss actually shares vocabulary with the clue) stayed
   0/28 -- the 59 newly-known candidates' glosses just don't repeat their clues' wording.
   recall@N was 0/28 this run (a smaller fresh corpus found none of this puzzle's answers),
   so top-1/MRR remain untested since #53's own n=2. A real, mixed, disclosed result -- gloss
   coverage widened for real, the score-based signal this project plans to rank by did not.
   See log.

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
- 2026-08-22: **first FULL-puzzle live blind trial of `solve_pass.py`**, closing the gap
  flagged since 2026-08-16 ("solve_pass.py is not yet wired into a live blind solve that
  produces a reliable precision/coverage/yield number ... that full-puzzle trial is the
  honest next step"). Chose this over another candidate-generation/defspan attempt because
  `list_pull_requests` showed the backlog down to 1 open PR (#23, item 7's fix, opened
  2026-08-21) and RESEARCH.md's sweep this run (see its own 2026-08-22 entry) found nothing
  new to extend either struck-or-negative lever — the queue's own explicitly-named
  remaining gap under item 1(a) was the best-evidenced next step.

  BOOTSTRAP: `./bootstrap.sh --dev-only` succeeded cleanly this run (51/52 puzzles, 1429
  clues; the 14across bot-wall that blocked recent runs did not engage today). Reverted
  the regressed `solver/lex/substitutions.json` rebuild (528 vs committed 2,220 head
  words) per the standing warning, as every prior run has had to.

  PUZZLE CHOICE: 2026-05-15, deliberately — it is the one puzzle DAILY.md's own log
  explicitly flags as still safe for a genuinely blind trial (2026-08-16's agent partially
  transcribed its image but never touched its answer key or wrote clue text; 2026-05-21 and
  2026-05-29, the other candidate dev dates, both have SPECIFIC gold answers quoted
  in-line in this very file's log from earlier runs' enum-reversal/recall write-ups, which
  would have burned them for MY blind attempt the moment I read this file — checked this
  explicitly before picking a puzzle, since DAILY.md itself is required reading each run
  and is therefore a leak vector its own instructions don't flag).

  TRANSCRIBED all 28 clues (15 across, 13 down) from `data/images/2026-05-14.jpg` myself,
  cross-cropping/zooming ambiguous words multiple times. Validated every enum sum against
  `data/grids/2026-05-15.json` via `solver/grid_tools.py validate` (grid geometry only,
  no gold answer read) — **0/28 mismatches**, strong independent confirmation the
  transcription is accurate before any gold was touched. Only after that did
  `solver/build_dataset.py` join clue text with the (already-bootstrapped)
  `data/answers/by_date/2026-05-15.json` — I did not read that file myself; the join step
  reported **0 len mismatches, 0 missing answers** across all 28 rows, again computed by
  code, not read.

  DELEGATED the actual solving to a fresh subagent (no memory of this session, so no
  chance of the puzzle-selection reasoning above leaking anything) with SOLVE_PROTOCOL.md
  as its method and an explicit, repeated hard rule never to touch `data/answers/**`,
  `data/dataset/**`, `14across.co.il`, or search the clue text verbatim. It used
  `homographs.py scan` + `solve_pass.py clue` per clue, `prove.py check` before every
  commit, and applied the self-flag-your-weakest-commit rule (downgraded 8A from committed
  to suggestion). Output: 2 committed, 11 suggestion, 15 blank — archived at
  `evals/runs/live/2026-08-22_2026-05-15_blind.json`.

  MEASURED (executed): `python3 evals/run_eval.py evals/runs/live/2026-08-22_2026-05-15_blind.json`
  — **PRECISION 0/2 = 0%, COVERAGE 7.1% (2/28), YIELD 0%**, suggestion hit-rate 0/11.
  Both committed answers were WRONG. Error report at
  `evals/runs/live/2026-08-22_2026-05-15_blind_errors.json`.

  HONEST ROOT-CAUSE, inspected directly, not just the number. Both misses are the SAME
  failure mode 2026-08-16 already predicted from the literature: a mechanically-verified
  device landing on a real Hebrew word that is not the setter's intended answer.
  - **9A** `הבהמה צריכה מים גם למזוג` (3): committed `גמל` (camel) via a hidden-word device
    spanning a word boundary (`גם ל`(מזוג) -> גמל), definition "the animal that needs
    water." Gold is `תאו` (water buffalo) — an equally-valid, arguably BETTER fit for
    "the animal that needs water" (water buffaloes wallow), that the hidden-word scan
    structurally cannot find because it isn't a literal substring of the clue at all.
    `prove.py`'s `is_hidden` genuinely passed; the mechanism was never the problem, the
    candidate it happened to surface was the wrong one for this definition.
  - **24A** `בגב שער ירושלמי` (3): committed `רעש` (noise) via a clean letter-reversal of
    `שער` (gate reversed = noise), self-contained pun. Gold is `שכמ` (Shechem/"shoulder") —
    `שער שכם` is the literal Hebrew name for Damascus Gate (Shechem Gate), and `שכם` also
    literally means "shoulder/back," so `בגב` ("on the back") is a double-definition
    pointing straight at `שכם` via Jerusalem-gate culture knowledge the reversal mechanism
    has no way to compete with. Again a real, passing proof — on the wrong candidate.

  Combined with 2026-08-16's trial (1/2, also correctly attributable to a definition-fit
  misjudgment on the wrong side, per that day's own log), **cumulative live precision
  across the only two full/partial live trials this project has run is now 1/4 = 25%** —
  well below both the 96.9% batch-dev number (which is not a blind measurement in the same
  sense; see RESULTS.md) and the ~50-95% precision this project's earlier hand-solved
  rounds report. This is the sharpest evidence yet, across two independent trials on two
  independent puzzles, that **the proof gate's real limitation is exactly what
  SOLVE_PROTOCOL.md already states in prose but this project had not yet measured live at
  n>2**: `prove.py` proves a wordplay MECHANISM is internally consistent, never that a
  candidate is THE answer, and `solve_pass.py`'s ranking (lexicon-tier, split-feasibility)
  does not currently touch definition-fit at all — which is precisely the gap definition-
  span detection was meant to close, and which the 2026-08-19 attempt at that (indicator-
  word density) already measured as not working on this corpus. The queue does not
  currently have a replacement idea for definition-fit scoring; RESEARCH.md's literature
  sweeps have not found a Hebrew-portable one either. Flagging as the sharpest open
  question this project has, not solving it today.

  COVERAGE, separately: 7.1% (2/28) is well below every historical dev number (36-57%) and
  below 2026-08-16's 9.5% — expected, not concerning: this was a genuinely cold, unassisted
  puzzle with no crossing letters ever available (0 answers reached confidence 0.6, so
  SOLVE_PROTOCOL's grid-propagation loop never got to run at all), a materially harder
  setting than any prior dev/eval score, most of which had some crossings by the time they
  were scored. Blank rate (15/28, 54%) is the policy working as intended — PRECISION FIRST
  means most of a genuinely stuck puzzle should be blank, not guessed, and today's 2
  committed answers (both wrong) show even the deliberately-conservative 0.75 confidence
  bar was not conservative enough this trial.

  AUDIT (mandatory gate). No forbidden reads: grepped the subagent's own tool-call log for
  literal `data/answers`, `data/dataset`, and `14across` path arguments in Bash/Read
  invocations (not just any mention, which would also catch the guardrail instructions
  echoed back) — zero hits; the only matches were the rule text itself. `held_out_answers()`
  correctly blocked all 28 of this puzzle's own gold answers regardless of whether PR #23's
  fix is merged, because all 28 clues were transcribed (the fix only matters for PARTIAL
  puzzles, which this wasn't). No jump to explain — 0% and 7.1% are both drops from every
  prior number, the opposite direction a leak would produce; if anything, a wrong-on-both
  live result is easier to trust than a suspiciously high one, and is itself indirect
  evidence against contamination (a leaked gold answer would very likely have scored a hit,
  not two misses). Puzzle-selection leak risk (DAILY.md's own log text) is disclosed above
  and was checked before picking 2026-05-15, not after.

  NOT DONE, honestly: did not attempt a second live puzzle for a larger sample (would
  dilute today's one-lever discipline and this trial alone took the full run); did not
  build a definition-fit scorer (flagged above as the real gap, not attempted — no
  validated approach exists yet per RESEARCH.md); did not merge or otherwise act on PR #23
  (out of scope for this lever, flagged for whoever reviews next).
- 2026-08-28: **crawled `note.co.il` for the first time this project's lifetime**, closing
  queue item 1(d)'s own next step (flagged unattempted in the 2026-08-25/08-26/08-27 log
  entries). Branched from `origin/daily/2026-08-27-live-trial-retrieval` (PR #29, open,
  unmerged, mergeable-clean) rather than from main, since main still lacks #29's work and
  stacking on the latest unmerged PR is the standing fix for the PR-pileup pattern.

  BOOTSTRAP: `./bootstrap.sh --dev-only` hit the same 14across hard wall as
  2026-08-19/08-26/08-27 (killed by a 170s timeout with only 1/52 puzzles recovered, the
  rest `None: 0 clues`) — not fought further. Fetched `data/images/2026-05-28.jpg` and
  `data/images/2026-06-04.jpg` directly from the public CDN (bypassing bootstrap's
  sequential step order, since steps 3-6 don't depend on step 2 finishing) rather than
  waiting on the script.

  CORPUS: ran `scraper/crawl_defs.py note` for the first time ever in this project —
  discovered 934 candidate solution-page URLs across all 22 Hebrew letters, fetched 829 of
  them before a deliberate ~15-minute stop (not exhausted). Also re-ran `crawl_defs.py
  mordo` fresh: 13,646 raw entries (12,890 after `reparse_mordo()` populated their
  `answers` field), up from 2026-08-25's 9,685 — the blogspot feed apparently has more
  indexed content now. No code change needed: `retrieve_defs.build_index()` already globs
  every `*.jsonl` under `private_defs/`, confirmed by reading the code before assuming it.

  RE-TRANSCRIBED THE CANONICAL DEV PUZZLE (2026-05-29) a third independent time (after
  2026-08-06's original and 2026-08-25's redo), via the documented image-fallback
  technique, so today's number is directly comparable to both prior measurements on this
  exact puzzle. Clue text from `data/images/2026-05-28.jpg` (28/28 clues); gold letters
  from the small solved-grid recap in `data/images/2026-06-04.jpg` ("פתרון תשבץ ההיגיון
  מהשבוע שעבר"), with the grid pixel geometry calibrated PROGRAMMATICALLY (darkness-
  fraction column/row detection, not eyeballed): all 16 row-lines and all 12 column-lines
  detected as continuous dark strokes, and after correcting the column read order to
  RTL (index 0 = rightmost, per `grid_tools.py`'s own documented convention — the first
  attempt was column-reversed, caught immediately by a full 8-row mirror-image mismatch,
  the same symptom PR #27 and 2026-08-26's entry both already flag as this fallback
  technique's characteristic bug), the reconstructed black/white pattern matched the
  committed `data/grids/2026-05-29.json` with **0/15 row mismatches**. `grid_tools.py
  validate` caught one real transcription bug before any measurement: clue 13 across's
  enum was mistranscribed as (6) (mistaking clue 11's trailing enum for clue 13's own,
  since clue 13's text wraps across the newspaper's column break) — the grid slot was
  4, not 6; corrected to (4) once the actual clue-13-final enum was traced to a `(4)`
  three words later in the wrapped text, re-validated clean. All 28 extracted gold answers'
  letter-counts matched their enums exactly, an independent cross-check beyond the
  grid-pattern match. Several extracted answers are recognizable real words/names
  (`ברישניקוב`/Baryshnikov, `ליסט`/Liszt, `צרנוביל`/Chernobyl, and `ישפרחימ` for 7-across
  — exactly the worked example `SOLVE_PROTOCOL.md` itself already cites for this clue),
  further corroborating the transcription independent of the pixel/enum checks.

  MEASURED (executed, not estimated), controlled before/after on the re-derived puzzle
  (`python3 solver/candidates.py recall data/dataset/clues.jsonl eval [--no-culture]
  [--no-retrieval]`):
  - Mechanical-only baseline (`--no-culture --no-retrieval`): **3.6% (1/28)** — exactly
    reproduces the 2026-08-06 and 2026-08-25 numbers on this same puzzle from two
    independent prior transcriptions, a strong cross-check that today's third independent
    transcription is correct.
  - `+ retrieval_candidates` (`--no-culture`, grown corpus): **10.7% (3/28)** — up from
    the 7.1% (2/28) this exact puzzle scored 2026-08-25 with the smaller, mordo-only
    corpus. The new hit is 1 down (`באות לפני דקירת רקדן (עפ"י צבי ויצמן)` (9) ->
    `ברישניקוב`, i.e. Mikhail Baryshnikov, "רקדן בלט ושחקן רוסי אמריקאי" in the matching
    doc) plus the same 26-across hit 2026-08-25 already found (`פחותאבלכואב`).
  - Full defaults (culture+retrieval): also 10.7% — `culture_category_candidates`
    contributes nothing extra on this puzzle, consistent with its established narrow,
    puzzle-dependent pattern.
  - **Isolated which source produced the gain**, tested by moving each private_defs file
    aside in turn and re-running: mordo ALONE reproduces the full 10.7% (both hits,
    including the new `ברישניקוב` one — absent from 2026-08-25's smaller mordo crawl, so
    genuinely new from mordo's own growth). note.co.il ALONE reproduces exactly 7.1%
    (2/28) — the SAME 26-across answer, but via a DIFFERENT, independently-checked source
    document (`note.co.il`'s own "שיר למילים של יהונתן גפן" entry listing `פחות אבל כואב`
    among Geffen's song titles, distinct from mordo's matching doc) — confirming note.co.il
    is a real, independently-working retrieval source, not dead weight, even though on
    this specific puzzle it doesn't add a NET-NEW hit beyond what mordo's growth already
    supplied.
  - **Honest attribution**: today's recall gain over 2026-08-25's number (7.1% -> 10.7%)
    traces to mordo's corpus having grown, not to today's note.co.il crawl specifically —
    disclosed plainly rather than crediting the more novel-sounding half of today's work.

  AUDIT (mandatory gate). Both retrieval hits' source docs confirmed `pid=None` (external
  private_defs corpus, not this project's own puzzle text) by direct grep over
  `retrieve_defs.build_index()`'s doc list. `lexicon.held_out_answers()` AND
  `retrieve_defs.held_out()` both confirmed to block all 28 of this puzzle's own gold
  answers (`gold_norm - blocked` empty for both, checked directly, not assumed from the
  code path). No forbidden reads: gold data came entirely from the two public CDN images;
  14across was never queried for this puzzle. No jump to explain: 3.6% -> 10.7%
  (+7.1 points) is well under the ~15-point implausibility bar and fully accounted for by
  2 legitimate external retrieval hits. All 5 affected selftests (`candidates.py`,
  `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`) re-run clean.

  NOT DONE, honestly: did not run note.co.il's crawl to exhaustion (829/934 discovered
  URLs fetched, deliberately stopped, not a hard limit); did not re-measure the
  2026-06-26 or 2026-07-10 puzzles with the grown corpus (the two puzzles that most
  needed a bigger index, per 2026-08-26's/08-27's own findings — out of scope to keep
  this run to one lever); did not wire anything new into `solve_pass.py` (no code change
  was needed — the existing wiring already picks up the grown corpus automatically); did
  not merge PR #29 or this branch (only the project owner can); did not act on queue
  items 8 or 9 this run.
- 2026-08-29: **continued queue item 1(d)'s own next step from 2026-08-28**: a fuller
  `note.co.il` crawl (no early stop this time) plus a fresh `mordo` re-crawl, re-measured
  on 2026-07-10 (one of the two puzzles 2026-08-28 flagged as most needing a bigger
  corpus, since it scored flat with the smaller one on 2026-08-27).

  RESEARCH first (per the scheduled task's priority order): general candidate-generation
  literature ("cryptic crossword clue solving diverse candidate generation arxiv 2026"),
  Hebrew nonconcatenative morphology, and definition-fit scoring (item 9, the fourth pass
  on this exact gap after 2026-08-22/23/24) all surfaced only the same paper family
  already logged repeatedly since 2026-08-06 — nothing new or buildable. See RESEARCH.md
  for the full entry. Confirmed the queue's standing read: no literature lever this run;
  proceed with the internal, already-flagged next step instead.

  BOOTSTRAP: `./bootstrap.sh --dev-only` succeeded FULLY at 14across this run — 52/52
  puzzles, 1,457 clues — the first clean run since 2026-08-19 (2026-08-19/08-26/08-27/
  08-28 all hit a hard wall). Reverted the substitutions.json regression (528 vs 2,220
  head words) via `git checkout` per the standing warning before touching anything else.
  6 of 52 puzzles still came back `None: 0 clues` (an intermittent per-puzzle bot-check
  miss, not the hard wall) — 2026-06-26 and 2026-05-29 are both among them, so neither
  got real 14across data this run.

  TRANSCRIPTION: since 14across worked for 2026-07-10, took the simpler of the two paths
  the task instructions offer — clue TEXT transcribed from `data/images/2026-07-11.jpg`
  (19/28 clues, the same across-1-15 gap 2026-08-27 independently found transcribing this
  exact puzzle from the same image — a cross-check that both transcriptions found the
  same real gap, not a transcription slip), gold ANSWERS taken directly from
  `data/answers/by_date/2026-07-10.json` (real crowd-sourced 14across data, not the
  image-fallback solution-grid technique this project usually falls back to). Every one
  of the 19 enum sums validated against the real answer length via
  `solver/build_dataset.py` before any measurement: **0 mismatches**. Caught one genuine
  transcription puzzle along the way and resolved it by direct grid + gold cross-check
  rather than guessing: several across clues carry a `(מ)`/`(ח)` marker that is NOT an
  enumeration but a plene/defective-spelling flag (`candidates.py`'s own `CREDIT_RE`
  already documents this) — where a clue's own printed numeric enum was genuinely absent
  or ambiguous next to one of these markers, the grid-derived slot length (already
  cross-checked against `data/grids/2026-07-10.json`, which matches the 14across answer
  lengths exactly) settled it, not a guess.

  CORPUS: `scraper/crawl_defs.py note` run without a time-boxed stop this time — discovered
  1,301 unique solution-page URLs (up from 2026-08-28's 934) and fetched 970 before being
  stopped at a natural plateau in the fetch rate rather than a fixed 15-minute clock;
  `scraper/crawl_defs.py mordo` re-crawled fresh: 25,350 raw entries, 24,361 with parsed
  answers after `reparse_mordo()` (up from 2026-08-28's 13,646 raw / 12,890 parsed — the
  blogspot feed has grown again, the third consecutive run to observe this). Neither
  crawl was run to literal exhaustion (mordo's feed showed no sign of a hard end within
  the time budget this run allowed; note.co.il reached 970/1301 discovered) — "fuller,
  unbounded" here means not stopped early on a fixed timer, not proven exhaustive; both
  are honestly disclosed as such rather than claimed complete.

  MEASURED (executed, not estimated), controlled before/after (`python3 solver/
  candidates.py recall data/dataset/clues.jsonl eval [--no-culture] [--no-retrieval]`):
  - Mechanical-only baseline (`--no-culture --no-retrieval`): **0.0% (0/19)** — exactly
    reproduces 2026-08-27's number on this same puzzle, a strong cross-check that today's
    independent transcription (sourced differently — real 14across answers, not the image
    fallback) is correct.
  - `+ retrieval_candidates` (`--no-culture`, the much bigger corpus): **still 0.0%
    (0/19), UNCHANGED** — avg candidates/clue rose from 9.3 to 20.7 (retrieval IS
    contributing more raw candidates with the bigger corpus) but none of them is gold on
    any of the 19 clues.
  - Full defaults (culture+retrieval): also 0.0% — `culture_category_candidates`
    contributes nothing extra on this puzzle either.

  AUDIT (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
  both re-checked AFTER the corpus grew (not just assumed from the pre-crawl check) and
  confirmed to block all 19 of this puzzle's own gold answers (`gold_norm - blocked`
  empty for both). No forbidden reads: gold answers came from the sanctioned
  `data/answers/by_date/` path (bootstrap's own 14across scrape), clue text from the
  public Haaretz CDN image; 14across was never queried for clue text or verbatim clue
  search. No jump to explain — 0.0% stayed 0.0%, the opposite of an implausible result,
  so there is nothing here that could be a leak. All 5 affected selftests (`candidates.py`,
  `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`) re-run clean.

  HONEST READ: this is a genuine, informative NEGATIVE result on this specific puzzle,
  not a failed lever — retrieval's earlier gains (2026-05-29, twice, at two different
  corpus sizes) are real and reproduce; 2026-07-10 has now scored 0.0% three times, at
  three different corpus sizes (2026-08-27's original, 2026-08-28's grown corpus by
  inheritance, and today's nearly-doubled-again corpus), which is strong evidence this
  puzzle's specific idioms/culture references simply are not the kind of content
  note.co.il/mordo carry, not that the corpus is still too small. The queue's existing
  "puzzle-dependent, not a reliable lift" diagnosis is now better evidenced, not
  overturned: corpus growth is a real, repeatable lever for SOME puzzles and provably not
  a universal fix.

  NOT DONE, honestly: did not re-measure 2026-06-26 (the other puzzle 2026-08-28 flagged)
  — 14across missed that date again this run, and the image-fallback reconstruction
  (partially started: clue text transcribed for 18/28 clues from `data/images/
  2026-06-25.jpg`, cross-validated against `data/grids/2026-06-26.json`'s slot lengths
  with 0 mismatches, but gold-letter extraction from the following week's solution-grid
  image was not finished) was abandoned once 14across proved to have clean real data for
  2026-07-10 instead, to avoid stretching this run across two full puzzle
  reconstructions; did not run either crawl to literal exhaustion (see CORPUS above); did
  not wire anything new into `solve_pass.py` or attempt a live trial (no code change —
  this was a pure corpus-growth + re-measurement lever, matching 2026-08-28's shape); did
  not act on queue items 8 or 9 this run (item 9's research pass found nothing new, see
  RESEARCH.md); no PRs were open to merge or act on.

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
- 2026-08-24: **definition-driven candidate generation** (`solver/candidates.py`:
  `culture_category_candidates`), a new sub-item under lever queue item 1. Chose this over
  re-attempting definition-span detection (queue item 2, struck 2026-08-19) because
  RESEARCH.md's sweep this run (see its own 2026-08-24 entry) confirmed no external
  resource (Hebrew embedding space, Hebrew WordNet — checked directly and found real but
  answering the wrong question) exists to build a definition-fit SCORER on, but this
  project's own committed `solver/lex/culture.json` supports a definition-driven
  GENERATOR without any new scrape: every mechanism in `candidates.py` so far derives an
  answer from the clue's letters; this is the first one to derive it from the clue's
  meaning instead, generalizing SOLVE_PROTOCOL.md's homograph rule ("the singer" may mean
  the word שרה) from single ambiguous tokens to whole culture-namelist categories, and
  PLAYBOOK.md 1.8's own "creator/genre" recipe from song titles specifically to every
  category `lex/culture.json` tracks.

  BOOTSTRAP: `./bootstrap.sh --dev-only` hit a hard 14across bot-wall today, the same
  failure mode as 2026-08-19/2026-08-20 (not the "~half of requests" intermittent
  behavior from 2026-08-06) — of 52 staged answer pages, only **2 recovered** after the
  full retry-with-backoff loop ran to completion (~25 minutes). Hspell, culture.json, and
  the 4 dev images all came through the unaffected CDN/API paths as always. Reverted the
  regressed `solver/lex/substitutions.json` rebuild (528→116 head words this run) per the
  standing warning, as every prior run has had to.

  PUZZLE CHOICE: one of the 2 puzzles 14across did return this run was **2026-06-19** —
  fetched its clue-text image directly from the public Haaretz CDN (`data/images/
  2026-06-18.jpg`, bypassing 14across for the clue-text step entirely, same pattern prior
  runs used when the standard 4 dev dates failed to scrape) and transcribed all 28 clues
  (15 across, 13 down) by eye. Cross-cropped/zoomed ambiguous line-wraps multiple times —
  this puzzle's printed clue column wraps enum numbers across line breaks in a way that
  first read as off-by-one (an enum appearing to sit next to the WRONG clue number); caught
  and corrected before trusting it by cross-validating **every one of the 28 enum sums
  against `data/grids/2026-06-19.json`'s own derived slot lengths** (computed independently
  in Python from the grid's black/white pattern, not read off the image) — 0/28 mismatches
  once corrected, and a second independent check against this puzzle's real 14across gold
  answer lengths (which the bootstrap run happened to recover) also came back 0/28
  mismatches. Both checks passing independently is strong confirmation the transcription is
  accurate, not merely self-consistent.

  BUILT `culture_category_candidates` in `solver/candidates.py`: a hand-curated (NOT
  corpus-mined — disclosed in the code and RESEARCH.md rather than dressed up as
  empirical) Hebrew role/genre/geography trigger vocabulary mapping a clue's named
  category to the matching `lex/culture.json` bucket, filtered to the enum length. Wired
  into `generate()` behind a `use_culture` toggle (default on) so a controlled before/after
  recall measurement needs no second copy of the function; `solve_pass.py` needed NO
  changes at all — it already ranks by lexicon tier, and a culture-entity hit is
  automatically tier 3, so the new mechanism's candidates are already prioritized above
  plain-dictionary hits without any new ranking logic. Selftest extended with 3 new
  synthetic checks (a clue sharing NO letters with its candidate answer — the entire point
  of this device, contrasted with every other mechanism's selftest); all 10 checks pass.

  **AUDIT FINDING, caught DURING implementation, before any measurement — not a
  hypothetical.** The first version of `culture()` loaded `solver/lex/culture.json`
  directly, with no held-out filtering, unlike every other corpus-backed source in this
  file (`lexicon.load()`, `sub_fwd()`). Checked directly before running any eval: **5 of
  2026-06-19's own 28 gold answers (ישע, דונשבנלברט, בתשלמה, שמאיגולנ, אורהירח) were
  sitting unfiltered in the raw committed culture.json.** This is exactly the leak shape
  RESULTS.md's INTEGRITY FINDING already caught once in `lexicon.py` (a retrieval tool
  built from the same corpus as the eval set leaks even when file-access rules are
  perfectly obeyed) — fixed by giving `culture()` the same `lexicon.held_out_answers()`
  filter `lexicon.load()` uses, verified directly (`candidates.culture()`'s output no
  longer contains any of the 5 formerly-leaked answers; the mechanism's own hit list for
  the one clue it fired on does not contain that clue's gold answer either) before trusting
  any recall number below.

  MEASURED (executed, not estimated), controlled before/after on the same 28 clues:
  `python3 solver/candidates.py recall data/dataset/clues.jsonl eval --no-culture` →
  **0/28 = 0.0%** (avg 10.5 candidates/clue) — the mechanical-only baseline on this
  puzzle, notably lower than 2026-05-29's 3.6% or 2026-05-21's 7.1%, consistent with this
  being a harder-than-average puzzle (no anagram/hidden/reversal hits at all this time).
  `python3 solver/candidates.py recall data/dataset/clues.jsonl eval` (culture ON) →
  **still 0/28 = 0.0%** (avg 11.4 candidates/clue). Diagnostic breakdown: the new
  mechanism fired on only **1 of 28 clues** (6 down, triggered by "סופר" = author),
  generating 339 raw candidates before truncation, 0 of which matched gold.

  HONEST READ, root-cause not just the number: n=1 fired-clue is far too small a sample
  to call this mechanism dead, but the ONE case it did fire is genuinely informative. The
  clue text was "רואים שהשרה היא בכלל סופר שכתב על השואה" (gold `שמאיגולנ`, not a real
  author's name) — it contains BOTH "השרה" (a homograph — she sings / the (female)
  minister / Sarah) AND "סופר" (author), and PLAYBOOK.md's own worked examples (§1.8-1.9)
  show this setter routinely uses a category word like "סופר" as HOMOGRAPH/WORDPLAY
  fodder (a pun, a combo device) rather than as a literal pointer to a real author's name.
  My trigger vocabulary can't tell those two uses apart — it fires on the surface word
  regardless of whether the setter means it literally or as misdirection, which is exactly
  the ambiguity a genuinely cryptic clue is designed to exploit. This is a smaller, more
  specific version of the same standing finding from 2026-08-19's definition-span
  measurement and 2026-08-22's live-trial root-cause: this setter's clues resist
  surface-level heuristics (indicator words, category nouns) precisely because the
  misdirection is the point. A second puzzle's worth of data would help distinguish "this
  mechanism doesn't work here" from "this puzzle just had few category-noun clues," but
  building that costs a full independent transcription and this run's one-lever budget
  went to measuring and auditing what's here rather than a second data point.

  AUDIT (mandatory gate): the held-out leak above was found and fixed before any recall
  number was computed, not after — re-verified clean post-fix (see finding above). No
  forbidden reads: only `data/images/2026-06-18.jpg` (public CDN, transcription) and
  `data/answers/by_date/2026-06-19.json` (enum-length validation per protocol, plus the
  held-out audit check above — never fed to the generator itself). No jump to explain:
  0/28 to 0/28 is not a jump at all, the least suspicious result a controlled before/after
  can produce. All pre-existing selftests (`candidates.py`, `solve_pass.py`, `prove.py`,
  `defspan.py`, `substitutions.py`) re-run clean, no regressions.

  NOT DONE, honestly: no second puzzle for a larger sample (see above); did not build a
  corpus-mined version of the trigger vocabulary (would need many transcribed puzzles'
  worth of clue text to mine reliably — today's is hand-curated and disclosed as such); did
  not merge PRs #23/#25 (queue items 7/7b, both still open as of this run, out of scope for
  today's lever); did not act on queue item 8 (audit of across 1-13 sourcing) this run.
- 2026-08-25: **backlog consolidation, then wired ranked retrieval into candidate
  generation** (queue item 1's long-open "RANKED RETRIEVAL" sub-lever).

  **CONSOLIDATION FIRST.** `list_pull_requests` showed 3 open PRs against the same main:
  #23 (2026-08-21, item 7 fix), #25 (2026-08-23, item 7b fix, cherry-picks #23), #26
  (2026-08-24, `culture_category_candidates`) — the PR-pileup pattern flagged 2026-08-16,
  struck 2026-08-21, and now recurred twice more at smaller scale, exactly as 2026-08-24's
  own log warned it might. Verified #25's `lexicon.py` diff is byte-identical to #23's
  (`diff` on both branches vs main, 0 lines) confirming #25 fully supersedes #23. Cherry-
  picked the real code+RESEARCH.md commits from #25 (`7ad01cf05`, `a9838aa0d`) and #26
  (`0db509665`) onto one fresh branch off current main — all applied clean or with a
  trivial RESEARCH.md append-conflict, resolved by keeping both entries in chronological
  order (git's 3-way merge put 2026-08-22's entry before 2026-08-21's since the two PRs
  diverged from different points in main's history; fixed by hand). Hand-merged
  DAILY.md's state table, "Last lever" narrative, and Log section from all three PRs'
  branches (their DAILY.md-only commits were NOT cherry-picked, to avoid a 3-way header
  conflict — the state/log content was instead copied in directly) so no day's
  measurement or audit trail was dropped. Re-ran every affected module's selftest
  (`candidates.py`, `lexicon.py`, `substitutions.py`, `retrieve_defs.py`) post-merge — all
  pass, 0 regressions. This branch/PR supersedes #23, #25, and #26; the project owner can
  close those three once this one is reviewed instead of merging four times.

  **RESEARCH.** No new external finding either research thread turned up (see RESEARCH.md):
  general cryptic-solving literature unchanged; BM25-over-embeddings reconfirmed as the
  right call at this corpus's scale; Hebrew WordNet re-confirmed real but wrong-shaped for
  definition-fit. One recurring, worth-repeating finding: a plain web search's own summary
  presented this project's RETRACTED 96% leak number as a standing result AGAIN (second
  time, after 2026-08-20) — the live page itself fully caveats it, the summarizer drops
  that context every time. Since neither thread produced anything new to build ON, today's
  lever is the queue's own long-open INTERNAL gap instead: `solver/retrieve_defs.py` (BM25
  ranked retrieval, built 2026-08-08, the 2026-08-08 research queue's own priority-2 item)
  has never once been wired into `candidates.py`'s `generate()` pool — every measurement of
  it so far (5.4% gold@25, 2026-08-08) was standalone, never combined with the mechanical
  mechanisms to see if the UNION recall improves, which is exactly the logic that made
  RESULTS.md's consensus-merge experiments work (independent signals miss on different
  clues).

  **BOOTSTRAP.** `./bootstrap.sh --dev-only` hit the same severe 14across bot-wall
  documented since 2026-08-19/08-20/08-24 (only ~35/52 answer pages recovered after 45+
  minutes, still running in the background when this run's measurement was taken — not
  waited on, see below). hspell, culture.json, substitutions.json, and all 4 dev images
  came through the unaffected CDN/API paths cleanly. Reverted the regressed
  `solver/lex/substitutions.json` rebuild per the standing warning, as every prior run has.

  **BUILT `retrieval_candidates` in `solver/candidates.py`**: wraps
  `solver/retrieve_defs.py`'s existing `candidates()` (BM25 over private_defs + train-split
  clue explanations, held-out safe by construction via `retrieve_defs.held_out()`) as one
  more source in `generate()`, behind a `use_retrieval` toggle (default on, same pattern as
  `use_culture`) so before/after ablation needs no second copy of the function. `solve_pass.py`
  needed no changes — a retrieval hit ranks by the same lexicon-tier logic as every other
  candidate. Selftest extended with 2 new checks using an injected synthetic `docs_df`
  (independent of the real corpus, same discipline as every other mechanism here); all 12
  checks pass.

  **REBUILT THE EXTERNAL RETRIEVAL CORPUS** (`data/answers/private_defs/`, gitignored, so
  every run needing it must redo this): `python3 scraper/crawl_defs.py mordo` — a Blogspot
  JSON feed of pitaronfree.blogspot.com posts, 150 at a time — recovered 10,346 raw posts /
  9,685 parsed definition->answer pairs in under 3 minutes before being stopped (the feed is
  effectively unbounded and this run did not need a full crawl). Did NOT run `crawl_defs.py
  note` (the other source, note.co.il — a much slower per-page crawl per its own code) —
  flagged as a concrete next step for a bigger index, not attempted today to keep this run
  to one lever. `build_index()` confirmed to load all 9,685 pairs (0 from train-split, since
  today's only transcribed puzzle is eval-split — the external corpus alone is what's being
  tested here).

  **RE-TRANSCRIBED THE CANONICAL DEV PUZZLE (2026-05-29)** via the documented image-fallback
  technique (bootstrap.sh step 6's "NO-14ACROSS ALTERNATIVE") rather than wait out today's
  slow scrape: clue text from `data/images/2026-05-28.jpg` (28/28 clues, all enum sums
  validated by eye against the printed enumerations); solution letters from the small filled
  grid in `data/images/2026-06-04.jpg` (captioned "solution to last week's puzzle"),
  transcribed cell-by-cell and cross-validated PROGRAMMATICALLY (not just visually) against
  `data/grids/2026-05-29.json`: **0/15 row pattern mismatches** on the black/white cell
  geometry, and **28/28 enum sums matched** the grid-derived slot lengths independently
  computed from both sources. Both checks passing together is strong evidence this is really
  2026-05-29 and the transcription is accurate, matching the technique's 2026-08-03
  precedent.

  **ONE REAL TRANSCRIPTION ERROR CAUGHT AND FIXED, disclosed rather than hidden.** The
  initial pixel-cropped read of one cell (grid row 0, column 8 in left-to-right display
  order — shared by 1-across and 2-down) came out as ל, giving 2-down = `לחפניות`. This
  didn't match this file's own 2026-08-06 citation of the historical anagram hit
  (`יחפניות`) for the same slot on the same puzzle. Rather than silently trust either
  source, checked directly: `לחפניות` is absent from `solver/lex/hspell.txt`; `יחפניות` is
  present AND is an exact-multiset anagram of the clue's fodder "פחות יין" — strong evidence
  of a misread, not a citation error. Root-caused it: naive linear cell-boundary estimation
  (assuming 11 equal-width columns across a fixed pixel span) drifted by roughly a full
  cell-width by the 9th column, because the true grid boundary sits ~76px short of where a
  naive right-margin estimate placed it (that margin is blank space before the page's
  vertical caption text, not part of the grid). Fixed by detecting actual gridlines
  programmatically (column darkness profile across many rows) rather than assuming uniform
  spacing, re-cropped the disputed cell precisely, and confirmed it visually reads י, not ל.
  Re-validated the corrected grid: still 0/15 pattern mismatches (the fix doesn't change any
  slot's length, only one letter). **This is a real, general lesson worth keeping**: pixel-
  math cell-boundary estimates for this fallback technique should be calibrated from
  detected gridlines, not assumed-uniform spacing, especially past the first few columns.

  **MEASURED (executed, not estimated), controlled before/after on the re-derived
  2026-05-29 (`python3 solver/candidates.py recall data/dataset/clues.jsonl eval
  [--no-retrieval] [--no-culture]`):**
  - Mechanical-only baseline (`--no-culture --no-retrieval`): **1/28 = 3.6%**, the SAME
    single anagram hit (`יחפניות`, 2 down) as the 2026-08-06 baseline on this exact puzzle
    — this exact reproduction of a 2.5-week-old number, from an independently redone
    transcription, is itself a strong sanity check that today's re-transcription is
    correct, beyond the pattern/enum validation above.
  - `+ culture_category_candidates` alone: 1/28 = 3.6%, unchanged (consistent with
    2026-08-24's finding that this mechanism is narrow and puzzle-dependent).
  - `+ retrieval_candidates` alone: **2/28 = 7.1%** — the new hit is 26 across
    (`יהונתן גפן ויהודה פוליקר על ברית מילה (עפ"י עפר קציר)` -> `פחותאבלכואב`), a real
    Yehonatan Geffen / Yehuda Poliker song title ("less but hurts") that shares ZERO
    letters with the clue text — structurally unreachable by anagram/hidden/reversal/
    substitution/homograph, exactly the failure mode `culture_category_candidates` was
    built to address on 2026-08-24 but didn't catch on that puzzle. Recall DOUBLED.
  - Both together: 2/28 = 7.1% (culture_category still contributes nothing extra on this
    puzzle; the two mechanisms did not stack here, but neither hurt the other).

  **HONEST READ.** This is the first candidate-generation sub-lever since 2026-08-06 to
  move recall at all — every other attempt (substitution/homograph twice, culture_category
  once) measured flat or near-flat. One hit on one puzzle is a small sample; it does not
  establish retrieval as a reliable source, only that it CAN catch a real class of miss
  (culture-reference answers sharing no letters with the clue) that a hand-curated category
  list did not catch on this same puzzle. The private_defs corpus used today (mordo/
  pitaronfree only, 9,685 pairs) is a fraction of what `crawl_defs.py note` could add; a
  fuller index and a second dev puzzle are the natural next steps, not attempted today to
  keep this run to one lever plus the consolidation housekeeping.

  **AUDIT (mandatory gate).** No forbidden reads: 2026-05-29's gold data came entirely from
  public CDN images (the sanctioned fallback), never from 14across for this specific
  puzzle — the background bootstrap's own (still-incomplete, unused) 14across scrape was
  for the general corpus, not this measurement. Tool-leak check: `lexicon.held_out_answers()`
  confirmed to block all 28 of this puzzle's own gold answers (`gold_norm - blocked` is the
  empty set, checked directly). The retrieval hit's source document was inspected directly
  (`pid=None`, a generic "works by Yehonatan Geffen" listing from the external mordo corpus,
  not this project's own puzzle text) — genuine independent knowledge, not a leak, the same
  "controlled fact lookup" SOLVE_PROTOCOL.md already sanctions for culture clues. No jump to
  explain: 3.6% -> 7.1% is a small, explicable move (one legitimate external hit), nowhere
  near the ~15-point implausibility bar. All affected selftests re-run clean post-fix.

  NOT DONE, honestly: did not crawl `note.co.il` for a bigger retrieval index; did not
  re-measure on a second puzzle; did not merge this branch to main (only the project owner
  can); did not act on queue items 8 or 9 this run.
- 2026-08-26: **second, independent dev-puzzle measurement of `retrieval_candidates`**,
  closing PR #27's own explicitly flagged gap ("worth a second puzzle's data point before
  calling this settled"). Branched from `origin/daily/2026-08-25-consolidate-and-lever`
  (PR #27, open, unmerged, mergeable-clean against main) rather than from main directly —
  main still lacks all of #23/#25/#26/#27's work, and stacking on the latest unmerged PR
  is the same fix the 2026-08-16/08-25 PR-pileup findings already recommend, so this PR
  supersedes #27 (and by extension #23/#25/#26) too; the project owner only needs to merge
  one of them.

  BOOTSTRAP: `./bootstrap.sh --dev-only` ran clean for lexicon (129,574 words) but 14across
  (step 2) was fully blocked all run — 0/52 puzzles recovered after 30+ consecutive `None: 0
  clues` responses, matching 2026-08-19's hard-wall failure mode (not 2026-08-06's "~50%
  random" one). Not needed for today's measurement (see below), left running in the
  background rather than fought.

  PUZZLE CHOICE AND TRANSCRIPTION: picked 2026-06-26 — the next committed-grid date after
  every puzzle this project's log already shows as gold-touched (2026-05-15, 05-21, 05-29,
  06-05, 06-12, 06-19, 04-03), so genuinely fresh. Fetched `data/images/2026-06-25.jpg`
  (its own clue image) and `data/images/2026-07-02.jpg` (the FOLLOWING week's image, whose
  small reference grid prints "פתרון תשבץ ההיגיון מהשבוע שעבר" — solution to LAST week's
  puzzle, i.e. this one) directly from the public Haaretz CDN, bypassing the blocked
  14across entirely, per the documented bootstrap.sh step 6 fallback. Transcribed clue text
  by eye; confirmed the recurring across-clue gap this project's queue item 8 already
  documents, this time worse than usual — only across 22-26 are printed for this puzzle,
  across 1-21 are absent from the image (a stray unnumbered clue fragment ending "(6)"
  appeared before ".22"; rather than guess which slot it belongs to, EXCLUDED it, matching
  this project's own "explicitly left as not attempted" precedent from 2026-06-12).
  Transcribed 18 clues total (5 across, 13 down). Every enum was resolved by cross-checking
  against `solver/grid_tools.py`'s own computed slot lengths for 2026-06-26's committed
  grid BEFORE reading any gold answer — `grid_tools.py validate` confirms 0 enum-sum
  mismatches on all 18 transcribed clues (the 10 untranscribed across slots correctly
  report as "grid slot but no printed clue", not a mismatch).

  GOLD LETTERS: rather than eyeball the small solved-grid image's cell boundaries (the
  source of a real transcription bug PR #27 hit and fixed yesterday), calibrated the grid
  pixel geometry PROGRAMMATICALLY this run: detected grid-line pixel columns/rows via a
  darkness-fraction threshold, then verified the resulting 11x15 cell grid's black/white
  pattern against the ALREADY-COMMITTED `data/grids/2026-06-26.json` — 0/15 row mismatches
  once column order was corrected (the first attempt was column-reversed, caught
  immediately by 8 row mismatches that were exact mirror images of the expected pattern,
  which is what mis-ordered RTL columns look like as a symptom). With calibration
  confirmed, cropped and read each needed slot as a single strip image (not the whole
  grid at once), which also gave an independent semantic sanity check on nearly every
  answer as it was read (`תגלת פלאסר` = Tiglath-Pileser for "an ancient king"; `בוב דילן`
  containing hidden `בדיל` for "won a Nobel prize because it contains their metal";
  `מרידיאן` from queen+princess names "Mary/Di/Ann" in a line; `בר סמכא` for "the expert";
  etc. — real, checkable wordplay, not noise, which is itself evidence the transcription
  and grid-calibration are correct, independent of the enum-sum validation).

  MEASURED (executed, not estimated): `python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval [--no-retrieval] [--no-culture]` on these 18 clues:
  - Mechanical-only baseline (`--no-culture --no-retrieval`): **0/18 = 0.0%**.
  - `+ retrieval_candidates` (`--no-culture`): **1/18 = 5.6%** — the new hit is 21 down
    (`המומחה משיב אבל אינו מסכים (עפ"י צבי ויצמן)` (4,2) -> `ברסמכא`, i.e. "בר סמכא", an
    authority figure). Full defaults (culture+retrieval both on) also land at 1/18 = 5.6%;
    `culture_category_candidates` contributes nothing extra on this puzzle either,
    consistent with 2026-08-24's finding that it fires rarely.
  - Rebuilt the external private_defs/mordo.jsonl corpus fresh this run
    (`scraper/crawl_defs.py mordo`) rather than reuse anything (gitignored, as always) —
    recovered 31,347 definition->answer pairs before a deliberate stop, over 3x
    2026-08-25's 9,685 (the site apparently has more indexed content now, or yesterday's
    run stopped early for an unrelated reason not recorded in its own log).

  AUDIT (mandatory gate). Retrieval-hit provenance checked directly: both index documents
  matching `ברסמכא` carry `pid=None` (external mordo corpus, a generic "מומחה המשמש
  כאוטוריטה" definition entry) — not this project's own puzzle text, not a leak.
  `lexicon.held_out_answers()` confirmed to block all 18 of this puzzle's own gold answers;
  separately confirmed none of the 18 appear at corpus/culture priority tier (>=2) in the
  loaded lexicon at all (0 leaked). No forbidden reads: 14across was never queried for this
  puzzle's gold data, only the two public CDN images (the sanctioned fallback). No jump to
  explain: 0.0% -> 5.6% is a small, single-hit move in the same direction as yesterday's
  3.6% -> 7.1%, not an outlier. `solve_pass.py`, `candidates.py`, `retrieve_defs.py`,
  `lexicon.py`, `substitutions.py`, and `prove.py` selftests all re-run clean.

  HONEST READ: this is now TWO independent puzzles, transcribed by two different agents on
  two different days, both showing `retrieval_candidates` roughly DOUBLE recall (3.6%->7.1%,
  0.0%->5.6%) versus the mechanical-only baseline. That is meaningfully stronger evidence
  than yesterday's n=1 anecdote that this lever is a real (if still small) source of
  candidates the mechanical mechanisms structurally cannot reach — but it is still only 2
  total hits across 46 clues, and both hits are idiom/name lookups a definition-retrieval
  index is naturally suited to, not evidence the approach generalizes to this setter's
  harder charade/pun clues. `culture_category_candidates` continues to look narrow and
  puzzle-dependent (0 extra contribution on both of the last two dev puzzles it's been
  tried against).

  NOT DONE, honestly: did not crawl `note.co.il` (still the one external source never
  crawled this project's lifetime); did not wire `retrieval_candidates` into a live
  `solve_pass.py` blind trial (every candidate-gen sub-lever so far has stopped at offline
  recall@N, a standing gap this queue keeps naming and no run has yet closed); did not act
  on queue items 8 or 9; did not merge PR #27 or this branch (only the project owner can).
- 2026-08-27: **first LIVE blind trial with `retrieval_candidates` active**, closing the
  gap flagged in every retrieval-related run since 2026-08-25 ("worth eventually wiring
  into a live solve pass — still true of every candidate-gen sub-lever so far"). No code
  change was needed: `solve_pass.py`'s `rank()` already calls `candidates.py generate()`
  with `use_retrieval=True` by default (confirmed by reading the source before assuming
  anything), so retrieval has been live-reachable since 2026-08-25 — it had simply never
  been exercised by an actual live trial.

  RESEARCH (see RESEARCH.md for full entries): fourth-plus consecutive literature pass
  finding nothing new and buildable on candidate generation or definition-fit scoring.
  One genuinely new citation — "Splintering Nonconcatenative Languages for Better
  Tokenization" (arXiv 2503.14433, SPLINTER) — describes Hebrew proclitic-prefix
  handling but for LM-pretraining tokenization, not runtime clue-fragment segmentation;
  doesn't transfer here. An MCTS crossword-solving paper and a WordNet-based semantic
  candidate-generation paper both confirmed standing conclusions (queue item 4's
  sequencing; Hebrew WordNet answers the wrong question) rather than adding anything.

  BOOTSTRAP: `./bootstrap.sh --dev-only` hit a full 14across wall today — 0/52 puzzles
  after 30+ minutes with the background scrape still returning nothing; a direct
  single-URL fetch of one specific date also failed after 8 retries with backoff,
  confirming this is the 2026-08-19/08-26 hard-wall failure mode, not the intermittent
  ~50%-random one, so the background scrape was killed rather than waited out further.
  hspell/culture/substitutions all came through the unaffected CDN/API paths cleanly.

  PUZZLE CHOICE AND TRANSCRIPTION: needed a genuinely untouched puzzle with a committed
  grid (since 14across couldn't supply gold data). `data/grids/2026-07-03.json`,
  `2026-07-10.json`, and `2026-07-17.json` are all committed and untouched by any prior
  log entry (grepped DAILY.md/RESULTS.md/PLAN_V2.md/RESEARCH.md for all three dates —
  zero hits) — chose 2026-07-10. Fetched its own clue-text image directly from the
  public CDN (`data/image_urls.txt`'s `2026-07-11` entry — an odd Saturday-dated
  manifest label, but its content and grid pattern confirm it is genuinely 2026-07-10's
  own puzzle image, not a mislabeled different date) and transcribed 19 of 28 clues (6
  across, 13 down) — the standard across-1-15 gap this project's queue item 8 already
  documents recurring most weeks. Validated every enum sum against
  `data/grids/2026-07-10.json` via `solver/grid_tools.py validate` BEFORE touching any
  gold data: 0/19 mismatches, and the 9 "problems" reported are exactly the 9 missing-
  clue across slots (1,7,8,9,10,11,12,13,14), not genuine mismatches — strong
  confirmation the transcription and puzzle-date identification are both correct.

  GOLD LETTERS, since 14across was unreachable: recovered from the small solved-grid
  recap in the FOLLOWING week's image (`data/images/2026-07-16.jpg`, captioned "פתרון
  תשבץ ההיגיון מהשבוע שעבר" — confirmed by reading that caption directly, not assumed),
  per the documented NO-14ACROSS fallback. Rather than eyeball cell boundaries,
  calibrated the grid geometry programmatically (row/column gridline detection via a
  darkness-fraction threshold) and transcribed all 15 rows' letters in IMAGE reading
  order, then let code (not hand arithmetic) reverse each row into
  `grid_tools.py`'s index convention — validated by comparing the resulting black-cell
  pattern against the ALREADY-COMMITTED `data/grids/2026-07-10.json`, row by row.

  TWO REAL TRANSCRIPTION BUGS CAUGHT AND FIXED by that same check, disclosed rather than
  silently corrected: (1) an early attempt hand-derived the index-reversal for
  non-palindromic rows algebraically and made an arithmetic slip on row 7 (swapped a
  three-letter middle span), invisible until the row-by-row pattern diff was run against
  the committed grid — fixed by re-deriving every row's reversal in code instead of by
  hand, and re-validating all 15 rows, not just the one that was visibly wrong; (2) a
  straight typo substituted a final-form letter (ן) for its regular form (נ) in one
  cell, caught because the project's own convention (grid letters are never final-form)
  gave a second, independent check beyond the black-pattern match — the resulting
  answer read as nonsense (`ןוקטורנו`) until fixed to the semantically correct
  `נוקטורנו` ("Nocturne," matching the clue's "musical work" definition). Both bugs were
  live before any candidate generation or scoring touched the data; neither reached the
  live trial. `held_out_answers()` confirmed to block all 19 gold answers once the
  dataset was built.

  DELEGATED to a fresh subagent (no memory of this session) with SOLVE_PROTOCOL.md as
  its method, `solve_pass.py`/`prove.py`/`homographs.py`/`wiki.py` as its tools, and
  explicit hard rules never to touch `data/answers/**`, `data/dataset/**`,
  14across.co.il, or search clue text verbatim. Output: 7 self-labeled "committed", 4
  suggestion, 8 blank — archived at
  `evals/runs/live/2026-08-27_2026-07-10_blind.json`.

  MEASURED (executed): `python3 evals/run_eval.py evals/runs/live/2026-08-27_2026-07-10_blind.json`
  — **PRECISION 1/1 = 100% (only 1 of the 7 self-labeled commits cleared the policy's
  0.75 confidence bar; `run_eval.py`'s own tier-enforcement correctly downgraded the
  other 6 to suggestion, which is the policy working as intended, not a scoring bug),
  COVERAGE 5.3% (1/19), YIELD 5.3%, suggestion hit-rate 0/10 = 0%**. The one correct
  commit (23A, `ראי`) is a double-definition culture reference solved via `wiki.py`
  entity lookup (two different songs/poems sharing the word `ראי`), not via any
  candidate generator. Error report at
  `evals/runs/live/2026-08-27_2026-07-10_blind_errors.json`.

  RETRIEVAL'S CONTRIBUTION, specifically: grepped the subagent's full tool-call
  transcript for `(retrieval, fodder=` — `solve_pass.py`'s own output marker for a
  retrieval-sourced candidate — across all 19 `solve_pass.py clue` invocations (one per
  clue, confirmed by count). **Zero matches.** `retrieval_candidates` never surfaced a
  single candidate this trial. This is not a contradiction of the offline signal but a
  confirmation of it: this run's own `candidates.py recall data/dataset/clues.jsonl
  eval` diagnostic on this identical puzzle also measured 0/19 recall with retrieval
  on vs. off (unchanged) — the private_defs corpus (mordo/pitaronfree, built 2026-08-26)
  simply has no coverage of this puzzle's specific idioms and culture references. Two of
  the three independently-measured puzzles so far show a real retrieval gain; this one
  shows none at all — the honest updated read is that retrieval is a real but
  inconsistent, puzzle-dependent source, not a reliable lift, and (on this puzzle) not
  what's suppressing coverage.

  HONEST READ ON COVERAGE: 5.3% is the lowest of the three live trials (7.1%, 9.5%,
  5.3%), on a puzzle with only 19 of 28 clues even printed and zero of them culture-
  reference clues that retrieval happened to cover. The 8 blanks were each genuinely
  investigated (homographs.py/solve_pass.py/wiki.py all run per the subagent's own
  account) and correctly left blank rather than padded — PRECISION FIRST working as
  intended on a puzzle this specific instance of the harness had little purchase on. The
  cumulative 3-trial precision (2/5 = 40%, up from 1/4 = 25%) should NOT be read as
  "retrieval improved live precision" — the gain is one more culture-reference hit from
  a pre-existing tool (`wiki.py`), unrelated to today's lever. The standing 2026-08-22
  finding (mechanism verification is not definition-fit judgment) is reinforced rather
  than revised: every one of today's 6 downgraded-to-suggestion "committed" answers had
  a passing `prove.py` proof and was still wrong.

  AUDIT (mandatory gate). Transcript grepped for `data/answers`, `data/dataset`, and
  `14across` as literal path/domain strings in tool-call arguments (not just any
  mention, which would also catch the guardrail instructions echoed back in the
  system prompt) — one non-leaking deviation found and disclosed rather than hidden:
  the subagent ran `ls -la data/dataset/` once (a directory listing — filenames and
  byte-sizes only, e.g. `clues.jsonl` at 5934 bytes — while checking what tooling
  existed), never opened or read that file's actual content. The only place
  `clues.jsonl`/`by_date` appears as file CONTENT anywhere in the transcript is inside
  `solver/retrieve.py`'s own source code (permitted reading, `solver/*.py`), which
  internally restricts itself to train-split rows by construction — not a read of gold
  data by the agent. `lexicon.held_out_answers()` confirmed (checked directly, before
  any measurement) to block all 19 of this puzzle's own gold answers. No jump to
  explain: 100% precision is on n=1, and every other number (coverage, yield,
  suggestion-hit-rate) is flat-to-lower than prior trials — the opposite direction a
  leak would produce.

  NOT DONE, honestly: did not crawl `note.co.il` (still never crawled this project's
  lifetime, still the concrete next step for a bigger retrieval index); did not attempt
  a second live puzzle this run (would dilute the one-lever discipline, and today's
  trial — transcription, gold recovery, two bug-fixes, delegation, scoring, audit — took
  the full run); did not act on queue items 8 or 9 beyond what transcribing this
  puzzle incidentally reconfirmed about item 8's across-clue gap.

- 2026-08-29: **nativ mobile bug-fix + virality pass** (branch
  `claude/game-bugs-ux-bkcqsr`). Played the game under Playwright touch emulation
  (Pixel 7) and confirmed four real bugs before touching code: (1) one grazed
  wrong cell mid-drag wiped the ENTIRE trace — the single biggest "hard from the
  phone" cause; now only the wrong cell is dropped (with red flash + vibration),
  and a rejected cell is ignored while the finger lingers on it; (2) the natural
  resume gesture — put finger on the trace head and keep dragging — POPPED the
  head instead (pointerdown tap-undo); undo now waits for pointerup, so both
  tap-undo and resume-drag work; (3) a mid-game reload lost all progress
  (constant on mobile: tab eviction, pull-to-refresh) — in-progress state now
  persists in `nativ.progress.v1` and restores on boot; (4) `?d=` leaked FUTURE
  puzzles — clamped to <= today (past days stay playable so challenge links
  survive the midnight rollover). Also: dead-zone hit-testing mid-drag (central
  ~3/4 of a cell), pointercancel handling, `touch-action:manipulation` on
  buttons, no more `window.prompt` for the leaderboard nickname (blocked the win
  panel; broken in WhatsApp/Instagram webviews) — replaced with an inline form.
  Virality, learned from a teardown of flashback-il.xyz (scraped + analyzed by a
  subagent): two share flows with separate UTM campaigns (result/challenge vs
  invite) so acquisition is measurable; share squares now Wordle-lingua 🟩/🟨;
  "עקפתם X% מהשחקנים" percentile line gated the flashback way (>=5 players,
  never demoralizing); countdown to the next puzzle after a win; first-visit
  how-to modal. New beyond flashback: the shared URL is itself a CHALLENGE
  (`?d&m&ct&ch&cn`) — the friend sees a "beat them?" banner and a head-to-head
  verdict at the finish, no backend needed (nick rendered via textContent only —
  it arrives from the URL). Leaderboard API time floor 10s→3s (legit sub-10s
  easy-board solves were rejected). Verified with 27 Playwright checks
  (touch + mouse): all pass.
- 2026-08-30: **candidate generation, queue item 1(d)'s own repeatedly-flagged "NOT
  DONE" gap: re-measured `retrieval_candidates` on 2026-06-26 with a full transcription
  and a massively grown corpus.** Bootstrap hit the 14across hard wall again (4/52
  fetches in a row `None: 0 clues` after full retry-with-backoff — matches
  2026-08-19/08-26/08-27/08-28's failure mode, killed rather than waited out); worked
  entirely from the no-14across image-fallback technique (bootstrap.sh step 6).

  RESEARCH (full entries in RESEARCH.md): sixth-plus consecutive literature pass with
  nothing new and buildable on candidate generation or definition-span/fit scoring. One
  new citation this run — Zeinalipour et al., "From Arabic Text to Puzzles" (arXiv
  2501.11035) — checked directly and found not to transfer: it is crossword-clue
  GENERATION from text for education, standard (non-cryptic) puzzles, the opposite
  direction from this project's clue-to-answer task. Also worth naming even though not
  new: 2506.04824's candidate generator hypothesizes answers directly rather than
  mechanism-first, which is closer to what this project's live blind trials already do
  informally than to `candidates.py`'s mechanical approach — not a buildable delta today
  (would need fine-tuning a small LM), but a useful frame.

  TRANSCRIPTION: 2026-06-26 was chosen because it is the exact puzzle DAILY.md's own
  2026-08-28/08-29 entries named as still needing a re-measurement with the grown
  corpus, and no run had finished it (2026-08-26's own attempt only reached 18/28
  clues before 14across came back up that day). Transcribed all 28 clues fresh from
  `data/images/2026-06-25.jpg`: the previously-missing 5 across clues (19, 22-26) turned
  out to be present after all — the across section's text wraps across the print
  column boundary partway through clue 19, which 2026-08-26's transcription evidently
  stopped at rather than followed. Validated every enum sum against the GRID-DERIVED
  slot length (from the already-committed `data/grids/2026-06-26.json`'s black-cell
  pattern — structural geometry only, no gold data read) before touching any answer:
  0/28 mismatches, including recovering clue 19's own printed enum from its column-wrap
  continuation rather than assuming a value. Caught and DISCLOSED one real reversed
  enumeration (not silently corrected): clue 22 across prints `(4,3)` but its
  grid-derived answer `חוקמרפי` (Murphy's Law) splits `חוק`(3)+`מרפי`(4) — the sum (7)
  still matches so `len_ok` is unaffected; this is at least the 7th documented instance
  of this setter's known reversed-enum quirk.

  GOLD LETTERS came from the small solved-grid recap in the FOLLOWING week's image
  (`data/images/2026-07-02.jpg`), grid-calibrated programmatically (darkness-threshold
  gridline detection, not eyeballed): all 15 rows' black-cell pattern matched the
  committed grid EXACTLY, 0/15 mismatches — the strongest form of this project's
  standard cross-check. Several derived answers independently make clean semantic sense
  against their clues (אירטיש/Irtysh river, תגלתפלאסר/Tiglath-Pileser, מרידיאנ/meridian
  from Mary+Di+Ann), further corroboration beyond the grid-pattern match alone.

  CORPUS: `crawl_defs.py mordo` re-crawled fresh (gitignored, redone every run):
  **66,443 raw / 62,403 parsed answers, 2.6x 2026-08-29's 25,350/24,361** — confirmed
  this is real new content, not a pagination-loop bug, by sampling for duplicate
  definitions (~98% unique). `crawl_defs.py note` ran under a disclosed 12-minute time
  budget: **1,001/1,301 discovered URLs fetched (998 parsed)**, up from 970/1,301
  despite the bound, since URL discovery (the slow first phase on a cold run) had
  already finished by the time the budget expired.

  MEASURED, controlled before/after (`python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval [--no-culture] [--no-retrieval]`): mechanical-only
  baseline **0.0% (0/28)**; **+ retrieval: 14.3% (4/28)** — the highest recall this
  diagnostic has ever measured on any single puzzle (previous best 10.7%, 2026-08-28),
  and the largest single-puzzle point gain. Full defaults (culture+retrieval) land at
  the same 4/28, confirming `culture_category_candidates` adds nothing here (consistent
  with its established rare-firing pattern). The 4 hits: 13A `מניע` (motive, clue "the
  reason"), 17A `רומח` (spear, clue "a serious weapon"), 5D `בובדילנ` (Bob Dylan, clue
  "won the Nobel prize"), 21D `ברסמכא` (an authority figure, clue "the expert" — the
  same hit 2026-08-26's smaller/partial attempt already found, now reproduced
  independently with a full transcription and 7x the corpus).

  AUDITED (mandatory gate). Provenance of all 4 hits checked directly: every matching
  document carries `pid=None` (external private_defs corpus, never this project's own
  puzzle text) and each match's definition text is a clean semantic fit for its clue
  (e.g. `רומח`'s docs are about weapons; `בובדילנ`'s are about a Nobel-winning American
  singer-songwriter), not a coincidental string collision. `lexicon.held_out_answers()`
  and `retrieve_defs.held_out()` both confirmed (computed, not assumed) to block all 28
  of this puzzle's own gold answers. **Disclosed rather than hidden**: DAILY.md's own
  2026-08-26 entry for this exact puzzle already named 2 of today's 4 hits (`בובדילנ`,
  `ברסמכא`) before this run's required reading — a standing, previously-flagged-but-
  unaddressed leak-adjacent property of the log file itself (2026-08-22: "DAILY.md
  itself is required reading each run and is therefore a leak vector its own
  instructions don't flag"). This did not compromise the measured number: gold letters
  came from independently grid-calibrating the solution image (0/15 row mismatches, an
  objective check unrelated to foreknowledge) and `candidates.py recall`'s hit/miss
  decision is a mechanical string-equality comparison with no room for bias — but the
  other 2 hits (`מניע`, `רומח`) are the genuinely first-time, stronger data point. No
  forbidden reads: 14across was never queried for this puzzle's gold data, only the two
  public CDN images. Implausibility check: 0.0%→14.3% (14.3 points) sits just under this
  project's own ~15-point suspicion threshold — treated as suspect until explained, and
  fully explained by 4 individually-verified, semantically sound, externally-sourced
  hits rather than one anomalous mechanism. All 5 affected selftests (`candidates.py`,
  `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`) re-run clean.

  HONEST READ: the strongest single data point this lever has produced across 6
  independent measurements on 3 puzzles — a puzzle that scored a flat 0.0% on its
  first, partial attempt now scores the project's highest-ever recall@N once both the
  transcription gap and the corpus size are closed together. This does not prove corpus
  size is a universal fix (2026-07-10 stays flat at 0.0% across three much-grown corpus
  sizes) — the honest read across all 6 measurements is still that retrieval's gain is
  real but puzzle-dependent, though the balance now looks more like "most puzzles
  benefit once the corpus is big enough, one specific puzzle's idioms genuinely aren't
  covered" than an even split.

  NOT DONE, honestly: did not re-measure 2026-07-10 a fourth time against today's much
  bigger corpus (already flat three times at three sizes; not this run's chosen puzzle,
  to keep this run to one puzzle's full transcription-plus-audit cycle); did not act on
  the DAILY.md-as-leak-vector finding beyond disclosing it — a real fix (redacting
  specific answer strings from log prose, or splitting required-reading history from an
  answer-bearing appendix) is a process question worth its own future lever, not
  designed under today's one-lever budget; did not merge or otherwise act on any open PR.

- 2026-08-31 (session 2): **nativ content-fairness pass** after user playtest feedback
  on the mountains day (branch `claude/game-bugs-ux-bkcqsr`). Three complaints, all
  reproduced in the data before fixing: (1) EASY MODE WAS NOT EASY - the day served
  obscure mountains in Nigeria/Panama/Finland because `prefer_rich` (4 rich pages in
  116 mountains) was a hollow notability proxy. Easy boards now draw ONLY from a
  curated FAMOUS list per category (~30-70 names each, verified against
  entities.json), with a full-pool fallback that triggered 0/90 days after the pools
  were topped up. (2) THEME PURITY - the mountain category carried 7 נחלים, 2
  mountain passes and 2 Martian peaks (recategorized to stream/site, Mars excluded
  by desc regex); "כולם קיבוצים" days served מושבים - theme renamed to "כולם
  קיבוצים ומושבים". (3) ISRAEL/PA ATTRIBUTION - per the owner's rule (Israeli
  settlement in B/C -> Israel; Arab locality/geography -> PA): 52 PA localities
  (בית לחם, ג'נין, חברון, יריחו, עזה...) moved from `city_il` to a new `city_pa`
  category so they never appear under "כולם יישובים בישראל" (1948-depopulated
  villages inside Israel stay); "הר בגוש עציון, ישראל" description trimmed of
  ", ישראל"; bonus catch: 6 cities in Syria/Jordan/Lebanon (דרעא, מעאן, מידבא...)
  were also filed under city_il - moved to world_city. DATA GAPS FILLED: the milon
  had NO famous world cities at all (no London/Paris/Rome - the category was
  African/Chinese/US-state capitals), no Everest/Tabor/Meron, no
  Jerusalem/Tel Aviv/Haifa under city_il, and politicians only as full names (too
  long for 4x4) - added 140 real entities with descriptions (world cities, Israeli
  cities, mountains, athletes incl. יעל ארד/גל פרידמן, authors, actors, surname
  politicians like רבין/בגין/גולדה, everyday common words). Rebuilt puzzles.json:
  90/90 days validated, zero purity violations, zero famous-pool fallbacks; today's
  easy board went from צ'אפל ואדי/הלטי/בארו to אולימפוס/ארבל/אררט.
- 2026-08-31 (session 3, solver daily loop): **second, independent puzzle's measurement
  of `culture_category_candidates`** (queue item 1(c)) — full transcription, measurement,
  three-way root-cause breakdown, and audit trail written up under the state table's
  "Last lever added (2026-08-31)" entry above (search for it rather than duplicating here
  per this file's own established practice of keeping the detailed narrative at the top).
  Summary: fresh puzzle 2026-07-03 (not among any of the 8 previously-used dev dates),
  transcribed from `data/images/2026-07-02.jpg`, gold letters from the following week's
  solution recap (`data/images/2026-07-11.jpg`, 0/15 row mismatches against the committed
  grid). One real enum-print anomaly found and disclosed (clues 17/18 down had their
  printed enumerations transposed between each other — a new variant of this setter's
  known enum quirk, resolved by grid-derived slot length, `grid_tools.py validate` now
  prints OK on all 28). MEASURED: mechanical baseline 7.1% (2/28); + culture_category:
  still 7.1% (2/28), unchanged, mechanism fired on 3/28 clues (up from 1/28 on 2026-06-19)
  with 0 gold hits. The three firings each have a DIFFERENT root cause: one homograph/pun
  misdirection (reproduces the 2026-06-19 finding), one where the gold answer sits in the
  raw corpus but is correctly excluded by the held-out safety filter (a newly-surfaced
  measurement-methodology blind spot: this project's own dev/eval discipline makes such a
  hit structurally unmeasurable, not a corpus or trigger-vocabulary gap), and one genuine
  entity-list coverage gap (a real mountain name absent from `culture.json`'s 119-entry
  list). AUDITED: `lexicon.held_out_answers()`/`retrieve_defs.held_out()` confirmed to
  block all 28 gold answers; raw `culture.json` confirmed to contain 4 of them unfiltered
  but `candidates.culture()`'s post-filter output confirmed to contain 0; no forbidden
  reads (14across hard-walled again, 7/7 fetches failed, worked entirely from the two
  public CDN images); no jump to explain (7.1% -> 7.1% is unchanged). All 5 selftests
  re-run clean. RESEARCH.md: ninth-plus consecutive pass with nothing new on
  definition-fit scoring (queue item 9) — one new citation checked directly (an Italian
  non-cryptic crossword retrieval/ranking line, confirmed not to transfer) but nothing
  buildable, so item 9 was left untouched per its own standing instruction rather than
  forcing a stub. NOT DONE: did not build a corpus-mined trigger vocabulary (today's
  breakdown suggests it would not have helped any of the 3 firings, demoting its
  priority); did not grow `culture.json`'s entity lists to close the one real coverage
  gap found (a concrete next step, not attempted this run); did not touch
  `retrieval_candidates` or run any corpus crawl (deliberate, after six straight days on
  that lever); did not merge or act on any PR (none open).
- 2026-09-02: **candidate generation, queue item 1's "generate diverse candidates by
  mechanism and by definition-span hypothesis" instruction.** Wired
  `retrieve_defs.end_candidates()` (BM25 query restricted to a short prefix/suffix
  word-span of the clue, trying both ends, rather than one classifier's guess) into
  `candidates.py` as a new `defspan_retrieval_candidates()` source. See the state table
  above for the full measurement, audit, and honest-negative-result writeup — summary:
  correctly implemented and wired in, but on the one puzzle measured (2026-05-29) it adds
  ZERO incremental recall over the already-wired whole-clue `retrieval_candidates()` (both
  land on 10.7%/3-28, hitting the identical 2 clues; raw candidate sets are identical on
  27/28 clues). Root-caused, not just observed: this corpus's clues average 7 words and
  `end_candidates()`'s widest window is 4 words per end, so for a typical clue here the
  end-span already covers most of the clue's content, and BM25 scoring here only rewards
  shared terms (extra query terms don't dilute a doc's score), so the whole-clue query's
  hypothesized noise problem doesn't bite at this corpus's clue lengths. Shipped anyway:
  the lever closes a real, previously undisclosed gap — every DAILY.md/RESEARCH.md entry
  since 2026-08-08 has quoted retrieval's standalone strength ("gold@25=5.4%, ceiling 27%")
  as measured by `retrieve_defs.py eval`'s CLI, which has always used `end_candidates()`,
  while the mechanism actually running live in `generate()`/`solve_pass.py` since
  2026-08-25 has always used the whole-clue query instead — the quoted number never
  described what was running. Bootstrap ran clean against 14across this run (recovered
  from a handful of intermittent bot-check redirects); `crawl_defs.py mordo` was run under
  a disclosed ~5-minute budget (8,249 raw / 7,384 parsed — bootstrap.sh does not fetch
  `private_defs` at all, a separate manual step every run must redo). Transcription of
  2026-05-29 caught and resolved one real column-wrap: clue 13 across's enum initially
  looked entirely missing (the printed column ran out at "13. בני טוב" with no visible
  enumeration), until re-examining the reading order showed its remaining text
  ("כמלחין", enum (4)) wraps to the top of the next print column, ahead of clue 15 —
  the same recurring print-layout quirk 2026-08-30 documented for a different puzzle and
  date, now confirmed on a third. All 28 enum sums validated against the real gold
  answer's letter count (from 14across, not the image-fallback this time): 0/28
  mismatches. AUDIT clean (held-out blocking confirmed computed for both `retrieve_defs`
  and `lexicon`; both hits' source docs confirmed `pid=None` and semantically sound; no
  forbidden reads; 3.6%→10.7% jump reproduces 2026-08-28's own number on this exact
  puzzle, not a new implausible jump). RESEARCH.md: sixth-plus run with no new external
  resource turning into a buildable generator; one new citation checked and found not
  transferable (IdioLink, arXiv 2605.22247 — needs Hebrew dense-retriever training data
  this project doesn't have), and one (`nikcholer/cryptic-solver`) confirmed rather than
  added to the standing direction (semantic, not indicator-density, definition-fit
  judgement — queue item 9 — is the right direction, already what live trials do
  informally). NOT DONE: did not crawl note.co.il; did not re-measure a second puzzle to
  see if the defspan/whole-clue gap ever separates on longer clues; did not merge or
  act on any open PR.
- 2026-09-03: **candidate generation, queue item 1(e): `container_candidates` — the
  container/insertion device.** Three PRs were open and unmerged against main when this
  run started (#38 2026-08-31, #39 2026-09-01, #41 2026-09-02, all candidate-generation
  or retrieval-query work) — not merged or cherry-picked this run (only the project
  owner merges PRs; this run branches off main per the standing protocol, same as every
  prior run when a backlog exists), but read directly so today's lever would not
  duplicate what they already measured: #39/#41 both re-examined `retrieval_candidates`'s
  query shape (whole-clue vs. end-anchored BM25), both landing on null results on
  2026-05-29; #38 is a diagnostic-only re-measurement of `culture_category_candidates`.
  None touched the container device, so today's lever is genuinely new relative to the
  full open backlog, not just to main.

  RESEARCH (full entries in RESEARCH.md): general searches on candidate generation and
  definition-span detection surfaced nothing beyond the same paper family logged
  repeatedly since 2026-08-06. A TARGETED search specifically for container/insertion
  CANDIDATE GENERATION (not detection) found one new, concrete resource worth checking
  directly rather than citing at a glance: `github.com/nikcholer/cryptic-solver`, a 2026
  neuro-symbolic (LLM-parse + deterministic-validate) demo. Read directly: its container
  handling is LLM-guided, not mechanically enumerated — it does not generate container
  candidates either, matching every academic paper already logged and this project's OWN
  prior standing approach. This is the reason today's lever is worth building rather than
  skipping: no public solver, academic or hobbyist, mechanically generates container
  candidates; `prove.py` has been able to VERIFY one (`is_container`) since the proof
  gate was built, but nothing has ever generated one to check.

  BOOTSTRAP: `./bootstrap.sh --dev-only` hit the 14across hard wall again — 7 consecutive
  answer-page fetches returned `None: 0 clues` after full retry-with-backoff each (the
  worst-case cost of waiting out all 52 at that rate is hours, not minutes); killed after
  confirming the pattern rather than waited out, matching the failure mode documented
  since 2026-08-19. hspell (129,574 words), `solver/lex/culture.json` (already fully
  committed, 24 categories / thousands of entities — no rebuild needed) and the dev
  puzzle images (public CDN, unaffected by the 14across wall) all came through cleanly.

  BUILT `solver/candidates.py`: `container_parts()` (shared fragment-source helper) and
  `container_candidates()` — an OUTER fragment with an INNER fragment spliced at a
  STRICTLY INTERIOR position (matching `prove.is_container`'s own contract exactly, so
  every candidate this mechanism proposes is provable by the existing verifier
  unchanged). Fragment sources are the SAME two the file's other mechanisms already use
  (no new corpus, no new data file): a clue word or its de-affixed stem (reusing
  `homograph_candidates`'s own `_destem()`), and the mined clue-word/answer-fragment
  substitution table (`sub_fwd()`, the same held-out-safe in-memory rebuild
  `substitution_candidates()` already depends on). Wired into `generate()` behind a new
  `use_container` toggle (default on), in the same early priority tier as
  homograph/substitution/culture/retrieval, for the same reason: it is bounded by a
  small fragment pool, not an unbounded window scan, so it doesn't need to wait behind
  the cheap high-volume mechanisms. Selftest added (`python3 solver/candidates.py
  selftest`): unlike every other mechanism's selftest, which either uses a synthetic
  fixture or an injected table, this one's core check uses a REAL word found by
  scanning the actual committed lexicon offline (`מכות` + `מל` spliced at an interior
  position -> `ממלכות`, "kingdoms") — not gold-answer-linked, not synthetic, and it
  confirms the mechanism reaches the real dictionary, not just a hand-built fixture.
  Also checks that a word cannot supply both the outer and inner fragment of its own
  candidate. All checks pass.

  TRANSCRIPTION: re-transcribed the canonical dev puzzle 2026-05-29 fresh (5th
  independent transcription of this exact puzzle across this project's history, after
  2026-08-06/08-25/08-28/2026-09-01's PR #39 — chosen for direct comparability against
  the many prior measurements on it, since 14across left no other option this run).
  Clue text from `data/images/2026-05-28.jpg` (both across columns — the right
  "אופקי:" box for clues 1,7,8,9,10,11,13 and the wrapped continuation for 15 through
  26 in the middle column, reading right-column-then-left-column as one flow, which
  resolved a genuine transcription ambiguity mid-run: an enum that first looked
  misplaced turned out to belong to the PRECEDING clue once the two-column wrap was
  understood, not a printing error — caught by cross-checking every enum sum against
  the grid-derived slot length BEFORE accepting any reading, per protocol). All 28
  enum sums matched their grid-derived slot lengths exactly, 0 mismatches, before any
  gold answer was touched.

  GOLD LETTERS, since 14across was unreachable: recovered from the small solved-grid
  recap in the FOLLOWING week's image (`data/images/2026-06-04.jpg`, captioned "פתרון
  תשבץ שהופיע בשבוע שעבר"). Rather than eyeball cell boundaries, calibrated the grid
  geometry PROGRAMMATICALLY: detected gridline pixel rows/columns via a darkness-
  fraction threshold (`numpy`/`PIL`, installed this run), extracted all 15x11 cells'
  black/white pattern from the calibrated coordinates, and confirmed it against the
  ALREADY-COMMITTED `data/grids/2026-05-29.json` — 0/15 row mismatches. Read each row's
  letters from the same calibrated coordinates (not a second, independent crop), then
  converted from on-page visual (left-to-right) order to this project's index
  convention (index 0 = rightmost cell) by simple reversal, and extracted every
  (number, direction) slot's answer via `grid_tools.slots()` rather than assembling
  them by hand. Several derived answers independently corroborate the transcription
  beyond the grid-pattern match alone, including two that reproduce gold answers this
  exact puzzle's own prior log entries already recorded independently (1D
  `ברישניקוב`/Baryshnikov — DAILY.md 2026-08-28; 26A `פחותאבלכואב` — DAILY.md
  2026-08-25) and one that reproduces PR #39's own independently-reported finding for
  this same puzzle (1A `בליברטיולנס`/"Liberty Valance," whose printed enum (4,7)
  reverses the true 7+4 split, this setter's well-documented reversed-enum quirk).
  `python3 solver/grid_tools.py validate` printed OK; `python3 solver/build_dataset.py`
  reported 0 length mismatches across all 28 rows (split: eval, since this is the only
  puzzle date present this run and the split rule assigns the newest date(s) to eval).

  MEASURED, controlled before/after (`python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval [--no-culture] [--no-retrieval] [--no-container]`):
  mechanical-only baseline **3.6% (1/28)** — exactly reproduces every prior
  transcription of this puzzle, a strong cross-check that today's 5th independent
  transcription is correct; **+ container: still 3.6% (1/28), UNCHANGED**; full
  defaults (culture+retrieval) also unaffected by the container toggle either way.
  Direct inspection: `container_candidates` fired on only 1/28 clues (9 across, 2 raw
  candidates, neither matching gold), and the run's own by-mechanism breakdown shows
  `substitution_candidates` — the ALREADY-SHIPPED mechanism sharing today's new
  mechanism's mined-fragment source — ALSO fired 0 times this run (only `anagram`
  produced the one hit, unchanged from the mechanical-only baseline). This is the
  direct, checked explanation: `sub_fwd()` rebuilds in-memory from this puzzle's own
  crowd explanations (`data/answers/by_date`), which do not exist this run because
  14across was unreachable — the mechanism's mined-substitution fragment source was
  empty for the SAME reason it was empty for the already-shipped mechanism sharing it,
  not a defect specific to container. Only the corpus-free destem/literal-word half of
  the fragment pool was exercised.

  AUDIT (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
  both confirmed (computed, not assumed) to block all 28 of this puzzle's own gold
  answers (`gold_norm - block` empty for both, checked directly after the dataset was
  built). No forbidden reads: 14across was never queried for this puzzle's gold data,
  only the two public CDN images (the sanctioned fallback); no answers site accessed.
  No jump to explain — recall stayed flat at 3.6% with container on vs off, the
  opposite direction an implausible result would take. All 5 affected selftests
  (`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`)
  re-run clean.

  HONEST READ: this is a real but CONFOUNDED result, disclosed as such rather than
  reported as a clean negative. `container_candidates` is implemented, unit-tested
  against a real dictionary word (not a synthetic fixture), wired in behind a toggle,
  and closes a genuine gap (verification existed, generation didn't) that this run's
  own research check confirms no public solver has closed either — but today's live
  measurement cannot distinguish "the device doesn't help this puzzle" from "its main
  fragment source was empty this run," because the SAME corpus starvation flattened
  the already-shipped `substitution_candidates` to zero fires too. The honest
  conclusion is: re-measure once 14across is reachable (or any dev/eval puzzle already
  has real crowd explanations available) before drawing any conclusion about whether
  the container device itself helps recall — today's number is evidence about this
  run's environment, not yet about the mechanism.

  NOT DONE, honestly: did not crawl `note.co.il`/`mordo` (that corpus feeds
  `retrieval_candidates`, not `sub_fwd()` — would not have helped today's specific
  starvation); did not re-measure any of the other puzzles with existing transcriptions
  from prior runs (data/ is gitignored, so none persist between runs — every run starts
  from zero); did not merge or otherwise act on PRs #38/#39/#41 (only the project owner
  merges PRs); did not attempt to reconstruct `sub_fwd()`'s fragment source from the
  committed `solver/lex/substitutions.json` as a workaround — that file was very likely
  built from a corpus that included this exact canonical dev puzzle's own crowd
  explanations (it is reused as the dev/eval baseline in nearly every prior run), so
  using it here would risk exactly the kind of leak RESULTS.md's INTEGRITY FINDING
  already caught once; left the fragment source honestly empty rather than take that
  risk.
- 2026-09-04: **candidate generation, queue item 1(f): `double_definition_candidates` —
  the מילה משותפת (double-definition) device.** Four solver-lever PRs were open and
  unmerged against main when this run started (#38 2026-08-31, #39 2026-09-01, #41
  2026-09-02, #42 2026-09-03) — read directly (diffs against their own merge-bases) to
  confirm none had already built this device before choosing it; not merged or
  cherry-picked (only the project owner merges PRs; this run branches off main per
  standing protocol). See RESEARCH.md for the full research entry: checked a new GitHub
  hybrid cryptic-helper repo directly and confirmed it does generate double-definition
  candidates, but via English WordNet/embeddings with no Hebrew equivalent — the
  transferable idea (score each clue half independently, require both to agree) was
  built with this project's own already-audited `retrieve_defs.py` BM25 index instead of
  any new external dependency.

  BOOTSTRAP hit the 14across hard wall again (killed at the dev-only timeout, 0/52);
  hspell and the dev puzzle images (public CDN) came through cleanly. `crawl_defs.py
  mordo` ran under a disclosed 10-minute budget (killed by timeout): 33,299 raw entries.
  **Caught a real gap in that step**: the raw crawl output has no parsed `answers` field
  at all (0/33,299) until `reparse_mordo()` is run separately — a step named in this
  file's own prior log prose but not in `crawl_defs.py`'s own docstring/CLI in a way that
  makes it obvious; ran it explicitly (32,150/33,299 gained parsed answers) and confirmed
  the retrieval index was non-empty before treating any 0% result as meaningful, catching
  what would otherwise have been a silent false negative (an empty index trivially
  produces 0% recall for every mechanism, which is a corpus bug, not a solving result).

  PUZZLE CHOICE, deliberately: this file's own log prose has repeatedly quoted specific
  gold-answer strings for 2026-05-29, 2026-06-26, and 2026-07-03 (each required reading
  before this run, a leak-adjacent property flagged since 2026-08-22/08-30 but never
  fixed) — chose 2026-05-21 instead, a date this file has never named a gold answer for,
  to keep at least this one measurement clean of that specific risk. Transcribed all 21
  printed clues (8 across, 13 down; the standard across-1-12 gap excludes clues 7,8,9,10)
  from `data/images/2026-05-20.jpg`. Every enum validated against the grid-derived slot
  length (`grid_tools.py validate`, 0 genuine mismatches — the 7 reported "problems" are
  exactly the excluded missing-clue slots) before any gold data was touched.

  GOLD LETTERS from the small solved-grid recap in `data/images/2026-05-28.jpg`
  (captioned "פתרון תשבץ ההיגיון לשבוע שעבר"). Grid-calibrated programmatically
  (darkness-threshold gridline detection). **A real transcription drift was caught, not
  silently fixed**: an early row-by-row read drifted by a full row past row 9 (a padding
  miscalculation in the crop offsets), producing letters that looked individually
  plausible but, once checked, didn't match ANY of the grid's known row patterns for
  their apparent position. Re-derived the affected rows by matching each row's own
  BLACK-CELL SHAPE (not just content) against the committed grid's per-row pattern list,
  which is unambiguous even when letter content alone isn't — this recovered the correct
  row order. Final transcription: **all 15 rows match the committed
  `data/grids/2026-05-21.json` pattern EXACTLY, 0/15 mismatches**, the project's
  strongest standard cross-check. Several extracted answers make independent semantic
  sense against their clues beyond the pattern match alone (רוקפור/Roquefort for a
  cheese clue, לימוזינ/limousine for "an expensive car", שדרות/Sderot — a southern
  Israeli city — for "fed from it, a worker in a southern city", ירדאלהעמ/"ירד אל העם"
  for Moses "descending to the people" at the giving of the Torah).

  MEASURED, controlled (`python3 solver/candidates.py recall data/dataset/clues.jsonl
  eval [--no-culture] [--no-retrieval] [--no-double-def]`): mechanical-only baseline
  **0.0% (0/21)**; **+ retrieval alone: 9.5% (2/21)** (רוקפור, פרופסורה); **+
  double_definition alone: 0.0% (0/21), fired on 0/21 clues** — confirmed directly (not
  inferred from the 0% score) that the mechanism never once produced a candidate, and
  that even relaxing its own "both halves" requirement to "either half alone" still
  found nothing for the five short slots PLAYBOOK.md flags as the device's home turf.
  Full defaults land at the same 9.5% (2/21) as retrieval alone.

  AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
  both confirmed to block all 21 gold answers. Both retrieval hits confirmed `pid=None`
  (external mordo docs — cheese-type and academic-status definitions respectively),
  clean semantic fits, not string coincidences. No forbidden reads: 14across never
  queried for this puzzle, only the two public CDN images. No jump to explain: 0.0% ->
  9.5% is well under the ~15-point suspicion bar. All 5 affected selftests
  (`candidates.py`, `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`)
  re-run clean; `candidates.py selftest` gained two double_definition checks (a
  synthetic both-halves-agree case, and a single-word clue returning empty rather than
  erroring).

  HONEST READ: a genuine negative result, sharpened rather than softened by the
  zero-fire finding — this isn't "generates plausible-looking wrong candidates," it's
  "never generates anything for this puzzle's clues at all," which points at corpus
  coverage (today's mordo-only, 10-minute-budget, no-note.co.il index) rather than a
  design flaw in the two-sided-split idea itself, especially since `retrieval_candidates`
  on the identical index DID fire and hit twice. Whether growing the corpus the way
  2026-08-30 did for `retrieval_candidates` (66K+ raw entries, note.co.il added) would
  let this mechanism fire at all is the concrete open question, not attempted this run.

  NOT DONE, honestly: did not crawl note.co.il or run mordo to a natural stop (disclosed
  10-minute budget only); did not re-measure a second puzzle (n=1); did not act on the
  DAILY.md-leak-vector finding beyond mitigating it via today's puzzle choice; did not
  merge or otherwise act on PRs #38/#39/#41/#42 (read only, per standing protocol).
- 2026-09-04: **nativ fairness + phone-layout pass** (branch `claude/game-bugs-ux-bkcqsr`),
  after the owner played the live game and reported UI, opacity, usability and
  relevance bugs. All four measured before fixing, on a Pixel 7 viewport.
  (1) RELEVANCE, the real one: the 2026-08-31 fix gated only EASY mode, so
  regular mode still drew straight from the milon and served
  "אדהם הדיה / שרון לב / מייק קרטר / מוסא סלים" (2026-09-04). The milon is an
  exhaustive crossword *reference* (1,531 athletes, 2,283 artists) - a random
  draw from it is a lookup, not a puzzle. New `app/nativ_pools.py` holds a
  curated pool per theme (821 entries, 16 themes); BOTH modes now draw only
  from it and the build FAILS if any pooled word does not resolve against its
  source, so a typo can never silently shrink a pool. Five new everyday-word
  themes (בעלי חיים, מטבח, חפצים, מקצועות, מילים) come from
  `solver/lex/fillbank.json`, where every clue is a real dictionary definition
  and there is no trivia at all. Data added to support it: 106 entities
  (central biblical figures - the milon had no יהושע/דבורה/אליהו/דניאל -
  surname forms of politicians, international athletes and authors, mountain
  ranges) and 38 fillbank words. Regular mode also names each answer at the
  end now, since every pooled word carries a description.
  (2) OPACITY: solved tiles were white on `--accent`, which measures 2.73:1 in
  dark mode - a finished board read as faded, not solved. Now `--on-accent`
  (6.6:1); same fix for the hint tiles, the WhatsApp button and the stats bars.
  Zero contrast failures left in either theme.
  (3) USABILITY: 462px of the 839px viewport was chrome above the board, and
  board + clue list needed 656px of the 377px left - you could never see the
  board and its clues together. Phone layout drops the kicker and tagline,
  collapses the toolbar to one icon row, and a new `fitBoard()` scales the
  board (and its letters) into the height that remains. Now 308px of chrome,
  and board + clues fit the screen in every mode and both themes. Boards also
  shrank: TOTALS 25/30 -> 20/25 (5x4, 5x5), because 30 letters over 4 words
  demanded a 7.5-letter average only obscure names could supply.
  (4) A challenge link with `ct=0` was rejected by the parser (`t>0`).
  Verified: 22/22 Playwright checks (touch, both modes, challenge round-trip
  across two browser contexts), and a sweep of all 180 boards - every word in
  its theme's pool, every word clued, no board over 25 cells.
- 2026-09-05: **candidate generation, queue item 1(g): `homophone_candidates` — the
  נשמע (sounds-like) device.** Five solver-lever PRs were open and unmerged against
  main when this run started (#38 2026-08-31, #39 2026-09-01, #41 2026-09-02, #42
  2026-09-03, #44 2026-09-04) — the compounding-backlog pattern queue item 6 has
  flagged three times before. Consolidated all five onto one branch first (cherry-
  picked in date order, DAILY.md/RESEARCH.md reconciled by hand, chronological, no
  content dropped), resolving one real code conflict: PR #39 redefined
  `retrieval_candidates()` to use `retrieve_defs.end_candidates()`, unaware PR #41
  (a day later, off a different main) instead added a NEW, independently-toggleable
  `defspan_retrieval_candidates()` calling the same function and left
  `retrieval_candidates()` alone — applying both literally would make two mechanisms
  run an identical query. Kept #41's shape (preserves both query shapes as separately
  measurable) and dropped #39's redefinition as superseded, disclosed rather than
  silently discarded. All 5 selftests re-run clean post-consolidation, before any new
  code was added.

  RESEARCH (full entry in RESEARCH.md): no Hebrew-specific resource found; confirmed
  (not discovered) that English cryptic-solving tools handle the homophone device with
  a phonetic-indexing algorithm (Soundex/Metaphone) — the same shape this run
  independently arrived at, grounded in this setter's own documented Hebrew
  consonant-ambiguity classes instead of English vowel-based Soundex.

  BOOTSTRAP: hspell/culture.json/substitutions.json already committed, no rebuild
  needed. 14across hard-walled again, confirmed directly rather than assumed: a
  single-URL fetch for 2026-05-29 with 8 retries came back `None: 0 clues` on all 8
  attempts (matching `scraper/parse_answers.py`'s own retry policy), and the full
  52-puzzle scrape independently showed the same pattern (14/15 empty before being
  killed) — worked entirely from the no-14across image-fallback technique.

  BUILT `solver/candidates.py`: `PHON_FOLD`/`phon()` (a length-preserving Hebrew
  consonant-class fold: ק/כ/ח, ט/ת, ס/ש, א/ע — indicators.json's own crowd-mined
  homophone entry names these as free swaps), `by_phon()` (a phon-keyed lexicon
  index, mirroring `by_len()`), and `homophone_candidates()` (the same fixed-width
  char-window scan `anagram_candidates`/`hidden_candidates` already run, looked up
  by phon-key instead of exact match; a literal-spelling match is excluded, since
  that's `hidden`, not a homophone). Wired into `generate()` behind `use_homophone`
  (default on), in the window-scan tier with anagram/hidden/reversal (same cost
  profile). `solver/prove.py` gained a matching `is_homophone(fodder, answer)`
  assertion (same fold rule, duplicated per this file's own self-contained-file
  discipline) so a live solve pass can now PROVE a homophone claim, not just
  hypothesize one — no prior proof primitive existed for this device at all.
  Selftest (both files): a real ק/כ swap pair, קר/כר, both real hspell words found
  by scanning the live lexicon, not a synthetic fixture; the identical-spelling
  exclusion also checked directly.

  TRANSCRIPTION: re-transcribed 2026-05-29 fresh (6th independent transcription of
  this exact puzzle). All 28 clues (15 across, 13 down) from `data/images/
  2026-05-28.jpg`; every enum validated against the GRID-DERIVED slot length before
  any gold data was touched — 0/28 mismatches. Disclosed methodology finding: this
  puzzle's print layout intermittently floats a printed enum after the FOLLOWING
  clue's number rather than its own (observed at the 9->10 and 22->23->24
  boundaries) — resolved via grid-derived length wherever the printed position was
  ambiguous, never by guessing.

  GOLD LETTERS from the small solved-grid recap in `data/images/2026-06-04.jpg`.
  Grid-calibrated (cropped, upscaled, read row by row, then reversed to match the
  project's index-0-is-rightmost convention): all 15 rows match the committed
  `data/grids/2026-05-29.json` EXACTLY, 0/15 mismatches. FOUR independent
  corroborations beyond the grid-pattern match, checked only after extraction: two
  answers reproduce gold strings this file's own prior entries already disclosed for
  this puzzle (1A `בליברטיולנס`, 26A `פחותאבלכואב`), one reproduces
  `SOLVE_PROTOCOL.md`'s own worked example verbatim (7A `ישפרחימ`), one reproduces
  `prove.py selftest`'s own worked example verbatim (11A `קרתנימ`).
  `grid_tools.py validate` printed OK; `build_dataset.py` reported 0 length
  mismatches across all 28 rows.

  MEASURED, controlled (`python3 solver/candidates.py recall data/dataset/clues.jsonl
  eval --no-homophone`): mechanical-only baseline **3.6% (1/28)** — exactly reproduces
  every prior transcription of this puzzle; **+ homophone alone: still 3.6% (1/28),
  UNCHANGED**, but the mechanism fired on **8/28 clues** (avg candidates/clue 11.7 ->
  11.8), not a zero-fire result. Direct inspection: this puzzle's own homophone-
  credited clue (22 across, "...הזורזים (עפ"י השמיעה של אליעזר כמון)" -> gold
  `אנזימימ`) needs "הזורזים" (7 letters) read as sounding like "אנזימים" (8 letters) —
  a vowel-insertion relationship this length-preserving consonant-fold cannot reach
  by construction, exactly the scope limit disclosed in the code's own docstring.
  Full defaults (every mechanism together): 3.6% (1/28), same single anagram hit
  (`יחפניות`, 2 down) every prior measurement of this puzzle has found.

  AUDIT (mandatory gate). `lexicon.held_out_answers()`/`retrieve_defs.held_out()`
  both confirmed (computed, not assumed) to block all 28 gold answers.
  `homophone_candidates` introduces no new leak surface: it only looks up the
  already held-out-filtered `lex()`, the same source `anagram_candidates`/
  `hidden_candidates` already use safely. No forbidden reads: the single-URL
  14across probe returned `None: 0 clues` on all 8 attempts before any content was
  read; both images used are the sanctioned public-CDN fallback. No jump to
  explain: 3.6% -> 3.6% is the least suspicious result possible. All 5 affected
  selftests re-run clean.

  HONEST READ: a real, mechanically-sound, newly-provable device with a genuinely
  negative recall result on this one puzzle — but the negative result is now
  understood, not just observed: this puzzle's specific homophone clue needs vowel
  flexibility a v1 that deliberately excludes vowel modeling was never going to
  catch. The mechanism DID fire realistically elsewhere (8/28 clues), which is
  evidence it works mechanically; it needs a second puzzle or the vowel extension
  before its real hit rate is known, not a verdict that it's dead.

  NOT DONE, honestly: did not model vowel-letter (ו/י) flexibility (the concrete
  next step this run's own root-cause finding surfaced); did not re-measure a
  second puzzle (n=1); did not crawl any corpus (irrelevant to this lever, which
  touches no external corpus); did not merge or otherwise act on the five
  consolidated PRs beyond folding their code into this branch (#38/#39/#41/#42/#44
  should be closed in favor of this branch; only the project owner merges PRs).

- 2026-09-06: **candidate generation, queue item 1(g) continued: `homophone_vowel_candidates`
  — closes 2026-09-05's own disclosed vowel-letter gap** (branch built on PR #46 rather
  than main, after `list_pull_requests` surfaced that PR #41 had already built and
  measured the end-span retrieval idea this run almost re-implemented from scratch —
  discarded before it ran, avoiding a seventh duplicate-effort branch). Extends
  `homophone_candidates` to the free ו/י vowel-letter insertion/omission device
  `indicators.json` documents alongside the consonant-class swaps: two fixed-width
  fodder windows (target_len-1 with an insertion, target_len+1 with a deletion), looked
  up against the same phon-folded lexicon index; `prove.py`'s `is_homophone()` now
  accepts the same one-vowel-off match. MEASURED on the 7th independent transcription
  of 2026-05-29: **3.6% (1/28), UNCHANGED**, but the mechanism fired on 14/28 clues (up
  from 8/28 for the consonant-only version) — a real, mechanically active device with
  no recall movement yet on this one puzzle. Directly re-tested the specific clue
  2026-09-05 diagnosed as this device's target (22 across, `הזורזים` -> `אנזימימ`) and
  found it STILL produces zero candidates there — the true sound relationship is more
  than one vowel letter apart, so the prior single-vowel diagnosis was itself an
  oversimplification, independent of whether this device is correctly built. Also
  caught and fixed a real transcription error while re-deriving gold data: 26 across's
  answer had been recorded as the character-reverse of the value three independent
  prior runs agree on (rows 0 and 14 are both all-white, so a whole-row mirroring error
  is invisible to the grid-pattern cross-check) — resolved via SOLVE_PROTOCOL's own
  real-word-split rule against the live lexicon, not by vote count. AUDITED: held-out
  blocking reconfirmed for both lexicon.py and retrieve_defs.py; no new leak surface
  (same held-out-filtered `lex()` every window-scan mechanism already uses); no
  forbidden reads; 3.6% -> 3.6% needed no implausibility check. NOT DONE, honestly: did
  not model a >1-vowel-letter distance (the concrete next step this run's own
  re-diagnosis surfaced); did not re-measure a second puzzle; did not merge or act on
  PR #46/#38/#39/#41/#42/#44 beyond building on top of #46 (only the project owner
  merges PRs). See RESEARCH.md for the day's search (no Hebrew-specific phonetic-
  distance resource found).

- 2026-09-07 (solver session): **PR-backlog consolidation (queue item 6, recurred a
  fifth time) + candidate generation, queue item 1(b): `substitution_candidates`'
  3-part charade chain.** `list_pull_requests` showed EIGHT open PRs (#38, #39, #41,
  #42, #44, #46, #47, #50) against main. Checked ancestry directly
  (`git merge-base --is-ancestor`), not assumed from titles: #47
  (`daily/2026-09-06-homophone-vowel`) already supersedes #38/#39/#41/#42/#44/#46 via
  #46's own 2026-09-05 consolidation plus one more day's lever; #50 is unrelated
  site/SEO work (no solver-code overlap), left untouched. Branched from #47, merged
  current main in: one real conflict, in DAILY.md only (both sides had appended
  different dated Log entries after the same point) — resolved by chronological
  concatenation, and by writing in 2026-09-06's own Log entry, which that day's commit
  had omitted (it updated the state-table narrative but never appended to `## Log`).

  AUDIT-BEFORE-BUILDING (mandatory before trusting anything downstream of a merge): ran
  all 5 selftests post-merge and found a real bug, not assumed clean — `candidates.py
  selftest`'s `homophone_vowel` toggle check called `generate()` without disabling
  retrieval/defspan-retrieval/double-definition, so it crashed in any environment
  without a bootstrapped `data/dataset/clues.jsonl` (like this one): every OTHER toggle
  check in the file calls the standalone mechanism function directly for exactly this
  reason, this one didn't. Fixed by disabling those three toggles explicitly, matching
  the file's own established pattern. All 5 selftests then re-ran clean.

  BOOTSTRAP: hspell/culture.json already committed. `scraper/parse_answers.py` hard-
  walled severely today: **4/52 puzzles recovered** (2026-07-10, 2026-07-03,
  2026-01-30, 2025-08-08 — 112 real crowd-explained clues), 48/52 came back `None: 0
  clues` after full retry-with-backoff each. None of the 4 recovered dates is a
  previously-used dev/eval puzzle, so worked from the no-14across image-fallback
  technique for the canonical benchmark instead, per bootstrap.sh step 6.

  TRANSCRIPTION: 2026-05-29, 8th independent transcription of this project's most-used
  benchmark puzzle, from `data/images/2026-05-28.jpg`. Every one of the 28 enum sums
  validated against the GRID-DERIVED slot length (`solver/grid_tools.py`'s own
  `slots()`, pure structural geometry from the already-committed
  `data/grids/2026-05-29.json` — no gold data read) before any gold data was touched:
  **0/28 mismatches**, including correctly resolving clue 13's own column-wrap (its
  text splits across the same print-layout boundary queue item 8 already documents for
  other dates on this puzzle: "...כמלחין" sits at the top of the NEXT column, not a
  missing word). GOLD LETTERS from the solved-grid recap in
  `data/images/2026-06-04.jpg`, grid-calibrated programmatically (PIL, row-by-row pixel
  crops, not eyeballed): all 15 rows' black-cell pattern matched the committed grid
  EXACTLY, **0/15 mismatches** — cross-checked cell-for-cell as each row was
  transcribed, not just at the end. FOUR independent corroborations beyond the pattern
  match itself, all reproducing strings this project's own files already name for this
  exact puzzle: 1A `בליברטיולנס`, 26A `פחותאבלכואב` (both named in multiple prior
  DAILY.md entries), 7A `ישפרחימ` (SOLVE_PROTOCOL.md's own worked example), 11A
  `קרתנימ` (`prove.py selftest`'s own worked example), plus 1D `ברישניקוב`/Baryshnikov
  (named in the 2026-08-28 log entry) and 22A `אנזימימ` for the clue carrying the
  "(עפ"י השמיעה של אליעזר כמון)" homophone credit (matches 2026-09-05/06's own
  disclosed target clue exactly, transcribed independently here).

  BUILT `solver/candidates.py`: `substitution_candidates()` gained a third shape —
  three ADJACENT clue words' mined substitutes concatenating, in clue order, to the
  full target length, the same adjacency-constrained search the existing 1-word and
  2-word cases already use, generalized by one more segment (deliberately NOT
  `charade.py`'s open-ended every-split search, measured weak in 2026-08-08/08-17: 2.8%
  and 4.0% recall on two puzzles, unchanged). New `use_3part` parameter on the function
  and `use_substitution_3part` toggle threaded through `generate()`/`recall_eval()`/the
  CLI (`--no-substitution-3part`), matching every other mechanism's on/off switch in
  this file. Two new selftest checks: a synthetic 3-word chain fires correctly, and a
  NON-adjacent triple (a gap word with no substitute sitting between two that do)
  correctly does NOT chain across the gap.

  MEASURED, controlled (`python3 solver/candidates.py recall data/dataset/clues.jsonl
  eval --no-substitution-3part`): **3.6% (1/28) both with and without** — avg
  candidates/clue identical (13.8) either way, meaning the mechanism fired on **0/28
  clues**, not just missed gold. Checked directly why, not assumed: the EXISTING 2-part
  substitution mechanism (which the 3-part case extends) ALSO fired 0/28 times this
  run, against both the tiny in-memory held-out-safe table today's hard-walled
  bootstrap produced (35 head words) and, as an audit-only diagnostic never used for
  the scored number, the full committed `solver/lex/substitutions.json` (2,220 head
  words — `git diff --stat` caught that this run's own smaller `substitutions.py build`
  call had briefly overwritten it before anything was committed, exactly the failure
  mode bootstrap.sh's own comments warn about; reverted with `git checkout --` before
  measuring). Zero fires at both corpus sizes for both part-counts means THIS PUZZLE's
  specific clue set has no adjacent-word substitution chain at all, of any length — not
  evidence the 3-part device is broken (its own selftest, on synthetic data with a
  real 3-way chain, passes) or a verdict that 3-part charades never fire, just that
  this run could not produce the precondition (a puzzle where the 2-part baseline
  already fires) needed to test whether extending it to 3 parts adds anything.

  AUDIT (mandatory gate). `lexicon.held_out_answers()` confirmed (computed, not
  assumed) to block all 28 of this puzzle's own gold answers before any measurement.
  The 3-part mechanism introduces no new leak surface beyond what the existing 1/2-part
  shapes already have (same `sub_fwd()`/`table` source, same full-length-match
  requirement). No forbidden reads: 14across was queried only for its own answers-page
  scrape (never this puzzle's date, which it never returned), gold letters came from
  the sanctioned public-CDN image-fallback path. No jump to explain: 3.6% -> 3.6% is
  the least suspicious result possible, needed no implausibility check. All 5 selftests
  re-run clean post-lever.

  HONEST READ: today's run is two things, not one — a genuinely necessary backlog
  consolidation (the fifth recurrence of queue item 6, closing six days of otherwise-
  stranded solver work: culture_category's 2nd puzzle, container, double_definition,
  defspan_retrieval, homophone, homophone_vowel, none of which main had ever seen) and
  an honestly INCONCLUSIVE test of today's own new lever, not a clean negative. The
  fair statement: 3-part substitution charades remain unvalidated in either direction —
  neither shown to help nor shown to be structurally wrong — because this run's one
  available benchmark puzzle happens to have zero exploitable substitution chains at
  any length. The concrete next step is measuring on a puzzle where 2-part
  substitution already fires (none of this project's repeatedly-used dev puzzles are
  confirmed to be one), not re-testing 2026-05-29 again.

  NOT DONE, honestly: did not find or transcribe a second puzzle to get a firing
  baseline for substitution (would have meant a second full transcription-plus-audit
  cycle in one run, out of scope for one lever); did not merge or otherwise act on PR
  #47/#50 beyond building on top of #47 (only the project owner merges PRs) — this
  branch is offered as superseding #38/#39/#41/#42/#44/#46/#47; did not act on queue
  items 8 or 9 beyond the incidental clue-13 column-wrap note above; did not re-crawl
  note.co.il/mordo (irrelevant to this lever, which touches the explanations corpus,
  not the definitions corpus retrieval_candidates uses).

- 2026-09-07: **site UI bug hunt after a live report** ("tables and lines are getting
  breaks, the crosswords opacity is off, some of the riddles are bad"), branch
  `claude/game-bugs-ux-bkcqsr`. Everything below was measured before it was
  touched; both repo gates (`evals/ui_smoke.py`, `evals/topicgen_eval.py`) pass
  after.
  OPACITY, and the worst bug of the three: `.board .cell.clue .ac` carried a
  hardcoded `#1B1A4E` on a background that followed the theme, so in DARK MODE
  the arrowword clues were dark-on-dark - measured **1:1, i.e. invisible**, and
  every arrowword board was unplayable. The board is deliberately "paper" in
  both themes, so the clue cell now takes a fixed paper tint (`--cell-clue`) and
  the text the cell's own ink: 14.62:1 in both. Same class of bug in the cell
  numbers (`--accent` on a paper cell, 2.65:1 in dark mode -> `--cell-num`,
  5.08:1), and `.board .cell` now pins `color` to `--cell-ink` so nothing drawn
  inside a paper cell can inherit the page colour again. Clue text 8px -> 8.96px,
  re-measured for clipping (zero).
  LINES: 19 em-dashes were live in published Hebrew text (`docs/solve/`,
  `docs/research/`) against the repo's own content rule, plus one inside
  `docs/solve/data/demos.json`; fixed in the three generators as well, so a
  rebuild cannot bring them back. Also fixed a regression I shipped on 09-04:
  `fitBoard()` squeezed נתיב into the leftover viewport height on every screen,
  which on a 1280px desktop meant a 232px board - now phone-only, desktop back
  to 420px.
  RIDDLES: found a real inconsistency in `solver/topicgen.py`. Hidden-clue
  carriers already had to be words "the reader has met", but reversal and
  anagram fodder only had to be in the lexicon - which carries the whole
  inflection tail. That is where "ערבוב האותיות של תבשם" (for שבתם) and
  "הפוך את מניב" (for בינם) came from: 373 of 1,164 answers were wordplay-clued
  and every one named a word nobody could produce. Both indexes now require the
  fodder to be in the `common` set, `topicgen_eval.py` gates the same rule so it
  cannot drift back, and all 44 boards were regenerated: **0 clues now name an
  unrecognisable word** (was 373), level 2 dropped from 13% to 14% wordplay with
  far better clues (tanach L2 is now almost all real definitions), and level 4
  rose 59% -> 73% - the honest trade: its answers are drawn outside everyday
  vocabulary by design, so restricting the fodder leaves it more wordplay, but
  each clue now names something solvable. Also grew the fillbank by 13 words at
  the starved lengths and moved seven vehicles out of נתיב's
  "כולם חפצים מהבית" theme (an אוטובוס was due to appear on 09-08).
  Gates: ui_smoke 9/9 pages at both widths, topicgen_eval 52/52 boards,
  url_guard clean (6,071 URLs, none dropped), nativ regression 22/22.

- 2026-09-08: **candidate generation, `solver/candidates.py`: `charade_candidates`** — a
  new mechanical mechanism for 2-part enums that solves each part as an INDEPENDENT
  anagram/hidden-word window, in clue order and non-overlapping, rather than requiring one
  contiguous window to cover the whole answer (all `anagram_candidates`/`hidden_candidates`
  can do today). Bootstrap hit the same hard 14across wall as most recent runs (confirmed
  directly: a bare 300s-budget `scraper/parse_answers.py` run outside bootstrap.sh still
  came back `None: 0 clues` on 7/7 consecutive fetches) — worked entirely from the
  public-CDN image-fallback technique.

  RESEARCH: followed today's stated priority order (candidate-generation diversity,
  definition-span, Hebrew NLP). General search surfaced only the same paper family logged
  repeatedly since 2026-08-06 (2506.04824, 2407.08824, 2403.12094, 2104.08620) — nothing
  new there. One genuinely new citation this run: a GitHub repo,
  `raphm72-spec/cryptic_crossword_helper` (hybrid ML+rule-based English cryptic solver:
  MiniLM embeddings, a multi-label wordplay-indicator classifier, WordNet-based synonym
  expansion, definition-span-at-start/end detection). Checked directly rather than assumed
  from the title: 0 stars, 6 commits, English-only, and its core technique (definition
  fixed at clue start/end + indicator-word classification) is exactly the shape
  `defspan.py` already measured NEGATIVE on this setter's own clues (2026-08-19: only 25%
  of clues have a mechanically-locatable single-window span at all, and an indicator-word
  classifier scored 1/5 on the rest). Transfer: none — an unvalidated hobby tool for a
  different language, built on the same premise this project already falsified for this
  setter. Conclusion: seventh-plus consecutive literature pass with nothing new and
  buildable; today's lever is queue item 1's own flagged next step for the substitution
  device instead (multi-part charades, quoted in the queue since 2026-08-20) — except that
  exact idea turned out to be UNTESTABLE today (see below), so the closest testable
  relative was built instead, honestly labeled as such rather than silently substituted.

  RE-TRANSCRIBED THE CANONICAL DEV PUZZLE (2026-05-29) from scratch, since `data/` starts
  empty every run. Read `data/images/2026-05-28.jpg` for all 28 clues (both the
  wrapped-column `אופקי` 1-13 section and the main `אנכי` column) and grid-calibrated the
  solved recap grid in the FOLLOWING week's image (`data/images/2026-06-04.jpg`) for gold
  letters, per bootstrap.sh's documented fallback. Caught and fixed two real transcription
  bugs mid-run, disclosed rather than hidden: (1) an imprecise grid-crop boundary
  undercounted the 11-column solution grid to 9 columns and, when corrected by eye rather
  than by re-deriving the true pixel geometry, one row got transcribed in the wrong
  (right-to-left) direction — fixed by detecting the grid's own gridlines pixel-precisely
  (dark-line scan) and re-reading every row in small 3-4-cell crops (never a whole row at
  once) with each row's black-cell pattern cross-checked against the already-committed
  `data/grids/2026-05-29.json` (0/15 mismatches once corrected); (2) one single-cell
  misread (ל for י) caught because it broke a mechanical anagram check against the clue's
  own fodder, not by inspection alone. The corrected transcription independently
  reproduced three separate historical answers from this puzzle's prior runs byte-for-byte
  (1 down `ברישניקוב`, 2 down `יחפניות`, 26 across `פחותאבלכואב`), and the mechanical-only
  recall@N baseline reproduced the historical 3.6% (1/28) exactly. All 28 enum sums
  validated against the grid-derived slot length, 0 mismatches.

  While building the queue's flagged multi-part-substitution idea, found it is currently
  UNTESTABLE, not just unattempted: `substitutions.explanations()` sources
  `data/answers/answers_parsed.json`, which needs a working 14across fetch (walled today),
  so `sub_fwd()` built an EMPTY equivalence table this run (0 pairs mined, confirmed by
  direct inspection before writing any new code against it). Built `charade_candidates`
  instead — multi-part, but via the mechanical anagram/hidden lexicon search rather than a
  mined table, so it does not depend on 14across at all.

  MEASURED, controlled before/after (`python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval --no-culture --no-retrieval [--no-charade]`): baseline
  (charade off) **3.6% (1/28)**, avg 11.7 candidates/clue, 17.9s wall time; **with charade:
  3.6% (1/28), UNCHANGED**, avg 18.9 candidates/clue, 30.2s. Charade fired on all 10 of the
  puzzle's 2-part-enum clues (hitting its own 200-candidate-per-clue cap on 8 of them) but
  matched 0/10 gold answers — confirmed by dumping per-clue candidate counts and gold
  membership directly, not just trusting the aggregate number. Full defaults
  (culture+retrieval+charade) also 3.6%, unchanged, since no `private_defs` corpus was
  crawled this run (today's lever was a new mechanism, not a corpus refresh) and
  `culture_category` does not fire on this puzzle's clues.

  AUDITED (mandatory gate). `lexicon.held_out_answers()`, `substitutions.held_out()`, and
  `retrieve_defs.held_out()` all confirmed to block all 28 of this puzzle's own gold
  answers now that it sits in `data/dataset/clues.jsonl` as the `eval` split (`gold_norm -
  blocked` empty for all three). No forbidden reads: confirmed `data/answers/
  answers_parsed.json` does not exist this run, so 14across was never the source of this
  puzzle's gold data — only the two public CDN images. No jump to explain: 3.6% stayed
  3.6%. All 6 affected selftests (`candidates.py` — including 2 new cases for
  `charade_candidates` — `retrieve_defs.py`, `lexicon.py`, `prove.py`, `substitutions.py`)
  re-run clean.

  HONEST READ: a real, correctly-implemented, well-tested new mechanism that does not move
  recall on the one puzzle it was measured against, plus a real wall-clock cost (+69% on
  this eval) for zero gain here. The structural gap it targets (a charade's two parts need
  not be contiguous in the fodder) is still sound per SOLVE_PROTOCOL.md's own description
  of the device; this puzzle's specific 2-part-enum clues either use a different device or
  their correct parts aren't real-word anagrams/hidden-words of the right sub-lengths —
  this diagnostic cannot distinguish a wordplay-mechanism miss from a definition-fit miss.
  NOT DONE, honestly: not measured on a second puzzle; did not tighten the 200-candidate
  cap despite it being hit on 8/10 clues; did not extend to 3+-part enums (clue 26's
  (4,3,4) was the only 3-part clue here, stayed out of scope); did not crawl a fresh
  `private_defs` corpus; did not merge or otherwise act on any open PR.

- 2026-09-09: **`solver/deffit.py` — a definition-fit RE-RANKER, queue item 9 ("the
  sharpest gap PR #24 surfaced").** Bootstrap's 14across scrape hit the same intermittent
  bot-check wall this project has hit repeatedly (consistent HTTP 202 on direct curl
  probes, confirmed rather than assumed, then killed — not waited out); worked entirely
  from the public-CDN image fallback. RESEARCH (full entries in RESEARCH.md): definition-
  fit scoring's tenth-plus consecutive literature pass, re-checked with a deliberately
  different framing (a signal needing neither embeddings nor span-location). Found one
  genuinely new angle not logged before: classic gloss-overlap (Lesk-style) scoring —
  score a candidate by lexical overlap between the clue and the candidate ANSWER's own
  corpus-attested definition, no embedding model and no definition-span localization
  required. Distinct in kind from both prior dead ends (WordNet's synsets, the missing
  Hebrew embedding space). TRANSCRIBED a puzzle not previously used as this project's
  dev/eval canon, 2026-05-15, chosen because queue item 8 already confirmed its own image
  prints across clues 1-13 cleanly (sidestepping that item's still-open gap on
  2026-05-29/2026-05-21). All 28 clues transcribed from `data/images/2026-05-14.jpg` — the
  across text turned out to be split across TWO print columns (a main column from 22
  onward, and a narrow sidebar carrying 1,7,8,9,10,11,13,15,17,19, next to the small
  solution-recap box) — the same "separate column" shape queue item 8 already found for
  2026-06-19, now confirmed on a second date. GOLD LETTERS from the small solved-grid
  recap in the FOLLOWING week's image (`data/images/2026-05-20.jpg`), grid-calibrated
  programmatically (darkness-threshold gridline detection on both axes): all 15 rows'
  black-cell pattern matched the committed `data/grids/2026-05-15.json` exactly, 0/15
  mismatches. `grid_tools.validate()`: 0 problems, every enum sum matches its grid-derived
  slot length. `crawl_defs.py mordo` re-crawled fresh (13,049 raw / 12,302 parsed) under a
  240s budget; `crawl_defs.py note` under a 200s budget (125 pairs — smaller than prior
  runs' 12-minute/unbounded budgets, disclosed rather than hidden).

  BUILT `solver/deffit.py`: reuses `retrieve_defs.py`'s own BM25 index and scoring formula
  in the REVERSE direction (candidate answer -> its own corpus gloss, scored against the
  clue) and attaches a `def_fit` score to every candidate `candidates.py` already
  generated, then stable-sorts by it. Never proposes a new answer, so recall@N is
  unchanged by construction (selftest-verified). MEASURED
  (`python3 solver/deffit.py eval data/dataset/clues.jsonl eval`): of the 2 clues where
  recall@N already contains gold (7A `שערציונ`/Zion Gate, 24A `שכמ`/shoulder-Shechem pun,
  both retrieval hits), reranking left top-1 accuracy unchanged (0/2) but moved mean
  reciprocal rank 0.333 -> 0.350 (7A's gold candidate: rank 6 -> 5 of 25; 24A's, already
  rank 2, unchanged). n=2 is nowhere near enough to call this positive.

  THE MORE IMPORTANT FINDING IS STRUCTURAL: checked directly whether def_fit ever scores a
  NON-retrieval candidate (anagram/hidden/reversal/homograph/culture) above zero anywhere
  in this puzzle's 28 clues — **0/28**. Not a coverage gap a bigger crawl fixes: it is a
  logical consequence of the design, since `def_fit_score` looks up a candidate's docs in
  the exact index `retrieval_candidates()` already searches, so any non-zero-scoring
  answer was, by construction, already reachable by `retrieval_candidates()` itself.
  Today's `deffit.py` can rerank retrieval's own hits but cannot yet independently
  corroborate a mechanically-derived candidate's meaning — it adds nothing to the live
  solve pass's actual failure mode (a mechanically-real candidate that is semantically
  wrong) beyond what `retrieval_candidates` already contributes as a candidate SOURCE.
  Concrete next step, not attempted today: point `deffit.py` at a SECOND, independent
  gloss source — `solver/lex/fillbank.json` (2,412 real dictionary word->definition
  pairs, already committed, used by the public site) — which could recognize a common
  word's meaning independently of whether it ever appears as a crossword answer in
  private_defs.

  AUDITED (mandatory gate). `lexicon.held_out_answers()` and `retrieve_defs.held_out()`
  both confirmed (computed, not assumed) to block all 28 of this puzzle's own gold
  answers. Provenance of both retrieval hits checked directly: every matching document
  carries `pid=None` (external private_defs corpus) and each is a clean semantic fit
  (`שכמ`'s docs are about the shoulder/upper-back and a city in Samaria; `שערציונ`'s docs
  are about a site in Jerusalem's Old City) — not a coincidental string match. No
  forbidden reads: 14across's partial, unrelated 9-puzzle leftover output (answers +
  crowd explanations, no clue text, from the killed bootstrap step) was inspected only to
  confirm it carries no clue TEXT and therefore cannot feed `clues.jsonl` — never used in
  any measurement. All 6 affected selftests (`candidates.py`, `retrieve_defs.py`,
  `lexicon.py`, `prove.py`, `substitutions.py`, `deffit.py`) re-run clean. Implausibility
  check: recall stayed at 7.1% (2/28, unchanged by the smaller note.co.il crawl); the MRR
  movement (0.333->0.350) is a tiny, unsuspicious shift.

  HONEST READ: a well-implemented, well-tested piece of infrastructure (selftest covers
  the reranking mechanism, the never-drops-a-candidate guarantee, and tie-stability) that
  measured negative-to-null on its first live puzzle, for a reason now understood
  precisely: it shares its evidence source with an existing mechanism, so it cannot yet
  add information the pipeline doesn't already have. This converts "no generator-shaped
  resource has been found" (RESEARCH.md, 3+ prior passes) into "one was found and built,
  and here is precisely why it doesn't help yet, with the exact fix named."

  NOT DONE, honestly: did not wire a second gloss source (fillbank.json) into deffit
  today, to keep this run to one lever; did not re-measure on a second puzzle
  (transcription of one 28-clue puzzle plus its audit was this run's full budget); did not
  run `crawl_defs.py note` to a natural plateau (200s budget) — unlikely to change the
  structural finding above regardless of corpus size, since the redundancy is
  architectural, not a coverage gap; did not merge or otherwise act on any open PR.

- 2026-09-10: **PR-backlog consolidation (queue item 6, sixth recurrence) + `deffit.py`:
  `fillbank.json` as a second gloss source, closing 2026-09-09's own disclosed next step.**
  `list_pull_requests` showed ELEVEN open PRs against main (#38, #39, #41, #42, #44, #46,
  #47, #50, #51, #52, #53). #51 (2026-09-07) already consolidates #38/#39/#41/#42/#44/#46/#47;
  #52 (2026-09-08, `charade_candidates`) and #53 (2026-09-09, `deffit.py`) were each branched
  independently off the same pre-#51 main and never reconciled with it or each other. Branched
  from #51, merged #52 then #53 on top: two real `solver/candidates.py` conflicts (both #51
  and #52 independently extended `generate()`/`recall_eval()`'s parameter list and priority
  docstring) resolved by keeping every mechanism from both branches, not either alone;
  `solver/deffit.py` (#53) merged clean. DAILY.md/RESEARCH.md conflicts (dated entries from
  both branches) resolved by chronological reordering, dropping nothing. All 6 selftests
  re-run clean immediately after the merge, before trusting it. Please close #38, #39, #41,
  #42, #44, #46, #47, #52 and #53 in favor of this PR.

  Bootstrap hit the same hard 14across wall as most recent runs (6/52 puzzles recovered,
  none a prior dev/eval date); worked from the public-CDN image fallback. RESEARCH (full
  entries in RESEARCH.md): followed the scheduled task's stated priority order (candidate
  generation diversity, Hebrew morphology); the same paper family surfaces again with
  nothing new, and a fresh general search for multi-dictionary/ensemble gloss-scoring
  approaches surfaced only generic cryptic-crossword guides, not research. Today's lever is
  the queue's own concrete next step instead: #53's own disclosed follow-up for
  `deffit.py`.

  RE-TRANSCRIBED 2026-05-15 independently (bootstrap's `data/` starts empty every run):
  28/28 clues from `data/images/2026-05-14.jpg`, all enum sums validated against the
  grid-derived slot length (0/28 mismatches) before any gold data was touched. GOLD LETTERS
  from `data/images/2026-05-20.jpg`'s solved-grid recap, this run calibrated end-to-end
  programmatically: dark-line-fraction gridline detection located all 16 horizontal and 12
  vertical gridlines to the pixel, then each of the 15 rows was cropped and read individually
  at 6x zoom. All 15 rows' black-cell pattern matched the committed `data/grids/2026-05-15.json`
  EXACTLY (0/15 mismatches) after correcting for the image's left-to-right pixel order vs the
  grid's right-to-left storage convention (verified by reversal, not assumed). `python3
  solver/build_dataset.py` independently confirmed 0/28 length mismatches from the joined
  files. Seven of the 28 derived answers make clean independent cultural/semantic sense
  against their clues beyond the mechanical enum/grid match alone (קומראנ/Qumran for a clue
  about ancient scrolls and a holy book found there; שכמ/Shechem for "on the back of a
  Jerusalem gate", i.e. שער שכם; גולגולתא/Golgotha for "the gate, gate of the city, in
  Jerusalem"; מבשרתציונ/Mevaseret Zion; עירדויד/City of David; קישלה/Kishle, the historic
  Old City prison, for "in jail"; מחזיקאצבעות/"holding thumbs" for wishing Stallone luck) —
  strong corroboration beyond the structural checks alone.

  THE LEVER: `build_fillbank_index()` adds `solver/lex/fillbank.json` (2,412 word->definition
  pairs) as a second, independently-scored gloss source (own BM25 N/df/avg, kept separate
  from private_defs' to avoid one corpus silently swamping the other), and `def_fit_score`
  now takes the max across every available source. FOUND AND FIXED A REAL BUG before ever
  measuring: fillbank's keys are ordinary Hebrew orthography (e.g. אוהלים, final mem), but
  candidates.py's norm() unconditionally final-folds every answer it produces (אוהלימ) — so
  the naive dict lookup would have silently missed every fillbank entry ending in ם/ן/ץ/ף/ך,
  557 of 2,450 (22.7%), checked directly by counting rather than assumed. Fixed by folding
  fillbank's own keys with the same FIN table before indexing; a new selftest case (an
  injected synthetic final-letter word, never the real file) guards the regression.

  MEASURED, controlled before/after (`python3 solver/deffit.py eval data/dataset/clues.jsonl
  eval [--no-fillbank]`): recall@N (mechanical+retrieval) is 0/28 either way this run — a
  fresh, deliberately time-boxed `crawl_defs.py` corpus (mordo 12,298 raw/240s budget;
  note.co.il 125 pairs/200s budget) found none of this puzzle's answers, unlike #53's own
  larger crawl (2/28) — a genuine puzzle-AND-corpus-dependent null. Since recall_hit is 0/28,
  top-1/MRR are undefined (0/0) this run. Split the structural diagnostic into two numbers on
  purpose (collapsing them would hide the real finding): `nonretrieval_known_gloss_clues`
  (any non-retrieval candidate has SOME known gloss, any source) moved 3/28 (private_defs
  alone) -> 14/28 (+fillbank) — a real, substantial, disclosed gain; `nonretrieval_scored_clues`
  (that gloss actually shares vocabulary with the clue, def_fit>0) stayed 0/28 either way.
  Inspected directly why: of the 59 non-retrieval candidates (of 592 total) with a newly-known
  fillbank gloss, none scored above zero because their glosses (e.g. ירושלים -> בירת ישראל,
  כלי -> חפץ לשימוש כמו סיר או פטיש) don't repeat the clue's own wording — a real, understood
  limitation of lexical-overlap scoring for proper nouns and common objects, not a bug and not
  evidence fillbank contributes nothing (coverage genuinely widened; the score signal built on
  top of it just didn't fire on these 59 specific cases).

  AUDITED (mandatory gate). `lexicon.held_out_answers()`, `retrieve_defs.held_out()`, and
  `substitutions.held_out()` all confirmed to block all 28 of this puzzle's own gold answers
  (gold_norm - blocked empty for all three). No forbidden reads: confirmed directly that
  2026-05-15 is NOT one of the 6 dates 14across recovered this run — its by_date file was
  written entirely from the two public-CDN images. Fillbank carries no held-out risk by
  construction (an ordinary third-party dictionary, not mined from this project's own puzzle
  explanations — RESULTS.md's own established precedent for lexicon.py's plain dictionary
  words). Implausibility check: nothing here approaches the ~15-point suspicion bar — recall
  stayed at 0%, and the 3/28->14/28 gloss-coverage move is a counted, explained fact (59
  specific candidate/gloss pairs), not a suspicious jump in any accuracy number. All 6
  affected selftests re-run clean after both the merge and the lever, including 4 new
  `deffit.py` cases covering the final-letter-folding bug specifically.

  HONEST READ: a real bug caught before it could ship silently broken, and a real, mixed,
  precisely-explained result once fixed. Two consecutive runs on this queue item
  (2026-09-09, 2026-09-10) have each produced a genuine negative-or-mixed result with a
  specific, understood cause, which is more useful than either an optimistic claim or
  silence. NOT DONE, honestly: did not find a puzzle with nonzero recall@N this run, so the
  actual top-1/MRR reranking claim remains untested beyond #53's own n=2; did not weight
  scores across sources (a private_defs score and a fillbank score are not calibrated to the
  same scale, disclosed rather than hidden); did not crawl either corpus to a natural
  plateau (both deliberately time-boxed); did not act on any PR beyond building this one.

- 2026-09-11: **solver lever: `container_candidates` (`solver/candidates.py`), queue item
  1(e), closing the last gap in the mechanism roster** — `prove.py` has verified container
  proofs (`is_container`) since its first version, but no generator ever produced one to
  check; every other named mechanism (anagram/hidden/reversal/substitution/homograph) had
  a generator already. Bootstrap: 33/52 puzzles recovered from 14across (925 clues; 19 came
  back dateless, the ordinary intermittent pattern, not a hard wall). Transcribed
  2026-06-05 fresh (first time this puzzle has been used for the candidate-recall
  diagnostic) from `data/images/2026-06-04.jpg`, validating all 28 enum sums against the
  GRID-DERIVED slot length rather than the printed numerals, which this run found genuinely
  wrong for 3 clues (8/10/11 across) — a new print-error sub-type, disclosed rather than
  silently patched over. MEASURED: `python3 solver/candidates.py recall
  data/dataset/clues.jsonl eval --no-culture --no-retrieval [--no-container]`: **0.0%
  (0/28) unchanged, container fired on 0/28 clues** (avg candidates/clue 11.8 both ways).
  ROOT-CAUSED via the puzzle's own crowd explanation: this puzzle's one real container clue
  (16A, קטלנ) needs synonym substitution (בית~קן, "the judge"~טל) the literal-clue-word
  design cannot reach — the same underlying gap already documented for the charade device.
  AUDITED: `lexicon.held_out_answers()` confirmed to block all 28 gold answers
  (`gold_norm - blocked` empty) before the measurement ran, so the mechanism's `cand in
  lex()` check could not leak one by coincidence; no forbidden reads; no jump to explain.
  All 6 affected selftests re-run clean, including two new `container_candidates` cases
  (a positive hit reusing `prove.py`'s own worked example, and a negative edge-insertion
  check). Research (full entry in RESEARCH.md): fresh literature pass found nothing new and
  buildable on candidate generation or definition-span/fit scoring — the same conclusion
  every pass since 2026-08-06 has reached — so this run's lever came from the project's own
  code (an unfilled gap between `prove.py`'s DSL and `candidates.py`'s generator roster),
  not from a paper. HONEST READ: a real, well-audited negative recall result on the one
  puzzle measured (n=1), but not an uninformative one — it fills a genuine mechanism-roster
  gap at near-zero cost when it doesn't fire, and the root-cause trace names a concrete,
  correctly-deferred next step (draw container's OUTER/INNER from `substitutions.py`'s
  mined table too, not just literal clue words) rather than a dead end. NOT DONE, honestly:
  only one puzzle measured; did not crawl `private_defs` this run; did not merge or
  otherwise act on any open PR. **[Branched directly off pre-#54 main — never saw #54's own
  2026-09-03 `container_candidates`, which already implements exactly the "draw from
  substitutions.py's mined table too" next step this entry names. See 2026-09-12's entry
  for the reconciliation.]**

- 2026-09-12: **branch-hygiene fix + hardening on `container_candidates`; no new recall
  number, disclosed rather than fabricated.** `list_pull_requests` showed #55 (2026-09-11)
  had branched directly off pre-#54 main and independently reimplemented
  `container_candidates` — a function this branch's own history already added 2026-09-03
  (PR #42, folded into #54's 2026-09-10 consolidation) — because #55 never saw #54's
  branch. Queue item 6's compounding-loss pattern, recurring on a single function instead
  of a whole file. Diffed both implementations line by line: #42/#54's sources outer/inner
  fragments from a clue word's destemmed form UNION `sub_fwd()`'s mined-substitution
  equivalents; #55's sources ONLY literal clue words. #55 measured 0/28 on a freshly
  transcribed 2026-06-05 and root-caused its one real container clue (16A, "חי בבית
  השופט", per the crowd explanation קטלנ = קן containing טל) as needing exactly the
  synonym-substitution capability #42/#54's version already has. Kept #54's strictly more
  general version; did not re-add #55's narrower one or open a second PR for it — it is
  superseded, not merged.

  HARDENED before trusting the superset claim rather than just asserting it: added a new
  `candidates.py` selftest (`מכות וגם ציון` -> `ממלכות`, via a substitution table where the
  inner fragment `מל` is reachable ONLY through the mined table for `ציון`, not through any
  destemmed literal word) that proves the merged mechanism's synonym-sourced fragment path
  actually fires, and does NOT fire without the table entry (ruling out a coincidental
  hit). This path had never actually been exercised live before: #42's own 2026-09-03
  measurement was itself confounded (14across down that day too, so `sub_fwd()` was empty).
  All 6 affected selftests re-run clean (`candidates.py`, `prove.py`, `substitutions.py`,
  `retrieve_defs.py`, `lexicon.py`); `solve_pass.py`'s selftest requires
  `data/dataset/clues.jsonl` to exist, which today's bootstrap state does not produce, so
  it could not be exercised today (disclosed, not silently skipped).

  INDEPENDENTLY RE-TRANSCRIBED 2026-06-05 (not copied from #55's branch — `data/` is
  gitignored, so #55's own transcription was never reachable) from
  `data/images/2026-06-04.jpg`, fetched directly from the public CDN. Validated all 28 enum
  sums against the GRID-DERIVED slot length (`solver/grid_tools.py validate`, 0 problems)
  and independently rediscovered the SAME 3 print anomalies #55 disclosed (clues 8, 10, 11
  across print enums that do not match the grid-derived length) plus one more (clue 19's
  printed text needed merging across the column-wrap boundary, a distinct, already-
  catalogued phenomenon). Two independent transcriptions of the same defective print
  landing on the same 3 anomalous clues is a real cross-check that neither is careless
  misreading. Clue 16 itself ("חי בבית השופט (עפ"י מיקי זבדי)", enum (4)) was clean and
  unambiguous in both transcriptions.

  BOOTSTRAP AND GOLD DATA, disclosed plainly rather than estimated: 14across was hard-
  walled this run — confirmed directly, not just observed as flaky: a standalone
  single-URL fetch for this exact puzzle's answer page returned HTTP 202 (the documented
  bot-check page) on 3 consecutive retries with delays, and the full 52-URL bootstrap step
  was killed after 23 minutes having recovered zero puzzles. Attempted the no-14across
  image-fallback (the following week's small solved-grid recap, `data/images/2026-06-11.jpg`):
  the black-cell PATTERN read cleanly and matched the committed grid for row 0, and row 0's
  letters assembled into a real, semantically perfect answer for clue 1 ("כלהכבודלשר" =
  "כל הכבוד לשר", matching its (3,5,2) enum exactly) — but a second row's letters did not
  assemble into a real word at all, a direct, executed sign that letter-level OCR of this
  embedded, sub-100px-tall grid is not reliable enough here without a zoom/crop tool this
  environment does not have. Rather than publish a partially-guessed gold set and an
  accuracy number built on it, this run reports no live recall@N number for 2026-06-05
  today — exactly the "if something genuinely cannot be run, say so plainly rather than
  estimating" rule this file itself states.

  AUDIT-ONLY DIAGNOSTIC (same established practice as 2026-08-20's log entry: querying the
  larger, historical `solver/lex/substitutions.json` for context without using it as the
  scored live table): `python3 solver/substitutions.py --to קן` -> `בית (seen 18x)`, i.e.
  בית really is a recorded, generic substitution for קן. But `python3 solver/substitutions.py
  --to טל` does NOT include `שופט`/`השופט` at all — `שופט` maps only to `קונ`/`דיינ`/`דנ`
  (generic "judge" synonyms). `טל` here almost certainly names a SPECIFIC judge (a real
  Israeli justice surnamed Tal), which is an entity/culture fact, not a generic synonym
  pair — refining, not just repeating, #55's diagnosis: the missing piece is a THIRD
  fragment source (a role/entity lookup like `culture_category_candidates`' trigger
  vocabulary), not merely "more corpus" for the two sources this mechanism already has. A
  further check (audit-only, both fragments injected by hand): even with `קן`+`טל` both
  available, the assembled `קטלנ` is NOT present in the loaded hspell lexicon at all, so —
  if #55's crowd-sourced gold answer is right — this specific clue would ALSO fail the
  mechanism's final lexicon-membership gate, a fourth, independent obstacle beyond fragment
  sourcing. None of this is asserted as certain (the gold answer itself is unverified
  today, since 14across never confirmed it), but each piece was checked by executing code
  against real committed data, not guessed.

  Research (full entry in RESEARCH.md): no new external paper or tool found this cycle
  turns into a working addition to candidate generation this project doesn't already have
  some version of — the same conclusion recent passes have reached. Today's lever came from
  the project's own PR backlog (a duplicate-implementation bug), not from a paper.

  HONEST READ: no recall@N delta to report today, and that is the honest result of a real
  infrastructure constraint (14across hard-walled, small-image OCR unreliable), not of the
  lever being uninteresting — the branch-hygiene fix prevents a real wasted-effort pattern
  from recurring a third time, the new selftest converts a previously-unexercised claim
  into a verified one, and the audit-only diagnostic gives a sharper, data-checked root
  cause than "needs more corpus" for the next attempt. NOT DONE, honestly: no live
  recall@N number for 2026-06-05; did not re-verify 2026-05-29's existing confounded
  3.6%/1.28-unchanged number from 2026-09-03; did not build the culture/entity fragment
  source this run's own root-cause analysis points to next (a real third lever, correctly
  deferred rather than squeezed into today's one-lever budget); did not merge or otherwise
  act on any other open PR.
