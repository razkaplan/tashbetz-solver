#!/usr/bin/env python3
"""Build the static, deployable demo of the solving assistant (docs/solve/).

The hosted site has no Python backend, so this bakes one puzzle into a static bundle:
  - puzzle.json (grid, clues, slots)
  - engine.json (the blind precision-first solve: tiers, proofs, hint fields)
  - hints1.json (precomputed homograph scans per clue — the level-1 hint)
and injects a client-side shim over api() so hints, checks, and logging work without
a server. Uploading new puzzles stays a local-app feature; the demo says so.

Usage: python3 app/build_static_demo.py <pid>
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def main():
    pid = sys.argv[1] if len(sys.argv) > 1 else 'sample3107'
    pdir = f'app/puzzles/{pid}'
    out = 'docs/solve'
    os.makedirs(out, exist_ok=True)
    puzzle = json.load(open(f'{pdir}/puzzle.json'))
    engine = json.load(open(f'{pdir}/engine.json'))

    # precompute level-1 hints (homograph scan) for every clue
    hints1 = {}
    for d in ('across', 'down'):
        for c in puzzle['clues'][d]:
            r = subprocess.run(['python3', 'solver/homographs.py', 'scan', c['clue']],
                               capture_output=True, text=True)
            hints1[f"{c['num']}-{d}"] = r.stdout.strip()

    json.dump(puzzle, open(f'{out}/puzzle.json', 'w'), ensure_ascii=False)
    json.dump(engine, open(f'{out}/engine.json', 'w'), ensure_ascii=False)
    json.dump(hints1, open(f'{out}/hints1.json', 'w'), ensure_ascii=False)

    html = open('app/static/index.html').read()
    shim = """
<script>
/* ---- STATIC DEMO SHIM: no backend; data is baked in, session stays in this browser ---- */
window.STATIC=true;
let SDATA=null, SENG=null, SH1=null;
async function loadStatic(){
  [SDATA,SENG,SH1]=await Promise.all(['puzzle.json','engine.json','hints1.json']
    .map(u=>fetch(u).then(r=>r.json())));
  SDATA.board=JSON.parse(localStorage.getItem('tash_board_'+SDATA.id)||'{}');
  SDATA.engine_status='done';
}
function sEngine(num,dir){return SENG.find(e=>e.clue_number===num&&e.direction===dir)||null}
const HEB={anagram:'אנגרם',reversal:'היפוך',container:'הכלה (מילה בתוך מילה)',
  hidden:'מילה מוסתרת ברצף',charade:'שרשור חלקים',double:'מילה משותפת',culture:'רפרנס תרבותי'};
window.api=async function(u,body){
  if(u==='/api/board'){localStorage.setItem('tash_board_'+PID,JSON.stringify(body.board));return{saved:true}}
  if(u==='/api/log'){const k='tash_log_'+PID,l=JSON.parse(localStorage.getItem(k)||'[]');
    l.push(body);localStorage.setItem(k,JSON.stringify(l));return{ok:true}}
  if(u==='/api/hint'){
    const e=sEngine(body.num,body.dir),L=body.level;
    if(L===1){let t='מילים דו-משמעיות בהגדרה:\\n'+(SH1[body.num+'-'+body.dir]||'(לא נמצאו)');
      if(e&&e.mechanism&&e.mechanism!=='other')t+='\\n\\nהמנגנון כנראה: '+(HEB[e.mechanism]||e.mechanism);
      return{hint:t}}
    if(L===2){const s=e&&e.definition_side;
      return{hint:s==='start'?'החלק המגדיר נמצא בתחילת ההגדרה; השאר הוא משחק המילים.'
        :s==='end'?'החלק המגדיר נמצא בסוף ההגדרה; השאר הוא משחק המילים.'
        :'ההגדרה הישירה יושבת באחד הקצוות — נסו לקרוא מכל כיוון.'}}
    if(L===3)return{hint:e&&e.hint_fragment?('רמז לחלק מהדרך: '+e.hint_fragment)
      :'אין רמז זמין להגדרה הזאת בדמו.'}
    if(L===4){const a=e&&(e.answer||'').replace(/[^א-ת]/g,'');
      return{hint:a&&e.tier!=='blank'?('האות הראשונה: '+a[0]+'   (ואורך: '+a.length+' אותיות)')
        :'למנוע אין כאן תשובה מבוססת. נסו הצלבות.'}}
    if(L===5){if(!e||e.tier==='blank'||!e.answer)
        return{hint:'המנוע נשאר כאן ריק בכוונה — אין לו תשובה שהוא מוכן להתחייב עליה. אתם לבד בזה :)'};
      const badge=e.tier==='committed'?'מוכחת':'השערה בלבד — לא מוכחת';
      return{hint:'התשובה ('+badge+'): '+e.answer+'\\n\\nההסבר:\\n'+(e.explanation||'')}}
  }
  if(u==='/api/check'){
    const e=sEngine(body.num,body.dir),a=(body.answer||'').replace(/[^א-ת]/g,'');
    const cells=PUZ.slots[body.num+'-'+body.dir]||[];
    if(a.length!==cells.length)return{ok:false,why:'אורך לא מתאים: '+a.length+' במקום '+cells.length};
    const ea=e&&(e.answer||'').replace(/[^א-ת]/g,'');
    return{ok:true,conflicts:[],in_lexicon:null,engine_agrees:ea?(ea===a):null};
  }
  return{};
};
window.addEventListener('DOMContentLoaded',async()=>{
  await loadStatic();
  document.getElementById('drop').innerHTML=
    '<div class="big">דמו: התשבץ של 31.7.2026</div>'+
    '<p class="small">גרסת הדגמה סטטית — העלאת תשבץ משלכם זמינה בגרסה המקומית (ראו GitHub). לחצו להתחלה.</p>';
  document.getElementById('drop').onclick=()=>start(SDATA);
});
</script>"""
    # neutralize the server-resume path and inject the shim before </body>
    html = html.replace("const qp=new URLSearchParams(location.search).get('p');",
                        "const qp=null;")
    html = html.replace('</body>', shim + '\n</body>')
    open(f'{out}/index.html', 'w').write(html)
    n_com = sum(1 for e in engine if e.get('tier') == 'committed')
    print(f'built {out}/ — {n_com} committed answers baked in, '
          f'{len(hints1)} level-1 hints precomputed')

if __name__ == '__main__':
    main()
