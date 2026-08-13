#!/usr/bin/env python3
"""Definition-span classification for cryptic clues.

WHY: a cryptic clue's definition sits ENTIRELY at one end (SOLVE_PROTOCOL.md already
states this as the human-solver heuristic, and RESEARCH.md's 2026-08-06 entry on
"What Makes Cryptic Crosswords Challenging for LLMs?" (arXiv 2412.09012) found that
giving a model the correct definition span measurably improves solve accuracy in
English cryptics). This is lever queue item 2 in DAILY.md ("never tried here") — the
structural claim was documented but nothing in this repo actually classified which end
before today.

APPROACH: rule-based, not learned. RESEARCH.md already judged a trained span classifier
a poor fit (no Hebrew embedding space tuned for this genre, and 8,249 clues is thin to
train from scratch). Instead: a clue end that contains a WORDPLAY INDICATOR word
(solver/indicators.json's empirically-collected anagram/reversal/container/hidden/
homophone/deletion vocab, mined from this exact corpus) is almost certainly the
wordplay side, so the opposite end is hypothesized as the definition. This needs no
new data — it reuses indicator lists already validated against this setter's clues.
Ties / no indicator found fall back to PLAYBOOK.md's noted convention that definitions
in this genre usually run 1-3 words, so the SHORTER edge is the weak-confidence guess.

This module only PROPOSES a span; it never asserts an answer. Feeding the wordplay span
into solver/candidates.py restricts fodder windows to the side that is actually wordplay,
which is the intended integration (see `--restrict` in candidates.py).

CLI:
  python3 solver/defspan.py clue "<text>"     # prints the classification + rationale
  python3 solver/defspan.py selftest
"""
import sys, os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Mechanisms whose indicator vocabulary marks the WORDPLAY side of the clue.
# (double_definition is deliberately excluded: it does not mark one side as wordplay,
# it marks the whole clue as two overlapping definitions.)
WORDPLAY_MECHANISMS = ['anagram', 'reversal', 'container', 'hidden', 'homophone', 'deletion']

CREDIT_RE = re.compile(r'\((עפ["\']?י|מ|ח)[^)]*\)')


def strip_credit(text):
    return CREDIT_RE.sub(' ', text or '')


_INDICATORS = None


def indicators():
    """{mechanism: [word-tuples]}, each indicator pre-split into its own tokens so
    multi-word indicators (e.g. 'כפי ששמענו') can be matched as a token run, not a
    naive substring (which would false-hit on unrelated words sharing a prefix —
    'hidden' even lists bare prefix letters מ/ב that must never substring-match)."""
    global _INDICATORS
    if _INDICATORS is None:
        d = json.load(open(os.path.join(HERE, 'indicators.json')))
        out = {}
        for mech in WORDPLAY_MECHANISMS:
            out[mech] = [tuple(w.split()) for w in d.get(mech, [])]
        _INDICATORS = out
    return _INDICATORS


def tokenize(clue_text):
    return re.findall(r'[א-ת"\'׳״]+', strip_credit(clue_text))


def _token_run_positions(tokens, phrase):
    """Every start index i where tokens[i:i+len(phrase)] == phrase (exact token match)."""
    n = len(phrase)
    return [i for i in range(len(tokens) - n + 1) if tuple(tokens[i:i + n]) == phrase]


def find_indicators(tokens):
    """Every (mechanism, indicator_words, start_index) hit in the clue, whole-token only."""
    hits = []
    for mech, phrases in indicators().items():
        for phrase in phrases:
            if not phrase or not phrase[0]:
                continue
            for i in _token_run_positions(tokens, phrase):
                hits.append((mech, phrase, i))
    return hits


def classify(clue_text):
    """Return {definition_end, confidence, rationale, wordplay_span, definition_span}.
    definition_end in {'front', 'back', 'ambiguous'}."""
    tokens = tokenize(clue_text)
    n = len(tokens)
    if n < 2:
        return {'definition_end': 'ambiguous', 'confidence': 0.0,
                'rationale': 'clue too short to split', 'wordplay_span': clue_text,
                'definition_span': clue_text}

    hits = find_indicators(tokens)
    # assign each hit to exactly one side by its token-span CENTER — using separate
    # "front" / "back" distance thresholds (as an earlier version did) let a single
    # indicator sitting near the midpoint satisfy both at once and get miscounted as
    # "found on both ends"; a center-vs-midpoint comparison partitions cleanly.
    mid = n / 2.0
    front_hits, back_hits = [], []
    for (m, p, i) in hits:
        center = i + len(p) / 2.0
        (front_hits if center < mid else back_hits).append((m, p, i))

    if front_hits and not back_hits:
        # indicator lives in the front -> front is wordplay, definition is the back
        m, p, i = max(front_hits, key=lambda h: len(h[1]))  # longest (most specific) indicator
        wp_end = i + len(p)
        wp_end = max(wp_end, len(front_hits and [h[2] + len(h[1]) for h in front_hits] or [wp_end]))
        # wordplay side = all front tokens up to the furthest indicator hit; definition = rest
        wp_tokens = tokens[:max(h[2] + len(h[1]) for h in front_hits)]
        def_tokens = tokens[len(wp_tokens):]
        if not def_tokens:
            return {'definition_end': 'ambiguous', 'confidence': 0.3,
                    'rationale': f'indicator "{" ".join(p)}" ({m}) fills the whole clue',
                    'wordplay_span': clue_text, 'definition_span': clue_text}
        return {'definition_end': 'back', 'confidence': 0.75,
                'rationale': f'wordplay indicator "{" ".join(p)}" ({m}) in front half',
                'wordplay_span': ' '.join(wp_tokens), 'definition_span': ' '.join(def_tokens)}

    if back_hits and not front_hits:
        m, p, i = max(back_hits, key=lambda h: len(h[1]))
        wp_start = min(h[2] for h in back_hits)
        wp_tokens = tokens[wp_start:]
        def_tokens = tokens[:wp_start]
        if not def_tokens:
            return {'definition_end': 'ambiguous', 'confidence': 0.3,
                    'rationale': f'indicator "{" ".join(p)}" ({m}) fills the whole clue',
                    'wordplay_span': clue_text, 'definition_span': clue_text}
        return {'definition_end': 'front', 'confidence': 0.75,
                'rationale': f'wordplay indicator "{" ".join(p)}" ({m}) in back half',
                'wordplay_span': ' '.join(wp_tokens), 'definition_span': ' '.join(def_tokens)}

    if front_hits and back_hits:
        # indicators on both sides: no reliable single wordplay side (could be a
        # charade of two devices, or a coincidental indicator word used as ordinary
        # surface vocabulary). Do not guess; this is exactly the ambiguous case.
        return {'definition_end': 'ambiguous', 'confidence': 0.2,
                'rationale': 'wordplay indicators found on both ends', 'wordplay_span': clue_text,
                'definition_span': clue_text}

    # no indicator anywhere: fall back to PLAYBOOK.md's noted convention that
    # definitions run short (1-3 words) — guess the shorter edge is the definition,
    # low confidence, never enough to restrict candidate generation on its own.
    if n <= 3:
        return {'definition_end': 'ambiguous', 'confidence': 0.1,
                'rationale': 'no indicator; clue too short to split confidently',
                'wordplay_span': clue_text, 'definition_span': clue_text}
    k = 1 if n <= 5 else 2
    front_short = k
    back_short = n - k
    # Two candidate splits (definition=front k words, or definition=back k words);
    # without any other signal we cannot choose between them, so report both as the
    # ambiguous ends of a low-confidence guess rather than assert one.
    return {'definition_end': 'ambiguous', 'confidence': 0.15,
            'rationale': 'no wordplay indicator found; PLAYBOOK convention (short edge) '
                         'is not enough alone to pick a side',
            'wordplay_span': clue_text, 'definition_span': clue_text}


def wordplay_text(clue_text):
    """Convenience for candidates.py: the substring hypothesized to hold the wordplay,
    or the full (credit-stripped) clue when classify() is not confident."""
    c = classify(clue_text)
    if c['confidence'] >= 0.7:
        return c['wordplay_span']
    return strip_credit(clue_text)


# ---------------------------------------------------------------------------
def selftest():
    """Synthetic examples only — no dev/eval gold data, same discipline as
    candidates.py's selftest."""
    ok = True

    print('--- anagram indicator at the FRONT marks front=wordplay, back=definition ---')
    c = classify('מבולבל שלום עכשיו כלב גדול')
    print(f'  {c}')
    good = c['definition_end'] == 'back' and 'שלום' not in c['wordplay_span'].split()[:0]
    ok &= (c['definition_end'] == 'back')
    print(f'  definition_end == back: {c["definition_end"] == "back"} (expected True)')

    print('--- reversal indicator at the BACK marks back=wordplay, front=definition ---')
    c = classify('כלב גדול מאוד רץ חוזר')
    print(f'  {c}')
    ok &= (c['definition_end'] == 'front')
    print(f'  definition_end == front: {c["definition_end"] == "front"} (expected True)')

    print('--- container indicator mid-clue splits correctly ---')
    c = classify('שם יפה בתוך מילה ארוכה מאוד')
    print(f'  {c}')
    ok &= (c['definition_end'] in ('front', 'back'))
    print(f'  produced a definite side (not ambiguous): {c["definition_end"] != "ambiguous"} (expected True)')

    print('--- no indicator anywhere -> ambiguous, low confidence, never overconfident ---')
    c = classify('ילד קטן אוהב תפוזים מתוקים')
    print(f'  {c}')
    ok &= (c['definition_end'] == 'ambiguous' and c['confidence'] < 0.3)
    print(f'  ambiguous + low confidence: {c["definition_end"] == "ambiguous" and c["confidence"] < 0.3} (expected True)')

    print('--- indicators on both ends -> ambiguous, not a guess ---')
    c = classify('מבולבל מאוד וגם חוזר לאחור')
    print(f'  {c}')
    ok &= (c['definition_end'] == 'ambiguous')
    print(f'  ambiguous when both ends carry indicators: {c["definition_end"] == "ambiguous"} (expected True)')

    print('--- credit note is stripped before classification (not treated as clue text) ---')
    c = classify('מבולבל שלום עכשיו (עפ"י דני כהן)')
    print(f'  {c}')
    ok &= ('דני' not in c['wordplay_span'] and 'דני' not in c['definition_span'])
    print(f'  credit words absent from both spans: '
          f'{"דני" not in c["wordplay_span"] and "דני" not in c["definition_span"]} (expected True)')

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'clue':
        text = sys.argv[2]
        print(json.dumps(classify(text), ensure_ascii=False, indent=2))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
