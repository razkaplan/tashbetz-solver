# Plan: winning organic traffic for the tashbetz dictionary

Grounded in the 2026-08-28 competitor research (`competitors.md`, `serp_snapshots/2026-08-28.md`).

## Diagnosis — why we lose today

1. **Wrong atomic unit.** Users search the clue ("שחקן ישראלי תשחץ"). Incumbents' page = one
   clue. Our pages = category×length ("שחקנים ב-5 אותיות") and per-answer (`/milon/e/משק/`).
   We rank for queries nobody types and sit out every query people do type.
2. **No authority.** `tashbetz.gtmascode.dev` is a fresh subdomain of a dev domain with no
   backlinks, against 10-year-old .co.il sites. Even perfect pages won't rank quickly here.
3. **No freshness/UGC loop.** Every winner has comments/submissions; our pages are static.
4. **Index shape risk.** 5,656 of 6,190 sitemap URLs are thin per-answer pages — crawl budget
   spent on the lowest-value shape.

What we have that no competitor has: a 129k-word length/pattern lexicon, a 31k clue→answer
corpus, entity datasets **with descriptions**, and a solver that can **explain** cryptic answers.

## P0 — Measure (do first, cheap)

- Wire Google Search Console + verify; confirm sitemap ingestion, watch index coverage.
- Keep the monthly SERP snapshot loop (`TRACKING.md`).
- Decide the domain question (see "Domain" below) **before** building links to the current one.
  **Decided 2026-08-30: move, within two weeks - see `DOMAIN_AND_MONETIZATION.md`.**

## P1 — Ship clue-shaped pages (the core move)

Create `/milon/d/<הגדרה>/` — one page per common clue phrasing, generated from data we
already have (category datasets map naturally: kibbutz → "קיבוץ בצפון", "קיבוץ בדרום";
artist → "זמר ישראלי", "זמרת ישראלית"; city_il → "עיר בישראל"; nation → "מדינה באפריקה"...).
Start with ~200 high-frequency clue phrasings (the corpus gives frequency), not thousands.

Page template — copy the proven skeleton, then beat it on the two gaps nobody fills:

1. H1 = clue + variant ("קיבוץ בצפון | קיבוץ בצפון הארץ — פתרונות תשחץ ותשבץ").
2. Intro naming תשחץ/תשבץ + newspapers (as note.co.il does).
3. Answers grouped by letter count, then multi-word — **each answer linked to its
   `/milon/e/` page and shown with its one-line description** (our edge #1: no competitor
   explains why an answer fits; this also finally gives the 5,168 answer pages a job as
   supporting nodes instead of dead weight).
4. In-page anchors per length (`#4-אותיות`) with title/H2 phrasing "קיבוץ בצפון 4 אותיות"
   to take the per-length tail without yo-yoo's thin-duplicate risk.
5. "ביטויים דומים" variant block (mordo's trick).
6. Cross-links: to the category-length pages we already have, to related clues, alef-bet nav.
7. Answer-count in the title tag ("— 47 פתרונות") for CTR (arrowword's trick).
8. A "חסר פתרון? כתבו לנו" mailto/form CTA (UGC-lite until real comments exist).

Content sourcing rule: generate from **our own datasets** (culture.json, geo lists, lexicon),
not from the scraped mordo corpus — use the corpus only to *rank which clue phrasings are
frequent* and to QA coverage, never as copied page content (copyright + originality).

Also in P1: retitle/re-describe existing `/milon/<cat>-<N>/` pages to include the clue
phrasing ("שחקן ישראלי 5 אותיות — כל הפתרונות") and link them into the new clue pages.

## P2 — Ship the two differentiated products

- **Weekly explained solutions** for the Haaretz תשבץ היגיון (and later more papers):
  `/solutions/haaretz/YYYY-MM-DD/` — the solver's answers *with wordplay explanations*.
  14across owns these queries with bare answers and query-string URLs; explanations are a
  step-change. Copyright care: paraphrase clues / partial quoting for commentary, our own
  explanation text, link the paper. Each issue = a fresh dated page (their own freshness
  trick, done better).
- **Interactive pattern solver** at `/solver/`: the 129k lexicon behind a fast, ad-free
  "פתרון לפי אותיות" (מ??ה) UI — client-side over a shipped word index. Beats snopi/yo-yoo
  on coverage and UX; the natural link magnet and brand anchor.

## P3 — Topical authority

- Publish the PLAYBOOK as a human guide: "המדריך להגדרות תשבץ היגיון" — device taxonomy with
  real examples; targets "איך לפתור תשבץ היגיון" where incumbent content is thin.
- Keep /tirgul/ practice pages linked from it (already built).
- Recent-additions module sitewide (note.co.il's freshness trick).

## P4 — Authority & links

- **Domain**: buy a dedicated Hebrew-facing domain (a .co.il if one is obtainable, else
  `milontashbetz.com`) and 301 the dev subdomain, *early* (before link building compounds on
  the wrong host). Candidate list, availability, migration checklist and code touchpoints:
  `DOMAIN_AND_MONETIZATION.md`. Not executed yet.
- The research note ("AI solves the hardest Hebrew cryptic") is genuinely newsworthy: pitch
  Geektime/Calcalist tech desks + the crossword community (14across forum, the תשבצי היגיון
  Facebook groups Israel's solvers actually use). One good story seeds the link profile.
- Answer-video experiment optional later (YouTube already ranks in these SERPs).

## Sequencing & success criteria

| When | Ship | Success signal (via TRACKING.md) |
|---|---|---|
| Month 0 | P0 + first 200 clue pages + retitles | pages indexed; first impressions in GSC |
| Month 1 | Weekly explained solutions live ×4 issues | impressions on "פתרונות תשבץ היגיון" queries |
| Month 2 | Pattern solver + PLAYBOOK guide | first top-20 positions on clue long tail |
| Month 3+ | Domain move done, press push | 5/15 tracked queries with our result in top 20 |

The honest expectation: clue long tail and newspaper-solutions queries are winnable in
months (weak defense, fresh entrants prove it); head terms ("מילון תשבצים") are a year+ of
compounding pages, UGC and links behind the duopoly.
