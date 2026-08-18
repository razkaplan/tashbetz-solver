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

## 2026-08-18

**"Orthographic Constraint Satisfaction and Human Difficulty Alignment in Large Language
Models"** (arXiv 2511.21086, 2025). https://arxiv.org/html/2511.21086
Uses the NYT Spelling Bee (generate valid words from 7 fixed letters, 1 mandatory, min
length 4) as a testbed for how well LLMs respect hard character-level constraints when
generating candidate words directly. Finding: all models keep near-perfect PRECISION
(a word they claim fits, does fit the letter set) but RECALL is poor and gets worse
with word length (up to 71x degradation for small models vs 1.3x for humans); failures
concentrate on common words with atypical-looking orthography (e.g. "data", "loll") —
models lean on distributional plausibility over actually checking the constraint,
even though the constraint check is trivial to do exactly.
**Transfer: strong, and it is a confirmation, not a new direction.** This is
independent evidence for a design choice this project already made: `candidates.py`
generates anagram/hidden/reversal candidates MECHANICALLY (Python string ops over the
lexicon), specifically because asking an LLM to directly produce "words of length N
using exactly these letters" is exactly the failure mode this paper measures — good
precision, bad and length-sensitive recall, worst on the internally-common (headline)
cases. Nothing to change here; it argues for staying the course (grow the mechanical
generator, keep the LLM out of the character-constraint-satisfaction step) rather than
reverting to LLM-native candidate generation.

**"Sampling More, Getting Less: Calibration is the Diversity Bottleneck in LLMs"**
(arXiv 2605.11128, 2026). https://arxiv.org/pdf/2605.11128
Finds that a model's own calibration (how well its confidence tracks correctness)
caps the diversity gained from sampling more candidates: well-calibrated sampling
concentrates around the model's single best guess, so drawing more samples does not
proportionally widen the correct-candidate pool the way a diversity-seeking search
would. **Transfer: confirms two decisions already made and logged, does not open a
new one.** (1) DAILY.md's "Things already tried — do not repeat" already found
majority-vote / confidence-weighted consensus reverses sign with run quality — this
paper gives a mechanism for why naive multi-sampling under-delivers diversity; the
project's actual fix (`candidates.py`'s exhaustive mechanical enumeration, independent
of any model's self-confidence) sidesteps the bottleneck entirely rather than fighting
it. (2) It reinforces the "hypothesis breadth" lever (research-informed queue,
2026-08-08 log): breadth has to come from an enumeration procedure, not from asking
one LLM to sample more times at a fixed temperature.

**Definition-span position, re-checked against this project's own corpus (not new
literature — a sanity check on 2026-08-06's queue item 2).** `solver/PLAYBOOK.md`
section 2.4, built empirically from the 728-clue corpus with crowd explanations
already in hand, states plainly: "No fixed rule. Definition can be at the start, the
end, or *interleaved*." This is the setter's own idiom working against the standard
English-cryptic heuristic ("definition sits entirely at one end") that queue item 2
and the calling task's priority (b) both assume. **Judgement: the classic
one-end-definition heuristic does not transfer to יורם הרועה as a hard classifier.**
A rule/heuristic-based "first-N-words vs last-N-words" span detector, scored by
whether the other end's residual parses as a wordplay device (the approach floated in
the 2026-08-06 entry as the only feasible non-learned version for Hebrew), would be
built on a premise this project's own data already contradicts for a meaningful
fraction of clues — double-definitions (14% of the corpus, both ends ARE
definitions), interleaved clues, and pun-definitions where the whole surface is the
definition. Not implemented today for this reason: it would be shipping a classifier
whose core assumption this corpus falsifies, which is exactly the kind of thing
DAILY.md asks to be honest about rather than paper over with a lever that "sounds
right." Queue item (a)'s own logged next step — extend `candidates.py` with
substitution- and homograph-aware mechanisms — has no such contradiction and is
today's implemented lever instead (see DAILY.md log).
