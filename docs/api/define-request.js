// Definition-request queue for the milon: readers ask for clue phrasings we
// don't cover yet ("עיר בהולנד"), and the weekly drain run turns the queue
// into /milon/d/ pages (app/drain_requests.py + CLAUDE.md rules).
//
// Same zero-dependency Vercel-Blob pattern as leaderboard.js: one JSON
// snapshot blob, read-modify-write, last-writer-wins - fine at this scale.
// POST {q}            add a request (counted, deduped by normalized text)
// GET                 list the queue (public - it is just search phrases)
// POST {resolve:[..]} remove fulfilled phrases (the drain run calls this;
//                     no auth by design: worst case a prankster clears
//                     pending requests, which only delays them)

"use strict";

const BLOB_API = "https://blob.vercel-storage.com";
const PATH_PREFIX = "defreq/";
const MAX_QUEUE = 500;
const MAX_LEN = 60;

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

function normQuery(raw) {
  if (typeof raw !== "string") return null;
  const q = raw
    .replace(/[\u0000-\u001f\u007f<>\\]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, MAX_LEN);
  // must contain Hebrew - the milon is Hebrew-only
  if (!/[א-ת]{2}/.test(q)) return null;
  return q;
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
  if (!origin) return true; // CLI drain runs and same-origin GETs carry no Origin
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
      const items = Object.keys(state.items).map(function (q) {
        return { q: q, count: state.items[q].c, first: state.items[q].at };
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
          const q = normQuery(raw);
          if (q && state.items[q]) { delete state.items[q]; removed++; }
        });
        if (removed) await writeQueue(state);
        res.status(200).json({ ok: true, removed: removed });
        return;
      }

      const q = normQuery(body.q);
      if (!q) {
        res.status(400).json({ error: "q must be Hebrew text up to 60 chars" });
        return;
      }
      const state = await readQueue();
      if (state.items[q]) {
        state.items[q].c += 1;
      } else {
        if (Object.keys(state.items).length >= MAX_QUEUE) {
          res.status(429).json({ error: "queue full" });
          return;
        }
        state.items[q] = { c: 1, at: Date.now() };
      }
      await writeQueue(state);
      res.status(200).json({ ok: true, count: state.items[q].c });
      return;
    }

    res.setHeader("Allow", "GET, POST");
    res.status(405).json({ error: "method not allowed" });
  } catch (err) {
    res.status(502).json({ error: "storage error" });
  }
};
