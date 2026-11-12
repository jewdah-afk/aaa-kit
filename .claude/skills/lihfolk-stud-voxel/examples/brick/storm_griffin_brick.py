# Storm Griffin (stud-voxel boss, brick pipeline). Reworked from the skill's War Rhino example.
# GLOW: subtle   (read by scripts/run_brick.ps1: not strong = crisp glow, small halo only)
# Reference = concept_sheet.jpg (same folder). Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs).
# Body/legs/head/tail are modelled in DESIGN space and scaled by S into the grid; wings are built straight in grid space.
# Run: powershell -File <skill>\scripts\run_brick.ps1 storm_griffin_brick.py
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'StormGriffin'
S = 1.6                     # body/legs/head scale (design -> grid)
SX = S * 1.1                # extra width: heavy, broad body
DY = 4.0                    # crouch: body space sits DY (design units) lower than the legs were modelled

lo = np.array((-128.0, -0.5, -84.0)); hi = np.array((128.0, 172.5, 120.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
GX, GY, GZ = np.meshgrid(cx.astype(np.float32), cy.astype(np.float32), cz.astype(np.float32), indexing='ij')
X, Y, Z = GX / SX, GY / S, GZ / S; AX = np.abs(X)            # design space (legs)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
WHITE = hx('f2f4f7'); LGREY = hx('c4c9d2'); MGREY = hx('8d94a3'); DGREY = hx('4a4d5c'); STORM = hx('34363f'); DEEP = hx('262a34')
TALON = hx('15161b'); GOLD_L = hx('f2c14e'); GOLD = hx('d99a2b'); GOLD_D = hx('a8691c'); GOLD_S = hx('70460f')
BEAK = hx('ffcf3a'); BEAK_D = hx('e39a1c'); MOUTH = hx('6e1a22'); TONGUE = hx('c4434e')
GLOW = {2: hx('1e8cff'), 3: hx('5fdcff'), 4: hx('f2feff')}   # electric blue / cyan / white-hot core

REC = []                                                                         # rig: masks recording which puts belong to a part
def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l
    for r_ in REC: r_ |= m

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def sd_ells(c, r):                                    # mirrored pair (|x|)
    px, py, pz = (AX - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def chain_t(pts, radii, sym=False):                 # capsule chain -> (mask, t 0..1 along it, signed dist); sym = mirrored in x
    pts = [np.array(p, float) for p in pts]; L = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    acc = np.concatenate([[0], np.cumsum(L)]) / sum(L)
    XX = AX if sym else X
    best = np.full(n, 1e9); T = np.zeros(n)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a
        t = np.clip(((XX - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
        dd = np.sqrt((XX - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2) - (radii[i] + (radii[i + 1] - radii[i]) * t)
        w = dd < best; best[w] = dd[w]; T[w] = acc[i] + (acc[i + 1] - acc[i]) * t[w]
    return best <= 0, T, best
def chain(pts, radii, sym=False): return chain_t(pts, radii, sym)[0]
def hashv(a, b, s=0):
    v = np.sin(a * 12.9898 + b * 78.233 + s * 37.719) * 43758.5453
    return v - np.floor(v)
def pdist2(U, V, pts):                               # distance in a 2D plane to a polyline
    best = np.full(np.broadcast(U, V).shape, 1e9)
    for i in range(len(pts) - 1):
        a = np.array(pts[i], float); b = np.array(pts[i + 1], float); ab = b - a
        t = np.clip(((U - a[0]) * ab[0] + (V - a[1]) * ab[1]) / ab.dot(ab), 0, 1)
        best = np.minimum(best, np.hypot(U - a[0] - ab[0] * t, V - a[1] - ab[1] * t))
    return best

# ---------------------------------------------------------------- front legs (built first, real heights): short, very heavy eagle legs + big hooked talons
FL, flt, _ = chain_t([(13, 24, -12), (14, 13, -15), (14, 6, -14)], [10.5, 9.0, 7.8], sym=True)
put(FL, GOLD, p=20, l=0)
band = (hashv(np.floor(X / 3.2) + 7 * np.floor(Z / 3.2), np.floor(Y / 3.2), 5) > .62) & FL & (Y < 22)
put(band, GOLD_L, p=21, l=1)                                         # scattered light scale blocks (no bee stripes)
put(FL & (Y < 7) & ~band, GOLD_D, p=20, l=0)
for dx in (-4.8, 0.0, 4.8):                                         # 3 front toes + big stepped talons hooking forward-down
    xt = 14 + dx * 1.25
    T_, tt, _ = chain_t([(14 + dx * .4, 5.5, -17), (14 + dx, 4.0, -22.5), (xt, 3.8, -26.5)], [3.6, 3.2, 2.9], sym=True)
    put(T_ & (kind == 0), GOLD, p=22, l=0)
    put(T_ & (np.floor(tt * 4) % 2 == 1), GOLD_L, p=23, l=1)
    for (hw_, y0, y1, z0, z1, c_) in ((2.4, 2.5, 7.0, -30.5, -26.0, DGREY), (1.7, .5, 4.5, -33.5, -29.5, DGREY), (1.0, -.3, 2.0, -35.5, -32.5, TALON)):
        put((np.abs(AX - abs(xt)) < hw_) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1), c_, st=False)
put(chain([(14, 5, -9), (14, 3.5, -4.5)], [3.0, 2.4], sym=True) & (kind == 0), GOLD, p=22, l=0)   # back toe
put(chain([(14, 4.0, -4), (14, 4.2, -1.6), (14, 1.8, .2)], [1.8, 1.4, 1.0], sym=True), DGREY, st=False)
put(chain([(14, 1.8, .2), (14, -.2, -.2)], [1.0, .45], sym=True), TALON, st=False)

# ---------------------------------------------------------------- hind legs: heavy lion legs, hock, wide paws with big hooked claws
HL = chain([(14, 21, 26), (14.5, 11, 33), (14.5, 5, 31)], [11.5, 8.6, 7.6], sym=True)
put(HL, GOLD, p=30, l=0)
put((sd_ells((14.5, 3.0, 26.5), (8.6, 3.8, 9.0)) < 0) & (kind == 0), GOLD, p=31, l=0)     # paw
for dx in (-5.4, -1.8, 1.8, 5.4):
    put((sd_ells((14.5 + dx, 3.0, 18.6), (1.7, 2.8, 2.1)) < 0), GOLD_L, p=32, l=1)          # toe bumps
    put(chain([(14.5 + dx, 3.2, 17.0), (14.5 + dx, 3.4, 15.4), (14.5 + dx, 1.4, 14.2)], [1.6, 1.3, .9], sym=True), DGREY, st=False)
    put(chain([(14.5 + dx, 1.4, 14.2), (14.5 + dx, -.2, 14.6)], [.9, .4], sym=True), TALON, st=False)

Y = Y + DY          # crouch: everything below is modelled in "body space" and lands DY lower in the grid

# ---------------------------------------------------------------- lion body: deep chest, tucked waist, big haunches. Front = -z.
d = sd_ell((0, 33, 6), (19.5, 13.5, 20))                            # barrel (short)
d = smin(d, sd_ell((0, 38, -10), (21.5, 17, 14)), 6)                # deep HIGH chest
d = smin(d, sd_ell((0, 46, -6), (17, 8.5, 11)), 5)                  # arched shoulder hump
d = smin(d, sd_ell((0, 32, 22), (19, 13, 11)), 6)                 # rump (low, crouched)
d = smin(d, sd_ell((0, 27, 6), (13, 7.5, 16)), 5)                     # belly
d = smin(d, sd_ells((14, 27.5, 24), (11.5, 15, 13)), 4)          # big crouched lion haunch
d = smin(d, sd_ells((13, 30, -12), (8.5, 11, 8.5)), 4)              # eagle shoulders
bodym = d < 0
put(bodym & (kind == 0), GOLD, p=1, l=0)
# chunky muscle blocks on the hide: offset rows of 10x6x10 cells, ~60% stand proud, each block thickest at its bottom
RYb = np.floor(Y / 6); OFb = 5 * (RYb % 2)
CXb = np.floor((AX + OFb) / 10); CZb = np.floor((Z + OFb) / 10); FYb = (Y - RYb * 6) / 6
PRb = hashv(CXb * 7 + CZb, RYb, 4) > .4
blk = (d >= -.5) & (d < .5 + (.6 + .9 * (1 - FYb)) * PRb) & (Y > 19) & ((kind != 1) | bodym)
blk &= ~((kind == 1) & (pid >= 20) & (pid < 40))                                  # never over the legs
code = (60 + (CXb * 13 + CZb * 7 + RYb * 3) % 39).astype(np.int32)
for k_ in np.unique(code[blk]):
    m_ = blk & (code == k_)
    put(m_, GOLD, p=int(k_), l=1)
put(blk & (FYb > .7), GOLD_L)                                                    # light top band of every block
put((kind == 1) & (pid >= 1) & (pid < 100) & ((pid < 20) | (pid >= 40)) & (pid != 50) & (pid != 51) & (Y < 25), GOLD_D)     # dark underside

# ---------------------------------------------------------------- neck, head, chest ruff (feathered). Head is wide; beak stays compact.
dh = sd_ell((0, 62, -30), (15, 12, 12))                          # skull (wide)
dh = smin(dh, sd_ell((0, 51, -25), (14, 12, 10)), 5)              # neck
dh = smin(dh, sd_ell((0, 40, -20), (19, 14, 9.5)), 5)             # chest bib
dh = smin(dh, sd_ell((0, 46, -10), (19, 10.5, 10.5)), 5)              # ruff over the shoulders
dh = smin(dh, sd_ells((11, 58, -29), (7, 8.5, 7.5)), 3)              # cheek flare
head = dh < 0
put(head & (kind == 0), WHITE, p=40, l=0)
put(head & (kind == 1) & (Y > 30), WHITE, p=40, l=0)
RYc = np.floor((Y + 2) / 7); OFc = 4 * (RYc % 2)
CXc = np.floor((AX + OFc) / 8); CZc = np.floor((Z + OFc) / 8); FYc = (Y + 2 - RYc * 7) / 7
PRc = hashv(CXc * 5 + CZc, RYc, 8) > .35
coat = (dh >= 0) & (dh < .5 + (.6 + 1.0 * (1 - FYc)) * PRc) & (Y > 27)
codec = (2300 + CXc * 97 + (CZc + 10) * 13 + RYc * 3).astype(np.int32)
rowY = RYc * 7 + 1.5
for k_ in np.unique(codec[coat]):
    m_ = coat & (codec == k_)
    put(m_, WHITE, p=int(k_), l=float(PRc[m_][0]))
put(coat & (rowY < 52) & (hashv(CXc * 3 + CZc, RYc, 21) > .55), LGREY)          # mixed white / light-grey shingles
put(coat & (rowY < 46) & (Z > -2), MGREY)                                         # ruff darkens over the lion back
FACEZ = (dh >= 0) & (dh < 2.4) & (Y > 49) & (Z < -27)
kind[FACEZ & (pid >= 2000) & (pid < 2900)] = 0
put((dh >= 0) & (dh < .6) & (Y > 49) & (Z < -27) & (kind == 0), WHITE, p=2950, l=0)
for (x0, x1, y0, y1, pp_) in ((6.5, 15.5, 49.5, 57.5, 2951), (12.5, 18.5, 57.5, 68.5, 2952), (0, 10.5, 67.5, 74.5, 2953)):
    put((dh >= .4) & (dh < 1.7) & (AX >= x0) & (AX < x1) & (Y >= y0) & (Y < y1) & (Z < -24) & (kind == 0), WHITE, p=pp_, l=1)
# face plates: flatten the front of the head into stepped columns (clean blocks, not noise)
FS = (kind == 1) & (pid >= 2000) & (pid < 3000) & (Z < -20) & (Y > 30)
ZI = np.arange(n[2])
zf = np.where(FS, ZI[None, None, :], 10 ** 6).min(axis=2)
XB = np.floor(np.abs(cx / SX) / 5.5)[:, None] * np.sign(cx)[:, None]; YB = np.floor((cy / S + DY - 30) / 6.5)[None, :]
XB2 = np.broadcast_to(XB, zf.shape); YB2 = np.broadcast_to(YB, zf.shape)
cid = 0
for xb in np.unique(XB2[zf < 10 ** 6]):
    for yb in np.unique(YB2[zf < 10 ** 6]):
        cm = (zf < 10 ** 6) & (XB2 == xb) & (YB2 == yb)
        if cm.sum() < 6: continue
        zc = int(np.median(zf[cm])); cid += 1
        for (i_, j_) in np.argwhere(cm):
            z0 = zf[i_, j_]
            if abs(z0 - zc) > 4: continue
            c0 = col[i_, j_, z0].copy()
            if z0 > zc:
                col[i_, j_, zc:z0] = c0; kind[i_, j_, zc:z0] = 1
            elif z0 < zc:
                kind[i_, j_, z0:zc] = 0
            pid[i_, j_, zc:zc + 3] = 2960 + cid; lvl[i_, j_, zc:zc + 3] = cid % 2
# raked feather crown: points rooted on the crown/back of the head, sweeping up and back (kept clear of the eyes)
CC = np.array((0, 61.0, -31.0))
for k_, ang in enumerate((40, 62, 90, 118, 140, 25, 155)):
    a = np.radians(ang); dv = np.array((np.cos(a), np.sin(a), 0))
    zb = -31 + 5 * (k_ >= 5)
    b0 = CC + dv * 10.0 + np.array((0, 0, zb + 31))
    tip = b0 + dv * 4.5 + np.array((0, 3.0, 13.0))
    put(chain([b0, b0 + (tip - b0) * .5, tip], [3.0, 1.9, .6]) & (kind == 0), WHITE, p=3100 + k_, l=3)
for ang in range(-70, 251, 16):                                                # outline spikes flaring round the face
    if 250 < (ang % 360) < 290: continue
    a = np.radians(ang); dv = np.array((np.cos(a), np.sin(a), 0))
    rr = 13.5 if 20 < ang < 160 else 15.5
    b0 = np.array((0, 59.0, -29.0)) + dv * rr
    tip = b0 + dv * 7.0 + np.array((0, -1.5 if (ang < 20 or ang > 160) else 0, 3.0))
    put(chain([b0 - dv * 2.5, b0, tip], [2.8, 2.2, .6]) & (kind == 0), WHITE if (20 < ang < 160) else LGREY, p=3150 + (ang + 70) // 16, l=3)
for (zt, rr0, Lt, sh, col_) in ((-35.5, 12.0, 4.5, 0, WHITE), (-23.0, 16.0, 7.5, 8, LGREY)):   # spiky shingled feather tiers framing the face
    for ang in range(-74 + sh, 255, 16):
        if 240 < (ang % 360) < 300: continue
        a = np.radians(ang); dv = np.array((np.cos(a), np.sin(a), 0))
        if zt < -30 and abs(np.cos(a)) < .45 and np.sin(a) < 0: continue           # keep the beak/mouth clear
        b0 = np.array((0, 58.5, zt)) + dv * rr0
        tip = b0 + dv * Lt + np.array((0, -1.2, 2.0))
        put(chain([b0 - dv * 2.0, b0, tip], [2.4, 1.9, .55]) & (kind == 0), col_ if 10 < ang < 170 or zt < -30 else LGREY, p=3200 + (ang + 80) // 16 + (0 if zt < -30 else 30), l=3)
for z_ in (-25, -19):                                                          # second + third raked tiers down the back of the neck
    for k_, ang in enumerate((55, 90, 125)):
        a = np.radians(ang); dv = np.array((np.cos(a), np.sin(a), 0))
        b0 = np.array((0, 58.0 - (z_ + 18) * .4, z_)) + dv * 11.5
        tip = b0 + dv * 3.5 + np.array((0, 2.5, 11.0))
        put(chain([b0, tip], [2.8, .6]) & (kind == 0), WHITE if z_ < -12 else LGREY, p=3110 + k_ + (z_ + 30), l=3)

# beak: COMPACT hooked upper mandible (~1/3 face width), open red mouth below, short lower jaw
MO = (sd_ell((0, 54.0, -40.0), (4.8, 2.8, 3.6)) < 0) & (Z < -37.0)
put(MO, MOUTH, st=False)
UBm = (sd_ell((0, 60.0, -40.0), (5.4, 3.8, 5.5)) < 0) & (Y > 56.8) & (Z < -35)
UBh = chain([(0, 60, -43), (0, 59.0, -45.6), (0, 57.4, -46.4), (0, 56.2, -45.6)], [3.8, 3.2, 2.4, 1.4]) & (Y > 55.4)
UB = UBm | UBh
put(UB, BEAK, st=False)
put(UB & (Y < 57.8) & ~UBh, BEAK_D, st=False)                        # darker cutting edge
put(UBh & (Y < 56.8), BEAK_D, st=False)
put(UBm & (Y > 62.6), GOLD_L, st=False)                              # cere
JAWM = np.zeros(n, bool); REC[:] = [JAWM]
LB = chain([(0, 51.6, -38.5), (0, 50.6, -41.5), (0, 50.4, -42.6)], [4.6, 3.6, 2.4]) & (Y < 51.8)
put(LB, BEAK_D, st=False)
put(LB & (Y > 51.0), BEAK, st=False)
TG = chain([(0, 52.2, -39), (0, 52.0, -42.5)], [2.2, 1.6]) & (Y > 51.6)
put(TG, TONGUE, st=False)
REC[:] = []
GR = chain([(4.8, 57.0, -41.0), (5.2, 54.0, -41.5), (4.4, 51.4, -41.2)], [1.1, 1.1, 1.1], sym=True)   # gape rims framing the red mouth
put(GR, BEAK_D, st=False)

# face painting helper: 2D masks over (grid x, grid y) columns, design coords
XD2 = (cx / SX)[:, None] * np.ones((1, n[1])); YD2 = (cy / S + DY)[None, :] * np.ones((n[0], 1))
def front_z(i, j, only_solid=True):
    c = np.where(kind[i, j, :] == 1)[0] if only_solid else np.where(kind[i, j, :] > 0)[0]
    return c.min() if len(c) else None
def zdes(zi): return (lo[2] + .5 + zi) / S
# eyes: recessed slit, outer corner high, crisp (no halo); dark socket ring; angry brow above (never covering)
AXD = np.abs(XD2)
eye = (((YD2 >= 61) & (YD2 < 62.2) & (AXD >= 6.6) & (AXD < 10.4)) | ((YD2 >= 62.2) & (YD2 < 63.4) & (AXD >= 7.4) & (AXD < 11.6)) |
       ((YD2 >= 63.4) & (YD2 < 64.4) & (AXD >= 9.2) & (AXD < 12.4)))
core = (YD2 >= 62.2) & (YD2 < 63.4) & (AXD >= 8.4) & (AXD < 10.4)
glint = (YD2 >= 62.8) & (YD2 < 63.4) & (AXD >= 9.6) & (AXD < 10.4)
EYE = []
def dil(m):
    o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]; return o
sock = dil(eye) & ~eye
for (i, j) in np.argwhere(sock):
    zi = front_z(i, j)
    if zi is None or zdes(zi) > -36: continue
    col[i, j, zi] = DEEP; pid[i, j, zi] = 301; lvl[i, j, zi] = 0
for (i, j) in np.argwhere(eye):
    zi = front_z(i, j)
    if zi is None or zdes(zi) > -36: continue
    k = 2                                                              # EYEFIX: one flat glow colour (was cyan core + white glint)
    kind[i, j, zi] = 0                                                 # recess one brick
    col[i, j, zi + 1] = GLOW[k]; kind[i, j, zi + 1] = k
    EYE.append((i, j, zi))
# brow: grey feather plates stepping down toward the beak (angry V), one brick proud, above the slit
brow = (((YD2 >= 64.4) & (YD2 < 66.4) & (AXD >= 4.6) & (AXD < 8.8)) | ((YD2 >= 65.2) & (YD2 < 67.2) & (AXD >= 8.4) & (AXD < 12.4)) |
        ((YD2 >= 66.0) & (YD2 < 68.0) & (AXD >= 12.0) & (AXD < 14.8)))
for (i, j) in np.argwhere(brow):
    zi = front_z(i, j)
    if zi is None or zdes(zi) > -30: continue
    for zz in (zi - 2, zi - 1, zi):
        col[i, j, zz] = DGREY; kind[i, j, zz] = 1; pid[i, j, zz] = 300; lvl[i, j, zz] = 4
for (i, j) in np.argwhere(brow & ~np.roll(brow, -1, axis=1)):           # light top edge of the brow
    zi = front_z(i, j)
    if zi is not None and pid[i, j, zi] == 300: col[i, j, zi] = MGREY

# ---------------------------------------------------------------- tail: lion tail curling up to a crackling storm tuft (crisp: solid ball + bolt spikes)
TAILM = np.zeros(n, bool); REC[:] = [TAILM]
TA, tat, _ = chain_t([(0, 33, 31), (0, 29, 39), (0, 26, 47), (0, 27, 55), (0, 33, 61), (0, 41, 63)], [3.0, 2.6, 2.3, 2.1, 2.0, 1.8])
put(TA & (kind == 0), GOLD, p=50, l=0)
put(TA & (np.floor(tat * 9) % 2 == 1), GOLD_D, p=51, l=1)
TC = np.array((0, 48.5, 66.0))
put(sd_ell(TC, (7.0, 7.5, 7.0)) < 0, GLOW[2], k=2, st=False)
rng = np.random.RandomState(7)
for i in range(26):
    v = rng.normal(size=3); v[1] = abs(v[1]) * .8 + .2; v /= np.linalg.norm(v)
    L = 10.5 + 3.0 * rng.rand()
    mid = TC + v * L * .5 + np.cross(v, (0, 1, 0)) * 1.2
    pts = [TC + v * 4, mid, TC + v * L]
    if i % 3 == 0:
        put(chain(pts, [1.8, 1.2, .5]) & (kind == 0), STORM, st=False, p=52)
    else:
        put(chain(pts, [1.6, 1.0, .45]) & (kind == 0), GLOW[3], k=3, st=False)
        put(chain(pts[:2], [.75, .5]) & (kind == 3), GLOW[4], k=4, st=False)
put((sd_ell(TC, (7.1, 7.6, 7.1)) < 0) & (sd_ell(TC, (6.0, 6.5, 6.0)) > 0) & (hashv(np.floor(X / 1.5), np.floor((Y + Z) / 1.5), 9) > .55), STORM, st=False, p=52)

REC[:] = []
# ---------------------------------------------------------------- lightning on the body (side flanks + front legs): crisp white core + cyan edge
Y = Y - DY
solid1 = kind == 1
mx = np.where(solid1, AX, -1).max(axis=0)                             # outermost |x| per (y, z)
shellS = solid1 & (AX >= mx[None] - .8) & (AX > 9)
for pts in ([(-6, 38), (2, 33), (-2, 30.5), (7, 25), (3, 23), (11, 17)],):
    dl = pdist2(Z, Y, pts)
    put(shellS & (dl < 1.05) & (pid < 100), GLOW[3], k=3, st=False)
    put(shellS & (dl < .4) & (pid < 100), GLOW[4], k=4, st=False)
mz = np.where(kind == 1, Z, 1e9).min(axis=2)                          # front-most z per (x, y)
shellF = (kind == 1) & (Z <= mz[..., None] + .8)
dl = pdist2(AX, Y, [(11, 22), (14.5, 17.5), (11.5, 15), (15, 9)])
put(shellF & (dl < 1.05) & (pid >= 20) & (pid < 30), GLOW[3], k=3, st=False)
put(shellF & (dl < .4) & (pid >= 20) & (pid < 30), GLOW[4], k=4, st=False)

# ---------------------------------------------------------------- wings (GRID space): high V arm + 4 rows of big dark feather blocks, light 1-brick top edge per block
X, Y, Z = GX, GY, GZ; AX = np.abs(X)
def obb(c, A, B, Cn, ha, hb, hc, taper=0.0):
    r = np.sqrt(ha * ha + hb * hb + hc * hc) + 1
    i0_ = [max(0, int(np.floor(c[k] - r - lo[k]))) for k in range(3)]; i1_ = [min(n[k], int(np.ceil(c[k] + r - lo[k])) + 1) for k in range(3)]
    sl = tuple(slice(i0_[k], i1_[k]) for k in range(3))
    px, py, pz = X[sl] - c[0], Y[sl] - c[1], Z[sl] - c[2]
    a = px * A[0] + py * A[1] + pz * A[2]; b = px * B[0] + py * B[1] + pz * B[2]; cc = px * Cn[0] + py * Cn[1] + pz * Cn[2]
    hbx = hb * (1 - taper * np.clip((a - (ha - hb * 1.6)) / (hb * 1.6), 0, 1))
    m = np.zeros(n, bool); A_ = np.zeros(n, np.float32)
    m[sl] = (np.abs(a) <= ha) & (np.abs(b) <= hbx) & (np.abs(cc) <= hc)
    A_[sl] = a
    return m, A_
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
WROWS = (  # (start along the feather, length, half width, half thickness, front offset) - inner rows sit BEHIND, outer rows step forward
    (-2.0, 14.0, 4.8, 2.2, 0.0),       # lesser coverts (by the arm)
    (10.5, 15.0, 4.9, 2.2, -3.6),       # greater coverts
    (23.0, 16.0, 5.0, 2.2, -7.2),      # secondaries
    (36.0, 24.0, 5.2, 2.2, -10.8),      # primaries (outer edge, longest)
)
WTONE = (DGREY, STORM)
WBOLT = []
for sx in (1, -1):
    ARMP = np.array([(20, 86, -12), (29, 108, -12), (41, 129, -13), (55, 146, -15), (69, 157, -17), (79, 162, -18), (86, 161, -19)], float)
    ARMP[:, 0] *= sx
    seg = np.linalg.norm(np.diff(ARMP, axis=0), axis=1); acc = np.concatenate([[0], np.cumsum(seg)]); TOT = acc[-1]
    def arm(f):
        t = f * TOT; i = min(np.searchsorted(acc, t, 'right') - 1, len(seg) - 1); w = (t - acc[i]) / seg[i]
        return ARMP[i] + (ARMP[i + 1] - ARMP[i]) * w, unit(ARMP[i + 1] - ARMP[i])
    def fdir(f):                                      # feathers hang down-back at the shoulder, fan out sideways past the wrist
        th = np.radians(2 + 34 * f ** 1.2)
        return unit((sx * np.sin(th), -np.cos(th), .55 + .2 * f))
    for ri, (s0, L, hw, ht, off) in enumerate(WROWS):
        step = 2 * hw * .86
        nb = int(TOT / step) + 1
        for j in range(nb):
            f = (j + .5 * (ri % 2)) * step / TOT
            if f > 1.0: continue
            P0, T0 = arm(f); D = fdir(f)
            Lr = L * (.75 + .4 * f)
            Nn = unit(np.cross(D, T0)); Nn = Nn if Nn[2] < 0 else -Nn       # thickness axis, pointing to the front (-z)
            Bw = unit(np.cross(Nn, D))
            jit = 1.2 * np.sin(j * 2.3 + ri)
            Lj = Lr + jit
            c = P0 + D * (s0 * (.75 + .4 * f) + Lj / 2) + Nn * (off - .7 * (j % 2))
            m, A_ = obb(c, D, Bw, Nn, Lj / 2, hw, ht, taper=.5 if ri == 3 else .2)
            m &= ((X * sx) > 4) & ((kind == 0) | ((pid >= 590) & (pid < 1100)))   # never over body / head
            pidb = 600 + ri * 200 + j + (100 if sx < 0 else 0)
            lvb = ri + .3 * (j % 2)
            put(m, WTONE[(j + ri) % 2], p=pidb, l=lvb)
            put(m & (A_ < -Lj / 2 + 1.25), LGREY, p=pidb, l=lvb)              # light grey 1-brick top edge of each block
    ARMM = chain([tuple(q) for q in ARMP], [5.5, 5.2, 4.8, 4.2, 3.6, 3.0, 2.4])
    put(ARMM & ((X * sx) > 4) & ((kind == 0) | ((pid >= 590) & (pid < 1100))), DGREY, p=590, l=0)
    up = ARMM & ~np.roll(ARMM, -1, axis=1)
    put(up & ((X * sx) > 4) & (pid == 590), LGREY, p=590, l=0)
    # zigzag bolts in (f, depth) wing coords -> projected to (x, y)
    for pts in (((.30, 4), (.37, 10), (.31, 14), (.39, 22), (.33, 26), (.41, 34)),
                ((.68, 6), (.76, 14), (.69, 19), (.79, 30), (.72, 35), (.82, 48))):
        WBOLT.append([tuple((arm(f)[0] + fdir(f) * d_)[:2]) for f, d_ in pts])
WINGP = (pid >= 590) & (pid < 1100) & (kind >= 1)
U2 = cx[:, None] * np.ones((1, n[1])); V2 = cy[None, :] * np.ones((n[0], 1))
for pts in WBOLT:                                                         # paint on the front-most and back-most wing brick of each column
    dl = pdist2(U2, V2, pts)
    for (i, j) in np.argwhere(dl < 1.75):
        zs = np.where(WINGP[i, j, :])[0]
        if not len(zs): continue
        kk = 4 if dl[i, j] < .75 else 3
        for zi in (zs.min(), zs.max()):
            if kind[i, j, zi] == 4: continue
            kind[i, j, zi] = kk; col[i, j, zi] = GLOW[kk]

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
X, Y, Z = GX / SX, GY / S, GZ / S
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
dark &= ~(((pid >= 2000) & (pid < 3100)) | (pid == 40) | (pid == 300) | (pid == 301))
col[dark & (kind == 1)] *= .72
col[dark & (kind == 1) & (pid >= 2960) & (pid < 3200)] *= 1.12          # head plates: seams only to light grey
SHF = np.clip(.7 + .45 * (Y / 70.0), .7, 1.15).astype(np.float32)
SHF[(pid >= 590) & (pid < 1100)] = 1.0
SHF[((pid >= 2000) & (pid < 3400)) | (pid == 40)] = 1.0           # feather coat keeps its white / light-grey mix
GB = (pid >= 1) & (pid < 100)
SHF[GB] = np.clip(.9 + .3 * (Y[GB] / 70.0), .9, 1.15)
col *= SHF[..., None]                                                              # lit tops, dark underside (wings exempt)
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('f6f8fb', 'c4c9d2', '8d94a3', '4a4d5c', '34363f', '262a34', '15161b',
                                 'f5c85a', 'd99a2b', 'a8691c', '70460f',
                                 'ffd23f', 'e39a1c', '6e1a22', 'c4434e')])
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

nbc = sum(np.roll(kind > 0, s, axis=ax) for ax in range(3) for s in (1, -1))   # drop lone bricks (no face neighbour)
print('VOX_OK lone bricks removed', int(((kind > 0) & (nbc == 0)).sum())); kind[(kind > 0) & (nbc == 0)] = 0; solid = kind > 0
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
body = build('Griffin', kind == 1, True)
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
np.savez_compressed(os.path.join(OUT, 'occ.npz'), kind=kind)                    # for the connected-component audit
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for sx in (1, -1):                                                         # eye lights: the glow spills onto brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 120; L.data.color = (.118, .549, 1.0); L.data.shadow_soft_size = 1.0
        L.location = B(14.0 * sx, 90.0, -76.0)
    L = bpy.data.objects.new('TuftLight', bpy.data.lights.new('TuftLight', 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 700; L.data.color = (.35, .7, 1.0); L.location = B(0, 70, 118)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 2.2, (62, 0, -80), 40), ('FillR', 2.4, (62, 0, 80), 40), ('Back', 1.6, (60, 0, 170), 40)):
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
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.26, .4, .2, 1)
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
    cen = (0, 84, 6); D = 540
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 88, 18), 700, az, el, ortho=250)
    for nm, a in (('rest_34', (cen, D, -35, 12)), ('rest_side', (cen, D, 90, 6)), ('rest_front', (cen, D, 0, 6)), ('rest_back', (cen, D, 150, 14)),
                  ('face', ((0, 86, -64), 120, 0, 4)), ('headside', ((0, 84, -58), 140, 90, 4)), ('head34', ((0, 86, -60), 140, -38, 10)),
                  ('footfront', ((-22, 10, -36), 90, 0, 6)), ('footside', ((-22, 10, -32), 100, -90, 4)), ('feet', ((0, 20, 14), 280, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): bones in brick coords, L = +x
def bb(x, y, z): return (x * SX, (y - DY) * S, z * S)                    # body space -> bricks
def lg(x, y, z): return (x * SX, y * S, z * S)                           # leg (design) space -> bricks
Xd, Yd, Zd = GX / SX, GY / S, GZ / S; AXd = np.abs(Xd); Yb = Yd + DY      # design / body coords
sol_ = kind > 0; WING = (pid >= 590) & (pid < 1100) & sol_
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', bb(0, 32, 22), bb(0, 33, 6)), ('spine', 'hips', bb(0, 33, 6), bb(0, 40, -12)),
       ('neck', 'spine', bb(0, 44, -20), bb(0, 54, -27)), ('head', 'neck', bb(0, 54, -27), bb(0, 59, -46)), ('jaw', 'head', bb(0, 53.5, -36), bb(0, 50.5, -43))]
TP = [bb(0, 33, 31), bb(0, 26, 47), bb(0, 27, 55), bb(0, 41, 63), bb(0, 55, 67)]
TB = [('tail_%d' % (i + 1), 'hips' if i == 0 else 'tail_%d' % i, TP[i], TP[i + 1]) for i in range(3)] + [('tail_tuft', 'tail_3', TP[3], TP[4])]
RIG += TB
OVR = brick_rig.limb(GX, GY, GZ, TAILM & sol_, TB) + [(TAILM & ((Xd ** 2 + (Yb - 48.5) ** 2 + (Zd - 66) ** 2) < 15 ** 2), 'tail_tuft')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    for fb, par, P_, m_ in (('F', 'spine', [lg(14 * sx, 26, -11), lg(14 * sx, 13, -15), lg(14 * sx, 6, -14), lg(14 * sx, 2, -33)],
                             (Xd * sx > 4) & (Yd < 23) & (Zd < -2) & (Zd > -40)),
                            ('B', 'hips', [lg(14 * sx, 30, 22), lg(14.5 * sx, 11, 33), lg(14.5 * sx, 5, 31), lg(14.5 * sx, 1, 15)],
                             (Xd * sx > 4) & (Yd < 24) & (Zd > 8))):
        ch = [('leg%s%s_%s' % (fb, sd, nm), par if j == 0 else 'leg%s%s_%s' % (fb, sd, ('up', 'low')[j - 1]), P_[j], P_[j + 1]) for j, nm in enumerate(('up', 'low', 'foot'))]
        RIG += ch; OVR += brick_rig.limb(GX, GY, GZ, m_ & sol_ & ~WING & ~TAILM, ch)
    AP = np.array([(20, 86, -12), (29, 108, -12), (41, 129, -13), (55, 146, -15), (69, 157, -17), (79, 162, -18), (86, 161, -19)], float); AP[:, 0] *= sx
    AP = [tuple(float(v) for v in q) for q in AP]
    WB = [('wing%s_arm' % sd, 'spine', AP[0], AP[2]), ('wing%s_fore' % sd, 'wing%s_arm' % sd, AP[2], AP[4]), ('wing%s_hand' % sd, 'wing%s_fore' % sd, AP[4], AP[6])]
    RIG += WB; OVR += brick_rig.limb(GX, GY, GZ, WING & (GX * sx > 0), WB)
OVR += [((Yb > 49) & (Zd < -17) & sol_ & ~WING, 'head'), ((Yb > 60) & (Zd < -5) & (AXd < 20) & sol_ & ~WING, 'head'), (JAWM, 'jaw')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (20, 0, 0), 'jaw': (25, 0, 0), 'wingL_arm': (0, 0, 30), 'wingL_hand': (0, 0, 25), 'wingR_fore': (0, 0, -20),
                       'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail_2': (0, 0, 25)},
                 render='render' in argv)
print('BL_OK')
