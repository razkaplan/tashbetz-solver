// Global daily leaderboard for נתיב (nativ).
// Zero-dependency: talks to the Vercel Blob REST API directly with fetch.
// Storage: one JSON snapshot blob per write at nativ-lb/<date>/<ts>.json.
// Each write uses a fresh pathname because the blob CDN caches a given URL
// for at least ~60s; a new URL is always a cache miss, so reads see the
// latest snapshot immediately (verified empirically). Old snapshots are
// deleted best-effort after each write. Read-modify-write still races under
// true concurrency (last writer wins), acceptable at this scale.
//
// HONESTY NOTE: scores are self-reported by the client after a win. There is
// no server-side replay of the puzzle, so the board is only as honest as its
// players. Clamps below stop garbage, not determined cheaters.

"use strict";

const BLOB_API = "https://blob.vercel-storage.com";
const PREFIX = "nativ-lb/";
const TOP_N = 50;
const MAX_ENTRIES = 2000; // hard cap per day, keeps the blob tiny

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

function sanitizeName(raw) {
  if (typeof raw !== "string") return null;
  // strip control chars, angle brackets and backslashes; collapse whitespace
  let name = raw
    .replace(/[\u0000-\u001f\u007f<>\\]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 20);
  return name.length ? name : null;
}

function clampInt(v, min, max) {
  const n = Number(v);
  if (!Number.isFinite(n)) return null;
  const i = Math.round(n);
  if (i < min || i > max) return null;
  return i;
}

function sortEntries(entries) {
  entries.sort(function (a, b) {
    return a.h - b.h || a.t - b.t || (a.at || 0) - (b.at || 0);
  });
}

async function listSnapshots(date) {
  const listRes = await fetch(
    BLOB_API + "/?prefix=" + encodeURIComponent(PREFIX + date + "/") + "&limit=1000",
    { headers: { Authorization: "Bearer " + token() } }
  );
  if (!listRes.ok) throw new Error("blob list failed: " + listRes.status);
  const listing = await listRes.json();
  const blobs = listing.blobs || [];
  // pathnames embed a zero-padded timestamp, so lexicographic max = latest
  blobs.sort(function (a, b) { return a.pathname < b.pathname ? -1 : 1; });
  return blobs;
}

async function readDay(date) {
  const blobs = await listSnapshots(date);
  const latest = blobs[blobs.length - 1];
  const day = { entries: [], _snapshots: blobs.map(function (b) { return b.url; }) };
  if (!latest) return day;
  const get = await fetch(latest.url, { cache: "no-store" });
  if (!get.ok) return day;
  const data = await get.json().catch(function () { return null; });
  if (data && Array.isArray(data.entries)) day.entries = data.entries;
  return day;
}

async function writeDay(date, day) {
  const path = PREFIX + date + "/" + String(Date.now()).padStart(14, "0") + ".json";
  const put = await fetch(BLOB_API + "/" + path, {
    method: "PUT",
    headers: {
      Authorization: "Bearer " + token(),
      "x-api-version": "7",
      "x-content-type": "application/json",
      "x-add-random-suffix": "0",
    },
    body: JSON.stringify({ entries: day.entries }),
  });
  if (!put.ok) throw new Error("blob put failed: " + put.status);
  // best-effort cleanup of superseded snapshots
  const old = day._snapshots || [];
  if (old.length) {
    await fetch(BLOB_API + "/delete", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token(),
        "x-api-version": "7",
        "content-type": "application/json",
      },
      body: JSON.stringify({ urls: old }),
    }).catch(function () {});
  }
}

function sameOriginOk(req) {
  // Same-origin only: browsers omit Origin on same-origin GETs; for POSTs
  // (and any request that carries Origin) require it to match our host.
  const origin = req.headers.origin;
  if (!origin) return true;
  const host = req.headers["x-forwarded-host"] || req.headers.host || "";
  try {
    return new URL(origin).host === host;
  } catch (e) {
    return false;
  }
}

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  // no Access-Control-Allow-Origin header on purpose: same-origin only

  if (!token()) {
    res.status(503).json({ error: "leaderboard storage not configured" });
    return;
  }
  if (!sameOriginOk(req)) {
    res.status(403).json({ error: "forbidden" });
    return;
  }

  try {
    if (req.method === "GET") {
      const date = String((req.query && req.query.date) || "");
      if (!DATE_RE.test(date)) {
        res.status(400).json({ error: "date must be YYYY-MM-DD" });
        return;
      }
      const day = await readDay(date);
      sortEntries(day.entries);
      res.status(200).json({
        date: date,
        total: day.entries.length,
        top: day.entries.slice(0, TOP_N).map(function (e) {
          return { name: e.n, timeSec: e.t, hints: e.h, mistakes: e.m };
        }),
      });
      return;
    }

    if (req.method === "POST") {
      let body = req.body;
      if (typeof body === "string") {
        try { body = JSON.parse(body); } catch (e) { body = null; }
      }
      if (!body || typeof body !== "object") {
        res.status(400).json({ error: "invalid JSON body" });
        return;
      }
      const date = String(body.date || "");
      const name = sanitizeName(body.name);
      const timeSec = clampInt(body.timeSec, 10, 3600);
      const hints = clampInt(body.hints, 0, 10);
      const mistakes = clampInt(body.mistakes, 0, 50);
      if (!DATE_RE.test(date) || !name || timeSec === null || hints === null || mistakes === null) {
        res.status(400).json({ error: "invalid fields" });
        return;
      }

      const day = await readDay(date);
      const entry = { n: name, t: timeSec, h: hints, m: mistakes, at: Date.now() };
      const idx = day.entries.findIndex(function (e) { return e.n === name; });
      if (idx >= 0) {
        const old = day.entries[idx];
        const better = entry.h < old.h || (entry.h === old.h && entry.t < old.t);
        if (better) day.entries[idx] = entry; // overwrite-if-better
      } else {
        if (day.entries.length >= MAX_ENTRIES) {
          res.status(429).json({ error: "board full for today" });
          return;
        }
        day.entries.push(entry);
      }
      sortEntries(day.entries);
      await writeDay(date, day);
      res.status(200).json({
        ok: true,
        rank: day.entries.findIndex(function (e) { return e.n === name; }) + 1,
        total: day.entries.length,
      });
      return;
    }

    res.setHeader("Allow", "GET, POST");
    res.status(405).json({ error: "method not allowed" });
  } catch (err) {
    res.status(502).json({ error: "storage error" });
  }
};
