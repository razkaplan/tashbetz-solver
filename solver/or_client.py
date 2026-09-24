#!/usr/bin/env python3
"""OpenRouter client with TYPED replies and mechanical guardrails.

Why this exists. The hosted /solve/ app and the eval harness used to ask the
model for "one fenced json block", regex the block out of free prose, and
JSON.parse it. That is three failure modes before the answer is even looked
at: no block, a block with extra keys or wrong types, a block that parses but
says `tier: "sure"`. This module replaces the free-form contract with a
JSON-schema contract (OpenRouter structured outputs, `strict: true`), pins the
sampling (temperature 0, fixed seed) so a run reproduces, and then runs the
reply through the same mechanical checks the engine applies to itself
(`solver/prove.py` essentials): the schema makes the reply well-typed, the
guard makes it well-founded. A committed answer that fails a check is
downgraded to a suggestion, never dropped, so the reader still sees it.

Two schemas ship: CLUE_SCHEMA (crack one clue) and TRANSCRIBE_SCHEMA (digitize
a puzzle image). Both use only the JSON-schema subset every structured-output
provider accepts (type, enum, properties, required, items,
additionalProperties, description), so `provider.require_parameters` can route
to any model that honours `response_format` without a per-provider special case.

Usage:
    from or_client import ORClient, CLUE_SCHEMA, guard_clue
    c = ORClient(model='anthropic/claude-sonnet-4.5')      # key from OPENROUTER_API_KEY
    r = c.chat(messages, schema=CLUE_SCHEMA)                # r.data is validated dict
    e = guard_clue(r.data, enum=[3, 4], pattern='???????', clue='...', lexicon=LEX)

Nothing here imports the corpus; the lexicon guard takes whatever set the
caller has (the shipped docs/solve/data/lexicon.txt works in a fresh clone).
"""
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass, field

try:
    import requests
except ImportError:  # the guard and schemas are usable without the network layer
    requests = None

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_MODEL = 'anthropic/claude-sonnet-4.5'
DEFAULT_SEED = 7
COMMIT_THRESHOLD = 0.75            # same bar as evals/run_eval.py

FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


# ---------------------------------------------------------------- schemas
MECHANISMS = ['anagram', 'reversal', 'container', 'hidden', 'charade', 'double',
              'homophone', 'culture', 'portmanteau', 'definition', 'unknown']

CLUE_SCHEMA = {
    'name': 'tashbetz_clue',
    'strict': True,
    'schema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['answer', 'tier', 'confidence', 'mechanism', 'fodder', 'words',
                     'definition_side', 'hint_fragment', 'explanation'],
        'properties': {
            'answer': {'type': 'string',
                       'description': 'The answer in Hebrew letters, spaces between words. '
                                      'Empty string when tier is blank.'},
            'tier': {'type': 'string', 'enum': ['committed', 'suggestion', 'blank'],
                     'description': 'committed only when every letter is explained by the '
                                    'wordplay and the definition fits.'},
            'confidence': {'type': 'number',
                           'description': 'Probability in [0,1] that the answer is correct.'},
            'mechanism': {'type': 'string', 'enum': MECHANISMS},
            'fodder': {'type': 'string',
                       'description': 'For anagram: the exact words of the clue whose letters '
                                      'are rearranged. Otherwise empty.'},
            'words': {'type': 'array', 'items': {'type': 'string'},
                      'description': 'The answer split into words in enumeration order. '
                                     'One element for a single-word answer.'},
            'definition_side': {'type': 'string', 'enum': ['start', 'end', 'unknown']},
            'hint_fragment': {'type': 'string',
                              'description': 'One clue word and what it stands for, without '
                                             'revealing the answer.'},
            'explanation': {'type': 'string',
                            'description': 'Short Hebrew explanation of definition and wordplay.'},
        },
    },
}

TRANSCRIBE_SCHEMA = {
    'name': 'tashbetz_transcription',
    'strict': True,
    'schema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['grid', 'across', 'down'],
        'properties': {
            'grid': {'type': 'array', 'items': {'type': 'string'},
                     'description': "Rows top to bottom; '.' white, '#' black; index 0 is the "
                                    'RIGHTMOST cell.'},
            'across': {'type': 'array', 'items': {'$ref': '#/$defs/clue'}},
            'down': {'type': 'array', 'items': {'$ref': '#/$defs/clue'}},
        },
        '$defs': {
            'clue': {
                'type': 'object',
                'additionalProperties': False,
                'required': ['num', 'clue', 'enum'],
                'properties': {
                    'num': {'type': 'integer'},
                    'clue': {'type': 'string'},
                    'enum': {'type': 'array', 'items': {'type': 'integer'}},
                },
            },
        },
    },
}


# ---------------------------------------------------------------- validator
def validate(obj, schema, path='$'):
    """Minimal JSON-schema check for the subset the schemas above use.
    Returns a list of problems (empty = valid). No third-party dependency, so the
    browser port and this file agree on what 'valid' means."""
    probs = []
    root = schema
    def walk(o, s, p, root):
        if '$ref' in s:
            ref = s['$ref']
            if not ref.startswith('#/'):
                probs.append(f'{p}: unsupported $ref {ref}'); return
            t = root
            for part in ref[2:].split('/'):
                t = t[part]
            walk(o, t, p, root); return
        t = s.get('type')
        if t == 'object':
            if not isinstance(o, dict):
                probs.append(f'{p}: expected object, got {type(o).__name__}'); return
            props = s.get('properties', {})
            for k in s.get('required', []):
                if k not in o:
                    probs.append(f'{p}.{k}: missing')
            if s.get('additionalProperties') is False:
                for k in o:
                    if k not in props:
                        probs.append(f'{p}.{k}: unexpected key')
            for k, sub in props.items():
                if k in o:
                    walk(o[k], sub, f'{p}.{k}', root)
        elif t == 'array':
            if not isinstance(o, list):
                probs.append(f'{p}: expected array, got {type(o).__name__}'); return
            for i, x in enumerate(o):
                walk(x, s.get('items', {}), f'{p}[{i}]', root)
        elif t == 'string':
            if not isinstance(o, str):
                probs.append(f'{p}: expected string, got {type(o).__name__}'); return
            if 'enum' in s and o not in s['enum']:
                probs.append(f'{p}: {o!r} not in {s["enum"]}')
        elif t == 'integer':
            if isinstance(o, bool) or not isinstance(o, int):
                probs.append(f'{p}: expected integer, got {o!r}')
        elif t == 'number':
            if isinstance(o, bool) or not isinstance(o, (int, float)):
                probs.append(f'{p}: expected number, got {o!r}')
        elif t == 'boolean':
            if not isinstance(o, bool):
                probs.append(f'{p}: expected boolean, got {o!r}')
    walk(obj, schema.get('schema', schema), path, schema.get('schema', schema))
    return probs


def parse_json(text):
    """The legacy free-form contract: first fenced json block, else the widest
    bracketed span. Raises ValueError when nothing parses."""
    m = re.search(r'```json\s*([\s\S]*?)```', text or '') or \
        re.search(r'([\[{][\s\S]*[\]}])', text or '')
    if not m:
        raise ValueError('no JSON in model reply')
    return json.loads(m.group(1))


PREFIXES = 'והבלמכש'


def in_lexicon(lexicon, w):
    """Word, or word minus one clitic prefix (ו/ה/ב/ל/מ/כ/ש), is known."""
    if w in lexicon:
        return True
    return len(w) > 2 and w[0] in PREFIXES and w[1:] in lexicon


def anagram_window(clue, answer):
    """True if some contiguous run of clue words has exactly the answer's letters."""
    toks = [norm(t) for t in re.split(r'[\s,.;:!?()"\'\-־]+', clue or '')]
    toks = [t for t in toks if t]
    answer = norm(answer)
    want = Counter(answer)
    L = len(answer)
    for i in range(len(toks)):
        acc = ''
        for j in range(i, len(toks)):
            acc += toks[j]
            if len(acc) > L:
                break
            if len(acc) == L and Counter(acc) == want:
                return True
    return False


# ---------------------------------------------------------------- guardrails
def guard_clue(e, enum, pattern=None, clue=None, lexicon=None):
    """Mechanical checks on one clue reply. Mutates and returns `e`, adding
    e['guard'] (list of failed checks) and e['tier_raw'] (what the model said).
    A committed answer that fails any check becomes a suggestion; a blank stays
    blank. The checks are the ones an honest solver can be held to:
      length      letters == sum(enum)
      words       the declared word split joins to the answer and matches enum
      anagram     fodder letters == answer letters AND some contiguous run of
                  clue words has exactly those letters (the anagrams are literal)
      crossings   every known letter of the slot pattern agrees
      lexicon     a single-word answer is a word we know, allowing one clitic
                  prefix (portmanteaus exempt; multi-word answers are not checked)
      echo        the answer is not simply a word lifted from the clue
      confidence  self-reported confidence clears the commit bar
    """
    if not isinstance(e, dict):
        e = {'answer': '', 'tier': 'blank'}
    e.setdefault('answer', '')
    e['tier_raw'] = e.get('tier') or 'blank'
    fails = []
    a = norm(e.get('answer'))
    if not a:
        e['tier'] = 'blank'
        e['guard'] = []
        return e
    if enum and sum(enum) != len(a):
        fails.append(f'length {len(a)} != enum {sum(enum)}')
    words = [norm(w) for w in (e.get('words') or []) if norm(w)]
    if words:
        if ''.join(words) != a:
            fails.append('words do not join to answer')
        elif enum and len(enum) > 1 and [len(w) for w in words] != list(enum):
            fails.append(f'word lengths {[len(w) for w in words]} != enum {list(enum)}')
    elif enum and len(enum) > 1:
        fails.append('multi-word answer with no word split')
    if e.get('mechanism') == 'anagram':
        f = norm(e.get('fodder'))
        if not f:
            fails.append('anagram without fodder')
        elif Counter(f) != Counter(a):
            fails.append('anagram fodder letters != answer letters')
        elif clue is not None and not anagram_window(clue, a):
            # the setter's anagrams are literal: some contiguous run of clue words
            # carries exactly the answer's letters
            fails.append('no contiguous window of the clue anagrams to the answer')
    if pattern:
        pat = ''.join(ch if ch == '?' else norm(ch) or '?' for ch in pattern)
        if len(pat) == len(a):
            for i, ch in enumerate(pat):
                if ch != '?' and ch != a[i]:
                    fails.append(f'crossing letter {i} is {ch}, answer has {a[i]}'); break
        else:
            fails.append(f'pattern length {len(pat)} != answer {len(a)}')
    if lexicon is not None and e.get('mechanism') != 'portmanteau' and len(words) <= 1:
        # single words only: a multi-word answer is checked by its crossings and
        # word split, and the lexicon lacks many prefixed forms (הפורענות)
        if not in_lexicon(lexicon, a):
            fails.append('single word not in lexicon')
    if clue is not None:
        cw = {norm(w) for w in re.split(r'[\s,.;:!?()"\'\-־]+', clue)}
        if a in cw:
            fails.append('answer is a word of the clue')
    conf = e.get('confidence')
    if isinstance(conf, (int, float)) and not isinstance(conf, bool) and conf < COMMIT_THRESHOLD:
        fails.append(f'confidence {conf} below commit bar')
    e['guard'] = fails
    if e['tier_raw'] == 'committed' and fails:
        e['tier'] = 'suggestion'
    elif e['tier_raw'] not in ('committed', 'suggestion', 'blank'):
        e['tier'] = 'suggestion'
    else:
        e['tier'] = e['tier_raw']
    return e


# ---------------------------------------------------------------- client
@dataclass
class Reply:
    text: str = ''
    data: object = None
    ok: bool = False              # parsed AND schema-valid
    structured: bool = False      # was response_format honoured on this call
    fell_back: bool = False       # structured refused -> free-form retry
    problems: list = field(default_factory=list)
    status: int = 0
    latency: float = 0.0
    usage: dict = field(default_factory=dict)
    finish_reason: str = ''
    provider: str = ''
    request: dict = field(default_factory=dict)


class ORClient:
    def __init__(self, model=DEFAULT_MODEL, api_key=None, seed=DEFAULT_SEED, temperature=0.0,
                 timeout=180, referer='https://tashbetz.gtmascode.dev', title='Tashbetz Solver'):
        self.model = model
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY', '')
        self.seed = seed
        self.temperature = temperature
        self.timeout = timeout
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json',
                        'HTTP-Referer': referer, 'X-Title': title}

    def body(self, messages, schema=None, max_tokens=2500, deterministic=True):
        """The request body, exposed so a dry run can show exactly what is sent."""
        b = {'model': self.model, 'messages': messages, 'max_tokens': max_tokens}
        if deterministic:
            b['temperature'] = self.temperature
            b['seed'] = self.seed
        if schema:
            b['response_format'] = {'type': 'json_schema', 'json_schema': schema}
            # only route to providers that honour response_format; otherwise a
            # provider silently ignores it and we are back to free prose
            b['provider'] = {'require_parameters': True}
        return b

    def chat(self, messages, schema=None, max_tokens=2500, deterministic=True, fallback=True):
        """One completion. With `schema`, the reply is parsed as JSON and validated;
        if the provider refuses the structured request (4xx) and `fallback` is on,
        the same messages are re-sent free-form and the fenced block is extracted."""
        if requests is None:
            raise RuntimeError('pip install requests')
        if not self.api_key:
            raise RuntimeError('OPENROUTER_API_KEY is not set')
        body = self.body(messages, schema, max_tokens, deterministic)
        r = self._post(body)
        r.structured = bool(schema)
        if schema and r.status >= 400 and r.status < 500 and fallback:
            r2 = self._post(self.body(messages, None, max_tokens, deterministic))
            r2.fell_back, r2.structured = True, False
            r2.problems.insert(0, f'structured request refused ({r.status}): {r.text[:160]}')
            r = r2
        if r.status != 200:
            r.problems.append(f'HTTP {r.status}: {r.text[:200]}')
            return r
        try:
            r.data = json.loads(r.text) if r.structured else parse_json(r.text)
        except ValueError as ex:
            # a structured reply that is not bare JSON: try the lenient path once
            try:
                r.data = parse_json(r.text)
                r.problems.append('structured reply was not bare JSON')
            except ValueError:
                r.problems.append(f'unparseable reply: {ex}')
                return r
        if schema:
            r.problems += validate(r.data, schema)
        r.ok = not [p for p in r.problems if not p.startswith('structured reply was not bare')]
        return r

    def _post(self, body):
        rep = Reply(request=body)
        t0 = time.time()
        try:
            resp = requests.post(OPENROUTER_URL, headers=self.headers, json=body, timeout=self.timeout)
        except requests.RequestException as ex:
            rep.problems.append(f'network: {ex}')
            rep.latency = time.time() - t0
            return rep
        rep.latency = time.time() - t0
        rep.status = resp.status_code
        if resp.status_code != 200:
            rep.text = resp.text
            return rep
        d = resp.json()
        ch = (d.get('choices') or [{}])[0]
        rep.text = (ch.get('message') or {}).get('content') or ''
        rep.finish_reason = ch.get('finish_reason') or ''
        rep.usage = d.get('usage') or {}
        rep.provider = d.get('provider') or ''
        if 'error' in d:
            rep.problems.append(f'api error: {d["error"]}')
        return rep


def load_shipped_lexicon(root=None):
    """The lexicon the hosted app ships (committed, so it exists in a fresh clone)."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, 'docs', 'solve', 'data', 'lexicon.txt')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return {norm(w) for w in f if w.strip()}


if __name__ == '__main__':
    import sys
    print(json.dumps(CLUE_SCHEMA if 'transcribe' not in sys.argv else TRANSCRIBE_SCHEMA,
                     ensure_ascii=False, indent=1))
