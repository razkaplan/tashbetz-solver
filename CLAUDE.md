# Working rules for this repo

## Deploying (IMPORTANT)

Production (`tashbetz.gtmascode.dev`) deploys **only** via the git-linked
Vercel project: merge to `main` and it auto-deploys (Root Directory = docs).

**Never run `vercel deploy --prod` / `vercel --prod` from a working tree or a
branch.** On 2026-08-29 a CLI production deploy from a stale feature branch
overwrote the live site minutes after main went live and took new pages down.
Preview deploys of branches happen automatically on push; production comes
from `main` alone.

## Building the milon (docs/milon/)

`app/build_seo.py` needs the gitignored corpus asset
`data/culture/descriptions.json`. In a fresh clone it is ABSENT, and a rebuild
without it strips ~12,700 descriptions and deletes thousands of rich entity
pages (this shipped once, 2026-08-28, and had to be restored from git). The
script now refuses to run without the file; do not bypass with
ALLOW_BARE_MILON=1 unless a description-less milon is truly intended.
`app/build_defs.py` (clue pages, /milon/d/) and `app/build_nativ.py` use only
committed data and are safe anywhere.

## Definition requests (demand-driven /milon/d/ pages)

Readers request missing definitions from the site (the milon hub's search-miss
button and the /milon/d/ request box POST to /api/define-request). A weekly
Routine drains the queue; the procedure, runnable by any session:

1. GET https://tashbetz.gtmascode.dev/api/define-request (via Bright Data MCP
   when direct egress is blocked; save the JSON to a file).
2. `python3 app/drain_requests.py <queue.json>` - mechanical fulfillment into
   solver/lex/defs_requested.json. REVIEW every AUTO spec: open the matched
   answers and drop any that don't actually fit the phrase.
3. Hand-curate the NEEDS-CURATION phrases (most-requested first, skip junk)
   as "items" specs in the same file: verified facts only, 10-40 answers,
   a short description each, optional "wiki" source article. Content rules
   below apply.
4. `python3 app/build_defs.py`, commit, merge to main (auto-deploys).
5. If egress allows, `python3 app/drain_requests.py --resolve` to clear the
   fulfilled phrases from the server queue; otherwise leave them (idempotent).
6. Note the additions in marketing_kb/TRACKING.md's movement log.

## Content rules

- No newspaper clue text is ever published (see README).
- No em-dashes in published text; plain hyphens.
- Every generated page carries the נתיב promo strip; keep it when templating.

## Marketing / SEO context

Competitor knowledge base, keyword research, tracking runbook and the plan
live in `marketing_kb/`. Update `marketing_kb/TRACKING.md`'s movement log when
shipping SEO-relevant changes.
