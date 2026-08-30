# Domain move and monetization: the decision memo

Written 2026-08-30, from the competitor research in this folder, the live
inventory (5,747 sitemap URLs: 5,191 `/milon/e/`, 51 `/milon/d/`, ~450
category-by-length, 101 `/tirgul/`, the נתיב game), and current 2026 ad-market
facts. Numbers are reproducible: `python3 app/monetization_model.py`.

Everything below assumes the SEO_PLAN P1/P2 ship continues. The domain and the
money questions do not change what to build next; they change where it lives
and what it is allowed to become.

---

## 1. The domain: yes, move, within two weeks

### Should you

Yes, and the reason is timing rather than SEO upside. A move never adds
authority. What it buys:

1. **Trust and click-through with a Hebrew consumer audience.** Every player in
   this market is a `.co.il` (note, yo-yoo, arrowword, 14across) or a brand
   people already know (mordo). A crossword solver scanning a Google result
   page sees `tashbetz.gtmascode.dev` and reads "someone's dev sandbox". The
   audience here skews older and non-technical; the domain is doing real damage
   to CTR on every impression you eventually earn.
2. **Separability.** The property currently lives inside a personal portfolio
   domain. It cannot be sold, spun out, handed to a partner, or given its own
   brand identity while it is a subdomain of `gtmascode.dev`, and any authority
   the root domain accumulates is entangled with unrelated content.
3. **It is free right now and expensive later.** Today: ~5,750 URLs indexed,
   **zero** competitive rankings (2026-08-28 snapshot), effectively no
   backlinks. A 301 costs a rebuild and a Search Console form. After the press
   push in `PR_PLAN.md` lands links, and after the clue pages start ranking,
   the same move costs a 4-8 week traffic dip plus the risk that the links you
   worked for point at the wrong host.

The honest counter-argument: a brand-new domain also starts with zero
authority, so you are not "losing" anything by staying. True. That is precisely
why now is the moment. The cost of the move only goes up from here, and the
benefit (brand, CTR, optionality) starts compounding from the first indexed
page on the new host.

### Which

Preference order, best fit first:

| Option | Status (checked 2026-08-30) | Verdict |
|---|---|---|
| `tashbetz.co.il` | **Registered**, resolves, but has zero Google presence (no indexed pages for the domain) - it looks parked or dormant | The ideal name. Worth one acquisition attempt via the ISOC-IL whois contact or a broker. Cap the budget: an exact-match domain is a nice-to-have, not a moat. Give it two weeks, not two months |
| `tashbetzim.co.il`, `pitaron.co.il`, `pitronim.co.il`, `milon.co.il` | Registered, resolving | Not available |
| `milontashbetz.co.il`, `pitaronim.co.il`, `hagdarot.co.il`, `hagdara.co.il` | No DNS records. NOT proof of availability - `.il` needs a registry check, which this sandbox could not reach | Check first at an Israeli registrar (~60-100 ILS/yr). A two-word `.co.il` beats any `.com` for this audience |
| `milontashbetz.com` | **Available, $11.25/yr** (Vercel registrar) | The recommended floor. It is the head keyword ("מילון תשבצים") transliterated, and `.com` is the only global TLD this audience reads as a real site |
| `tashchetz.com`, `pitaronim.com` | Available, $11.25/yr | Fallbacks; weaker than the above |
| `tashbetz.org` ($8.49), `tashbetz.co` ($29.99), `tashbetz.io` ($30) | Available | Avoid. `.io`/`.co`/`.org` read as tech-project or nonprofit to Israeli consumers. Do not trade audience trust for an exact-match string |
| `tashbetz.com`, `tashbetz.net`, `tashbetz.app` | Taken | - |

**Recommendation:** register `milontashbetz.com` today for $11 so nothing is
blocked, and in parallel open a `.co.il` track (registry check on the two-word
options, one acquisition offer on `tashbetz.co.il`). If a `.co.il` lands inside
two weeks, use it and keep the `.com` as a redirect; otherwise ship on the
`.com` and stop thinking about it. Do not let the perfect domain delay the move
by a quarter, which is what usually happens here.

### When

**Before the next content push, and before any press.** Concretely: this week
or next. The sequence that keeps the cost near zero is domain first, then keep
shipping clue pages onto the new host, then pitch press.

### How (the actual work)

The domain is hardcoded in five builders and two workflows, and appears in
5,801 generated files, so the change is mechanical but not a one-liner:

- `app/build_seo.py`, `app/build_defs.py`, `app/build_trainer.py`,
  `app/patch_milon_kibbutz_split.py` (`BASE = ...`), `app/drain_requests.py`
  (`API = ...`), `.github/workflows/defreq-mirror.yml` (API URL),
  `.github/workflows/indexnow.yml` (`HOST = ...`). Pull `BASE` from one place
  (an env var with the new domain as default) instead of repeating the literal.
- Rebuild everything so canonicals, `og:url`, JSON-LD and `sitemap.xml` all
  carry the new host, then merge to main (which auto-deploys, per CLAUDE.md).
- In Vercel: add the new domain to the `tashbetz-solver` project, make it the
  production domain, and leave `tashbetz.gtmascode.dev` attached as a permanent
  301 to it. Keep those redirects forever, not six months.
- Search Console: create the new property, verify, submit the sitemap, then run
  **Change of Address** on the old property (it supports subdomain-to-domain
  moves and forwards signals; it needs the 301s live first).
- Fire the IndexNow workflow against the new host after the first deploy.
- Update GA4's stream URL, the repo README, and any link you control.

Two things that would otherwise break quietly: the `/api/` endpoints
(`define-request`, `leaderboard`) move with the domain, so anything caching the
old origin (the weekly drain, the game's leaderboard POSTs) needs the new URL;
and `docs/vercel.json`'s CSP has `form-action 'self'`, which is fine, but check
the game's share links and OG images resolve on the new host.

---

## 2. Monetization: ads are the floor, not the plan

### What ads actually pay here

The model (`app/monetization_model.py`, gross, before the hosting floor):

| pageviews/mo | $1.50 RPM | $3.00 RPM | $6.00 RPM |
|---|---|---|---|
| 10,000 | $180/yr | $360/yr | $720/yr |
| 50,000 | $900/yr | $1,800/yr | $3,600/yr |
| 100,000 | $1,800/yr | $3,600/yr | $7,200/yr |
| 250,000 | $4,500/yr | $9,000/yr | $18,000/yr |
| 500,000 | $9,000/yr | $18,000/yr | $36,000/yr |
| 1,000,000 | $18,000/yr | $36,000/yr | $72,000/yr |

Why those RPMs and not the $10-20 figures in ad-network marketing: Israel is a
mid-tier ad market (real, but well under US/UK), and crossword help is a
low-commercial-intent vertical. Nobody bids to reach someone who wants a
five-letter kibbutz. You get remnant display. $1.50-3 on self-serve AdSense and
$5-7 on a managed network is the honest band; treat any number here as a
placeholder until the network's own report replaces it.

**The gates you will hit, as of 2026:**

- **AdSense** - no minimum, start whenever.
- **Mediavine** main network is now revenue-based (about $5,000/yr in ad
  earnings), with a **Journey** on-ramp at 1,000 sessions. Journey is the
  realistic first upgrade.
- **Raptive** dropped to **25,000 pageviews/mo** (Oct 2025), which makes it the
  first serious RPM jump within reach.
- **Ezoic raised its minimum to 250,000 users/mo** (Feb 2026), so the old "use
  Ezoic while small" advice is dead.

**The cost nobody mentions:** running ads makes this a commercial project, and
**Vercel's Hobby plan forbids commercial use, naming AdSense explicitly**. Ads
therefore start at **$240/yr for Vercel Pro**. Break-even on that alone is
about 13,000 pageviews/mo at AdSense rates, 6,700 at a decent layout. Below
that, ads are a net loss that also slows your pages while you are trying to
earn rankings.

### The verdict on ads

Turn them on, but late and narrowly:

- **Not before ~30,000 pageviews/mo** or three months of stable growth.
- **Only on the dictionary pages** (`/milon/d/`, `/milon/e/`, the
  category-by-length pages). Users landing there have their answer in ten
  seconds and leave; an ad there costs you nothing you were keeping.
- **Never on the solver, the נתיב game, or the explained-solutions pages.** The
  competitor research says mordo and note both lose on "heavy ads, ads above
  content". Being the fast clean one is a real differentiator and it is worth
  more than the incremental $40/mo those placements would add.
- Realistic outcome even if you win this niche: a #2-3 player at maturity might
  see 100-300k pageviews/mo, i.e. **$3,600-18,000/yr**. That is a good side
  income, not a business, and it is not proportional to the effort this project
  is absorbing. Which is the whole argument for what follows.

### The alternatives, ranked by revenue per unit of effort

**1. The daily game (נתיב) is the actual business.** Games beat dictionary
long tail on every economic axis: repeat visits instead of one-and-done,
5-20x the pageviews per user, an owned audience (email/push) that Google
cannot take away, and a subscription people actually buy. A 15 ILS/mo tier
(no ads + puzzle archive + stats):

| monthly actives | 1% convert | 2% convert | 3% convert |
|---|---|---|---|
| 5,000 | $2,600/yr | $5,300/yr | $7,900/yr |
| 20,000 | $10,600/yr | $21,200/yr | $31,800/yr |
| 50,000 | $26,500/yr | $52,900/yr | $79,400/yr |

At 20,000 monthly actives the subscription alone beats the entire dictionary's
ad revenue at ten times that pageview count. The virality work already shipped
(challenge links, percentile lines, share squares) is the highest-leverage code
in the repo and nothing in the current plan treats it that way.

**2. Freemium solving assistance, which no competitor can copy.** "Photograph
your תשבץ היגיון, get graded hints" - free 3 hints/day, ~19 ILS/mo unlimited.
This is the one asset that is genuinely defensible: 14across publishes bare
answers, nobody explains wordplay, and the solver plus PLAYBOOK is years of
work no incumbent will replicate. Watch the unit economics (inference cost per
solve is real, unlike a static page) and price above it.

**3. A direct sponsor beats programmatic by 2-6x at the same traffic.** The
audience is older, educated, and has money, which is exactly what programmatic
under-prices and a direct advertiser over-values. One sponsor at 3,000 ILS/mo
is ~$10,600/yr, which is 5.9x the programmatic revenue at 50k pageviews/mo and
still 2x at 150k. Needs a media kit and 50k+ pageviews to be credible. Natural
buyers: publishers and book chains, cultural institutions, insurers and health
services aimed at 55+, banks.

**4. B2B licensing: smallest audience, best margin.** The 129k lexicon, the
31k clue-answer corpus, and the crossword-spelling-normalized entity data with
descriptions do not exist anywhere else in Hebrew. Buyers: puzzle constructors
and puzzle houses (zolo.co.il is both a competitor and a plausible customer),
newspapers that commission puzzles, and app developers (xword.co.il, "התשחץ
שלי"). A constructor tool at 50-200 ILS/mo will not find a thousand customers -
the Hebrew constructor population is small - but 2,000-5,000 ILS/mo from a
handful of professional users is realistic and costs almost no ongoing effort.
Caveat below on what data may be licensed.

**5. Affiliate and donations: add them, expect noise.** Puzzle books via
Israeli book retailers on relevant pages, and a "קנה לי קפה" link. Together,
plausibly $50-200/mo at scale. Nearly free to add; do not build a plan on it.

### Sequencing

| When | Do | Do not |
|---|---|---|
| Weeks 0-2 | Domain move. Wire GSC properly (SEO_PLAN P0 still open). Confirm GA4 is reporting on the new host | Do not add ads to a site with no traffic |
| Months 1-3 | Keep shipping clue pages and weekly explained solutions. Push the game: email/push capture, retention, the archive | Do not build a payment flow before there is an audience to charge |
| Months 3-6 | AdSense on dictionary pages only, once past ~30k pv/mo. Apply to Mediavine Journey. Ship the freemium hint tool if solver reliability holds | Do not put ads on the game or the solver |
| Months 6-12 | Raptive at 25k+ pv/mo. Media kit and one direct sponsor. Open licensing conversations with a publisher and a puzzle house | Do not let ad density creep into the differentiator |

### Risks worth naming before money is involved

- **Revenue changes the copyright calculus.** The repo already forbids
  publishing newspaper clue text and forbids using the scraped mordo corpus as
  page content (SEO_PLAN, README). Those rules become load-bearing the moment
  the site earns: a non-commercial research site and an ad-supported
  competitor are treated very differently by both the sources and their
  lawyers. Keep generation strictly from owned datasets, and keep licensing
  offers to data you built rather than data you crawled.
- **AI Overviews are the structural threat to the entire ad model.** "What is
  the 5-letter answer" is exactly the query an AI answer box eats. Every
  alternative above (game, subscription, tool, sponsor, licensing) is a hedge
  against that, and the dictionary long tail alone is not.
- **The privacy/consent layer.** Ads plus GA4 means a real privacy policy and a
  consent mechanism; Israeli privacy law enforcement tightened in 2025 and EU
  visitors need it regardless.
- **Opportunity cost.** The research note is worth more as a credibility asset
  than the dictionary is as an ad property. Do not warp the product to chase
  $300/mo.

---

## What would sharpen all of this

The one thing missing here is your actual traffic. GA4 (`G-V7LGK8CMHQ`) is
live but Vercel Web Analytics is not enabled on the project, so this memo
models ranges rather than reading your numbers. With monthly pageviews,
sessions, top landing pages and GSC impressions, every table above collapses to
a single row: `python3 app/monetization_model.py --pv <your number>`.
