"""The shipped letter pages, not just the function that writes their copy.

docs/ is committed, so it can drift from the generator: a rebuild with an old
app/ would quietly put the crossword-framed titles back. These assertions read
the HTML that actually deploys.
"""
import glob
import html
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = sorted(glob.glob(os.path.join(ROOT, 'docs/milon/*-letter-*/index.html')))

TITLE = re.compile(r'<title>(.*?)</title>', re.S)
DESC = re.compile(r'<meta name="description" content="(.*?)"', re.S)
H1 = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)


def _meta(path):
    with open(path, encoding='utf-8') as fh:
        s = fh.read()
    return (html.unescape(TITLE.search(s).group(1)),
            html.unescape(DESC.search(s).group(1)),
            html.unescape(H1.search(s).group(1)))


class BuiltLetterPages(unittest.TestCase):
    def test_there_are_letter_pages(self):
        self.assertGreater(len(PAGES), 200, 'letter pages missing from docs/')

    def test_titles_promise_a_list_and_fit(self):
        for p in PAGES:
            t, _, _ = _meta(p)
            with self.subTest(page=os.path.relpath(p, ROOT)):
                self.assertIn('הרשימה המלאה', t)
                self.assertNotIn('תשבץ', t)
                self.assertNotIn('תשחץ', t)
                self.assertLessEqual(len(t), 60)

    def test_h1_matches_title(self):
        for p in PAGES:
            t, _, h = _meta(p)
            with self.subTest(page=os.path.relpath(p, ROOT)):
                self.assertEqual(t, h)

    def test_descriptions_name_entries_and_fit(self):
        for p in PAGES:
            _, d, _ = _meta(p)
            with self.subTest(page=os.path.relpath(p, ROOT)):
                self.assertLessEqual(len(d), 155)
                self.assertIn(': ', d)
                listed = d.split(': ', 1)[1].split(' ועוד')[0].split('. עם')[0]
                self.assertTrue(listed.strip(), 'description names no entry')

    def test_descriptions_are_unique(self):
        seen = [_meta(p)[1] for p in PAGES]
        self.assertEqual(len(set(seen)), len(seen), 'duplicate descriptions')

    def test_titles_and_descriptions_publish_no_em_dash(self):
        for p in PAGES:
            t, d, _ = _meta(p)
            with self.subTest(page=os.path.relpath(p, ROOT)):
                self.assertNotIn('—', t + d)
                self.assertNotIn('–', t + d)


if __name__ == '__main__':
    unittest.main()
