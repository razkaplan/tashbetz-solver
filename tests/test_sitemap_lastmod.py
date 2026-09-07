"""The sitemap must tell Google WHEN each page last changed.

Measured 2026-09-07 with the Search Console URL Inspection API: every sampled
tashbetz page is "Crawled - currently not indexed" and Googlebot's last crawl
of this host was 2026-08-11. Five deploys have shipped since then (the letter
link graph, entity sense priority, the letter page copy) and Google has seen
none of them. All 6,071 <url> entries carried a <loc> and nothing else, so the
sitemap offered no way to tell which URLs had changed.

lastmod is only useful if it is TRUE, so these tests check trustworthiness, not
just presence: dates come from the git history of the built file, they are real
ISO dates, and they are not in the future.
"""
import datetime
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, 'docs', 'sitemap.xml')
BASE = 'https://tashbetz.gtmascode.dev'

import sys
sys.path.insert(0, os.path.join(ROOT, 'app'))
import sitemap_lastmod as sl


def sitemap():
    with open(SITEMAP, encoding='utf-8') as f:
        return f.read()


def entries():
    return re.findall(r'<url>(.*?)</url>', sitemap(), flags=re.S)


class TestSitemapShape(unittest.TestCase):
    def test_every_url_has_a_lastmod(self):
        missing = [e for e in entries() if '<lastmod>' not in e]
        self.assertEqual(
            [], missing[:5],
            f'{len(missing)} of {len(entries())} <url> entries carry no <lastmod>')

    def test_every_lastmod_is_a_real_iso_date(self):
        bad = []
        for e in entries():
            m = re.search(r'<lastmod>([^<]*)</lastmod>', e)
            if not m:
                continue
            try:
                datetime.date.fromisoformat(m.group(1))
            except ValueError:
                bad.append(m.group(1))
        self.assertEqual([], bad[:5], f'{len(bad)} lastmod values are not ISO dates')

    def test_no_lastmod_is_in_the_future(self):
        today = datetime.date.today()
        future = [m for e in entries()
                  for m in re.findall(r'<lastmod>([^<]*)</lastmod>', e)
                  if datetime.date.fromisoformat(m) > today]
        self.assertEqual([], future[:5], f'{len(future)} lastmod values are in the future')

    def test_loc_count_is_unchanged(self):
        """lastmod is an addition. It must not add or drop a single URL."""
        xml = sitemap()
        self.assertEqual(xml.count('<loc>'), xml.count('<url>'))
        self.assertEqual(xml.count('<loc>'), xml.count('<lastmod>'))


class TestLastmodIsTrue(unittest.TestCase):
    """A lastmod Google cannot trust is worse than no lastmod at all."""

    def test_url_maps_to_the_built_file(self):
        self.assertEqual('docs/index.html', sl.page_path('/'))
        self.assertEqual('docs/milon/city_il-3/index.html',
                         sl.page_path('/milon/city_il-3/'))
        self.assertEqual('docs/tirgul/7/index.html', sl.page_path('/tirgul/7/'))

    def test_entity_url_maps_to_the_percent_encoded_directory(self):
        """/milon/e/ keeps the encoded name on disk."""
        self.assertEqual('docs/milon/e/%D7%90%D7%99%D7%9C%D7%AA/index.html',
                         sl.page_path('/milon/e/%D7%90%D7%99%D7%9C%D7%AA/'))

    def test_letter_url_maps_to_the_raw_hebrew_directory(self):
        """The letter pages keep the decoded name, the opposite convention."""
        self.assertEqual('docs/milon/actor-letter-א/index.html',
                         sl.page_path('/milon/actor-letter-%D7%90/'))

    def test_every_sitemap_url_resolves_to_a_file_that_exists(self):
        """A URL that resolves to nothing gets today's date, which is a lie."""
        xml = sitemap()
        locs = re.findall(r'<loc>([^<]*)</loc>', xml)
        missing = [u for u in locs
                   if not os.path.exists(os.path.join(ROOT, sl.page_path(u[len(BASE):])))]
        self.assertEqual([], missing[:5],
                         f'{len(missing)} of {len(locs)} sitemap URLs resolve to no built file')

    def test_date_comes_from_git_not_from_today(self):
        """Seeding every URL with the build date would be a lie."""
        dates = sl.git_dates(['docs/index.html'])
        self.assertIn('docs/index.html', dates)
        self.assertRegex(dates['docs/index.html'], r'^\d{4}-\d{2}-\d{2}$')

    def test_sitemap_dates_are_not_all_the_same_day(self):
        """The corpus was not written in one day, so the dates must vary."""
        vals = {m for e in entries()
                for m in re.findall(r'<lastmod>([^<]*)</lastmod>', e)}
        self.assertGreater(
            len(vals), 1,
            'every lastmod is the same date, which Google will learn to ignore')

    def test_sitemap_dates_match_git_for_a_sample(self):
        xml = sitemap()
        pairs = re.findall(
            r'<url><loc>([^<]*)</loc><lastmod>([^<]*)</lastmod></url>', xml)
        self.assertTrue(pairs, 'sitemap entries are not in the expected shape')
        sample = pairs[:40]
        paths = [sl.page_path(u[len(BASE):]) for u, _ in sample]
        want = sl.git_dates(paths)
        wrong = [(u, got, want.get(p))
                 for (u, got), p in zip(sample, paths)
                 if p in want and want[p] != got]
        self.assertEqual([], wrong[:5],
                         f'{len(wrong)} of {len(sample)} lastmod values disagree with git')

    def test_entry_renders_one_line(self):
        self.assertEqual(
            '  <url><loc>https://x/a/</loc><lastmod>2026-01-02</lastmod></url>\n',
            sl.url_entry('https://x', '/a/', '2026-01-02'))


class TestAppendingWritersStayIdempotent(unittest.TestCase):
    """build_words / build_defs / build_topics rewrite their own slice of the
    sitemap by regex-deleting it and appending a fresh block. Those delete
    patterns matched '<loc>...</loc></url>' exactly, so adding <lastmod> in
    between would stop them matching and every rebuild would DOUBLE their URLs.
    """

    def assert_removes_own_block(self, module, sample_urls):
        """Call the writer twice and require the second run to be a no-op."""
        import importlib, tempfile, contextlib
        m = importlib.import_module(module)
        head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset>\n'
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, 'docs'))
            path = os.path.join(tmp, 'docs', 'sitemap.xml')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(head + '</urlset>')
            cwd = os.getcwd()
            old_root = getattr(m, 'ROOT', None)
            try:
                os.chdir(tmp)
                if old_root is not None:
                    m.ROOT = tmp
                m.update_sitemap(sample_urls)
                with open(path, encoding='utf-8') as f:
                    once = f.read()
                m.update_sitemap(sample_urls)
                with open(path, encoding='utf-8') as f:
                    twice = f.read()
            finally:
                os.chdir(cwd)
                if old_root is not None:
                    m.ROOT = old_root
        self.assertIn('<lastmod>', once, f'{module} emitted no lastmod')
        self.assertEqual(
            len(sample_urls), once.count('<loc>'),
            f'{module} did not write one entry per URL')
        self.assertEqual(
            once, twice,
            f'{module} is not idempotent, so every rebuild duplicates its URLs')

    def test_build_words_removes_its_own_entries(self):
        self.assert_removes_own_block('build_words', ['/milon/w/%D7%A2%D7%A5/'])

    def test_build_defs_removes_its_own_entries(self):
        self.assert_removes_own_block('build_defs', ['/milon/d/%D7%A2%D7%A5/'])

    def test_build_topics_removes_its_own_entries(self):
        self.assert_removes_own_block('build_topics', ['/nosim/x/', '/bakasha/'])


class TestUntrackedFilesFallBackHonestly(unittest.TestCase):
    def test_file_with_no_git_history_falls_back_to_today(self):
        d = sl.dates_for(['docs/__does_not_exist__/index.html'])
        self.assertEqual(datetime.date.today().isoformat(),
                         d['docs/__does_not_exist__/index.html'])

    def test_a_page_the_build_just_rewrote_is_dated_today(self):
        """The rebuild flow: the file changed, the commit has not happened yet."""
        page = 'docs/milon/city_il-3/index.html'
        before = sl.dates_for([page])[page]
        self.assertNotEqual(datetime.date.today().isoformat(), before,
                            'pick a page that is not already dated today')
        original = open(os.path.join(ROOT, page), 'rb').read()
        try:
            with open(os.path.join(ROOT, page), 'ab') as f:
                f.write(b'\n<!-- touched by test -->')
            sl._dirty.cache_clear()
            self.assertEqual(datetime.date.today().isoformat(),
                             sl.dates_for([page])[page])
        finally:
            with open(os.path.join(ROOT, page), 'wb') as f:
                f.write(original)
            sl._dirty.cache_clear()


if __name__ == '__main__':
    unittest.main()
