# Research log

Append-only. One entry per daily run: links, a one-line summary, and an honest judgement
of whether it transfers to a blind, no-corpus-fine-tune, Hebrew cryptic solver running
inside an LLM-agent harness (not a trained model with gradient access).

## 2026-08-03

Searched: cryptic crossword solving with LLMs / definition-span detection, candidate
generation for constrained crossword puzzles, and Hebrew NLP morphology/tokenization —
the three areas DAILY.md flags as relevant to the current lever queue.

- **"A Reasoning-Based Approach to Cryptic Crossword Clue Solving"**
  (arXiv 2506.04824, and the related "Proving that Cryptic Crossword Clue Answers are
  Correct", arXiv 2407.08824). LLM hypothesises answer + wordplay, then a *verifier*
  operating on codified/formalised reasoning steps checks it; reports new SOTA on
  Cryptonite (Times/Telegraph cryptics). **Transfers: already adopted.** This is the
  design `solver/prove.py` already implements (executable assertions, not an LLM judging
  plausibility) — added here 2026-07-28, one day before this paper would otherwise have
  been "new" to us. No further action; the interesting open question this paper doesn't
  answer for us is upstream of verification: candidate generation, which is today's lever.

- **"Are LLMs Good Cryptic Crossword Solvers?"** (arXiv 2403.12094) and **"Language
  Models are Crossword Solvers"** (arXiv 2406.09043). Benchmark papers quantifying that
  off-the-shelf LLMs solve English cryptics far below human-expert level, and that
  performance is bottlenecked by wordplay decomposition, not definition recognition.
  **Transfers as a prior, not a technique**: consistent with our own error profile
  (PLAN_V2.md: misses are wordplay-decomposition failures, spread evenly across clue
  length, not concentrated in culture references as we'd earlier assumed). No new
  method to adopt, but it corroborates that today's lever (candidate generation to feed
  the proof gate) is the right target rather than more knowledge tooling.

- **"Towards a Semantic Approach for Candidate Answer Generation in Solving Crossword
  Puzzles"** (ScienceDirect / ResearchGate, S1877050920312424). Generates candidate
  answer LISTS per slot using WordNet lexical relations (synonymy/hypernymy chains) for
  definition-type clues, then a CSP solver fills the grid from ranked candidate pools.
  **Partially transfers, mechanism only, not the tool**: the "produce a pool per slot,
  optimize over crossings afterward" architecture is exactly PLAN_V2's methodology (A),
  and is the structural motivation for today's `solver/candidates.py`. WordNet itself is
  useless here (no Hebrew WordNet with meaningful coverage of this genre's slang/proper
  nouns) — our closest analogue is `solver/substitutions.py` (setter-specific mined
  equivalences) plus the lexicon's culture tier, neither of which is a general semantic
  network. This is why today's lever ships two purely MECHANICAL generators (anagram,
  hidden-word) rather than a semantic one: we have no Hebrew WordNet to lean on, and
  building a synonym-based generator without one would mean inventing synonyms, which
  `prove.py`'s `means()` already exists specifically to catch and reject.

- **"Developing a Scalable and Fast Crossword Engine"** (Very Good Ventures blog) and
  the classic Berkeley Crossword Solver / Dr.Fill lineage it cites: ranked candidate
  lists per slot + weighted CSP / belief propagation over the whole grid, not greedy
  left-to-right filling. **Transfers as architecture, already the plan**: this is
  PLAN_V2 item A verbatim, prioritized *after* candidate pools are good (item A is
  ordered last: "worth doing once candidate lists are good enough to optimise over").
  Confirms the ordering in PLAN_V2 is right, not just plausible — candidate generation
  before global optimization, because a CSP optimizer over empty/single-item candidate
  lists (today's measured state, see below) has nothing to optimize.

- **Hebrew morphology/tokenization surveys** (AlephBERT arXiv 2104.04052; "Splintering
  Nonconcatenative Languages for Better Tokenization" arXiv 2503.14433; DictaBERT-char
  2025; NNLP-IL Hebrew-Resources). Confirms Hebrew is still flagged as a low-resource,
  morphologically-rich language in 2025-2026 work, and that root-and-pattern
  (nonconcatenative) morphology specifically resists BPE-style tokenization. **Does not
  transfer to this project directly**: these are all about training/tokenizing neural
  models, and this solver has no fine-tuning track in active use (Track B / sft.jsonl is
  explicitly deprioritized in RESULTS.md — "thin for teaching wordplay"). The one
  relevant idea — that Hebrew word-internal structure needs explicit handling, not
  subword-token guessing — is already implemented here as *hand-written* rules
  (final-letter folding, gematria letter values, prefix stripping in indicators.json)
  rather than a learned tokenizer, which is the right call at this corpus size (8,249
  pairs is far below what any of these papers train on).

**Bottom line for today's lever**: no paper hands us a Hebrew-specific technique to
adopt wholesale (expected — this remains a niche, unaddressed setting). The actionable
transfer is architectural and already reflected in PLAN_V2's own priority order: stop
generating one candidate and rationalizing it; generate a pool per mechanism, verify
with `prove.py`, then (later) optimize jointly over the grid. Built today:
`solver/candidates.py`, two mechanical generators (anagram-window, hidden-run). See
DAILY.md log for the measured result — low recall (1/28 blind), with a specific,
verified explanation for why (mechanism mix + proper-noun/foreign-word coverage gaps in
the realness dictionary), not a vague shortfall.
