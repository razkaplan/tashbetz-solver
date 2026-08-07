#!/usr/bin/env python3
"""Tashbetz solving-assistant server — local, stdlib-only.

Upload a crossword photo/PDF -> the engine digitizes it (pixel grid extraction +
claude-CLI vision transcription) -> an interactive RTL board where you solve WITH
the engine: graded hints, mechanical answer checks, and a proof reveal when a clue
falls. Every session is logged so the solver learns from real human solving
(solver/learn_from_sessions.py folds it back into the corpus).

Design constraints, deliberate:
- stdlib HTTP only (no Flask): nothing to install.
- The LLM is the locally-authenticated `claude` CLI, so no API keys are handled here.
- Precision-first survives in the UI: the engine only ever asserts tiers it can defend
  ("committed" carries an executable proof; "suggestion" is visibly humble).

Run:  python3 app/server.py   ->  http://localhost:8765
"""
import json, os, re, sys, subprocess, threading, uuid, base64, time
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'app')
UPLOADS = os.path.join(APP, 'uploads')
PUZZLES = os.path.join(APP, 'puzzles')
SESSIONS = os.path.join(ROOT, 'data', 'sessions')
for d in (UPLOADS, PUZZLES, SESSIONS):
    os.makedirs(d, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, 'solver'))
import grid_tools  # slots / validate / check_fill

FIN = str.maketrans('ךםןףץ', 'כמנפצ')
def norm(s): return re.sub(r'[^א-ת]', '', s or '').translate(FIN)

MODEL = os.environ.get('TASH_MODEL', 'sonnet')
JOBS = {}   # job_id -> {status, step, result, error}

# ---------------------------------------------------------------- claude CLI
def claude_json(prompt, timeout=900, model=MODEL):
    """Headless claude call that must return a fenced JSON block; parsed or raises."""
    out = subprocess.run(
        ['claude', '-p', prompt, '--model', model,
         '--allowedTools', 'Read,Glob,Grep,Bash(python3:*)'],
        capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    txt = out.stdout
    m = re.search(r'```json\s*(.*?)```', txt, re.S) or re.search(r'(\[.*\]|\{.*\})', txt, re.S)
    if not m:
        raise RuntimeError('claude returned no JSON: ' + txt[-400:])
    return json.loads(m.group(1))

# ---------------------------------------------------------------- digitize
def pixel_grid(img_path):
    """Haaretz-layout pixel extraction; returns rows or None if implausible."""
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(img_path).convert('L'); a = np.array(im)
        sys.path.insert(0, os.path.join(ROOT, 'scraper'))
        from extract_grid import find_bbox, classify
        bbox = find_bbox(a, a.shape[1])
        means = classify(a, bbox)
        rows = [''.join('#' if means[r][c] < 128 else '.' for c in range(11)) for r in range(15)]
        # sanity: some black, mostly white, 180-degree symmetric-ish
        blacks = sum(r.count('#') for r in rows)
        if not (4 <= blacks <= 60):
            return None
        return rows
    except Exception:
        return None

def digitize_job(job_id, img_path):
    j = JOBS[job_id]
    try:
        j['step'] = 'קורא את הרשת מהתמונה'
        rows = pixel_grid(img_path)
        j['step'] = 'מתמלל את ההגדרות (זה לוקח דקה-שתיים)'
        grid_note = ('A pixel scan suggests this black/white grid pattern '
                     f'(row 0 = top, index 0 = RIGHTMOST cell): {json.dumps(rows)}. '
                     'Verify it against the image and correct if needed. '
                     if rows else
                     'Also transcribe the grid: 11 wide x 15 tall unless clearly otherwise; ')
        prompt = f"""Read the image at {img_path}. It contains a Hebrew logic crossword (תשבץ היגיון).
If the page holds several puzzles, use the one titled תשבץ היגיון (byline יורם הרועה) and ignore the rest.
Transcribe every clue: number, direction (אופקי=across, אנכי=down), full Hebrew text, and the
trailing parenthesized enumeration as a list of ints ordered so enum[0] is the FIRST word of the
answer (the paper's RTL rendering sometimes prints the tuple reversed — if unsure, keep printed
order; it is validated later). Rejoin words hyphen-broken across lines.
{grid_note}
Then VALIDATE yourself by running:
  python3 solver/grid_tools.py validate /tmp/_g.json /tmp/_c.json
after writing your grid as {{"grid": [...]}} to /tmp/_g.json and your clues to /tmp/_c.json.
Iterate until it prints OK (fix grid cells or enum order as needed).
Finally output ONE fenced json block:
```json
{{"grid": ["...15 rows of . and #..."], "across": [{{"num":1,"clue":"...","enum":[..]}}], "down": [...], "validation": "OK or the remaining problems"}}
```"""
        data = claude_json(prompt, timeout=1200)
        grid = data['grid']
        clues = {'across': data.get('across', []), 'down': data.get('down', [])}
        problems = grid_tools.validate(grid, clues)
        pid = job_id
        pdir = os.path.join(PUZZLES, pid); os.makedirs(pdir, exist_ok=True)
        slots = {f'{n}-{d}': cells for (n, d), cells in grid_tools.slots(grid).items()}
        puzzle = {'id': pid, 'grid': grid, 'clues': clues, 'slots': slots,
                  'validation': 'OK' if not problems else problems,
                  'image': '/uploads/' + os.path.basename(img_path)}
        json.dump(puzzle, open(os.path.join(pdir, 'puzzle.json'), 'w'), ensure_ascii=False)
        j.update(status='done', result=puzzle)
        # quietly start the engine solving in the background so hints are ready
        threading.Thread(target=solve_job, args=(pid,), daemon=True).start()
    except Exception as e:
        j.update(status='error', error=str(e)[:500])

# ---------------------------------------------------------------- engine solve
def solve_job(pid):
    pdir = os.path.join(PUZZLES, pid)
    marker = os.path.join(pdir, 'engine.status')
    open(marker, 'w').write('running')
    try:
        prompt = f"""Solve the Hebrew logic crossword described in {pdir}/puzzle.json (read it).
Follow solver/SOLVE_PROTOCOL.md strictly — precision first: a wrong answer is worse than a blank.
Use the tools: python3 solver/lexicon.py, solver/homographs.py, solver/substitutions.py,
solver/prove.py, solver/retrieve.py, solver/wiki.py. Never consult crossword-solution sites;
never search clue text verbatim. Every "committed" answer must pass solver/prove.py (put the
passing proof in explanation). Multi-word commits require a passing word_order assertion.
Unspaced answers, no final letter forms, exact enum length.
Output ONE fenced json block: a list with one entry per clue:
```json
[{{"clue_number":1,"direction":"across","answer":"...","tier":"committed|suggestion|blank","explanation":"...","confidence":0.0,"mechanism":"anagram|reversal|container|hidden|charade|double|culture|other","definition_side":"start|end|unknown","hint_fragment":"one clue word and what it stands for, or ''"}}]
```"""
        data = claude_json(prompt, timeout=2400)
        json.dump(data, open(os.path.join(pdir, 'engine.json'), 'w'), ensure_ascii=False)
        open(marker, 'w').write('done')
    except Exception as e:
        msg = str(e)
        tag = 'auth' if ('401' in msg or 'authenticate' in msg.lower()) else 'error: ' + msg[:300]
        open(marker, 'w').write(tag)

def engine_entry(pid, num, dirn):
    p = os.path.join(PUZZLES, pid, 'engine.json')
    if not os.path.exists(p):
        return None
    for e in json.load(open(p)):
        if e.get('clue_number') == num and e.get('direction') == dirn:
            return e
    return None

# ---------------------------------------------------------------- hints (graded)
def make_hint(pid, num, dirn, level, clue_text):
    eng = engine_entry(pid, num, dirn)
    status = open(os.path.join(PUZZLES, pid, 'engine.status')).read() \
        if os.path.exists(os.path.join(PUZZLES, pid, 'engine.status')) else 'idle'
    if level == 1:
        # mechanism scent — deterministic homograph/indicator scan, plus engine's read if ready
        out = subprocess.run(['python3', 'solver/homographs.py', 'scan', clue_text],
                             capture_output=True, text=True, cwd=ROOT).stdout.strip()
        mech = (eng or {}).get('mechanism')
        txt = 'מילים דו-משמעיות בהגדרה:\n' + (out or '(לא נמצאו)')
        if mech and mech != 'other':
            heb = {'anagram': 'אנגרם', 'reversal': 'היפוך', 'container': 'הכלה (מילה בתוך מילה)',
                   'hidden': 'מילה מוסתרת ברצף', 'charade': 'שרשור חלקים', 'double': 'מילה משותפת',
                   'culture': 'רפרנס תרבותי'}.get(mech, mech)
            txt += f'\n\nהמנגנון כנראה: {heb}'
        return txt
    if level == 2:
        side = (eng or {}).get('definition_side', 'unknown')
        if side in ('start', 'end'):
            heb = 'בתחילת ההגדרה' if side == 'start' else 'בסוף ההגדרה'
            return f'החלק המגדיר (הפירוש הישיר) נמצא {heb}; השאר הוא משחק המילים.'
        return ('בתשבץ היגיון ההגדרה הישירה יושבת באחד הקצוות. '
                'נסו לקרוא את המשפט פעם מכל כיוון.' if status != 'done'
                else 'המנוע לא הצליח לזהות בוודאות את צד ההגדרה כאן.')
    if level == 3:
        frag = (eng or {}).get('hint_fragment')
        if frag:
            return 'רמז לחלק מהדרך: ' + frag
        # deterministic fallback: substitutions on clue words
        best = []
        for w in re.split(r'[\s,.;:!?()"\'\-־]+', clue_text):
            if len(norm(w)) < 2: continue
            out = subprocess.run(['python3', 'solver/substitutions.py', norm(w)],
                                 capture_output=True, text=True, cwd=ROOT).stdout
            if 'can be written as' in out:
                best.append(out.strip().splitlines()[0] + ' -> ' +
                            out.strip().splitlines()[1].strip())
            if len(best) >= 2: break
        return ('תחליפים מוכרים של המחברים:\n' + '\n'.join(best)) if best else \
            'אין רמז זמין עדיין — המנוע עוד עובד על ההגדרה הזאת.'
    if level == 4:
        a = norm((eng or {}).get('answer', ''))
        if a and (eng or {}).get('tier') in ('committed', 'suggestion'):
            return f'האות הראשונה: {a[0]}   (ואורך: {len(a)} אותיות)'
        return 'למנוע אין עדיין תשובה מבוססת כאן. נסו הצלבות ונחזור לזה.'
    if level == 5:
        if not eng or eng.get('tier') == 'blank' or not norm(eng.get('answer', '')):
            return 'המנוע נשאר כאן ריק בכוונה — אין לו תשובה שהוא מוכן להתחייב עליה. אתם לבד בזה :)'
        badge = 'מוכחת' if eng.get('tier') == 'committed' else 'השערה בלבד — לא מוכחת'
        return (f"התשובה ({badge}): {eng['answer']}\n\nההסבר:\n{eng.get('explanation','')}")
    return '...'

# ---------------------------------------------------------------- answer check
def check_answer(pid, num, dirn, answer, board):
    puzzle = json.load(open(os.path.join(PUZZLES, pid, 'puzzle.json')))
    key = f'{num}-{dirn}'
    cells = puzzle['slots'].get(key)
    a = norm(answer)
    if not cells:
        return {'ok': False, 'why': 'slot not found'}
    if len(a) != len(cells):
        return {'ok': False, 'why': f'אורך לא מתאים: {len(a)} אותיות במקום {len(cells)}'}
    conflicts = []
    for (r, c), ch in zip(cells, a):
        cur = (board or {}).get(f'{r},{c}', '')
        if cur and cur != ch:
            conflicts.append(f'שורה {r+1}: מתנגש עם אות קיימת {cur}')
    verdicts = {'in_lexicon': None, 'engine_agrees': None}
    out = subprocess.run(['python3', 'solver/lexicon.py', 'pattern', a],
                         capture_output=True, text=True, cwd=ROOT).stdout
    verdicts['in_lexicon'] = a in [norm(x) for x in out.split()]
    eng = engine_entry(pid, num, dirn)
    if eng and norm(eng.get('answer', '')):
        verdicts['engine_agrees'] = (norm(eng['answer']) == a)
    return {'ok': not conflicts, 'conflicts': conflicts, **verdicts}

# ---------------------------------------------------------------- http plumbing
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def _file(self, path, ctype):
        try:
            b = open(path, 'rb').read()
        except OSError:
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p in ('/', '/index.html'):
            return self._file(os.path.join(APP, 'static', 'index.html'), 'text/html; charset=utf-8')
        if p.startswith('/uploads/'):
            return self._file(os.path.join(UPLOADS, os.path.basename(p)), 'image/png')
        if p.startswith('/api/job/'):
            j = JOBS.get(p.rsplit('/', 1)[1])
            return self._json(j or {'status': 'unknown'})
        if p.startswith('/api/puzzle/'):
            pid = p.rsplit('/', 1)[1]
            f = os.path.join(PUZZLES, pid, 'puzzle.json')
            if os.path.exists(f):
                d = json.load(open(f))
                st = os.path.join(PUZZLES, pid, 'engine.status')
                if not os.path.exists(st):   # first open: engine starts solving quietly
                    threading.Thread(target=solve_job, args=(pid,), daemon=True).start()
                    d['engine_status'] = 'running'
                else:
                    d['engine_status'] = open(st).read()
                bf = os.path.join(PUZZLES, pid, 'board.json')
                d['board'] = json.load(open(bf)) if os.path.exists(bf) else {}
                return self._json(d)
            return self._json({'error': 'not found'}, 404)
        self.send_response(404); self.end_headers()

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        p = self.path
        if p == '/api/upload':
            raw = base64.b64decode(body['data_b64'])
            uid = uuid.uuid4().hex[:10]
            name = body.get('name', 'up.png').lower()
            ext = 'pdf' if name.endswith('.pdf') else 'png'
            fp = os.path.join(UPLOADS, f'{uid}.{ext}')
            open(fp, 'wb').write(raw)
            if ext == 'pdf':
                subprocess.run(['pdftoppm', '-png', '-r', '150', '-f', '1', '-l', '1',
                                fp, fp[:-4]], check=True)
                fp = fp[:-4] + '-1.png'
            return self._json({'upload_id': uid, 'image': '/uploads/' + os.path.basename(fp),
                               'path': fp})
        if p == '/api/digitize':
            job = uuid.uuid4().hex[:10]
            JOBS[job] = {'status': 'running', 'step': 'מתחיל...'}
            threading.Thread(target=digitize_job, args=(job, body['path']), daemon=True).start()
            return self._json({'job': job})
        if p == '/api/hint':
            txt = make_hint(body['pid'], body['num'], body['dir'], body['level'],
                            body.get('clue', ''))
            self._log(body['pid'], {'t': 'hint', **{k: body[k] for k in ('num', 'dir', 'level')}})
            return self._json({'hint': txt})
        if p == '/api/check':
            v = check_answer(body['pid'], body['num'], body['dir'], body['answer'],
                             body.get('board'))
            self._log(body['pid'], {'t': 'check', 'num': body['num'], 'dir': body['dir'],
                                    'answer': body['answer'], 'ok': v.get('ok')})
            return self._json(v)
        if p == '/api/board':
            pid = body['pid']
            json.dump(body.get('board', {}),
                      open(os.path.join(PUZZLES, pid, 'board.json'), 'w'), ensure_ascii=False)
            return self._json({'saved': True})
        if p == '/api/log':
            self._log(body.pop('pid', 'anon'), body)
            return self._json({'ok': True})
        self._json({'error': 'unknown endpoint'}, 404)

    def _log(self, pid, event):
        event['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        with open(os.path.join(SESSIONS, f'{pid}.jsonl'), 'a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    os.chdir(ROOT)
    print(f'tashbetz assistant on http://localhost:{port}')
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
