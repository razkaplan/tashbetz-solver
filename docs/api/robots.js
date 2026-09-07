// robots.txt, served dynamically so we can see which AI crawlers actually
// fetch it. GA cannot: it runs from JavaScript and filters bots, so GPTBot and
// friends are invisible there by construction. Every well-behaved crawler
// requests robots.txt before crawling, which makes this the cheapest honest
// signal about who is reading the site.
//
// SAFETY: this route must never fail. Google treats a 5xx on robots.txt as a
// temporary "do not crawl", so a broken logger here could pause crawling of
// the whole site. The response is therefore built first and returned no matter
// what; logging is strictly best-effort inside a try/catch with a timeout.
//
// Storage mirrors api/leaderboard.js: zero-dependency Blob REST, with the whole
// record encoded in the PATHNAME so there is never a read-modify-write race.
//   ai-crawl/<YYYY-MM-DD>/<bot>~<hour>.json
// Repeat hits in the same hour overwrite the same path (random suffix off), so
// writes are bounded at 24 per bot per day instead of one per request. That
// trades exact hit counts for "which hours was this bot active", which is the
// question actually being asked and costs far less.

"use strict";

const BLOB_API = "https://blob.vercel-storage.com";
const PREFIX = "ai-crawl/";
// 1500ms looked generous until testing: the first write after an idle period
// pays TLS setup to the blob API and aborted every time, so exactly the records
// we care about went missing while warm ones succeeded. Crawlers tolerate a
// slow robots.txt far better than a missing one, and this route is fetched a
// handful of times per bot per day, so buy the headroom.
const WRITE_TIMEOUT_MS = 4000;

const ROBOTS = [
  "User-agent: *",
  "Allow: /",
  "",
  "# AI and answer-engine crawlers are welcome. The dictionary and the",
  "# practice puzzles are ours to share; the newspaper corpus is not here.",
  "User-agent: GPTBot",
  "Allow: /",
  "",
  "User-agent: OAI-SearchBot",
  "Allow: /",
  "",
  "User-agent: ChatGPT-User",
  "Allow: /",
  "",
  "User-agent: ClaudeBot",
  "Allow: /",
  "",
  "User-agent: Claude-SearchBot",
  "Allow: /",
  "",
  "User-agent: PerplexityBot",
  "Allow: /",
  "",
  "User-agent: Google-Extended",
  "Allow: /",
  "",
  "User-agent: Applebot-Extended",
  "Allow: /",
  "",
  "User-agent: CCBot",
  "Allow: /",
  "",
  "Sitemap: https://tashbetz.gtmascode.dev/sitemap.xml",
  "",
].join("\n");

// Canonical names for the crawlers worth naming. Order matters: the first
// match wins, so put the more specific token first (Claude-SearchBot before
// ClaudeBot, which is a prefix of nothing but reads ambiguously otherwise).
const KNOWN = [
  ["OAI-SearchBot", /OAI-SearchBot/i],
  ["ChatGPT-User", /ChatGPT-User/i],
  ["GPTBot", /GPTBot/i],
  ["Claude-SearchBot", /Claude-SearchBot/i],
  ["Claude-User", /Claude-User/i],
  ["ClaudeBot", /ClaudeBot|anthropic-ai/i],
  ["PerplexityBot", /PerplexityBot/i],
  ["Perplexity-User", /Perplexity-User/i],
  ["Google-Extended", /Google-Extended/i],
  ["Applebot-Extended", /Applebot-Extended/i],
  ["Applebot", /Applebot/i],
  ["CCBot", /CCBot/i],
  ["Bytespider", /Bytespider/i],
  ["meta-externalagent", /meta-externalagent|FacebookBot/i],
  ["Amazonbot", /Amazonbot/i],
  ["cohere-ai", /cohere-ai/i],
  ["DuckAssistBot", /DuckAssistBot/i],
  ["YouBot", /YouBot/i],
  ["Diffbot", /Diffbot/i],
  // Conventional search crawlers, kept so the AI share has a denominator.
  ["Googlebot", /Googlebot/i],
  ["bingbot", /bingbot|BingPreview/i],
  ["Yandex", /YandexBot/i],
  ["DuckDuckBot", /DuckDuckBot/i],
  ["Bravebot", /Bravebot/i],
];

const LOOKS_LIKE_BOT = /bot|crawler|spider|scrape|fetch|agent|python-requests|curl|wget|headless/i;

function classify(ua) {
  if (!ua) return null;
  for (const [name, re] of KNOWN) if (re.test(ua)) return name;
  if (!LOOKS_LIKE_BOT.test(ua)) return null; // ordinary browser: not our business
  // Unknown crawler: name it after the token that actually identifies it.
  // Taking the FIRST token looked fine in tests against "SomeCrawler/0.9" but
  // is useless in the wild, where almost every bot opens with "Mozilla/5.0"
  // and every unknown would collapse into one "other-Mozilla" bucket, which is
  // precisely the discovery this is here to do. Prefer a bot-looking token.
  const m = ua.match(/([A-Za-z0-9._-]*(?:bot|crawler|spider|agent|scraper)[A-Za-z0-9._-]*)/i)
        || ua.match(/(curl|wget|python-requests|headless[A-Za-z]*)/i)
        || ua.match(/([A-Za-z0-9._-]{3,40})(?:\/|\s|$)/);
  const token = (m && m[1]) || "unknown";
  return "other-" + token.replace(/[^A-Za-z0-9._-]/g, "").slice(0, 32);
}

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

async function logHit(bot, ua, path) {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const hour = String(now.getUTCHours()).padStart(2, "0");
  const safe = bot.replace(/[^A-Za-z0-9._-]/g, "").slice(0, 48);
  const key = PREFIX + date + "/" + safe + "~" + hour + ".json";

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), WRITE_TIMEOUT_MS);
  try {
    await fetch(BLOB_API + "/" + key, {
      method: "PUT",
      headers: {
        Authorization: "Bearer " + token(),
        "x-api-version": "7",
        "x-content-type": "application/json",
        "x-add-random-suffix": "0",
      },
      body: JSON.stringify({ bot, at: now.toISOString(), path, ua: String(ua).slice(0, 300) }),
      signal: ctrl.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

module.exports = async function handler(req, res) {
  try {
    const ua = (req.headers && (req.headers["user-agent"] || req.headers["User-Agent"])) || "";
    const bot = classify(ua);
    if (bot && token()) {
      await logHit(bot, ua, (req.url || "/robots.txt").slice(0, 120));
    }
  } catch (e) {
    // Never let the logger affect the response. A missed record costs nothing;
    // a 5xx here could stop the site being crawled at all.
    console.error("robots logging failed:", e && e.message);
  }
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  // No caching: a cached robots.txt is served by the CDN and never reaches this
  // function, which would make the log silently stop after the first fetch.
  res.setHeader("Cache-Control", "no-store");
  res.status(200).send(ROBOTS);
};
