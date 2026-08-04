# Research log — daily improvement agent

Append-only. Each entry: link, one-line summary, honest transfer judgement for a Hebrew
cryptic (יורם הרועה) solved by an LLM+tool harness, not a trained model.

## 2026-08-04

- **A Reasoning-Based Approach to Cryptic Crossword Clue Solving** (2025) —
  https://arxiv.org/html/2506.04824v1
  Pipeline: small LMs propose (answer, wordplay) candidates, a separate LM formalises
  each proposal as executable Python, a verifier runs it and only proved candidates
  survive. TRANSFERS DIRECTLY — this is the paper `solver/prove.py` already implements
  (the DAILY.md log even cites it by name). What it does that we do not yet do: it
  treats candidate *proposal* as a first-class generation step with its own model call,
  separate from and prior to verification. Our solver still mostly generates one
  candidate ad hoc per clue and asks prove.py to bless it after the fact — proposal and
  verification are conflated. This is the exact gap DAILY.md's lever queue item (1)
  names as the measured bottleneck, and this paper is direct evidence for prioritizing
  it: their ablations show verification alone (no diverse proposal stage) plateaus well
  below their headline number.

- **What Makes Cryptic Crosswords Challenging for LLMs?** (2025) —
  https://arxiv.org/pdf/2412.09012
  Confirms the definition sits at one END of the clue (start or end), never split
  across the middle, and that state-of-the-art LLMs mis-locate the definition span far
  more often than they fail the wordplay mechanics once the span is known. TRANSFERS AS
  DIAGNOSIS, uncertain as a technique: their fix is a fine-tuned classifier trained on
  ~470k English cryptic clues with gold definition-span labels. We have no Hebrew
  definition-span-labelled data at all (our corpus has answer + crowd explanation text,
  not span-annotated clues), so we cannot replicate their classifier. What DOES transfer
  is the structural fact itself (definition-at-an-end) as a generation heuristic: for
  each clue, hypothesizing "definition = first k words" and "definition = last k words"
  as two competing structural readings, and generating wordplay candidates from the
  complementary remainder under each hypothesis, is implementable today without any
  labelled data. This is lever queue item (2), and it composes with item (1) rather than
  competing with it — folded both into today's candidate generator.

- **Decrypting Cryptic Crosswords: Semantically Complex Wordplay Puzzles as a Target
  for NLP** (2021) — https://arxiv.org/abs/2104.08620
  English cryptic dataset + curriculum-learning baselines (pretrain on anagram-unscramble
  tasks, then fine-tune). Concludes cryptics remain unsolved even with curriculum
  fine-tuning. DOES NOT TRANSFER — this is a from-scratch model-training result; we run
  a fixed LLM plus tools, no training loop, and the paper's own conclusion (still fails
  to generalize) is not encouraging for a training-based approach here even if we had
  the Hebrew data to attempt it. Reinforces PLAN_V2's existing deprioritization of
  Track-B fine-tuning.

- **Cryptonite: A Cryptic Crossword Benchmark for Extreme Ambiguity in Language**
  (2021) — https://arxiv.org/pdf/2103.01242
  Large (470k) English cryptic clue benchmark; the "SOTA system" figure DAILY.md's
  state table compares corpus size against traces back to work built on this dataset.
  DOES NOT TRANSFER DIRECTLY (English, not Hebrew, no equivalent Hebrew corpus at that
  scale exists or is buildable short-term) but the scale comparison itself is the right
  frame for judging our 8,249-pair corpus: we are two orders of magnitude smaller, which
  is exactly why PLAN_V2 treats corpus growth as "the long game" rather than this week's
  lever.

- **Proving that Cryptic Crossword Clue Answers are Correct** (2024) —
  https://arxiv.org/html/2407.08824v1
  A separate formal-verification take: represent wordplay as a typed grammar and check
  an answer against it deductively rather than via ad hoc Python assertions. TRANSFERS
  PARTIALLY, not urgent: our prove.py's assertion DSL (is_anagram, is_container,
  is_hidden, means, word_order, has_length) already covers the mechanism types this
  paper formalises; the incremental gain from a typed-grammar rewrite would be catching
  a class of malformed proof we have not actually observed failing. Lower priority than
  candidate generation, which the error profile in PLAN_V2 identifies as the real gap.

- **Hebrew NLP resources survey** (NNLP-IL/Hebrew-Resources, ongoing) —
  https://github.com/NNLP-IL/Hebrew-Resources/blob/master/models_tools_services.rst,
  plus **NeoDictaBERT** (2026, https://arxiv.org/pdf/2510.20386) and the **YAP**
  morphological parser it surveys. MOSTLY DOES NOT TRANSFER YET: these are
  general-purpose Hebrew morphological analyzers/LLMs (root+pattern extraction, clitic
  segmentation, disambiguation) aimed at standard prose, not cryptic wordplay. The one
  piece worth flagging for a future lever: a root-extraction step (שורש) could make the
  anagram/container mechanisms root-aware (Hebrew roots recombine with different
  patterns, so "letters that anagram" is a weaker signal here than in English — a root
  match might be a stronger prior than a raw letter-multiset match for some clue types).
  Not attempted today; today's lever stays at the raw-letter level like the rest of the
  existing lexicon/anagram tooling, to keep the change attributable to one thing.

**Bottom line for today's lever**: the two highest-value, actually-transferable ideas
from the literature — diverse candidate *proposal* before verification (Cryptonite/
Reasoning-Based paper), and definition-at-an-end as a structural generation heuristic
(What Makes Cryptic Crosswords Challenging) — are exactly DAILY.md's queue items (1) and
(2), and neither requires data we don't have. Implementing them together today as one
candidate-generation tool that (a) tries both ends as the definition hypothesis and (b)
proposes anagram/reversal/hidden/charade candidates from the complementary wordplay
span, feeding into the existing prove.py gate.
