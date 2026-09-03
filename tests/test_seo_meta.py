"""Letter-page title/description copy.

Grounded in a SERP read of the letter shape (2026-09-03). For
"עיר בישראל באות ד" not one of the ten organic results is a crossword site:
the winners are ארץ עיר game answer lists (yo-yoo, kids-games, lamakama),
plain settlement lists (zips.co.il, zoharatights, hebrew-academy) and
Wikipedia categories. Their titles promise a LIST ("הרשימה המלאה",
"רשימת שמות היישובים") and their snippets NAME the entries. Our letter pages
promised "תשובות לתשבץ ותשחץ" and named none, and took 0 impressions in the
17 days after they shipped.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))

from seo_meta import letter_title, letter_meta

CITY = 'ערים ויישובים בישראל'
DALET = ['דבורייה', 'דהמש', 'דורא', 'דימונה', 'דיר אל-אסד', 'דיר חנא']


class LetterTitle(unittest.TestCase):
    def test_names_the_category_and_the_letter(self):
        t = letter_title(CITY, 'ד', 9)
        self.assertIn(CITY, t)
        self.assertIn('באות ד', t)

    def test_promises_a_list_not_crossword_answers(self):
        # the SERP vocabulary is "רשימה", not "תשבץ/תשחץ"
        t = letter_title(CITY, 'ד', 9)
        self.assertIn('הרשימה המלאה', t)
        self.assertNotIn('תשבץ', t)
        self.assertNotIn('תשחץ', t)

    def test_carries_the_count(self):
        self.assertIn('9', letter_title(CITY, 'ד', 9))

    def test_fits_a_serp_title(self):
        self.assertLessEqual(len(letter_title(CITY, 'ד', 9)), 60)


class LetterMeta(unittest.TestCase):
    def test_names_actual_entries(self):
        m = letter_meta(CITY, 'ד', DALET, 9)
        self.assertIn('דבורייה', m)
        self.assertIn('דימונה', m)

    def test_is_unique_per_page(self):
        a = letter_meta(CITY, 'ד', DALET, 9)
        b = letter_meta(CITY, 'ח', ['חיפה', 'חדרה', 'חולון', 'חצור'], 4)
        self.assertNotEqual(a, b)

    def test_fits_a_serp_snippet(self):
        # Google truncates around 155 chars; a long category plus many names
        # is the case that overflows, so check the worst one we ship.
        long_names = ['מעלה אדומים', 'מבשרת ציון', 'מגדל העמק', 'מזכרת בתיה',
                      'מטולה', 'מיתר', 'מכבים רעות', 'מנחמיה']
        m = letter_meta('ערים ויישובים בישראל', 'מ', long_names, 40)
        self.assertLessEqual(len(m), 155)

    def test_never_truncates_a_name_mid_word(self):
        long_names = ['מעלה אדומים', 'מבשרת ציון', 'מגדל העמק', 'מזכרת בתיה',
                      'מטולה', 'מיתר', 'מכבים רעות', 'מנחמיה']
        m = letter_meta('ערים ויישובים בישראל', 'מ', long_names, 40)
        for name in long_names:
            head = name.split()[0]
            if head in m:
                self.assertIn(name, m, f'{name!r} appears cut short in {m!r}')

    def test_publishes_no_em_dash(self):
        m = letter_meta(CITY, 'ד', ['דיר אל—אסד', 'דימונה'], 9)
        self.assertNotIn('—', m)

    def test_survives_a_single_entry(self):
        m = letter_meta(CITY, 'ד', ['דימונה'], 1)
        self.assertIn('דימונה', m)
        self.assertLessEqual(len(m), 155)


if __name__ == '__main__':
    unittest.main()
