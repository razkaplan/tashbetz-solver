# Hebrew Crossword Dictionary — Competitor Map

Research date: 2026-08-28 · Method: Google IL SERP scrapes (8 head + long-tail queries) + full-page template scrapes.
Machine-readable version: `competitors.json`. Baseline SERP snapshot: `serp_snapshots/2026-08-28.md`.

## The market in one paragraph

Hebrew crossword help ("מילון תשבצים") is won on the **clue-text long tail**: people type the
definition they're stuck on plus תשחץ/תשבץ ("קיבוץ בצפון תשחץ", "עיר באיטליה 5 אותיות").
Four sites split nearly every such SERP — **מורדו** (pitaronfree.blogspot.com), **note.co.il**,
**yo-yoo.co.il/crossword**, and newcomer **arrowword.co.il** — with Wikipedia categories and
YouTube answer videos absorbing the rest. A separate niche, weekly *solutions to newspaper
puzzles* ("פתרונות תשבץ היגיון הארץ"), is owned outright by the community site **14across.co.il** —
which is exactly this project's home turf, and their solutions come with **no explanations**.

## Tier 1 — the incumbents

### מורדו — pitaronfree.blogspot.com (leader)
- **What ranks:** one Blogspot post per definition (often several per variant), since ~2012. Takes 2–3 slots on many SERPs.
- **Why it wins:** 13 years of pages + backlinks; brand habit ("הוסיפו מורדו להגדרה"); a "ביטויים דומים" footer that explicitly targets query variants; comments crowdsource missing answers (free updates + freshness); interlinks between related definitions; 11K-like Facebook page.
- **Weak spots:** dated Blogspot UX, heavy ads, flat unstructured lists, no tools, unverified answers.

### note.co.il (leader)
- **What ranks:** `/solutions/<הגדרה>` pages (plus a parallel `/solution/<הגדרה>/` set = double SERP presence), alef-bet index.
- **Why it wins:** exact-niche .co.il domain; boilerplate names the newspapers (ידיעות 7 ימים, מעריב, הארץ, ישראל היום) catching paper-specific queries; answers grouped by letter- and word-count; "ערכים אחרונים" fresh-links module on every page.
- **Weak spots:** thin (answers only, zero explanation), no per-length pages, ads above content.

### yo-yoo.co.il/crossword (leader)
- **What ranks:** `/crossword/solution/<id>` + **per-length subpages** (`solution-6.php?id=` → "עיר באיטליה 6 אותיות") + category pages + an interactive pattern solver (א?א).
- **Why it wins:** the only site structurally targeting "<clue> N אותיות"; portal domain authority; enormous internal mesh (Wordle solver, rhymes, gematria, acronyms = topical breadth).
- **Weak spots:** kids-portal branding, dated PHP, per-length pages are near-duplicate thin content.

### 14across.co.il (leader of the solutions niche)
- **What ranks:** weekly `answers.php?crossword=<id>` threads per newspaper puzzle — including **Haaretz תשבץ היגיון by יורם הרועה**, this repo's subject.
- **Why it wins:** fresh date-stamped page every issue, real community, zero competition for "פתרונות תשבץ היגיון <עיתון>".
- **Weak spots:** bare answers with **no wordplay explanations**; ugly query-string URLs; no definitions dictionary.

## Tier 2 — challengers proving the niche is winnable

### תשחציישן — arrowword.co.il (the template to beat/copy)
Modern WordPress site (~2021) already on page 1 for major definitions. Formula: Hebrew-slug URL per definition, H1 "X תשחץ / תשבץ", answers by length **with inline links to related definitions**, then a long unique prose section (e.g. profiles of 10 Italian cities), category taxonomy, comments, and answer-count titles ("120+ פתרונות אפשריים"). **Proof a newcomer can break in within ~2–3 years.**

### Others
- **zolo.co.il** — constructor-grade definitions engine; tool-first, weak page-level SEO.
- **snopi.com/xDic** — owns pattern-search intent (מד??ה); single-page tool, no moat.
- **pesher.net** — small note-style definition pages, page 1 occasionally.
- **ptoroti.blogspot.com** — mordo imitator, scraps only.
- **xword.co.il + app "התשחץ שלי"** — play intent (תשחץ יומי), adjacent not competing.
- **Newspapers (Haaretz, Israel Hayom, Maariv)** — daily puzzle pages; never explain solutions.
- **SERP absorbers:** Wikipedia categories rank on nearly every definition query; YouTube "פתרונות תשחץ" videos; milog/milononline for "מה זה X". Even a spam domain (schlossmalberg.de) ranks — these SERPs are weakly defended.

## The winning page anatomy (common to all ranking pages)

1. **H1 = the clue text**, often with a variant ("קיבוץ בצפון | קיבוץ בצפון הארץ תשחץ").
2. Short intro naming תשחץ/תשבץ + the newspapers where the clue appears.
3. **Answers grouped by letter count**, then "2 מילים, N אותיות".
4. Variant-phrase block ("ביטויים דומים: X תשחץ, X מילון, שם של X 5 אותיות").
5. Submission CTA / comments (UGC keeps pages alive).
6. Alef-bet + category navigation and links to related definitions.
7. (yo-yoo only) per-length subpages; (arrowword only) unique prose depth.

## Where we stand today

`tashbetz.gtmascode.dev` is indexed (6,190 sitemap URLs) but appears in **zero** competitive
SERPs. Two root causes:

1. **Wrong atomic unit.** Our pages are category×length ("שחקנים ב-5 אותיות") and per-answer
   (`/milon/e/משק/`). Nobody searches those. Searchers type the *clue*: "שחקן ישראלי תשחץ".
   We have no page whose H1 is a clue.
2. **No authority.** A subdomain of a dev domain, days-old pages, no backlinks, vs. .co.il
   incumbents with 10+ years of links.

What we uniquely have that nobody in the market has: a 129k-word length/pattern lexicon, a
31k clue→answer corpus, culture/geo entity datasets with descriptions, and a solver that can
**explain** cryptic answers. See `SEO_PLAN.md` for how to turn that into wins.
