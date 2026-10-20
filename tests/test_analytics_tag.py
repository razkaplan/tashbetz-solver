"""Every generated page carries the shared GA4 tag.

The 2026-09-01 redesign replaced the page templates and dropped the tag from
everything except /solve/, so GA reported 3 sessions for a site Search
Console was showing 200 impressions a day. The tag lives in brand.HEAD so
that all three generators (milon, trainer, topic boards) emit it.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA = "G-V7LGK8CMHQ"
CLARITY = "clarity.ms/tag/"
CLARITY_ID = "z0mh7paigf"
SAMPLE = ["docs/index.html", "docs/milon/index.html", "docs/nativ/index.html",
          "docs/tirgul/index.html", "docs/nosim/index.html", "docs/solve/index.html",
          "docs/research/index.html", "docs/milon/city_il-6/index.html"]


class AnalyticsTag(unittest.TestCase):
    def test_brand_head_carries_the_tag(self):
        import sys; sys.path.insert(0, os.path.join(ROOT, "app"))
        import brand
        self.assertIn(GA, brand.HEAD)
        self.assertIn("googletagmanager.com/gtag/js?id=" + GA, brand.HEAD)

    def test_brand_head_carries_clarity(self):
        import sys; sys.path.insert(0, os.path.join(ROOT, "app"))
        import brand
        self.assertIn(CLARITY, brand.HEAD)
        self.assertIn(CLARITY_ID, brand.HEAD)
        self.assertIn('clarity("set","traffic","ai-assistant")', brand.HEAD)

    def test_built_pages_carry_clarity_once(self):
        for rel in SAMPLE:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            with self.subTest(page=rel):
                html = open(p, encoding="utf-8").read()
                self.assertEqual(html.count(CLARITY_ID), 1)

    def test_csp_allows_clarity(self):
        import json
        cfg = json.load(open(os.path.join(ROOT, "docs", "vercel.json"), encoding="utf-8"))
        csp = next(h["value"] for rule in cfg["headers"] for h in rule["headers"] if h["key"] == "Content-Security-Policy")
        script = [d for d in csp.split(";") if d.strip().startswith("script-src")][0]
        connect = [d for d in csp.split(";") if d.strip().startswith("connect-src")][0]
        self.assertIn("https://www.clarity.ms", script)
        self.assertIn("https://*.clarity.ms", connect)

    def test_built_pages_carry_the_tag(self):
        for rel in SAMPLE:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            with self.subTest(page=rel):
                self.assertIn(GA, open(p, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
