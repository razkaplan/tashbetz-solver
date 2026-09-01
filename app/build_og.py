#!/usr/bin/env python3
"""Render the social cards (og.png, 1200x630) in the site brand.

Each card is a small HTML page laid out with the brand tokens and rendered
with headless Chromium. Fonts come from Google Fonts when the renderer has
network, or from a local @font-face sheet passed as FONT_CSS (the path of a
css file whose url()s are absolute).

Usage: python3 app/build_og.py            # writes every card under docs/
       CHROME=/path/to/chrome FONT_CSS=fonts.css python3 app/build_og.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, 'app')
import brand  # noqa: E402

CARDS = {
    'docs/og.png': dict(
        emoji='🧩', kicker='חכם. מהנה. בעברית.', title='תשבץ<i>.</i>היגיון',
        sub='משחק יומי, תשבצי נושא, מילון ענק ועוזר פתירה שמוכיח כל תשובה',
        tiles='תשבץ', color='#6C4CF6', tint='#E5DEFF'),
    'docs/solve/og.png': dict(
        emoji='🧩', kicker='פותרים ביחד', title='עוזר תשבץ היגיון',
        sub='מנוע שפותר איתך, לא במקומך: רמזים מדורגים והוכחה מכנית לכל תשובה',
        tiles='מוכח', color='#6C4CF6', tint='#E5DEFF'),
    'docs/nativ/og.png': dict(
        emoji='☀️', kicker='המשחק היומי', title='נתיב<i>.</i>',
        sub='גוררים מסלול בין האותיות ומגלים את מילות היום. חדש כל יום, בחינם',
        tiles='נתיב', color='#FFC83D', tint='#FFF1C4'),
    'docs/milon/og.png': dict(
        emoji='📖', kicker='מילון תשבץ', title='מילון תשבצאים',
        sub='22 אלף שמות וביטויים לפי אורך, אות פותחת, תבנית ואנגרם',
        tiles='מילה', color='#17B890', tint='#D7F5EA'),
    'docs/tirgul/og.png': dict(
        emoji='🏋️', kicker='תרגול תשבץ', title='תשבצי אימון',
        sub='מאה תשבצים לפי רמה, וכל תשובה מגיעה עם ההוכחה שלה',
        tiles='אמון', color='#FF5E5B', tint='#FFE0DE'),
}

HTML = '''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
{fonts}
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FFFBF3 radial-gradient(#E8E2D4 1.5px,transparent 1.5px);background-size:28px 28px;color:#1B1A4E;
  font-family:'Rubik','Heebo',sans-serif;position:relative}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:16px;background:{color}}}
.logo{{position:absolute;top:44px;right:64px;display:flex;align-items:center;gap:14px;font-family:'Fredoka',sans-serif;font-weight:700;font-size:36px}}
.logo svg{{width:52px;height:52px}} .logo i{{font-style:normal;color:#FF5E5B}}
.txt{{position:absolute;top:150px;right:64px;width:660px}}
.kicker{{display:inline-block;background:{color};color:{kcolor};font-weight:700;font-size:22px;padding:6px 22px;border-radius:999px;border:3px solid #1B1A4E;box-shadow:4px 4px 0 #1B1A4E}}
h1{{font-family:'Fredoka',sans-serif;font-weight:700;font-size:88px;line-height:1.05;margin-top:26px;letter-spacing:-.01em}}
h1 i{{font-style:normal;color:#FF5E5B}}
.sub{{font-size:30px;line-height:1.35;color:#5B5A8A;margin-top:18px}}
.stage{{position:absolute;left:72px;top:118px;width:360px}}
.grid{{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;background:#1B1A4E;border:6px solid #1B1A4E;border-radius:26px;padding:8px;transform:rotate(-4deg);box-shadow:12px 12px 0 {color};direction:rtl}}
.grid div{{aspect-ratio:1;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;font-family:'Fredoka',sans-serif;font-weight:700;font-size:52px}}
.grid .b{{background:#0B0A20}} .grid .t{{background:{tint}}} .grid .h{{background:{color};color:{kcolor}}}
.sticker{{position:absolute;background:#FF5E5B;color:#fff;font-family:'Fredoka',sans-serif;font-weight:700;font-size:30px;padding:8px 26px;border-radius:999px;border:3px solid #1B1A4E;box-shadow:4px 4px 0 #1B1A4E;transform:rotate(-8deg);top:-30px;left:-22px;z-index:2}}
.emoji{{position:absolute;bottom:60px;left:80px;font-size:64px}}
</style></head><body>
<div class="logo">{logo}<span>תשבץ<i>.</i>היגיון</span></div>
<div class="txt"><span class="kicker">{kicker}</span><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="stage"><span class="sticker">{emoji} {stick}</span><div class="grid">{cells}</div></div>
<div class="bar"></div>
</body></html>'''

LAYOUT = ['t', 'W0', 'b', 'W1', 'W2', 'W3', 't', '', '', 'b', '', 't', '', 't', 'b', '']  # 4x4, W = word letter


def cells_for(word):
    out = []
    for cell in LAYOUT:
        if cell.startswith('W'):
            out.append(f'<div class="h">{word[int(cell[1])]}</div>')
        elif cell == 'b':
            out.append('<div class="b"></div>')
        elif cell == 't':
            out.append('<div class="t"></div>')
        else:
            out.append('<div></div>')
    return ''.join(out)


def main():
    chrome = os.environ.get('CHROME') or shutil.which('chromium') or shutil.which('google-chrome') \
        or '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    font_css = os.environ.get('FONT_CSS')
    fonts = (f'<style>{open(font_css).read()}</style>' if font_css
             else f'<link href="{brand.FONTS}" rel="stylesheet">')
    logo = brand.LOGO_SVG.replace('currentColor', '#1B1A4E').replace('var(--paper)', '#FFFBF3') \
        .replace('var(--pop)', '#FF5E5B').replace('var(--sun)', '#FFC83D')
    tmp = tempfile.mkdtemp(prefix='og-')
    for out, c in CARDS.items():
        dark_text = c['color'] in ('#FFC83D',)
        html = HTML.format(fonts=fonts, logo=logo, cells=cells_for(c['tiles']),
                           kcolor='#1B1A4E' if dark_text else '#fff',
                           stick={'☀️': 'חדש כל יום', '📖': '22K ערכים', '🏋️': '100 לוחות'}.get(c['emoji'], 'מוכח ✓'),
                           **c)
        src = os.path.join(tmp, os.path.basename(os.path.dirname(out) or 'home') + '.html')
        open(src, 'w', encoding='utf-8').write(html)
        dst = os.path.abspath(out)
        subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                        '--allow-file-access-from-files', '--force-device-scale-factor=1',
                        '--window-size=1200,630', '--virtual-time-budget=3000',
                        f'--screenshot={dst}', 'file://' + src],
                       check=True, capture_output=True, timeout=120)
        print(out, os.path.getsize(dst))


if __name__ == '__main__':
    main()
