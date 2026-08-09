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

## 2026-08-09

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824).
https://arxiv.org/html/2407.08824v1
A fine-tuned Llama model proposes definition + wordplay annotations for a
(clue, candidate-answer) pair; a second model formalises the wordplay as a Python DSL
program; a verifier executes it and — the part not previously in this project's
literature notes — on failure returns a structured error/hint back to the generator for
up to 5 iterative rewrites, rather than a bare pass/fail. The paper also reports that
gold answers are measurably more "provable" than close semantic decoys (~38-42%
true-positive preference), i.e. provability itself carries a correctness signal.
**Transfer: partial, and not implemented today.** `solver/prove.py`'s docstring already
credits the sibling ICML paper (2506.04824) for the propose-then-verify shape and
already returns a WHY string on failure (`prove.py check` prints the failing assertion).
What is genuinely new here is *feeding that failure hint back into another generation
round* — this project's proof gate currently treats a failed proof as a terminal signal
("repair the derivation or downgrade to suggestion" — SOLVE_PROTOCOL.md's own wording),
not as input to a second attempt. That is a plausible future lever (an iterative
prove-then-repair loop around `candidates.py` output) but is a distinct, non-trivial
piece of work — flagging for the queue, not attempting it inside today's single-lever
budget.

**"Are LLMs Good Cryptic Crossword Solvers?"** (arXiv 2403.12094) — re-checked for
definition-span detection technique detail (last run's note said this needed a closer
read). The PDF did not extract cleanly this run either (binary/figure-heavy layout), so
no new technical detail was recoverable beyond what was already logged 2026-08-06:
LLMs are tested on definition-span identification as an isolated subtask and do
measurably better on it than on full clue solving, which is process confirmation, not a
portable technique — the paper does not describe a rule-based or embedding-free
definition-span method that would work without English-tuned resources. No update to
the prior skeptical judgement.

**Hebrew morphology 2025-2026 survey** (Arabic root-pattern tokenizer study
arXiv 2603.15773; Hebrew coreference/morphology benchmark arXiv 2604.17108) — checked
for anything that would improve `candidates.py`'s character-window fodder search or
`homographs.py`'s prefix/suffix stripping. **Transfer: none actionable today.** Both
papers are evaluation/benchmark work (how well do LLMs/tokenizers represent Semitic
morphology), not new segmenters this project could call as a library; the standing
finding from 2026-08-06 (a real morphological analyzer could in principle replace the
ad hoc prefix list in `homographs.py`'s `PREFIXES`/`SUFFIXES`) is unchanged and still
not pursued — the ad hoc list already covers the productive Hebrew clitics (ו/ה/ב/ל/
מ/ש/כ) and the benchmark literature gives no evidence a full analyzer would move this
project's numbers, only that LLMs alone underperform on the task in general.

**Net for today:** no new technique changed the plan. This confirmed the queue item
DAILY.md already flagged as untried and still-relevant: definition-span detection
(rule-based, since no learned/embedding approach transfers without English-tuned
resources) — see the Log entry below for what was actually built.
