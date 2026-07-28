# Improvement plan v2 — grounded in the v8 error profile

## What the errors actually say (and what it overturns)

Consensus scores 37/56 (66%). Profile of the 19 misses:

| bucket | count | note |
|---|---|---|
| long multiword (>=8 letters) | 5 | |
| **short answers (<=4 letters)** | **5** | as many as the long ones |
| clue carries a contributor credit | 10 | credits are noise, not signal |
| culture reference | 5 | |
| no crowd explanation available | 0 | |

Mean length of missed answers is 6.3 vs 6.1 for all clues. **Length does not predict failure.**

This overturns the "culture-reference tail is the ceiling" diagnosis carried from v4-v5.
The misses are spread evenly across clue types, and short answers fail as often as showpieces.
Examples: `וכנ` (3, reversal of פרעה נכו), `שיסל` (4), `קטלנ` (4), `הונדורס` (7, הון+דורס),
`מראהמקומ` (double meaning). These are **wordplay-decomposition failures, not knowledge gaps.**

Implication: knowledge tooling (wiki, culture lexicon) has done what it can. The remaining
gap is (a) decomposing dense wordplay, and (b) disambiguating short slots where a letter
pattern matches hundreds of dictionary words and only the wordplay can choose.

## Methodologies, ranked by expected value

### A. Global constraint optimization over ranked candidates  ← biggest structural gap
Today an LLM greedily places answers one at a time. The established approach for crossword AI
(Proverb, Dr. Fill, Berkeley Crossword Solver) is different in kind: produce a **ranked,
scored candidate list per slot**, then run a **global optimizer** (weighted CSP / loopy belief
propagation / A*) that maximises joint likelihood over the whole grid subject to crossings.
Evidence it fits here: across two runs the union of correct answers was 19/28 while the merge
captured 18 — the ceiling is the candidate pool, not the merge. And short slots fail precisely
because greedy placement cannot exploit the global structure that disambiguates them.
Effort: high. Payoff: likely the single largest.

### B. Substitution dictionary mined from 8,249 crowd explanations
The explanations encode the setter's private vocabulary of equivalences: a word standing for a
letter, an abbreviation, a nickname, a fragment. Auto-extract `clue-fragment -> answer-fragment`
pairs into a lookup table, then expose it as a tool. Directly targets the short-answer bucket,
which is the largest single miss category. This is supervised signal we already own and have
never mined. Effort: medium. Payoff: high.

### C. Deliberate ensemble diversity
Runs are currently N identical prompts. Measured overlap: two runs each got 12 right, only 5 the
same. Diversity is already where consensus gain comes from, so engineer it: an anagram-first
solver, a culture-first solver, a definition-first solver, a reversal/container specialist.
Widening the union raises the ceiling that the merge draws from. Effort: low. Payoff: medium-high.

### D. Consensus-in-the-loop (multi-round)
Today: independent runs, merged once, done. Better: round 1 -> merge only high-confidence
anchors -> feed those back as known letters -> round 2 re-attacks the rest with more constraints
-> repeat until no gain. Grid constraints compound; a single merge throws that away.
Effort: low. Payoff: medium-high.

### E. Adversarial verifier
Confidence is self-reported, and self-reports were exactly what the leak inflated. Add an
independent critic that must account for **every letter** of a proposed answer via the stated
wordplay, and rejects when it cannot. Re-rank by verifier score rather than by self-confidence.
Effort: medium. Payoff: medium, and it hardens against the failure mode that already bit us.

### F. Homograph index expansion  (known defect)
v8b reported `homographs.py scan` returning only three tokens on a puzzle where the homograph
*principle* cracked four clues. The index under-covers: it needs morphological expansion
(prefixes ב/ל/מ/ש/ה/ו/כ, construct forms, inflections) and the equivalences from (B).
The concept is validated; the implementation lags. Effort: low. Payoff: medium.

### G. Retrieval pool expansion
`retrieve.py` draws only on train-split clues that have text (~1,100). The secondary corpus has
6,792 answered clues but no clue text, because clue text lives in the tartey_mashma images.
Transcribing those unlocks roughly 5x the retrieval pool. Effort: medium (reuses the existing
image-transcription pipeline). Payoff: medium.

### H. Curriculum validation on the easier tier
Run the whole harness against דקל בנו / ליאני puzzles, where the culture wall is thinner.
Tells us whether the method is sound but outmatched by this setter, or tops out generally.
Effort: medium (needs G's transcription). Payoff: diagnostic rather than score.

### I. Track B fine-tune — deprioritised, honestly
`sft.jsonl` has 1,108 examples. That is thin for teaching wordplay, and the harness does the
heavy lifting. Revisit only if (G) grows the corpus substantially.

## Methodology of the loop itself (fix this first)

**Statistical power.** Dev is currently 2 puzzles / 56 clues. One clue = 1.8 points, so
differences under ~10 points are noise. Several past "findings" sat inside that band.
-> Expand dev to 4 puzzles (112 clues) before trusting any single-digit movement.

**Held-out discipline.** The 6 eval puzzles have never been touched. Keep it that way; promote
to eval only when dev shows a stable, repeated gain.

**Mandatory audit gate** (added after the leak). Every reported number requires:
1. transcript scan for forbidden file reads, solution sites, image reads;
2. tool-leak check (are held-out answers reachable through any tool?);
3. implausibility check — if a result jumps more than ~15 points, treat it as suspect until
   explained. Identical prompts producing wildly different scores indicates a leak, not skill.

## The loop, concretely

Each iteration:
1. State hypothesis + the mechanism by which it should help.
2. Implement.
3. Run 3 **diverse** solvers per dev puzzle.
4. Consensus-in-the-loop merge, score.
5. **Audit gate** (above). No audit, no number.
6. Re-profile errors; the profile chooses the next hypothesis.
7. Promote to eval only on a stable gain.

Ordering (cheap and validated first, structural last):
- **Iteration 9**: C + D + F together (ensemble diversity, multi-round consensus, homograph
  expansion). All low-effort, all independently motivated. Expect the union to widen.
- **Iteration 10**: B (substitution dictionary). Targets the largest miss bucket.
- **Iteration 11**: E (adversarial verifier) to convert a wider union into a better merge.
- **Iteration 12**: A (global constraint optimization). The real prize, and worth doing once
  candidate lists are good enough to optimise over.
- **Parallel track**: G then H — transcribe the easier-tier images, validate the harness there.

Success criterion, restated honestly: 80% on this setter may not be reachable. The more useful
target is a stable, audited **>=75% on the easier tier** plus continued gains here, which would
establish that the harness is sound and this setter is simply hard.
