// Personal-crossword request queue: readers ask for a board on a subject of
// their own ("כיתה ז2", "יום הולדת לסבתא", "מכבי חיפה"), and a weekly drain
// run turns the queue into real puzzles (app/drain_puzzle_requests.py).
//
// Same zero-dependency Vercel-Blob pattern as leaderboard.js and
// define-request.js: one JSON snapshot blob, read-modify-write,
// last-writer-wins - fine at this scale.
//
// POST {topic, level, kind, note}   add a request (counted, deduped by topic)
// GET                               list the queue
// POST {resolve:[..]}               remove the ones that shipped
//
// NOTHING HERE IS PUBLISHED AUTOMATICALLY. The queue is a to-do list that a
// human or an agent reads; a requested board goes live only after the run in
// CLAUDE.md, which reviews the text. That is also why no contact details are
// collected: there is nobody to mail back, and a request is not a form.

"use strict";

const BLOB_API = "https://blob.vercel-storage.com";
const PATH_PREFIX = "pzreq/";
const MAX_QUEUE = 400;
const MAX_TOPIC = 60;
const MAX_NOTE = 200;
const KINDS = ["regular", "arrow", "any"];

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

function clean(raw, max) {
  if (typeof raw !== "string") return "";
  return raw
    .replace(/[\u0000-\u001f\u007f<>\\]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

function normTopic(raw) {
  const t = clean(raw, MAX_TOPIC);
  if (!/[א-ת]{2}/.test(t)) return null;   // the site is Hebrew-only
  return t;
}

async function latestSnapshot() {
  const res = await fetch(
    BLOB_API + "/?prefix=" + encodeURIComponent(PATH_PREFIX) + "&limit=1000",
    { headers: { Authorization: "Bearer " + token() } }
  );
  if (!res.ok) throw new Error("blob list failed: " + res.status);
  const blobs = (await res.json()).blobs || [];
  blobs.sort(function (a, b) { return a.pathname < b.pathname ? -1 : 1; });
  return { latest: blobs[blobs.length - 1], all: blobs.map(function (b) { return b.url; }) };
}

async function readQueue() {
  const snap = await latestSnapshot();
  const state = { items: {}, _old: snap.all };
  if (!snap.latest) return state;
  const get = await fetch(snap.latest.url, { cache: "no-store" });
  if (!get.ok) return state;
  const data = await get.json().catch(function () { return null; });
  if (data && data.items && typeof data.items === "object") state.items = data.items;
  return state;
}

async function writeQueue(state) {
  const path = PATH_PREFIX + String(Date.now()).padStart(14, "0") + ".json";
  const put = await fetch(BLOB_API + "/" + path, {
    method: "PUT",
    headers: {
      Authorization: "Bearer " + token(),
      "x-api-version": "7",
      "x-content-type": "application/json",
      "x-add-random-suffix": "0",
    },
    body: JSON.stringify({ items: state.items }),
  });
  if (!put.ok) throw new Error("blob put failed: " + put.status);
  if (state._old && state._old.length) {
    await fetch(BLOB_API + "/delete", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token(),
        "x-api-version": "7",
        "content-type": "application/json",
      },
      body: JSON.stringify({ urls: state._old }),
    }).catch(function () {});
  }
}

function sameOriginOk(req) {
  const origin = req.headers.origin;
  if (!origin) return true;  // CLI drain runs and same-origin GETs carry no Origin
  const host = req.headers["x-forwarded-host"] || req.headers.host || "";
  try {
    return new URL(origin).host === host;
  } catch (e) {
    return false;
  }
}

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (!token()) {
    res.status(503).json({ error: "storage not configured" });
    return;
  }
  if (!sameOriginOk(req)) {
    res.status(403).json({ error: "forbidden" });
    return;
  }

  try {
    if (req.method === "GET") {
      const state = await readQueue();
      const items = Object.keys(state.items).map(function (t) {
        const v = state.items[t];
        return { topic: t, count: v.c, level: v.lv, kind: v.k, note: v.note, first: v.at };
      });
      items.sort(function (a, b) { return b.count - a.count; });
      res.status(200).json({ total: items.length, items: items });
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

      if (Array.isArray(body.resolve)) {
        const state = await readQueue();
        let removed = 0;
        body.resolve.forEach(function (raw) {
          const t = normTopic(raw);
          if (t && state.items[t]) { delete state.items[t]; removed++; }
        });
        if (removed) await writeQueue(state);
        res.status(200).json({ ok: true, removed: removed });
        return;
      }

      const topic = normTopic(body.topic);
      if (!topic) {
        res.status(400).json({ error: "topic must be Hebrew text up to 60 chars" });
        return;
      }
      let level = parseInt(body.level, 10);
      if (!(level >= 1 && level <= 4)) level = 2;
      const kind = KINDS.indexOf(body.kind) >= 0 ? body.kind : "any";
      const note = clean(body.note, MAX_NOTE);

      const state = await readQueue();
      if (state.items[topic]) {
        state.items[topic].c += 1;
        if (note && !state.items[topic].note) state.items[topic].note = note;
      } else {
        if (Object.keys(state.items).length >= MAX_QUEUE) {
          res.status(429).json({ error: "queue full" });
          return;
        }
        state.items[topic] = { c: 1, lv: level, k: kind, note: note, at: Date.now() };
      }
      await writeQueue(state);
      res.status(200).json({ ok: true, count: state.items[topic].c });
      return;
    }

    res.setHeader("Allow", "GET, POST");
    res.status(405).json({ error: "method not allowed" });
  } catch (err) {
    res.status(502).json({ error: "storage error" });
  }
};
