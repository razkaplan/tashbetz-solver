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
