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
