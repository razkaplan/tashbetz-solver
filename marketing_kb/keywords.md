# Keyword landscape — Hebrew crossword help

Machine-readable detail (owners, difficulty, our assets per class): `keywords.json`.

The market is not a few head keywords — it is **thousands of clue-shaped long-tail queries**.
Priority order by opportunity:

1. **Clue long tail** — `<הגדרה> תשחץ/תשבץ` ("קיבוץ בצפון תשחץ"). The traffic engine of every
   incumbent. We have zero pages in this shape. → SEO_PLAN P1.
2. **Clue + length** — `<הגדרה> N אותיות`. Only yo-yoo targets it structurally; our data is
   already length-indexed. → P1 (same pages, anchor sections).
3. **Newspaper solutions** — `פתרונות תשבץ היגיון הארץ`, `תשחץ ישראל היום פתרונות`. Single weak
   incumbent (14across, bare answers). Our solver explains wordplay — unique. → P2.
4. **Cryptic education** — `איך לפתור תשבץ היגיון`. Thin incumbent content vs our PLAYBOOK. → P3.
5. **Tools** — `פתרון תשבצים לפי אותיות`. Winnable with the 129k-word lexicon as an
   interactive pattern solver. → P2.
6. **Answer lookup** (`מה זה X`) — keep /milon/e/ pages as supporting link targets only.
7. **Play online** (`תשחץ אונליין`) — out of scope for now.

Fixed tracking query set (16 queries) lives in `keywords.json`; snapshots in `serp_snapshots/`.
