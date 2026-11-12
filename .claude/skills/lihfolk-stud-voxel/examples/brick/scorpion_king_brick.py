# Sand Scorpion King (stud-voxel boss, brick pipeline). Reference = concept_sheet.jpg (this folder).
# GLOW: strong   (read by run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Built from the War Rhino brick example: field -> plates/segments with stepped seams -> brick faces + square-stud overlay -> EEVEE.
# Run: powershell -File <skill>\scripts\run_brick.ps1 scorpion_king.py
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'ScorpionKing'

lo = np.array((-58.0, -0.5, -74.0)); hi = np.array((58.0, 72.5, 60.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)                                      # plate id / plate height level

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
GOLDL = hx('f0c050'); GOLD = hx('dba032'); GOLDM = hx('c2852c'); GOLDD = hx('a0702c')
BRONZE = hx('4a3024'); BRONZED = hx('3b2728'); BLACK = hx('140c0c')
GLOW = {2: hx('d812d0'), 3: hx('ff5cf2'), 4: hx('ffd6ff')}   # magenta edge / hot centre / white-pink glint

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb, flat=False):                   # capsule a->b (flat=True: cylinder with flat ends)
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t0 = ((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab); t = np.clip(t0, 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    m = d <= ra + (rb - ra) * t
    return m & (t0 >= 0) & (t0 <= 1) if flat else m
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def rbox(c, h, p=4):                                  # rounded box (superellipsoid) centre c, half sizes h
    return ((np.abs(X - c[0]) / h[0]) ** p + (np.abs(Y - c[1]) / h[1]) ** p + (np.abs(Z - c[2]) / h[2]) ** p) < 1

NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ---------------------------------------------------------------- body (mesosoma): boxy segmented barrel, front = head
# profile along z: (z, half width, bottom y, top y)
BP = np.array([(-22, 12.0, 20.5, 34.5), (-14, 14.5, 19.0, 38.5), (-2, 15.5, 18.5, 40.5), (10, 15.0, 19.0, 40.0),
               (20, 13.0, 20.5, 38.0), (28, 10.0, 23.0, 36.0), (33, 7.5, 25.5, 34.0)])
bw = np.interp(Z, BP[:, 0], BP[:, 1]); bb = np.interp(Z, BP[:, 0], BP[:, 2]); bt = np.interp(Z, BP[:, 0], BP[:, 3])
bm = (bb + bt) / 2; bh = (bt - bb) / 2
body = ((AX / bw) ** 4 + (np.abs(Y - bm) / bh) ** 4 < 1) & (Z > -22) & (Z < 33)
put(body, BRONZE, st=False)
# tergite plates: 6 gold shields over the top half, each plate's REAR edge 1 brick higher (stepped overlap)
PZ = [-22, -12, -2, 8, 17, 25, 33]
for k_ in range(6):
    z0, z1 = PZ[k_], PZ[k_ + 1]
    t = np.clip((Z - z0) / (z1 - z0), 0, 1)
    shell = ((AX / (bw + .6 + .9 * t)) ** 4 + (np.abs(Y - bm) / (bh + .6 + .9 * t)) ** 4 < 1) & (Z > z0) & (Z < z1)
    shell &= (Y > bm + 3.0 - 2.2 * (AX / bw) ** 3)      # plate wraps down the flanks
    put(shell, GOLD, p=3000 + k_, l=1 + (k_ % 2) * .5)
for z in PZ[1:-1]:                                   # dark seam between plates
    put((np.abs(Z - z) < .9) & (kind == 1) & (pid >= 3000), BRONZED, st=False)
put((kind == 1) & body & (Y < bm - 3), BRONZED, st=False)                         # underside darker

# ---------------------------------------------------------------- head (prosoma): boxy, gold crown + cheeks, dark recessed face
HP = np.array([(-39, 10.5, 20.5, 30.0), (-34, 12.0, 20.0, 31.0), (-26, 12.5, 20.0, 31.5), (-20, 12.0, 20.5, 32.0)])
hw = np.interp(Z, HP[:, 0], HP[:, 1]); hb = np.interp(Z, HP[:, 0], HP[:, 2]); ht = np.interp(Z, HP[:, 0], HP[:, 3])
hm = (hb + ht) / 2; hh = (ht - hb) / 2
head = ((AX / hw) ** 5 + (np.abs(Y - hm) / hh) ** 5 < 1) & (Z > -39) & (Z < -19)
HID = newid()
put(head, GOLD, p=HID, l=3)
put(head & (Y < 23), BRONZE, st=False)                                              # underjaw
put(box(-1, 9.0, 20, 28.0, -39.5, -37), BRONZED, st=False)                         # face panel (dark) ...
kind[box(-1, 9.0, 20, 28.0, -39.5, -38)] = 0                                         # ... recessed 1 brick
CR = newid()
put(box(-1, 11.5, 28.5, 32.0, -40, -21) & (Y < ht + .9), GOLD, p=CR, l=5)              # crown plate (proud lip at the front)
put(box(-1, 1.5, 20, 28.5, -39, -37), BRONZE, st=False)                              # dark nose ridge between the eyes
put(box(-1, 2.5, 26.5, 29.0, -39.5, -37), GOLD, p=CR, l=5)                           # gold brow centre
for xi in range(2, 10):                                                              # angry brow: V over the eyes (inner end low)
    put(box(xi, xi + 1, 26.6 + (xi - 2) * .3, 29.0, -39.5, -37), GOLD, p=CR, l=5)
# eyes (flush in the recessed panel): big inner pair, small outer pair, tiny lower pair
for (xa, xb, y) in ((3.0, 5.5, 23), (2.5, 6.5, 24), (3.5, 7.0, 25), (7.0, 9.5, 24), (7.5, 9.5, 25), (8.5, 9.5, 26)):   # slanted angry eyes, outer corner high
    put(box(xa, xb, y - .5, y + .5, -38.5, -37), GLOW[2], k=2, st=False)
put(box(2.5, 4.5, 20.5, 21.5, -38.5, -37), GLOW[2], k=2, st=False)
for s in (1, -1):                                                                    # chelicerae: short thick gold tusks, down + in
    put(chain([(6.5 * s, 20.0, -38), (6.2 * s, 17.0, -40), (4.5 * s, 14.0, -40.5)], [2.3, 1.6, .5]), GOLDL, p=newid(), l=6)
# crown: raised centre block on the crown front carrying the gem, big gold spikes behind it
put(box(-1, 4.5, 30, 35.0, -40, -30), GOLD, p=newid(), l=6)
put(chain([(0, 33, -32), (0, 40, -33), (0, 48, -34)], [5.0, 3.2, .6]), GOLDL, p=newid(), l=7)
for s in (1, -1):
    put(chain([(6.5 * s, 30, -30), (7.5 * s, 37, -31), (8.3 * s, 43, -31)], [3.9, 2.5, .5]), GOLDL, p=newid(), l=7)
    put(chain([(10.5 * s, 29, -29), (13.0 * s, 34, -30), (15.5 * s, 38.5, -30)], [3.5, 2.2, .5]), GOLDL, p=newid(), l=7)
gem = (AX / 2.6 + np.abs(Y - 32.5) / 3.2 < 1) & (Z > -41) & (Z < -39)
put(gem, GLOW[2], k=2, st=False)
put(gem & (AX < 1.2) & (Y > 32) & (Y < 34.5), GLOW[3], k=3, st=False)
put(gem & (X < -.1) & (X > -1.2) & (Y > 33) & (Y < 34.5), GLOW[4], k=4, st=False)

# ---------------------------------------------------------------- limbs: gold segments shortened at both ends, dark recessed joint ring between
def seg(a, b, ra, rb, c, gap=1.1, l=2, st=True):
    a = np.array(a, float); b = np.array(b, float); d = (b - a) / np.linalg.norm(b - a)
    put(cap(a + d * gap, b - d * gap, ra, rb, flat=gap > 0), c, p=newid(), l=l, st=st)
def joint(c, r): put(sd_ell(c, (r, r, r)) < 0, BRONZED, st=False)

# ---------------------------------------------------------------- pincers (pedipalps): heavy arm + big serrated claw, C opening inward
for s in (1, -1):
    SH, EL, WR = (11 * s, 24, -28), (28 * s, 28, -25), (30 * s, 20, -31)
    joint(EL, 4.2); joint(WR, 4.4)
    seg(SH, EL, 4.2, 4.7, GOLD, gap=.01)
    seg(EL, WR, 4.8, 5.2, GOLD, l=3)
    palm = rbox((28 * s, 15, -40), (9.5, 9.5, 8.5))
    put(palm, GOLD, p=newid(), l=4)
    put(palm & (Y < 8), GOLDM, p=newid(), l=4)
    fo = chain([(33 * s, 17, -47), (34 * s, 16, -57), (30 * s, 13, -66), (22 * s, 10, -71)], [5.6, 4.7, 3.2, 1.0])
    fi = chain([(21 * s, 10, -47), (18 * s, 8, -55), (18 * s, 6, -62), (21 * s, 5, -67)], [4.6, 3.6, 2.4, .8])
    put(fo, GOLD, p=newid(), l=5); put(fi, BRONZE, st=False)
    kind[cap((26 * s, 11.5, -52), (25 * s, 9.5, -66), 2.4, 1.6) & ~fo & ~fi] = 0         # open jaw gap between the fingers
    for zt in np.arange(-62, -50, 2.5):                                              # serrated inner edges (dark teeth)
        put(cap((28.5 * s, 13.5, zt), (26.0 * s, 12.5, zt), 1.0, .4) & (Z < -50), BRONZED, st=False)
        put(cap((21.2 * s, 8.5, zt), (23.6 * s, 9.5, zt), 1.0, .4) & (Z < -50), BRONZED, st=False)
    put(fo & (Z < -67), BRONZED, st=False); put(fi & (Z < -64.5), BRONZED, st=False)   # dark tips

# ---------------------------------------------------------------- legs: 4 pairs, chunky gold segments, dark joints, dark pointed tips
LEGS = [(-14, (-6, -13, -19)), (-4, (-2, -6, -9)), (6, (3, 7, 11)), (15, (7, 15, 22))]
for i, (z0, (d1, d2, d3)) in enumerate(LEGS):
    for s in (1, -1):
        A = (11 * s, 22, z0); K = (31 * s, 36 - i * .7, z0 + d1); N = (44 * s, 12, z0 + d2); F = (49 * s, 0.5, z0 + d3)
        seg(A, K, 3.4, 3.9, GOLD, gap=.01)
        seg(K, N, 3.9, 3.3, GOLD, gap=1.6, l=3)
        seg(N, F, 3.0, .6, BRONZE, gap=1.2, st=False)
        joint(K, 4.3); joint(N, 3.6)                                                 # dark knuckles proud of the segments

# ---------------------------------------------------------------- tail (metasoma): boxy segments along a smooth arc in the y-z plane
TP = np.array([(32, 27), (39, 34), (50, 39), (60, 40), (67, 35), (71, 26), (70, 15), (65, 6), (60, 0)])   # (y, z)
def catmull(P, k=40):
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return np.array(out)
C = catmull(TP)
S = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; S /= S[-1]
Tg = np.gradient(C, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]
Nr = np.stack([-Tg[:, 1], Tg[:, 0]], 1)                       # normal in the y-z plane
CEN = np.array((48.0, 22.0))                                   # inside of the arc
Nr *= np.sign(((CEN - C) * Nr).sum(1))[:, None]               # normal points to the arc's inside
yy, zz = np.meshgrid(cy, cz, indexing='ij')
iN = np.argmin((yy[..., None] - C[:, 0]) ** 2 + (zz[..., None] - C[:, 1]) ** 2, -1)
off = np.stack([yy - C[iN, 0], zz - C[iN, 1]], -1)
on = (off * Nr[iN]).sum(-1); ot = (off * Tg[iN]).sum(-1)
s2 = S[iN]; r2 = 7.4 - 2.2 * s2                               # radius tapers to the stinger
NSEG = 7
segi = np.minimum((s2 * NSEG).astype(int), NSEG - 1); fr = s2 * NSEG - segi
def b3(a): return np.broadcast_to(a[None], tuple(n))
ON, R, SG, FR, IN2 = b3(on), b3(r2), b3(segi), b3(fr), b3(np.abs(ot) < .75)
tube = IN2 & ((AX / R) ** 4 + (np.abs(ON) / R) ** 4 < 1) & (b3(s2) > .01)
G = .9 * FR                                                    # each segment swells toward its tip end: stepped overlap
tube_g = IN2 & ((AX / (R + G)) ** 4 + (np.abs(ON) / (R + G)) ** 4 < 1) & (b3(s2) > .01)
RC = R - .8                                                    # recessed dark collar radius
collar = IN2 & ((AX / RC) ** 4 + (np.abs(ON) / RC) ** 4 < 1) & (b3(s2) > .01) & (FR < .3)
put(collar, BRONZED, st=False)
for k_ in range(NSEG):
    m_ = tube_g & (SG == k_) & (FR >= .3)
    put(m_ & (ON < .45 * R), GOLD, p=4000 + k_, l=1 + (k_ % 2) * .5)                 # gold segment (back + sides)
    put(m_ & (ON >= .45 * R), BRONZE, st=False)                                     # inner side bronze
# venom slots: glowing windows set in the dark collars (sides + inner side), like the concept
win = collar & (FR > .07) & (FR < .23) & ((AX > RC * .5) | (ON > RC * .5)) & (np.abs(X) > -1)
put(win & (b3(s2) > .1), GLOW[2], k=2, st=False)
put(win & (b3(s2) > .1) & (FR > .11) & (FR < .19), GLOW[3], k=3, st=False)
# stinger: bronze bulb + big faceted magenta crystal hanging forward
put(sd_ell((0, 60.5, -1), (5.0, 5.5, 5.5)) < 0, BRONZE, st=False)
tip = np.array((0, 46.0, -9.0)); base = np.array((0, 58.0, -3.0)); ax_ = tip - base; L = np.linalg.norm(ax_); ax_ /= L
tt = (Y - base[1]) * ax_[1] + (Z - base[2]) * ax_[2]
qy = Y - base[1] - ax_[1] * tt; qz = Z - base[2] - ax_[2] * tt
rr = np.sqrt(X ** 2 + qy ** 2 + qz ** 2)
prof = np.where(tt < 3, 3.6 + tt * .5, 5.1 * (1 - (tt - 3) / (L - 3)))
cry = (tt > -1.5) & (tt < L) & (AX + (np.abs(qy) + np.abs(qz)) * .7 < prof * 1.25) & (rr < prof)
put(cry, GLOW[2], k=2, st=False)
put(cry & (X > 0) & (rr < prof * .7), GLOW[3], k=3, st=False)
put(cry & (X > 1) & (tt > 1) & (tt < 4), GLOW[4], k=4, st=False)
for zc in (-16, -7, 3, 12.5, 21):                                                   # body side windows (magenta) in the dark flank band
    w = (kind == 1) & (np.abs(Z - zc) < 2.4) & (np.abs(Y - (bm - .5)) < 2.0) & (AX > bw - 1.6) & body
    put(w, GLOW[2], k=2, st=False)
    put(w & (np.abs(Z - zc) < 1.2) & (np.abs(Y - (bm - .5)) < 1.0), GLOW[3], k=3, st=False)

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
gold_ = (kind == 1) & (col.min(-1) > .15)
col[gold_] *= (1 + .07 * ((pid[gold_] % 3) - 1))[:, None]     # plate-to-plate tone variation
col *= np.clip(.7 + .45 * (Y / 55.0), .7, 1.2)[..., None]                      # lit tops, dark underside
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('fbd06a', 'efbd4c', 'dca236', 'c68a2c', 'a66e26', '865422', '6a4022',     # gold ladder
                                 '5a3a26', '4a3024', '3b2728', '2a1c1c', '140c0c')])                         # bronze / seam / black
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- mesh: exposed faces (vertex colours) + studs on 2x2 flat tops
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb

STUD_PNG = os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png')
def build(name, mask, with_studs):
    """exposed brick faces as flat quads; UVs = brick coords / 4 so the 4x4 stud tile puts ONE stud on every brick face"""
    verts = []; faces = []; cols = []; uvs = []; nv = 0
    for ax in range(3):
        u, w = [k for k in range(3) if k != ax]
        for s in (1, -1):
            e = np.argwhere(exposed(mask, ax, s))
            if not len(e): continue
            base = lo + e; off = np.zeros(3); off[ax] = 1 if s > 0 else 0
            q = []; t = []
            for du, dw in ((0, 0), (1, 0), (1, 1), (0, 1)):
                dd = off.copy(); dd[u] = du; dd[w] = dw; q.append(base + dd)
                t.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w] + dw) / 16.0], 1))   # Roblox square-stud tile (8x8 studs): one stud per 2x2 bricks
            q = np.stack(q, 1); t = np.stack(t, 1); k = len(e)
            idx = nv + np.arange(4 * k).reshape(k, 4)
            if not ((s > 0) != (ax == 1)): idx = idx[:, ::-1]; t = t[:, ::-1]; q = q[:, ::-1]; idx = nv + np.arange(4 * k).reshape(k, 4)
            verts.append(q.reshape(-1, 3)); faces.append(idx); nv += 4 * k; uvs.append(t.reshape(-1, 2))
            cols.append(np.repeat(col[e[:, 0], e[:, 1], e[:, 2]], 4, axis=0))
    Vt = np.concatenate(verts); Cv = np.concatenate(cols); UV = np.concatenate(uvs)
    Vb = np.stack([Vt[:, 0], Vt[:, 2], Vt[:, 1]], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(Vb.tolist(), [], np.concatenate(faces).tolist())
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.concatenate([lin(np.clip(Cv, 0, 1)), np.ones((len(Cv), 1))], 1).ravel())
    ul = me.uv_layers.new(name='UVMap')
    li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
    ul.data.foreach_set('uv', UV[li].ravel())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
body = build('ScorpionKing', kind == 1, True)
m = bpy.data.materials.new('Brick'); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
bs.inputs['Roughness'].default_value = .6
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
tx.image.colorspace_settings.name = 'Non-Color'                     # overlay values: .5 = unchanged, lighter = highlight, darker = shadow
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 1
nt.links.new(at.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
body.data.materials.append(m); body['glow'] = False
GL = []
for k, c in GLOW.items():
    if not (kind == k).any(): continue
    o = build('Glow%d' % k, kind == k, False)
    gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
    cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
    b2.inputs['Emission Strength'].default_value = 5.0; gm.diffuse_color = cl
    o.data.materials.append(gm); o.color = cl; GL.append(o)
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for nm, p, e in (('EyeL', (5, 24.5, -44), 500), ('EyeR', (-5, 24.5, -44), 500), ('Gem', (0, 32.5, -43), 600), ('Sting', (0, 51, -13), 3000)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.color = (0xd8 / 255, 0x12 / 255, 0xd0 / 255) if nm.startswith('Eye') else (1.0, .2, .95); L.data.shadow_soft_size = 1.0
        L.location = B(*p)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .78, .82)
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.55, .45, .3, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 5000
    def view(name, tgt, dist, az, el, lens=50, ortho=None):
        t = B(*tgt)
        dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
        cam.location = t + dv * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        cam.data.type = 'ORTHO' if ortho else 'PERSP'
        if ortho: cam.data.ortho_scale = ortho
        p = os.path.join(REN, '%s_%s.png' % (ID, name))
        sc.render.engine = ENG; sc.render.film_transparent = False; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_shadows = False; sh.show_cavity = False
        g.hide_render = True; sc.render.film_transparent = True; sc.render.filepath = p[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
        sc.render.film_transparent = False; keep = tuple(sc.world.color); sc.world.color = (0, 0, 0); sh.background_type = 'WORLD'
        body.color = (0, 0, 0, 1)
        sc.render.filepath = p[:-4] + '_glow.png'; bpy.ops.render.render(write_still=True)
        sc.world.color = keep; g.hide_render = False
    cen = (0, 30, -6); D = 250
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 34, -7), 400, az, el, ortho=150)
    for nm, a in (('rest_34', (cen, D, -35, 16)), ('rest_side', (cen, D, 90, 8)), ('rest_front', (cen, D, 0, 8)), ('rest_back', (cen, D, 150, 18)),
                  ('face', ((0, 27, -38), 70, 0, 6)), ('headside', ((0, 28, -36), 90, 90, 4)), ('head34', ((0, 28, -38), 90, -38, 12)),
                  ('footfront', ((-22, 12, -50), 60, -25, 12)), ('feet', ((0, 30, 10), 250, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): body + head, 2 pincer arms (claw + moving jaw), 8 legs x 3, tail chain x 7 + stinger; L = +x
SOL = kind > 0
def ball(c, r): return sd_ell(c, (r, r, r)) < 0
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('body', 'root', (0, 30, 30), (0, 30, -20)), ('head', 'body', (0, 26, -20), (0, 26, -39))]
OVR = [(SOL, 'body'), (SOL & (Z < -19) & (AX < 17) & (Y > 12), 'head')]
ki = [int(round(k / NSEG * (len(C) - 1))) for k in range(NSEG + 1)]                   # tail bones on the arc, one per segment
ki = [int(np.argmin(np.abs(S - k / NSEG))) for k in range(NSEG + 1)]
for k_ in range(NSEG):
    a_, b_ = C[ki[k_]], C[ki[k_ + 1]]
    RIG.append(('tail%d' % (k_ + 1), 'body' if k_ == 0 else 'tail%d' % k_, (0, a_[0], a_[1]), (0, b_[0], b_[1])))
    OVR.append((SOL & (tube_g | collar) & (SG == k_), 'tail%d' % (k_ + 1)))
RIG.append(('stinger', 'tail%d' % NSEG, (0, C[-1][0], C[-1][1]), (0, 46.0, -9.0)))
OVR.append((SOL & ((sd_ell((0, 60.5, -1), (5.0, 5.5, 5.5)) < 0) | cry), 'stinger'))
for sx, sd in ((1, 'L'), (-1, 'R')):
    SH, EL, WR = (11 * sx, 24, -28), (28 * sx, 28, -25), (30 * sx, 20, -31)
    ARM = [('arm%s_up' % sd, 'head', SH, EL), ('arm%s_low' % sd, 'arm%s_up' % sd, EL, WR), ('claw' + sd, 'arm%s_low' % sd, WR, (28 * sx, 14, -60))]
    RIG += ARM + [('clawjaw' + sd, 'claw' + sd, (21 * sx, 10, -46), (21 * sx, 5, -67))]
    side = X * sx > 0
    FO = chain([(33 * sx, 17, -47), (34 * sx, 16, -57), (30 * sx, 13, -66), (22 * sx, 10, -71)], [5.6, 4.7, 3.2, 1.0])
    FI = chain([(21 * sx, 10, -47), (18 * sx, 8, -55), (18 * sx, 6, -62), (21 * sx, 5, -67)], [5.2, 4.2, 3.0, 1.4])
    TI = np.zeros(n, bool); TO = np.zeros(n, bool)                     # inner (jaw) / outer (claw) teeth
    for zt in np.arange(-62, -50, 2.5):
        TI |= cap((21.2 * sx, 8.5, zt), (23.6 * sx, 9.5, zt), 1.4, .9); TO |= cap((28.5 * sx, 13.5, zt), (26.0 * sx, 12.5, zt), 1.4, .9)
    PIN = SOL & side & ~head & (cap(SH, EL, 5.6, 6.0) | cap(EL, WR, 6.0, 6.6) | ball(EL, 5.4) | ball(WR, 5.6) | rbox((28 * sx, 15, -40), (10.5, 10.5, 9.5)) | FO | FI | TI | TO)
    OVR += brick_rig.limb(X, Y, Z, PIN, ARM)
    OVR += [(PIN & (rbox((28 * sx, 15, -40), (10.5, 10.5, 9.5)) | FO | TO), 'claw' + sd), (PIN & (FI | TI) & ~FO & ~TO, 'clawjaw' + sd)]
    for i, (z0, (d1, d2, d3)) in enumerate(LEGS):
        A = (11 * sx, 22, z0); K = (31 * sx, 36 - i * .7, z0 + d1); N_ = (44 * sx, 12, z0 + d2); F = (49 * sx, 0.5, z0 + d3)
        LB = [('leg%d%s_1' % (i + 1, sd), 'body', A, K), ('leg%d%s_2' % (i + 1, sd), 'leg%d%s_1' % (i + 1, sd), K, N_), ('leg%d%s_3' % (i + 1, sd), 'leg%d%s_2' % (i + 1, sd), N_, F)]
        RIG += LB
        LM = SOL & side & (AX > bw + 1.6) & ~rbox((28 * sx, 15, -40), (10.5, 10.5, 9.5)) & (cap(A, K, 4.8, 5.3) | cap(K, N_, 5.3, 4.7) | cap(N_, F, 4.4, 2.0) | ball(K, 5.6) | ball(N_, 4.9))
        OVR += brick_rig.limb(X, Y, Z, LM, LB)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (0, 0, 10), 'clawjawL': (0, 0, 30), 'clawjawR': (0, 0, -30), 'armR_up': (25, 0, 0), 'leg2L_1': (0, 0, 20), 'tail5': (-15, 0, 0), 'stinger': (-25, 0, 0)},
                 render='render' in argv)
print('BL_OK')
