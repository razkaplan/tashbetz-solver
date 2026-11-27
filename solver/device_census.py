#!/usr/bin/env python3
"""Device-frequency census over the FULL answered corpus (52 puzzles, 1,457 clues),
using crowd EXPLANATIONS only -- no clue text, no image transcription needed.

WHY: every candidate-generation mechanism this project has built (anagram, hidden,
reversal, container, homograph, double-definition, substitution, gematria,
abbreviation, homophone, ...) has been measured almost exclusively on single
28-clue dev puzzles (PLAN_V2.md: "one clue = 1.8 points, differences under ~10
points are noise"). Across dozens of independent measurements, nearly every
mechanical generator has landed at or near 0 marginal recall on whichever
28-clue sample it was tried on, and each null result has been treated as its
own small-n finding. This script asks a different, higher-powered question
first: across ALL 1,457 answered clues (not one puzzle), how often does each
device actually occur at all, going only by what the crowd's own solving
commentary says was used? If a device is genuinely rare corpus-wide, a 28-clue
sample finding ~0 hits for it is not a surprising miss, it is the expected
outcome of its low base rate -- which redirects effort size, not blame, onto
future generator-building decisions.

Classification is RULE-BASED on `solver/indicators.json`'s own
`explanation_labels.yoram_haroeh` vocabulary (crowd-commentary markers this
project already curated, e.g. "אנגרם" literally means "this is an anagram"),
not a new invented keyword list, so it does not quietly introduce its own
unvalidated taxonomy. A clue can match multiple devices (crowd explanations
often chain two steps, e.g. an anagram landing inside a container). Clues
matching none of the markers fall into `unlabeled` -- almost certainly mostly
charades/substitutions/culture-definition clues, whose crowd explanations are
free-form fragment breakdowns with no single naming convention, not evidence
those clues have no wordplay.

This is a MEASUREMENT of the crowd's labeling habits, not a new solving
mechanism, and it does not touch clue text or any held-out answer's
correctness -- same safety profile as PLAYBOOK.md/indicators.json themselves,
which were built from this exact same explanation corpus including dev/eval
rows.

Usage:
  python3 solver/device_census.py census [data/answers/answers_parsed.json]
  python3 solver/device_census.py selftest
"""
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MARKERS = {
    'anagram': ['אנגרם'],
    'homophone': ['נשמע'],
    'double_definition': ['מילה משותפת', 'משפט משותף', 'משמעות כפולה', 'פירוש כפול'],
    'reversal': ['להפך זה', 'ההיפך:', 'ההפך של'],
    'hidden': ['רצף אותיות'],
    'container': ['בתוך'],
    'palindrome': ['פלינדרום'],
    'deletion': ['בלי ', 'ללא ', 'חסר '],
    'gematria': ['גימטריה', 'גימטרייה'],
}
# order matters only for selftest readability; classification itself checks all keys.
DEVICE_ORDER = ['anagram', 'homophone', 'double_definition', 'reversal', 'hidden',
                'container', 'palindrome', 'deletion', 'gematria']


def classify(explanation_text):
    """Return the sorted list of device labels whose marker substring appears
    anywhere in the (concatenated) explanation text. Pure substring match --
    deliberately simple and auditable, not a hidden second heuristic."""
    hits = []
    for dev in DEVICE_ORDER:
        if any(m in explanation_text for m in MARKERS[dev]):
            hits.append(dev)
    return hits


def census(path):
    data = json.load(open(path))
    total = 0
    no_explanation = 0
    dev_counts = Counter()
    multi = 0
    unlabeled = 0
    unlabeled_examples = []
    per_puzzle_unlabeled = Counter()
    per_puzzle_total = Counter()
    for puzzle in data:
        pdate = puzzle.get('puzzle_date', '?')
        for c in puzzle['clues']:
            total += 1
            per_puzzle_total[pdate] += 1
            expls = c.get('explanations') or []
            if not expls:
                no_explanation += 1
                continue
            text = ' \n '.join(expls)
            labels = classify(text)
            if not labels:
                unlabeled += 1
                per_puzzle_unlabeled[pdate] += 1
                if len(unlabeled_examples) < 15:
                    unlabeled_examples.append((pdate, c['clue_number'], c['direction'],
                                                c['answer'], expls[0][:80]))
            else:
                if len(labels) > 1:
                    multi += 1
                for d in labels:
                    dev_counts[d] += 1
    return {
        'total': total,
        'no_explanation': no_explanation,
        'unlabeled': unlabeled,
        'multi_label': multi,
        'device_counts': dict(dev_counts),
        'unlabeled_examples': unlabeled_examples,
        'per_puzzle_unlabeled_rate': {
            d: (per_puzzle_unlabeled[d], per_puzzle_total[d]) for d in per_puzzle_total
        },
    }


def selftest():
    """Synthetic fixtures only -- no real clue/answer leaves this file, same
    discipline candidates.py/lexicon.py enforce."""
    ok = True
    cases = [
        ('אנגרם של פחות יין', ['anagram']),
        ('נשמע ריח אדנים', ['homophone']),
        ('מילה משותפת לשתי המשמעויות', ['double_definition']),
        ('להפך זה ישן', ['reversal']),
        ('רצף אותיות בתוך המילה הארוכה', ['hidden', 'container']),
        ('ד בריא מת', []),  # charade fragments, no named marker -> unlabeled
        ('אנגרם של X, והתוצאה בתוך Y', ['anagram', 'container']),
    ]
    for text, expected in cases:
        got = classify(text)
        match = got == expected
        print(f'  {text!r} -> {got} (expected {expected}): {"OK" if match else "FAIL"}')
        ok &= match
    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    elif cmd == 'census':
        path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'data/answers/answers_parsed.json')
        res = census(path)
        total = res['total']
        print(f"total clues: {total}")
        print(f"no explanation at all: {res['no_explanation']} ({res['no_explanation']/total:.1%})")
        print(f"unlabeled (no device marker matched): {res['unlabeled']} ({res['unlabeled']/total:.1%})")
        print(f"multi-label clues (>=2 devices matched): {res['multi_label']}")
        print("\ndevice frequency (clue may match more than one; % of ALL clues):")
        for d in DEVICE_ORDER:
            n = res['device_counts'].get(d, 0)
            print(f"  {d:20s} {n:5d}  ({n/total:.1%})")
        print("\nsample unlabeled clues (for manual spot-check):")
        for pdate, num, direction, answer, expl in res['unlabeled_examples']:
            print(f"  {pdate} {num} {direction} {answer}: {expl}")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
