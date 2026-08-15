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

**"Language Models are Crossword Solvers"** (arXiv 2406.09043) and the general
crossword-AI literature (Berkeley Crossword Solver, Dr. Fill, Proverb) — checked again,
no new transferable finding beyond what PLAYBOOK.md and PLAN_V2.md already extracted
(global constraint optimisation over ranked candidates, item A in PLAN_V2.md, still not
implemented — candidate generation is upstream of that and had to come first).
**Transfer: none new.** These systems solve non-cryptic (American-style) grid puzzles
where "candidate" means "any dictionary word of the right length crossing existing
letters" — there is no wordplay-decoding step, which is the entire difficulty of this
project's puzzles. Confirms DAILY.md's standing skepticism.

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
