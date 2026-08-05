# Research log — cryptic crossword solving, wordplay parsing, Hebrew NLP

Append-only. Each entry: link, one-line summary, honest transfer judgement for a Hebrew
cryptic solver graded on exact-match with an executable proof gate.

## 2026-08-05

**[A Reasoning-Based Approach to Cryptic Crossword Clue Solving](https://arxiv.org/abs/2506.04824)**
(Andrews & Witteveen, ICML 2025; code: [mdda/cryptic-crossword-reasoning-verifier](https://github.com/mdda/cryptic-crossword-reasoning-verifier))
Fine-tunes Gemma2-9B to generate **20 candidate answers per clue** (given clue text +
length pattern + orientation), then a separate verifier proves/refutes each candidate by
codifying its wordplay as executable reasoning steps. New SOTA on Cryptonite (Times/Telegraph).
**Transfers directly.** This is the exact shape of lever (a) in our queue — "generate N
diverse candidates, let the proof gate filter" — independently validated as the winning
architecture on English cryptics, by the same paper family this repo's `prove.py` already
adapted (the "formalise wordplay as code, verify by execution" line in SOLVE_PROTOCOL.md
cites this same lineage). The one thing worth copying exactly: candidates are generated
BEFORE any commitment to a parse, not by iterating on a single leading guess. Our solver
does not yet have an analogous per-clue candidate-generation step — `lexicon.py` offers
pattern/anagram lookups as tools a human-or-LLM solver can call, but nothing enumerates N
independent hypotheses per clue automatically. This is today's lever.

**[Language Models are Crossword Solvers](https://aclanthology.org/2025.naacl-long.104.pdf)**
(NAACL 2025) Targets standard (non-cryptic) American-style crosswords: candidate generation
per slot + constraint propagation across the grid, closer to Berkeley Crossword Solver than
to cryptic-specific wordplay. **Partial transfer.** The GRID-LEVEL mechanic (rank candidates
per slot, propagate crossing constraints, global optimization) is exactly lever (d) in our
queue and already flagged as "worth doing once candidate lists are good" in PLAN_V2. But the
per-slot candidate generation itself is definition-lookup / clue-embedding similarity, which
assumes a non-cryptic definitional clue — does not transfer to wordplay-driven answers where
the surface reading is deliberately misleading. Confirms our existing prioritization (candidates
first, then grid optimization) rather than adding anything new.

**[What Makes Cryptic Crosswords Challenging for LLMs?](https://arxiv.org/pdf/2412.09012)**
Diagnoses LLM failure modes on cryptic clues: models struggle most with (1) identifying which
end holds the definition vs. the wordplay, and (2) multi-step charades/containers requiring
letter-exact tracking. **Transfers directly to lever (b).** This is independent confirmation
that definition-span detection is a real, distinct failure mode worth isolating as its own
step rather than folding into general "solve the clue" prompting — matches our queue's framing
("a cryptic clue's definition sits at one END; classify which end, solve wordplay from the
remainder"). Also reinforces why `word_order` in prove.py exists: the paper's #2 failure mode
(losing track of exact letters through multi-step wordplay) is precisely what that assertion
catches.

**[Proving that Cryptic Crossword Clue Answers are Correct](https://arxiv.org/html/2407.08824v1)**
Earlier paper in the same lineage as the ICML 2025 work above: LLM proposes an answer, then
a separate step formalises the wordplay as executable/checkable logic rather than a prose
"justification." **Already adopted here** — this is the design `solver/prove.py` implements
(is_anagram, is_container, word_order, etc. as assertions that must execute). No new action;
confirms the existing architecture is aligned with the field, not behind it.

**Hebrew NLP / morphology search:** no work found on cryptic-wordplay generation or
definition-span detection specific to Hebrew or any morphologically-rich non-English language.
General Hebrew-NLP resources (AlephBERT, YAP morphological parser, HebPipe) exist for tagging/
parsing standard prose, not wordplay. **Does not transfer** — nothing to adopt this cycle;
this confirms the project's own tooling (hspell lexicon + mined substitution dictionary +
homograph index) remains the only source of Hebrew-specific wordplay knowledge, since the
academic literature has not addressed this genre in Hebrew at all.

**Bottom line for today's lever:** the strongest, most directly-transferable finding is the
ICML 2025 paper's N=20-candidates-then-verify architecture, which matches our own
measured diagnosis (DAILY.md: "the solver produces one candidate and tries to justify it;
that is backwards") almost exactly. Implementing lever (a), candidate generation, this run.
