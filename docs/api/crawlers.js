// Read side of the AI crawler log written by api/robots.js.
// GET /api/crawlers            summary for the last 30 days
// GET /api/crawlers?days=90    longer window
//
// Everything is derived from blob PATHNAMES (ai-crawl/<date>/<bot>~<hour>.json),
// so this is one list call with no content fetches. A bot's "hours" is the
// number of distinct UTC hours it was seen in, which is the volume proxy the
// writer records; it is deliberately not a raw hit count.

"use strict";

const BLOB_API = "https://blob.vercel-storage.com";
const PREFIX = "ai-crawl/";

// Which of the names api/robots.js assigns are AI/answer-engine crawlers, as
// opposed to conventional search or unclassified bots.
const AI = new Set([
  "GPTBot", "OAI-SearchBot", "ChatGPT-User",
  "ClaudeBot", "Claude-SearchBot", "Claude-User",
  "PerplexityBot", "Perplexity-User",
  "Google-Extended", "Applebot-Extended",
  "CCBot", "Bytespider", "meta-externalagent",
  "Amazonbot", "cohere-ai", "DuckAssistBot", "YouBot", "Diffbot",
]);

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

async function listAll() {
  const out = [];
  let cursor = null;
  for (let page = 0; page < 20; page++) {
    const url = BLOB_API + "/?prefix=" + encodeURIComponent(PREFIX) + "&limit=1000" +
      (cursor ? "&cursor=" + encodeURIComponent(cursor) : "");
    const r = await fetch(url, { headers: { Authorization: "Bearer " + token() } });
    if (!r.ok) throw new Error("blob list failed: " + r.status);
    const j = await r.json();
    out.push(...(j.blobs || []));
    cursor = j.cursor || j.nextCursor || null;
    if (!cursor || !j.hasMore) break;
  }
  return out;
}

function parse(pathname) {
  // ai-crawl/<date>/<bot>~<hour>.json
  if (!pathname.startsWith(PREFIX)) return null;
  const rest = pathname.slice(PREFIX.length);
  const slash = rest.indexOf("/");
  if (slash < 0) return null;
  const date = rest.slice(0, slash);
  const m = rest.slice(slash + 1).match(/^(.+)~(\d{2})\.json$/);
  if (!m) return null;
  return { date, bot: m[1], hour: m[2] };
}

module.exports = async function handler(req, res) {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("X-Robots-Tag", "noindex");
  res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=600");
  if (!token()) {
    return res.status(200).json({ error: "no blob store configured", bots: [] });
  }
  try {
    const days = Math.min(365, Math.max(1, parseInt((req.query && req.query.days) || "30", 10) || 30));
    const cutoff = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

    const recs = (await listAll()).map(b => parse(b.pathname)).filter(Boolean)
      .filter(r => r.date >= cutoff);

    const byBot = new Map();
    const byDate = new Map();
    for (const r of recs) {
      if (!byBot.has(r.bot)) byBot.set(r.bot, { bot: r.bot, hours: 0, days: new Set(), first: r.date, last: r.date });
      const b = byBot.get(r.bot);
      b.hours += 1;
      b.days.add(r.date);
      if (r.date < b.first) b.first = r.date;
      if (r.date > b.last) b.last = r.date;
      byDate.set(r.date, (byDate.get(r.date) || 0) + 1);
    }

    const bots = [...byBot.values()]
      .map(b => ({ bot: b.bot, ai: AI.has(b.bot), hoursActive: b.hours, daysActive: b.days.size, first: b.first, last: b.last }))
      .sort((x, y) => y.hoursActive - x.hoursActive);

    return res.status(200).json({
      windowDays: days,
      note: "hoursActive counts distinct UTC hours the bot fetched robots.txt, not raw hits",
      totals: {
        distinctBots: bots.length,
        aiBots: bots.filter(b => b.ai).length,
        aiHours: bots.filter(b => b.ai).reduce((s, b) => s + b.hoursActive, 0),
        otherHours: bots.filter(b => !b.ai).reduce((s, b) => s + b.hoursActive, 0),
      },
      bots,
      byDate: [...byDate.entries()].sort().map(([date, hours]) => ({ date, hours })),
    });
  } catch (e) {
    return res.status(200).json({ error: String((e && e.message) || e), bots: [] });
  }
};
