#!/usr/bin/env python3
"""STRICT positive validation of culture.json (2026-08-10, after user found polluted pages).

Rule reversal: an entity stays in a category ONLY if its wikipedia description POSITIVELY
confirms that category. No description = no page (we cannot verify it, and 'blank beats
wrong' applies to the milon exactly as it applies to the grid). This kills disambiguation
pages, list pages, people harvested from place-categories, and cross-category leakage
(a moshav filed as a mountain, the Concorde filed as a capital city).

Person/name cats (song/artist/politician/athlete/bible/author/actor) keep their source
semantics but still drop junk pages.

Usage: python3 scraper/validate_culture.py [--apply]
"""
import json, re, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JUNK_DESC = re.compile(r'דף פירושונים|פירושונים|רשימת ערכים|^רשימה של|דף פירוש')
JUNK_TITLE = re.compile(r'רשימת |קצרמר|\(פירושונים\)|היסטוריה של|הקרב על|מבצע |אצטדיון|אנדרטת|תבנית:|קטגוריה:')
PERSON = re.compile(r'\b(סופר|משורר|שחקן|שחקנית|זמר|זמרת|פוליטיקאי|רב\b|נביא|אציל|גאולוג|גיאולוג|'
                    r'נולד|נולדה|היה איש|הייתה|מנהל|אוצר|מנכ"ל|ראש עיריי|חבר כנסת|שר\b|כדורגלן)')

# description must match one of these to keep the entity in that category
ACCEPT = {
 'neighborhood': r'שכונה|רובע',
 'park':         r'גן לאומי|שמורת טבע|פארק|שמורה',
 'museum':       r'מוזיאון|מוזאון|בית נכות',
 'site':         r'^אתר ארכ|^תל |^חורב|^עיר עתיקה|^שרידי|^ה?אתר|^גן לאומי',
 'world_city':   r'^בירת|עיר בירה|בירתה|^עיר ב|^העיר',
 'nation':       r'^מדינה|מדינה ב|מדינת|רפובליק|ממלכה|נסיכות|קיסרות',
 'city_il':      r'עיר ב|מועצה מקומית|מועצה אזורית|יישוב|ישוב|כפר|מושב|קיבוץ|עיירה',
 'kibbutz':      r'קיבוץ',
 'moshav':       r'מושב|כפר שיתופי|יישוב קהילתי',
 'mountain':     r'\bהר\b|הר ב|רכס|פסגה|הרי ',
 'stream':       r'נחל|ואדי|יובל של',
 'river':        r'נהר|יובל של|זורם',
 'valley':       r'^עמק|^בקעה|^בקעת|^ה?עמק',
 'desert':       r'מדבר',
 'island':       r'\bאי\b|^אי |איים|ארכיפלג',
 'lake_sea':     r'\bים\b|אגם|מפרץ|לגונה|ימה',
 'region':       r'^חבל|^אזור|^מחוז|^פרובינצי',
 'place':        r'עיר ב|מועצה|יישוב|כפר|מושב|קיבוץ',
}
PERSON_FORBIDDEN = set(ACCEPT)          # every place cat rejects person descriptions
PROTECTED = {'song','artist','politician','athlete','bible','author','actor','military','common'}

def main():
    apply = '--apply' in sys.argv
    cult = json.load(open('solver/lex/culture.json'))
    desc = json.load(open('data/culture/descriptions.json'))
    stats = {}
    for cat, items in cult.items():
        if cat in PROTECTED:
            kept = [t for t in items if not JUNK_TITLE.search(t)
                    and not JUNK_DESC.search(desc.get(t, ''))]
            stats[cat] = (len(items), len(kept), 'junk-only')
            cult[cat] = kept
            continue
        pat = ACCEPT.get(cat)
        kept, seen = [], set()
        for t in items:
            d = desc.get(t, '')
            n = re.sub(r'[^א-ת]', '', t)
            if not d or JUNK_DESC.search(d) or JUNK_TITLE.search(t): continue
            # HEAD-NOUN rule: the category word must be the head of the description,
            # not a passing mention ("יישוב ... בעמק יזרעאל" is a town, not a valley)
            if pat and not re.search(pat, d[:14]): continue
            if cat in PERSON_FORBIDDEN and PERSON.search(d): continue
            if n in seen: continue
            seen.add(n); kept.append(t)
        stats[cat] = (len(items), len(kept), 'strict')
        cult[cat] = kept
    for cat, (b, a, mode) in sorted(stats.items(), key=lambda x: -(x[1][0]-x[1][1])):
        if b != a: print(f'{cat:14} {b:6} -> {a:6}  (-{b-a})  [{mode}]')
    total = sum(len(v) for v in cult.values())
    uniq = len({re.sub(r'[^א-ת]', '', t) for v in cult.values() for t in v})
    print(f'\nrows: {total}   distinct names: {uniq}')
    if apply:
        json.dump(cult, open('solver/lex/culture.json', 'w'), ensure_ascii=False, indent=0)
        print('APPLIED')

if __name__ == '__main__':
    main()
