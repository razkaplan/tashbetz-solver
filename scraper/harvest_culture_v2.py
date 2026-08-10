#!/usr/bin/env python3
"""Expand culture.json with more crossword-valuable categories (merge, never shrink)."""
import json, time, urllib.parse, urllib.request, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harvest_culture import members, clean   # reuses paced, retrying category walker

NEW_CATS = {
    'neighborhood': ['שכונות תל אביב-יפו', 'שכונות ירושלים', 'שכונות חיפה', 'שכונות באר שבע'],
    'park':         ['גנים לאומיים בישראל', 'שמורות טבע בישראל', 'פארקים בישראל'],
    'museum':       ['מוזיאונים בישראל'],
    'nation':       ['מדינות אירופה', 'מדינות אסיה', 'מדינות אפריקה',
                     'מדינות אמריקה הצפונית', 'מדינות אמריקה הדרומית', 'מדינות אוקיאניה'],
    'world_city':   ['ערי בירה'],
    'athlete':      ['כדורגלנים ישראלים', 'כדורסלנים ישראלים', 'ספורטאים אולימפיים ישראלים',
                     'שחייני ישראל', 'אצנים ישראלים'],
    'bible':        ['אישים בתנ"ך'],
    'author':       ['סופרים ישראלים', 'משוררים ישראלים'],
    'actor':        ['שחקני תיאטרון ישראלים', 'שחקני טלוויזיה ישראלים', 'שחקני קולנוע ישראלים'],
    'kibbutz':      ['קיבוצים', 'מושבים'],
}

def main():
    cult = json.load(open('solver/lex/culture.json'))
    for kind, cats in NEW_CATS.items():
        seen = set(cult.get(kind, []))
        before = len(seen)
        for c in cats:
            for t in members(c):
                ct = clean(t)
                if 1 < len(ct) <= 40 and re.search(r'[א-ת]', ct):
                    seen.add(ct)
            print(f'  {kind}/{c}: {len(seen)}', flush=True)
            time.sleep(2)
        cult[kind] = sorted(seen)
        print(f'{kind}: {before} -> {len(seen)}', flush=True)
        json.dump(cult, open('solver/lex/culture.json', 'w'), ensure_ascii=False, indent=0)
    print('total entities:', sum(len(v) for v in cult.values()))

if __name__ == '__main__':
    main()
