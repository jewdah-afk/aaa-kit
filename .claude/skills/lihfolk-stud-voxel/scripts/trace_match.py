"""Outline a concept view, line it up with the model's own flat view, measure the gap, and trace the concept's plates.

    python3 scripts/trace_match.py <model key> <concept.jpg> x0 y0 x1 y1 <out prefix> [plates.npz]

<model key> is a grid cached by `scorecard.py dump` / `file` (same SV_CACHE). x0..y1 is the crop of the concept's SIDE view.
Needs numpy + Pillow only.

What it does (research ch. 92):
  1. outline   concept silhouette (not the grey background) + its dark plates (lit top faces; the joins between them are the plate lines)
  2. fit       stretch and slide the concept until its silhouette overlaps the model's side view best (IoU search)
  3. measure   silhouette IoU; chamfer distance (mean distance in bricks from each line pixel to the nearest line of the
               other image) for the outline and for the interior lines, both directions
  4. picture   <prefix>_overlay.png (model view, concept lines in orange, model lines in cyan) and
               <prefix>_side_by_side.png (fitted concept | model | overlay)
  5. trace     with [plates.npz]: the concept's plates (lit top faces) resampled to one cell per brick,
               each with a height level chosen so touching plates never share a level. A model file reads this map and
               builds its plates from it (see war_rhino_plated_brick.py).
The concept is a drawing in perspective and often in another pose; the fit is a stretch, not a camera solve.
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorecard as sc

S = 3                                                  # working pixels per brick


def components(m, min_size=1):
    """4-connected regions of a boolean image -> label image (0 = none), sizes"""
    lab = np.zeros(m.shape, np.int32); sizes = [0]; H, W = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]: continue
        k = len(sizes); st = [(y0, x0)]; lab[y0, x0] = k; c = 0
        while st:
            y, x = st.pop(); c += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = k; st.append((yy, xx))
        sizes.append(c)
    sizes = np.array(sizes)
    if min_size > 1: lab[sizes[lab] < min_size] = 0
    return lab, sizes


def dist(m, cap=60):
    """distance (pixels, chamfer 1 / 1.4) from every pixel to the nearest True pixel of m"""
    d = np.where(m, 0.0, float(cap))
    for _ in range(cap):
        p = np.pad(d, 1, constant_values=cap)
        n = np.minimum.reduce([d, p[:-2, 1:-1] + 1, p[2:, 1:-1] + 1, p[1:-1, :-2] + 1, p[1:-1, 2:] + 1,
                               p[:-2, :-2] + 1.4, p[:-2, 2:] + 1.4, p[2:, :-2] + 1.4, p[2:, 2:] + 1.4])
        if np.array_equal(n, d): break
        d = n
    return d


def outline(m):
    p = np.pad(m, 1); return m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])


def grow(lab):
    """fill label 0 pixels with the nearest label (plates then touch each other)"""
    lab = lab.copy()
    for _ in range(200):
        z = lab == 0
        if not z.any(): break
        p = np.pad(lab, 1)
        for nb in (p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]):
            t = z & (nb > 0) & (lab == 0); lab[t] = nb[t]
    return lab


def concept_view(path, box):
    a = np.asarray(Image.open(path).convert('RGB').crop(box)).astype(float)
    ai = a.astype(int); m = ((ai.max(-1) - ai.min(-1)) > 28) | (ai.mean(-1) < 95)          # not the flat grey background
    lab, sizes = components(m); m = sc.fill_holes(lab == int(np.argmax(sizes)))
    ys, xs = np.nonzero(m); sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    return a[sl], m[sl]


def resize_bool(m, h, w): return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)) > 127


def place(img, h, w, ty, tx, H, W, fill=0):
    """resize img to (h, w) and paste it at (ty, tx) on an (H, W) canvas"""
    im = Image.fromarray(img).resize((w, h), Image.BILINEAR if img.dtype != bool else Image.NEAREST)
    out = Image.new(im.mode, (W, H), fill); out.paste(im, (tx, ty)); return np.asarray(out)


def fit(cm, mm):
    """stretch (w, h) and offset of the concept mask that maximise IoU with the model mask; coarse then fine"""
    H, W = mm.shape; best = (-1,)
    c8 = (cm * 255).astype(np.uint8)
    def iou_at(h, w, ty, tx):
        pm = place(c8, h, w, ty, tx, H, W) > 127
        return (pm & mm).sum() / max(1, (pm | mm).sum())
    h0, w0 = H, W
    for step, rng in ((6, 4), (2, 3), (1, 2)):
        _, bh, bw, bty, btx = best if best[0] >= 0 else (0, h0, w0, 0, 0)
        for h in range(bh - rng * step, bh + rng * step + 1, step):
            for w in range(bw - rng * step, bw + rng * step + 1, step):
                if h < 8 or w < 8: continue
                for ty in range(bty - rng * step, bty + rng * step + 1, step):
                    for tx in range(btx - rng * step, btx + rng * step + 1, step):
                        v = iou_at(h, w, ty, tx)
                        if v > best[0]: best = (v, h, w, ty, tx)
    return best


def main():
    a = sys.argv[1:]; key, concept, box, prefix = a[0], a[1], tuple(int(v) for v in a[2:6]), a[6]
    plates_out = a[7] if len(a) > 7 else None
    z = np.load(os.path.join(sc.CACHE, key + '.npz')); j = json.load(open(os.path.join(sc.CACHE, key + '.json')))
    kind, col, lo = z['kind'], z['col'].copy(), z['lo']
    for k, c in j.get('glow', {}).items(): col[kind == int(k)] = np.round(np.array(c) * 255)
    c, d, m, g = sc.project(kind, col, 0, True)                         # side view, front (-z) at the left
    ys, xs = np.nonzero(m); r0, c0 = ys.min(), xs.min()
    m, c, d, g = sc.crop(m, c, d, g)
    img, rel, dd = sc.shade(c, d, m, g)
    Hb, Wb = m.shape; H, W = Hb * S, Wb * S
    up = lambda x: np.repeat(np.repeat(x, S, 0), S, 1)
    mm = up(m); mimg = up(img).astype(np.uint8)
    Lm = sc.oklab_L(img) * 8; e = np.zeros_like(m)                       # model interior lines = lightness steps of a band or more
    e[:, 1:] |= m[:, 1:] & m[:, :-1] & (np.abs(Lm[:, 1:] - Lm[:, :-1]) >= sc.EDGE); e[1:] |= m[1:] & m[:-1] & (np.abs(Lm[1:] - Lm[:-1]) >= sc.EDGE)
    mline = up(e & (sc.blur(m.astype(float), 1) > .999))
    # concept
    ca, cm = concept_view(concept, box)
    L = sc.oklab_L(ca)
    top = cm & (L > sc.blur(L, 6, cm) + .01)                             # plates = lit top faces, brighter than their surroundings
    creg, _ = components(top, min_size=40)
    creg = np.where(cm, grow(creg), 0)                                   # plates grown until they touch: the joins are the plate lines
    cline0 = np.zeros_like(cm); cline0[:, 1:] |= creg[:, 1:] != creg[:, :-1]; cline0[1:] |= creg[1:] != creg[:-1]
    cline0 &= sc.blur(cm.astype(float), 2) > .999
    iou, h, w, ty, tx = fit(cm, mm)
    pc = place(ca.astype(np.uint8), h, w, ty, tx, H, W, (255, 255, 255))
    pm = place((cm * 255).astype(np.uint8), h, w, ty, tx, H, W) > 127
    pline = place((cline0 * 255).astype(np.uint8), h, w, ty, tx, H, W) > 100
    # measures (in bricks)
    def chamfer(a_, b_): return float(dist(b_)[a_].mean() / S) if a_.any() and b_.any() else float('nan')
    res = dict(model=key, iou=round(float(iou), 3), fit=dict(h=h, w=w, ty=ty, tx=tx, px_per_brick=S),
               outline_c2m=round(chamfer(outline(pm), outline(mm)), 2), outline_m2c=round(chamfer(outline(mm), outline(pm)), 2),
               lines_c2m=round(chamfer(pline & mm, mline), 2), lines_m2c=round(chamfer(mline & pm, pline), 2))
    # pictures
    ov = mimg.copy(); ov[~mm] = 255
    ov[mline] = (0, 200, 230); ov[pline] = (255, 120, 0); ov[outline(pm)] = (255, 60, 0); ov[outline(mm)] = (0, 90, 200)
    K = 2
    big = lambda x: np.repeat(np.repeat(x, K, 0), K, 1)
    mview = mimg.copy(); mview[~mm] = 255
    sheet = Image.new('RGB', (3 * W * K + 40, H * K + 34), (24, 26, 32)); dr = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate((('Concept, fitted', pc), ('Model, flat side view', mview), ('Overlay: concept orange, model blue', ov))):
        sheet.paste(Image.fromarray(big(im)), (i * (W * K + 20), 34)); dr.text((i * (W * K + 20) + 6, 10), lab, fill=(235, 235, 235))
    sheet.save(prefix + '_side_by_side.png'); Image.fromarray(big(ov)).save(prefix + '_overlay.png')
    # trace the plates
    if plates_out:
        reg = np.asarray(Image.fromarray(creg.astype(np.int32)).resize((w, h), Image.NEAREST))
        full = np.zeros((H, W), np.int32); ys0, xs0 = max(0, ty), max(0, tx)
        sub = reg[ys0 - ty:ys0 - ty + H - ys0, xs0 - tx:xs0 - tx + W - xs0]; full[ys0:ys0 + sub.shape[0], xs0:xs0 + sub.shape[1]] = sub
        reg = full
        cell = reg.reshape(Hb, S, Wb, S)[:, S // 2, :, S // 2]           # one cell per brick (centre sample)
        small = np.bincount(cell.ravel()); cell[small[cell] < 8] = 0; cell = grow(cell)   # drop slivers;                                                # bricks outside the concept take the nearest plate
        ids = [i for i in np.unique(cell) if i > 0]
        Lp = place((np.clip(L, 0, 1) * 255).astype(np.uint8), h, w, ty, tx, H, W)
        light = {i: float(Lp[reg == i].mean()) if (reg == i).any() else 0.0 for i in ids}
        adj = {i: set() for i in ids}
        for a_, b_ in ((cell[:, 1:], cell[:, :-1]), (cell[1:], cell[:-1])):
            for p, q in set(zip(a_[a_ != b_].tolist(), b_[a_ != b_].tolist())): adj[p].add(q); adj[q].add(p)
        level = {}
        for i in sorted(ids, key=lambda i: -(cell == i).sum()):          # biggest plates first; lighter plates sit higher
            want = sorted((1, 2, 3, 4), key=lambda v: abs(v - (1 + 3 * (light[i] - min(light.values())) / max(1e-6, max(light.values()) - min(light.values())))))
            level[i] = next((v for v in want if all(level.get(n) != v for n in adj[i])), want[0])
        lv = np.zeros(max(ids) + 1, np.int8)
        for i, v in level.items(): lv[i] = v
        np.savez_compressed(plates_out, plate=cell.astype(np.int16), level=lv, z0=lo[2] + .5 + c0, ytop=lo[1] + .5 + (kind.shape[1] - 1 - r0))
        res['plates'] = len(ids)
        pal = np.random.RandomState(3).randint(60, 230, (max(ids) + 1, 3)).astype(np.uint8)
        Image.fromarray(np.repeat(np.repeat(np.where(m[..., None], pal[cell], 255).astype(np.uint8), 6, 0), 6, 1)).save(prefix + '_plates.png')
    json.dump(res, open(prefix + '.json', 'w'), indent=1); print('TRACE_OK', json.dumps(res))


if __name__ == '__main__':
    main()
