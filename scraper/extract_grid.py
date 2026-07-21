import sys, json
from PIL import Image
import numpy as np

def find_bbox(a, w):
    dark = a < 128
    region = dark[:, :int(w*0.55)]
    col_counts = region.sum(axis=0)
    row_counts = region.sum(axis=1)
    cols = np.where(col_counts > col_counts.max()*0.5)[0]
    rows = np.where(row_counts > row_counts.max()*0.5)[0]
    return cols.min(), rows.min(), cols.max(), rows.max()

def classify(a, bbox, ncols=11, nrows=15):
    x0, y0, x1, y1 = bbox
    gw = (x1-x0)/ncols; gh = (y1-y0)/nrows
    means = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            ix0 = int(x0 + c*gw + gw*0.25); ix1 = int(x0 + c*gw + gw*0.75)
            iy0 = int(y0 + r*gh + gh*0.45); iy1 = int(y0 + r*gh + gh*0.85)
            row.append(a[iy0:iy1, ix0:ix1].mean())
        means.append(row)
    return means

if __name__ == '__main__':
    path = sys.argv[1]
    im = Image.open(path).convert('L')
    a = np.array(im)
    bbox = find_bbox(a, a.shape[1])
    print('bbox', bbox, 'cellw', (bbox[2]-bbox[0])/11, 'cellh', (bbox[3]-bbox[1])/15)
    means = classify(a, bbox)
    rows = []
    for r in range(15):
        s = ''.join('#' if means[r][c] < 128 else '.' for c in range(10, -1, -1))
        rows.append(s)
        amb = [round(m) for m in means[r] if 60 < m < 200]
        print(s, 'ambiguous:' if amb else '', amb if amb else '')
    # symmetry check (180 deg)
    sym = all(rows[r][i] == rows[14-r][10-i] for r in range(15) for i in range(11))
    print('180-symmetric:', sym)
    print(json.dumps({'grid': rows}))
