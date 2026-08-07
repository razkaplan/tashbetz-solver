# Research log

Append-only. Each entry: date, what was searched, links, one-line summary, honest
transfer judgement for THIS project (LLM + hand-written verification DSL, Hebrew,
one specific hard setter). Be skeptical — most crossword-AI work targets non-cryptic
puzzles and does not transfer.

## 2026-08-07

Searched: cryptic crossword solving SOTA, wordplay formalization/verification,
definition-span detection, non-cryptic crossword techniques, Hebrew NLP/morphology.

### 1. Cryptic crossword solving — SOTA, candidate generation, ranking

- **"A Reasoning-Based Approach to Cryptic Crossword Clue Solving"** — Andrews &
  Witteveen, ICML 2025. [arXiv:2506.04824](https://arxiv.org/abs/2506.04824) /
  [code](https://github.com/mdda/cryptic-crossword-reasoning-verifier)
  Current published SOTA on Cryptonite (English). Pipeline: LLM generates **20
  candidate answers per clue**, then **10 wordplay hypotheses per candidate**, a
  formaliser LM rewrites each into Python assertions, executes and AST-checks them,
  with up to 2 repair iterations on failure. 32.5% top-1 (Gemini-Flash formaliser) vs
  ~8.6% for prior rule-based SOTA — a ~4x jump driven almost entirely by moving from
  single-answer generation to N-candidate sampling + execution-based filtering.
  **The paper states its own 20-candidate stage caps recall at ~45%** — the ceiling is
  candidate diversity, not the verifier. This is close to exact structural confirmation
  of our own diagnosis (stuck at ~57% coverage with ~1 candidate/clue).
  **Transfers directly.** This is the same architecture as our `prove.py` DSL
  (`is_anagram/is_reversal/is_container/means/word_order/has_length` maps closely onto
  their `is_anagram/is_synonym/is_abbreviation/is_homophone` + action-type enum). Two
  gaps worth noting: they have explicit `is_abbreviation`/initials and
  `REMOVE_FIRST`/`REMOVE_LAST` (deletion) primitives we don't; and they report
  `is_synonym()` (our `means()`) as "a significant bottleneck" — expect our `means()`
  to be the noisiest gate too, since it's the one primitive that can't be checked by
  pure combinatorics.
  Lineage: ICML-2024-workshop precursor *"Proving that Cryptic Crossword Clue Answers
  are Correct"* ([arXiv:2407.08824](https://arxiv.org/html/2407.08824v1)) and an
  ICLR-2025-workshop version *"Generating Code to Verify Cryptic Crossword Reasoning"*.
  **Failure modes to pre-empt in our own gate**: their write-up flags verifiers fooled
  by comment-only "proofs", conditional logic that bypasses assertions, logically
  disconnected proof steps, and hints that silently produce vacuous `assert False`-style
  checks. Worth an audit of whether our DSL is robust to the Hebrew-LLM analogues.

- **"Are LLMs Good Cryptic Crossword Solvers?"** — Sadallah, Kotova & Kochmar, 2024.
  [arXiv:2403.12094](https://arxiv.org/html/2403.12094)
  Benchmarks LLaMA2/Mistral/ChatGPT zero-shot, few-shot, and QLoRA-fine-tuned on
  Cryptonite. Zero-shot near 0%; best reported numbers (GPT-4-Turbo 76%) are under a
  hinted/partial-letter setting, not a blind cold-start — not comparable to our 0-letter
  starting point. No definition-span detection attempted; treats the clue holistically.
  **Weak transfer.** Only real signal: crossing-letter hints massively help, which
  supports our existing iterative grid-propagation passes, but offers nothing new for
  the candidate-generation lever itself.

- **"What Makes Cryptic Crosswords Challenging for LLMs?"** — Sadallah, Kotova &
  Kochmar, COLING 2025. [arXiv:2412.09012](https://arxiv.org/pdf/2412.09012)
  Diagnostic study of LLM failure modes by clue-type; confirms surface-reading
  indirection (not vocabulary) drives failures. **No new technique — background only.**

- **"Language Models are Crossword Solvers"** — Saha et al., NAACL 2025.
  [arXiv:2406.09043](https://arxiv.org/pdf/2406.09043)
  Reports gains on cryptic-clue benchmarks via prompting/search (no fine-tuning), and
  *separately* a search algorithm hitting 93% on non-cryptic NYT grids — the 93% number
  is for a different puzzle type; don't conflate the two when citing this. **Partial
  transfer**: cryptic-clue component relevant as background; NYT component is non-cryptic
  grid search (see §3).

- **"Decrypting Cryptic Crosswords"** — Rozner, Potts & Mahowald, NeurIPS 2021.
  [arXiv:2104.08620](https://arxiv.org/pdf/2104.08620) (pre-2023, included as necessary
  foundation — this is the paper that introduced the Cryptonite dataset).
  Its CFG-based rule-solver baseline **enumerates BOTH definition-at-start and
  definition-at-end parses** and scores wordplay-output-vs-definition similarity via
  WordNet — it does not use a dedicated definition-boundary classifier at all.
  **This is the closest prior art to our "which end is the definition" lever, and it
  argues against building a classifier**: brute-force try both parses, let a downstream
  scorer (their WordNet similarity; our `means()`/proof gate) arbitrate. Directly
  informed today's implementation choice (see below).

### 2. Formalizing wordplay as executable/checkable programs

This is the Andrews & Witteveen 2025 line above (§1) — it is the up-to-date, and
apparently only, published instance of exactly our "wordplay as executable proof"
pattern for cryptics. No other 2023-2026 paper found doing this for cryptics; it looks
like a single two-person research line (mdda.net) currently owns this niche. See §1 for
the DSL-primitive comparison and failure-mode warnings — both directly actionable
against `solver/prove.py`.

### 3. Non-cryptic crossword solving — skeptical read

- **Berkeley Crossword Solver** — Wallace, Tomlin et al., ACL 2022.
  [arXiv:2205.09665](https://arxiv.org/abs/2205.09665) (pre-2023, still the reference
  architecture). Pipeline: neural QA model → n-best **scored** candidates per clue →
  **loopy belief propagation** over the grid's crossing constraints → local search
  repair. NYT accuracy 57% -> 82%.
  **Confirmed skeptical read**: their candidate generator is a bi-encoder trained on
  direct-definition American clue/answer pairs — it has nothing to say about cracking
  wordplay, so it does NOT help our actual bottleneck (getting correct wordplay-derived
  candidates). The one thing worth stealing is the *shape* — scored candidates + belief
  propagation over crossings — for our grid-filling stage, strictly AFTER verified
  candidates with confidence scores exist. Matches PLAN_V2 lever A, which is correctly
  sequenced after candidate generation, not before.

- **Dr.Fill** (Ginsberg 2011, still referenced in 2023+ surveys) and **WebCrow French**
  (2023, [arXiv:2311.15626](https://arxiv.org/html/2311.15626)): same story — weighted
  CSP / retrieval-based grid solving for non-cryptic, non-English puzzles. Confirms the
  post-verification grid-assembly architecture generalizes across languages, but neither
  touches wordplay. **No transfer to today's lever.**

- **CrossWordBench**, 2025. [arXiv:2504.00043](https://arxiv.org/abs/2504.00043) — LLM
  grid-constraint reasoning benchmark, not cryptic-specific as far as accessible
  materials show. **Marginal**: possibly reusable as an eval-harness idea (accuracy vs.
  % of grid pre-filled), not a solving technique.

- **Bottom line for §3**: consistent with the brief's expectation — non-cryptic
  crossword-AI does not transfer to the candidate-generation bottleneck. Its only clean
  transfer point (loopy BP / weighted CSP for grid assembly) is already lever A in
  PLAN_V2, correctly sequenced for later.

### 4. Hebrew NLP / morphology

- **DictaBERT-seg** (dicta-il, HuggingFace) — a fine-tuned model specifically for
  prefix-segmentation (ב/ל/מ/ש/ה/ו/כ) in unvocalized Hebrew.
  **Directly useful, not yet adopted**: an off-the-shelf alternative to asking the LLM to
  strip prefixes inline. Worth a future eval as a preprocessing pass before mechanism
  classification — flagged for a future run, not today's lever.

- **"Do Pretrained Contextual Language Models Distinguish between Hebrew Homograph
  Analyses?"** — EACL 2023 / extended [arXiv:2405.07099](https://arxiv.org/abs/2405.07099).
  Studies exactly our שרה-type homograph problem. Finding: contextual Hebrew models
  handle segmentation-level ambiguity (is a ו a prefix or not) reasonably but are
  comparatively weak at pure **word-sense** disambiguation, and degrade further as the
  number of simultaneous readings grows past 2.
  **Directly relevant and cautionary**: this is the exact device `solver/homographs.py`
  targets. The finding argues AGAINST leaning on a single best-guess disambiguator and
  FOR generating multiple candidate readings and letting downstream verification filter
  — i.e. the same "more candidates, verify downstream" strategy as §1, applied to
  homographs specifically. Supports extending `candidates.py`-style generation to
  homograph readings in a future pass, not attempted today.

- **SPLINTER** (2025, [arXiv:2503.14433](https://arxiv.org/abs/2503.14433)) — linearizes
  Hebrew/Arabic/Malay root-and-pattern morphology for better subword tokenization.
  **Not directly usable**: a tokenizer-training technique, not a plug-in library: would
  require re-tokenizing/fine-tuning, out of scope for an LLM-prompting project. Noted for
  awareness only.

- **"MRL Parsing Without Tears: The Case of Hebrew"**, ACL Findings 2024 — new SOTA
  Hebrew POS/dependency parsing via a flipped whole-token pipeline.
  **Secondary relevance** — useful only if we later need POS/dependency signal to help
  `means()` judge synonym plausibility. Not a fix for today's bottleneck.

- **Dvd848/Crossword-Solver** (GitHub, not a paper) — an open Hebrew word-pattern lookup
  tool (DAWG-indexed, Wiktionary/Wikipedia/Hebrew-WordNet/hspell). Not cryptic-aware, but
  legitimate off-the-shelf infrastructure for pattern lookup — we already have an
  equivalent in `solver/lexicon.py`, so low incremental value.

### 5. Definition-span / definition-boundary detection

**No dedicated 2023-2026 paper on automatic definition-boundary classification for
cryptic clues was found** — checked from several angles (sequence labeling, classifier
framing, commercial-solver framing). This is a real literature gap, not a search miss:

- The rule-based era (§1, Rozner et al. 2021's CFG solver) doesn't classify the
  definition side — it enumerates both parses and lets a downstream scorer decide.
- The current SOTA (Andrews & Witteveen 2025) sidesteps the problem entirely: their
  training data has **manually annotated** definition spans; the pipeline consumes
  pre-segmented clues rather than detecting the split automatically.
- Sadallah et al. 2024 treats the clue holistically, no boundary detection at all.

**No evidence that automatic definition-span classification is either a solved problem
with a reusable technique, or something the strongest systems found necessary** — both
successful lines avoid a standalone classifier, either by brute-force enumeration + a
downstream scorer, or by not automating it (human annotation).

### Bottom line

The research converges on one conclusion, from three independent angles: (1) the
closest analogous SOTA (Andrews & Witteveen) attributes its own accuracy ceiling
directly to candidate-generation width, not the verifier, and its ~8.6%→32.5% jump is
structurally the same move we're making; (2) no cryptic-solving system, past or
present, uses a standalone definition-boundary classifier — the historically successful
alternative is to enumerate both hypotheses as part of candidate generation and let the
verifier arbitrate; (3) the Hebrew-homograph literature independently argues for
generate-many-then-verify over single-shot disambiguation.

**This directly supports today's implementation choice**: `solver/candidates.py`
generates candidates by mechanism (anagram/reversal/hidden) and, for every hit, tags
which end of the clue is left over as the definition-span hypothesis — folding lever
(b) into lever (a) as an axis of the same generator, rather than building a separate
upstream classifier, exactly as the literature (and the CFG-solver precedent
specifically) recommends.
