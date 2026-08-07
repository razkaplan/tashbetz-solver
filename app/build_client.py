#!/usr/bin/env python3
"""Build the client-side data bundle for the BYO-key web app (docs/solve/data/).

The hosted app runs the deterministic engine tools in the BROWSER: lexicon membership,
pattern and anagram search, homograph senses, the setters' substitution table, and the
mechanical proof checks. Only reasoning (digitize / crack-a-clue) goes to OpenRouter with
the visitor's own key. This script emits the data those JS tools need.

What ships and why it is OK to ship:
  lexicon.txt        hspell-derived public wordlist + wikipedia culture entities (titles)
  substitutions.json derived word-pair equivalences (our analysis, not source content)
  ambiguities.json   derived homograph senses (our analysis)
  crosswordese.json  derived answer-frequency counts
  playbook.txt       our own written solving digest, embedded into prompts
  demo/*             one puzzle as a working demo (same 1-puzzle excerpt precedent as
                     the research page). Built only if the engine solve exists.
Held-out dev/eval answers are excluded from the lexicon exactly as in solver/lexicon.py.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, 'solver')
OUT = 'docs/solve/data'
os.makedirs(OUT, exist_ok=True)

import lexicon  # reuses held_out_answers gating

def main():
    words = lexicon.load()          # {word: priority}, dev/eval answers already blocked
    with open(f'{OUT}/lexicon.txt', 'w') as f:
        f.write('\n'.join(sorted(words)))
    print(f'lexicon.txt: {len(words)} words')

    for src, dst in [('solver/lex/substitutions.json', 'substitutions.json'),
                     ('solver/lex/ambiguities.json', 'ambiguities.json'),
                     ('solver/crosswordese.json', 'crosswordese.json')]:
        if os.path.exists(src):
            d = json.load(open(src))
            json.dump(d, open(f'{OUT}/{dst}', 'w'), ensure_ascii=False)
            print(f'{dst}: ok')

    # compact playbook digest for prompts (~2KB, from our own PLAYBOOK/PROTOCOL)
    digest = """תשבץ היגיון של יורם הרועה: כל הגדרה = הגדרה ישירה בקצה אחד + משחק מילים בשאר.
מנגנונים לפי שכיחות: שרשור חלקים (הנפוץ), אנגרם (הפודר מופיע מילולית בהגדרה! חלון רצוף
שאורכו = סכום המספור), מילה משותפת (שתי משמעויות), הכלה (א בתוך ב), היפוך (להפך/חוזר),
הומופון ("עפ\"י השמיעה של X" מסמן זאת), רפרנס תרבותי (פוליטיקאים/שירים/תנ\"ך).
כללי ברזל: (עפ\"י שם) בסוף הגדרה = קרדיט לקורא ששלח, לא חלק מהתחבולה. ברשת אין אותיות
סופיות (ם/ן/ץ/ף/ך נכתבות מ/נ/צ/פ/כ). מילה שמציינת מקצוע/תפקיד חשודה כשם פרטי (שרה=זמרת
/שרה בממשלה/שם). (מ) בסוף = כתיב מלא. סדר מילים בתשובה רב-מילים חייב להיות מוכרח ע\"י
הצלבה, לא ניחוש. תשובה שגויה גרועה מריק: היא מרעילה הצלבות."""
    open(f'{OUT}/playbook.txt', 'w').write(digest)

    # demo puzzles: every app/puzzles/<id> with a finished engine solve
    DEMOS = [('demo3107', 'sample3107', 'התשבץ של 31.7.2026'),
             ('demo0708', 'sample0708', 'התשבץ של 7.8.2026')]
    manifest = []
    for did, src, title in DEMOS:
        pdir = f'app/puzzles/{src}'
        if not os.path.exists(f'{pdir}/engine.json'):
            print(f'demo {did}: engine not ready — skipped'); continue
        eng = json.load(open(f'{pdir}/engine.json'))
        com = sum(1 for e in eng if e.get('tier') == 'committed')
        os.makedirs(f'{OUT}/demo/{did}', exist_ok=True)
        for fn in ('puzzle.json', 'engine.json'):
            json.dump(json.load(open(f'{pdir}/{fn}')),
                      open(f'{OUT}/demo/{did}/{fn}', 'w'), ensure_ascii=False)
        manifest.append({'id': did, 'title': title,
            'desc': f'המנוע פתר אותו בעיוורון: {com} מתוך {len(eng)} בתיוג "מוכח". רמזים זמינים בלי מפתח.'})
        print(f'demo {did}: baked ({com} committed)')
    json.dump(manifest, open(f'{OUT}/demos.json', 'w'), ensure_ascii=False)

if __name__ == '__main__':
    main()
