# SLAB REBUILD of ember_dragon_brick.py (not yet owner-approved): armour as faceted slabs with dark walls and wide lava channels.
# Ember Dragon boss (stud-voxel brick pipeline, based on examples/brick/war_rhino_brick.py)
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference: concept_sheet.jpg (charcoal armour + lava cracks, molten belly, red ember wings, brown horns, spade tail).
# Run: powershell -File <skill>\scripts\run_brick.ps1 ember_dragon.py
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'EmberDragonSlab'
STUD_PNG = os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png')

GS = 1.5                      # LARGE SCALE: designed in the old units, voxelised 1.5x bigger
lo = np.array((-172.0, -0.5, -188.0)); hi = np.array((172.0, 196.5, 216.0))   # grid units (bricks)
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid((cx / GS).astype(np.float32), (cy / GS).astype(np.float32), (cz / GS).astype(np.float32), indexing='ij'); AX = np.abs(X)   # design coords
col = np.zeros((*n, 3), np.float32); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n, np.float32); keep = np.zeros(n, bool)          # keep = skip top-lit shading (belly, wings)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
CHAR = hx('2a2a31'); PLATE = hx('3a3a42'); STONE = hx('55555e'); DEEP = hx('1c1c22'); BLACK = hx('0c0c10')
RED = hx('b0221a'); REDD = hx('6e1410'); REDO = hx('dc4a1c')
BELLY = hx('ffbe2a'); BELLYO = hx('ff8a10'); BELLYS = hx('c85a0a')
LAVA = hx('ff9a1c'); HORN = hx('7a5e4c'); HORND = hx('5a463a'); IVORY = hx('f0e0c0'); IVORYS = hx('c8b090')
GLOW = {2: hx('ff5a0a'), 3: hx('ffa21a'), 4: hx('fff0c0')}   # lava orange / hot yellow-orange / white-hot glint
# COLOUR VARIANTS: SV_VARIANT=frost|venom|void turns the hue of every warm colour (wings, belly, lava, glow, lights) and leaves
# the charcoal, horns and claws alone. Value and saturation are kept, so the hierarchy is the same in every variant.
import colorsys
VARIANT = os.environ.get('SV_VARIANT', 'ember'); HUE = dict(ember=0.0, frost=.52, venom=.27, void=.78)[VARIANT]
def vr(c):
    h, l, s_ = colorsys.rgb_to_hls(*[float(v) for v in c]); return np.array(colorsys.hls_to_rgb((h + HUE) % 1.0, l, s_))
if HUE:
    GLOW = {k: vr(v) for k, v in GLOW.items()}; ID = ID + '_' + VARIANT
    RED, REDD, REDO, BELLY, BELLYO, BELLYS, LAVA = (vr(c) for c in (RED, REDD, REDO, BELLY, BELLYO, BELLYS, LAVA))

REC = []                                                                         # rig: masks recording which puts belong to a part
def unrec(m): REC[:] = [r_ for r_ in REC if r_ is not m]
def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l
    for r_ in REC: r_ |= m

def sd_ell(c, r):
    px, py, pz = (AX - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def sd_cap(a, b, ra, rb, XX=None):
    XX = AX if XX is None else XX
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((XX - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((XX - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d - (ra + (rb - ra) * t)
def sd_chain(pts, radii, XX=None):
    d = np.full(n, 1e9)
    for i in range(len(pts) - 1): d = np.minimum(d, sd_cap(pts[i], pts[i + 1], radii[i], radii[i + 1], XX))
    return d
def chain(pts, radii, XX=None): return sd_chain(pts, radii, XX) <= 0

rng = np.random.RandomState(7)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ---------------------------------------------------------------- body: deep chest, barrel, hips, S-neck, long tail, 4 legs
BS = 1.2; _U = (X, Y, Z, AX); X = X / BS; Y = Y / BS; Z = Z / BS; AX = np.abs(X)   # body, neck, head, legs, tail built 1.2x (wings are not)
LIFT = 6.0                                                           # body raised: more leg under the belly
_Y0 = Y; Y = _Y0 - LIFT
d = sd_ell((0, 23, -17), (20.0, 15.5, 16.0))                         # deep chest
d = smin(d, sd_ell((0, 25, 2), (18.0, 12.5, 22.0)), 5)              # barrel
d = smin(d, sd_ell((0, 26, 21), (17.0, 12.5, 13.0)), 5)             # hips
NECK = [(0, 28, -23), (0, 40, -28), (0, 51, -33), (0, 58, -40), (0, 59, -49), (0, 54, -57), (0, 49, -63)]   # S-neck: up, crest, then down into the head (pre-LIFT)
d = smin(d, sd_chain(NECK, [12, 10.5, 9.5, 9, 8.5, 8.2, 8]), 5)
TZ = [25, 39, 54, 68, 82, 95]; TX = [0, 0, 0, 0, 0, 0]                                     # tail straight back ...
TAIL = [(x_, y_, z_) for x_, y_, z_ in zip(TX, [27, 25, 21, 16, 12, 9], TZ)]               # ... and curves down toward the tip
d = smin(d, sd_chain(TAIL, [10.5, 8.6, 6.8, 5.3, 3.9, 3.0], X), 4)
def xo(z): return float(np.interp(z, TZ, TX))
Y = _Y0
legs = sd_ell((18.5, 28, -18), (11.0, 14.5, 12.4))                   # shoulders / thighs (lifted)
legs = np.minimum(legs, sd_ell((18.5, 29, 20), (11.7, 15.5, 13.8)))
legs = np.minimum(legs, sd_chain([(19, 28, -18), (24, 16, -20), (27, 5.0, -24)], [11.0, 8.8, 7.8]))        # front: long, nearly straight
legs = np.minimum(legs, sd_chain([(19, 29, 20), (25, 18, 16), (27, 8.5, 22), (27, 4.5, 20)], [12.4, 9.2, 7.4, 7.1]))  # rear
d = smin(d, legs, 3)
BODY = d < 0

# ARMOUR AS FACETED SLABS (research ch. 91, 92; same style as war_rhino_plated_brick.py). The hide is cut into voronoi
# cells; each cell is ONE flat slab: a plane fitted to the body surface under it, tilt snapped to a brick-friendly slope,
# lifted by the cell's level (1-3). The outer layer of a slab is its lit face (faces that look up are lighter); everything
# under it is a dark side wall. The joins between slabs are recessed channels, 2 bricks wide: black, or solid lava.
NSEED = 300; RISE = .85; SNAP = np.array([0, .5, 1.0])               # fewer, bigger blocks; rise per level in design units (~1.5 bricks)
shell = (d < 3.8) & (d > -3.5) & (Y > 2.5)
seeds = np.stack([rng.uniform(-38, 38, 800), rng.uniform(2, 70, 800), rng.uniform(-72, 100, 800)], 1)[:NSEED]
idx = np.argwhere(shell); P = np.stack([cx[idx[:, 0]], cy[idx[:, 1]], cz[idx[:, 2]]], 1) / GS / BS
near = np.zeros(len(P), np.int32)
for s in range(0, len(P), 20000):
    q = P[s:s + 20000]; near[s:s + 20000] = np.argmin(((q[:, None, :] - seeds[None]) ** 2).sum(-1), 1)
cell = np.full(n, -1, np.int32); cell[tuple(idx.T)] = near
raise_ = (rng.rand(800) < .45)
level = 1 + (rng.rand(800) * 3).astype(int)                           # 1..3
SH = [CHAR, PLATE, PLATE, CHAR * 1.1, STONE * .85]
shade = rng.randint(0, len(SH), 800)
put(BODY, DEEP, st=False)
dv = d[tuple(idx.T)]; Pa = P.copy(); Pa[:, 0] = np.abs(Pa[:, 0])
on = np.zeros(len(P), bool); tone = np.ones(len(P), np.float32)
order = np.argsort(near, kind='stable'); cuts = np.searchsorted(near[order], np.arange(NSEED + 1))
for c in range(NSEED):
    ii = order[cuts[c]:cuts[c + 1]]
    if not len(ii): continue
    thin = seeds[c, 2] < -20 or seeds[c, 2] > 30                         # neck and tail: low, shallow slabs keep their line
    if thin: level[c] = min(level[c], 2)
    rise = (RISE * .6 if thin else RISE) * level[c] - .4
    sf = ii[np.abs(dv[ii]) < .6]
    if len(sf) < 12: on[ii] = dv[ii] < rise; continue
    c0 = Pa[sf].mean(0); nrm = np.linalg.svd(Pa[sf] - c0, full_matrices=False)[2][2]
    if nrm[1] * (c0[1] - 26) + nrm[0] * c0[0] < 0: nrm = -nrm          # point away from the body's axis
    q = nrm / np.abs(nrm).max(); q = np.sign(q) * SNAP[np.argmin(np.abs(np.abs(q)[:, None] - SNAP[None]), 1)]
    nrm = q / np.linalg.norm(q)
    h = Pa[ii].dot(nrm); top = np.median(Pa[sf].dot(nrm)) + rise
    k_ = ((h <= top) & (dv[ii] < rise + .6)) | (dv[ii] < .25)
    on[ii] = k_
    t_ = np.full(len(ii), .95 + .50 * max(nrm[1], 0) + .06 * level[c], np.float32)
    t_[(h <= top - .6) & (dv[ii] < rise - .1)] *= .6                   # side wall
    tone[ii] = t_
skin = np.zeros(n, bool); skin[tuple(idx[on].T)] = True
tn = np.ones(n, np.float32); tn[tuple(idx.T)] = tone
cs = np.minimum(np.array(SH)[shade[cell[skin]]] * tn[skin][:, None], STONE[None] * 1.04)   # stay in the charcoal greys
col[skin] = cs; kind[skin] = 1; stud[skin] = True; pid[skin] = 1000 + cell[skin]; lvl[skin] = level[cell[skin]]
# channels between slabs: both sides of every join, sunk to the hide
bord = np.zeros(n, bool)
for ax in range(3):
    for s_ in (1, -1):
        nc = np.roll(cell, s_, axis=ax)
        bord |= shell & (nc >= 0) & (nc != cell)
chan = bord & (d < .3) & (d > -3.5)
kind[bord & (d >= .3) & (pid >= 1000)] = 0                            # cut the channel open above the hide
hsh = (cell.astype(np.int64) * 2654435761 % 97)
nb_h = np.zeros(n, np.int64)
for ax in range(3):
    for s_ in (1, -1): nb_h = np.maximum(nb_h, np.where(np.roll(cell, s_, axis=ax) >= 0, np.roll(hsh, s_, axis=ax), 0))
lava = chan & (np.minimum(hsh, nb_h) < 48)                            # a join is lava when either of its two cells says so
put(chan & ~lava, BLACK, st=False)
put(lava, LAVA, st=False); keep[lava] = True

# molten belly: segmented plates under the neck, down the chest front, along the underside
yb = np.interp(Z, [-65, -57, -49, -40, -33, -28, -22, -15, 12, 19, 25], [52, 57, 63, 63, 57, 46, 36, 28, 25, 24, 0])
bel = (kind > 0) & (d > -3.5) & (AX < 12.5 - np.clip((Z - 6) * .25, 0, 5)) & (Y < yb) & (Y > 3) & (Z < 23)
segi = np.where(Z < -12, np.floor(Y / 4.0), 100 + np.floor(Z / 5.0)).astype(int)
put(bel, BELLY, st=True, p=3, l=2); keep[bel] = True; BELLYM = bel.copy()
segb = bel & np.where(Z < -12, np.roll(segi, 1, 1) != segi, np.roll(segi, 1, 2) != segi)
put(segb, BELLYS, st=False, p=3, l=2)
put(bel & (AX > 11 - np.clip((Z - 6) * .25, 0, 5)), BELLYO, st=False, p=3, l=2)   # dark orange rim

# ---------------------------------------------------------------- head: cranium + blocky snout + open jaw, lowered and forward
def prof(rows, power=6):
    R = np.array(rows, float)
    hb = np.interp(Z, R[:, 0], R[:, 1]); ht = np.interp(Z, R[:, 0], R[:, 2]); hw = np.interp(Z, R[:, 0], R[:, 3])
    hm = (hb + ht) / 2; hh = (ht - hb) / 2
    return ((AX / hw) ** power + (np.abs(Y - hm) / hh) ** power < 1) & (Z > R[0, 0]) & (Z < R[-1, 0])
_SAVE = (X, Y, Z, AX); PV = np.array((0, 40, -48.)); HS = 1.38; HOY = 13.0; HOZ = -15.0   # head 1.2x, moved up/forward onto the long neck (above the shoulders)
X = PV[0] + (X - PV[0]) / HS; Y = PV[1] + (Y - PV[1] - HOY) / HS; Z = PV[2] + (Z - PV[2] - HOZ) / HS; AX = np.abs(X)
HID = newid(); HEADM = np.zeros(n, bool); REC.append(HEADM)
def profT(rows, k=.6):                                                          # trapezoid section: narrower toward the bottom
    R_ = np.array(rows, float)
    hb = np.interp(Z, R_[:, 0], R_[:, 1]); ht = np.interp(Z, R_[:, 0], R_[:, 2]); hw = np.interp(Z, R_[:, 0], R_[:, 3])
    w = hw * (k + (1 - k) * np.clip((Y - hb) / (ht - hb), 0, 1))
    return (AX < w) & (Y > hb) & (Y < ht) & (Z > R_[0, 0]) & (Z < R_[-1, 0])
SN = [(-78, 38.5, 43.2, 4.0), (-75, 38, 44.5, 5.2), (-68, 38, 45.5, 6.0), (-61, 38, 46.5, 7.0)]
snout = prof(SN, power=4)
cran = prof([(-62, 37, 49.5, 9.5), (-56, 36, 51.0, 10.0), (-50, 36, 50.5, 9.5), (-46, 37, 48.5, 8.5)])
JW = [(-76, 29.5, 33.0, 3.2), (-70, 29.0, 33.5, 4.4), (-60, 29.5, 35.0, 6.0), (-50, 31.5, 37.5, 7.5), (-46, 34, 39, 8.0)]
jaw = profT(JW)
put(snout | cran, STONE * .82, p=HID, l=3)                                       # head a value lighter than the neck behind it
put(cran & (Y > 47.5), STONE, p=newid(), l=4)                                     # skull cap plate
put(jaw, CHAR, p=newid(), l=2)
put(jaw & (Y < 30.6), DEEP, st=False)                                             # chin underside
head_ = snout | cran | jaw
gape = (Y > 32.0) & (Y < 38.4) & (Z > -76) & (Z < -46) & ~head_
hw_sn = np.interp(Z, [r[0] for r in SN], [r[3] for r in SN])
mouth = gape & (AX < 2.2 + (Y - 32.0) * .5)                                       # V-shaped opening (narrow at the chin)
put(gape & ~mouth & (AX < hw_sn) & (Z > -73.5) & (Z < -64), CHAR, p=newid(), l=2)  # lips frame the mouth (front fangs stand in front of them)
put(mouth, REDD, st=False)                                                        # dark-red mouth interior
put(mouth & (Z > -62) & (AX < 3.4), GLOW[3], k=3, st=False)                       # inner throat glow only
put(box(-1, 6.2, 29.5, 33.5, -72, -58) & jaw & (Y > 31.6), REDD, st=False)        # tongue floor
UPF = np.zeros(n, bool); REC.append(UPF)
for zt in (-74.5, -71, -67.5, -64, -60.5, -57):                                   # upper fangs hang from the lip edge
    xe = float(np.interp(zt, [r[0] for r in SN], [r[3] for r in SN])) - .8
    put(chain([(xe, 38.6, zt), (xe - .2, 33.8 if zt < -73 else 34.8, zt - .3)], [.66, .18]), IVORY, st=False)
unrec(UPF); LOWF = np.zeros(n, bool); REC.append(LOWF)
for zt in (-72.5, -69, -65.5, -62):                                               # lower fangs rise from the jaw edge
    xe = float(np.interp(zt, [r[0] for r in JW], [r[3] for r in JW])) - .7
    put(chain([(xe, 32.4, zt), (xe - .2, 36.0, zt + .3)], [.6, .18]), IVORYS, st=False)
unrec(LOWF); REC.append(UPF)
put(chain([(3.7, 38.6, -75.6), (3.4, 33.6, -75.9)], [.7, .18]), IVORY, st=False)   # big front fangs on the V edges
unrec(UPF); REC.append(LOWF)
put(chain([(2.6, 31.8, -74.6), (2.8, 35.6, -74.3)], [.6, .18]), IVORYS, st=False)
unrec(LOWF)
put(box(1.0, 3.0, 43.4, 45.6, -78.6, -75.4), BLACK, st=False)                     # nostril notches ...
kind[box(1.0, 3.0, 44.4, 45.6, -78.6, -76.4)] = 0                                # ... cut into the snout's top front edge
put(box(0, 2.6, 44.6, 46.6, -68, -62), PLATE * 1.25, p=newid(), l=5)              # snout ridge plate
# eyes on the cranium front face, slanted (outer corner high), dark socket, heavy angry brow
put(box(5.5, 10.8, 43.5, 47.5, -63.2, -59), BLACK, st=False)
for (xa, xb, y) in ((5.5, 8.5, 44), (6.5, 9.5, 45), (8.0, 10.5, 46), (9.5, 10.5, 47)):
    put(box(xa, xb, y - .5, y + .5, -63.5, -60.5), GLOW[2], k=2, st=False)
put(box(6.5, 9.0, 43.5, 45.5, -63.5, -61.5), GLOW[2], k=2, st=False)   # EYEFIX: one flat glow colour (was hot core + glint)
BR = newid()
put(box(7.0, 11.0, 47.5, 50.5, -65, -55), STONE, p=BR, l=6)                     # brow ridge, outer high
put(box(3.0, 7.0, 46.5, 49.5, -65, -57), STONE * .95, p=BR, l=6)                # inner brow steps DOWN = angry V
put(box(3.0, 11.0, 46.5, 47.5, -65.2, -64), DEEP, st=False)                      # brow underside shadow
put(box(0, 1.0, 47.5, 49.5, -62, -60), GLOW[2], k=2, st=False)                   # forehead lava crack
put(chain([(0, 50, -58), (0, 54, -56), (0, 57, -53)], [2.2, 1.4, .5]), DEEP, st=False, p=newid(), l=6)   # crest spike
for (a, b) in (((9.5, 46, -56), (20, 49, -52)), ((9.8, 41.5, -55), (21, 41, -51)), ((9.2, 37.5, -53), (18, 33, -49))):   # cheek spikes fan out sideways
    put(chain([a, b], [2.8, .5]), CHAR, st=False, p=newid(), l=5)
# horns: brown-grey, swept up and back, tips curving in; banded segments
HORNP = [(6.5, 49, -52), (12, 55, -48), (14.5, 61, -41), (13.5, 67, -33), (9, 71, -26)]
hm_ = chain(HORNP, [4.6, 4.1, 3.3, 2.2, .7])
put(hm_, HORN, st=False, p=newid(), l=7)
put(hm_ & (np.floor((Y + .5 * Z) / 3.0) % 2 == 0), HORND, st=False, p=newid(), l=7)

unrec(HEADM)
X, Y, Z, AX = _SAVE

# ---------------------------------------------------------------- feet: 3 thick toes + pale cream claws
for (fx, fz) in ((27.5, -26), (27.5, 19)):
    put(box(fx - 7.6, fx + 7.6, -1, 6.0, fz - 4, fz + 7), PLATE, p=newid(), l=1)
    for k_ in range(4):
        a = fx - 7.6 + 3.9 * k_
        put(box(a, a + 3.3, -1, 6.0, fz - 9, fz - 3), PLATE * 1.1, p=newid(), l=1)
        put(box(a, a + 3.3, -1, 3.4, fz - 13.0, fz - 8.3), IVORY, st=False)                 # big ivory claw
        put(box(a + .5, a + 2.8, 3.3, 4.8, fz - 12.0, fz - 8.3), IVORY, st=False)
        put(box(a + .5, a + 2.8, -1, 2.4, fz - 14.6, fz - 12.8), IVORYS, st=False)          # claw tip
    for k_ in range(3):
        g_ = fx - 7.6 + 3.9 * k_ + 3.3
        put(box(g_, g_ + .6, -1, 6.0, fz - 9, fz - 3), BLACK, st=False)                      # black gap between toes

# ---------------------------------------------------------------- wings: arm + 4 fingers, scalloped red membranes, ember edges
WINGM = np.zeros(n, bool); REC.append(WINGM)
_S = (X, Y, Z, AX); X, Y, Z, AX = _U                                             # wings: unscaled coords
S0 = (15, 42, -8); S_ = tuple(np.array(S0) * BS)
def _w(p_, k=1.2): return tuple(np.array(S_) + (np.array(p_) - np.array(S0)) * k)
E_ = _w((20, 64, -16)); W_ = _w((30, 83, -12)); M_ = _w((56, 100, 20))          # M_ = top of the arched leading edge
F = [_w((84, 92, 60)), _w((92, 40, 44)), _w((70, 24, 52)), _w((48, 24, 42)), tuple(np.array((15, 40, 21)) * BS)]   # F0 top/back tip ... F4 = body (hip) attach
def tri(A, Bv, Cv, scal, edge=True, lines=True):
    A = np.array(A, float); Bv = np.array(Bv, float); Cv = np.array(Cv, float)
    e1 = Bv - A; e2 = Cv - A; nr = np.cross(e1, e2); nr /= np.linalg.norm(nr)
    G = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]]); Gi = np.linalg.inv(G)
    mn = np.minimum(np.minimum(A, Bv), Cv) - 2; mx = np.maximum(np.maximum(A, Bv), Cv) + 2
    sel = (AX > mn[0]) & (AX < mx[0]) & (Y > mn[1]) & (Y < mx[1]) & (Z > mn[2]) & (Z < mx[2])
    I = np.argwhere(sel); Pp = np.stack([np.abs(cx[I[:, 0]]), cy[I[:, 1]], cz[I[:, 2]]], 1) / GS - A
    dist = Pp @ nr; b = np.stack([Pp @ e1, Pp @ e2], 1) @ Gi.T; u, v = b[:, 0], b[:, 1]; tt = u + v
    a = np.where(tt > 1e-6, v / np.maximum(tt, 1e-6), 0)
    lim = 1 - scal * np.sin(np.pi * a) ** 2                                   # blunt finger tips, deep middle
    ok = (np.abs(dist) < .8) & (u >= -.02) & (v >= -.02) & (tt <= lim)
    hgt = np.linalg.norm(np.cross(e1, e2)) / np.linalg.norm(Cv - Bv)            # wrist -> trailing edge distance
    gap = (lim - tt) * hgt
    I = I[ok]; gap = gap[ok]; tt = tt[ok]; a = a[ok]
    m = np.zeros(n, bool); m[tuple(I.T)] = True
    free = m & (kind == 0)
    put(free, RED, st=True, p=50, l=0); keep[free] = True
    g = np.zeros(n); g[tuple(I.T)] = gap; ta = np.zeros(n); ta[tuple(I.T)] = tt; aa = np.zeros(n); aa[tuple(I.T)] = a
    cellc = (np.floor(ta * 4) + 2 * np.floor(aa * 3)) % 3 == 0                     # every 3rd panel darker
    put(free & cellc, REDD, st=True, p=50, l=0)                                    # 2-tone panels
    if lines: put(free & ((np.abs(aa * 3 - np.round(aa * 3)) * np.maximum(ta, .2) * hgt < .55) | (np.abs(ta * 6 - np.round(ta * 6)) * hgt / 6 < .5)) & (g > 12.0), DEEP, st=False, p=50)   # panel lines
    if edge:
        put(free & (g < 12.0), REDO, st=True, p=50)
        put(free & (g < 7.0), BELLYO, st=True, p=50)                               # crisp ember edge: solid bricks, no halo
        put(free & (g < 3.5), BELLY, st=True, p=50)
_C = 2 * np.array(M_) - (np.array(W_) + np.array(F[0])) / 2                       # quadratic arch W -> M -> F0
ARCH = [tuple((1 - t) ** 2 * np.array(W_) + 2 * t * (1 - t) * _C + t * t * np.array(F[0])) for t in np.linspace(0, 1, 11)]
for k_ in range(1, 10): tri(W_, ARCH[k_], ARCH[k_ + 1], 0, edge=False, lines=False)
for A_, B_, C_, sc in ((W_, F[0], F[1], .17), (W_, F[1], F[2], .19), (W_, F[2], F[3], .19), (W_, F[3], F[4], .15)):
    tri(A_, B_, C_, sc)
tri(S_, W_, F[4], 0, edge=False)
tri(S_, E_, W_, 0, edge=False)
# bones: thick arm, fingers tapering, chunky studded blocks on the leading edge, wrist claw
put(chain([S_, E_, W_], [4.0, 3.5, 3.2]), CHAR, p=newid(), l=3)
put(chain(ARCH, list(np.linspace(3.4, 1.4, len(ARCH)))), CHAR, p=newid(), l=3)
for k_, f in enumerate(F[1:4]):
    put(chain([W_, f], [3.0, 1.4]), DEEP, p=newid(), l=3)
    for s in (.3, .6): put(sd_ell(tuple(np.array(W_) + (np.array(f) - np.array(W_)) * s), (3.1, 3.1, 3.1)) < 0, DEEP, p=newid(), l=3)
for pnt in (E_, tuple((np.array(E_) + np.array(W_)) / 2)):                          # heavy blocks on the arm
    put((np.abs(AX - pnt[0]) < 2.6) & (np.abs(Y - pnt[1] - 3.2) < 2.6) & (np.abs(Z - pnt[2]) < 2.6), PLATE, p=newid(), l=4)
for t_ in np.linspace(0, .96, 40):                                                # overlapping blocks taper along the arch
    pnt = (1 - t_) ** 2 * np.array(W_) + 2 * t_ * (1 - t_) * _C + t_ * t_ * np.array(F[0])
    hb_ = 2.6 - 1.7 * t_; off = 3.2 - 2.0 * t_
    put((np.abs(AX - pnt[0]) < hb_) & (np.abs(Y - pnt[1] - off) < hb_) & (np.abs(Z - pnt[2]) < hb_), PLATE, p=newid(), l=4)
put(chain([W_, (W_[0] + 1, W_[1] + 5, W_[2] - 4), (W_[0] + 1, W_[1] + 7, W_[2] - 9)], [2.0, 1.2, .4]), DEEP, st=False, p=newid(), l=5)
# a few lava cracks on the arm
put(chain([E_, W_], [4.1, 3.6]) & ~chain([E_, W_], [3.0, 2.6]) & (np.abs((Z * 3 + Y) % 11) < 1.0) & (kind == 1), LAVA, st=False)

X, Y, Z, AX = _S                                                                 # back to the 1.2x body coords
unrec(WINGM)
# ---------------------------------------------------------------- spine + tail spikes, spade tip
xi = int(round(0.5 - lo[0] - .5))
def top_at(z):
    xi = int(round(xo(z) * GS * BS + .5 - lo[0] - .5))
    zi = int(round(z * GS * BS - lo[2] - .5)); c_ = np.where(kind[xi, :, zi] > 0)[0]
    return None if not len(c_) else (lo[1] + .5 + c_.max()) / GS / BS
zd = cz / GS / BS; xd = cx / GS / BS
for zi_ in np.where((zd > -60) & (zd < 93))[0]:                                    # glowing seam down the spine, raised 1 brick
    for xc in np.where(np.abs(xd - xo(zd[zi_])) < 1.6)[0]:
        c_ = np.where(kind[xc, :, zi_] > 0)[0]
        if not len(c_): continue
        yi_ = c_.max()
        if kind[xc, yi_, zi_] == 1 and pid[xc, yi_, zi_] >= 1000:
            if zd[zi_] < -18 or zd[zi_] > 40: col[xc, yi_, zi_] = LAVA; keep[xc, yi_, zi_] = True; pid[xc, yi_, zi_] = 0; continue   # neck and tail: solid lava bricks, no halo
            kind[xc, yi_, zi_] = 2; col[xc, yi_, zi_] = GLOW[2]
            if yi_ + 1 < n[1] and kind[xc, yi_ + 1, zi_] == 0: kind[xc, yi_ + 1, zi_] = 2; col[xc, yi_ + 1, zi_] = GLOW[2]
TOPS = {zs: top_at(zs) for zs in range(-58, 95, 7)}                             # sample the back BEFORE adding spikes (no stacking)
for zs, yt in TOPS.items():
    if yt is None: continue
    L = float(np.interp(zs, [-58, -40, -10, 10, 30, 60, 93], [5.5, 8.5, 11.5, 12.0, 12.0, 11.0, 8.5]))
    x_ = xo(zs)
    put(chain([(x_, yt - 1.2, zs), (x_, yt + L * .55, zs + 1.0), (x_, yt + L, zs + 2.6)], [L * .28, L * .16, .4], X), DEEP, st=False, p=newid(), l=6)
# spade: vertical arrowhead, glowing rim + centre line
SPZ = 115.0; SY = 9 + LIFT; SAX = AX                    # spade on the centre plane (tail straight back)
hsp = np.where(Z < 100, (Z - 90) * 1.35, (SPZ - Z) * .9)
sp = (SAX < 2.2) & (np.abs(Y - SY) < hsp) & (Z > 90) & (Z < SPZ)
put(sp, CHAR, p=newid(), l=4)
sp_in = sp & (np.abs(Y - SY) < hsp - 1.6) & (Z > 91.5) & (Z < SPZ - 1.8)      # dark outline all round (edge-on = dark)
inner = sp & (np.abs(Y - SY) < hsp - 3.4) & (Z > 93) & (Z < SPZ - 3.6)
put(sp_in & ~inner & (SAX > 1.5), GLOW[2], k=2, st=False)                         # glow ring only on the two outer faces
put(inner & (np.abs(Y - SY) < .8) & (SAX > 1.5), GLOW[3], k=3, st=False)

# ---------------------------------------------------------------- connectivity: drop any brick not 26-connected to the body
def _dil(m):                                                                    # 3x3x3 dilation (separable) = 26-neighbourhood
    o = m
    for ax in range(3):
        a_ = [slice(None)] * 3; b_ = [slice(None)] * 3; a_[ax] = slice(1, None); b_[ax] = slice(None, -1)
        t = o.copy(); t[tuple(a_)] |= o[tuple(b_)]; t[tuple(b_)] |= o[tuple(a_)]; o = t
    return o
_sol = kind > 0
_ix = np.argwhere(_sol); _a, _b = _ix.min(0), _ix.max(0) + 1
_sc = _sol[_a[0]:_b[0], _a[1]:_b[1], _a[2]:_b[2]]
_reach = np.zeros_like(_sc); _c0 = (np.array(_sc.shape) // 2)
_seed = np.argwhere(_sc[:, :, _c0[2]]); _reach[_seed[0][0], _seed[0][1], _c0[2]] = True
for _it in range(4000):
    _nr = _dil(_reach) & _sc
    if _it % 8 == 0 and _nr.sum() == _reach.sum(): break
    _reach = _nr
_drop = _sc & ~_reach
print('CONN_OK kept', int(_reach.sum()), 'dropped floating', int(_drop.sum()))
kind[_a[0]:_b[0], _a[1]:_b[1], _a[2]:_b[2]][_drop] = 0
# ---------------------------------------------------------------- seams + shading + palette
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1) & ~keep] *= .6
shf = np.clip(.72 + .5 * (Y / 60.0), .72, 1.2)
col *= np.where(keep, 1.0, shf)[..., None]
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('1c1c22', '2a2a31', '3a3a42', '55555e', '0c0c10',            # charcoal deep / main / plates / stone / black
                                 'b0221a', '6e1410', 'dc4a1c',                                # wing red / dark cell / red-orange edge
                                 'ffbe2a', 'ff8a10', 'c85a0a',                                # belly yellow / orange / seam
                                 '7a5e4c', '5a463a', 'f0e0c0', 'c8b090', 'ff9a1c')])          # horn / horn shade / ivory / ivory shade / stone light
if HUE: PAL[[5, 6, 7, 8, 9, 10, 15]] = [vr(c) for c in PAL[[5, 6, 7, 8, 9, 10, 15]]]
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
    # POSITION PASS data: every face carries the brick coordinates of its centre, scaled 0..1 over the grid, so a render
    # of this attribute tells each pixel which brick it shows (scripts/fx_bake.py reads it to run effects in 3D)
    cen_ = np.repeat(Vt.reshape(-1, 4, 3).mean(1), 4, axis=0); pn = np.clip((cen_ - lo) / (hi - lo), 0, 1)
    pa = me.color_attributes.new('Pos', 'FLOAT_COLOR', 'POINT')
    pa.data.foreach_set('color', np.concatenate([pn, np.ones((len(pn), 1))], 1).ravel())
    me.color_attributes.active_color = ca; me.color_attributes.render_color_index = 0
    ul = me.uv_layers.new(name='UVMap')
    li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
    ul.data.foreach_set('uv', UV[li].ravel())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
BELLYM = BELLYM | ((kind == 1) & (np.abs(col - LAVA).sum(-1) < 1e-3))                 # lava cracks share the molten (emissive) material
body = build('EmberDragon', (kind == 1) & ~BELLYM, True)
belly = build('Belly', (kind == 1) & BELLYM, True)
m = bpy.data.materials.new('Brick'); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
bs.inputs['Roughness'].default_value = .6
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
tx.image.colorspace_settings.name = 'Non-Color'
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 1
nt.links.new(at.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
body.data.materials.append(m); body['glow'] = False
mb = m.copy(); mb.name = 'BellyMolten'; bb = mb.node_tree.nodes['Principled BSDF']
mb.node_tree.links.new([nd for nd in mb.node_tree.nodes if nd.type == 'MIX'][0].outputs[2], bb.inputs['Emission Color']); bb.inputs['Emission Strength'].default_value = .55
belly.data.materials.append(mb)
GL = []
for k, c in GLOW.items():
    if not (kind == k).any(): continue
    o = build('Glow%d' % k, kind == k, False)
    gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
    cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
    b2.inputs['Emission Strength'].default_value = 5.0; gm.diffuse_color = cl
    o.data.materials.append(gm); o.color = cl; GL.append(o)
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')
np.savez_compressed(os.path.join(OUT, 'solid.npz'), solid=np.packbits(kind > 0), shape=np.array(n))

def B(x, y, z): return Vector((x, z, y)) * GS
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for sx in (1, -1):                                                         # eye lights: glow spills onto brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 3000; L.data.color = tuple(vr((1.0, .353, .039))); L.data.shadow_soft_size = 1.0
        L.location = B(11.0 * sx * BS, 59.8 * BS, -86.0 * BS); L.data.energy = 3000 * GS * GS
    L = bpy.data.objects.new('MouthLight', bpy.data.lights.new('MouthLight', 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 2500; L.data.color = tuple(vr((1.0, .45, .08))); L.location = B(0, 44.5 * BS, -101 * BS); L.data.energy = 2500 * GS * GS
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
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.26, .4, .2, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 20000
    PTS = np.concatenate([np.array([v.co[:] for v in o.data.vertices])[::7] for o in [body, belly] + GL])   # model points (Blender coords)
    def fit(dv, lens, ortho):                         # tight framing: centre the projected model, size to fit (4% margin)
        dv = np.array(dv[:]); up = np.array((0, 0, 1.0)) if abs(dv[2]) < .99 else np.array((0, 1.0, 0))
        r = np.cross(up, dv); r /= np.linalg.norm(r); u = np.cross(dv, r)
        pr = PTS @ r; pu = PTS @ u; pf = PTS @ dv
        c = r * (pr.max() + pr.min()) / 2 + u * (pu.max() + pu.min()) / 2 + dv * (pf.max() + pf.min()) / 2
        q = PTS - c; qr = np.abs(q @ r); qu = np.abs(q @ u); qf = q @ dv
        if ortho: return Vector(c), 3000, 2.08 * max(qr.max(), qu.max())
        th = 18.0 / lens
        return Vector(c), 1.04 * max(((qr / th) + qf).max(), ((qu / th) + qf).max()), None
    def pos_pass(p):                                                  # flat render of the 'Pos' attribute, 16 bit, linear
        keng = sc.render.engine; sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'VERTEX'
        sh.show_shadows = False; sh.show_cavity = False; g.hide_render = True; sc.render.film_transparent = True
        for o in [body, belly] + GL: o.data.color_attributes.render_color_index = 1; o.data.color_attributes.active_color_index = 1
        sc.view_settings.view_transform = 'Raw'; sc.render.image_settings.color_depth = '16'
        sc.render.filepath = p[:-4] + '_pos.png'; bpy.ops.render.render(write_still=True)
        for o in [body, belly] + GL: o.data.color_attributes.render_color_index = 0; o.data.color_attributes.active_color_index = 0
        sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.color_depth = '8'
        sc.render.film_transparent = False; g.hide_render = False; sh.color_type = 'OBJECT'; sc.render.engine = keng
    def view(name, tgt, dist, az, el, lens=50, ortho=None):
        dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
        if tgt is None: t, dist, ortho = fit(dv, lens, ortho)
        else: t = B(*tgt); dist = dist * GS
        cam.location = t + dv * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        cam.data.type = 'ORTHO' if ortho else 'PERSP'
        if ortho: cam.data.ortho_scale = ortho
        p = os.path.join(REN, '%s_%s.png' % (ID, name))
        if POS_ONLY: pos_pass(p); return
        sc.render.engine = ENG; sc.render.film_transparent = False; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_shadows = False; sh.show_cavity = False
        g.hide_render = True; sc.render.film_transparent = True; sc.render.filepath = p[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
        sc.render.film_transparent = False; keep_ = tuple(sc.world.color); sc.world.color = (0, 0, 0); sh.background_type = 'WORLD'
        body.color = (0, 0, 0, 1); belly.color = (0, 0, 0, 1)
        sc.render.filepath = p[:-4] + '_glow.png'; bpy.ops.render.render(write_still=True)
        sc.world.color = keep_; g.hide_render = False; body.color = (1, 1, 1, 1); belly.color = (1, 1, 1, 1)
        pos_pass(p)
    cen = None; D = 0                                  # None = auto tight framing
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, None, 0, az, el, ortho=True)
    for nm, a in (('rest_34', (cen, D, 35, 14)), ('rest_side', (cen, D, 90, 8)), ('rest_front', (cen, D, 0, 8)), ('rest_back', (cen, D, 150, 18)),
                  ('face', ((0, 67, -100), 96, 0, 4)), ('headside', ((0, 70, -90), 114, 90, 4)), ('head34', ((0, 70, -93), 120, -38, 10)),
                  ('footfront', ((-33, 8, -35), 56, 0, 6)), ('footside', ((-33, 8, -35), 60, -90, 4)), ('feet', ((0, 10, 0), 220, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
POS_ONLY = bool(os.environ.get('SV_POS_ONLY'))                       # render only the position pass, then stop (no rig export)
if 'render' in argv: render_all()
if POS_ONLY: print('POS_OK'); raise SystemExit(0)

# ---------------------------------------------------------------- rig (always): bones in brick coords, L = +x
X, Y, Z = np.meshgrid(cx.astype(np.float32), cy.astype(np.float32), cz.astype(np.float32), indexing='ij')   # brick coords
K_ = GS * BS
def b_(x, y, z): return (x * K_, y * K_, z * K_)                                       # body coords (lifted y) -> bricks
def h_(x, y, z): return b_(x * HS, 40 + HOY + (y - 40) * HS, -48 + HOZ + (z + 48) * HS)   # head coords -> bricks
def w_(p, sx): return (p[0] * GS * sx, p[1] * GS, p[2] * GS)                           # wing design coords -> bricks
NK = [b_(0, 34, -23), b_(0, 46, -28), b_(0, 57, -33), b_(0, 65, -45), b_(0, 57, -61)]
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', b_(0, 32, 21), b_(0, 31, 2)), ('spine', 'hips', b_(0, 31, 2), b_(0, 30, -20))]
RIG += [('neck_%d' % (i + 1), 'spine' if i == 0 else 'neck_%d' % i, NK[i], NK[i + 1]) for i in range(4)]
RIG += [('head', 'neck_4', NK[4], h_(0, 41, -78)), ('jaw', 'head', h_(0, 34, -46), h_(0, 31, -76))]
TL = [b_(0, 32, 21), b_(TX[1], 31, 39), b_(0, 27, 54), b_(0, 22, 68), b_(0, 18, 82), b_(0, 15, 115)]
TAILB = [('tail_%d' % (i + 1), 'hips' if i == 0 else 'tail_%d' % i, TL[i], TL[i + 1]) for i in range(5)]
RIG += TAILB
Xb, Yb, Zb = X / K_, Y / K_, Z / K_; AXb = np.abs(Xb)                                  # body coords (unlifted y)
Yh = 40 + (Yb - 40 - HOY) / HS; Zh = -48 + (Zb + 48 - HOZ) / HS; AXh = AXb / HS
sol_ = kind > 0
JAWM = HEADM & (((Zh < -45.5) & (Yh < 34.6) & (AXh < 9) & ~UPF) | LOWF)
OVR = brick_rig.limb(X, Y, Z, sol_ & (Zb > 34) & (AXb < 12) & ~WINGM, TAILB)
for sx, sd in ((1, 'L'), (-1, 'R')):
    LF = [b_(19 * sx, 30, -18), b_(24 * sx, 16, -20), b_(27 * sx, 5, -24), b_(27 * sx, 1, -38)]
    LB = [b_(19 * sx, 30, 20), b_(25 * sx, 18, 16), b_(27 * sx, 6, 21), b_(27 * sx, 1, 7)]
    for fb, P_, par, zr in (('F', LF, 'spine', (-46, -4)), ("B", LB, "hips", (2, 36))):
        ch = [('leg%s%s_%s' % (fb, sd, nm), par if i == 0 else 'leg%s%s_%s' % (fb, sd, ('up', 'low')[i - 1]), P_[i], P_[i + 1]) for i, nm in enumerate(('up', 'low', 'foot'))]
        RIG += ch
        OVR += brick_rig.limb(X, Y, Z, sol_ & (Xb * sx > 9) & (Yb < 27) & (Zb > zr[0]) & (Zb < zr[1]) & ~BELLYM & ~WINGM, ch)
    # wing: shoulder -> forearm -> arch finger (2 bones) + 3 membrane fingers, so the membrane folds/flaps
    WA = [w_(S_, sx), w_(E_, sx), w_(W_, sx)]
    WB = [('wing%s_arm' % sd, 'spine', WA[0], WA[1]), ('wing%s_fore' % sd, 'wing%s_arm' % sd, WA[1], WA[2]),
          ('wing%s_f0a' % sd, 'wing%s_fore' % sd, WA[2], w_(ARCH[5], sx)), ('wing%s_f0b' % sd, 'wing%s_f0a' % sd, w_(ARCH[5], sx), w_(F[0], sx))]
    WB += [('wing%s_f%d' % (sd, k + 1), 'wing%s_fore' % sd, WA[2], w_(F[k + 1], sx)) for k in range(3)]
    RIG += WB
    OVR += brick_rig.limb(X, Y, Z, WINGM & (X * sx > 0), WB)
OVR += [(HEADM, 'head'), (JAWM, 'jaw')]
del Xb, Yb, Zb, AXb, Yh, Zh, AXh
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'neck_1': (-12, 0, 0), 'head': (20, 0, 0), 'jaw': (30, 0, 0), 'wingL_arm': (0, 0, 35), 'wingR_arm': (0, 0, -15),
                       'wingL_f1': (0, 0, 20), 'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail_3': (0, 0, 25)},
                 render='render' in argv)
print('BL_OK')
