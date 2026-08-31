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

1. `git pull`, then `python3 app/drain_requests.py` - it reads the committed
   queue snapshot (solver/lex/defs_queue_snapshot.json, mirrored from the API
   every Saturday by .github/workflows/defreq-mirror.yml, which also resolves
   already-fulfilled phrases). No egress needed. A live GET of
   https://tashbetz.gtmascode.dev/api/define-request works too when egress
   allows.
2. The script auto-fulfills mechanically into solver/lex/defs_requested.json.
   REVIEW every AUTO spec: open the matched answers and drop any that don't
   actually fit the phrase.
3. Hand-curate the NEEDS-CURATION phrases (most-requested first, skip junk)
   as "items" specs in the same file: verified facts only, 10-40 answers,
   a short description each, optional "wiki" source article. Content rules
   below apply.
4. `python3 app/build_defs.py`, commit, merge to main (auto-deploys).
5. If egress allows, `python3 app/drain_requests.py --resolve` to clear the
   fulfilled phrases from the server queue; otherwise leave them (idempotent).
6. Note the additions in marketing_kb/TRACKING.md's movement log.

## Topic crosswords (docs/nosim/)

Boards by subject and level, generated rather than scraped.

- `solver/grids_topic.py` holds the four templates: two crosswords
  (`classic7`, `classic9`) and two arrowwords (`arrow9`, `arrow11`). They are
  checked at import: an entry with nowhere to print its clue, or a cell that
  belongs to no entry, raises instead of shipping.
- `solver/topicgen.py` is the back end: `generate(topic, level, shape, seed)`.
  Level 1-2 fill only from answers the corpus actually saw in printed puzzles;
  3-4 open the whole lexicon. Every clue carries a checkable proof.
- **`evals/topicgen_eval.py` is the gate. Run it before publishing a change to
  the generator, the grids or the banks** (`python3 evals/topicgen_eval.py`,
  or `--quick` while iterating). It re-derives every judgement from the
  committed data rather than trusting the generator, and it is what catches a
  "topic crossword" that came out with two on-topic answers in it. Runs land
  in `evals/runs/topicgen/`.
- Rebuild: `python3 app/build_topics.py --generate` regenerates
  `docs/nosim/puzzles.json` (tens of minutes: it takes the best of three seeds
  per board) and the pages; without `--generate` it only re-renders from the
  committed JSON (seconds). `--effort 0.5` halves each board's search.
- The search is bounded by a NODE COUNT, not a clock, so a seed reproduces.
  The boards committed on 2026-08-31 were generated just before that change and
  will not reproduce byte-for-byte; anything generated since does. Re-running
  the full rebuild replaces them with reproducible equivalents when convenient.
- Term banks live in `solver/lex/topics.json` (curated, ten bagrut subjects)
  and `solver/lex/fillbank.json` (common words for the filler). Content rules
  below apply to both: a description is published verbatim as a clue.

## Weekly news crossword

`.github/workflows/news-weekly.yml` runs Sundays. `scraper/news_israel.py`
reads Israeli news RSS and keeps only *which entities already in our index*
were mentioned; the clue published is our own description of that entity. No
headline text is stored or published, and an entity we have no description for
is dropped rather than described from the headline. It writes
`solver/lex/topics_news.json`, which `topicgen` merges as the topic
`hadashot`. The feeds are unreachable from the agent sandbox (the egress proxy
denies them), which is why this runs on a GitHub runner and commits.

## Personal crossword requests (/bakasha/)

Readers ask for a board on a subject of their own; the queue is
`docs/api/puzzle-request.js`, mirrored into
`solver/lex/pzreq_queue_snapshot.json` every Saturday by the same workflow as
the definition queue. Weekly:

1. `git pull`, then `python3 app/drain_puzzle_requests.py`. It builds every
   requested topic the entity index can already answer and appends it to
   `docs/nosim/puzzles.json`.
2. **Read every requested topic before it ships.** It is reader-written text
   that ends up in a page title; nothing is published automatically.
3. Topics the script could not build need a curated bank in
   `solver/lex/topics.json` first, content rules below.
4. `python3 app/build_topics.py`, commit, merge to main (auto-deploys).
5. If egress allows, `python3 app/drain_puzzle_requests.py --resolve`.

## Content rules

- No newspaper clue text is ever published (see README). This covers news
  headlines too: the weekly puzzle publishes our descriptions, never theirs.
- No em-dashes in published text; plain hyphens.
- Every generated page carries the נתיב promo strip; keep it when templating.
- A term bank description is published verbatim as a crossword clue, so it has
  to be a verified fact, must not contain its own answer, and must identify
  that answer rather than a whole category. The bank builders check the first
  two; the third is on the person writing it.

## Marketing / SEO context

Competitor knowledge base, keyword research, tracking runbook and the plan
live in `marketing_kb/`. Update `marketing_kb/TRACKING.md`'s movement log when
shipping SEO-relevant changes.
