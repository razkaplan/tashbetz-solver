"""SERP-facing copy for the milon category-letter pages.

Why this is a module and not an f-string inside build_seo.py: the copy is a
measured bet, so it needs a test that fails when someone reverts it.

The bet (SERP read 2026-09-03, query "עיר בישראל באות ד"): not one of the ten
organic results is a crossword site. The winners are ארץ עיר game answer lists
(yo-yoo, kids-games, lamakama), plain settlement lists (zips.co.il,
zoharatights, hebrew-academy) and Wikipedia categories. Two things are true of
all of them and were true of none of our letter pages:

  1. the title promises a LIST ("הרשימה המלאה", "רשימת שמות היישובים"),
     not crossword answers
  2. the snippet NAMES entries ("דאלית אל-כרמל דבורה דבוריה דבירה")

Ours said "תשובות לתשבץ ותשחץ" and named nobody, and every one of the 262
pages carried the same sentence with only the letter and the count swapped.
They took 0 impressions in the 17 days after they shipped while length pages
fielded the letter queries at position 38-83.
"""

# Google truncates a description around 155 characters.
SNIPPET_LIMIT = 155
# and a title around 60.
TITLE_LIMIT = 60

_TAIL = '. עם מספר האותיות של כל שם.'
_TAIL_MORE = ' ועוד' + _TAIL


def _clean(s):
    """No em-dashes are published by this project, including from source data."""
    return ' '.join((s or '').replace('—', '-').replace('–', '-').split())


def letter_title(plural, ch, count):
    """'ערים ויישובים בישראל באות ד: הרשימה המלאה (9 שמות)'"""
    stem = f'{_clean(plural)} באות {ch}: הרשימה המלאה'
    full = f'{stem} ({count} שמות)'
    return full if len(full) <= TITLE_LIMIT else stem


def letter_meta(plural, ch, names, count):
    """A snippet that names entries, the way every winning result does.

    Names are added whole and greedily until the next one would push the
    description past what Google will show. A name is never cut in half: a
    half-name in a snippet reads as broken data, which is worse than a
    shorter list.
    """
    plural = _clean(plural)
    names = [_clean(n) for n in names if _clean(n)]
    head = f'{count} {plural} שמתחילים באות {ch}: '
    if not names:
        return (head[:-2] + _TAIL).strip()

    picked = []
    for i, name in enumerate(names):
        tail = _TAIL if i == len(names) - 1 else _TAIL_MORE
        if len(head + ', '.join(picked + [name]) + tail) > SNIPPET_LIMIT:
            break
        picked.append(name)
    if not picked:                      # one very long name: ship it anyway
        picked = [names[0]]

    tail = _TAIL if len(picked) == len(names) else _TAIL_MORE
    return head + ', '.join(picked) + tail
