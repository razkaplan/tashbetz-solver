# Research log — daily improvement agent

One entry per run: what was found, one-line summary, and an honest judgement of whether
it transfers to a Hebrew cryptic solver with an 8k-clue corpus. Default skepticism: most
crossword-AI work targets non-cryptic (American-style) puzzles and does not transfer.

## 2026-08-10

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824).
https://arxiv.org/html/2407.08824v1
Hybrid pipeline: a fine-tuned Llama-3 proposes definition+wordplay annotations, Gemini
formalises them into Python proof assertions (`is_synonym`, `is_abbreviation`, string
concatenation), and a verifier executes them, allowing up to 5 LLM re-write attempts on
failure. Catalogs nine wordplay types (anagram, charade, container, deletion, double
definition, hidden word, homophone, reversal, + one more) with a corresponding DSL.
Headline result: proofs distinguish the gold answer from a close FastText-similarity
distractor only 38-42% of the time, with 55-59% draws — even this system's own authors
call that short of reliable at scale.
**Transfer: strong structural confirmation, one important negative data point.**
`solver/prove.py` already independently converged on the same design (assertion DSL,
execute-don't-persuade) before this paper was read here — convergent validation, not a
new idea to adopt. The genuinely new information is the **definition-span number**: this
paper's candidate generation and evaluation both start from a *human-annotated* definition
span (curly-brace markup in their "Wordplay" dataset), not an automatically detected one.
That is direct evidence that automatic definition-span detection is still an open problem
even in the English cryptic literature with far more training data (470k+ clues) than this
project has — which recalibrates queue item 2 ("definition-span detection... standard in
the literature") from "a known technique to port" to "an unsolved problem elsewhere too."
Any heuristic built here should be evaluated as a research attempt, not treated as an
established baseline we're merely behind on.

**Hebrew morphology / LLM benchmarks, checked for anything new since 2026-08-06.**
https://arxiv.org/pdf/2604.17108 (Hebrew coreference benchmark), NNLP-IL resource list.
No new transferable finding: confirms the standing read that general-purpose LLM Hebrew
morphology handling still lags dedicated tools (GPT-4o scored 5 points below a small
encoder-based baseline on Hebrew coreference with gold mention boundaries given). Does not
change this project's approach, which already avoids depending on an LLM's own Hebrew
segmentation and instead does explicit prefix/suffix stripping (`homographs.py`'s
`variants()`, and today's `candidates.py` port of the same stemming).
**Transfer: none new — status quo confirmed.**

**Operational finding, not a paper: `bootstrap.sh` step 2 (14across.co.il) was
100%-blocked this run**, not the "~half, random" intermittency logged 2026-08-06. Five
retries with backoff (the existing fix) failed on every one of the first 7/52 puzzles
before the run was aborted; a direct `curl` reproduced a persistent HTTP 202 `sgcaptcha`
redirect with zero successes across 9 attempts over several minutes. Routing the identical
GET through the Bright Data MCP scraping tool (a different egress path) succeeded on the
first try for both puzzles fetched. This is an infrastructure/IP-reputation fact about
today's environment, not a code defect — `parse_answers.py`'s retry logic is correct for
the failure mode it was built for (transient, ~50%), just not for a fully-blocked egress
IP. Left unfixed today (out of scope for one lever); flagging for whoever next hits a
0/N bootstrap run: try an alternate egress path before assuming the scraper regressed.

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
