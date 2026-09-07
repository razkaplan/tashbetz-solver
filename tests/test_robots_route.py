"""robots.txt must be served by docs/api/robots.js, never by a static file.

Vercel resolves the filesystem before rewrites, so a committed docs/robots.txt
silently shadows the route and the crawler log goes dark. That is exactly what
happened between 2026-08-29 and 2026-09-07. These tests pin the three things
that keep the route alive, and exercise the handler itself through node.
"""
import json
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

NODE_SMOKE = r"""
const h = require(process.argv[1]);
const res = { h: {}, code: 0, body: "", setHeader(k, v) { this.h[k] = v; },
              status(c) { this.code = c; return this; }, send(b) { this.body = b; } };
const req = { headers: { "user-agent": process.argv[2] }, url: "/robots.txt" };
h(req, res).then(() => console.log(JSON.stringify({ code: res.code, cache: res.h["Cache-Control"], body: res.body })));
"""


class RobotsRoute(unittest.TestCase):
    def test_no_static_robots_txt_is_committed(self):
        self.assertFalse(os.path.exists(os.path.join(DOCS, "robots.txt")),
                         "docs/robots.txt exists and would shadow /api/robots")

    def test_build_seo_does_not_write_robots_txt(self):
        src = open(os.path.join(ROOT, "app", "build_seo.py"), encoding="utf-8").read()
        self.assertNotIn("open('docs/robots.txt'", src)
        self.assertNotIn('open("docs/robots.txt"', src)

    def test_vercel_rewrites_robots_to_the_function(self):
        cfg = json.load(open(os.path.join(DOCS, "vercel.json"), encoding="utf-8"))
        self.assertIn({"source": "/robots.txt", "destination": "/api/robots"}, cfg.get("rewrites", []))

    def test_handler_answers_200_no_store_without_a_blob_token(self):
        env = {k: v for k, v in os.environ.items() if k != "BLOB_READ_WRITE_TOKEN"}
        out = subprocess.run(["node", "-e", NODE_SMOKE, os.path.join(DOCS, "api", "robots.js"),
                              "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"],
                             capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        r = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(r["code"], 200)
        self.assertEqual(r["cache"], "no-store")
        self.assertIn("Sitemap: https://tashbetz.gtmascode.dev/sitemap.xml", r["body"])
        self.assertIn("User-agent: *", r["body"])


if __name__ == "__main__":
    unittest.main()
