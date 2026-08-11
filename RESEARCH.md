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

## 2026-08-11

Re-checked all four papers already logged above (2506.04824, 2412.09012, 2407.08824,
1808.07214/general Hebrew morphology) for anything new since 2026-08-08 — no new
transferable finding; the field has not moved in three days. One paper re-read more
carefully this run:

**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824).
https://arxiv.org/html/2407.08824v1
Re-read specifically for what's novel BEYOND the execution-verified-proof idea this
project already adopted (`solver/prove.py`, credited from 2506.04824's line of work).
Two things stood out on closer reading: (1) an iterative refinement loop where a failed
proof's assertion error becomes a hint for a re-write attempt (up to 5 tries) — prove.py
already returns a hint on failure (`ProofError` messages), but nothing in this repo
*loops* on that hint automatically; that's a plausible small lever, not attempted today.
(2) definition-span candidate generation via FastText cosine-similarity against
dictionary words — **this is queue item 2 (definition-span detection)**, and confirms
the *structural* idea again (as 2412.09012 already did) without adding a Hebrew-usable
technique: there is no FastText model trained on this genre's Hebrew, and the paper's
own honest number for this compare (38-42% true-positive rate distinguishing correct
from near-correct answers) is not strong evidence the technique generalizes even in
English. Filed under: structural idea re-confirmed a third time now (SOLVE_PROTOCOL.md
already has it as queue item 2), still no free technical transfer.

**New Hebrew NLP tooling found this run: DictaBERT-seg** (dicta-il/dictabert-seg,
arXiv 2308.16687, huggingface.co/dicta-il/dictabert-seg). A fine-tuned BERT model that
does PREFIX segmentation for Modern Hebrew (splitting clitics ו/ה/ב/ל/מ/ש/כ off the
following word) — exactly the morphological gap flagged as "not attempted" in the
2026-08-06 entry above (`candidates.py`'s fodder windows are character-level, not
morphology-aware, so a clue word's leading clitic can throw off an anagram/hidden
window by exactly one letter). **Honest assessment: real candidate, not pursued today.**
It would require adding `torch`+`transformers` (~1-2GB) and downloading model weights —
a genuinely heavier dependency than anything else in this repo, which is deliberately
"plain Python, no frameworks" per its own style rule, and this environment's network
access to the *answers* corpus (14across.co.il) was itself unreliable today (see log),
so depending on a model-hub download inside `bootstrap.sh` risks making reconstruction
LESS reliable, not more. A cheap alternative that stays in the existing style: a small
hard-coded clitic-stripping pass over `_char_windows`'s candidate words (candidates.py
already has a `PREFIXES`/`SUFFIXES` list doing exactly this in `homographs.py`'s
`variants()` — that same list could be reused to generate additional stripped windows
for `candidates.py` without a new dependency). Flagged for a future lever, not today's.

**Environment finding, not a research finding, but consequential for reproducibility:**
`bootstrap.sh`'s answers-corpus fetch (step 2/6) failed completely in today's sandbox —
every plain HTTP request to 14across.co.il returned the same `sg-captcha` JS
proof-of-work challenge (HTTP 202, `sg-captcha: challenge` header), confirmed
reproducibly (5/5 fresh curls, and the actual `scraper/parse_answers.py` fetch function
with its existing retry-with-backoff also failed, 0/3 retries succeeded in ~14s). The
2026-08-06 log entry described this as "roughly half of requests, random" and fixed it
with retries; today it was a consistent, total block — plausibly because this sandbox's
outbound proxy IP differs from whatever IP the 2026-08-06 session used and is more
aggressively challenged. Worked around it by fetching through the (already
session-connected) Bright Data MCP tool instead, which does solve the JS challenge, and
feeding the returned HTML into the SAME `scraper/parse_answers.parse_page()` function
(no reimplementation) — confirmed working (28/28 clues parsed correctly for the one
puzzle needed this run; a background fetch of all 52 was still started for the full
corpus but ran far slower than a plain HTTP scrape would and did not finish in this
session's window). Not a literature finding, but worth recording: `bootstrap.sh`'s
"reconstructible from public sources" claim is now conditional on network egress not
being challenge-blocked, which is a fragility the next run should know about.
