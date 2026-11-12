# Trace a voxel model out of a reference picture (side view on a light background) -> .npz colour map for bld.Grid.trace.
#   py trace_ref.py <image> <x0> <y0> <x1> <y1> <cell px> <out.npz> [colours=10]
# Each cell = median colour of the non-background pixels inside it (cells under half covered are empty);
# colours are reduced to a small palette so shading noise becomes clean colour blocks. Glow (bright saturated blue/cyan)
# is flagged so Grid.trace can make it emissive.
import sys
import numpy as np
from PIL import Image

img, x0, y0, x1, y1, cell, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
ncol = int(sys.argv[8]) if len(sys.argv) > 8 else 10
im = Image.open(img).convert('RGBA').crop((x0, y0, x1, y1))
rgba = np.asarray(im, float); a = rgba[..., :3]
bg = (rgba[..., 3] < 128) | ((a.min(2) > 222) & (a.max(2) - a.min(2) < 25))   # transparent or white / light grey background
H, W = a.shape[0] // cell, a.shape[1] // cell
cols = np.zeros((H, W, 3)); occ = np.zeros((H, W), bool)
for i in range(H):
    for j in range(W):
        blk = a[i * cell:(i + 1) * cell, j * cell:(j + 1) * cell]; m = ~bg[i * cell:(i + 1) * cell, j * cell:(j + 1) * cell]
        if m.mean() > .5:
            occ[i, j] = True; cols[i, j] = np.median(blk[m], 0)
# keep only the biggest connected piece (8-neighbour flood fill) so bits of neighbouring objects in the crop drop out
lab = np.zeros((H, W), int); best, bestn, nl = 0, 0, 0
for si, sj in zip(*np.nonzero(occ)):
    if lab[si, sj]: continue
    nl += 1; st = [(si, sj)]; lab[si, sj] = nl; cnt = 0
    while st:
        i, j = st.pop(); cnt += 1
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                a_, b_ = i + di, j + dj
                if 0 <= a_ < H and 0 <= b_ < W and occ[a_, b_] and not lab[a_, b_]:
                    lab[a_, b_] = nl; st.append((a_, b_))
    if cnt > bestn: best, bestn = nl, cnt
occ &= lab == best
def quant(cells, n):                                                       # median-cut palette for a set of colours
    if len(cells) == 0: return cells
    pi = Image.fromarray(cells[None].astype(np.uint8)).quantize(colors=min(n, len(cells)), method=Image.Quantize.MEDIANCUT)
    pal = np.array(pi.getpalette()[:3 * 256]).reshape(-1, 3)
    return pal[np.asarray(pi)[0]]
sat = cols.max(2) - cols.min(2)
acc = occ & ((sat > 40) | ((cols[..., 2] > 150) & (cols[..., 2] - cols[..., 0] > 35)))   # accents (gold, orange, blue lights) keep their own palette
neu = occ & ~acc
glow = occ & (cols[..., 2] > 200) & (cols[..., 2] - cols[..., 0] > 55)  # lights: flagged on the RAW colour (quantising merged them)
acc &= ~glow
q = np.zeros((H, W, 3)); q[neu] = quant(cols[neu], ncol); q[acc] = quant(cols[acc], 6); q[glow] = cols[glow]
np.savez(out, col=np.clip(q / 255.0 * 1.15, 0, 1)[::-1], occ=occ[::-1], glow=glow[::-1])     # flip so row 0 = bottom
print('TRACE', out, 'grid', W, 'x', H, 'cells', int(occ.sum()), 'glow', int(glow.sum()))
