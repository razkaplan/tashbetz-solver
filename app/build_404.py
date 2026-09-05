#!/usr/bin/env python3
"""The site's 404 page: docs/404.html, which Vercel serves for any missing path.

Until this existed a dead URL showed Vercel's bare NOT_FOUND screen - and the
site had 1,474 dead URLs Google had indexed (entity pages removed in the
August cleanups with no redirect). The page does three things:

  1. looks like the site and offers the milon search, prefilled with the last
     path segment, so someone landing on /milon/e/לגמ/ sees לגם straight away;
  2. links the main sections;
  3. reports the missed path to /api/missed - the demand signal that
     app/drain_missed.py turns into pages (see CLAUDE.md, "Dead URLs and
     pages in demand"). Path only, no query string, no identifiers.

Rebuild after a shell change: python3 app/build_404.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import brand  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..')

BODY = """<p>הכתובת שהגעתם אליה לא קיימת באתר, או שהדף הוסר. אפשר לחפש אותו כאן:</p>
<div class="search"><input id="q" type="search" placeholder="מילה, שם או תבנית: ג?ל*" autocomplete="off" aria-label="חיפוש במילון"></div>
<ul id="res" class="results"></ul>
<div class="cards" style="margin-top:1.4rem">
<a class="card" href="/milon/"><b>📖 מילון תשבץ</b><span>ערכים, אנגרמות והגדרות נפוצות</span></a>
<a class="card" href="/nosim/"><b>🎓 תשבצי נושא</b><span>עשרה מקצועות בגרות בארבע רמות</span></a>
<a class="card" href="/nativ/"><b>☀️ נתיב היומי</b><span>חידה חדשה כל יום</span></a>
<a class="card" href="/solve/"><b>🧩 עוזר הפתירה</b><span>רמזים מדורגים והוכחות</span></a>
</div>
<script>
(function(){
const q=document.getElementById('q'),res=document.getElementById('res');
let E=null;
fetch('/milon/entities.json').then(r=>r.json()).then(d=>{E=d;run();}).catch(()=>{});
const FINMAP={'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'},canon=s=>s.replace(/[ךםןףץ]/g,m=>FINMAP[m]);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function run(){if(!E)return;const v=q.value.trim();res.innerHTML='';if(v.length<2)return;
  const c=canon(v);let hits=E.filter(e=>e.t.includes(v)||e.n.includes(c));
  const sc=e=>(e.t===v||e.n===c)?2:(e.t.startsWith(v)||e.n.startsWith(c))?1:0;hits.sort((a,b)=>sc(b)-sc(a));
  res.innerHTML=hits.slice(0,30).map(e=>{const u=e.p?('/milon/e/'+encodeURIComponent(e.t)+'/'):('/milon/'+e.c+'-'+e.l+'/#'+encodeURIComponent(e.n));
    return '<li><a href="'+u+'"><b>'+esc(e.t)+'</b>'+(e.d?'<br><small>'+esc(e.d)+'</small>':'')+'</a></li>'}).join('');}
q.oninput=run;
// prefill from the path: /milon/e/לגמ/ -> "לגמ"
try{const seg=decodeURIComponent(location.pathname.replace(/\\/+$/,'').split('/').pop()||'');
  if(/[א-ת]{2}/.test(seg)){q.value=seg;}}catch(e){}
if(matchMedia('(pointer:fine)').matches)q.focus();
// the demand signal: which dead paths people actually reach. Path only.
try{const p=location.pathname;
  if(/^\\/(milon|nosim|tirgul|methods|research|bakasha|nativ)\\//.test(p)&&p.length<=200){
    fetch('/api/missed',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({p:p,g:/google\\./.test(document.referrer)?1:0}),keepalive:true}).catch(()=>{});}}catch(e){}
})();
</script>"""

STYLE = ('<style>.search input{width:100%;font-size:1.15rem;padding:.7rem .9rem;border:2px solid var(--ink);'
         'border-radius:12px;background:#fff;color:#111}.results{list-style:none;padding:0;margin:.8rem 0 0}'
         '.results li{padding:.45rem 0;border-bottom:1px solid var(--line,#ddd)}.results a{text-decoration:none;color:inherit}'
         '.results b{color:var(--accent)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:.8rem}'
         '.cards .card{display:block;text-decoration:none;color:inherit}.cards .card span{display:block;font-size:.9rem;opacity:.8}</style>')


def main():
    html = brand.document(
        title='הדף לא נמצא', desc='הדף שחיפשתם אינו קיים. חפשו במילון התשבץ או עברו לאחד מחלקי האתר.',
        canonical=f'{brand.BASE}/404.html',
        meta='<meta name="robots" content="noindex">',
        style=STYLE, kicker='🧭 הדף לא נמצא', h1='אופס, אין כאן תשבץ',
        crumbs=[('דף הבית', '/'), ('הדף לא נמצא', '/404.html')],
        body=BODY, current='milon')
    out = os.path.join(ROOT, 'docs', '404.html')
    open(out, 'w', encoding='utf-8').write(html)
    print('wrote docs/404.html')


if __name__ == '__main__':
    main()
