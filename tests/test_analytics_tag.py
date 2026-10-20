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
SAMPLE = ["docs/index.html", "docs/milon/index.html", "docs/nativ/index.html",
          "docs/tirgul/index.html", "docs/nosim/index.html"]


class AnalyticsTag(unittest.TestCase):
    def test_brand_head_carries_the_tag(self):
        import sys; sys.path.insert(0, os.path.join(ROOT, "app"))
        import brand
        self.assertIn(GA, brand.HEAD)
        self.assertIn("googletagmanager.com/gtag/js?id=" + GA, brand.HEAD)

    def test_built_pages_carry_the_tag(self):
        for rel in SAMPLE:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            with self.subTest(page=rel):
                self.assertIn(GA, open(p, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
