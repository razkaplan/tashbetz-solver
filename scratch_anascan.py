import json,re,itertools,sys
sys.path.insert(0,'solver')
from collections import Counter
FIN=str.maketrans('ךםןףץ','כמנפצ')
def norm(s): return re.sub(r'[^א-ת]','',s or '').translate(FIN)
inp=json.load(open('data/dataset/inputs/2026-06-05.json'))
def strip_credit(c):
    return re.sub(r'\(עפ"י[^)]*\)','',c)
for sec in ['across','down']:
    for cl in inp[sec]:
        text=strip_credit(cl['clue'])
        words=[w for w in re.split(r'[\s,\.\?\!"]+',text) if norm(w)]
        total=sum(cl['enum'])
        hits=[]
        for i in range(len(words)):
            for j in range(i+1,len(words)+1):
                window=''.join(norm(w) for w in words[i:j])
                if len(window)==total:
                    hits.append((' '.join(words[i:j]),window))
        if hits:
            print(f"{cl['num']} {sec} enum={cl['enum']} total={total}")
            for w,win in hits:
                print("   FODDER:",w,"->",''.join(sorted(win)))
