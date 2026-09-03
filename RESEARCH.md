# Research log — daily improvement agent

One entry per run: what was found, one-line summary, and an honest judgement of whether
it transfers to a Hebrew cryptic solver with an 8k-clue corpus. Default skepticism: most
crossword-AI work targets non-cryptic (American-style) puzzles and does not transfer.

## 2026-09-03

Bootstrap hit the 14across hard wall again — 7 consecutive answer-page fetches returned
`None: 0 clues` after full retry-with-backoff each (worst case ~190s/URL x 52 puzzles
would be hours), matching the established hard-wall failure mode documented since
2026-08-19 rather than the intermittent ~50%-random one. Killed the background scrape
after confirming the pattern rather than waiting it out, per established practice, and
worked entirely from the no-14across image-fallback technique (bootstrap.sh step 6) for
both clue text and gold letters on the canonical dev puzzle (2026-05-29).

**General search: "cryptic crossword clue candidate generation container indicator
wordplay parsing 2026" and "cryptic crossword solver definition span detection neural
2025 2026 arxiv".** Surfaced only the same paper family already logged repeatedly since
2026-08-06 (2506.04824, 2407.08824, 2104.08620, 2406.09043, 2403.12094) — no new academic
work found on candidate generation or definition-span/fit scoring. **Transfer: none new,
consistent with every literature pass since 2026-08-27.**

**Targeted search for container/insertion CANDIDATE GENERATION specifically** (not just
detection/verification, since that's this run's chosen lever): "container OR insertion
wordplay candidate generation algorithm crossword clue solver enumerate splice". Turned
up general descriptions of the container device (a Stella Zawistowski blog post,
"Decrypting the Cryptic #3: Containers") that match what PLAYBOOK.md §1.4 already
documents in far more depth for this specific setter, and one genuinely new item worth
checking directly rather than citing at a glance: `github.com/nikcholer/cryptic-solver`,
a 2026 neuro-symbolic demo (LLM clue parsing + deterministic Python validation) that
came up in the first search. Fetched and read it directly rather than trusting the
title: its container handling is **LLM-guided, not mechanically generated** — "the
system doesn't appear to enumerate all possible word-inside-word combinations; instead,
it relies on LLM interpretation to guide which components should combine," then
validates the result against the dictionary. **Transfer: this is a useful negative
data point, not a lead** — it confirms (does not contradict) that exhaustively
enumerating container candidates mechanically, the way this run's lever does, is not
something any published or public solver (academic or hobbyist) already does; every
one treats container as a verify-only step guided by a language model's own reading
of the clue, exactly this project's OWN standing approach before today. That absence
of precedent is itself the reason `container_candidates` (see DAILY.md) is worth
building rather than skipping: it closes a gap nobody else's public work has closed
either, not just this project's.

**Conclusion.** No new external resource changes any standing conclusion (BM25 over
embeddings, no definition-fit scorer exists to build on, Hebrew WordNet answers the
wrong question). Today's lever is therefore an internal one: PLAYBOOK.md §1.4 names
the container device as ~10-12% of this setter's clues, the fourth-most-common
mechanism after charade/anagram/double-definition, and until today `solver/prove.py`
could VERIFY a container proof (`is_container`, present since the proof gate was
built) but no generator in `solver/candidates.py` ever produced a container candidate
to hand it — pure verification infrastructure with nothing feeding it, the same shape
of gap PR #39/#41 found in `retrieval_candidates()`'s query function this week
(infrastructure that existed but was never exercised as designed).

## 2026-08-31 (session 3, solver daily loop)

Bootstrap hit the same hard 14across wall as 2026-08-19/08-26/08-27/08-28/08-30 (7
consecutive answer-page fetches returned `None: 0 clues` within the first ~2 minutes of
retry-with-backoff, matching the established hard-wall failure mode rather than the
intermittent ~50%-random one) — killed rather than waited out. `solver/lex/culture.json`
and `solver/lex/substitutions.json` are committed (not gitignored), so no rebuild was
needed for those; worked entirely from the no-14across image-fallback technique for the
one new dev puzzle this run needed.

Per the scheduled task's own framing, checked first for a genuinely new, buildable-today
idea on definition-fit scoring (queue item 9) before defaulting to another corpus-growth
measurement of `retrieval_candidates` (explicitly discouraged this run after six
consecutive days on that exact lever shape).

**"cryptic crossword clue candidate answer definition semantic fit scoring 2026 arxiv" /
"cryptic crossword solver definition span classification new method 2026" (general
search).** Surfaced only the same paper family logged repeatedly since 2026-08-06
(2506.04824, 2407.08824, 2104.08620/2103.01242, 2406.09043, 2403.12094) plus the same
OpenReview mirrors (Bo5eKnJPML) already confirmed 2026-08-26 to resolve to 2506.04824 and
still blocked by the bot-verification page today (checked directly again, not assumed).
**Transfer: none new** — eighth-plus consecutive pass over this exact literature finding
nothing beyond what is already logged.

**NEW THIS RUN: Italian (non-cryptic) crossword retrieval/ranking line, checked directly
rather than dismissed by title.** A different search angle ("retrieval augmented answer
verification crossword clue reverse dictionary lookup scoring") surfaced a CLiC-it
(Italian computational linguistics workshop) paper family not previously logged here:
Giovannetti et al., "A Multi-Strategy Approach to Crossword Clue Answer Retrieval and
Ranking" (CLiC-it 2021) plus two 2025/2026 successors at the same venue's Cruciverb-IT
shared task (`ceur-ws.org/Vol-4195/15.pdf` "UniTor at Cruciverb-IT: Retrieval-Augmented
Two-Step..." and `/46.pdf` "Retrieval-Based Approaches for Italian Crossword Clue...",
plus "Crossword Space: Latent Manifold Learning for Italian Crosswords and Beyond",
2025.clicit-1.26). The 2021 paper's abstract was reachable via search summary (confirms:
neural embedding retrieval/ranking for STANDARD Italian/English crossword clues, not
cryptic); the three 2025/2026 PDFs could not be read as text (no `pdftotext`/`pypdf` in
this environment, and WebFetch returns raw PDF bytes for these hosts rather than parsed
text — a genuine tooling gap, disclosed rather than papered over with an assumed
summary). Confirmed via the reachable abstract and the shared task's own name
(Cruciverb-IT = Italian, standard/definitional crosswords, not cryptic) that this entire
line targets exactly the case RESEARCH.md's header default-skepticism already names:
non-cryptic puzzles. **Transfer: none** — even if the unread PDFs contained a genuinely
new reranking technique, it would be solving a different problem (matching a plain
definition clue to an answer via embeddings) than this project's gap (choosing among
several MECHANICALLY-valid wordplay-derived candidates for the one the setter intended),
which is why past passes on embedding-rerank approaches (2412.09012, 2026-08-06/20/23/24)
already concluded "reranks a list a separate mechanism produced, doesn't generate, and no
Hebrew crossword-tuned embedding space exists to port it to" — nothing here changes that.

**Checked one hobby/toy resource directly rather than by name alone: github.com/G-Kurup/
cryptics-llm** (surfaced by a broader "LLM judge candidate rerank cryptic 2026" search).
Fine-tunes T5-small on 169,993 scraped Guardian cryptic clues (English), 18.4% test
accuracy, candidate-ranking limited to "generate N beam candidates, keep those matching
the enum length." **Transfer: none actionable** — same answer-first shape 2506.04824
already covers (logged 2026-08-30), and the data-scale gap alone rules it out: this
hobby project needed ~170k training clues to reach 18% on English; this project's whole
corpus is ~8k Hebrew clue-answer pairs. Confirms rather than adds to the standing
"fine-tuning is a different, much larger effort, not a drop-in lever" conclusion.

**Conclusion for today's lever.** Ninth-plus consecutive research pass (2026-08-22/23/24/
25/26/27/28/29/30/31) with nothing new and buildable on definition-fit scoring — the
queue's own 2026-08-24 instruction ("the next attempt on this item should assume none
exists and work from the project's own data... or be scoped as a genuinely new internal
idea, not another literature sweep") is followed literally today: no new internal idea
for definition-fit scoring surfaced either, so item 9 is left untouched again rather than
forcing a stub. Per the scheduled task's explicit steer away from another
`retrieval_candidates` corpus-growth measurement, today's lever is queue item 1(c)'s own
named next step: a SECOND puzzle's data point for `culture_category_candidates`
(2026-08-24, measured only once, n=1 fired-clue). See DAILY.md for the transcription,
measurement, and a genuinely new methodological finding this second data point surfaced
(a held-out-safety-filter blind spot, distinct from both this item's already-known
homograph-misdirection failure mode and a plain corpus-coverage gap).

## 2026-08-30

Bootstrap hit the same hard 14across wall as 2026-08-19/08-26/08-27/08-28 (4 consecutive
answer-page fetches returned `None: 0 clues` after several minutes of retry-with-backoff
each — killed rather than waited out further, matching the established hard-wall failure
mode rather than the intermittent ~50%-random one). Worked entirely from the no-14across
image-fallback technique documented in bootstrap.sh step 6.

Research this run followed the scheduled task's own stated priority order: candidate
generation (diverse candidates by mechanism / by definition-span hypothesis) first, then
Hebrew NLP/morphology, before falling back to the queue's own next concrete step.

**"cryptic crossword clue solving candidate generation diversity 2026 arxiv" /
"definition detection cryptic crossword clue span identification neural 2025 2026"
(general search).** Surfaced only the same paper family logged repeatedly since
2026-08-06 (2506.04824 ICML 2025 "A Reasoning-Based Approach to Cryptic Crossword Clue
Solving", 2407.08824, 2104.08620, 2406.09043). One detail newly worth naming even though
the paper itself isn't new to this log: 2506.04824's candidate generator hypothesizes
ANSWERS directly (a fine-tuned Gemma2 9B proposes a word/phrase from clue+pattern, THEN a
separate step searches for wordplay to justify it), which is the inverse of this
project's `candidates.py` (mechanism-first: enumerate what anagram/hidden/reversal/
substitution/homograph CAN produce, then check the lexicon). This project's live blind
trials already do the answer-first version informally (a solver agent proposes an answer
from reasoning, then `prove.py` checks it) — the paper doesn't add a new technique so
much as name what the live trials are already doing versus what the offline mechanical
generator does. **Transfer: none actionable today** — replicating the paper's version
would mean fine-tuning a small LM on this project's own explanation corpus, which is a
different, much larger effort than one day's lever, not a drop-in addition to
`candidates.py`.

**"non-English cryptic crossword solver templatic morphology candidate generation 2025
2026".** Surfaced one genuinely new citation to this log: Zeinalipour et al.,
"From Arabic Text to Puzzles: LLM-Driven Development of Arabic Educational Crosswords"
(arXiv:2501.11035, ACL LoResLM 2025) and the related ArabIcros line of work. Checked
directly, not assumed from the title: this is crossword-clue GENERATION from source text
for educational use (fine-tuning Llama3-8B to turn a text passage into ordinary
definition-style crossword clues), not cryptic-clue SOLVING, and the crosswords involved
are standard (definition-only), not cryptic (no wordplay layer at all). Despite Arabic
sharing Hebrew's root-and-pattern templatic morphology, this paper's task and direction
(text -> clue) is the opposite of what this project needs (clue -> answer via wordplay),
and it never touches wordplay decomposition. **Transfer: none** — surfaced by a search
this project hadn't tried before, but doesn't apply once actually read.

**"crossword definition always at start or end heuristic parser cryptic clue
segmentation".** Reconfirmed the standard English-cryptic heuristic (definition is a
prefix or suffix span; the rest is wordplay; clues parse via a restricted CFG) that
`defspan.py` (2026-08-19) already tested against this setter's own clues and found does
NOT hold well here: only 25% of clues even have a mechanically-locatable wordplay window,
and 29% of those are interior, not edge. **Transfer: none new** — this is confirmation of
the premise `defspan.py` already falsified for this specific setter, not a new lead;
re-attempting definition-span classification on the strength of the ENGLISH-cryptic
literature restating its own textbook heuristic would be re-fighting a already-measured
loss with the same signal.

**Hebrew morphology/NLP.** No new 2026 resource beyond RFTokenizer/HebPipe/DictaBERT-seg/
YAP/Splintering (arXiv 2503.14433) already logged repeatedly since 2026-08-06/08-27.
**Transfer: none new.**

**Conclusion for today's lever.** Sixth-plus consecutive literature pass with nothing
new and buildable on candidate generation or definition-fit/span scoring; the one new
citation found (Arabic crossword generation) doesn't transfer once read past its title.
Per DAILY.md's own explicitly-flagged, twice-repeated "NOT DONE" item under queue 1(d)
(2026-08-28 and 2026-08-29 both name it: re-measure 2026-06-26 — the puzzle 2026-08-28's
corpus-growth finding named as still needing a bigger corpus — with the grown
private_defs corpus, which no run has done because 14across kept missing that date and a
from-scratch re-transcription was never finished), today's lever is exactly that
still-open gap: transcribe 2026-06-26 in full (28/28 clues this time, closing the
18/28 partial gap 2026-08-26 left, since the across-clue column that's sometimes missing
in other weeks turned out to be present in this week's own image once its column-wrap
onto the next print column was tracked down) and re-measure `retrieval_candidates`
against a freshly-crawled corpus. See DAILY.md for the transcription/audit/measurement
trail.

## 2026-08-29

Bootstrap this run actually succeeded fully at 14across (52/52 puzzles, 1,457 clues) —
the first clean run in several consecutive attempts (2026-08-19/08-26/08-27/08-28 all hit
a hard wall). Research this run followed the scheduled task's own priority order: general
candidate-generation/definition-span literature first, then Hebrew morphology, then
definition-fit scoring (item 9), each checked against what's already logged here before
searching, to avoid repeating a dead search.

**"cryptic crossword clue solving diverse candidate generation arxiv 2026" (general
search).** Surfaced only the same paper family logged repeatedly since 2026-08-06/08-15
(2506.04824 ICML 2025, 2406.09043, 2407.08824). **Transfer: none new** — this is now the
sixth-plus consecutive research pass finding nothing beyond what's already logged; the
field has not produced a new diverse-candidate-generation technique since this project
started tracking it.

**"Hebrew nonconcatenative morphology root pattern generation NLP 2026".** Surfaced the
same Splintering paper (arXiv 2503.14433, logged 2026-08-27) plus one paper not
previously found by name in this search but already independently logged here on
2026-08-2x under a different query: arXiv 2603.15773 ("Morphemes Without Borders:
Evaluating Root-Pattern Morphology in Arabic Tokenizers and LLMs") — confirmed via grep
this is already in RESEARCH.md (Arabic, not Hebrew, tokenizer-evaluation not a
generation tool this project could call). **Transfer: none new.**

**"definition fit scoring candidate answer cryptic crossword semantic match 2026" (item
9's own gap).** Surfaced only the existing paper family plus unrelated daily-cryptic
hint-site pages (not research). One general solving-heuristic mention ("check semantic
fit plus mechanical fit") restates what SOLVE_PROTOCOL.md and PLAYBOOK.md already encode
by hand; no scorable/buildable resource. **Transfer: none** — this is the fourth research
pass on this exact gap (after 2026-08-22/23/24) finding nothing new; per the queue's own
note, item 9 should not be attempted again without a genuinely new finding, and today's
search is one more confirmation there isn't one yet.

**Conclusion for today's lever.** Fifth-plus consecutive literature pass with nothing
new and buildable on candidate generation, Hebrew morphology, or definition-fit scoring.
Per the queue's own explicitly-flagged next step for item 1(d) (2026-08-28: "a FULLER,
unbounded `crawl_defs.py note` crawl... and re-measuring the 2026-06-26 and/or
2026-07-10 puzzles... against the grown corpus"), and given 14across worked cleanly this
run (simpler gold-answer path than the image-fallback grid technique), today's lever is
that continuation: a genuinely unbounded `note.co.il` crawl (no 15-minute stop this
time) alongside a fresh `mordo` re-crawl, re-measured on a freshly transcribed
2026-07-10 (clue text from its image, gold answers from real 14across data this time,
not the image-fallback solution-grid technique). See DAILY.md for the measurement.

## 2026-08-28

Bootstrap: `./bootstrap.sh --dev-only` hit the same hard 14across wall as
2026-08-19/08-26/08-27 (killed after 170s with only 1/52 puzzles recovered, the rest
`None: 0 clues`) — not fought further, per standing precedent; worked entirely from the
public-CDN image fallback (fetched `data/images/2026-05-28.jpg` and `2026-06-04.jpg`
directly, bypassing bootstrap's sequential step order, since steps 3-6 do not depend on
step 2 finishing). Research this run focused on today's scheduled-task priority (candidate
generation, diverse-hypothesis and definition-span framing) and, failing new material,
queue item 1(d)'s own repeatedly-flagged concrete next step: `crawl_defs.py note`, the one
external definitions source never crawled this project's lifetime.

**General search: "cryptic crossword clue definition location structural parser 2026
arxiv", "arxiv September 2026 cryptic crossword wordplay generation candidates".**
Surfaced only the same paper family already logged repeatedly (2506.04824, 2412.09012,
2407.08824, 2104.08620, 2403.12094) — 2506.04824 (ICML 2025, "A Reasoning-Based Approach
to Cryptic Crossword Clue Solving") re-confirmed as the closest SOTA match to this
project's own generate-candidates -> formalise -> prove structure (20 answer candidates x
10 wordplay guesses per candidate, then a code-formalising verifier), already logged
2026-08-15 and cited again 2026-08-27. **Transfer: none new** — fifth-plus consecutive
pass over this literature finding nothing not already logged; the field has not produced
a new diverse-candidate-generation or definition-location technique since this project
started tracking it.

**Considered and rejected today's "definition-span hypothesis" framing from the scheduled
task's own wording** before touching code: the idea would be to hypothesize each CLUE END
as the definition and restrict `candidates.py`'s anagram/hidden/reversal character-window
scan to the residual (non-definition) letters, generating one candidate set per hypothesis
instead of scanning the whole clue at once. Checked directly whether this could add
recall, not just assumed: `_char_windows()` already slides across the FULL joined-clue
string, so windows built from a residual (one end's words removed) are a STRICT SUBSET of
what the full scan already finds — end-word removal only shrinks which windows exist, it
does not create new adjacencies unless the definition sits in the interior (item 8/17's
own 2026-08-19 finding: only 25% of clues even have a mechanically-locatable single-window
span, and 29% of those are interior). So this framing could only ever restrict/re-rank
existing candidates, not grow `recall@N` — and re-ranking without a live solve pass to
score against is not independently measurable today. **Transfer: a real idea, but not a
recall-moving one, and 2026-08-19's defspan finding (do not re-attempt without a
fundamentally different signal) already covers the "classify-and-restrict" shape of it.**
Not implemented — recorded as a considered-and-rejected path rather than silently dropped.

**Hebrew morphology / NLP** — no new 2026 resource beyond RFTokenizer/HebPipe/DictaBERT-seg/
YAP already logged repeatedly since 2026-08-06. **Transfer: none new.**

**Conclusion for today's lever.** No new external finding reopens either struck queue item
or unseats the standing diagnosis (candidate generation, not verification, is the
bottleneck; `retrieval_candidates` is the only sub-lever of it that has moved recall at
all across three independent measurements). Today's lever is therefore the queue's own
long-flagged, still-open internal gap: `scraper/crawl_defs.py note` (note.co.il) has never
been crawled this project's lifetime, despite being named as the concrete next step in
three consecutive log entries (2026-08-25, 2026-08-26, 2026-08-27). Growing the
`private_defs` retrieval corpus with a second, independent source is not a literature
lever, but it is the best-evidenced use of today's one-lever budget given what did and
did not turn up above.

## 2026-08-27

Bootstrap found 14across fully walled today (0/52, matching the 2026-08-19/08-26
hard-wall failure mode, not the ~50%-random one) — a direct single-URL fetch of
2026-07-17's answer page also failed after 8 retries, confirming this wasn't just
slow, it was blocked. Worked entirely from the public-CDN image fallback (see
DAILY.md's log entry for the transcription/gold-recovery trail). Research this run
focused on today's queue priority per the scheduled task itself: candidate
generation (diverse candidates per clue by mechanism/definition-span) and, failing
new material there, closing PR #27/#28's own flagged gap (retrieval_candidates never
live-trialed).

**"Diverse candidate generation cryptic crossword LLM 2026" / "charade segmentation
dynamic programming wordplay decomposition" (general search).** Surfaced only the
same paper family already logged repeatedly here (2506.04824, 2412.09012, 2406.09043,
2407.08824, 2104.08620 — the Cryptonite origin paper, now cited directly rather than
only by inheritance). **Transfer: none new** — fourth-plus consecutive pass over this
literature turning up nothing not already logged; the field has not produced a new
candidate-generation-by-diverse-hypothesis technique since this project started
tracking it.

**Charade/segmentation background (crosswordunclued.com, cryptichelper.com,
bestforpuzzles.com — solver-education sites, not research).** Confirmed the general
human-solver heuristic this project's PLAYBOOK.md already encodes: charades often
carry NO indicator word (breakpoints found by testing divisions, not by a lexical
cue), consistent with the 2026-08-19 defspan finding that this setter's devices are
often unmarked. **Transfer: none new** — restates, does not add to, the standing
diagnosis.

**NEW: "Splintering Nonconcatenative Languages for Better Tokenization" (Gazit,
Shmidman, Shmidman, Pinter; arXiv 2503.14433).**
https://arxiv.org/abs/2503.14433 , code at github.com/MeLeLBGU/Splintering
A pre-processing step ("SPLINTER") that rearranges Hebrew/Arabic/Malay/Georgian text
before BPE/UnigramLM tokenization so a subword tokenizer's contiguous-substring
assumption stops fighting Hebrew's proclitic-stacking morphology (up to 2-5 letters
of ב/ל/מ/ש/ה/ו/כ chained onto a word, 100+ possible prefix permutations, most too
sparse to earn their own vocabulary token). Evaluated via BERT-architecture Hebrew
LM downstream tasks. **Transfer: interesting but does not apply here.** This is a
tokenizer-pretraining technique for training a language model from scratch — this
project has no LM to pretrain and does no subword tokenization anywhere in the
pipeline (`candidates.py`'s fodder search is character-window based, not token-
based). It is adjacent to, but not the same problem as, PLAN_V2.md item F's flagged
gap (`homographs.py`/`candidates.py` don't systematically strip proclitic prefixes
before matching) — that gap needs a Hebrew morphological ANALYZER at solve time
(YAP, confirmed real and available per 2026-08-06's entry, still not integrated),
not a tokenizer pre-processing step for model training. No change to the standing
"not attempted, flagged for later" status of that item.

**"A crossword solving system based on Monte Carlo tree search" (ScienceDirect,
2024).** Relevant to queue item 4 (global constraint optimization over ranked
candidates), not candidate generation — MCTS as an alternative to belief propagation
for the joint-grid-optimization stage. **Transfer: filed for later, not now** —
2026-08-16's finding (candidate quality must clear a materially higher bar before
optimization-over-candidates is worth building) still holds; this is one more
concrete technique to consider WHEN that stage is reached, not a reason to reorder
the queue today.

**"Towards a Semantic Approach for Candidate Answer Generation in Solving Crossword
Puzzles" (ResearchGate).** WordNet-relation-based candidate generation for
definition-type (non-cryptic) clues. **Transfer: none, confirms a closed door** —
this is exactly the shape of resource 2026-08-23/24's Hebrew WordNet check already
ruled out for this project (gives synonym/synset relations, not the ROLE-CATEGORY
membership — "the singer" -> שרה — this setter's culture clues actually need). Same
conclusion, different paper.

**Conclusion for today's lever.** Fourth-plus consecutive literature pass with
nothing new and buildable on either candidate generation or definition-fit scoring.
Per the queue's own explicitly-named next step (DAILY.md 2026-08-26: "did not wire
`retrieval_candidates` into a live `solve_pass.py` blind trial ... a standing gap
this queue keeps naming and no run has yet closed"), and per today's own finding
that 14across is walled (forcing the image-fallback transcription route anyway, so
a fresh dev puzzle was being built regardless of which lever this run picked),
today's lever is that live trial: `solve_pass.py` already calls `candidates.py`'s
`generate()` with `use_retrieval=True` by default (confirmed by reading
`solve_pass.py`'s `rank()` — no new wiring code needed), so today's build work was
transcription/gold-recovery for a genuinely fresh puzzle (2026-07-10, previously
untouched by this project) rather than a `solver/*.py` code change. See DAILY.md for
the live-trial measurement and the third-puzzle offline recall@N data point.

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

## 2026-08-15


**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824). The
direct precursor to the ICML 2025 paper already credited in this log (2506.04824) — same
proving-framework lineage `solver/prove.py` was adapted from. Read it specifically for two
things not previously checked here: (1) how it formalizes wordplay into Python (an LLM,
Gemini, generates `is_synonym()`/`is_abbreviation()`/`is_anagram()` assertions from an
informal wordplay gloss — structurally identical to what `prove.py`'s DSL already does);
(2) its own honest accuracy ceiling on distinguishing correct answers from close-but-wrong
ones: **~38-40% true-positive rate, ~55% draws, ~5-6% false negatives** on 100 test clues,
with the authors stating outright the system "is a long way from being a reliable oracle
of answer correctness." **Transfer: confirms a limitation this project independently hit
today.** Building `solve_pass.py` (this run's lever), the first design re-ran `is_anagram`/
`is_hidden`/`is_reversal` on `candidates.py`'s own output and found it proved 100% of raw
hits — because those generators only ever emit answers that already satisfy the mechanism
by construction, so "proving" them is a tautology, not verification. The English-cryptic
paper's own 38-40% ceiling (on a MATURE candidate pool from FastText-embedding retrieval,
not a from-scratch mechanical generator) is independent confirmation that execution-based
proof gates are a real but bounded tool: they catch wordplay that outright fails to
execute, not wordplay that executes but is coincidental. Neither this project's `prove.py`
nor the source paper's prover is "an oracle" — both need a human/LLM definition-fit
judgment layered on top, which is exactly the division of labour `solve_pass.py` ended up
encoding after the false start (see DAILY.md log).

**Candidate ranking / definition-span retrieval, re-checked**: the same paper's candidate
generator extracts "the span in the generated definition" and ranks crossword wordlists by
FastText cosine similarity to it, filtered to the right letter pattern. Structurally the
same idea already logged here 2026-08-06 (arXiv 2412.09012) and judged "structurally yes,
technically no" for transfer (no Hebrew embedding space tuned for this genre, corpus too
thin to train one). Re-confirmed, not new information — but now doubly attested across two
independent English-cryptic systems, which raises this project's own priority on lexicon-
tier ranking (tried today, see DAILY.md: corpus/culture-tier hits outrank plain dictionary
hits) as a cheap partial substitute for embedding similarity that this corpus CAN support.

**General sweep** (cryptic candidate generation / diverse hypothesis breadth 2025-2026,
Hebrew morphological tooling): no further new transferable results beyond what the
2026-08-06 entries already covered. The mdda/cryptic-wordplay dataset-building tools
(github.com/mdda/cryptic-wordplay) turned up again in search results — English-clue
dataset tooling, not directly reusable for Hebrew, no action taken.

## 2026-08-16


Before searching, read the full run history first: 9 prior daily runs (PRs #1, #2, #6-#11
plus RESULTS/DAILY's own logs) already implemented and measured mechanical candidate
generation (anagram/hidden/reversal/pattern, then substitution- and homograph-augmented
variants) and definition-span detection twice each, independently, on three different dev
puzzles (2026-05-29, 2026-05-21, and one earlier). Every measurement landed in the same
3.6-7.1% recall@N band regardless of which mechanism was added. That is a saturated
result, not a promising one — today's research pass is calibrated against it rather than
re-discovering it.

**"Are LLMs Good Cryptic Crossword Solvers?"** (arXiv 2403.12094). Benchmarks LLaMA2,
Mistral, and ChatGPT directly on cryptic clues; reports ChatGPT at ~9.5% raw accuracy vs.
~99% for expert humans on the same clue set — the largest reported human/LLM gap found in
this literature so far. **Transfer: corroborating, not actionable.** It measures the same
"a bare LLM cannot decode wordplay from a single pass" ceiling this project hit and moved
away from years ago (RESULTS.md v2-v6): no new architecture, prompting technique, or
candidate/verification split is proposed here beyond what 2506.04824 and 2407.08824
(already logged 2026-08-06/08-15) already contribute. Filed as confirmation the general
finding replicates across model families, not as a new lever.

**Hebrew LLM Benchmark Suite** (huggingface.co/blog/leaderboard-hebrew, and the
"Hebrew LLM Benchmark Suite" overview, both early-2026). A new open leaderboard for
general Hebrew-language LLM capability, with morphology/orthography-aware metrics.
**Transfer: none for this project.** It benchmarks whole-model Hebrew fluency (QA,
summarization, generation) — nothing about cryptic wordplay, definition-span structure,
or candidate enumeration. Checked because it is new and Hebrew-specific, not because it
looked promising; it doesn't change anything here.

**Root-pattern morphology re-check** — no update beyond the 2026-08-06 entry (arXiv
2603.15773, on Arabic not Hebrew, still the closest available finding: tokenizer/morpheme
alignment is neither necessary nor sufficient for correct morphological generation). No
new Hebrew-specific morphological segmenter surfaced this search that PLAYBOOK.md's
hand-built prefix/suffix stripping doesn't already approximate.

**Berkeley Crossword Solver / belief-propagation family, re-checked for queue item 4**
(global constraint optimization). Confirmed again: BCS's own reported gain (57% -> 82%
exact-puzzle accuracy at the NYT tournament) comes from combining a strong *candidate*
list (fine-tuned BERT QA over ~6M clue-answer pairs) with belief propagation across grid
constraints — the propagation step is described everywhere as a *re-ranker*, not a
generator; it cannot manufacture a correct candidate that never entered the list. Also
found the WebCrow French solver (arXiv 2311.15626), a non-English data point, but it is
the same non-cryptic genre (clue = a definition to embed/retrieve against, not wordplay to
decode) as the English CSP literature already logged 2026-08-06. **Transfer: reconfirms
queue item 4 is correctly sequenced after, not before, candidate quality — and today's
9-run history of flat 3.6-7.1% recall is exactly the "candidate list not good enough yet"
condition that makes running belief propagation now premature.** Nothing here overrides
that ordering; if anything it strengthens the case for leaving item 4 alone until
candidate generation clears a materially higher recall bar than mechanical
anagram/hidden/reversal/substitution/homograph search has reached in 9 attempts.

**Conclusion for today's lever choice:** the research pass turned up no new technique for
either candidate generation or definition-span detection — both queue items have had a
fair, repeated trial and the literature offers nothing that would move them off their
current plateau without a fundamentally different resource (a large Hebrew clue-embedding
model, which this project's 8k-clue corpus cannot train). The honest move is not a 10th
attempt at the same lever; it's finishing the one sub-task of item 1(a) that all 9 prior
attempts explicitly left undone: an actual live LLM solve session using the ranked
candidate list, measuring real precision/coverage/yield rather than offline recall@N. See
DAILY.md's log for what that trial found.
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

## 2026-08-19


**"Proving that Cryptic Crossword Clue Answers are Correct"** (arXiv 2407.08824).
https://arxiv.org/html/2407.08824v1
Pipeline: a fine-tuned LLM annotates an informal definition span + wordplay for a
clue+candidate pair; a second LLM formalises the wordplay into executable assertions
(`is_synonym`, `is_abbreviation`, `is_anagram`, ...); a Python prover executes them,
giving the LLM up to 5 iterative rewrite attempts on failure. Headline finding: proving
the GROUND-TRUTH answer beats a close FastText-similarity distractor only 38-42% of the
time (53-59% draws) — i.e. even with the correct answer in hand, the proof step alone
often cannot outscore a wrong-but-plausible neighbor; scale of candidate pool matters more
than proof strength alone. **Transfer: high, and largely already independently converged
on.** This is essentially this project's own architecture (prove.py = the verifier,
candidates.py = the FastText-similarity-generator's role, both built over the last two
weeks before this paper was found) rediscovered from the English-cryptic side, which is
reassuring rather than novel — it says the design direction here is not a dead end. The
one piece genuinely not yet present here: their **iterative rewrite loop** (a proof that
fails gets fed its own failure back for up to 5 repair attempts) vs. prove.py's current
one-shot check-or-reject. Flagging as a possible future lever, not attempted today (would
touch the solve LOOP, not a standalone tool, and today's lever budget went to definition-
span detection instead). Their draw-heavy result is also a caution for lever 4 in the
research-informed queue (HYPOTHESIS BREADTH / more candidates): a bigger candidate pool
only helps if the prover can actually discriminate, which their own numbers say is not
free.

**"Cryptic Grammar" (Viresh Ratnakar, 2023, informal writeup, revisited today for currency).**
https://viresh-ratnakar.github.io/writings/2023/cryptic-grammar-04-2023.html
Formalises English cryptic-clue *surface grammar* (placeholder-substitution: replace
fodder with `[fodder]`, definition with `[solution]`, check the remainder reads as a
valid instruction/assertion in English). **Transfer: none.** It explicitly does not
address definition placement (assumes the solver already knows), and the technique is
English-morphology-specific (tense/participle agreement) with no Hebrew analogue in this
project's tooling. Checked because it looked promising from the title; recording the
negative so a future run does not re-check it.

**Today's own empirical check — see DAILY.md log for the executed measurement.**
`solver/PLAYBOOK.md` section 2.4 asserts, from qualitative reading, that this specific
setter (יורם הרועה) does NOT follow the standard cryptic convention that the definition
sits entirely at one end of the clue ("No fixed rule... can be interleaved"). Before
building `solver/defspan.py`'s classifier half, I tested that claim mechanically against
this run's transcribed puzzle by locating each gold answer's own anagram/hidden/reversal
window in its clue text and bucketing the window's position (start/end/interior). See
DAILY.md for the executed numbers and the resulting go/no-go decision — this is the kind
of check the definition-span literature (2412.09012, still the standing reference) never
does for a non-English, non-standard-convention setter, and it directly gates whether
lever queue item 2 is worth pursuing further here.

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

## 2026-08-21


Re-checked for anything new since 2026-08-20 on: cryptic candidate generation,
definition-span detection, and Hebrew NLP/morphology, plus a general sweep for any new
cryptic-solving system.

**General search: "cryptic crossword solver LLM candidate generation 2026".** Surfaced
only papers already logged here (2406.09043 NAACL 2025, 2412.09012, 2506.04824) plus one
new item worth checking: Sadallah et al. (2025) reports ChatGPT few-shot accuracy of
9.5% on English cryptics vs. 99% human-expert — a bigger accuracy gap than this project's
own numbers, on an easier language (English cryptics have a stable one-end definition
convention this setter explicitly does not follow, per the already-measured 08-19
finding). **Transfer: confirms rather than changes anything** — if frontier LLMs
struggle this much on the *easier*, well-studied version of this task even with full
in-context few-shot prompting (no external candidate generator, no proof gate), it's
consistent with this project's standing diagnosis that the wordplay-cracking step itself,
not tooling, is the hard part, and that a bare LLM without this project's harness would
do worse here, not better. Also surfaced this project's own public page again in a
general search (as on 2026-08-20) — spot-checked that it still correctly represents the
96% figure as retracted, not fixed by omission.

**Definition-span detection, general search.** No new academic result; general
crossword-advice pages restate the same one-end convention already known to not hold for
this setter (killed 2026-08-19, queue item 2 struck). **Transfer: none** — nothing here
contradicts or should reopen that finding.

**Hebrew morphology / NLP.** Same landscape as 2026-08-06/08-20 (RFTokenizer, HebPipe,
YAP), plus one tool not previously named directly: **DictaBERT-seg**, a Hebrew
transformer fine-tuned specifically for the prefix-segmentation task (splitting off
ב/ל/מ/ש/ה/ו/כ clitics), more targeted than YAP's full morpho-syntactic parse for this
project's narrow need. **Transfer: still plausible, still not attempted, still not the
bottleneck.** Same reasoning as the last two research entries — this project's own
measured numbers (candidate recall 3.6-7.1% across three independent puzzles/
implementations, defspan classifier 1/5) point at wordplay-mechanism coverage and
definition-fit judgment as the gap, not tokenization quality; the ad hoc prefix lists
already in `homographs.py`/`charade.py` are not where the last three levers' failures
traced to. Not queued above candidate-generation-shape work without a concrete case where
a prefix-list miss caused a specific measured failure.

**Conclusion for today's lever.** No new external finding changes the queue's priority
order or reopens either struck item. Given the queue's top code lever (candidate
generation, item 1) has now been tried in three independently-written shapes across three
different dev puzzles with the same null result (3.6% / 7.1% / 4.0% recall, all flat
before/after adding substitution+homograph mechanisms), and item 2 is struck, today's
lever is the lowest-risk, best-evidenced item actually still open: queue item 7, fixing
`lexicon.held_out_answers()`'s coverage gap. It is not a research-literature lever — it's
an internal integrity fix flagged twice already (2026-08-16, 2026-08-17 log entries) as a
real, unaddressed leak vector, and this project's own history (the 96% leak) is the
reason leak-vector fixes get priority over one more speculative recall experiment on a
lever already measured negative three times running.

## 2026-08-22


Swept for anything new since 2026-08-20 on: cryptic candidate generation, definition-span
detection, Hebrew NLP/morphology, and (new angle this run) any existing Hebrew-specific
cryptic-solving tooling that might already exist and be worth learning from.

**General cryptic-solving literature** — re-searched broadly (arXiv, "August 2026 cryptic
crossword reasoning"). No new paper beyond the set already logged (2406.09043, 2412.09012,
2403.12094, 2407.08824, 2506.04824). **Transfer: none new.** The field's SOTA is still the
same generate-candidates -> formalise -> prove pipeline this project already mirrors
structurally (candidates.py + prove.py), and its own published ceiling on a MATURE English
candidate pool (~38-40% true positive per 2026-08-15's RESEARCH note on 2407.08824) is a
useful sanity check on how much headroom "better proving" alone has left here — not much;
this project's bottleneck, as DAILY.md's own measurements keep confirming, is candidates,
not verification.

**Hebrew morphology/NLP** — no new 2026 resource beyond RFTokenizer/HebPipe/the root-pattern
evaluation already logged. **Transfer: none new.**

**NEW THIS RUN: existing Hebrew crossword tooling, checked directly rather than assumed.**
Search for "תשבץ היגיון AI" surfaced a Hebrew cryptic-crossword *platform*
(https://dvd848.github.io/cryptic-crossword/, code at github.com/Dvd848/cryptic-crossword)
that looked, from the title alone, like it could be a solver for exactly this puzzle genre.
Fetched and read directly (not just the search snippet, per the 2026-08-08 lesson about
trusting search summaries over primary sources): it is an **interactive puzzle archive and
manual-entry UI** (started as an internal Intel project), with explicitly no automated
solving mechanism — users type answers into cells themselves. **Transfer: none** — it solves
a different problem (rendering/UX for weekly puzzles since 2013), not answer derivation.

Also checked a second, adjacent repo the same author links, github.com/Dvd848/Crossword-Solver,
which sounded more promising by name. Fetched directly: it is a **plain pattern-matching word
finder** over a DAWG-encoded Hebrew dictionary (letters + `?` wildcards -> matching dictionary
words), with **no wordplay, anagram, or definition handling at all** — functionally a
faster/more compact version of what `solver/lexicon.py pattern` already does here.
**Transfer: none for solving**, but its dictionary source list is worth noting for a possible
future lexicon-expansion lever (not today's): it aggregates Wiktionary, Wikipedia, Hebrew
WordNet, and Hspell under CC-BY-SA/MIT/AGPL — Hebrew WordNet in particular is a source this
project's `solver/lexicon.py` does not currently draw from and hspell already does; low
priority since PLAYBOOK.md's diagnosis is that this setter's difficulty is wordplay-device
coverage, not raw vocabulary size (RESULTS.md: this project's own corpus already covers most
attempted answers' definitions; the gap is deriving them from wordplay, not defining them).

**Conclusion for today.** No literature or tooling finding changes the queue's priority
order or unsticks either struck lever (definition-span detection, indicator-density
version; substitution/homograph candidate generation in the shape already tried twice).
Today's implementation lever (see DAILY.md log) is therefore the queue's own explicitly-
flagged remaining gap under item 1(a) — a full-puzzle LIVE blind trial of `solve_pass.py`
(the previous live trial, 2026-08-16, was n=2 and explicitly flagged as too small to be a
reliable estimate) — not a new mechanism, since neither today's research nor the last three
runs' mechanism attempts found anything to extend.

## 2026-08-26

Read the full unmerged-PR state first (per the standing "don't re-derive a result already
sitting in an unmerged PR" lesson): PR #27 (2026-08-25) consolidates the whole backlog
(#23/#25/#26) and adds `retrieval_candidates` (BM25 over `retrieve_defs.py`'s definition
index) to `candidates.py`, MEASURING a real positive move (3.6% -> 7.1% recall) on the
2026-05-29 dev puzzle — the first candidate-gen sub-lever to move the number at all since
2026-08-06. Its own log explicitly flags the open gap: "worth a second puzzle's data
point before calling this settled." Searched today with that gap specifically in mind —
is there new evidence for or against ranked-retrieval-augmented candidate generation
generalizing, and is there anything new on definition-fit scoring (queue item 9, still the
project's sharpest open question per the 2026-08-22/23 live-trial root-cause)?

**General search: "cryptic crossword solver LLM candidate generation definition-fit
scoring 2026".** Surfaced the same paper family already logged here, but through two new
paths worth checking directly rather than assumed duplicate: an OpenReview forum page
(`openreview.net/forum?id=Bo5eKnJPML`, titled "A Reasoning-Based Approach to Cryptic
Crossword Clue Solving") and a second OpenReview entry (`id=2nC7zy7adD`, "Generating Code
to Verify Cryptic Crossword Reasoning", ICLR 2025 Workshop on Deep Learning for Code).
Both direct PDF/forum fetches were blocked by OpenReview's bot-verification page (could
not read content directly, unlike arXiv mirrors); cross-checked via search instead —
both resolve to the same Andrews & Witteveen authorship and arXiv ID (2506.04824) already
logged 2026-08-06, the ICLR workshop entry being an earlier version of the same paper.
**Transfer: none new** — not two additional data points, one paper found twice.

**NEW CITATION, not previously logged by name: "Decrypting Cryptic Crosswords:
Semantically Complex Wordplay Puzzles as a Target for NLP"** (Rozner, Potts, Mahowald,
2021; arXiv 2104.08620). This is the origin paper for the Cryptonite dataset that every
other paper in this log's citation chain (2506.04824, 2407.08824, 2406.09043, 2403.12094)
benchmarks against — a T5 baseline fine-tuned on Cryptonite's 470k clues reaches only
7.6% accuracy, and their own curriculum pretraining (unscrambling-word pretasks) improves
on that but still falls well short of human performance. **Transfer: confirms rather than
adds** — it is the historical baseline the entire "generate then verify" pipeline this
project already mirrors was built specifically to beat; no new technique here that isn't
already superseded by the more recent papers in this log, but worth citing by name now
that it surfaced directly rather than only by inherited reference.

**Checked one adjacent research area for queue item 4 (global constraint optimization,
still correctly sequenced after candidate quality per 2026-08-16's finding): "LLM-Solve
2026"** (sites.google.com/view/llm-solve-2026), an FLoC'26 workshop (Lisbon, July 2026) on
LLM + constraint-solving (CP/SAT/SMT/MIP) integration generally. **Transfer: none
concrete** — it is a general venue for the LLM+solver research area converging, not a
crossword-specific result or a technique with a reported number; confirms the area is
active but gives nothing to port today. Queue item 4's sequencing (after candidate
quality clears a materially higher bar) is unaffected.

**Definition-fit scoring (queue item 9), re-checked once more.** No new resource beyond
2026-08-23/24's findings (embedding-rerank techniques need a Hebrew crossword-tuned
embedding space that doesn't exist; Hebrew WordNet is real but answers synonymy, not the
role-category lookup this setter's culture clues need). **Transfer: none new** — third
consecutive research pass with nothing buildable-today on this item; the standing
2026-08-24 conclusion (next attempt should be a new internal idea, not another literature
sweep) still holds.

**Meta-finding, re-checked for the third time (2026-08-20, 2026-08-25, today): does search
summarization still drop this project's own retraction context?** This run's general
search surfaced the project's own public page again, and this time the auto-summary
correctly cited "43 percent per run and 64 percent merged, against a 25 percent baseline"
— the real, audited v8 numbers, NOT the retracted 96%. **Worth recording as a data point,
not a reversal of the standing caution**: the summarizer's behavior is inconsistent
run-to-run (query-phrasing-dependent, presumably), which if anything argues MORE strongly
for always reading RESULTS.md directly rather than trusting any single summary's framing,
good or bad, since the same page produced a materially different (and this time correct)
summary than 2026-08-20/2026-08-25's runs got.

**Conclusion for today's lever.** No literature or resource finding today unsticks queue
item 9 (definition-fit) or adds a new candidate-generation mechanism. The best-evidenced
next step is therefore PR #27's own explicitly flagged gap: re-measure
`retrieval_candidates` on a SECOND, independent dev puzzle before treating the 3.6% -> 7.1%
result as more than an n=1 anecdote — exactly the kind of skepticism this project's own
"treat any jump over ~15 points as suspect" discipline calls for applied to a smaller,
real jump. See DAILY.md for the measurement.

## 2026-08-23


Two open PRs exist on top of this main (#23, 2026-08-21: `held_out_answers()` coverage
gap fix, queue item 7; #24, 2026-08-22: first full-puzzle live blind trial of
`solve_pass.py`, 0/2 precision) — neither merged, so main still lacks both. Read both in
full via `pull_request_read` before choosing today's lever, per the standing "don't
re-derive a result already sitting in an unmerged PR" lesson from the 2026-08-16 PR-pileup
finding. PR #24's root-cause trace is the most important thing either surfaces:
**cumulative live precision across the only two live trials this project has run
(2026-08-16, 2026-08-22) is 1/4 = 25%**, and both misses share one shape — `prove.py`
correctly verified a real mechanism (a hidden word, a reversal) on a plausible-but-wrong
Hebrew answer; the gap is definition-FIT judgment, not mechanism verification.

**Searched specifically for that gap: definition-candidate semantic-fit scoring for
cryptic solving, general and Hebrew-specific.** Confirms the existing 2412.09012/
2506.04824 finding already logged here (2026-08-06/08-15): the established technique is
FastText/embedding cosine similarity between a located definition span and each candidate,
used to RANK a candidate pool a separate generator already produced. **Transfer: still no
new mechanism** — no 2026 paper found that changes this, and this project still has no
Hebrew embedding space tuned for the genre (checked again: general-purpose Hebrew
embeddings exist — fastText/GloVe/Word2Vec/AlephBERT vectors are documented resources —
but none is crossword-register-tuned, and integrating any of them is a materially larger
lift than a text-only fix, out of scope to even prototype today alongside a second lever).

**Checked one specific new lead: Hebrew WordNet**, since English rule-based cryptic
solvers use WordNet path-similarity for exactly this definition-vs-candidate scoring role
(surfaced in today's search on general cryptic-solver definition-ranking approaches).
Hebrew WordNet (MultiWordNet-aligned, built at IRST/Ben-Gurion) exists in principle but
search results describe its canonical host as unavailable; the Open Multilingual WordNet
mirror project lists a Hebrew component but the reference itself could not be confirmed
reachable in the time budget for a research check (not attempted as a bootstrap step —
would need its own reconstructibility story before ever being wired in, matching this
project's standing rule that nothing gets committed unless bootstrap.sh can rebuild it).
**Transfer: plausible, unbuilt, flagged for a dedicated future lever** — path-similarity
over a Hebrew WordNet (if a working mirror exists) is the closest thing to a validated
technique for definition-fit scoring that the literature actually offers, more promising
than trying to hand-roll a heuristic the way `defspan.py`'s indicator-density classifier
did (which already measured 1/5, worse than chance, on the structurally adjacent
definition-*location* problem). Not started today: confirming a real, licensable,
scriptable download is its own investigation, and this run's one-lever budget went
elsewhere (see DAILY.md).

**Conclusion for today's lever.** No new external finding is buildable today: the one
concrete idea it points to (WordNet-based definition-fit scoring) needs a resource
whose availability this session couldn't confirm, so implementing a stub around it would
be exactly the kind of filler this project's own log explicitly says not to ship. Chose
the best-evidenced internal item instead: queue item 7b, flagged-not-fixed twice already
(2026-08-16 log entry named the gap; PR #23, 2026-08-21, fixed the `lexicon.py` half and
explicitly flagged the identical gap in `substitutions.py`/`retrieve_defs.py` as 7b,
unfixed). Checked directly before trusting that "identical" label: `substitutions.py`'s
`held_out()` has the EXACT same shape as `lexicon.py`'s old bug (its `explanations()`
sources `data/answers/answers_parsed.json` — every one of the 52 puzzles unconditionally —
while the old `held_out()` only blocked rows with a transcribed `clues.jsonl` entry), so
that half is a real, currently-exploitable leak on this main. `retrieve_defs.py`'s
`held_out()` has the same narrow row-only shape, but its only caller (`build_index()`)
sources dev/eval-adjacent docs exclusively from `clues.jsonl` rows marked `split=='train'`
— which an untranscribed slot can never have, by construction — so that half is a
name-only match to lexicon.py's bug, not an actively exploitable one under today's call
graph. Fixed both anyway (defense-in-depth, and to keep both functions on the same
by_date-expanded contract as `lexicon.held_out_answers()` rather than a narrower one that
happens to be safe only by luck of the current call sites) — see DAILY.md for the measured
before/after and the audit.

## 2026-08-24


Continuing the sharpest open question flagged 2026-08-22 (and, per PR #25's own unmerged
description read directly during this run's PR-backlog check, apparently also picked up
2026-08-23 by a still-open PR): **definition-fit / candidate-semantic-scoring** — the two
live trials so far (1/4 cumulative precision) both failed because a mechanically-valid
wordplay device landed on a real word that was not the setter's intended answer, and
neither trial's miss was even reachable by this project's candidate generator in the first
place (see DAILY.md's 2026-08-22 root-cause: gold תאו/שכמ are not literal anagram/hidden/
reversal fodder of their clues at all). That reframes the question from "how do we SCORE
candidates by definition fit" to "how do we GENERATE a candidate from the definition side
at all" — re-checked the literature with that reframing in mind.

**Definition-span embedding re-rank (2412.09012, already logged 2026-08-06/2026-08-20)** —
re-read specifically for whether it generates or only reranks. Confirmed once more: it
reranks a candidate list a separate mechanism already produced (FastText cosine similarity
between the marked definition span and each candidate). **Still not a generator**, and
still no Hebrew-tuned embedding space exists to port even the rerank half. No change to
the standing judgement.

**Hebrew WordNet — checked directly rather than left as an unconfirmed lead (queue item 9,
per PR #25's description).** `github.com/NLPH/HebrewWordnetShuly` is real: a mirror of
Shuly Wintner/University of Haifa's Hebrew WordNet (MultiWordNet methodology, aligned to
Princeton WordNet, "Complete" status, non-commercial license). This resolves queue item 9's
own condition ("confirm the resource is real and fetchable before building anything on
it") — it is real. **Not fetched or integrated today**: even confirmed-real, WordNet gives
synset/synonym relations, not the ROLE-CATEGORY lookup (this clue names a *singer*, a
*kibbutz*, a *minister*) that a Hebrew cryptic setter's culture-reference clues actually
need — mapping "the singer" to the word שרה is a homograph/role fact this project's own
HOMOGRAPHS.md already encodes, not a synonym-set fact WordNet encodes. Flagging as
possibly useful for a DIFFERENT lever (synonym-based `means()` expansion in prove.py,
Track record: RESULTS.md's PLAYBOOK diagnosis is that vocabulary breadth was never this
setter's bottleneck) rather than today's.

**BM25 vs. dense retrieval, general IR literature (new sighting, not previously logged)**
— a 2026 scaling study found BM25 leads a strong commercial embedding model
(text-embedding-3-large) on most metrics past roughly 10M corpus tokens. **Transfer:
narrow but real** — it's independent confirmation that `retrieve_defs.py`'s existing
choice of BM25 over an embedding index was the right call for this project's small corpus,
not a shortcut that should be revisited once more compute is available. Does not unstick
the definition-fit problem (retrieve_defs.py already measured gold@25=5.4% on its own
index, ceiling 27% — the bottleneck there is corpus coverage, not the ranking function).

**Conclusion, and the lever this run actually built.** No paper or resource found this
cycle turns into a working DEFINITION-DRIVEN GENERATOR usable today: the two real external
options (a Hebrew embedding space, Hebrew WordNet) either don't exist in a form this
project can reach, or answer the wrong question (synonymy, not role-category membership).
Rather than ship nothing on this front for a third run running, built the one
definition-driven source this project's OWN committed data already supports without any
new scrape or external dependency: `solver/candidates.py`'s new `culture_category_candidates`
— a hand-curated Hebrew role/genre/geography trigger vocabulary (honestly NOT corpus-mined,
disclosed in the code and here rather than dressed up as empirical) that maps a clue's
named category ("the singer", "a kibbutz") to solver/lex/culture.json's own named-entity
lists, filtered to the enum length. This is deliberately narrow and almost certainly not a
full solution to the definition-fit problem (see DAILY.md for the measured recall number
and an honest read of how far it goes) — it is the smallest real step available today given
what did and didn't turn up in this run's literature/resource check, not a claim that the
underlying research gap is closed.

## 2026-08-25

Also began by consolidating a 3-PR backlog (#23, #25, #26, all open against the same main,
none merged) before touching a lever — see DAILY.md's log for that housekeeping. Research
this run focused on the queue's two live threads: (1) whether ranked retrieval belongs in
`candidates.py`'s pool at all (queue item 1, still not attempted as of yesterday despite
`retrieve_defs.py` existing since 2026-08-08), and (2) one more check for anything new on
definition-fit scoring (queue item 9) before assuming yesterday's negative finding still
holds.

**General search: "cryptic crossword solver LLM candidate generation retrieval 2026".**
Surfaced only the same paper set already logged here (2506.04824, 2406.09043, 2403.12094)
plus a genuinely noteworthy repeat of the 2026-08-20 finding: this project's OWN public
page (tashbetz-solver.vercel.app) appears again in general search results, and the search
tool's auto-summary again stated "[a] v6 solver version returned 27 of 28 clues correct on
2026-06-05" as if it were a standing result — that is the RETRACTED 96% leak number
(RESULTS.md's INTEGRITY FINDING), presented with zero retraction context by the summarizer,
for the SECOND time this project has caught it happening (first: 2026-08-20). **Transfer:
this is not a one-off search-engine quirk, it is a recurring failure mode of trusting
search summaries over primary sources on a project with its own public writeup** — worth
stating plainly for whoever reads this project's own summarized coverage anywhere (a
teammate, a future agent, a casual search) rather than the live page's dedicated Retraction
section: do not trust a summary of this project's own results, read RESULTS.md directly.

**BM25 vs. embedding retrieval, re-checked.** Same conclusion as 2026-08-24's entry,
independently reconfirmed by a fresh search: BM25 remains the stronger default at this
corpus's scale, hybrid approaches add complexity without a demonstrated gain here.
**Transfer: no change** — `retrieve_defs.py`'s existing BM25 choice stays right; this
reconfirms rather than motivates any new work.

**Definition-fit scoring (queue item 9), re-checked once more.** No new resource found
this cycle beyond yesterday's Hebrew WordNet finding (real but answers the wrong question
— synonymy, not role-category membership). **Transfer: none new** — the standing
2026-08-24 conclusion holds: no external generator or scorer exists to build on here today.

**Conclusion, and the lever this run actually built.** Neither research thread produced a
new EXTERNAL resource to build on, so today's lever (see DAILY.md) is the queue's own
long-open internal gap instead: `solver/retrieve_defs.py` (BM25 ranked retrieval, built
2026-08-08, measured standalone at gold@25=5.4%) has never once been wired into
`candidates.py`'s `generate()` pool alongside the mechanical mechanisms, despite being
exactly the "RANKED RETRIEVAL" item the 2026-08-08 research-informed queue named as
priority 2. Wiring in an already-built, already-audited tool as one more candidate SOURCE
is not itself a research question — it is closing a gap between what the project's own
research queue prioritized in 2026-08-08 and what got implemented, which is worth doing
regardless of whether today's literature sweep turned up anything new.
