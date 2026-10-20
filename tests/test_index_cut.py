"""Entity and word pages stay live but leave Google's index.

Google crawled the 5,400 /milon/e/ and /milon/w/ pages once (Aug 9-11),
trialled 639 of them for a week at positions 25-58 (0.9% CTR), then dropped
the whole host on 2026-09-01, homepage included, and has not crawled it
since. 89% of the sitemap was template pages with ~440 unique characters.

So those pages keep serving readers and the internal link graph, but carry
noindex,follow and are not in the sitemap. Hubs, length and letter lists,
the games and the trainer stay indexable.
"""
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOINDEX = '<meta name="robots" content="noindex, follow">'


def read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


class IndexCut(unittest.TestCase):
    def test_sitemap_has_no_entity_or_word_pages(self):
        locs = re.findall(r"<loc>([^<]+)</loc>", read("docs/sitemap.xml"))
        cut = [u for u in locs if "/milon/e/" in u or "/milon/w/" in u]
        self.assertEqual(cut, [], f"{len(cut)} entity/word pages still in the sitemap")
        self.assertTrue(any(u.endswith("/milon/") for u in locs))
        self.assertTrue(any("-letter-" in u for u in locs))
        self.assertTrue(any("/tirgul/" in u for u in locs))
        self.assertLess(len(locs), 800)

    def test_entity_and_word_pages_carry_noindex_follow(self):
        for d in ("docs/milon/e", "docs/milon/w"):
            names = sorted(os.listdir(os.path.join(ROOT, d)))[:200]
            for n in names:
                p = os.path.join(d, n, "index.html")
                if not os.path.exists(os.path.join(ROOT, p)):
                    continue
                with self.subTest(page=p):
                    self.assertIn(NOINDEX, read(p))

    def test_hubs_and_lists_do_not(self):
        for p in ("docs/index.html", "docs/milon/index.html", "docs/milon/city_il-6/index.html",
                  "docs/nativ/index.html", "docs/tirgul/index.html"):
            with self.subTest(page=p):
                self.assertNotIn('name="robots"', read(p))

    def test_generator_emits_noindex_for_entity_pages(self):
        src = read("app/build_seo.py")
        self.assertIn("noindex", src)
        self.assertRegex(src, r"def page\([^)]*noindex")

    def test_url_guard_accepts_the_cut_by_prefix(self):
        out = subprocess.run(["python3", "app/url_guard.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
