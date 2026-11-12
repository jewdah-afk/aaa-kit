# Giant Kraken boss (stud-voxel, brick pipeline; machinery copied from the skill's war_rhino_brick.py)
# GLOW: per-colour (no 'strong' flag): after run_brick.ps1 run `py kraken_post.py` = tight eye halo, soft small cyan halo
# Reference = concept_sheet.jpg. Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'Kraken'
STUD_PNG = next(q for q in (os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png'),   # inside the skill (examples/brick)
                            os.path.expanduser(r'~/.claude/skills/stud-voxel-creatures/assets/roblox_square_studs.png')) if os.path.exists(q))

lo = np.array((-70.0, -0.5, -60.0)); hi = np.array((70.0, 68.5, 56.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8)                                 # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
PD = hx('4c1f96'); PM = hx('6a30c4'); PV = hx('a072f0'); PK = hx('2a1050')           # deep / mid / violet / darkest
TE = hx('2a9aa0'); TD = hx('1a5f6c'); PI = hx('f8c2d0'); PID = hx('a65a7c')           # teal / teal dark / sucker pink / pink dark
TAN = hx('dcc89c'); TAND = hx('140a1e'); COR = hx('e0402e'); SEA = hx('6aa02a')
WL = hx('86d4f2'); WM = hx('3c9ed8'); WH = hx('eef8ff'); BLACK = hx('140a1e')
GLOW = {2: hx('2ef2ff'), 3: hx('ffcc14')}                                           # cyan spots / eyes (ONE flat glow colour)

def put(m, rgb, k=1, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; pid[m] = p; lvl[m] = l

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1, sym=True):
    xx = AX if sym else X
    return (xx > x0) & (xx < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def ix(v, a): return int(round(v - lo[a] - .5))

rng = np.random.RandomState(7)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ---------------------------------------------------------------- teal skirt / underside + siphon column
sk = sd_ell((0, 17, 0), (20, 10, 17))
put(sk < 0, TE, p=newid(), l=0)
for b in range(4):                                                      # stepped teal rings
    put((sk < 0) & (sk > -1.6) & (np.abs(Y - (11 + 3 * b)) < .5), TD)
SIPH = newid()
SP_ = chain([(0, 12, -16), (0, 6, -19), (0, 2, -21)], [3.6, 3.8, 4.4])
put(SP_, TE, p=SIPH, l=1); put(SP_ & (np.mod(Y, 3) < 1), TD, p=SIPH, l=1)
for sx in (1, -1):                                                      # wide teal jowls flanking the beak
    jw = sd_ell((12 * sx, 21, -12), (8.5, 8, 7.5)) < 0
    put(jw, TE, p=3300, l=1); put(jw & (np.mod(Y, 3) < 1), TD, p=3300, l=1)

# ---------------------------------------------------------------- head: face block + big swept-back mantle with stepped ridges
dh = sd_ell((0, 30, -6), (18, 13.5, 13))                                # face / lower head
dm = sd_ell((0, 49, 3), (19, 17.5, 18))                                 # mantle front dome
dm = smin(dm, sd_ell((0, 47, 21), (16, 14, 18)), 5)                     # mantle swept back
dm = smin(dm, sd_ell((0, 39, 8), (18.5, 11, 18)), 4)
d = smin(dh, dm, 5)
ang = np.arctan2(X, -Z)                                                # 0 = front
band = np.floor((Y - 20 + 1.1 * np.sin(ang * 3 + 1.0) + .7 * np.sin(ang * 7)) / 3.0).astype(int)
segm = np.floor((ang + np.pi) / (2 * np.pi) * 9 + band * .5).astype(int)  # stagger blocks like masonry
SWT = np.array((.2, .95, .5, 1.15, .65, .3, 1.0))
blk = band * 31 + segm
swell = SWT[np.mod(band * 5 + segm * 3, len(SWT))]
head = d < swell
put(head, PM, p=0, l=0)
pid[head] = 30000 + blk[head]; lvl[head] = swell[head]

# back ridge stripe and cyan dots running down the back (back view)

jowl = head & (Y < 26) & (AX > 5.5) & (Z < 4)                           # teal jowls / skirt showing under the cheeks
put(jowl, TE, p=3300, l=1); put(jowl & (np.mod(Y, 3) < 1), TD, p=3300, l=1)

# ---------------------------------------------------------------- tentacles: Catmull-Rom spine, stepped bands, pink sucker side, cyan spots
def catmull(P, step=.4):
    P = np.array(P, float); P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        m = max(2, int(np.linalg.norm(p2 - p1) / step))
        for t in np.linspace(0, 1, m, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2]); return np.array(out)

def tentacle(P, r0, r1, spot_every=4.2, mirror=1, nb=None):
    P = [(x * mirror, y, z) for x, y, z in P]
    C = catmull(P); seg = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    R = r0 + (r1 - r0) * (s / L) ** .85
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    A = np.gradient(T, axis=0)
    for _ in range(6): A[1:-1] = (A[:-2] + A[1:-1] + A[2:]) / 3            # smoothed curvature
    down = np.array((0, -1.0, 0)); Nn = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)
    Nn = Nn * np.clip(np.linalg.norm(A, axis=1, keepdims=True) * 40, 0, 1) + down * .25
    if nb is not None: Nn = Nn + np.array((nb[0] * mirror, nb[1], nb[2]))
    Nn -= T * (Nn * T).sum(1, keepdims=True); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
    m0 = C.min(0) - r0 - 5; m1 = C.max(0) + r0 + 5
    a0 = [max(0, ix(m0[k], k)) for k in range(3)]; a1 = [min(n[k], ix(m1[k], k) + 1) for k in range(3)]
    sl = tuple(slice(a0[k], a1[k]) for k in range(3))
    Xs, Ys, Zs = X[sl], Y[sl], Z[sl]
    bd = np.full(Xs.shape, 1e9); bi = np.zeros(Xs.shape, int); bt = np.zeros(Xs.shape)
    for i in range(len(C) - 1):
        a = C[i]; ab = C[i + 1] - a; l2 = ab.dot(ab) + 1e-9
        t = np.clip(((Xs - a[0]) * ab[0] + (Ys - a[1]) * ab[1] + (Zs - a[2]) * ab[2]) / l2, 0, 1)
        dd = np.sqrt((Xs - a[0] - ab[0] * t) ** 2 + (Ys - a[1] - ab[1] * t) ** 2 + (Zs - a[2] - ab[2] * t) ** 2)
        rr = R[i] + (R[i + 1] - R[i]) * t
        q = dd - rr; w = q < bd
        bd[w] = q[w]; bi[w] = i; bt[w] = t[w]
    sv = s[bi] + seg[np.minimum(bi, len(seg) - 1)] * bt
    Rv = R[bi]
    cp = C[bi] + (C[np.minimum(bi + 1, len(C) - 1)] - C[bi]) * bt[..., None]
    v = np.stack([Xs, Ys, Zs], -1) - cp; vl = np.linalg.norm(v, axis=-1) + 1e-9
    cosn = (v * Nn[bi]).sum(-1) / vl
    Bn = np.cross(T, Nn); lat = (v * Bn[bi]).sum(-1)                                    # +1 = concave (sucker) side, -1 = top
    bandi = np.floor(sv / 2.6).astype(int)
    sw = np.where(bandi % 2 == 0, .55, 0.0) * (sv < L - 3)               # stepped segments
    inside = bd < sw
    ph = np.mod(sv, 2.4)
    sub_col = col[sl]; sub_kind = kind[sl]; sub_pid = pid[sl]; sub_lvl = lvl[sl]
    base_id = newid() * 100
    top = np.where((cosn < -.55)[..., None], PV, PM); side = np.where(((cosn > 0)[..., None]), PD, top)   # light-violet tops, dark undersides
    # evenly tiled square suckers: 3x3-brick light squares, 1-brick dark gaps, 1 brick proud, framed by purple.
    # 2 rows (one each side of the centre groove) on thin parts, 4 on the thick base: every square the same size
    tile = (np.mod(sv, 4.0) < 3.0) & (np.mod(np.abs(lat) - .5, 4.0) < 3.0) & (np.abs(lat) > .5) & (np.abs(lat) < .92 * Rv) & (sv > 2) & (sv < L - 1.5)
    proud = tile & (cosn > .5) & (bd >= sw) & (bd < sw + 1.0) & (Rv > 2.2)
    occ = inside | proud
    pink = occ & (cosn > .15) & (np.abs(lat) < .92 * Rv + .5)
    c = np.where(occ[..., None], side, sub_col)
    c[pink] = PID
    c[pink & tile] = PI
    sub_col[...] = c
    sub_kind[occ] = 1
    TMASK.append(np.zeros(n, bool)); TMASK[-1][sl] = occ
    sub_pid[occ] = 0
    # cyan spots along the top (convex) side: 1-2 voxel dots, flush in the surface
    spot = inside & (cosn < -.45) & (np.abs(lat) < .75) & (bd > -1.2) & (np.mod(sv + 1.0, spot_every) < 1.0) & (sv > 3) & (sv < L - 5)
    sub_kind[spot] = 2; sub_col[spot] = GLOW[2]
    j = int(np.argmin(C[:, 1])); return C, C[j]

# (azimuth pairs, mirrored in x). Paths written for the +x side.
CONTACT = []; TMASK = []; TCURVE = []
TP = [
    # A: front inner pair = the "beak" legs under the nose, arching down to the water in front
    ([(15, 12, -8), (15, 10, -20), (14, 7, -29), (15, 5, -36), (19, 6, -42), (24, 10, -42), (24, 15, -39)], 6.0, 2.0),
    # B: front-side pair: up over, down to the water, tip curls up and out
    ([(12, 22, -8), (21, 32, -14), (30, 31, -20), (36, 18, -25), (39, 7, -28), (46, 5, -30), (53, 9, -30), (54, 16, -27), (48, 19, -25)], 8.6, 2.2),
    # C: high pair: rises tall, tip hooks over outward and curls back in (question mark)
    ([(13, 26, 6), (27, 33, 6), (37, 43, 4), (40, 51, 2), (36, 56, 0), (30, 55, -1), (28, 50, -1), (31, 46, -1)], 7.8, 2.0),
    # D: back-low pair: arches out sideways/back, down to the water, tip curls up
    ([(12, 18, 10), (24, 28, 16), (35, 25, 21), (42, 10, 24), (47, 5, 26), (55, 7, 26), (59, 12, 23), (57, 18, 21), (51, 18, 20)], 8.4, 2.0),
]
for k_, (P, r0, r1) in enumerate(TP):
    for mir in (1, -1):
        C, cpt = tentacle(P, r0, r1, mirror=mir, nb=(-1.0, -.4, 1.0) if k_ == 0 else None); CONTACT.append(cpt)
        TCURVE.append(('t%s%s' % ('ABCD'[k_], 'L' if mir > 0 else 'R'), C))

# ---------------------------------------------------------------- face: brow, recessed slit eyes, nose ridge, mouth
def front():                                                          # frontmost solid z index per (x, y)
    o = kind > 0; return np.where(o.any(2), np.argmax(o, axis=2), -1)
FRONT = front()
def paint_front(mask2d, rgb, k=1, depth=1, back=0, p=0, l=0.0):
    for i, j in np.argwhere(mask2d):
        z0 = FRONT[i, j]
        if z0 < 0: continue
        col[i, j, z0 + back:z0 + back + depth] = rgb; kind[i, j, z0 + back:z0 + back + depth] = k
        pid[i, j, z0 + back:z0 + back + depth] = p; lvl[i, j, z0 + back:z0 + back + depth] = l
X2, Y2 = X[:, :, 0], Y[:, :, 0]; AX2 = np.abs(X2)
# eyes: x 3.5..11.5, angry almond: top edge slopes down to the centre, outer corner high
eye_top = 33.6 + (AX2 - 4.5) * .26; eye_bot = 29.0 + (AX2 - 4.5) * .30
EYE = (AX2 > 4.5) & (AX2 < 14.5) & (Y2 > eye_bot) & (Y2 < eye_top)
SOCK = (AX2 > 3.5) & (AX2 < 15.5) & (Y2 > eye_bot - 1) & (Y2 < eye_top + 1) & ~EYE
# recess: clear the front layer over the eye, paint the eye one brick deeper
for i, j in np.argwhere(EYE):
    z0 = FRONT[i, j]
    if z0 >= 0 and Z[i, j, z0] < -14: kind[i, j, z0] = 0; FRONT[i, j] = z0 + 1
paint_front(SOCK & (Y2 > 24), BLACK, depth=2)
paint_front(EYE, GLOW[3], k=3, depth=2)
# brow: heavy plates stepping down toward the centre, overhanging the eyes by 2 bricks
BR = newid()
for xa, xb, y0 in ((2, 5.5, 32.5), (5.5, 8.5, 33.5), (8.5, 11.5, 34.5), (11.5, 18, 35.5)):   # V brow, inner end lowest
    put(box(xa, xb, y0, y0 + 3.2, -22, -10) & (sd_ell((0, 35, -8), (20, 8, 15)) < 0), PM, p=BR, l=5)
put(box(0, 2.1, 31.5, 36.5, -22, -10) & (sd_ell((0, 35, -8), (20, 8, 15)) < 0), PM, p=BR, l=5)
put(box(1.5, 18, 31.5, 37, -22, -21) & (kind == 1) & (pid == BR) & (Y < 33.5 + (AX - 2) * .3), PK)   # dark brow underside                      # brow underside shadow line
# nose ridge running down into the beak legs, dark mouth cavity between them
NO = newid()
put(chain([(0, 33, -19.5), (0, 27, -21), (0, 23, -21.5)], [2.6, 2.8, 3.0]), PM, p=NO, l=4)
put(chain([(0, 32, -20.5), (0, 25, -22.2)], [1.0, 1.0]), PV, p=NO, l=4)
FRONT = front()
MOUTH = (AX2 < (24 - Y2) * .55 - 2.4) & (Y2 > 10) & (Y2 < 22)            # dark mouth wedge inside the beak legs
for i, j in np.argwhere(MOUTH):
    z0 = FRONT[i, j]
    if z0 >= 0 and Z[i, j, z0] < -12: kind[i, j, z0] = 0; FRONT[i, j] = z0 + 1
paint_front(MOUTH, BLACK, depth=3)
for sx in (1, -1):                                                      # beak legs: the inverted V under the nose
    lg = chain([(0, 25, -21.5), (5.5 * sx, 17, -22.5), (9 * sx, 9, -21.5)], [3.6, 3.4, 3.1])
    put(lg, PM, p=NO + 1, l=4)
    put(lg & (np.abs(X - (np.clip((24.5 - Y) * .58, 0, 9) * sx)) < 1.0) & (Z < -23.5), PV, p=NO + 1, l=4)

# ---------------------------------------------------------------- forehead rune (cyan), painted flush in the mantle front
RU = np.zeros(X2.shape, bool)
RU |= (AX2 < .6) & (Y2 > 40) & (Y2 < 60)                              # spine
for y0, w, rise in ((57, 6.5, .9), (51, 9, .7), (45, 10.5, .55)):     # chevrons: arms rise outward (trident / tree)
    yy = y0 + (AX2 - 1) * rise
    RU |= (AX2 > 1.4) & (AX2 < w) & (np.abs(Y2 - yy) < .55)
RU |= (np.abs(AX2 - 3.0) < .6) & (Y2 > 59) & (Y2 < 63)                 # top fork tips
paint_front(RU & (Y2 > 39), GLOW[2], k=2, depth=1)
# back of the mantle: stepped spine ridge (1 then 2 bricks proud) + cyan line with a diamond
back = (Z > 2) & (Y > 28) & (Y < 62)
r1 = back & (AX < 3.5) & (d >= swell) & (d < swell + 1.0); r2 = back & (AX < 1.5) & (d >= swell) & (d < swell + 2.0) & (Y > 32) & (Y < 58)
put(r1 & (kind == 0), PM, p=3400, l=3); put(r2 & (kind == 0), PV, p=3401, l=4)
def last():
    o = kind > 0; return np.where(o.any(2), n[2] - 1 - np.argmax(o[:, :, ::-1], axis=2), -1)
BACKZ = last()
BR_ = ((AX2 < 1) & (Y2 > 40) & (Y2 < 56)) | ((np.abs(AX2 + np.abs(Y2 - 48) * .8 - 4.5) < .75) & (AX2 > 1))
for i, j in np.argwhere(BR_):
    z1 = BACKZ[i, j]
    if z1 >= 0 and Z[i, j, z1] > 10: kind[i, j, z1] = 2; col[i, j, z1] = GLOW[2]

# ---------------------------------------------------------------- barnacles, coral, seaweed on the head
def top_y(x, z):
    xi, zi = ix(x, 0), ix(z, 2); w = np.where(kind[xi, :, zi] > 0)[0]
    return cy[w[-1]] if len(w) else None
for (bx, bz, r, h) in ((11, -1, 2.0, 3), (15, -4, 1.7, 2.5), (10, 5, 1.6, 2.5), (14.5, 3, 1.5, 2), (16, 9, 1.7, 2.5), (-11, 10, 1.6, 2.5), (12.5, 12, 1.5, 2.5), (8, 9, 1.4, 2), (-13, 13, 1.4, 2), (17, 3, 1.3, 2)):
    yt = top_y(bx, bz)
    if yt is None: continue
    cyl = ((X - bx) ** 2 + (Z - bz) ** 2 < r * r) & (Y > yt - 2) & (Y < yt + h + .5)
    put(cyl, TAN, p=newid(), l=6)
    put(((X - bx) ** 2 + (Z - bz) ** 2 < (r * .45) ** 2 + .3) & (np.abs(Y - (yt + h)) < .6), TAND)
CORAL = (((-12, -2), 1.0), ((-15, 6), .85), ((-9, 12), .75), ((16, -9), .7))
for (bx_, bz_), sc_ in CORAL:                                           # red coral clumps: trunk + 2 forks + side sprigs
    yt = top_y(bx_, bz_)
    if yt is None: continue
    sg = np.sign(bx_)
    tr = [(bx_, yt - 1, bz_), (bx_ + sg * 1 * sc_, yt + 5 * sc_, bz_ - .5), (bx_ + sg * 2.5 * sc_, yt + 10 * sc_, bz_ - 1)]
    put(chain(tr, [1.3 * sc_ + .2, 1.1 * sc_ + .2, .9 * sc_ + .2]), COR, p=newid(), l=6)
    for a_, dx_, dy_, dz_ in ((tr[1], -3, 4, 0), (tr[1], 2.5, 3, 1), (tr[2], -2, 3, 0), (tr[2], 2, 2.5, -1)):
        put(cap(a_, (a_[0] + dx_ * sc_, a_[1] + dy_ * sc_, a_[2] + dz_), .9, .7), COR, p=newid(), l=6)
WEED = ((17.5, -6, 14), (18.5, 0, 17), (18.5, 6, 13), (16, 11, 11), (-18, -4, 12), (-18.5, 3, 14), (-16, 9, 10))
for (sx, sz, ln) in WEED:                                               # thick green seaweed strands hanging down the head sides
    yt = top_y(sx * .9, sz) or 48
    pts = [(sx + np.sign(sx) * (.4 + .9 * math.sin(k * 1.1 + sz)), yt - 1 - k * 2.0, sz - 1.2) for k in range(int(ln / 2))]
    put(chain(pts, [1.15] * len(pts)), SEA, p=newid(), l=7)
for sx in (1, -1):                                                      # seaweed draped over the front tentacles
    pts = [(14 * sx + .8 * math.sin(k), 13 - k * 1.8, -20 - k * .6) for k in range(5)]
    put(chain(pts, [1.1] * 5), SEA, p=newid(), l=7)

# ---------------------------------------------------------------- water: flat ring with blocky splash crests
WAT = np.zeros(X2.shape if False else (n[0], n[2]), bool)
XZx, XZz = X[:, 0, :], Z[:, 0, :]
crest = np.zeros((n[0], n[2]))
edge = np.sqrt((XZx / 61) ** 2 + (XZz / 44) ** 2) + .07 * np.sin(XZx * .5) * np.cos(XZz * .4)
WAT |= edge < 1
for (ccx, ccz, r) in [(0, -6, 20)] + [(c[0], c[2], 11) for c in CONTACT]:   # splash crests ring each tentacle where it meets the water
    dd = np.sqrt((XZx - ccx) ** 2 + (XZz - ccz) ** 2)
    crest = np.maximum(crest, np.clip(1 - np.abs(dd - r * .75) / 2.5, 0, 1))
hsh = (np.floor(XZx / 2) * 73856093 + np.floor(XZz / 2) * 19349663).astype(np.int64) % 97 / 97.0
H = 1 + np.round(crest * (1 + 3 * hsh) * (hsh > .25)).astype(int)
H = np.where(WAT, H, 0)
for j in range(6):
    m2 = (H > j) & (kind[:, j, :] == 0)
    c = np.where(((H == j + 1) & (H > 2))[..., None], WH, WM if j == 0 else WL)
    col[:, j, :][m2] = c[m2]
    kind[:, j, :][m2] = 1; pid[:, j, :][m2] = 9000; lvl[:, j, :][m2] = 0

# ---------------------------------------------------------------- seams + shading + palette
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
dark &= (pid != 9000)
col[dark & (kind == 1)] *= .7
nolight = (pid == 9000) | ((kind == 1) & ((np.abs(col - PI).sum(-1) < .02) | (np.abs(col - PID).sum(-1) < .02) | (np.abs(col - TAN).sum(-1) < .02) | (np.abs(col - COR).sum(-1) < .02) | (np.abs(col - SEA).sum(-1) < .02)))
col *= np.where(nolight[..., None], 1.0, np.clip(.8 + .45 * (Y / 60.0), .8, 1.2)[..., None])
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('a878f4', '7438cc', '56249e', '3a1670', '220c40',     # purples: violet / mid / main / dark / seam
                                 '34aab0', '1d6670',                                  # teal / teal dark
                                 'f8c2d0', 'a65a7c',                                  # sucker pink / pink dark
                                 'dcc89c', 'e0402e', '6aa02a', '3c9ed8',              # barnacle / hole / coral / seaweed
                                 '86d4f2', 'f0faff', '140a1e')])                      # water / foam / black
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- mesh: exposed faces (vertex colours) + square-stud overlay
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb

def build(name, mask, with_studs):
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
                t.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w] + dw) / 16.0], 1))
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
body = build('Kraken', kind == 1, True)
m = bpy.data.materials.new('Brick'); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
bs.inputs['Roughness'].default_value = .6
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
tx.image.colorspace_settings.name = 'Non-Color'
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
    for sx in (1, -1):                                                         # yellow eye lights
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 600; L.data.color = (1.0, .82, .2); L.data.shadow_soft_size = 1.0
        L.location = B(9.5 * sx, 31.5, -24.0)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .8, .9)
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.06, .16, .26, 1)
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
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 30, -2), 400, az, el, ortho=142)
    cen = (0, 24, -2); D = 195
    for nm, a in (('rest_34', (cen, D, -35, 12)), ('rest_side', (cen, D, 90, 6)), ('rest_front', (cen, D, 0, 8)), ('rest_back', (cen, D, 160, 14)),
                  ('face', ((0, 38, -18), 88, 0, 4)), ('headside', ((0, 40, 2), 125, 90, 4)), ('head34', ((0, 38, -8), 120, -38, 10))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): head + 8 tentacles x 4 segments, water on root
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('head', 'root', (0, 12, 0), (0, 56, 10))]
TENT = np.zeros(n, bool); OVR = []
for (nm, C), M in zip(TCURVE, TMASK):
    s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
    P_ = [tuple(C[np.argmin(np.abs(s_ - s_[-1] * f))]) for f in (0, .25, .5, .75, 1)]
    ch = [('%s_%d' % (nm, i + 1), 'head' if i == 0 else '%s_%d' % (nm, i), P_[i], P_[i + 1]) for i in range(4)]
    RIG += ch; M = M & (kind > 0) & (pid != 9000); TENT |= M; OVR += brick_rig.limb(X, Y, Z, M, ch)
WATER = (pid == 9000) & (kind > 0)
OVR = [(~TENT & ~WATER, 'head')] + OVR + [(WATER, 'root')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (0, 0, 12), 'tCL_2': (35, 0, 0), 'tBR_2': (0, 0, -30), 'tAL_3': (-30, 0, 0), 'tDL_1': (0, 0, 20)},
                 render='render' in argv)
print('BL_OK')
