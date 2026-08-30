# PR plan - phenomenon first, press after

Revised thesis (owner call, 2026-08-29): press has no reason to cover this
before it is a phenomenon - journalists report traction, they don't create
it. So the plan inverts: GROW the game in the communities where Israeli
solvers already live, measure until the numbers tell a story on their own,
and only then let angles B/C pitch themselves. Press is the trophy, not the
lever.

The one exception that works at zero traction: the research story (angle A)
in builder venues - a Show HN / r/artificial post needs novelty, not users,
and can seed the first links while the game grows. Everything mainstream
waits for the threshold below.

**Press threshold (when pitching starts making sense):** a streak of days
with 100+ organic daily players, or a week where shares (WhatsApp referrals
in analytics) outnumber direct visits, or one community thread that takes
off on its own. Until then, all effort goes to the growth track.

## The assets (what we can honestly pitch)

1. **The research story**: an autonomous AI pipeline that solves יורם הרועה's
   Haaretz תשבץ היגיון - reputedly the hardest cryptic in Hebrew - with a
   machine-checked proof per answer and two consecutive blind 100%-precision
   solves. Open source, honest negative results logged daily (DAILY.md), a
   published research note on the site. This is a genuinely novel AI+culture
   story with an Israeli hook.
2. **The game**: נתיב - a free Hebrew daily word-path game (Strands-style),
   easy + regular modes, streaks, WhatsApp sharing, global daily leaderboard.
   "The Israeli Wordle" framing writes itself.
3. **The dictionary**: the only crossword dictionary in Hebrew that explains
   every answer, 15K entities, free tools (pattern search, anagram).

## Three story angles, three audiences

### Angle A - tech press: "בינה מלאכותית פיצחה את התשבץ הקשה בעברית"
- Hook: the proof-gate methodology (the AI refuses to answer without
  mechanical proof - the opposite of hallucination), built autonomously by
  agents, open source.
- Targets: Geektime, Calcalist (מדור טק), TheMarker (טכנולוגיה), ynet
  (מדור טכנולוגיה), וואלה טק, גלובס טק. English: Hacker News (Show HN with
  the research note), r/crosswords, r/artificial.
- Deliverable to attach: the research note URL, 3 concrete before/after
  clue examples (paraphrased, no verbatim newspaper clues), repo link.

### Angle B - culture/leisure press: "נתיב, המשחק היומי העברי החדש"
- Hook: Wordle-style daily habit, Hebrew-native (no finals, RTL path
  tracing), themes from Israeli culture, free, no app install.
- Targets: ynet+ / מדור תרבות, mako, TimeOut ישראל, וואלה תרבות, מעריב
  סופהשבוע (they run the guides to cryptics - see the SERP research),
  radio segments that love a daily-game item (גלצ, כאן ב').
- Deliverable: the game link, a 30-60s screen recording, the share-card
  emoji result as the visual.

### Angle C - the meta pitch: Haaretz itself
- Hook they can't get elsewhere: "המכונה נגד יורם הרועה" - a feature about
  an AI trying to beat their own hardest setter, with his possible comment.
  Haaretz already writes about its cryptics culture (2025 magazine piece in
  our SERP snapshot).
- Sensitivity: lead with what the project does NOT do - no clue text
  republished, no answers before print, community sources respected. The
  copyright-respect stance is part of the story.

## Growth track - making it a phenomenon (ALL effort goes here first)

The share loop is built (WhatsApp button, streaks, spoiler-free result,
daily leaderboard). What it needs is seeding and retention:

1. Seed where solvers already are: 14across forum + the תשבצי היגיון
   Facebook groups - post as a fellow solver sharing a free tool, answer
   every comment for the first week. One genuine thread in the right group
   IS the phenomenon engine.
2. Family-and-friends WhatsApp groups: the emoji result is designed for
   exactly this - a nightly "who beat whom" ritual in 5 groups seeds the
   viral loop better than any post.
3. Retention: the daily theme rotation and streaks exist; watch the easy
   mode completion rate (leaderboard totals per day, free to read) and
   tune difficulty where players drop.
4. Measure daily players via the leaderboard totals + Vercel analytics;
   log weekly numbers in TRACKING.md. When the threshold above is crossed,
   open the press track.

## Community track (part of growth, cheap, compounding)

1. 14across forum + the תשבצי היגיון Facebook groups (the ones surfaced in
   the SERP research): share the free tools genuinely - the pattern solver
   and the explained trainer - as a solver, not an advertiser. One post per
   community, then answer questions.
2. higayonbarie.co.il and the ravmilim blog (Lior Liani's tips column):
   offer a guest explainer or a link exchange around "how cryptic devices
   work" - our PLAYBOOK-derived guide is the depth they lack.
3. Wikipedia: the article on תשבץ היגיון has thin external links; where the
   research note genuinely adds reader value it is a legitimate external
   link (no self-promotional editing beyond that - Wikipedia norms).

## Sequencing

| Week | Move | Why this order |
|---|---|---|
| 1 | Community posts (14across, FB groups) | social proof + first referral traffic before press looks |
| 1 | GSC indexing requests done, /milon/d/ live | press traffic lands on a working, indexed site |
| 2 | Angle A pitches (Geektime first - fastest yes) + Show HN | tech press cites community traction |
| 2-3 | Angle B pitches with the game's share numbers from week 1-2 | "X players in week one" beats a cold pitch |
| 3-4 | Angle C to Haaretz with clips from A/B coverage | the meta story lands better with momentum |

## The pitch (Hebrew draft, angle A)

> שלום [שם],
> בניתי מערכת בינה מלאכותית שפותרת את תשבץ ההיגיון של יורם הרועה בהארץ -
> שנחשב לקשה בעברית. הטוויסט: היא מסרבת לענות בלי הוכחה מכנית לכל תשובה,
> ולכן היא מעדיפה להשאיר משבצת ריקה מאשר לטעות - ההפך מהזיות AI. שני
> תשבצים עיוורים נפתרו ברצף בדיוק של 100% על התשובות שהוגשו.
> הכול בקוד פתוח, כולל יומן כישלונות יומי. אשמח לספר איך זה עובד -
> ולמה דווקא תשבצים הם מבחן קשה יותר ממבחני התכנות המקובלים.
> [קישור למחקר] · [קישור לריפו]

## Measurement (fold into TRACKING.md monthly)

- Referring domains + links (Search Console links report; free).
- Referral sessions to /nativ/ and /research/ (Vercel analytics).
- Brand queries in GSC ("נתיב משחק", "תשבץ בינה מלאכותית").
- Community thread engagement (replies, shares of the emoji result).

## Rules

- Never publish or attach newspaper clue text in any pitch material.
- The setter and the paper are treated with respect in every framing - the
  story is admiration for the craft, not "machines beat humans".
- Journalist names/emails: verify current beat before sending (media moves
  fast); enrich this file with named contacts during the next tracking run.
