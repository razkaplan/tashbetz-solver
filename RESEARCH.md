# Research log — daily improvement agent

One entry per run: what was found, one-line summary, and an honest judgement of whether
it transfers to a Hebrew cryptic solver with an 8k-clue corpus. Default skepticism: most
crossword-AI work targets non-cryptic (American-style) puzzles and does not transfer.

## 2026-08-12

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824,
also on OpenReview as "Generating Code to Verify Cryptic Crossword Reasoning").
https://arxiv.org/abs/2407.08824 , https://openreview.net/forum?id=2nC7zy7adD
An earlier (Jul 2024), narrower paper than the ICML-2025 one already covered here
(2506.04824) — it is specifically about the executable-proof-verifier half of that
later pipeline, evaluated in isolation. Its DSL: `is_synonym`, `is_abbreviation`,
`action_type` (an Action enum: ANAGRAM, REMOVE_FIRST/REMOVE_LAST, INITIALS,
GOES_INSIDE/GOES_OUTSIDE, REVERSE, SUBSTRING, HOMOPHONE), `is_anagram`,
`is_homophone`. Headline finding: even with LLM-generated + code-verified proofs,
the framework only reaches a **38-42% true positive rate distinguishing correct
answers from plausible-but-wrong ones** — "a long way from being a reliable
oracle." Failure modes it names: unused clue words, logically disconnected proof
chains, conditional execution that bypasses an assertion. It reports no wordplay
device as harder to formalize than another — the weakness is systemic (an LLM can
write a proof that runs cleanly for the wrong answer), not device-specific.
**Transfer: two things, one already covered, one a genuine caution.**
(1) Two DSL primitives here are missing from `solver/prove.py`'s existing set
(`is_word, is_anagram, is_reversal, is_container, is_hidden, means, concat,
has_length, word_order`): an INITIALS/acrostic device (first-letter-of-each-word)
and an explicit deletion device (REMOVE_FIRST/REMOVE_LAST). Neither is
implemented here yet — flagged for a future lever, not built today, to keep
today's lever singular (see below). (2) The 38-42% true-positive number is a
direct, sobering data point for this project's own PROOF GATE claim in
SOLVE_PROTOCOL.md ("an assertion either runs or it does not... it cannot be
talked into agreeing") — this paper's own measurement shows a verifier that
*runs cleanly* still passes a majority of wrong answers when the LLM writes
both the candidate and its own proof. This project's re-crack rounds
(2026-08-09 log) independently found the same failure mode by hand — "definition-
only proofs matched gold's shared prefix on crossings, then diverged" — and
tightened the commit rule in response. This paper's number puts a rough size
on how much residual risk that discipline is compensating for: worth restating
as a reason NOT to treat prove.py's PROVED as ground truth without a human/second
pass, which the commit-rule tightenings already do in practice.

**Cryptonite SOTA / definition-span / Hebrew morphology re-checked.** No material
update since the 2026-08-06 entries here (2506.04824, 2412.09012, RFTokenizer/
Hebrew-Resources) — same conclusions stand: candidate-generation-before-verify is
already adopted; definition-span detection is structurally validated in the
literature but has no Hebrew-specific tooling to port; morphological segmentation
is a plausible but unbuilt future lever for fodder-window trimming.
**Transfer: none new, re-confirms standing skepticism.**

Today's lever (see DAILY.md log) is a direct, scoped continuation of the
2026-08-06 candidates.py work rather than a new paper transfer: extending the
existing anagram/hidden/reversal window search to also run against substitution-
mapped clue-word variants (using the project's OWN mined substitutions.json, not
external literature) — the concrete "remaining work" item that entry queued.

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
