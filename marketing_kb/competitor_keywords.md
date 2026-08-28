# Competitors' top keywords (free-tooling research, 2026-08-28)

**Tooling** (per the "free competitor SEO tools" ask): the roundup-recommended tools
(Ahrefs free tools, Semrush, Ubersuggest) are login-gated freemium with no free API, so
this research uses two genuinely free instruments instead:

1. **Bright Data MCP** (free tier, already connected) — SERP scraping + page scraping.
2. **`scraper/keyword_research.py`** — a keyless CLI over the competitors' own public,
   machine-readable output (works from any normal machine; the remote sandbox proxy blocks
   direct egress, in which case the same URLs go through the MCP).

Machine-readable results: `competitor_keywords.json`.

## The three sources and what they reveal

### 1. Mordo's complete keyword playbook — 76,384 label terms
The market leader labels every Blogspot post with the exact query phrasings it targets, and
the blog feed exposes the full vocabulary. Their targeting formula, by pattern:

| Query pattern | Labels | Share |
|---|---|---|
| X פירוש / X מילון | 23,918 | 31% |
| X ‏N אותיות | 12,984 | 17% |
| X תשבץ / X תשחץ | 11,733 | 15% |
| מה זה X? (question form) | 11,400 | 15% |
| X מילה נרדפת | 9,570 | 13% |
| bare definition | 6,680 | 9% |
| איך נקרא X | 99 | <1% |

**Takeaway:** every definition page should target ~6 phrasings of the same clue — exactly
the "ביטויים דומים" block. Note the #1 pattern is **פירוש/מילון**, matching what our own
Search Console found (build_seo.py docstring: users search "<word> פירוש", not by length).

### 2. yo-yoo's published popularity ranking — their top-traffic definitions
`/crossword/popular/1` is their own top-entries list (72 captured). The recurring themes:
מדינה ב־X, שחקן/סופר ישראלי ואמריקאי, קיבוץ/מושב ב־X, מין עוף/דג/קוף/ריקוד, תנ"ך
(פרשה, מטעמי המקרא), יסוד כימי, מלחין אוסטרי. Full list in the JSON.

### 3. arrowword's curated inventory — 199 pages the fastest climber chose to build
Their whole site is a bet on ~199 definitions; a newcomer's revealed ranking of what's
worth building. Full list in the JSON.

## Consensus top keywords (in ≥2 competitors' inventories)

70 definitions appear in arrowword's build list AND in mordo's vocabulary (count = how many
phrasing-variants mordo targets for it) or yo-yoo's top list. The top of the list:

| Keyword | Mordo variants | yo-yoo top |
|---|---|---|
| מסימני הניקוד | 8 | |
| ממלכי יהודה | 7 | |
| יסוד כימי | 6 | ✓ |
| ממלכי ישראל | 6 | |
| נהר באיטליה | 6 | |
| נווד | 6 | |
| כוכב השחר | 6 | |
| מטעמי המקרא | 5 | ✓ |
| נהר באפריקה | 5 | ✓ |
| מדינה באפריקה | 5 | |
| אל במיתולוגיה היוונית | 5 | |
| אות יוונית | 5 | |
| מפרשני המקרא | 5 | |
| מושב ברמת הגולן | 5 | |
| זמר ישראלי / זמרת ישראלית | 4 | ✓ |
| שחקן ישראלי / סופר ישראלי | 3 | ✓ |

(Full 70 in `competitor_keywords.json` → `consensus_top_keywords`.)

## How this plugs into the plan

- **P1 clue pages (SEO_PLAN.md):** the consensus list is the build order for the first
  `/milon/d/<הגדרה>/` pages — each covered from our own datasets (geo, culture, bible,
  mythology gap noted below), each carrying all 6 mordo phrasings as variants.
- **Data gaps revealed:** competitors' winners include categories we don't index yet —
  Greek mythology, יסודות כימיים, מלחינים, מיני בעלי חיים (עוף/דג/קוף), אבני החושן,
  סימני ניקוד, מלכי ישראל/יהודה. These are cheap curated lists to add to culture.json.
- **Tracking:** re-run `scraper/keyword_research.py` at each monthly TRACKING.md snapshot;
  diffs in arrowword's inventory and yo-yoo's popular list show where the market is moving.
