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

## Content rules

- No newspaper clue text is ever published (see README).
- No em-dashes in published text; plain hyphens.
- Every generated page carries the נתיב promo strip; keep it when templating.

## Marketing / SEO context

Competitor knowledge base, keyword research, tracking runbook and the plan
live in `marketing_kb/`. Update `marketing_kb/TRACKING.md`'s movement log when
shipping SEO-relevant changes.
