#!/usr/bin/env python3
"""A/B: free-form JSON prompting vs typed (JSON-schema) replies through OpenRouter.

The question this answers: does moving the hosted app's model calls from "reply
with one fenced json block" (regex + JSON.parse, provider-default sampling) to a
strict JSON-schema response_format with pinned sampling and mechanical
guardrails change (a) how often a reply is unusable, (b) whether a run
reproduces, and (c) precision on the answers the model commits to.

Arms (same clues, same context, same model):
  freeform    the production contract as of 2026-09: fenced json block, regex
              extraction, provider-default temperature, the page's
              verifyClaims() gate (length / anagram letters / word join).
  structured  response_format=json_schema strict, temperature 0 + seed,
              provider.require_parameters, schema validation, full guard_clue().

Gold: the three demo puzzles shipped with the app (docs/solve/data/demo/*).
Their engine.json entries tagged `committed` were checked against the
published keys (DAILY.md, 2026-07-31 / 08-07 / 08-14), so those answers are
the gold; the model solves every one of those clues blind (no crossings,
unless --crossings, which reveals the letters other gold answers put in the
slot, the situation a reader is usually in when they ask for a hint).

Scoring reuses evals/run_eval.py's policy: PRECISION over committed answers is
the headline, then COVERAGE, YIELD, suggestion hit-rate. Added here:
  parse_fail    replies with no usable JSON
  schema_fail   replies that parsed but violate the schema (structured arm)
  fell_back     structured requests the provider refused (retried free-form)
  guard_down    committed claims the guard downgraded (and how many of those
                were in fact wrong - the guard's catch rate)
  determinism   share of clues whose (answer, tier) is identical across all
                repeats of the same arm

Usage:
  OPENROUTER_API_KEY=... python3 evals/or_structured_eval.py [--model M] [--repeats 2]
      [--arms freeform,structured] [--limit N] [--crossings] [--workers 4]
  python3 evals/or_structured_eval.py --dry-run     # builds every request, sends none

Runs land in evals/runs/or_structured/<date>_<model>.json with a _summary.md.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'solver'))
from or_client import ORClient, CLUE_SCHEMA, guard_clue, norm, load_shipped_lexicon  # noqa: E402

DATA = os.path.join(ROOT, 'docs', 'solve', 'data')
OUT = os.path.join(ROOT, 'evals', 'runs', 'or_structured')
HEB_DIR = {'across': 'מאוזן', 'down': 'מאונך'}
SPLIT = re.compile(r'[\s,.;:!?()"\'\-־]+')


# ---------------------------------------------------------------- data
def load_demos():
    demos = json.load(open(os.path.join(DATA, 'demos.json')))
    out = []
    for d in demos:
        base = os.path.join(DATA, 'demo', d['id'])
        puz = json.load(open(os.path.join(base, 'puzzle.json')))
        eng = json.load(open(os.path.join(base, 'engine.json')))
        if isinstance(eng, dict):
            eng = eng.get('entries', [])
        gold = {(e['clue_number'], e['direction']): norm(e['answer'])
                for e in eng if e.get('tier') == 'committed' and norm(e.get('answer'))}
        out.append({'id': d['id'], 'date': puz.get('date') or d['id'], 'puzzle': puz, 'gold': gold})
    return out


def clue_list(puz):
    """puzzle.json carries clues either as a flat list or as {across:[..], down:[..]}
    with num/clue/enum (the transcription shape)."""
    c = puz['clues']
    if isinstance(c, list):
        return c
    out = []
    for d in ('across', 'down'):
        for x in c.get(d, []):
            out.append({'clue_number': x.get('clue_number', x.get('num')), 'direction': d,
                        'clue': x['clue'], 'enum': x['enum']})
    return out


def slot_key(n, d):
    return f'{n}-{d}'


def crossing_pattern(puz, gold, n, d):
    """Letters other gold answers put into this slot; '?' elsewhere."""
    slots = puz['slots']
    cells = slots[slot_key(n, d)]
    board = {}
    for (gn, gd), ans in gold.items():
        if (gn, gd) == (n, d):
            continue
        for (r, c), ch in zip(slots[slot_key(gn, gd)], ans):
            board[(r, c)] = ch
    return ''.join(board.get((r, c), '?') for r, c in cells)


def load_context():
    subs = json.load(open(os.path.join(DATA, 'substitutions.json')))
    amb = json.load(open(os.path.join(DATA, 'ambiguities.json')))
    playbook = open(os.path.join(DATA, 'playbook.txt'), encoding='utf-8').read()
    return subs, amb, playbook


HEBSENSE = {'common_word': 'מילה מן המילון', 'given_name': 'שם פרטי', 'surname': 'שם משפחה',
            'role_noun': 'תפקיד/פועל וגם שם', 'song': 'שם שיר', 'song_word': 'מילה מתוך שיר',
            'artist': 'זמר/להקה', 'politician': 'פוליטיקאי/ת', 'place': 'מקום',
            'bible': 'דמות מקראית', 'answer': 'הופיעה כתשובה בתשבצים'}


def pattern_search(lexicon, pat, cap=30):
    if not lexicon or '?' not in pat or pat.count('?') == len(pat):
        return []
    L = len(pat)
    out = []
    for w in lexicon:
        if len(w) != L:
            continue
        if all(p == '?' or p == ch for p, ch in zip(pat, w)):
            out.append(w)
            if len(out) >= cap:
                break
    return sorted(out)


def build_prompt(clue, enum, direction, pat, ctx, lexicon, arm):
    """Port of the /solve/ page's crackClue prompt. The two arms share every line
    of context; only the reply-format instructions differ."""
    subs, amb, playbook = ctx
    cands = pattern_search(lexicon, pat)
    subs_hits, senses = [], []
    for w in SPLIT.split(clue):
        nw = norm(w)
        if len(nw) < 2:
            continue
        if nw in subs.get('fwd', {}):
            subs_hits.append(nw + '~' + '/'.join(x[0] for x in subs['fwd'][nw][:3]))
        if nw in amb:
            senses.append(nw + ': ' + ', '.join(HEBSENSE.get(s, s) for s in amb[nw]['senses']))
    lines = [f'אתה פותר תשבץ היגיון עברי. {playbook}',
             f'ההגדרה: "{clue}" ({",".join(map(str, enum))}) - {HEB_DIR[direction]}.',
             f'אותיות ידועות מהצלבות (מימין לשמאל, ?=לא ידוע): {pat}']
    if cands:
        lines.append('מועמדים אמיתיים מהמילון שתואמים לתבנית: ' + ', '.join(cands))
    if subs_hits:
        lines.append('תחליפים מוכרים של המחברים: ' + ' | '.join(subs_hits))
    if senses:
        lines.append('מילים דו-משמעיות: ' + ' | '.join(senses))
    lines.append('כלל: עדיף להשאיר ריק מלנחש. tier="committed" רק אם כל אות מוסברת; אחרת "suggestion" או "blank".')
    if arm == 'freeform':
        lines.append('השב אך ורק בבלוק json:\n```json\n'
                     '{"answer":"ללארווחים","tier":"committed","confidence":0.9,"mechanism":"anagram",'
                     '"fodder":"אם אנגרם: המילים מההגדרה","words":["אם רב-מילים","סדר","נכון"],'
                     '"definition_side":"start","hint_fragment":"מילה מההגדרה ומה היא מייצגת",'
                     '"explanation":"הסבר קצר"}\n```')
    else:
        lines.append('השב בעצם JSON התואם לסכמה בלבד. fodder ריק אם אין אנגרם; words = פיצול התשובה '
                     'למילים לפי המספור; confidence = הסתברות בין 0 ל-1.')
    return '\n'.join(lines)


# ---------------------------------------------------------------- page-parity gate
def verify_claims_page(e, enum):
    """The page's verifyClaims(): what the freeform arm gets today."""
    a = norm(e.get('answer'))
    if not a:
        return False
    if enum and sum(enum) != len(a):
        return False
    if e.get('mechanism') == 'anagram' and e.get('fodder'):
        if sorted(norm(e['fodder'])) != sorted(a):
            return False
    if enum and len(enum) > 1 and e.get('words'):
        if ''.join(norm(w) for w in e['words']) != a:
            return False
    return True


# ---------------------------------------------------------------- one call
def run_one(client, job, ctx, lexicon, dry):
    arm = job['arm']
    prompt = build_prompt(job['clue'], job['enum'], job['direction'], job['pattern'], ctx, lexicon, arm)
    messages = [{'role': 'user', 'content': prompt}]
    rec = {k: job[k] for k in ('puzzle', 'clue_number', 'direction', 'arm', 'rep', 'clue', 'enum', 'pattern')}
    rec['gold'] = job['gold']
    if dry:
        body = client.body(messages, CLUE_SCHEMA if arm == 'structured' else None,
                           deterministic=(arm == 'structured'))
        rec.update(dry_request=body, answer='', tier='blank')
        return rec
    if arm == 'structured':
        r = client.chat(messages, schema=CLUE_SCHEMA, deterministic=True)
    else:
        r = client.chat(messages, schema=None, deterministic=False)
    rec.update(status=r.status, latency=round(r.latency, 2), usage=r.usage, provider=r.provider,
               finish_reason=r.finish_reason, structured=r.structured, fell_back=r.fell_back,
               problems=r.problems, raw=r.text[:1200])
    e = r.data if isinstance(r.data, dict) else None
    rec['parse_fail'] = e is None
    rec['schema_fail'] = bool(e is not None and arm == 'structured' and
                              [p for p in r.problems if p.startswith('$')])
    if e is None:
        e = {'answer': '', 'tier': 'blank'}
    if arm == 'structured':
        e = guard_clue(e, job['enum'], job['pattern'], job['clue'], lexicon)
        rec['guard'] = e['guard']
        rec['tier_raw'] = e['tier_raw']
    else:
        rec['tier_raw'] = e.get('tier') or 'blank'
        if e.get('tier') == 'committed' and not verify_claims_page(e, job['enum']):
            e['tier'] = 'suggestion'
        # what the full guard WOULD have done, for the comparison table
        g = guard_clue(dict(e, tier=rec['tier_raw']), job['enum'], job['pattern'], job['clue'], lexicon)
        rec['guard'] = g['guard']
    rec['answer'] = e.get('answer') or ''
    rec['tier'] = e.get('tier') if e.get('tier') in ('committed', 'suggestion', 'blank') else 'suggestion'
    rec['confidence'] = e.get('confidence')
    rec['mechanism'] = e.get('mechanism')
    rec['explanation'] = (e.get('explanation') or '')[:400]
    rec['correct'] = norm(rec['answer']) == job['gold'] if norm(rec['answer']) else None
    return rec


# ---------------------------------------------------------------- scoring
def score(records, arms, repeats):
    out = {}
    for arm in arms:
        rs = [r for r in records if r['arm'] == arm]
        n = len(rs)
        S = Counter()
        wrong = []
        for r in rs:
            S['calls'] += 1
            S['parse_fail'] += bool(r.get('parse_fail'))
            S['schema_fail'] += bool(r.get('schema_fail'))
            S['fell_back'] += bool(r.get('fell_back'))
            S['http_err'] += bool(r.get('status') and r['status'] != 200)
            S['tok_in'] += (r.get('usage') or {}).get('prompt_tokens', 0)
            S['tok_out'] += (r.get('usage') or {}).get('completion_tokens', 0)
            S['latency'] += r.get('latency', 0)
            t = r['tier']
            S[t] += 1
            if t == 'committed':
                S['commit_ok'] += bool(r['correct'])
                if not r['correct']:
                    wrong.append({'puzzle': r['puzzle'], 'key': [r['clue_number'], r['direction']],
                                  'clue': r['clue'], 'got': r['answer'], 'gold': r['gold'],
                                  'explanation': r.get('explanation')})
            elif t == 'suggestion':
                S['sugg_ok'] += bool(r['correct'])
            if r.get('tier_raw') == 'committed' and t != 'committed':
                S['guard_down'] += 1
                S['guard_down_wrong'] += (not r['correct'])
            elif arm == 'freeform' and r.get('tier_raw') == 'committed' and r.get('guard') \
                    and t == 'committed':
                S['guard_would_down'] += 1
                S['guard_would_down_wrong'] += (not r['correct'])
        # determinism across repeats
        by_clue = defaultdict(list)
        for r in rs:
            by_clue[(r['puzzle'], r['clue_number'], r['direction'])].append((norm(r['answer']), r['tier']))
        full = [v for v in by_clue.values() if len(v) == repeats]
        same = sum(1 for v in full if len(set(v)) == 1)
        same_ans = sum(1 for v in full if len({a for a, _ in v}) == 1)
        d = {
            'calls': n,
            'parse_fail': S['parse_fail'], 'schema_fail': S['schema_fail'], 'fell_back': S['fell_back'],
            'http_err': S['http_err'],
            'committed': S['committed'], 'commit_ok': S['commit_ok'],
            'suggestion': S['suggestion'], 'sugg_ok': S['sugg_ok'], 'blank': S['blank'],
            'precision': S['commit_ok'] / S['committed'] if S['committed'] else None,
            'coverage': S['committed'] / n if n else None,
            'yield': S['commit_ok'] / n if n else None,
            'sugg_hit': S['sugg_ok'] / S['suggestion'] if S['suggestion'] else None,
            'guard_down': S['guard_down'], 'guard_down_wrong': S['guard_down_wrong'],
            'guard_would_down': S['guard_would_down'], 'guard_would_down_wrong': S['guard_would_down_wrong'],
            'determinism': same / len(full) if full else None,
            'determinism_answer': same_ans / len(full) if full else None,
            'mean_latency': S['latency'] / n if n else None,
            'tok_in': S['tok_in'], 'tok_out': S['tok_out'],
            'wrong_commitments': wrong,
        }
        out[arm] = d
    return out


def pct(x):
    return '-' if x is None else f'{x:.0%}'


def summary_md(meta, sc):
    arms = list(sc)
    rows = [('calls', lambda d: d['calls']),
            ('parse failures', lambda d: d['parse_fail']),
            ('schema violations', lambda d: d['schema_fail']),
            ('structured refused (fell back)', lambda d: d['fell_back']),
            ('HTTP errors', lambda d: d['http_err']),
            ('PRECISION (committed)', lambda d: f"{d['commit_ok']}/{d['committed']} = {pct(d['precision'])}"),
            ('COVERAGE', lambda d: pct(d['coverage'])),
            ('YIELD', lambda d: pct(d['yield'])),
            ('suggestion hit-rate', lambda d: f"{d['sugg_ok']}/{d['suggestion']} = {pct(d['sugg_hit'])}"),
            ('blanks', lambda d: d['blank']),
            ('guard downgraded (of which wrong)', lambda d: f"{d['guard_down']} ({d['guard_down_wrong']})"),
            ('guard WOULD downgrade (of which wrong)', lambda d: f"{d['guard_would_down']} ({d['guard_would_down_wrong']})"),
            ('determinism (answer+tier)', lambda d: pct(d['determinism'])),
            ('determinism (answer only)', lambda d: pct(d['determinism_answer'])),
            ('mean latency s', lambda d: '-' if d['mean_latency'] is None else f"{d['mean_latency']:.1f}"),
            ('tokens in / out', lambda d: f"{d['tok_in']} / {d['tok_out']}")]
    L = [f"# Typed replies via OpenRouter: {meta['model']}", '',
         f"{meta['date']} - {meta['clues']} gold clues x {meta['repeats']} repeats, "
         f"crossings {'on' if meta['crossings'] else 'off (blind)'}", '',
         '| metric | ' + ' | '.join(arms) + ' |', '|---|' + '---|' * len(arms)]
    for name, f in rows:
        L.append(f'| {name} | ' + ' | '.join(str(f(sc[a])) for a in arms) + ' |')
    for a in arms:
        w = sc[a]['wrong_commitments']
        if w:
            L += ['', f'## Wrong commitments - {a}', '']
            for x in w:
                L.append(f"- {x['puzzle']} {x['key'][0]} {x['key'][1]}: got {x['got']} gold {x['gold']} - {x['clue']}")
    return '\n'.join(L) + '\n'


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', default=os.environ.get('OR_MODEL', 'anthropic/claude-sonnet-4.5'))
    ap.add_argument('--arms', default='freeform,structured')
    ap.add_argument('--repeats', type=int, default=2)
    ap.add_argument('--limit', type=int, default=0, help='clues per puzzle (0 = all gold clues)')
    ap.add_argument('--crossings', action='store_true', help='reveal letters from other gold answers')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    arms = [x for x in a.arms.split(',') if x]
    for x in arms:
        if x not in ('freeform', 'structured'):
            sys.exit(f'unknown arm {x}')
    if not a.dry_run and not os.environ.get('OPENROUTER_API_KEY'):
        sys.exit('OPENROUTER_API_KEY is not set (use --dry-run to build the requests without sending)')

    demos = load_demos()
    ctx = load_context()
    lexicon = load_shipped_lexicon(ROOT)
    jobs = []
    for d in demos:
        keys = sorted(d['gold'], key=lambda k: (k[1], k[0]))
        if a.limit:
            keys = keys[:a.limit]
        clues = {(c['clue_number'], c['direction']): c for c in clue_list(d['puzzle'])}
        for n, dirn in keys:
            c = clues[(n, dirn)]
            pat = crossing_pattern(d['puzzle'], d['gold'], n, dirn) if a.crossings \
                else '?' * sum(c['enum'])
            for arm in arms:
                for rep in range(a.repeats):
                    jobs.append({'puzzle': d['id'], 'clue_number': n, 'direction': dirn,
                                 'clue': c['clue'], 'enum': c['enum'], 'pattern': pat,
                                 'gold': d['gold'][(n, dirn)], 'arm': arm, 'rep': rep})
    n_clues = len({(j['puzzle'], j['clue_number'], j['direction']) for j in jobs})
    print(f'{len(demos)} puzzles, {n_clues} gold clues, {len(jobs)} calls '
          f'({",".join(arms)} x {a.repeats}) model {a.model}' + (' [DRY RUN]' if a.dry_run else ''))

    client = ORClient(model=a.model)
    t0 = time.time()
    records = []
    with ThreadPoolExecutor(max_workers=1 if a.dry_run else a.workers) as ex:
        for i, rec in enumerate(ex.map(lambda j: run_one(client, j, ctx, lexicon, a.dry_run), jobs), 1):
            records.append(rec)
            if not a.dry_run and (i % 10 == 0 or i == len(jobs)):
                print(f'  {i}/{len(jobs)}  {time.time()-t0:.0f}s', flush=True)

    meta = {'date': dt.date.today().isoformat(), 'model': a.model, 'arms': arms, 'repeats': a.repeats,
            'clues': n_clues, 'crossings': a.crossings, 'dry_run': a.dry_run,
            'gold_source': 'docs/solve/data/demo/*/engine.json committed entries',
            'seed': client.seed, 'temperature': client.temperature}
    sc = score(records, arms, a.repeats)
    os.makedirs(a.out, exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '-', a.model.lower()).strip('-')
    stem = os.path.join(a.out, f"{meta['date']}_{slug}" + ('_dry' if a.dry_run else ''))
    json.dump({'meta': meta, 'scores': sc, 'records': records},
              open(stem + '.json', 'w'), ensure_ascii=False, indent=1)
    md = summary_md(meta, sc)
    open(stem + '_summary.md', 'w').write(md)
    print()
    print(md)
    print('written:', stem + '.json')
    if a.dry_run:
        j = next(r for r in records if r['arm'] == 'structured') if 'structured' in arms else records[0]
        print('sample request body (structured arm):' if 'structured' in arms else 'sample request body:')
        print(json.dumps(j['dry_request'], ensure_ascii=False, indent=1)[:2500])


if __name__ == '__main__':
    main()
