# Tashbetz Solver: Hebrew Logic Crossword (תשבץ היגיון) Assistant

Goal: solve at least 80% of the clues of the Haaretz "יורם הרועה" logic crossword,
with a correct explanation per answer, without consulting the answers site at solve time.

## 1. What gets "trained"

Two tracks. Track A is what actually reaches 80%; Track B is the optional small-model distillation.

### Track A: Solver harness + learned pattern playbook (primary)
- A solver agent (LLM) equipped with tools and a **pattern playbook** distilled from the corpus.
- The playbook is data-derived: mechanism taxonomy, indicator words, solved examples per mechanism,
  and per-setter quirks of יורם הרועה (his style is stable week to week).
- Iteration loop: solve held-out puzzles -> error analysis -> update playbook/tools -> re-eval.
  This is "training" in the sense of learned artifacts, with no gradient steps, so it converges fast
  and every improvement is inspectable.

### Track B: Small model fine-tune (secondary, after corpus exists)
- SFT on (clue + enumeration + crossing letters) -> (answer + explanation) pairs, formatted as
  chat turns. Base candidate: a 4-8B multilingual model with strong Hebrew (e.g. Qwen3-8B or
  Dicta-LM 2.0) via LoRA on Apple Silicon (MLX). The same harness wraps either model.
- Realism note: with ~1,300 clue examples a small model alone will not hit 80%; it learns style
  and mechanism vocabulary, while the harness (lexicon tools + grid constraints) does the heavy
  lifting. Treat Track B as a cost/latency optimization, not the accuracy path.

## 2. Data sources

| Source | What it gives | Access |
|---|---|---|
| 14across.co.il answers.php?crossword=16 | answer per clue (data-content attr) + crowd explanations, per date | ~50 weekly dates back to 01/08/2025, plain HTML |
| Haaretz haaretzlogicpuzzle archive | article per week containing puzzle jpg (tashbetz2.jpg) | article body is JS/paywall-loaded; needs rendered browser or logged-in session |
| Puzzle jpg | clue texts + grid geometry + enumerations | Hebrew OCR via multimodal LLM transcription |

Key structural fact: **clue text exists only on the jpg**; answers+explanations exist only on
14across. The dataset is a join of the two on (date, clue_number, direction).

## 3. Dataset shape

`data/dataset/clues.jsonl`, one row per clue:

```json
{
  "puzzle_id": "haaretz-yoram-2026-07-17",
  "puzzle_date": "2026-07-17",
  "source_article_url": "https://www.haaretz.co.il/...",
  "image_url": "https://img.haarets.co.il/.../tashbetz2.jpg",
  "clue_number": 1,
  "direction": "across",
  "clue_text": "...",
  "enumeration": [5, 2, 5],
  "answer_raw": "שלומעלישראל",
  "answer_display": "שלום על ישראל",
  "answer_len": 11,
  "explanations_crowd": ["שלום(אש) על ישראל(כץ)"],
  "explanation_clean": "...",
  "mechanisms": ["charade", "definition_pun"],
  "definition_part": "...",
  "wordplay_part": "...",
  "split": "train"
}
```

Plus `data/dataset/grids.json`: per puzzle, the grid geometry (cell matrix, numbering,
crossing map) recovered from the image, enabling constraint propagation at solve time.

Splits: **by whole puzzle, by date.** Last ~8 puzzles = eval (never seen during playbook
building), previous ~5 = dev, rest = train. No clue-level leakage across splits.

Quality gates on the join:
- transcription letter-count must equal len(answer_raw) (final-letter forms normalized); mismatch -> re-transcribe that clue
- every 14across clue number must appear in transcription and vice versa; gaps flagged

## 4. Mechanism taxonomy (initial, refined from corpus)

Israeli תשבץ היגיון differs from UK cryptics: looser grammar, heavy punning. Initial labels:

- `charade` — concatenation of parts (שלום+על+ישראל)
- `anagram` — אנגרם, indicators like "מבולבל", "הרוס"
- `reversal` — להפך / read backwards
- `container` — X inside Y (טומי ב-אנה)
- `hidden` — answer hidden in surface text
- `double_definition` — מילה משותפת (one word, two meanings)
- `homophone` — sounds like
- `definition_pun` — definition + misdirecting pun (the dominant local style)
- `initials_finals`, `deletion`, `reference_culture` — names, songs, politicians (very frequent:
  Israeli pop culture, Bible, politicians)

Labeling: LLM labels each row grounded in the crowd explanation text (not the clue alone),
then a verification pass samples ~10% for consistency.

## 5. Pipeline

1. **Scrape answers** — Bright Data Scraper Studio collector over all date URLs (batch run).
2. **Enumerate Haaretz archive** — section page (+ load-more) -> article URLs per week.
3. **Get puzzle jpgs** — rendered-browser scrape of each article -> tashbetz2.jpg URL -> download
   at width=1500.
4. **Transcribe** — multimodal transcription of each jpg: clue list (number, direction, text,
   enumeration) + grid geometry. Validate against answers (gate above).
5. **Build dataset** — join, clean explanations, label mechanisms, split.
6. **Playbook** — distill: mechanism frequency, indicator lexicon, per-mechanism worked examples,
   setter quirks (recurring devices, favorite references).
7. **Solver harness** (`solver/`):
   - candidate generation per clue: mechanism-guided (anagram engine over Hebrew lexicon,
     reversal, charade assembly, double-definition lookup)
   - grid constraint propagation: crossings prune candidates; iterate easy->hard
   - self-check: answer must be justifiable by an explanation in the corpus style; confidence score
   - tools: Hebrew wordlist (wikidata/hspell-derived), gematria, celebrity/culture list
8. **Eval loop** — on held-out puzzles: % clues correct (exact answer match, spacing-insensitive),
   % with valid explanation (LLM-judged against crowd explanation). Error taxonomy -> playbook
   update -> repeat until >=80% on eval.

## 6. Honest feasibility

- Corpus ceiling: ~50 puzzles x ~26 clues ≈ 1,300 rows. Enough for playbook + few-shot retrieval;
  thin for pure SFT.
- 80% per-clue with explanations is ambitious but plausible **with grid constraints** (crossings
  massively prune) and cultural-reference tooling. Without crossings, a strong LLM alone typically
  lands far lower on Hebrew cryptics.
- Main risks: (1) Haaretz paywall blocking jpg discovery at scale — fallback: logged-in Chrome
  session; (2) transcription errors on low-res jpgs — mitigated by the letter-count gate;
  (3) explanation sparsity: some clues have no crowd explanation ("מילה משותפת" only).
