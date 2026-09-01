#!/usr/bin/env python3
"""The site shell shared by every generated page: fonts, stylesheet, logo,
header with the main navigation, page head, the נתיב promo strip, footer.

Every generator (build_seo.py, build_defs.py, build_topics.py,
build_trainer.py) imports this instead of carrying its own <style> block, so
a brand change is one edit here plus a rebuild (or, for the milon pages that
need the gitignored corpus to rebuild, one run of app/rebrand_pages.py, which
rewrites the shell of already-generated pages with the very same functions).

The stylesheet itself lives in docs/assets/brand.css.
"""
import html as _html

BASE = 'https://tashbetz.gtmascode.dev'

FONTS = ('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700'
         '&family=Rubik:wght@400;500;700&display=swap')

# Goes in <head>: favicon, fonts, the shared stylesheet.
HEAD = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="{FONTS}" rel="stylesheet">'
        '<link rel="stylesheet" href="/assets/brand.css">')

LOGO_SVG = ('<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
            '<rect x="1" y="1" width="30" height="30" rx="8" fill="currentColor"/>'
            '<rect x="5" y="5" width="10" height="10" rx="2.5" fill="var(--paper)"/>'
            '<rect x="17" y="5" width="10" height="10" rx="2.5" fill="var(--paper)"/>'
            '<rect x="5" y="17" width="10" height="10" rx="2.5" fill="var(--pop)"/>'
            '<rect x="17" y="17" width="10" height="10" rx="2.5" fill="var(--sun)"/></svg>')

WORDMARK = f'<a class="logo" href="/">{LOGO_SVG}<span>תשבץ<i>.</i>היגיון</span></a>'

# (href, label, key). `key` is what site_header(current=...) highlights.
NAV = [('/solve/', '🧩 האפליקציה', 'solve'),
       ('/nosim/', '🎓 תשבצי נושא', 'nosim'),
       ('/tirgul/', '🏋️ תרגול', 'tirgul'),
       ('/milon/', '📖 מילון', 'milon'),
       ('/methods/', '🔍 שיטות', 'methods')]

PROMO = ('<div class="promo"><span class="promo-ic">☀️</span><span>'
         '<a href="/nativ/"><b>נתיב</b>, המשחק היומי הטוב לחובבי תשבצים</a>'
         ' · חידה חדשה כל יום, עכשיו גם במצב קל</span></div>')

MILON_KICKER = '📖 מילון תשבץ · פותרים ביחד'
MILON_NOTE = ('מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) '
              'וניתוח סטטיסטי מקורי. לא מתפרסמות הגדרות מעיתונים. '
              '<a href="https://www.linkedin.com/in/razkaplan/" rel="me">פרויקט של רז קפלן</a>.')
DEFS_KICKER = '📖 מילון תשבץ · הגדרות נפוצות'
DEFS_NOTE = ('מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) '
             'ורשימות שנאספו ידנית. לא מתפרסמות הגדרות מעיתונים. '
             '<a href="https://www.linkedin.com/in/razkaplan/" rel="me">פרויקט של רז קפלן</a>.')

FOOT_NOTE_DEFAULT = ('לא מתפרסמות הגדרות מעיתונים. '
                     '<a href="https://www.linkedin.com/in/razkaplan/" rel="me">פרויקט של רז קפלן</a>.')


def esc(s):
    return _html.escape(str(s), quote=True)


def site_header(current=None):
    links = ''.join(
        f'<a href="{h}"{cls}>{l}</a>'
        for h, l, k in NAV for cls in [' class="on"' if k == current else ''])
    cta = ('<a class="btn sun sm cta" href="/nativ/">☀️ נתיב היומי</a>' if current != 'nativ'
           else '<a class="btn sun sm cta" href="/nativ/">☀️ משחקים</a>')
    return (f'<header class="site-head"><div class="site-in">{WORDMARK}'
            f'<nav class="site-nav" aria-label="ניווט ראשי">{links}</nav>{cta}</div></header>')


def crumbs_html(crumbs):
    """crumbs: [(label, href), ...]; the last one is the current page (no link)."""
    if not crumbs:
        return ''
    parts = [f'<a href="{h}">{esc(l)}</a>' for l, h in crumbs[:-1]]
    parts.append(f'<span>{esc(crumbs[-1][0])}</span>')
    return f'<nav class="crumb" aria-label="מיקום באתר">{"".join(parts)}</nav>'


def page_head(kicker, title, crumbs=(), kicker_class='', promo=True, title_html=None):
    kc = f'kicker {kicker_class}'.strip()
    h1 = title_html if title_html is not None else esc(title)
    return (f'<div class="pagehead"><span class="{kc}">{esc(kicker)}</span>'
            f'<h1>{h1}</h1>{crumbs_html(crumbs)}</div>' + (PROMO if promo else ''))


def site_footer(note=''):
    note = note or FOOT_NOTE_DEFAULT
    return f"""<footer class="site-foot"><div class="site-in">
<div class="foot-brand">{WORDMARK}<p>משחקי מילים חכמים בעברית: משחק יומי, תשבצי נושא, מילון ענק ועוזר פתירה שמוכיח כל תשובה.</p></div>
<div class="foot-col"><b>לשחק</b><a href="/nativ/">☀️ נתיב, המשחק היומי</a><a href="/nosim/">תשבצי נושא</a><a href="/tirgul/">תשבצי אימון</a><a href="/bakasha/">בקשת תשבץ אישי</a></div>
<div class="foot-col"><b>לפתור</b><a href="/solve/">עוזר הפתירה</a><a href="/milon/">מילון תשבץ</a><a href="/milon/anagram/">חיפוש אנגרם</a><a href="/milon/d/">הגדרות נפוצות</a><a href="/methods/">שיטות פתרון</a></div>
<div class="foot-col"><b>הפרויקט</b><a href="/research/he/">המחקר</a><a href="/research/">Research (English)</a><a href="https://github.com/razkaplan/tashbetz-solver">קוד פתוח ב-GitHub</a><a href="https://github.com/razkaplan/tashbetz-solver/tree/main/skills/tashbetz-solver">להתקין כ-Skill</a><a href="https://www.linkedin.com/in/razkaplan/" rel="me">רז קפלן</a></div>
<p class="foot-note">{note}</p>
</div></footer>"""


def document(*, title, desc, canonical, meta='', style='', kicker, h1=None, crumbs=(),
             body, note='', current=None, kicker_class='', promo=True, wide=False,
             title_html=None, lang='he'):
    """A complete generated page. `meta` is the caller's og/twitter/ld+json
    block, `style` its page-specific <style> (may be empty)."""
    h1 = title if h1 is None else h1
    w = 'w w-wide' if wide else 'w'
    return (f'<!doctype html><html lang="{lang}" dir="rtl"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>\n'
            f'<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">'
            f'{meta}{HEAD}{style}</head><body>\n{site_header(current)}\n<main class="{w}">\n'
            f'{page_head(kicker, h1, crumbs, kicker_class, promo, title_html)}\n{body}\n</main>\n'
            f'{site_footer(note)}</body></html>')
