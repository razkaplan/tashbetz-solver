#!/usr/bin/env python3
"""Build the HOMOGRAPH / AMBIGUITY index — the core device of Hebrew logic crosswords.

Unvocalized Hebrew collapses distinct words into one letter sequence:
  שרה = שָׁרָה (she sings) = שָׂרָה (a female minister) = Sarah (name)
The setter builds clues on exactly these collisions. A solver that knows a token has
several senses can read a clue's definition half in the other sense.

Sources of senses:
  common_word   hspell dictionary (~129k)
  song          he-wikipedia song titles
  artist        he-wikipedia singers/bands
  politician    he-wikipedia Knesset members / ministers
  place         he-wikipedia Israeli cities
  given_name    first-name components split out of person names
  surname       last-name components
  answer        an answer that actually appeared in the corpus
  role_noun     curated Hebrew role/agent nouns that double as names

Outputs solver/lex/ambiguities.json  {token: {senses:[...], evidence:{...}}}
and prints the highest-value collisions.
"""
import json, os, re, glob, sys
from collections import defaultdict

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

def words_of(phrase):
    """Split a multi-word title/name into its component words (normalized)."""
    return [norm(w) for w in re.split(r'[\s\-־]+', phrase or '') if len(norm(w)) >= 2]

# Curated role/agent nouns that are also common personal names or verbs.
# These are the setter's favourite pivots.
ROLE_NOUNS = {
    'שרה': 'female minister / she sings / Sarah',
    'שר': 'minister / he sings',
    'שרים': 'ministers / they sing',
    'נשיא': 'president / prince',
    'רב': 'rabbi / many / he quarrelled',
    'כהן': 'priest / surname Cohen',
    'לוי': 'Levite / surname Levy',
    'דוד': 'David / uncle / kettle',
    'אור': 'light / given name Or',
    'שיר': 'song / given name Shir',
    'תמר': 'date palm / Tamar',
    'רון': 'joy / given name Ron',
    'גל': 'wave / given name Gal',
    'אלון': 'oak / given name Alon',
    'ניר': 'furrow / given name Nir',
    'עמית': 'colleague / given name Amit',
    'ליאור': 'given name / to my light',
    'סער': 'storm / surname Saar',
    'ברק': 'lightning / Barak',
    'אשכול': 'cluster / Eshkol',
    'הרצוג': 'surname Herzog',
    'פרס': 'prize / Persia / Peres',
    'זהב': 'gold / surname',
    'ים': 'sea / given name Yam',
    'רם': 'high / given name Ram',
    'עדן': 'Eden / given name Eden',
    'נועה': 'given name Noa / motion',
    'יעל': 'ibex / given name Yael',
    'אילה': 'doe / given name Ayala',
    'שחר': 'dawn / given name Shahar',
    'טל': 'dew / given name Tal',
    'אביב': 'spring / given name Aviv',
    'נחל': 'stream / he inherited',
    'ענבל': 'clapper / given name Inbal',
    'אורן': 'pine / given name Oren',
    'ארז': 'cedar / given name Erez',
    'עופר': 'fawn / given name Ofer',
    'איל': 'ram / given name Eyal',
    'גפן': 'vine / surname Geffen',
    'חן': 'grace / given name Chen',
    'שלו': 'his / calm / surname Shalev',
    'מור': 'myrrh / given name Mor',
    'סתיו': 'autumn / given name Stav',
    'ליבי': 'my heart / given name Libi',
    'אמונה': 'faith / given name Emuna',
    'מלכה': 'queen / given name Malka',
    'שושנה': 'rose / given name Shoshana',
    'סיגל': 'violet / given name Sigal',
    'ורד': 'rose / given name Vered',
    'רקפת': 'cyclamen / given name Rakefet',
    'נעמי': 'Naomi',
    'רות': 'Ruth / quench',
    'דין': 'law / given name Din',
    'צדק': 'justice / Jupiter',
    'מזל': 'luck / zodiac sign',
    'כוכב': 'star / celebrity',
    'ארי': 'lion / given name Ari',
    'דב': 'bear / given name Dov',
    'זאב': 'wolf / given name Zeev',
    'יונה': 'dove / Jonah / given name Yona',
    'ציפורה': 'bird / Zipporah',
    'אפרוח': 'chick',
    'נשר': 'eagle / he fell out',
    'עין': 'eye / spring / letter ayin',
    'פה': 'mouth / here',
    'יד': 'hand / memorial',
    'רגל': 'leg / pilgrimage festival',
    'לב': 'heart / core',
    'ראש': 'head / chief',
}

def main():
    os.chdir(ROOT)
    sense = defaultdict(set)      # token -> set of sense labels
    evid = defaultdict(lambda: defaultdict(list))  # token -> sense -> examples

    # 1. dictionary words
    hp = os.path.join(HERE, 'lex/hspell.txt')
    dict_words = set()
    if os.path.exists(hp):
        for line in open(hp, encoding='utf-8'):
            w = norm(line)
            if w:
                dict_words.add(w)

    # 2. culture entities (full titles AND their component words)
    cp = os.path.join(HERE, 'lex/culture.json')
    if os.path.exists(cp):
        cult = json.load(open(cp))
        for kind, items in cult.items():
            for t in items:
                full = norm(t)
                if full:
                    sense[full].add(kind)
                    evid[full][kind].append(t)
                parts = words_of(t)
                if len(parts) > 1 and kind in ('artist', 'politician'):
                    # person name -> given name + surname components
                    if parts[0]:
                        sense[parts[0]].add('given_name'); evid[parts[0]]['given_name'].append(t)
                    for p in parts[1:]:
                        sense[p].add('surname'); evid[p]['surname'].append(t)
                elif len(parts) > 1 and kind == 'song':
                    for p in parts:
                        # a word inside a song title is only interesting if it is also something else
                        sense[p].add('song_word'); evid[p]['song_word'].append(t)

    # 3. corpus answers (real crossword answers)
    ans_files = ['data/answers/answers_parsed.json'] + glob.glob('data/answers/extra/*.json')
    for f in ans_files:
        if not os.path.exists(f):
            continue
        d = json.load(open(f))
        puzzles = d if isinstance(d, list) else d.get('puzzles', [])
        for p in puzzles:
            for c in p.get('clues', []):
                a = norm(c.get('answer'))
                if a:
                    sense[a].add('answer')
                    if len(evid[a]['answer']) < 3:
                        ex = (c.get('explanations') or [''])[0]
                        evid[a]['answer'].append(ex[:60])

    # 4. curated role nouns
    for w, gloss in ROLE_NOUNS.items():
        w = norm(w)
        sense[w].add('role_noun')
        evid[w]['role_noun'].append(gloss)

    # 5. mark dictionary membership
    for tok in list(sense.keys()):
        if tok in dict_words:
            sense[tok].add('common_word')

    # keep genuine ambiguities: >=2 distinct senses, at least one non-trivial
    TRIVIAL = {'song_word'}
    out = {}
    for tok, s in sense.items():
        if len(tok) < 2:
            continue
        real = s - TRIVIAL
        if len(real) >= 2:
            out[tok] = {'senses': sorted(s),
                        'evidence': {k: v[:3] for k, v in evid[tok].items() if v}}

    os.makedirs(os.path.join(HERE, 'lex'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'lex/ambiguities.json'), 'w'),
              ensure_ascii=False, indent=0, sort_keys=True)

    # report
    print(f'ambiguous tokens: {len(out)}')
    def score(kv):
        s = set(kv[1]['senses'])
        return (len(s), 'common_word' in s, 'answer' in s)
    top = sorted(out.items(), key=score, reverse=True)[:25]
    print('\nHighest-value collisions (most senses):')
    for tok, d in top:
        print(f"  {tok:12s} {','.join(d['senses'])}")
    # named check
    for probe in ['שרה', 'שר', 'גפן', 'פרס', 'ברק', 'אור', 'שיר']:
        p = norm(probe)
        if p in out:
            print(f"\n{probe}: {out[p]['senses']}")

HEBSENSE = {'common_word': 'מילה מן המילון', 'given_name': 'שם פרטי', 'surname': 'שם משפחה',
            'role_noun': 'תפקיד/פועל וגם שם', 'song': 'שם שיר', 'song_word': 'מילה מתוך שיר',
            'artist': 'זמר/להקה', 'politician': 'פוליטיקאי/ת', 'place': 'מקום',
            'bible': 'דמות מקראית', 'answer': 'הופיעה כתשובה בתשבצים'}
def heb_senses(senses):
    return ', '.join(HEBSENSE.get(s, s) for s in senses)

def query(tokens):
    """Look up senses for one or more tokens (used by the solver at solve time)."""
    path = os.path.join(HERE, 'lex/ambiguities.json')
    if not os.path.exists(path):
        print('index missing — run: python3 solver/homographs.py build'); return
    idx = json.load(open(path))
    for t in tokens:
        n = norm(t)
        d = idx.get(n)
        if not d:
            print(f'{t}: (no recorded ambiguity)')
            continue
        print(f'{t}  משמעויות: {heb_senses(d["senses"])}')
        for k, v in d['evidence'].items():
            ex = '; '.join(x for x in v if x)[:120]
            if ex:
                print(f'    {k}: {ex}')

PREFIXES = ['ו', 'ה', 'ב', 'ל', 'מ', 'ש', 'כ', 'וה', 'ול', 'וב', 'שה', 'מה', 'כש', 'לה', 'בה']
SUFFIXES = ['ים', 'ות', 'י', 'ה', 'ו', 'ת', 'נו', 'כם', 'יו', 'ים']

def variants(w):
    """A clue word may appear inflected or glued to a prefix; the bare token is what
    carries the ambiguity. Yield the word and its plausible stems."""
    out = {w}
    for p in PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 2:
            out.add(w[len(p):])
    for s in SUFFIXES:
        if w.endswith(s) and len(w) - len(s) >= 2:
            out.add(w[:-len(s)])
    # prefix + suffix together
    for p in PREFIXES:
        if w.startswith(p):
            stem = w[len(p):]
            for s in SUFFIXES:
                if stem.endswith(s) and len(stem) - len(s) >= 2:
                    out.add(stem[:-len(s)])
    return out

def scan(text):
    """Report every ambiguous token appearing in a clue — run this on EVERY clue.
    Matches inflected and prefixed forms back to their ambiguous stem."""
    path = os.path.join(HERE, 'lex/ambiguities.json')
    idx = json.load(open(path))
    hits, seen = [], set()
    for w in re.split(r'[\s,.;:!?()"\'\-־]+', text or ''):
        nw = norm(w)
        if len(nw) < 2:
            continue
        for v in sorted(variants(nw), key=len, reverse=True):
            if v in idx and (w, v) not in seen:
                seen.add((w, v))
                via = '' if v == nw else f'  [stem of {w}]'
                hits.append((v, idx[v]['senses'], via))
    if not hits:
        print('(no ambiguous tokens in this clue)')
    for v, s, via in hits:
        print(f'{v}: {heb_senses(s)}{via}')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'scan':
        scan(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] not in ('build',):
        query(sys.argv[1:])
    else:
        main()
