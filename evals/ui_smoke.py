#!/usr/bin/env python3
"""UI smoke test: drives the published pages in headless Chromium and asserts
that the games are still playable after a template or stylesheet change.

What it exercises (all from the committed docs/ tree, no network):
  topic crossword + trainer  type, advance, direction toggle, backspace,
                             arrows, check (ok/bad), explain, clear, clue strip
  solver demo                open a demo, type an answer with the keyboard,
                             check it, get the proof, ask for a hint
  נתיב                       dismiss onboarding, drag a real word path, lock
  milon hub                  live search renders result cards

Usage: python3 evals/ui_smoke.py [--chrome /path/to/chrome]
Exit status is non-zero on any failed assertion.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
CHROME_DEFAULT = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
HOOK = ('<script>window.__done=function(o){var p=document.createElement("pre");p.id="__out";'
        'p.textContent=JSON.stringify(o);document.body.appendChild(p)};'
        'window.addEventListener("error",function(e){window.__done({error:String(e.message)})});</script>')

CROSSWORD_JS = r"""
(function(){
 const out={}; const kd=(el,key)=>el.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));
 const cells=[...document.querySelectorAll('.cell')]; out.cells=cells.length;
 const c0=cells.find(c=>c.querySelector('input')); const inp=c0.querySelector('input'); const ri=inp.getBoundingClientRect();
 out.inputPx=Math.round(ri.width); out.hitTest=document.elementFromPoint(ri.left+ri.width/2,ri.top+ri.height/2)===inp;
 let cross=null; for(const k in inputs){const [r,c]=k.split(',').map(Number); if(PZ.entries.filter(e=>e.cells.some(x=>x[0]===r&&x[1]===c)).length===2){cross=inputs[k];break}}
 if(cross){cross.focus(); const d1=active.dir; cross.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); out.toggled=active.dir!==d1;
   out.hlMatchesActive=document.querySelectorAll('.cell.hl').length===active.cells.length;}
 else out.toggled=out.hlMatchesActive='n/a';
 const e=PZ.entries.find(e=>e.cells.length>=3); document.querySelector('.clues li[data-i="'+PZ.entries.indexOf(e)+'"]').click();
 const first=document.activeElement; out.clueFocus=first===inputs[e.cells[0].join(',')];
 out.curClue=document.getElementById('cur').textContent.length>3;
 first.value=e.answer[0]; first.dispatchEvent(new Event('input',{bubbles:true}));
 out.advanced=document.activeElement===inputs[e.cells[1].join(',')];
 kd(document.activeElement,'Backspace'); out.backspace=document.activeElement===first&&first.value==='';
 const [r,c]=e.cells[0]; const below=inputs[(r+1)+','+c]; kd(first,'ArrowDown'); out.arrow=below?document.activeElement===below:true;
 for(const e of PZ.entries) e.cells.forEach(([r,c],k)=>{inputs[r+','+c].value=e.answer[k];});
 document.getElementById('check').click();
 out.allOk=document.querySelectorAll('.cell.bad').length===0&&document.querySelectorAll('.clues li.done').length===PZ.entries.length;
 out.okColor=getComputedStyle(document.querySelector('.cell.ok input')).color;
 first.value=e.answer[0]==='א'?'ב':'א'; document.getElementById('check').click(); out.badMarked=document.querySelectorAll('.cell.bad').length===1;
 out.badColor=getComputedStyle(document.querySelector('.cell.bad input')).color;
 document.getElementById('explain').click(); out.explain=[...document.querySelectorAll('.exp')].every(x=>getComputedStyle(x).display!=='none');
 document.getElementById('clear').click(); out.cleared=[...document.querySelectorAll('.cell input')].every(i=>!i.value);
 out.noOverflow=document.documentElement.scrollWidth<=document.documentElement.clientWidth;
 window.__done(out);
})();
"""
SOLVER_JS = r"""
(function(){ const out={}; const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 (async()=>{ await sleep(500);
  document.querySelector('#demolist .card').click(); await sleep(2500);
  const grid=document.getElementById('grid'); out.tableLayout=getComputedStyle(grid).display==='table';
  const td=grid.querySelector('td:not(.black)'); const r=td.getBoundingClientRect(); out.tdPx=Math.round(r.width);
  out.noOverflow=document.documentElement.scrollWidth<=document.documentElement.clientWidth;
  const key='1-across'; const e=ENGINE.find(x=>x.clue_number===1&&x.direction==='across');
  document.querySelector('.clue[data-k="'+key+'"]').click(); await sleep(100);
  out.panel=getComputedStyle(document.getElementById('panel')).display==='flex';
  for(const ch of e.answer.replace(/[^א-ת]/g,'')) document.dispatchEvent(new KeyboardEvent('keydown',{key:ch,bubbles:true}));
  await sleep(100); await checkSlot(); await sleep(200);
  out.solved=document.querySelectorAll('td.ok').length===PUZ.slots[key].length; out.msg=document.getElementById('msg').textContent;
  out.proof=document.getElementById('proof').style.display==='block';
  await hint(1); await sleep(100); out.hint=getComputedStyle(document.getElementById('hintout')).display==='block';
  window.__done(out);
 })().catch(e=>window.__done({error:String(e)})); })();
"""
NATIV_JS = r"""
(function(){ const out={}; const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 (async()=>{ await sleep(800); document.getElementById('obGo').click(); await sleep(100);
  const board=document.getElementById('board'); const cells=[...board.querySelectorAll('.cell')];
  const bw=board.getBoundingClientRect().width; const cols=getComputedStyle(board).gridTemplateColumns.split(' ').length;
  const cw=cells[0].getBoundingClientRect().width; out.cellFills=Math.abs(cw-(bw-8-10-(cols-1)*5)/cols)<3;
  const data=await fetch('puzzles.json').then(r=>r.json());
  const d=new Date(); const key=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  const pz=(cells.length===16?data.easy:data.days)[key]; if(!pz){window.__done({skip:'no puzzle for '+key});return}
  const R=pz.rows,C=pz.cols,G=pz.grid; out.gridMatches=cells.map(c=>c.textContent).join('')===G.join('');
  function findPath(word){const adj=i=>{const r=Math.floor(i/C),c=i%C;const o=[];if(r>0)o.push(i-C);if(r<R-1)o.push(i+C);if(c>0)o.push(i-1);if(c<C-1)o.push(i+1);return o};
    function dfs(i,k,used){if(G[i]!==word[k])return null;if(k===word.length-1)return [i];for(const j of adj(i)){if(used.has(j))continue;used.add(j);const p=dfs(j,k+1,used);used.delete(j);if(p)return [i,...p];}return null;}
    for(let i=0;i<G.length;i++){const p=dfs(i,0,new Set([i]));if(p)return p}return null;}
  const w=pz.words.find(w=>findPath(w.n)); const path=findPath(w.n);
  const pt=i=>{const q=cells[i].getBoundingClientRect();return {clientX:q.left+q.width/2,clientY:q.top+q.height/2,bubbles:true,pointerId:1,isPrimary:true,button:0,pointerType:'touch'}};
  const locked0=board.querySelectorAll('.cell.lock').length;
  board.dispatchEvent(new PointerEvent('pointerdown',pt(path[0]))); await sleep(30);
  for(const i of path.slice(1)){board.dispatchEvent(new PointerEvent('pointermove',pt(i)));await sleep(30)}
  window.dispatchEvent(new PointerEvent('pointerup',pt(path[path.length-1]))); await sleep(1200);
  out.wordLocked=board.querySelectorAll('.cell.lock').length-locked0===w.n.length;
  out.rowDone=document.querySelectorAll('.wrow.done').length===1;
  out.lockBg=getComputedStyle(board.querySelector('.cell.lock')).backgroundColor;
  out.noOverflow=document.documentElement.scrollWidth<=document.documentElement.clientWidth;
  window.__done(out);
 })().catch(e=>window.__done({error:String(e)})); })();
"""
HUB_JS = r"""
setTimeout(()=>{const g=document.getElementById('res');const q=document.getElementById('q');q.value='ירושל';q.dispatchEvent(new Event('input'));
 setTimeout(()=>window.__done({grid:getComputedStyle(g).display==='grid',items:g.children.length,link:!!g.querySelector('a[href]')}),400)},1500)
"""

TESTS = [
    ('nosim/tanach/2/index.html', CROSSWORD_JS, 1280, dict(hitTest=True, toggled=True, hlMatchesActive=True, clueFocus=True, curClue=True, advanced=True, backspace=True, arrow=True, allOk=True, badMarked=True, explain=True, cleared=True, noOverflow=True)),
    ('nosim/tanach/4/index.html', CROSSWORD_JS, 390, dict(hitTest=True, toggled=True, clueFocus=True, advanced=True, backspace=True, allOk=True, badMarked=True, cleared=True, noOverflow=True)),
    ('tirgul/1/index.html', CROSSWORD_JS, 1280, dict(hitTest=True, toggled=True, clueFocus=True, advanced=True, backspace=True, arrow=True, allOk=True, badMarked=True, explain=True, cleared=True, noOverflow=True)),
    ('tirgul/100/index.html', CROSSWORD_JS, 390, dict(hitTest=True, allOk=True, badMarked=True, noOverflow=True)),
    ('solve/index.html', SOLVER_JS, 1280, dict(tableLayout=True, panel=True, solved=True, proof=True, hint=True, noOverflow=True)),
    ('solve/index.html', SOLVER_JS, 390, dict(tableLayout=True, solved=True, noOverflow=True)),
    ('nativ/index.html', NATIV_JS, 390, dict(cellFills=True, gridMatches=True, wordLocked=True, rowDone=True, noOverflow=True)),
    ('nativ/index.html', NATIV_JS, 1280, dict(cellFills=True, wordLocked=True, rowDone=True)),
    ('milon/index.html', HUB_JS, 1280, dict(grid=True, link=True)),
]


def run_page(chrome, mirror, page, js, width):
    src = os.path.join(DOCS, page)
    s = open(src, encoding='utf-8').read()
    s = re.sub(r'<link href="https://fonts.googleapis.com[^>]*>', '', s)
    s = s.replace('href="/assets/brand.css"', f'href="file://{mirror}/assets/brand.css"')
    s = s.replace("fetch('/milon/entities.json')", f"fetch('file://{DOCS}/milon/entities.json')")
    s = s.replace('<head>', '<head>' + HOOK, 1).replace('</body>', '<script>' + js + '</script></body>')
    pdir = os.path.dirname(page)
    os.makedirs(os.path.join(mirror, pdir), exist_ok=True)
    for f in os.listdir(os.path.join(DOCS, pdir)):
        fp = os.path.join(DOCS, pdir, f)
        if os.path.isfile(fp) and not f.endswith('.html'):
            shutil.copy(fp, os.path.join(mirror, pdir, f))
        if os.path.isdir(fp) and f == 'data' and not os.path.exists(os.path.join(mirror, pdir, 'data')):
            shutil.copytree(fp, os.path.join(mirror, pdir, 'data'))
    dst = os.path.join(mirror, pdir, 'smoke.html')
    open(dst, 'w', encoding='utf-8').write(s)
    if width < 600:  # Chromium will not open a window that narrow: lay the page out in an iframe instead
        wrap = dst + '.wrap.html'
        open(wrap, 'w').write(
            f'<html><body style="margin:0"><iframe id="f" src="file://{urllib.parse.quote(dst)}" style="border:0;width:{width}px;height:1400px"></iframe>'
            '<script>setInterval(function(){try{var o=document.getElementById("f").contentDocument.getElementById("__out");'
            'if(o&&!document.getElementById("__out")){var p=document.createElement("pre");p.id="__out";p.textContent=o.textContent;document.body.appendChild(p)}}catch(e){}},200)</script></body></html>')
        dst = wrap
    r = subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--allow-file-access-from-files',
                        f'--window-size={max(width, 800)},1400', '--virtual-time-budget=9000', '--dump-dom',
                        'file://' + urllib.parse.quote(dst)], capture_output=True, text=True, timeout=180)
    m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
    if not m:
        return {'error': 'no result (page did not call __done)'}
    return json.loads(html.unescape(m.group(1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chrome', default=os.environ.get('CHROME') or shutil.which('chromium') or CHROME_DEFAULT)
    a = ap.parse_args()
    mirror = tempfile.mkdtemp(prefix='ui-smoke-')
    os.makedirs(os.path.join(mirror, 'assets'))
    shutil.copy(os.path.join(DOCS, 'assets', 'brand.css'), os.path.join(mirror, 'assets', 'brand.css'))
    failed = 0
    for page, js, width, expect in TESTS:
        got = run_page(a.chrome, mirror, page, js, width)
        if 'skip' in got:
            print(f'SKIP {page}@{width}: {got["skip"]}')
            continue
        bad = {k: got.get(k) for k, v in expect.items() if got.get(k) != v}
        if 'error' in got:
            bad['error'] = got['error']
        status = 'FAIL' if bad else 'ok  '
        failed += bool(bad)
        print(f'{status} {page}@{width}' + (f'  {json.dumps(bad, ensure_ascii=False)}' if bad else ''))
    shutil.rmtree(mirror, ignore_errors=True)
    print('all passed' if not failed else f'{failed} page(s) failed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
