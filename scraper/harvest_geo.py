#!/usr/bin/env python3
"""Add geography categories to culture.json (merge, never shrink) - full geo sweep."""
import json, time, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harvest_culture import members, clean

GEO_CATS = {
    'city_il':  ['ערים בישראל', 'מועצות מקומיות בישראל', 'יישובים קהילתיים בישראל',
                 'יישובים ערביים בישראל'],
    'mountain': ['הרים בישראל', 'רכסים בישראל', 'הר הגעש', 'פסגות האלפים'],
    'stream':   ['נחלים בישראל', 'נחלי החוף בישראל'],
    'river':    ['נהרות באירופה', 'נהרות באסיה', 'נהרות באפריקה',
                 'נהרות באמריקה הצפונית', 'נהרות באמריקה הדרומית'],
    'valley':   ['עמקים בישראל', 'בקעות בישראל'],
    'lake_sea': ['ימים', 'אגמים', 'אגמים בישראל', 'מפרצים'],
    'desert':   ['מדבריות', 'מדבריות בישראל'],
    'island':   ['איים', 'איים ביוון', 'איי אינדונזיה', 'איים בים התיכון'],
    'region':   ['חבלי ארץ בישראל', 'אזורים בישראל'],
    'site':     ['אתרים ארכאולוגיים בישראל', 'תלים בישראל', 'גנים לאומיים בישראל'],
}

def main():
    cult = json.load(open('solver/lex/culture.json'))
    for kind, cats in GEO_CATS.items():
        seen = set(cult.get(kind, []))
        before = len(seen)
        for c in cats:
            try:
                for t in members(c):
                    ct = clean(t)
                    if 1 < len(ct) <= 40 and re.search(r'[א-ת]', ct):
                        seen.add(ct)
            except Exception as ex:
                print(f'  {kind}/{c}: SKIP ({ex})', flush=True)
            print(f'  {kind}/{c}: {len(seen)}', flush=True)
            time.sleep(2)
        cult[kind] = sorted(seen)
        print(f'{kind}: {before} -> {len(seen)}', flush=True)
        json.dump(cult, open('solver/lex/culture.json', 'w'), ensure_ascii=False, indent=0)
    print('total entities:', sum(len(v) for v in cult.values()))

if __name__ == '__main__':
    main()
