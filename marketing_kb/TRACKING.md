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

- **2026-08-30** - Strategy, not a ship: `DOMAIN_AND_MONETIZATION.md` added.
  Domain question (SEO_PLAN P0's open blocker) resolved: move off the dev
  subdomain within two weeks, `.co.il` if obtainable (tashbetz.co.il is
  registered but dormant, worth one offer) else `milontashbetz.com` ($11.25,
  available), with the 301/Change-of-Address checklist and the seven code
  locations that hardcode the host. Monetization modelled in
  `app/monetization_model.py`: display ads are the floor ($3.6-18k/yr even at a
  winning 100-300k pv/mo), gated behind ~30k pv/mo and Vercel Pro ($240/yr,
  since ads make the project commercial and Hobby forbids that); the נתיב game
  plus a subscription, a freemium hint tool, one direct sponsor (2-6x
  programmatic) and B2B data licensing carry the real upside. Next SERP
  snapshot should record the domain decision's execution date.
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
