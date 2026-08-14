# PLAYBOOK — תשבץ ההיגיון של יורם הרועה (הארץ)

Learned from 728 train rows (26 puzzles, 2025-11-07 → 2026-05-08), including the crowd
explanations and debates. This is the solver's core reference. All examples below are real
(clue → answer → crowd explanation). Answers are shown in grid form: **no final letters,
no spaces** (see §3).

---

## 0. The big picture

Every clue has (usually) two layers:
1. **הגדרה / רמז-פאן** — a definition, pun, or cultural reference for the whole answer.
2. **מנגנון** — wordplay that constructs the answer letter by letter.

But this setter is loose: sometimes the whole clue is a single pun ("משפט משותף") with no
letter-level wordplay at all, and sometimes there are *two* wordplay readings and no clean
definition (the crowd complains: "אין הגדרה ראשית, יש שני תרתי"). Do not force the strict
British-cryptic model; instead, verify: **can every letter of the answer be produced from
the clue, and does the leftover surface describe the answer?** If only one of the two holds
but strongly, that can still be Yoram's intended answer.

Empirical mechanism distribution (from crowd-explanation keywords, overlapping;
728 rows):

| mechanism | crowd phrasing | count | share |
|---|---|---|---|
| Charade / assembly (build from parts) | "X זה .. / Y זה .." | ~250-300 | ~35-40% (the default) |
| Anagram — אנגרם | "אנגרם", "ערבוב אותיות", "שיכול אותיות" | 117 | 16% |
| Double definition — מילה משותפת | "מילה משותפת", "משפט משותף", "מונח/שם משותף" | 103 | 14% |
| Container — X בתוך Y | "בתוך", "מוקף", "עוטפת" | ~74-92 | ~10-12% |
| Reversal — להפך | "להפך", "הפוך", "חוזר", "מאחור" | 48 | 7% |
| Homophone — נשמע | "נשמע", "שמענו", "לפי השמיעה" | 30 | 4% |
| Hidden / letter-run — רצף אותיות | "רצף אותיות" | 11+ | ~2% |
| Cross-reference (ר' N אופקי/אנכי) | "ראה N אופקי" | ~9-21 | ~2% |
| Pure culture-pun, no wordplay | explanation cites a song/sketch/book only | ~40-60 | ~6-8% |

Abbreviation/letter-decoding (a letter or acronym standing for a word) appears inside
~27% of all explanations — it is the setter's signature device (§2.3).

---

## 1. Mechanism taxonomy — with worked examples and indicators

### 1.1 אנגרם (anagram) — 117/728, 16%

**How the crowd phrases it:** "אנגרם <fodder>", "ערבוב אותיות של <fodder>", "שיכול אותיות".

**THE key empirical fact:** in **85% of anagram clues the fodder appears verbatim as a
contiguous run of clue words whose letters are an exact multiset match of the answer**
(finals normalized). Among non-anagram clues this almost never happens by chance
(3/611 ≈ 0.5%). So the strongest anagram detector is mechanical, not lexical:
> Scan every contiguous window of 1–5 clue words; normalize finals; if its letter
> multiset equals the answer-length multiset budget, you almost certainly found an
> anagram and its fodder.

**Indicators are weak and optional.** Yoram frequently gives NO anagram indicator — the
fodder doubles as the surface. When an indicator exists it is one of: מבלבל / מתבלבל /
בלבל, שיבוש, אחרת, מסעיר, יוצא, נוצר, תמורה ("תמורה - רמז לשינוי סדר האותיות"), משתלב,
מתברבר, הפרעה, בשגעון, פרוע / באופן פרוע, משונה, מעורב, שבור, גורס (=גרוס), or a
question mark on a name-like surface.

Worked examples:
- סופר עברי מאורשלים → מאירשלו — "אנגרם אורשלים" (fodder inside "מאורשלים", the מ is a
  prefix "from"; definition: סופר עברי = מאיר שלו)
- מסתפקים? סוטה מין ממינאפוליס? → מינסוטה — "אנגרם סוטה מין"
- הנידון: מלחין → דוהנני — "אנגרם הנידון" (Dohnányi; definition "מלחין")
- איום למוטט? → אולטימטומ — anagram of "איום למוטט", self-defining (איום = ultimatum)
- אני קורסת → אנורקסית — "אנגרם אני קורסת" (fodder ≡ definition; the whole clue is both)
- רם וגבוה בעיר מרחצאות בגרמניה → הומבורג — "אנגרם רם וגבוה" (def: spa town; note loose
  spelling — crowd protests "המבורג ולא הומבורג")
- האלוף ז"ל שעשה טוב לקיוסק? → טולקובסקי — "אנגרם טוב לקיוסק"
- מרים פיירברג ז"ל - זה לא ברשת → אשתהברזל — "אנגרם זה לא ברשת" (def: her nickname)
- נראה מנומנם, וקפה אולי יעזור לו → פוהק — "אנגרם וקפה" (tiny 4-letter fodder!)
- במאי נרגן גרם לתמורה → אינגמרברגמנ — "אנגרם במאי נרגן גרם"; תמורה is the indicator
- הרקוד... **subtractive anagram**: מוני אמריליו הלחין את "אליפלט" בלי מנין → טלפלא —
  "אנגרם אליפלט בלי י(מנין)" — fodder minus a letter, where the removed letter is itself
  clued (י = מנין = 10).
- **Anagram + addition**: כביכול לפני בית ספרו של בורלא → בליכוכב — "אנגרם כביכול + ב".

Practical recipe: compute the answer letter budget from the enum; slide windows over the
clue; on multiset match, the *rest* of the clue must define/pun the answer. If a window is
one letter short/long, look for "בלי X" / "עם X" / "+ letter clued by a word".

### 1.2 מילה משותפת (double definition) — 103/728, 14%

**How the crowd phrases it:** almost always just the two words "מילה משותפת" (variants:
"משותפת", "מיחה משותפת" [typo], "מילה נשותפת", "שם משותף", "מונח משותף"), or
"משפט משותף" when the answer is a multi-word phrase serving two readings.

**Structure:** the clue is TWO definitions side by side, usually 2–4 words total, often
with שאלה/ניחוח of a question mark. **Short answers (enum [3]) are overwhelmingly double
definitions** — clues #7, #10, #13, #19, #23 in each puzzle (the 3-letter slots) are the
first place to try this mechanism.

Worked examples:
- קרב על חלקנו? → מנת (קרב-מנת קרב / חלקנו-מנת חלקנו)
- מזל מזלי → גדי (zodiac Gedi / "my luck" גד)
- בשר או חלב? → לבנ (בשר לבן / חלב לבן... white meat, milk)
- גן ברכה → עדנ (גן עדן / עדן = ברכה)
- הומור של קרח? → יבש (dry humor / dry ice)
- לא למדו הרבה בדרום אפריקה → בורימ (בורים ignorant / Boers)
- חבל שצלע → יתר (rope-string / hypotenuse "צלע במשולש")
- משקל זבוב → בעל (משקל זבוב boxing? actually בעל זבוב / משקל בעל... the crowd just says
  מילה משותפת — accept loose fits)
- מכות מרות → קבל (קיבל מכות / קבל = complain bitterly)
- **משפט משותף** (phrase-level): לא התחשב במזג האויר ועשה קופה → יצאברוח ("יצא ברווח" /
  "יצא ב-רוח"); סמוראי נואש → חרבעולמו (חרבו-עולמו / חרב עולמו); הצטיינה בפוקר ביציאת
  מצרים → ידחזקה (יד חזקה); פרסם שתפס דג → העלהלרשת (העלה לרשת).

Trap: the crowd sometimes disputes "מילה משותפת" labels — the setter uses it loosely for
any clue whose two halves both mean the answer, even synonyms ("זה לא מילה משותפת, זו
מילה נרדפת לשתי המילים"). For solving it does not matter: try one word satisfying both
halves.

### 1.3 Charade / assembly (הרכבה) — the default mechanism, ~35-40%

No standard Hebrew name in the crowd; explanations just decode part by part:
"X זה <word1> / Y זה <word2>". Parts are, in rough order of frequency:
1. **Synonyms**: נחלאות = נחל (ירש) + אות (בית "letter"); קניות = רכישות.
2. **First names / surnames of celebrities**: בניחלופ = בני (אמדורסקי) + חלופ;
   מנדירודנ = מנדי (מחרימי? — מנדי רייס-דיוויס) + רודן (עריץ).
3. **Single letters standing for words** (§2.3).
4. **Acronyms**: רשתגימל = ר + שת(תחת) + גימ(הנסון) + ל; חנמ = חומר נפץ מרסק.
5. **Gematria numbers**: זימימ = ז(7) + ימים ("שבוע של דגים"); זבנימ = ז(7)+בנים
   ("7 בני חנה"); נגזרות = נ(50=5 עשרות)+גזרות; רבניות = ר(200=מאתים)+ב-ניות;
   יובלדור = יובל(50)+דור(25) "מדבב מוזיקאי 25:50"; להטריפו = לה(35)+טריפו.

Worked examples:
- אינפרנו: אין (חוסר) + פרנו (משקה) — "חוסר יין כזה הוא גיהנום!"
- טרומביל: טרום (מלפני) + ביל (קלינטון) — "מכונית מיושנת, מלפני קלינטון"
- בליצקריג: בלי צ'ק (ללא אמצעי תשלום) + ריג (דיאנה ריג) — "מלחמת הבזק"
- קונספציה: קונ (שופט) + ספ (מפתן) + ציה (מדבר) — "תפיסת השופט הזה על מפתן המדבר"
- אינטלקטואל: אינטל (חברה) + קטו (הזקן) + אל גור — "איש רוח בחברת זקן ידוע וגור"
- יונתנרושפלד: יון (עוף) + תן (טורף) + רושפ (יורה) + לד (נורה) — 4 parts!
- זרתוסטרה: זרת (אצבע) + וסטרה (הפליקה)
- מסריק: מס (היטל) + ריק (ואקום) — "נודע בעבר בפראג"
- שוליתהקוסמ: שולי (נתן) + תה (משקה) + קוסם (מפתה)

Recipe: split the enum; for each part generate candidates from clue words via
(a) synonym, (b) celebrity first/last name, (c) letter/acronym decode, (d) gematria;
then check the remaining clue words form the definition. Parts follow **clue order most
of the time but not always** — the setter freely reorders.

### 1.4 Container (הכלה) — "X בתוך Y" — ~10-12%

**How the crowd phrases it:** "X בתוך Y", "בתוך", "מוקף", "עטוף", "נכנס ל-", "לתוך".

**Clue-side indicators** (empirical): נכנס / נכנסים / נכנסו / להיכנס, ב- prefix on the
container word, בתוך, בלע / בולע / בלעה, עוטפת, מוקף, תקעו, מכניס, שבלע, מושקע,
תפסה, ב<location>-phrasing ("בגשם", "באלימות"), בין (between = split container),
באמצע, מחוץ ל- (X *outside* Y = Y inside X!).

Worked examples:
- ניראליהו: ראליה (מציאות) בתוך ניו — "מציאות בניו של הקבוץ" (kibbutz Nir Eliyahu)
- חפשפעולה: שפעו (נתנו הרבה) בתוך חפלה (מסיבה) — "נתנו הרבה במסיבה"
- פיתגורס: גו (משחק) בתוך יתר (בית"ר) בתוך פס (מסירה) — nested containers, "מובילה למשפט"
- הוליווד: ליוו (נכנסו בחברה) לתוך הוד (בית קולנוע)
- רקודנו: קוד בתוך רנו — "שחרור המכונית מנעילה"
- אשכרוע: שך (הרב) בתוך ארוע — "אם הרב משתתף בארוע, הוא בוק" (a tree)
- עמוסקולק: וסקו (דה גמה) בתוך עמלק (צוררים) — "גם דה גמה בצוררים! קובע הבמאי"
- פופולרימ: פול (מקרטני) בתוך פורים — "מקובלים על מקרטני בחג"
- סנפלינג: נפל (מדינה, Nepal) בתוך סינג (סינג-סינג = חצי בית סוהר!) — "נכנסה לחצי בית סוהר"
- לינקולנ: ינקול (גולדווסר) בתוך לן (ישן) — "גולדווסר בישן כמו הנשיא"
- אשתקד: שתק (לא פצה פה) בתוך אד (הבל) — "לפני שנה לא פצה פה בהבל"
- Reverse-container marker: "מחוץ ל" — סטנדרטי: סטי (המלחין Satie) מחוץ ל-טנדר (רכב).

### 1.5 Reversal (להפך) — 48/728, 7%

**How the crowd phrases it:** "להפך זה X", "ההפך מ-", "הפוך", "חוזר", "מאחור",
"בכיוון הפוך", "החזר של".

**Clue-side indicators** (strong, empirically validated): שוב (9 of 17 occurrences are
reversals!), חוזר / חוזרת / בחזרה / בשובו / יחזור / בחזור, החזיר / תחזיר / מחזיר / שהוחזר,
להפך (explicit, sometimes with "?להפך" appended at the end), מאחור / מאחורי / אחוריי,
מצד שני, במבט רטרוספקטיבי, ממול, עולה (in a down clue = read upward!), יורד...עולה,
מימין, לאחור, ערוף (behead then reverse).

Worked examples:
- שמעוני חוזר בליל הסדר → יחצ (צחי שמעוני reversed; def יח"צ? no — "בליל הסדר" = יחץ!)
- העגלון חוזר מאוחר → אפיל (ליפא reversed; אפיל = מאחר להבשיל)
- לא החליט להחזיר את השחיטה שלה → התחבט (טבחתה reversed)
- שוב פתח יבשה? להפך → לחה (החל=פתח reversed; def: ההפך מיבשה)
- הרקוד יהיה אטי יותר במבט רטרוספקטיבי → ולס (סלו reversed)
- יורד בתפקידו בבנין, עולה בתפקידו בצבא → רצפ (down: רצף flooring; up: פצ"ר)
- משעמם בכלא, מצד שני → יבש (שבי reversed)
- הכלל הוא לעולם... הפרשה חוזרת → תקח (פרשת חקת reversed; "לעולם תקח")
- מה קשה בעלוי הנשמות של החתול? → עשת (תשע reversed — cat's nine lives)
- קבוצה באה וחוזרת → קהל (להק reversed — both are groups; double-def + reversal)
- נשקי מאחור חיה → יחמור (רומחי reversed)
- **Down-clue "עולה"**: השחקן הצרפתי העולה הוא עצום → ורב (ברו=Jean-Louis Barrault
  reading upward).

### 1.6 Homophone (נשמע) — ~30/728, 4%

**How the crowd phrases it:** "נשמע X", "שמענו", and the credit line itself:
**"(עפ"י השמיעה של <שם>)"** in the clue is an explicit homophone marker (8 occurrences).

**Clue-side indicators:** שמענו (11/11 = homophone, perfectly reliable), "שמענו ש..."
(13 in corpus), כפי ששמענו, לשמוע, נשמעת, מצטלצל / מצלצל, כך אומרים, "אומרים" alone
(7 in corpus), קול, עפ"י השמועה, בנוסח / בהשראת השמיעה. SETTER QUIRK (user-attested,
2026-08-10): Yoram sometimes marks a homophone with nothing but a bare **ש׳** (a lone
shin+geresh) — treat a stray ש׳ in a clue as a possible homophone marker, not a typo.

Worked examples:
- שמענו שחקן מכריז שיפעל כפלאח → עזראדגנ ("נשמע אזרע דגן"; עזרא דגן the actor)
- שמענו שוה מה שעשה משרתו של הסולטן בכלי נגינה → הרמוניקה ("נשמע הרמון ניקה")
- נראה שמנהיג איראן משפיע בסתר → מושכבחותימ ("נשמע מושך בחוטים" — חותים/חוטים)
- הגבוה נכנס לחופה? לפחות התכוון לכך, כפי ששמענו → נשא (נשמע "ניסה")
- שמענו שאינם יכולים להתקיים במערכת המשפטית → תובעימ (נשמע "טובעים")
- צ'לן מגמגם את שם המסכת? (עפ"י השמיעה של...) → יויומה (יו-יו מא = Yo-Yo Ma; מסכת יומא)
- בכיה הנשמעת כנחמה → קינה (נשמע כינה — הכינה נחמה, kids-song reference)
- תקעו... "מי לחוטים אלי!" קוראת המדינה → לטביה (נשמע "לטוויה") — crowd notes the
  homophones are APPROXIMATE (stress/nikud differ). Accept fuzzy sound matches.

### 1.7 Hidden / רצף אותיות — ~11+, 2% (undercounted; watch for it)

**How the crowd phrases it:** "רצף אותיות" — the answer sits inside the running text of
the clue, crossing word boundaries.

Worked examples:
- מלחין מויימר, גרמניה? → רגר ("מויימ**ר גר**מניה" — Max Reger)
- שחקן צרפתי מברוקלין → ברו (מ**ברו**קלין)
- מכבים, חשמונאים, שילך לעזאזל! → ימחשמו (מכב**ים חשמו**נאים; def ימח שמו)
- בוכואלד מבאר-טוביה → ארט (ב**ארט**וביה — Art Buchwald)
- הפילוסוף מתל סהרון → תלס (מ**תלס**הרון — Thales)
- מייחל לשלג במיצרי טירן → יטי (במיצר**י טי**רן — Yeti)
- המצודה פרושה בין הר ודיונה → הרודיונ (**הר ודיונ**ה!)
- המלחין מגיע מהנוי וולדיווסטוק → ויוולדי (מהנ**וי וולדי**ווסטוק)
- הספורט האהוב על בריטני ספירס? → טניס (ברי**טני ס**פירס)
- אבנים מהעיר: עמוד ואד → באבאל? (actually double-def) — check both.
Indicator words: מ- prefix before a place/name, ב- prefix, "בין X ל-Y", "מגיע מ",
or no indicator at all — when a clue is dominated by one long proper noun, try extraction.

### 1.8 Pure culture-reference / pun-definition (~6-8%, plus flavor on most others)

The whole clue is a witty definition or an allusion to a song, sketch, book, or person;
the crowd explanation cites the source, no letter mechanics.

Worked examples:
- בריז'יט ברדו השתלטה על החנות בזמר העברי → תפסהאתהעסק (line from "קוסמי עליז" —
  עלי מוהר/יוני רכטר: "כמו בריז'יט ברדו שתפסה כבר את העסק")
- סדרת ילדים שלא ביים רוב ריינר → ראשכרוב (Rob Reiner's nickname "Meathead" in All in
  the Family = ראש כרוב)
- השב"כ הרשה למסור את שמה של גבורת תקרית גבול → הכבשהשרה (anagram השבכ הרשה **and**
  reference to the שייקה אופיר/אורי זוהר sketch "תקרית גבול" with הכבשה שרה)
- מנצח המקהלה מעודד זאב? → יופינחמה (Shaike Ophir sketch line "יופי נחמה" + זאב נחמה)
- תם וחכם, ראש הממשלה ומיליון דולר → ארבעקושיות (four famous "questions")
- העכברים ישמחו לבחור בין סרטו של רוב ריינר לסרטו של ארז תדמור → בחורימטובימ
  (two films with the same name)
- מה שעשה שרון לאביהו? → בשבילמדינה (פלאטו שרון's catchphrase; אביהו מדינה)

Recipe: when clue names a creator/genre ("בזמר העברי", "בשירם של X ו-Y", "הגששים",
"סרטו של X") — the answer is a TITLE or LYRIC LINE matching the enum. Search memory of
Israeli classics first (see §2.2 domains).

### 1.9 Combos

Very common: anagram+reference (הכבשהשרה), reversal+double-def (קהל/להק), container
inside charade (יונתנרושפלד), subtractive devices:
- **Deletion**: קניוק מינוס קן (בית) = יוק — "סופר חסר בית"; בעתה בלי בית = עתה
  ("הבהלה ההומלסית"); ציטט בלי סוף = ציט.
- **Beheading/curtailing**: פודמניצקי ערוף → ירדן בלי ראש → רדן → reversed נדר;
  "חרבין איה חרבין" without last letters = חרביאיחרבי ("עד אין סוף" = drop the end!).
- **Letter substitution**: אם נמיר את הכשלון בקוף → סלובניה→סלובקיה (replace נ with ק);
  "נ נכשל בין הס לדק" → הסנדק.
- **Half-word**: חצי סביבון = נס (from נס גדול היה פה); חצי בית סוהר = סינג; חצי שלמה =
  גרנ (half of גרוניך... disputed).

---

## 2. Setter quirks — יורם הרועה

### 2.1 The (עפ"י <שם>) credit — IMPORTANT, commonly misunderstood

**(עפ"י X) means the clue was CONTRIBUTED by reader/colleague X.** It is a crowdsourced
guest-clue credit, NOT a hint that the answer puns on X. 362/728 clues (50%) carry it.
Top contributors: אליעזר כמון (49), איציק בלול (49), יוסי אילן (43), יוסי קאופמן (33),
עפר קציר (31), אלי מועלם (26), צבי ויצמן (24), נדיב אבידן ז"ל, יחיאל שליטין, אמנון שחם,
תמי דותן. The crowd even attributes styles to them ("הגדרה סיפורית מדי בסגנון איציק
בלול", "אמרת קאופמן אמרת הכל").

Contributor style priors (use as weak evidence):
- **יוסי קאופמן** — convoluted multi-part charades, obscure trivia; crowd complains most.
- **איציק בלול** — narrative/story-like surfaces, "הגדרה סיפורית"; charades + containers.
- **אליעזר כמון** — heavy on wordplay including homophones; "עפ"י השמיעה של אליעזר כמון"
  is his homophone signature.
- **עפר קציר** — culture references: films, songs, poems (טשרניחובסקי, יוסי גמזו, sketches).
- **צבי ויצמן, אלי מועלם** — standard charades/anagrams.

Variants: "(עפ"י השמיעה של X)" = **homophone clue**. CORRECTED 2026-08-10:
"(מחדושי X)" is NOT a plain credit synonym — it is credit + a COINAGE FLAG (see the
Coinage section): the answer is an invented portmanteau absent from every lexicon.
"(מחדושי המחבר)" = Yoram's own coinage.

Other clue-tail markers:
- **(מ)** = כתיב מלא (plene spelling) — 62 clues. The answer is written with extra
  י/ו relative to default. E.g. (מ) on מקורזל, דווקאעכשיו, ביומזה.
- **(ח)** = כתיב חסר — 3 clues.
- Default with no marker is **standard ktiv haser-ish**: the setter often drops י
  (רקודנו=ריקודנו, מלכתחלה, תחלה, קימונו explained as קיימונו). When letters won't fit,
  try removing/adding י or ו first.

### 2.2 Favorite cultural domains (ranked by observed frequency)

1. **Old-guard Israeli politics**: יוסף בורג ("הד"ר"), אבא אבן, פרס, רבין, בגין, גולדה-era
   ministers (גדעון פת, ברמן, המר), נתניהו/שרה/ביבי, לפיד, יואב קיש (a favorite target —
   clued twice: "יש שר ויש בקיא בעניני חנוך" / "ישו בקיא בחינוך?" → יואבקיש), עזר ויצמן,
   בן גוריון/פולה, לופוליאנסקי.
2. **Israeli singers/composers of the 60s-80s**: מתי כספי (a running theme one week),
   מוני אמריליו (his name in the clue often just means "this is an anagram/nonsense
   phrase" — he was known for wordplay songs), בני אמדורסקי, שולי נתן, שלומי שבת,
   חוה אלברשטיין, יהודה פוליקר, עומר אדם, זאב נחמה, אחינועם ניני, קובי אפללו.
3. **Bible & Jewish sources**: parashot (חקת, זכור, יתרו, מטות), the ארבעה בנים of the
   Haggadah (multiple times!), masechtot (יומא, פרה, נדה, סוטה), biblical figures
   (רבקה/עשו, יעל וסיסרא, יהודה המכבי, אבא שאול, רבי עקיבא), Psalms/תהילים quotes,
   שיר השירים ("ברח דודי").
4. **Classic TV/radio/sketch comedy**: הגשש החיוור (quotes!), שייקה אופיר sketches,
   שמוליק רוזן "קפד ראשו", לוליק, מושיק טימור, ניקוי ראש-era figures, המרדף (כאן 11),
   גיא פינס, אברי גלעד-era hosts, ירדן פודמניצקי (קישון character).
5. **Old Hollywood/world culture**: ג'ון ויין, גרגורי פק, דיאנה ריג, אלק גינס, ליזה מינלי,
   מל ברוקס, בורגנין, ג'ון וויקליף, composers (ובר, סטי/Satie, מאיירבר, דוהנני, להר,
   טוסקניני, ויוולדי), writers (קונרד, קנז, גרוסמן, א"ב יהושע, מורקמי, בורלא).
6. **Israeli songs as answer sources**: לטיול יצאנו, ערב של שושנים, אליפלט, זלמן יש לו
   מכנסיים, משה משה איזה נביא, הייתי נער, ויבן עוזיהו, שיר לך כנרת. If the clue smells
   like a lyric, it is one.
7. **Holiday awareness**: puzzles are seasonal — Hanukkah clues in December (דמי חנוכה,
   סורה חשך, שיר חנוכה), Purim in late Feb (פורים containers, בני המן, ושתי), Passover
   in late March (ארבע קושיות, שבת הגדול, בעור, כל דכפין, שלח את עמי), ט"ו בשבט in
   late Jan (תמר מגהול twice!). **Use the puzzle_date to prime holiday vocabulary.**

### 2.3 Abbreviation & single-letter tricks (the signature device, ~27% of clues)

Letters stand for words. Empirically observed decodings:

| letter/abbr | stands for | example |
|---|---|---|
| ז | 7 / שבע | זימימ = ז' ימים = שבוע |
| ח | 8 / שמונה | חוצ: צו-ח reversed; כלאחריד: ח in כלא |
| י | 10 / מנין | ירקונימ = י(מנין)+רקונים; טלפלא = אליפלט בלי י |
| יג | 13 / בר-מצוה | ואדיגוז = יג inside ואדוז |
| לה | 35 | להטריפו = לה(35)+טריפו |
| נ | 50 / חמישים; also כשלון (the grade) | עדנ = עד נ; נגב = נ(נכשלה)+גב; נקדימונ |
| ר | 200 / מאתים | רבניות = ר+בניות |
| ק | 100 | — |
| ס | אפס / כלום / doing nothing | לקס = לק+ס; דלס = דל+ס; פנס = פן+ס |
| ט | טוב; ט"מ = טוב מאוד | אלט = אל+ט; טורנדוט = טורנדו+ט; מטמונ = מ-ט"מ+ו-נ |
| מ | מצוין (הציון); grade set: מ=מצוין, ט=טוב, נ=נכשל, א=ראשון | user-attested 2026-08-10 |
| א | ראשון / אלף; א"א = מצוינות | חטא = חט+א; אבאאבנ |
| ע"ה = ז"ל | (both = "the deceased") | מעה = מ-ע"ה ≡ מ-ז"ל ("מזל שוה כסף") |
| מ"מ | ממלא מקום / במקום | ממזג = מ"מ+זג |
| ר"מ / רה"מ | ראש ממשלה | רביבימ = ביבי inside ר"מ |
| מ"י | מחנה יהודה | ימפינס |
| ל"ע | מפלגה לשעבר | לעברנו = ל"ע+ב-רנו |
| ח | חבר (kibbutz "ח'") | חזרזיר = ח(חבר)+זרזיר; חחד = ח+ח+ד(דלת) |
| ש | 300 / שלוש מאות; also שין | ששיאישי = ש+שיאי+שי |
| ת"ת | תלמוד תורה | תנשמות = ת+נשמו+ת; מתת = מ-ת"ת |
| ר"ג | רמת גן | שפילברג = שפיל+ב-ר"ג |
| ת"א | תל אביב | שבתאי = ת"א ב-שבי |
| קק"ל | שדרות קק"ל | קלאסיקל = לאסי inside קק"ל |
| א"י | ארץ ישראל | רמאיות = רמ+א"י+ות |
| מ"כ | מפקד | יהודההמכבי = הודה+המ"כ+יבי |
| קמ"ן, פצ"ר, מח"א, קב"ט, יח"צ, מל"א, לח"י, ד"ר, עו"ד | military/professional acronyms | passim |

Also: solfège notes (סול, לה, דו, סי, מי as building blocks — דגלהדיו, סימבול), Latin/
English letters spelled in Hebrew (זד=Z, סי=C, אם=M, רו=Greek rho), currencies as short
words (ין, לק, פני, יואן, רנד, מעה, סו), and vehicle brands (רנו, ון) as containers.

### 2.4 Definition/wordplay ordering

No fixed rule. Definition can be at the start, the end, or *interleaved*; sometimes the
definition is the whole surface (pun-definitions with "?"). "?" marks a loose/punny
definition (41 clues end with ?); "!" marks exclamatory surfaces (14). Cross-reference
clues: "ר' 14 אופקי" (= see 14-across; the two entries share one long answer or phrase;
enum may even be empty []). "+21 אנכי" prefix = this answer continues in clue 21-down.

---

## 3. Enumeration & grid conventions

- **answer_raw is unspaced and uses NO final letters**: 0/728 answers contain ם ן ץ ף ך;
  174 answers end in מ/נ/צ/פ/כ (e.g. נדלנ, זימימ, שחפ). Produce answers the same way.
- **enum lists per-word letter counts**; sum = answer_len. Distribution: 1 word 62%
  (452), 2 words 34% (244), 3 words 4% (27), 4 words 3. Part sizes cluster at 3 (334)
  and 4 (249); parts of size 1-2 exist (א' בן-הנביא: enum [1,1,5] = א' + ב' + יהושע).
- Answer lengths 3-11, mean 6.0. The grid is a fixed weekly pattern: each puzzle has
  ~28 clues; the [3]-slots (clues 7,10,13,19,23 across; 12 down) are the double-definition
  hotspots; 1-across is usually a long showpiece (10-11 letters, often anagram or
  culture-pun).
- **Spelling is flexible**: default leans כתיב חסר; (מ) forces מלא, (ח) forces חסר.
  Foreign names are transliterated loosely to fit (הומבורג, רגן, דלס, טובאריש) — when a
  name almost fits, bend the transliteration, not the mechanism.

---

## 4. Step-by-step solving recipe (refines SOLVE_PROTOCOL.md)

1. **Parse the clue**: strip (עפ"י ...) / (מחדושי ...) credits; note (מ)/(ח) spelling
   flags; note "עפ"י השמיעה" → homophone; note "ר' N" cross-references; note puzzle_date
   for holiday priming.
2. **Anagram scan FIRST (mechanical, highest precision)**: normalize finals; slide
   windows of 1-5 consecutive clue words; if a window's letter multiset == the total
   enum letter count budget → treat as anagram fodder (85% recall, ~0.5% FP). Then the
   leftover words must define the answer; rearrange fodder into a real word/name/phrase
   fitting the enum split. Also try windows ±1 letter with "בלי X"/"עם X"/"+" phrases.
3. **If enum is [3]**: try double definition first — one 3-letter word satisfying both
   halves of the clue. Common 3-letter answers recur (עדנ, יבש, ודא, לפת appear twice
   each in 26 puzzles).
4. **Check reversal indicators** (שוב, חוזר, החזיר, להפך, מאחור, מצד שני, עולה-in-down):
   reverse a synonym or a name from the clue.
5. **Check homophone indicators** (שמענו, נשמע, מצטלצל, עפ"י השמיעה): say candidate
   phrases aloud; allow approximate vowels/stress.
6. **Check container indicators** (נכנס, בלע, בתוך, מוקף, עטוף, בין, ב-prefix, מחוץ ל-
   for the reverse): pick inner and outer candidates whose lengths add up.
7. **Hidden scan**: if the clue contains long proper nouns with מ-/ב- prefixes, scan the
   letter-run of the whole clue for an enum-length substring that is a real word/name.
8. **Charade (default)**: split enum into parts; for each clue word generate: synonyms,
   celebrity first/last names, acronym expansions, single-letter decodings (§2.3 table),
   gematria values, currencies, solfège. Assemble left-to-right, then try reorderings.
9. **Culture route**: if the clue cites a creator/show/song/genre, search Israeli-classics
   memory for a TITLE/LYRIC of enum shape. Seasonal words when near a holiday.
10. **Verification (hard gate)** before emitting:
    - letters: every letter of the candidate accounted for by the mechanism; enum split
      exact; no final letterforms in output.
    - surface: leftover clue words form a plausible definition/pun. If 1-2 words remain
      unaccounted, that's Yoram-normal padding (lower confidence slightly, don't reject).
    - spelling: if letters mismatch by only י/ו, adjust per (מ)/(ח)/default-haser.
    - reality: answer is a real Hebrew word, name, phrase, title, or accepted loose
      transliteration.
11. **Confidence**: 0.9+ = mechanical anagram/hidden with clean definition; 0.7 = charade
    with all parts decoded; 0.5 = pun/culture with no letter verification; below 0.5 =
    emit best guess and flag.
12. **Explanation format**: crowd style, one line: "אנגרם <fodder>", "מילה משותפת",
    "להפך זה <word>", "<part> זה <meaning> / <part> זה <meaning>", "נשמע <phrase>",
    "רצף אותיות", "X בתוך Y".

---

## 5. Common traps (mined from crowd complaints & debates)

1. **Loose foreign transliteration**: הומבורג/המבורג, רגן/רייגן, דלס/דאלאס, ניק/דיק
   (ניקסון), טר, רפרט. If a name is one letter off, the setter probably bent it.
   ("שמות לועזיים ניתן לעוות ככל שמתאים".)
2. **Missing י (ktiv haser by default)**: מלכתחלה, תחלה, רקודנו, קימונו. Crowd:
   "חסר י". Never reject a candidate for a missing/extra י/ו — check the (מ)/(ח) flag.
3. **Approximate homophones**: לטביה/לטוויה, כרש/קור-אש, תעסוקתי/"תעשו קאט י". Stress
   and nikud need not match.
4. **Padding words with no function**: crowd repeatedly asks "מה תפקיד המילה X?"
   (e.g. "פעם" in כרטיסאשראי, "בכנות", "כלאחר"). Do not force every word to work.
5. **Era-obscurity**: answers assume 1960s-80s Israeli culture (רפי לירז, לוליק, חיבת
   ציון, מולר של אתא, ראובן מס publishing). Prefer OLD references over current ones.
6. **Enum-order mismatch**: at least once the definition order was reversed vs the enum
   ("ההגדרה היא 3 ו-4, הפתרון 4 ו-3" — מולרבימ). Try both orders for 2-word answers.
7. **Non-dictionary coinages**: ביקרוני (=ביקרו אותי), מושכבחותימ, תרקידומ — the setter
   accepts grammatical constructions that aren't lexemes. Verb+suffix forms are fair game.
8. **Contested/wrong facts**: sometimes the setter is simply wrong (אספלט for אסבסט,
   ניאוקני for ניאוגן, לסו/חבל). If a near-miss candidate fits mechanics but the fact is
   off, it may still be the intended answer.
9. **Double reading of ש/ב letters**: ש read once as "שין" once as "ס-sound" (נשימבצד);
   ב read as "bet" or "in". Letter names (שין, תו, גימל) are usable as parts.
10. **"מילה משותפת" mislabels**: crowd argues whether a clue is truly double-definition
    vs two synonyms vs trivia. Ignore the taxonomy debate; just satisfy both halves.
11. **The setter riffs on his own grid**: the same answer/פירוש reappears across weeks
    (המורואיד twice, יואבקיש twice, בקשתיאש twice, דולניקר twice, תמרמגהול twice,
    גנייהושע twice — with DIFFERENT clues). Maintain a memory of past answers; recurrence
    is real signal.
12. **Cross-ref clues**: "ר' N אופקי" rows have near-empty clues and possibly empty enum;
    solve the paired clue first and split the long phrase across both entries.

---

## Cross-setter tactics (secondary corpus)

Mined 2026-07 from 310 puzzles / 6,792 clues (9,168 crowd-explanation strings) of SIMPLER
logic crosswords: **דקל בנו** — "תרתי משמע" (52 puzzles), "הפוך על הפוך" (51), ידיעות
יום שני (51), ידיעות יום רביעי (52), "לאישה" (52) — and **ליאור ליאני** — גלובס "היגיון
פשוט" (52). No clue texts in this corpus, only answer + crowd explanations; everything
below is answer-side mechanism knowledge plus explanation-vocabulary. All of §3's grid
conventions hold here too: answers unspaced, **no final letters** anywhere.

### C.1 Mechanism profile per setter (explanation-keyword counts)

| corpus | homophone | anagram | reversal | double-def | container | deletion |
|---|---|---|---|---|---|---|
| תרתי משמע (דקל) | 130 | 76 | 49 | 68 | 230 | 51 |
| הפוך על הפוך (דקל) | 61 | 175 | 20 | 69 | 231 | 66 |
| ידיעות ב' (דקל) | 30 | 53 | 46 | 56 | 140 | 21 |
| ידיעות ד' (דקל) | 16 | 35 | 53 | 62 | 144 | 21 |
| לאישה (דקל) | 43 | 51 | 64 | 83 | 191 | 18 |
| גלובס (ליאני) | **0** | 111 | 17 | **6** | 100 | 6 |

Read this as priors: in a Dekel puzzle, container ("X ב-Y") is the workhorse and
homophones are frequent; in a Liani puzzle expect charades + anagrams, essentially **zero
homophones and near-zero double definitions**.

### C.2 New mechanism vocabulary (how these communities phrase things)

**Double definition.** Yoram's crowd says "מילה משותפת"; here the labels are:
"מלה משותפת" (166), "מילה משותפת" (135), **"משמעות כפולה"** (150 — the standard label in
"הפוך על הפוך" and "תרתי משמע", often followed by a numbered list: "משמעות כפולה: 1) ...
2) ..."), "פירוש כפול", "פרשנות כפולה", "כפל משמעות", "דו משמעי", "תרתי משמע". Same
solving move; only the label differs. As with Yoram, short answers are the hotspot:
of 233 repeated 2-3-letter answers, ~40% are labeled some flavor of double definition
(יומ, רוח, הלל, יצא, זהב, בשר, שבת, טוב, אחד, רגע... all "מלה משותפת").

**Anagram.** Labels: "אנגרם", **"אנגרם של <fodder>"** (127 — the fodder is quoted
verbatim, e.g. מריחואנה → "אנגרם של האחרונים", פומפרניקל → "אנגרם של מלפפון יקר",
חברתהחשמל → "אנגרם של שמח להתרחב"), plus spelling variants אנגרמה / אנגראם / אנאגרם /
"טנגרם" (typo), and the Hebrew terms **"שיכול אותיות" / "סיכול אותיות"** (Liani's
preferred), "ערבוב אותיות", "בלבול אותיות", "שינוי סדר האותיות". The crowd polices
fodder-verbatim strictly ("ממתי עושים אנגרם למילה שלא מופיעה בהגדרה") — the §1.1
window-scan detector transfers 1:1 to these setters. Fodder is frequently a famous
NAME and the answer a phrase, or vice versa: הקאמרי↔אמריקה, סלוניקי↔סיליקון,
רובינא↔אורבני, פונטיאק↔"קנו פיאט", יואבקוטנר, יצחקתשובה, בנגביר, נדיהקומנצ.

**Reversal.** The near-universal formula is **"ההיפך: X"** (158). Clue-side/crowd
variants: "בהיפוך", "במהופך", "מהסוף", "מהסוף להתחלה", "משמאל לימין", "בקריאה
הפוכה/מאחור", "לקרוא הפוך", "מסתובב/לסובב", **"שבו"** (=returned; 6 in corpus, easy to
misread as "in which"), **"חזרו"** (plural returned; user-attested), "שידור חוזר" (שידורחוזר = "רוד יש"
backwards!), and for DOWN clues "מלמטה למעלה" / "עולה" / "בעליה" (ילדפלא = אלף+דלי
read upward; פסטרמה = "בתוך פסטה מר עולה"). Reversal fodder is very often a
celebrity name: הדסונ←נוסדה, דורמנ←נמרוד, בלושי←ישולב, מויאל←לאיום, לוק←(איריס) קול,
נדל←ל(נחל) דן, נחש←ש(שולה) חן.

**Coinage — "מחידושי <שם>" (setter-coined portmanteau).** Corpus-derived 2026-08-10
(user pointed at the marker; meaning derived from the 2 corpus instances):
the answer is an INVENTED blend, not a dictionary word or real phrase. A familiar
base word/phrase is warped by 1-2 letters (or a splice) so the result literally
encodes the definition side: אחימלחשק = אחים לנשק -> אחים לחשק ("חברותא בהתהוללות");
פקקיסטנ = פקיסטן + פקק ("מדינת הכבישים הסתומים"). The parenthetical credits the
coiner, exactly like (עפ"י שם).
SOLVING RULES: (1) lexicon membership must NOT veto the candidate - absence is
EXPECTED for coinages; (2) search for a base phrase/word within edit distance 1-2
of the enum whose warped form spells the definition; (3) the definition side reads
as a literal, often absurd, description of the pun; (4) proof = base + the exact
letter operation, both stated (prove.py: use concat/containment of the warped part,
never means() on the coined whole).

**Palindrome — a NEW named device** (absent from Yoram's corpus): crowd label
"פלינדרום" (19), also "נקרא משני הכיוונים", "נקראת אותו הדבר גם בכיוון ההפוך",
"מקדימה ומהסוף". Observed palindrome answers: דוד, אסא, סיס, סייס, קיק, וטו, רוטור,
וולוו, תוססות, מיצימ, מילימ, מיהימ, מישמשימ, נממנ, ימי, ירי, הלה, לעלעל, היההיה,
אבבא, מינונימ, נימינ. When a clue hints "בשני הכיוונים / הלוך ושוב", try a palindrome
fitting the enum.

**Homophone = phonetic charade (Dekel's signature).** The formula is **"נשמע: X Y"** —
the answer's SOUND is respelled as 2-3 small words, each clued separately. This differs
from Yoram (whole-phrase homophones): Dekel decomposes. Examples: כיבוש = "נשמע: קיא
בוש"; עכברוש = "אך בראש"; מאמינימ = "מע"מ מינים"; קצינ = "כת סין"; טמבור = "תם בור";
אלבטרוס = "על בת (דיאנה) רוס"; מציל = "מט סיל"; הודהלי = "(גדעון) הוד (סלבדור) דאלי".
Allowed sound-swaps (empirical): **ק↔כ, ט↔ת, שׂ↔ס, ש↔ס, א↔ע↔ה, ח↔כ, ו↔ב**, plus free
vowel/dagesh changes; the crowd grumbles but the setter is permissive. Clue-side flag:
Dekel writes **"(ש)" inside the clue** to mark the part taken by sound (analogous to
Yoram's "עפ"י השמיעה"). If a Dekel clue carries (ש), commit to a phonetic split.

**Container.** Formulas: "X בתוך Y" (366) and the terser **"X ב-Y"** (520): "רץ בתוך
קפה" = קרצפה; "טוב ב-מנה" = מנטובה; "לו בגבס" = גלובס. The crowd calls the ב-prefix
device **"הגדרת ב-"**: a clue word starting with ב is the container, what precedes goes
inside. Also "מקיף/מקיפה" (Y surrounds X), "סביב ל-", "אני מקיף את..." and nesting.
**"מחוץ ל-" is productive and means the OUTER word with the inner removed OR
wrapped around**: "בלם מחוץ ל-כת" = בלכתמ; "גלית מחוץ ל-לוב" = גלובלית; "מכים מחוץ
ל-ב(ית)" = מכבימ; "יש מחוץ לאות ב" = יבש; "נחה מחוץ לאות ב" = נבחה. Container fillers
recur: cars (רנו, ון, טנדר), cities/kibbutzim (ברן, ניס, וינה, קלן, יגור, דן, גת),
acronyms (ר"ג, ב"ש, ת"א, נ"ת, ס"ת, רס"מ, סנ"צ), and first names.

**Hidden.** Rare but labeled "רצף אותיות בהגדרה": ריסוס hides in "בפא**ריס וס**ופיה".
Dekel/Liani also use the **hidden-in-one-word notation "(ט)יפו(ס)"** — strip flanking
letters of a single clue word (יפו inside טיפוס; (א)לול; (ו)ספה; (שי)נוי; זבו(ב);
נפ(א)ל; ספי(נה); נתב(ג); (חו)מוס; (אב)יון). Treat "one long word in clue, short answer"
as an extraction candidate — same recipe as §1.7, plus single-word trimming.

**Deletion / substitution.** "בלי/ללא האות X", "פחות", "נעלם" ("2 נעלמים פג+גז" = פגז),
"רב אלוף בלי לוף" = רבא, "נתבע ללא העין" = נתב, "(ב)ית"ר בלי ב" = יתר, "מפלגת שינוי
ללא שי (ניצן)" = נוי, "ירמי קפלן איבד את הראש" = רמי. Letter substitution appears as
"X במקום Y" and niqqud-respelling ("ניקוד שונה: Johnny Depp = גְּוָונִי דַּף").

### C.3 Letter-level device inventory (extends §2.3)

**Gematria is heavier here than with Yoram** — the crowd writes it explicitly as
"letter (value)": ס (60), ח (8), ד (4), י (10), ג (3), ק (100), מ (40), נ (50), ל (30),
ר (200), ת (400 — "ת=400" in תבוסתנ), ה (5), ב (2), ט (9), כ (20), צ (90), plus year
gematria (תשפ"ו=786, תמ"ה=455, ל"ו צדיקים, ט"ו). Special doubles: **ס = both 60 and
אפס/0** ("ס (אפס) חב" = סחב; "דו ס (00)" = דוס); דו = 2/פעמיים ("דו (פעמיים) ק (100)"
= דוק).

**Bracketed-prefix decodes** — the community's way of glossing a single letter as a
word (same solving move as §2.3, new standard glosses):

| fragment | gloss | example |
|---|---|---|
| מ | (את) / (תוך) / (מושב/העיר) / (מספיק) / (מצוין - הציון) | מ(את) חם = מחם |
| כ | (מו) | כ(מו) בוי (ג'ורג') |
| ב | (ית) / (יום) / (תוך) / (בעל הבית) | ב(ית) ב-כר = כבר; חל ב(יום) ו' |
| ל | (מען) | ל(מען) עז = לעז |
| ו | (גם) / (ועוד, פלוס) | ו סט = וסט |
| ה | (הידיעה) / ha- | ה-גו (משחק סיני) = הגו |
| נ | (נכשל) — the failing grade | נ (נכשל) בתוך שופן |
| ט | (טוב) | ט bטריה = בקטריה... ט(וב) x17 |
| ס | (אפס) | פנ+ס, דל+ס |
| ק | (וף - the animal) / 100 | ק+בלן (עובד במקווה) |

**Small-word lexicon** (the "בן, בת, עיר, נהר" conventions — highest-frequency glosses):
אף=גם (13x); בר=בן (8x); בל=לא (8x); דו=פעמיים/2; די=רב/מספיק; קו=מסלול/גבול/מדיניות;
קן=בית; גו=פנים/משחק סיני/קפה גו; מש=זז; גל=מקל (גל מקל הכדורסלן!); יש=נמצא/מציאות;
קר=אדיש; בול=בדיוק; חת=פחד; שי=מתנה; אר=שטח; נס=דגל; יתר=שארית; מן=לחם (המדבר);
פן=צד; פרו=בעד; רע=עמית/חבר; עג=מסתובב; תו=סימן צליל; לית=אין (בארמית); סב=זקן;
צר=אויב; נץ=דורס; תן=טורף; שת=בנו של אדם; חט=שן; מד=בגד; כת=קבוצה; סט=מערכת;
לק=מטבע אלבני/לק ציפורניים; ין=מטבע; בס=דג/גיטרה; ריץ=מלון; פן=מייבש שיער.

**Days-of-week and grades as letters**: ימים ב' ג' ד' = בגד; ה-ו-ד = הוד; ב(יום) א'
מתחתן = באמתחתנ; כיתה ב'/ג'; נר ד' (רביעי בחנוכייה) = נרד.

**Acronym habits**: ר"ג=רמת גן, ב"ש=באר שבע, נ"ת=נמל תעופה, ני"ע, רו"ח, מ"פ, רס"ל,
מז"פ, ח"נ, ס"ת, א"ג.נ ("אדון גברת נכבדים"), וי"א="ויש אומרים", יא=ר"ת "יש אומרים",
ע"ה=ז"ל, מ"מ, אח"כ, מזל"ט, ת"ב=תשעה באב, ב"ב=בני ברק.

**Celebrity-first-name lexicon** (fragments standing for people — the single biggest
charade resource in this corpus): (ד"ר) נו, (עלמה) זק, (אילן) דר, (קפה) ג'ו / ג'ו
(עמר), (שלמה) בר, (שלום) אש, (הנסיכה) די, (המלכה) נור, יו (גרנט), אל (גור), סי
(היימן), עדי (אשכנזי), טל (ברמן), (ששי) גז, (קרן) פלס, (אדם) שוב, (נעלי) גלי, (עץ)
דום, (אבא) אבן, (עדי) רבן, (גנרל) לי, (גוש) דן, (יגאל) בשן, (לו) ריד, (שולה) חן,
(סלבדור) דאלי, (מאיר) שלו, (ריקי) גל, (ציפי) מור, (גולדי) הון, (קובי) אוז, (מטבע) ין,
(ויטמין) סי, (איריס) קול, (אייל) שני, (ואדי) ערה, (מס) בלו, (שרון) גל, (דיאנה) רוס,
ס. (יזהר), י.ל (פרץ), א.ד (גורדון), רן (ארז), רפי (גינת), מתן (חודורוב), גיל (ריבה),
אסי (עזר), פו (הדב), בוי (ג'ורג'), חמי (פרס), דני (רופ), טור (נועם), לאה (שבת),
(נעמי) פולני, (אביב) גפן, (בניין) קל, מיט (רומני), or (הנרי).

**Fragment selection (new device class)**: "חצי מהמילה חציר" = יר; "התחלת המילה
גנוסיד" = גנ; "מרכז המילה ערוגה" = רוג; "חצי ליטר" = לי; "חצי ליצ'י" = צ'י; "60%,
כלומר 3 מתוך 5 אותיות" = (חו)מוס; "ראש ח-טיבה" = ח. When a clue word resists synonym
decoding, try its head/tail/middle substring.

### C.4 Liani (גלובס) house style — read his explanations as a notation

Liani's crowd writes terse part-splits: **"פ-בלוב-ה"** (charade split with hyphens),
**"X # Y"** meaning X reads as Y backwards (מודה#[ה]דום, סבור#רובס, תומש#שמות,
מחליש#שילחם — 38 uses; also marks palindromes), and **[square brackets]** for glosses
or inserted letters (בילבי = בי[ל]בי; פנט[י]ום; "טל [ברמן]"). His charades lean on
single-letter flanks around a core word: י-רשת-ן, נ-ורדי-ם, ק-צרי-ן, ד-ישו-ן — i.e.
**answer = letter + word + letter** is a standard Liani skeleton; when solving his
grid, peel one letter off each end and look for a clued word inside. He uses אנגרם
liberally (111) but almost never quotes fodder, no homophones at all, and few double
definitions; cultural range is more current-affairs/business (globes audience:
בנגביר, יצחקתשובה, חרבותברזל, ליסינג, פוליסה, מע"מ).

### C.5 Answer-space statistics (crosswordese)

Across ALL corpora (8,249 clues, 6,836 distinct answers), 1,102 answers repeat 2+
times (see `solver/crosswordese.json`, 2,515 clue instances ≈ 30% of all slots). Top
repeaters: יומ (8), לשמ (7), יפו (7), רבע (6), לגו (6), גו/הלל/בו/אפס/בדו/לבנ/נורדי/
לוב/רוח/ראש/ימי (5 each). The repeat population is dominated by 2-4-letter fillers —
exactly the double-definition/letter-play slots — so the frequency list is a strong
prior: **before solving a short slot, check crosswordese.json for candidates matching
the crossing letters.** Repeats also recur WITH the same mechanism (לגו is always
ל+גו, בחנ is always ב+חן, סחב is always ס(אפס)+חב), so cache mechanism along with
answer.

### C.6 What transfers between setters — and what does not

**Universal (use everywhere):**
1. Anagram-fodder-verbatim: the fodder appears contiguously in the clue; window-scan
   with final-letter normalization works for all three setters.
2. Double definition owns the [3]-slots (except Liani).
3. "ההיפך של a clued word/name" reversals, including down-clue "עולה" reversals.
4. Gematria letters, acronym decoding, bracketed-prefix letters (מ=את, ב=בית, כ=כמו).
5. Container with ב- prefix; "מחוץ ל-" as the inverse.
6. No final letterforms; loose כתיב חסר; loose foreign transliteration.
7. Celebrity first/last-name fragments as charade parts (the shared Israeli-culture
   lexicon overlaps heavily: שולה חן, אבא אבן, פו הדב, דיאנה ריג/רוס-era names).

**Dekel Beno-specific:** phonetic-charade homophones with the (ש) clue-flag; the
"משמעות כפולה" label; palindromes as a routine device; heavier gematria; "ר. N מאוזן"
cross-references (one long phrase split across entries, exactly like Yoram's "ר' N
אופקי" — device transfers, format differs).

**Liani-specific:** letter+word+letter charade skeleton; # reversal notation; no
homophones (never propose one in a Globes puzzle); business/news vocabulary.

**Yoram HaRoeh-specific (do NOT expect elsewhere):** contributor credits (עפ"י X);
(מ)/(ח) spelling flags as printed markers; long culture-pun clues quoting songs/
sketches with no letter mechanics; the loose "two wordplays, no definition" style.
The secondary-corpus setters are stricter: nearly every clue has a clean definition
half + one mechanical half, so for them the strict verification gate of §4.10 can be
tightened (reject candidates whose leftover words do not define).


## External-guide audit additions (2026-08-10)
Diffed against blog.ravmilim.co.il tips, Maariv (Liani), he.wikipedia תשבץ היגיון,
ynet, higayonbarie, FXP. Items below were MISSING from this playbook:

1. **אותיות עוקבות**: indicators עוקבות/לפי הסדר/בסדר → answer contains an
   alphabet-consecutive letter run (דורשת = דו+רשת: ר,ש,ת; פרלמן = פר+למן: ל,מ,נ).
2. **Foreign-word phonetics**: (ל), באנגליה, בצרפת → sound out clue words in
   English/French ("תהיה טוב" = Be good → ביגוד; להפסיד = to lose → טולוז).
3. **Notation tails**: (כ"מ)/(כ"ח) = spelling variants; (ש"כ) = one clue word serves
   BOTH definitions; (ס) = slang answer; (מו"ש) = inspired by another clue in this
   puzzle; (דו"ש) = two-step: transform the definition first, then solve it
   ("הפוליטיקאית" → לבני → ידלבנימ).
4. **"בדיוק להפך" = container-role inversion**, not letter reversal: the ostensible
   container becomes the contained (ברוק->קורב inside מים = מקורבימ).
5. **"X, למשל"** = definition-by-example: answer is X's CATEGORY (חרטום, למשל → בירה).
6. **לסירוגין** = interleave letters of two words (rare, reserved word).
7. **"X או Y"** = both collocate with the answer on the same side (מדד או חום →
   יולי/אוגוסט); beware common-word multi-answer clues (אין שם יפה אחר → דבר).
8. **Letter glosses to ADD**: ו=תלוי (shape), ג=אישור (גימלים), ל=לומד (learner's L),
   ר=לקיש (ריש), ע=עין/הלל (ע. הלל), פ=פה, צ=צדיק, א=שור, ב=מיכאל (ב. מיכאל).
9. **Reversal indicators to ADD**: bare שב and bare סב (סב also glosses as זקן -
   disambiguate by syntax).
10. **Digits in clue → letter spelling**: printed numbers become gematria letter
    pairs inside the answer (15 → ט"ו in טורבנימ; 14 → י"ד in אירביד).
11. **Service-letter misreading (מש"ה וכל"ב)**: a clue word starting with ל/ב/כ/מ/ש/ו
    may be preposition+word or one whole word (לשון = ל+שון; לסוטות = ל+סוטות).
    Try both parses before synonym lookup.


**MORPHOLOGICAL AGREEMENT (learned from a 2026-08-14 miss).** The definition side fixes
the answer's person/gender/tense, and the wordplay must produce THAT form. Live miss:
"כשהיא תספר לי אל תכחישי - השיבי" (7) - the engine proved הודי(imperative)+עני = הודיעני
and committed at 0.85; gold was תודיעני (תודיע = "she will inform", matching "כשהיא...").
The wordplay executed perfectly; the FORM was wrong. RULE: before committing, restate the
definition side as a sentence and check the candidate can grammatically replace it
(person, gender, number, tense). A candidate that only differs from a valid answer in its
first letter is a red flag for exactly this error.
