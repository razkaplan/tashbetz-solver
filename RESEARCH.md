# Research log — daily improvement agent

One entry per run: what was found, one-line summary, and an honest judgement of whether
it transfers to a Hebrew cryptic solver with an 8k-clue corpus. Default skepticism: most
crossword-AI work targets non-cryptic (American-style) puzzles and does not transfer.

## 2026-08-06

**"A Reasoning-Based Approach to Cryptic Crossword Clue Solving"** (arXiv 2506.04824,
ICML 2025). https://arxiv.org/html/2506.04824v1
Pipeline: an LM hypothesises answer candidates + wordplay explanations, a second LM
formalises each explanation as executable code, a verifier runs it and only accepts
proofs that execute cleanly; SOTA on Cryptonite (Times/Telegraph cryptics).
**Transfer: already adopted, and only half-adopted until today.** `solver/prove.py`
already implements the verify-by-execution half of this pipeline (added in a prior
run, credited in its own docstring). What was missing was the OTHER half — the paper
generates candidates first, then verifies; this project was doing the reverse (one
hand-picked guess, then trying to justify it after the fact), which DAILY.md and
RESULTS.md both independently flagged as the measured bottleneck. Today's lever
(`solver/candidates.py`) is the direct transfer of that missing half: mechanical,
multi-mechanism candidate enumeration (anagram/hidden/reversal/pattern) so prove.py has
a list to filter instead of a single guess to rationalize. The paper's own honest
finding — "the weakest link is the wordplay 'Aha', humans still generate wordplay
current models can't" — matches this project's own diagnosis in PLAYBOOK.md that this
setter leans on substitution/homograph devices a pure mechanical generator can't invent.

**"What Makes Cryptic Crosswords Challenging for LLMs?"** (arXiv 2412.09012, Dec 2024).
https://arxiv.org/html/2412.09012v1
Studies English cryptic clues, including definition-span identification: giving a model
the correct definition span (one end of the clue) measurably improves solve accuracy,
consistent with the standard human-solver heuristic that a cryptic clue definition sits
entirely at one end. **Transfer: structurally yes, technically no.** The *structural*
claim (definition-at-one-end) already appears in this project's own
`solver/SOLVE_PROTOCOL.md` and is queue item (b), not invented by this paper — it is
independent confirmation the heuristic is worth building, not new information. The
*technical* approach (FastText-embedding similarity between a generated definition span
and candidate answers, trained/tuned on English clue corpora) does not transfer as-is:
there is no equivalent Hebrew embedding space tuned for this genre, and this project's
8,249-clue corpus is thin for training a dedicated span classifier from scratch. A
Hebrew definition-span detector here would have to be rule/heuristic-based (first N
words vs. last N words, scored by whether the OTHER end's residual parses as a wordplay
device) rather than learned — worth trying, but as a distinct, smaller lever, not a
drop-in port of this paper.

**Hebrew morphological segmentation (RFTokenizer, HebPipe, root-pattern morphology
evaluations in LLMs, 2025).**
https://github.com/NNLP-IL/Hebrew-Resources/blob/master/models_tools_services.rst ,
https://arxiv.org/pdf/2603.15773
General-purpose Hebrew morphological analyzers/segmenters and a 2025 evaluation of how
well LLMs represent Semitic root-pattern morphology (finding: tokenizer alignment with
morphology is neither necessary nor sufficient for a model to generate it correctly).
**Transfer: plausible but not attempted today.** This project's homograph/substitution
handling (`solver/homographs.py`, `solver/substitutions.py`) is already hand-built
against this specific corpus and works at the whole-word level; a real morphological
analyzer could in principle strip construct-state and prefix/suffix inflections (ב/ל/
מ/ש/ה/ו/כ) more systematically than the current ad hoc prefix-stripping in
`fix_enums.py`'s scoring heuristic. Flagging as a possible future lever for
`candidates.py`'s fodder-window search (letting windows trim a leading Hebrew clitic
before checking anagram/hidden matches), not pursued today to keep this run to one
lever.

## 2026-08-15

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824). The
direct precursor to the ICML 2025 paper already credited in this log (2506.04824) — same
proving-framework lineage `solver/prove.py` was adapted from. Read it specifically for two
things not previously checked here: (1) how it formalizes wordplay into Python (an LLM,
Gemini, generates `is_synonym()`/`is_abbreviation()`/`is_anagram()` assertions from an
informal wordplay gloss — structurally identical to what `prove.py`'s DSL already does);
(2) its own honest accuracy ceiling on distinguishing correct answers from close-but-wrong
ones: **~38-40% true-positive rate, ~55% draws, ~5-6% false negatives** on 100 test clues,
with the authors stating outright the system "is a long way from being a reliable oracle
of answer correctness." **Transfer: confirms a limitation this project independently hit
today.** Building `solve_pass.py` (this run's lever), the first design re-ran `is_anagram`/
`is_hidden`/`is_reversal` on `candidates.py`'s own output and found it proved 100% of raw
hits — because those generators only ever emit answers that already satisfy the mechanism
by construction, so "proving" them is a tautology, not verification. The English-cryptic
paper's own 38-40% ceiling (on a MATURE candidate pool from FastText-embedding retrieval,
not a from-scratch mechanical generator) is independent confirmation that execution-based
proof gates are a real but bounded tool: they catch wordplay that outright fails to
execute, not wordplay that executes but is coincidental. Neither this project's `prove.py`
nor the source paper's prover is "an oracle" — both need a human/LLM definition-fit
judgment layered on top, which is exactly the division of labour `solve_pass.py` ended up
encoding after the false start (see DAILY.md log).

**Candidate ranking / definition-span retrieval, re-checked**: the same paper's candidate
generator extracts "the span in the generated definition" and ranks crossword wordlists by
FastText cosine similarity to it, filtered to the right letter pattern. Structurally the
same idea already logged here 2026-08-06 (arXiv 2412.09012) and judged "structurally yes,
technically no" for transfer (no Hebrew embedding space tuned for this genre, corpus too
thin to train one). Re-confirmed, not new information — but now doubly attested across two
independent English-cryptic systems, which raises this project's own priority on lexicon-
tier ranking (tried today, see DAILY.md: corpus/culture-tier hits outrank plain dictionary
hits) as a cheap partial substitute for embedding similarity that this corpus CAN support.

**General sweep** (cryptic candidate generation / diverse hypothesis breadth 2025-2026,
Hebrew morphological tooling): no further new transferable results beyond what the
2026-08-06 entries already covered. The mdda/cryptic-wordplay dataset-building tools
(github.com/mdda/cryptic-wordplay) turned up again in search results — English-clue
dataset tooling, not directly reusable for Hebrew, no action taken.

## 2026-08-16

Before searching, read the full run history first: 9 prior daily runs (PRs #1, #2, #6-#11
plus RESULTS/DAILY's own logs) already implemented and measured mechanical candidate
generation (anagram/hidden/reversal/pattern, then substitution- and homograph-augmented
variants) and definition-span detection twice each, independently, on three different dev
puzzles (2026-05-29, 2026-05-21, and one earlier). Every measurement landed in the same
3.6-7.1% recall@N band regardless of which mechanism was added. That is a saturated
result, not a promising one — today's research pass is calibrated against it rather than
re-discovering it.

**"Are LLMs Good Cryptic Crossword Solvers?"** (arXiv 2403.12094). Benchmarks LLaMA2,
Mistral, and ChatGPT directly on cryptic clues; reports ChatGPT at ~9.5% raw accuracy vs.
~99% for expert humans on the same clue set — the largest reported human/LLM gap found in
this literature so far. **Transfer: corroborating, not actionable.** It measures the same
"a bare LLM cannot decode wordplay from a single pass" ceiling this project hit and moved
away from years ago (RESULTS.md v2-v6): no new architecture, prompting technique, or
candidate/verification split is proposed here beyond what 2506.04824 and 2407.08824
(already logged 2026-08-06/08-15) already contribute. Filed as confirmation the general
finding replicates across model families, not as a new lever.

**Hebrew LLM Benchmark Suite** (huggingface.co/blog/leaderboard-hebrew, and the
"Hebrew LLM Benchmark Suite" overview, both early-2026). A new open leaderboard for
general Hebrew-language LLM capability, with morphology/orthography-aware metrics.
**Transfer: none for this project.** It benchmarks whole-model Hebrew fluency (QA,
summarization, generation) — nothing about cryptic wordplay, definition-span structure,
or candidate enumeration. Checked because it is new and Hebrew-specific, not because it
looked promising; it doesn't change anything here.

**Root-pattern morphology re-check** — no update beyond the 2026-08-06 entry (arXiv
2603.15773, on Arabic not Hebrew, still the closest available finding: tokenizer/morpheme
alignment is neither necessary nor sufficient for correct morphological generation). No
new Hebrew-specific morphological segmenter surfaced this search that PLAYBOOK.md's
hand-built prefix/suffix stripping doesn't already approximate.

**Berkeley Crossword Solver / belief-propagation family, re-checked for queue item 4**
(global constraint optimization). Confirmed again: BCS's own reported gain (57% -> 82%
exact-puzzle accuracy at the NYT tournament) comes from combining a strong *candidate*
list (fine-tuned BERT QA over ~6M clue-answer pairs) with belief propagation across grid
constraints — the propagation step is described everywhere as a *re-ranker*, not a
generator; it cannot manufacture a correct candidate that never entered the list. Also
found the WebCrow French solver (arXiv 2311.15626), a non-English data point, but it is
the same non-cryptic genre (clue = a definition to embed/retrieve against, not wordplay to
decode) as the English CSP literature already logged 2026-08-06. **Transfer: reconfirms
queue item 4 is correctly sequenced after, not before, candidate quality — and today's
9-run history of flat 3.6-7.1% recall is exactly the "candidate list not good enough yet"
condition that makes running belief propagation now premature.** Nothing here overrides
that ordering; if anything it strengthens the case for leaving item 4 alone until
candidate generation clears a materially higher recall bar than mechanical
anagram/hidden/reversal/substitution/homograph search has reached in 9 attempts.

**Conclusion for today's lever choice:** the research pass turned up no new technique for
either candidate generation or definition-span detection — both queue items have had a
fair, repeated trial and the literature offers nothing that would move them off their
current plateau without a fundamentally different resource (a large Hebrew clue-embedding
model, which this project's 8k-clue corpus cannot train). The honest move is not a 10th
attempt at the same lever; it's finishing the one sub-task of item 1(a) that all 9 prior
attempts explicitly left undone: an actual live LLM solve session using the ranked
candidate list, measuring real precision/coverage/yield rather than offline recall@N. See
DAILY.md's log for what that trial found.
## 2026-08-17

**"Are LLMs Good Cryptic Crossword Solvers?"** (arXiv 2403.12094, Sadallah/Kotova/
Kochmar; NAACL-adjacent, revised Jan 2025). https://arxiv.org/pdf/2403.12094
Benchmarks LLaMA2, Mistral, and vanilla ChatGPT on English cryptics with no special
scaffolding: 7-9% clue accuracy vs 74% for self-reported amateur humans and 99% for
experts. **Transfer: calibration only, no new method.** It predates and is superseded
by the reasoning-based (generate-then-formalize-then-verify) approach already adopted
here (arXiv 2506.04824, credited 2026-08-06); its main value is confirming that raw
LLM wordplay-solving without candidate generation or a proof gate is genuinely weak in
general, not just on this Hebrew setter — consistent with this project's own diagnosis
that a single hand-picked guess is the wrong shape for this task.

**Substitution/equivalence mining from crowd-sourced puzzle explanations** — searched
specifically for prior art on today's lever (extracting clue-fragment -> answer-fragment
equivalences from crowd explanation text, as `solver/substitutions.py` already does).
Found nothing directly on point; closest adjacent work was "Explaining Puzzle Solutions
in Natural Language" (ACL 2025 Findings), which targets Sudoku solution *narration*, not
extracting a reusable equivalence table from existing human explanations for a downstream
generator. **Transfer: none found — this appears to be a locally-developed technique**,
which is consistent with the genre being a small, Hebrew-specific niche with no existing
academic benchmark (unlike English Cryptonite/Times cryptics).

**Hebrew morphological segmentation, re-checked.** Same landscape as 2026-08-06
(RFTokenizer, HebPipe), plus **YAP** (morpho-syntactic parser: analysis, disambiguation,
dependency parsing) and CommonMorph (LREC 2026, a participatory *documentation* platform,
not a segmenter). **Transfer: still plausible, still not attempted.** Same reasoning as
before — could in principle strip clitics (ב/ל/מ/ש/ה/ו/כ) more systematically than the
current ad hoc prefix lists in `homographs.py`/`charade.py`, but no new evidence this run
that it would move the measured bottleneck (candidate quality, not tokenization).

**Meta-finding, not a transfer question: search-engine summarization silently drops
retraction context.** A general web search for this exact research area surfaced this
project's own public site (tashbetz-solver.vercel.app) and the search tool's own summary
described "a v6 solver run returned 27 of 28 clues correct on 2026-06-05 ... suggesting
significant recent improvements" — presenting the **retracted 96%/leak result**
(RESULTS.md's own integrity finding, 2026-07-21) as if it were validated progress. The
live page itself is fully honest: it has a dedicated "Retraction" section explaining the
lexicon leak in detail, immediately below the same numbers. The summarizer simply
stripped that context when condensing the page. Not a site bug, not actioned — but a
concrete reminder for this project's own research step: read primary sources in full,
don't trust a search summary's framing, especially for anything self-referential.

## 2026-08-19

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824).
https://arxiv.org/html/2407.08824v1
Pipeline: a fine-tuned LLM annotates an informal definition span + wordplay for a
clue+candidate pair; a second LLM formalises the wordplay into executable assertions
(`is_synonym`, `is_abbreviation`, `is_anagram`, ...); a Python prover executes them,
giving the LLM up to 5 iterative rewrite attempts on failure. Headline finding: proving
the GROUND-TRUTH answer beats a close FastText-similarity distractor only 38-42% of the
time (53-59% draws) — i.e. even with the correct answer in hand, the proof step alone
often cannot outscore a wrong-but-plausible neighbor; scale of candidate pool matters more
than proof strength alone. **Transfer: high, and largely already independently converged
on.** This is essentially this project's own architecture (prove.py = the verifier,
candidates.py = the FastText-similarity-generator's role, both built over the last two
weeks before this paper was found) rediscovered from the English-cryptic side, which is
reassuring rather than novel — it says the design direction here is not a dead end. The
one piece genuinely not yet present here: their **iterative rewrite loop** (a proof that
fails gets fed its own failure back for up to 5 repair attempts) vs. prove.py's current
one-shot check-or-reject. Flagging as a possible future lever, not attempted today (would
touch the solve LOOP, not a standalone tool, and today's lever budget went to definition-
span detection instead). Their draw-heavy result is also a caution for lever 4 in the
research-informed queue (HYPOTHESIS BREADTH / more candidates): a bigger candidate pool
only helps if the prover can actually discriminate, which their own numbers say is not
free.

**"Cryptic Grammar" (Viresh Ratnakar, 2023, informal writeup, revisited today for currency).**
https://viresh-ratnakar.github.io/writings/2023/cryptic-grammar-04-2023.html
Formalises English cryptic-clue *surface grammar* (placeholder-substitution: replace
fodder with `[fodder]`, definition with `[solution]`, check the remainder reads as a
valid instruction/assertion in English). **Transfer: none.** It explicitly does not
address definition placement (assumes the solver already knows), and the technique is
English-morphology-specific (tense/participle agreement) with no Hebrew analogue in this
project's tooling. Checked because it looked promising from the title; recording the
negative so a future run does not re-check it.

**Today's own empirical check — see DAILY.md log for the executed measurement.**
`solver/PLAYBOOK.md` section 2.4 asserts, from qualitative reading, that this specific
setter (יורם הרועה) does NOT follow the standard cryptic convention that the definition
sits entirely at one end of the clue ("No fixed rule... can be interleaved"). Before
building `solver/defspan.py`'s classifier half, I tested that claim mechanically against
this run's transcribed puzzle by locating each gold answer's own anagram/hidden/reversal
window in its clue text and bucketing the window's position (start/end/interior). See
DAILY.md for the executed numbers and the resulting go/no-go decision — this is the kind
of check the definition-span literature (2412.09012, still the standing reference) never
does for a non-English, non-standard-convention setter, and it directly gates whether
lever queue item 2 is worth pursuing further here.

**"Language Models are Crossword Solvers"** (arXiv 2406.09043) and the general
crossword-AI literature (Berkeley Crossword Solver, Dr. Fill, Proverb) — checked again,
no new transferable finding beyond what PLAYBOOK.md and PLAN_V2.md already extracted
(global constraint optimisation over ranked candidates, item A in PLAN_V2.md, still not
implemented — candidate generation is upstream of that and had to come first).
**Transfer: none new.** These systems solve non-cryptic (American-style) grid puzzles
where "candidate" means "any dictionary word of the right length crossing existing
letters" — there is no wordplay-decoding step, which is the entire difficulty of this
project's puzzles. Confirms DAILY.md's standing skepticism.

## 2026-08-20

Re-checked for anything new since 2026-08-06 on: cryptic definition-span detection,
candidate generation, and Hebrew NLP/morphology.

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824, Andrews
& Witteveen, ICML 2024 workshop). https://arxiv.org/abs/2407.08824
The direct predecessor of the already-adopted 2506.04824 pipeline, by the same authors:
LLM proposes an answer + informal wordplay, a second LLM formalises it as a Python proof,
a prover checks it executes. **Transfer: none new** — this project's `solver/prove.py`
already implements this half (credited in RESEARCH.md 2026-08-06), and the newer paper
supersedes this one. Surfaced only because it clarifies the lineage: the "prove, don't
merely persuade" idea predates the "generate many candidates first" idea in this same
research line, which matches this project's own history (proof gate shipped 2026-07-28,
candidate generation only started 2026-08-06) — independent confirmation the ordering
DAILY.md picked (verification before generation) tracks how the field itself arrived at
the combined pipeline, not a coincidence of this project's own priorities.

**Definition-span detection, general search.** No new paper beyond 2412.09012 (already
logged 2026-08-06). One search result restates the standard human-solver heuristic more
concretely: an LLM-generated candidate definition is used to re-rank answer candidates by
semantic closeness to the marked span (via FastText/embedding similarity), i.e.
definition-span detection is used to SCORE candidates a separate mechanism already
produced, not to generate answers on its own. **Transfer: clarifies scope, doesn't change
the plan.** This confirms queue item 2 (definition-span detection) is correctly understood
here as a companion to candidate generation, not a replacement for it: the span tells you
WHICH candidate to prefer, not what the candidates are. Still no Hebrew-tuned embedding
space to port the scoring half with; the rule-based version (classify which end, check
whether the OTHER end's residual parses as wordplay) remains the only feasible variant
here, unbuilt, still queued.

**Hebrew morphology / NLP** — no new resource found beyond the 2025 items already logged
(RFTokenizer, HebPipe, the root-pattern morphology evaluation). No update.

**Conclusion for today's lever.** Nothing found this cycle changes the queue's priority
order. DAILY.md's own queue (2026-08-06 entry) already named the correct next step in
plain language before I went looking: "add substitution- and homograph-aware generation
... the setter leans on these, not literal anagram/hidden/reversal, per the 3.6% result
and PLAYBOOK.md." That diagnosis is internal (this project's own measured recall
breakdown + PLAYBOOK.md's empirically-mined mechanism distribution — charade/substitution
devices are ~35-40%+27% of clues vs. anagram's 16%), not something the external
literature has an opinion on either way, since none of the papers above study a
morphologically rich, unvocalized, small-corpus language. Implemented today: candidate
generation extended with `substitution_candidates` and `homograph_candidates`
mechanisms in `solver/candidates.py` (queue item 1(b)), plus a held-out-safety fix to
`solver/substitutions.py` that the new mechanism's use of that table required (see
DAILY.md log for the measured result and the audit).

## 2026-08-23

Two open PRs exist on top of this main (#23, 2026-08-21: `held_out_answers()` coverage
gap fix, queue item 7; #24, 2026-08-22: first full-puzzle live blind trial of
`solve_pass.py`, 0/2 precision) — neither merged, so main still lacks both. Read both in
full via `pull_request_read` before choosing today's lever, per the standing "don't
re-derive a result already sitting in an unmerged PR" lesson from the 2026-08-16 PR-pileup
finding. PR #24's root-cause trace is the most important thing either surfaces:
**cumulative live precision across the only two live trials this project has run
(2026-08-16, 2026-08-22) is 1/4 = 25%**, and both misses share one shape — `prove.py`
correctly verified a real mechanism (a hidden word, a reversal) on a plausible-but-wrong
Hebrew answer; the gap is definition-FIT judgment, not mechanism verification.

**Searched specifically for that gap: definition-candidate semantic-fit scoring for
cryptic solving, general and Hebrew-specific.** Confirms the existing 2412.09012/
2506.04824 finding already logged here (2026-08-06/08-15): the established technique is
FastText/embedding cosine similarity between a located definition span and each candidate,
used to RANK a candidate pool a separate generator already produced. **Transfer: still no
new mechanism** — no 2026 paper found that changes this, and this project still has no
Hebrew embedding space tuned for the genre (checked again: general-purpose Hebrew
embeddings exist — fastText/GloVe/Word2Vec/AlephBERT vectors are documented resources —
but none is crossword-register-tuned, and integrating any of them is a materially larger
lift than a text-only fix, out of scope to even prototype today alongside a second lever).

**Checked one specific new lead: Hebrew WordNet**, since English rule-based cryptic
solvers use WordNet path-similarity for exactly this definition-vs-candidate scoring role
(surfaced in today's search on general cryptic-solver definition-ranking approaches).
Hebrew WordNet (MultiWordNet-aligned, built at IRST/Ben-Gurion) exists in principle but
search results describe its canonical host as unavailable; the Open Multilingual WordNet
mirror project lists a Hebrew component but the reference itself could not be confirmed
reachable in the time budget for a research check (not attempted as a bootstrap step —
would need its own reconstructibility story before ever being wired in, matching this
project's standing rule that nothing gets committed unless bootstrap.sh can rebuild it).
**Transfer: plausible, unbuilt, flagged for a dedicated future lever** — path-similarity
over a Hebrew WordNet (if a working mirror exists) is the closest thing to a validated
technique for definition-fit scoring that the literature actually offers, more promising
than trying to hand-roll a heuristic the way `defspan.py`'s indicator-density classifier
did (which already measured 1/5, worse than chance, on the structurally adjacent
definition-*location* problem). Not started today: confirming a real, licensable,
scriptable download is its own investigation, and this run's one-lever budget went
elsewhere (see DAILY.md).

**Conclusion for today's lever.** No new external finding is buildable today: the one
concrete idea it points to (WordNet-based definition-fit scoring) needs a resource
whose availability this session couldn't confirm, so implementing a stub around it would
be exactly the kind of filler this project's own log explicitly says not to ship. Chose
the best-evidenced internal item instead: queue item 7b, flagged-not-fixed twice already
(2026-08-16 log entry named the gap; PR #23, 2026-08-21, fixed the `lexicon.py` half and
explicitly flagged the identical gap in `substitutions.py`/`retrieve_defs.py` as 7b,
unfixed). Checked directly before trusting that "identical" label: `substitutions.py`'s
`held_out()` has the EXACT same shape as `lexicon.py`'s old bug (its `explanations()`
sources `data/answers/answers_parsed.json` — every one of the 52 puzzles unconditionally —
while the old `held_out()` only blocked rows with a transcribed `clues.jsonl` entry), so
that half is a real, currently-exploitable leak on this main. `retrieve_defs.py`'s
`held_out()` has the same narrow row-only shape, but its only caller (`build_index()`)
sources dev/eval-adjacent docs exclusively from `clues.jsonl` rows marked `split=='train'`
— which an untranscribed slot can never have, by construction — so that half is a
name-only match to lexicon.py's bug, not an actively exploitable one under today's call
graph. Fixed both anyway (defense-in-depth, and to keep both functions on the same
by_date-expanded contract as `lexicon.held_out_answers()` rather than a narrower one that
happens to be safe only by luck of the current call sites) — see DAILY.md for the measured
before/after and the audit.

## 2026-08-21

Re-checked for anything new since 2026-08-20 on: cryptic candidate generation,
definition-span detection, and Hebrew NLP/morphology, plus a general sweep for any new
cryptic-solving system.

**General search: "cryptic crossword solver LLM candidate generation 2026".** Surfaced
only papers already logged here (2406.09043 NAACL 2025, 2412.09012, 2506.04824) plus one
new item worth checking: Sadallah et al. (2025) reports ChatGPT few-shot accuracy of
9.5% on English cryptics vs. 99% human-expert — a bigger accuracy gap than this project's
own numbers, on an easier language (English cryptics have a stable one-end definition
convention this setter explicitly does not follow, per the already-measured 08-19
finding). **Transfer: confirms rather than changes anything** — if frontier LLMs
struggle this much on the *easier*, well-studied version of this task even with full
in-context few-shot prompting (no external candidate generator, no proof gate), it's
consistent with this project's standing diagnosis that the wordplay-cracking step itself,
not tooling, is the hard part, and that a bare LLM without this project's harness would
do worse here, not better. Also surfaced this project's own public page again in a
general search (as on 2026-08-20) — spot-checked that it still correctly represents the
96% figure as retracted, not fixed by omission.

**Definition-span detection, general search.** No new academic result; general
crossword-advice pages restate the same one-end convention already known to not hold for
this setter (killed 2026-08-19, queue item 2 struck). **Transfer: none** — nothing here
contradicts or should reopen that finding.

**Hebrew morphology / NLP.** Same landscape as 2026-08-06/08-20 (RFTokenizer, HebPipe,
YAP), plus one tool not previously named directly: **DictaBERT-seg**, a Hebrew
transformer fine-tuned specifically for the prefix-segmentation task (splitting off
ב/ל/מ/ש/ה/ו/כ clitics), more targeted than YAP's full morpho-syntactic parse for this
project's narrow need. **Transfer: still plausible, still not attempted, still not the
bottleneck.** Same reasoning as the last two research entries — this project's own
measured numbers (candidate recall 3.6-7.1% across three independent puzzles/
implementations, defspan classifier 1/5) point at wordplay-mechanism coverage and
definition-fit judgment as the gap, not tokenization quality; the ad hoc prefix lists
already in `homographs.py`/`charade.py` are not where the last three levers' failures
traced to. Not queued above candidate-generation-shape work without a concrete case where
a prefix-list miss caused a specific measured failure.

**Conclusion for today's lever.** No new external finding changes the queue's priority
order or reopens either struck item. Given the queue's top code lever (candidate
generation, item 1) has now been tried in three independently-written shapes across three
different dev puzzles with the same null result (3.6% / 7.1% / 4.0% recall, all flat
before/after adding substitution+homograph mechanisms), and item 2 is struck, today's
lever is the lowest-risk, best-evidenced item actually still open: queue item 7, fixing
`lexicon.held_out_answers()`'s coverage gap. It is not a research-literature lever — it's
an internal integrity fix flagged twice already (2026-08-16, 2026-08-17 log entries) as a
real, unaddressed leak vector, and this project's own history (the 96% leak) is the
reason leak-vector fixes get priority over one more speculative recall experiment on a
lever already measured negative three times running.
