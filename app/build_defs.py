#!/usr/bin/env python3
"""Clue-shaped milon pages: /milon/d/<slug>/ - one page per common clue text.

The 2026-08 competitor research (marketing_kb/) showed every ranking page in
this niche has the CLUE as its unit ("קיבוץ בצפון", "עיר באיטליה"), while our
pages were category-by-length. These pages target the clue queries directly,
built in the proven shape (answers grouped by letter count, variant-phrase
block, newspapers intro) plus the one thing no competitor has: a one-line
description for every answer.

Two data sources, both COMMITTED (this builder is safe in a fresh clone,
unlike build_seo.py which needs the gitignored corpus):
  docs/milon/entities.json     names + descriptions + rich-page flags
  solver/lex/defs_curated.json closed-list categories competitors win that
                               the scraped datasets don't cover

Rerunnable: overwrites its own pages, rewrites its own sitemap block
(idempotent), and refreshes the hub section between its HTML markers.
"""
import html, json, os, re, urllib.parse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = 'https://tashbetz.gtmascode.dev'
OUT = 'docs/milon/d'
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
norm = lambda s: re.sub(r'[^א-ת]', '', s or '').translate(FIN)
esc = lambda s: html.escape(str(s), quote=True)

E = json.load(open('docs/milon/entities.json', encoding='utf-8'))
CUR = {k: v for k, v in json.load(open('solver/lex/defs_curated.json',
                                       encoding='utf-8')).items() if not k.startswith('_')}

# sanity: never build clue pages from a stripped entities.json (see the
# 2026-08-28 incident in build_seo.py)
assert sum(1 for e in E if e.get('d')) > 5000, \
    'entities.json has almost no descriptions - restore it before building'


def ents(cat, rx=None, ex=None, min_len=2, max_len=12):
    out = []
    for e in E:
        if e['c'] != cat:
            continue
        d = e.get('d') or ''
        if rx and not re.search(rx, d):
            continue
        if ex and re.search(ex, d):
            continue
        n = norm(e['t'])
        if not (min_len <= len(n) <= max_len):
            continue
        out.append({'t': e['t'], 'n': n, 'd': d, 'p': e.get('p', 0)})
    seen, ded = set(), []
    for x in out:
        if x['n'] not in seen:
            seen.add(x['n']); ded.append(x)
    return ded


def curated(key):
    return [{'t': t, 'n': norm(t), 'd': d, 'p': 0}
            for t, d in CUR[key]['items'].items()]


# slug -> (H1 clue phrase, variant phrases, item source, related slugs)
# Ordered by the consensus keyword list in marketing_kb/competitor_keywords.md.
PAGES = {
    'zamar-israeli': ('זמר ישראלי', ['זמר ישראלי תשחץ', 'זמר ישראלי תשבץ', 'שם של זמר ישראלי'],
                      lambda: ents('artist', r'זמר', r'זמרת'), ['zameret-israelit', 'lahaka-israelit', 'shir-arik-einstein']),
    'zameret-israelit': ('זמרת ישראלית', ['זמרת ישראלית תשחץ', 'זמרת ישראלית תשבץ', 'שם של זמרת'],
                         lambda: ents('artist', r'זמרת'), ['zamar-israeli', 'lahaka-israelit']),
    'lahaka-israelit': ('להקה ישראלית', ['להקה ישראלית תשחץ', 'להקת רוק ישראלית', 'שם של להקה'],
                        lambda: ents('artist', r'להקה|הרכב|צמד'), ['zamar-israeli', 'zameret-israelit']),
    'sachkan-israeli': ('שחקן ישראלי', ['שחקן ישראלי תשחץ', 'שחקן ישראלי תשבץ', 'שחקן קולנוע ישראלי', 'שחקן תיאטרון ישראלי'],
                        lambda: ents('actor', r'שחקן', r'שחקנית'), ['sachkanit-israelit', 'zamar-israeli']),
    'sachkanit-israelit': ('שחקנית ישראלית', ['שחקנית ישראלית תשחץ', 'שחקנית קולנוע ישראלית'],
                           lambda: ents('actor', r'שחקנית'), ['sachkan-israeli', 'zameret-israelit']),
    'sofer-israeli': ('סופר ישראלי', ['סופר ישראלי תשחץ', 'סופר ישראלי תשבץ', 'סופר עברי'],
                      lambda: ents('author', r'סופר', r'סופרת'), ['soferet-israelit', 'meshorer-israeli']),
    'soferet-israelit': ('סופרת ישראלית', ['סופרת ישראלית תשחץ', 'סופרת עברייה'],
                         lambda: ents('author', r'סופרת'), ['sofer-israeli', 'meshorer-israeli']),
    'meshorer-israeli': ('משורר ישראלי', ['משורר ישראלי תשחץ', 'משורר עברי', 'שם של משורר'],
                         lambda: ents('author', r'משורר', r'משוררת'), ['sofer-israeli', 'soferet-israelit']),
    'kadur-regel': ('כדורגלן ישראלי', ['כדורגלן ישראלי תשחץ', 'כדורגלן ישראלי תשבץ', 'שחקן כדורגל ישראלי'],
                    lambda: ents('athlete', r'כדורגלן'), ['kadur-sal', 'sportai-israeli']),
    'kadur-sal': ('כדורסלן ישראלי', ['כדורסלן ישראלי תשחץ', 'שחקן כדורסל ישראלי'],
                  lambda: ents('athlete', r'כדורסלן'), ['kadur-regel', 'sportai-israeli']),
    'sportai-israeli': ('ספורטאי ישראלי', ['ספורטאי ישראלי תשחץ', 'ספורטאית ישראלית'],
                        lambda: ents('athlete'), ['kadur-regel', 'kadur-sal']),
    'politikai-israeli': ('פוליטיקאי ישראלי', ['פוליטיקאי ישראלי תשחץ', 'מדינאי ישראלי', 'חבר כנסת'],
                          lambda: ents('politician'), ['rosh-memshala', 'sar-israeli']),
    'rosh-memshala': ('ראש ממשלת ישראל', ['ראש ממשלה ישראלי תשחץ', 'מראשי ממשלת ישראל'],
                      lambda: ents('politician', r'ראש הממשלה|ראש ממשלת'), ['politikai-israeli', 'sar-israeli']),
    'sar-israeli': ('שר בממשלת ישראל', ['שר ישראלי תשחץ', 'שר בממשלה'],
                    lambda: ents('politician', r'\bשר |השר '), ['politikai-israeli', 'rosh-memshala']),
    'medina-africa': ('מדינה באפריקה', ['מדינה באפריקה תשחץ', 'מדינה אפריקאית', 'מדינה באפריקה תשבץ'],
                      lambda: ents('nation', r'אפריק'), ['medina-asia', 'medina-europe', 'nahar-africa']),
    'medina-asia': ('מדינה באסיה', ['מדינה באסיה תשחץ', 'מדינה אסיאתית'],
                    lambda: ents('nation', r'אסיה'), ['medina-africa', 'medina-europe']),
    'medina-europe': ('מדינה באירופה', ['מדינה באירופה תשחץ', 'מדינה אירופית'],
                      lambda: ents('nation', r'אירופ'), ['medina-africa', 'medina-asia', 'ir-italia']),
    'kibbutz-tzafon': ('קיבוץ בצפון', ['קיבוץ בצפון הארץ', 'קיבוץ בצפון תשחץ', 'קיבוץ בגליל', 'קיבוץ ברמת הגולן'],
                       lambda: ents('kibbutz', r'קיבוץ.*(גליל|גולן|צפון|עמק (יזרעאל|הירדן|בית שאן)|כנרת|חולה)'),
                       ['kibbutz-negev', 'moshav-tzafon', 'kibbutz-israel']),
    'kibbutz-negev': ('קיבוץ בנגב', ['קיבוץ בנגב תשחץ', 'קיבוץ בדרום', 'קיבוץ בערבה'],
                      lambda: ents('kibbutz', r'קיבוץ.*(נגב|ערבה|דרום)'), ['kibbutz-tzafon', 'moshav-darom', 'kibbutz-israel']),
    'kibbutz-israel': ('קיבוץ בישראל', ['קיבוץ תשחץ', 'שם של קיבוץ', 'קיבוץ תשבץ'],
                       lambda: ents('kibbutz', r'קיבוץ', r'מושב'), ['kibbutz-tzafon', 'kibbutz-negev', 'moshav-israel']),
    'moshav-tzafon': ('מושב בצפון', ['מושב בצפון תשחץ', 'מושב בגליל', 'מושב ברמת הגולן', 'מושב בעמק'],
                      lambda: ents('kibbutz', r'מושב.*(גליל|גולן|צפון|עמק)'), ['moshav-darom', 'kibbutz-tzafon', 'moshav-israel']),
    'moshav-darom': ('מושב בדרום', ['מושב בדרום תשחץ', 'מושב בנגב', 'מושב בחבל לכיש'],
                     lambda: ents('kibbutz', r'מושב.*(נגב|ערבה|דרום|לכיש)'), ['moshav-tzafon', 'kibbutz-negev', 'moshav-israel']),
    'moshav-israel': ('מושב בישראל', ['מושב תשחץ', 'שם של מושב', 'מושב עובדים'],
                      lambda: ents('kibbutz', r'מושב'), ['moshav-tzafon', 'moshav-darom', 'kibbutz-israel']),
    'shchuna-jerusalem': ('שכונה בירושלים', ['שכונה בירושלים תשחץ', 'שכונה ירושלמית', 'שכונה בבירה'],
                          lambda: ents('neighborhood', r'ירושלים'), ['yishuv-aravi', 'har-israel']),
    'yishuv-aravi': ('יישוב ערבי בישראל', ['יישוב ערבי תשחץ', 'כפר ערבי בישראל', 'עיר ערבית בישראל'],
                     lambda: ents('city_il', r'ערבי|בדואי'), ['shchuna-jerusalem', 'kibbutz-israel']),
    'har-israel': ('הר בישראל', ['הר בישראל תשחץ', 'הר בגליל', 'הר בנגב', 'פסגה בישראל'],
                   lambda: ents('mountain', r'ישראל|גליל|נגב|כרמל|גולן|ירושלים|אילת'), ['kibbutz-tzafon', 'yishuv-aravi']),
    'i-yevani': ('אי יווני', ['אי יווני תשחץ', 'אי ביוון', 'אי בים האגאי'],
                 lambda: ents('island', r'יוון|יווני'), ['ir-italia', 'mitologia-yevanit']),
    'melech-mikrai': ('מלך מקראי', ['מלך מקראי תשחץ', 'מלך בתנ"ך', 'מלך קדום'],
                      lambda: ents('bible', r'מלך'), ['malchei-israel', 'malchei-yehuda', 'dmut-tanach']),
    'dmut-tanach': ('דמות מהתנ"ך', ['דמות מקראית תשחץ', 'דמות תנכית', 'איש מהתנ"ך'],
                    lambda: ents('bible'), ['melech-mikrai', 'parasha-bereshit']),
    'shir-arik-einstein': ('שיר של אריק איינשטיין', ['משירי אריק איינשטיין', 'שיר של אריק איינשטיין תשחץ'],
                           lambda: ents('song', r'אריק איינשטיין'), ['zamar-israeli', 'lahaka-israelit']),
    # curated closed lists
    'yesod-chimi': ('יסוד כימי', ['יסוד כימי תשחץ', 'יסוד כימי תשבץ', 'מתכת יסוד', 'גז אציל'],
                    lambda: curated('chemical_element'), ['ot-yevanit', 'mitologia-yevanit']),
    'ot-yevanit': ('אות יוונית', ['אות יוונית תשחץ', 'אות באלפבית היווני', 'אות יוונית תשבץ'],
                   lambda: curated('greek_letter'), ['yesod-chimi', 'mitologia-yevanit', 'i-yevani']),
    'simanei-nikud': ('מסימני הניקוד', ['סימן ניקוד תשחץ', 'תנועה בעברית', 'מסימני הניקוד תשבץ'],
                      lambda: curated('niqqud'), ['taamei-hamikra', 'ot-yevanit']),
    'avnei-hachoshen': ('מאבני החושן', ['אבן חושן תשחץ', 'מאבני החושן תשבץ', 'אבן יקרה מהחושן'],
                        lambda: curated('choshen_stone'), ['dmut-tanach', 'parasha-shemot']),
    'malchei-israel': ('ממלכי ישראל', ['מלך ישראל תשחץ', 'ממלכי ישראל תשבץ', 'מלך ממלכת ישראל'],
                       lambda: curated('king_israel'), ['malchei-yehuda', 'melech-mikrai', 'dmut-tanach']),
    'malchei-yehuda': ('ממלכי יהודה', ['מלך יהודה תשחץ', 'ממלכי יהודה תשבץ', 'מלך ממלכת יהודה'],
                       lambda: curated('king_judah'), ['malchei-israel', 'melech-mikrai', 'dmut-tanach']),
    'parshanei-mikra': ('מפרשני המקרא', ['פרשן מקרא תשחץ', 'מפרשני התנ"ך', 'פרשן תורה'],
                        lambda: curated('bible_commentator'), ['taamei-hamikra', 'dmut-tanach']),
    'taamei-hamikra': ('מטעמי המקרא', ['טעם מקרא תשחץ', 'מטעמי המקרא תשבץ', 'טעמי נגינה'],
                       lambda: curated('teamim'), ['simanei-nikud', 'parshanei-mikra']),
    'parasha-bereshit': ('פרשה בספר בראשית', ['פרשת שבוע בבראשית', 'פרשה בבראשית תשחץ'],
                         lambda: curated('parasha_bereshit'), ['parasha-shemot', 'dmut-tanach']),
    'parasha-shemot': ('פרשה בספר שמות', ['פרשת שבוע בשמות', 'פרשה בשמות תשחץ'],
                       lambda: curated('parasha_shemot'), ['parasha-bereshit', 'dmut-tanach']),
    'mitologia-yevanit': ('דמות במיתולוגיה היוונית', ['אל במיתולוגיה היוונית', 'אלה יוונייה', 'אל יווני תשחץ',
                                                      'אלת הנקמה במיתולוגיה היוונית', 'אל היין במיתולוגיה היוונית'],
                          lambda: curated('greek_mythology'), ['ot-yevanit', 'i-yevani']),
    'malchin-austri': ('מלחין אוסטרי', ['מלחין אוסטרי תשחץ', 'קומפוזיטור אוסטרי'],
                       lambda: curated('composer_austrian'), ['malchin-germani', 'malchin-tzarfati', 'klei-neshifa']),
    'malchin-germani': ('מלחין גרמני', ['מלחין גרמני תשחץ', 'קומפוזיטור גרמני'],
                        lambda: curated('composer_german'), ['malchin-austri', 'malchin-tzarfati', 'klei-neshifa']),
    'malchin-tzarfati': ('מלחין צרפתי', ['מלחין צרפתי תשחץ', 'קומפוזיטור צרפתי'],
                         lambda: curated('composer_french'), ['malchin-austri', 'malchin-germani', 'klei-neshifa']),
    'klei-neshifa': ('כלי נשיפה', ['כלי נשיפה תשחץ', 'כלי נשיפה מעץ', 'כלי נשיפה ממתכת'],
                     lambda: curated('wind_instrument'), ['malchin-austri', 'zamar-israeli']),
    'ir-italia': ('עיר באיטליה', ['עיר באיטליה תשחץ', 'עיר באיטליה תשבץ', 'עיר נמל באיטליה', 'עיר בצפון איטליה'],
                  lambda: curated('city_italy'), ['nahar-italia', 'medina-europe', 'i-yevani']),
    'nahar-italia': ('נהר באיטליה', ['נהר באיטליה תשחץ', 'נהר באיטליה תשבץ'],
                     lambda: curated('river_italy'), ['ir-italia', 'nahar-africa', 'nahar-russia']),
    'nahar-africa': ('נהר באפריקה', ['נהר באפריקה תשחץ', 'נהר באפריקה תשבץ'],
                     lambda: curated('river_africa'), ['medina-africa', 'nahar-italia', 'nahar-russia']),
    'nahar-russia': ('נהר ברוסיה', ['נהר ברוסיה תשחץ', 'נהר בסיביר'],
                     lambda: curated('river_russia'), ['nahar-italia', 'nahar-africa']),
}

STYLE = """<style>*{box-sizing:border-box}body{margin:0;background:#fff;color:#121212;font-family:'Frank Ruhl Libre','Arial Hebrew',serif;line-height:1.6}
.w{max-width:52rem;margin:0 auto;padding:1rem 1.2rem}header{border-bottom:1px solid #121212;box-shadow:0 3px 0 -1px #121212;padding:.8rem 0}
h1{font-size:1.6rem;margin:.2rem 0}.k{font-family:monospace;font-size:.65rem;letter-spacing:.12em;color:#fff;background:#f22b39;display:inline-block;padding:.12rem .5rem}
a{color:#f22b39}h2{border-bottom:3px solid #f22b39;display:inline-block;font-size:1.1rem;padding-bottom:.1rem}
.crumb{font-size:.8rem;color:#5c5c5c;margin:.6rem 0}
.promo{background:#fff4d6;border:1.5px solid #121212;border-radius:3px;padding:.45rem .7rem;margin:.7rem 0 0;font-size:.9rem}
.promo a{font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.4rem;padding:0;list-style:none}
.grid li{background:#f6f5f3;padding:.35rem .6rem;border-radius:3px}
.grid .net{font-family:monospace;color:#5c5c5c}
.lens{font-size:.9rem}
.vars{background:#f6f5f3;border-radius:3px;padding:.6rem .8rem;font-size:.85rem;color:#5c5c5c;margin-top:1.4rem}
footer{margin:2.5rem 0 1.5rem;border-top:1px solid #dcdcdc;padding-top:.8rem;font-size:.8rem;color:#5c5c5c}
@media(prefers-color-scheme:dark){body{background:#161616;color:#f2f0ec}.grid li,.vars{background:#222}.promo{background:#3a3115;border-color:#f2f0ec}}</style>"""

HUB_START = '<!-- defs-hub-start -->'
HUB_END = '<!-- defs-hub-end -->'


def build_page(slug, phrase, variants, items, related):
    by_len = {}
    for it in sorted(items, key=lambda x: (len(x['n']), x['n'])):
        by_len.setdefault(len(it['n']), []).append(it)
    total = sum(len(v) for v in by_len.values())
    lens = sorted(by_len)

    secs = []
    for L in lens:
        lis = []
        for it in by_len[L][:120]:
            name = esc(it['t'])
            if it['p']:
                name = f'<a href="/milon/e/{urllib.parse.quote(it["t"], safe="")}/">{name}</a>'
            words = '' if ' ' not in it['t'] else f' · {len(it["t"].split())} מילים'
            d = f'<br><small>{esc(it["d"][:90])}</small>' if it['d'] else ''
            lis.append(f'<li><b>{name}</b> <span class="net">{esc(it["n"])}</span>{words}{d}</li>')
        secs.append(f'<h2 id="len-{L}">{esc(phrase)} ב-{L} אותיות ({len(by_len[L])})</h2>\n'
                    f'<ul class="grid">{"".join(lis)}</ul>')

    len_nav = ' · '.join(f'<a href="#len-{L}">{L} אותיות</a>' for L in lens)
    rel_links = ' · '.join(f'<a href="/milon/d/{r}/">{esc(PAGES[r][0])}</a>'
                           for r in related if r in PAGES)
    var_text = ', '.join(esc(v) for v in variants)
    title = f'{phrase} בתשבץ ובתשחץ - {total} פתרונות לפי מספר אותיות'
    desc = (f'כל הפתרונות להגדרה "{phrase}" בתשבץ או בתשחץ: {total} תשובות ממוינות לפי '
            f'מספר אותיות ({lens[0]}-{lens[-1]}), עם הכתיב המדויק ברשת והסבר קצר לכל תשובה.')
    rel = f'/milon/d/{slug}/'
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'דף הבית', 'item': f'{BASE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'מילון', 'item': f'{BASE}/milon/'},
        {'@type': 'ListItem', 'position': 3, 'name': phrase, 'item': f'{BASE}{rel}'}]}
    il = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': title,
          'numberOfItems': total}

    body = f"""<p>מחפשים פתרון להגדרה <b>"{esc(phrase)}"</b>? ההגדרה מופיעה שוב ושוב בתשבצים
ובתשחצים בעיתונים - ידיעות אחרונות (7 ימים), מעריב, הארץ, ישראל היום ומגזינים שונים.
לפניכם <b>{total} פתרונות</b> ממוינים לפי מספר האותיות, עם כתיב הרשת המדויק
(בתשבץ אין אותיות סופיות: ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ) והסבר קצר לכל תשובה -
כך אפשר לבחור את הפתרון הנכון ולא רק לנחש.</p>
<p class="lens">קפיצה לפי אורך: {len_nav}</p>
{''.join(secs)}
<p style="margin-top:1.2rem">חסר פתרון שמצאתם בעיתון?
<a href="https://github.com/razkaplan/tashbetz-solver/issues">כתבו לנו ונוסיף אותו</a>.
רוצים לחפש לפי תבנית אותיות (למשל ?ו?ה)? נסו את <a href="/milon/">חיפוש המילון</a>
או את <a href="/milon/anagram/">חיפוש האנגרם</a>.</p>
<p>הגדרות קרובות: {rel_links}</p>
<div class="vars">ביטויים דומים שמחפשים: {var_text}, {esc(phrase)} מילון, {esc(phrase)} פתרון.</div>"""

    os.makedirs(f'{OUT}/{slug}', exist_ok=True)
    open(f'{OUT}/{slug}/index.html', 'w', encoding='utf-8').write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}{rel}">
<meta property="og:type" content="article"><meta property="og:site_name" content="מילון תשבץ">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{rel}"><meta property="og:image" content="{BASE}/milon/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="he_IL"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/milon/og.png">
<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(il, ensure_ascii=False)}</script>{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>{esc(phrase)} - פתרונות לתשבץ ולתשחץ</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/milon/d/">כל ההגדרות</a> · <a href="/nativ/">המשחק היומי</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div>
<div class="promo">☀️ <a href="/nativ/">נתיב - המשחק היומי הטוב לחובבי תשבצים</a> · חידה חדשה כל יום, עכשיו גם במצב קל</div></header>
{body}
<footer>מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA, עם קישור למקור) ורשימות שנאספו ידנית ·
לא מתפרסמות הגדרות מעיתונים · <a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a></footer></div></body></html>""")
    return total


def build_hub(counts):
    lis = ''.join(f'<li><a href="/milon/d/{s}/"><b>{esc(PAGES[s][0])}</b></a>'
                  f'<br><small>{counts[s]} פתרונות</small></li>'
                  for s in PAGES if counts[s])
    title = 'הגדרות תשבץ נפוצות - כל הפתרונות לפי הגדרה'
    desc = (f'{len(counts)} הגדרות תשבץ ותשחץ נפוצות עם כל הפתרונות: זמר ישראלי, קיבוץ בצפון, '
            f'עיר באיטליה, יסוד כימי ועוד. כל תשובה עם מספר אותיות, כתיב רשת והסבר.')
    body = f"""<p>העמודים כאן בנויים סביב ההגדרה עצמה - בדיוק כמו שמחפשים אותה: "זמר ישראלי",
"קיבוץ בצפון", "עיר באיטליה". בכל עמוד כל הפתרונות ממוינים לפי מספר אותיות, עם כתיב הרשת
המדויק והסבר קצר לכל תשובה.</p>
<ul class="grid">{lis}</ul>
<p style="margin-top:1.2rem">לא מצאתם את ההגדרה? <a href="/milon/">חיפוש חופשי במילון</a>
(גם לפי תבנית אותיות), או <a href="/milon/anagram/">חיפוש אנגרם</a>.</p>"""
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'דף הבית', 'item': f'{BASE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'מילון', 'item': f'{BASE}/milon/'},
        {'@type': 'ListItem', 'position': 3, 'name': 'הגדרות נפוצות', 'item': f'{BASE}/milon/d/'}]}
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}/milon/d/">
<meta property="og:type" content="article"><meta property="og:site_name" content="מילון תשבץ">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}/milon/d/"><meta property="og:image" content="{BASE}/milon/og.png">
<meta property="og:locale" content="he_IL"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/milon/og.png">
<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>{STYLE}</head><body><div class="w">
<header><span class="k">מילון תשבץ · פותרים ביחד</span><h1>הגדרות תשבץ נפוצות</h1>
<div class="crumb"><a href="/milon/">מילון</a> · <a href="/nativ/">המשחק היומי</a> · <a href="/solve/">עוזר הפתירה</a> · <a href="/">דף הבית</a></div>
<div class="promo">☀️ <a href="/nativ/">נתיב - המשחק היומי הטוב לחובבי תשבצים</a> · חידה חדשה כל יום, עכשיו גם במצב קל</div></header>
{body}
<footer>מבוסס על אינדקס פתוח (ויקיפדיה/ויקימילון/שירונט, CC BY-SA) ורשימות שנאספו ידנית ·
לא מתפרסמות הגדרות מעיתונים · <a href="https://www.linkedin.com/in/razkaplan/">פרויקט של רז קפלן</a></footer></div></body></html>""")


def update_sitemap(urls):
    s = open('docs/sitemap.xml', encoding='utf-8').read()
    s = re.sub(r'  <url><loc>%s/milon/d/[^<]*</loc></url>\n' % re.escape(BASE), '', s)
    block = ''.join(f'  <url><loc>{BASE}{u}</loc></url>\n' for u in urls)
    s = s.replace('</urlset>', block + '</urlset>')
    open('docs/sitemap.xml', 'w', encoding='utf-8').write(s)


def update_milon_hub():
    """Insert/refresh the defs section on /milon/ between HTML markers."""
    p = 'docs/milon/index.html'
    s = open(p, encoding='utf-8').read()
    top = ', '.join(f'<a href="/milon/d/{sl}/">{esc(PAGES[sl][0])}</a>'
                    for sl in ['zamar-israeli', 'sachkan-israeli', 'sofer-israeli',
                               'kibbutz-tzafon', 'ir-italia', 'medina-africa',
                               'yesod-chimi', 'ot-yevanit', 'mitologia-yevanit'])
    sec = (f'{HUB_START}<h2>הגדרות נפוצות</h2><p>כל הפתרונות לפי ההגדרה עצמה: {top} '
           f'ועוד - <a href="/milon/d/"><b>כל ההגדרות הנפוצות</b></a>.</p>{HUB_END}')
    if HUB_START in s:
        s = re.sub(re.escape(HUB_START) + '.*?' + re.escape(HUB_END), sec, s, flags=re.S)
    else:
        s = s.replace('<footer>', sec + '\n<footer>', 1)
    open(p, 'w', encoding='utf-8').write(s)


def main():
    counts = {}
    urls = ['/milon/d/']
    for slug, (phrase, variants, src, related) in PAGES.items():
        items = src()
        counts[slug] = len(items)
        if len(items) < 5:
            print(f'SKIP {slug} ({phrase}): only {len(items)} answers')
            counts[slug] = 0
            continue
        build_page(slug, phrase, variants, items, related)
        urls.append(f'/milon/d/{slug}/')
    build_hub(counts)
    update_sitemap(urls)
    update_milon_hub()
    built = sum(1 for c in counts.values() if c)
    print(f'def pages built: {built} (+hub), answers total: {sum(counts.values())}')
    for s, c in sorted(counts.items(), key=lambda x: -x[1])[:10]:
        print(f'  {PAGES[s][0]}: {c}')


if __name__ == '__main__':
    main()
