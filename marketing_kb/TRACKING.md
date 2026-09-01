# Competitor & ranking tracking runbook

Cadence: **monthly** (or after every major /milon/ ship). Each run appends a snapshot to
`serp_snapshots/YYYY-MM-DD.md` in the same table format as the 2026-08-28 baseline, then
updates the "Movement log" below. This file is the handoff between runs, DAILY.md-style.

## How to run a snapshot

1. Query Google with geo_location **il** for every query in `keywords.json` → `tracking_query_set`
   (in a Claude Code session, the Bright Data `search_engine_batch` tool; batches of ≤5,
   retry once on timeout — they're common).
2. Record the top 10 organic results per query. Highlight: our positions, any NEW domain
   not in `competitors.json`, and any incumbent that dropped out.
3. `site:tashbetz.gtmascode.dev` — record indexed-page themes and count trend.
4. Once Search Console is wired (see SEO_PLAN P0): export clicks/impressions/position for
   the same queries and add a "GSC" column — GSC is the source of truth, SERP scrapes are
   the competitor lens.
5. New competitor found → add to `competitors.json` + `competitors.md` (scrape its template
   first: URL pattern, H1 shape, answer grouping, internal links, UGC mechanisms).
6. Update the movement log below and the current-state table.

## What to watch per competitor

| Competitor | Watch for |
|---|---|
| mordo (pitaronfree) | still 2–3 slots per clue query? platform migration off Blogspot would be a big move |
| note.co.il | new page types (per-length? explanations?); whether the dual /solution(s)/ paths persist |
| yo-yoo | per-length subpage coverage growth; solver tool changes |
| 14across | any move toward explained solutions (kills our differentiator); new paper coverage |
| arrowword | coverage growth rate — it's the newcomer benchmark; if it stalls, note why |
| SERP features | YouTube answer videos and AI overviews eating clue queries |

## Current state (update every run)

| Metric | 2026-08-28 baseline | Target |
|---|---|---|
| Competitive queries where we appear (of 15) | **0** | 5 by +3 months of shipping clue pages |
| Clue-shaped pages (H1 = clue text) on our site | **49** (shipped 2026-08-28, /milon/d/, 8,012 answers) | 200+ (P1 of SEO_PLAN) |
| Newspaper-solutions pages | 0 | weekly, from first ship |
| Indexed pages (site:) | ~6,190 sitemap / sample indexed OK | monitor index bloat from /milon/e/ |

## Movement log

- **2026-09-01** - Site-wide redesign and rebrand ("fun and smart"): new
  shared stylesheet (docs/assets/brand.css), Fredoka + Rubik type, cream /
  indigo / grape / coral / sun palette, logo mark and favicon (there was
  none), sticky header with the main navigation on every page, a real footer
  with links to every section, and new social cards (og.png) for the home,
  solver, נתיב, milon and trainer pages. Homepage rewritten (hero, stats,
  six section cards, how-it-works). All 5,691 milon pages re-wrapped in place
  via app/rebrand_pages.py (build_seo needs the corpus); nosim, tirgul and
  /milon/d/ rebuilt from the generators. Titles, descriptions, canonicals,
  JSON-LD and URLs unchanged; the research pages now carry the production
  canonical instead of the old vercel.app og:url.

- **2026-08-31 (latest)** - All 44 topic-crossword boards regenerated and
  republished after a reported clue-quality problem: clues that made no sense,
  clues that did not connect to their subject, and clues unrelated to it. All
  three were mechanical. Hidden clues had been naming an inflection of their
  own answer ("צלופן מסתתר בתוך צלופנים" - 99.5% of the carrier index);
  general filler came from the entity index and the curated lists, so a לשון
  grammar board asked about בן אחאב and a מדבר בניז'ר; and entity clues
  published whatever the source article opened with, including labels
  ("דמות מקראית") that identify nobody. Every one is now a gate in
  evals/topicgen_eval.py, which runs before the rebuild workflow commits, so a
  failing board leaves the previous set up rather than replacing it. Six
  rebuilds to get a clean set: findings 15 -> 8 -> 3 -> 2 -> 0. SEO effect is
  on page CONTENT, not URLs - the 57 /nosim/ pages are unchanged in address, so
  nothing to resubmit, but the clue text a crawler sees is entirely new. Worth
  re-checking "תשבץ תנך" and "תשבץ ביולוגיה" ranking a couple of weeks out,
  since the earlier boards would have read as low-quality generated text.

- **2026-08-31 (later)** - New page family shipped: **topic crosswords**
  (`/nosim/`). Ten bagrut subjects x four levels, each a playable board with an
  explanation per answer, plus a landing page per subject and a request page
  (`/bakasha/`). A weekly news board joins at `/nosim/hadashot/` once
  .github/workflows/news-weekly.yml has run once. Targets a query family none
  of the tracked competitors covers: they publish clue->answer lists, nobody
  publishes *playable* subject boards. Watch "תשבץ תנך", "תשבץ ביולוגיה",
  "הכנה לבגרות תשבץ", "תשחץ להדפסה" and the per-subject variants in the next
  snapshot.

- **2026-08-31** - Post-rebuild repair: the 2026-08-30 full rebuild (#35) ran
  build_seo without build_defs after it, dropping all 51 /milon/d/ URLs from
  the sitemap and the defs hub section from /milon/; and the by-bare-title
  corpus fetch overwrote 59 curated kibbutz descriptions with wrong-article
  text (דליה the flower, גזר the vegetable, "דף פירושונים"). Restored the /d/
  sitemap block + hub section, curated descriptions now win for the kibbutz
  category in build_seo, and the 59 descriptions were fixed across
  entities.json, list pages and 28 entity pages. kibbutz clue page back to
  267 answers (had silently dropped to 208).
- **2026-08-29 (later 3)** - Kibbutz/moshav split shipped from user feedback:
  the mixed "קיבוצים ומושבים" category is now two categories, 65 missing
  kibbutzim added (דליה, בארי, עין גדי, פלמחים...) - kibbutz coverage now 271,
  matching the real count. 26 new /milon/moshav-*/ pages, kibbutz-11 and 3
  kibbutz letter pages dropped (under threshold after the split). Hub search
  fixed: '.', '?' and '*' all work as pattern wildcards (the placeholder
  promised '.' but only '?' worked) and exact name matches rank first.
  Letter pages no longer link to length pages that don't exist (fix lands
  site-wide on the next full build_seo run). /milon/d/ kibbutz clue pages
  now list 267 kibbutzim (was 206 mixed-in).
- **2026-08-29 (later 2)** - Production stomped by a parallel session's CLI
  deploy from the stale seo/category-hubs branch minutes after main went live;
  /milon/d/ 404'd again. Redeployed from main. Rule going forward: production
  deploys ONLY via the git-linked main - no `vercel --prod` from branches.
- **2026-08-29 (later)** - Vercel Root Directory set to docs; site now serves
  from the correct root on every auto-deploy.
- **2026-08-29** - Deploy pipeline fixed: the Vercel project was never
  git-linked, so nothing merged to main since 2026-08-28 had actually
  shipped (the /milon/d/ 404). Repo now connected in the Vercel dashboard;
  every merge to main auto-deploys, and the IndexNow workflow backfill is
  fired after each first deploy of new page sets.
- **2026-08-28 (later)** — Competitor top-keyword research added
  (`competitor_keywords.md`): mordo's 76K-term label vocabulary mined, yo-yoo's
  own popularity ranking captured, arrowword's 199-page inventory listed, and a
  70-keyword consensus build-order produced. Re-run `scraper/keyword_research.py`
  with each snapshot.
- **2026-08-28** — Baseline established. Duopoly mordo+note on clue queries; yo-yoo owns
  per-length; 14across owns newspaper solutions (incl. יורם הרועה); arrowword the rising
  newcomer; spam (schlossmalberg.de) ranking = weak defense. We appear nowhere.
