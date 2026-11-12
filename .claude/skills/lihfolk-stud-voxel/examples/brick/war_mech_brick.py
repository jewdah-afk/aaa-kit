# War Mech - giant steampunk war mech (stud-voxel brick pipeline, after WarMech/concept_sheet.jpg)
# GLOW: subtle   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Machine built from primitives on the grid (boxes, oriented beams, cylinders, gears, rivet rows) like arcane_train:
# brass + rust-brick cabin in a dark iron frame, gear-rimmed red cyclops eye, furnace grille, hazard pauldrons,
# 6-barrel gatling (right), 3-finger crusher claw (left), reverse-jointed legs with pistons, exhaust stacks + smoke.
# Run: run_brick.ps1 war_mech_brick.py   Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'WarMech'

lo = np.array((-58.0, -0.5, -44.0)); hi = np.array((58.0, 95.5, 30.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
BRASSL = hx('f0cf6a'); BRASS = hx('d4a53a'); BRASSD = hx('9c7424'); BRASSDD = hx('6e521c')
COPPER = hx('e8894a'); COPPERD = hx('8f4c26'); BROWN = hx('a0532e'); BROWND = hx('6b3520')
IRONL = hx('6a6a72'); IRON = hx('45454c'); IROND = hx('2a2a30'); HAZ = hx('f5c518'); BLACK = hx('121214')
SMOKE = hx('8c8c92'); SMOKED = hx('5e5e64'); STEAM = hx('eceff2')
GLOW = {2: hx('ff2a14'), 3: hx('ff9a80'), 4: hx('fff4ee'), 5: hx('ff7012'), 6: hx('ffd24a')}  # eye red / eye hot / glint / furnace / furnace hot

NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
def put(m, rgb, k=1, p=None, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = k == 1; pid[m] = newid() if p is None else p; lvl[m] = l
def carve(m): kind[m] = 0

def box(x0, x1, y0, y1, z0, z1, s=0):              # s=0: symmetric in x (|x|); s=+-1: one side only
    xx = AX if s == 0 else X * s
    return (xx > x0) & (xx < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def sph(c, r): return (X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2 < r * r
def cylx(y, z, r, x0, x1, s=0):
    xx = AX if s == 0 else X * s
    return ((Y - y) ** 2 + (Z - z) ** 2 < r * r) & (xx > x0) & (xx < x1)
def cyly(x, z, r, y0, y1): return ((X - x) ** 2 + (Z - z) ** 2 < r * r) & (Y > y0) & (Y < y1)
def cylz(x, y, r, z0, z1): return ((X - x) ** 2 + (Y - y) ** 2 < r * r) & (Z > z0) & (Z < z1)
def obox(a, b, hw, hd, ext=0.0):                   # oriented beam a->b; hw across x, hd across the other axis
    a = np.array(a, float); b = np.array(b, float); L = np.linalg.norm(b - a); u = (b - a) / L
    v = np.array((1.0, 0, 0)) - u[0] * u; v /= np.linalg.norm(v); w = np.cross(u, v)
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    t = px * u[0] + py * u[1] + pz * u[2]
    return (t > -ext) & (t < L + ext) & (np.abs(px * v[0] + py * v[1] + pz * v[2]) < hw) & (np.abs(px * w[0] + py * w[1] + pz * w[2]) < hd)
def cap(a, b, ra, rb=None):
    rb = ra if rb is None else rb
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def pipe(pts, r):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], r)
    return m
def gear(c, axis, r, rt, teeth, a0, a1, phase=0.0):   # (body, teeth) masks; c = centre (x,y,z); a0..a1 = range along the axis
    if axis == 'x': p, q, al = Y - c[1], Z - c[2], X
    elif axis == 'y': p, q, al = X - c[0], Z - c[2], Y
    else: p, q, al = X - c[0], Y - c[1], Z
    rr = np.sqrt(p * p + q * q); th = np.arctan2(q, p) + phase
    on = (al > a0) & (al < a1)
    tooth = (np.mod(th * teeth / (2 * np.pi), 1.0) < .5) & (rr >= r) & (rr < rt) & on
    return (rr < r) & on, tooth
YOFF = [0.0]                                        # upper body is built in coords lowered by YOFF (see LIFT)
def cell(x, y, z):                                  # one voxel at the centre nearest (x,y,z)
    i = int(round(x - lo[0] - .5)); j = int(round(y + YOFF[0] - lo[1] - .5)); k = int(round(z - lo[2] - .5))
    m = np.zeros(n, bool)
    if 0 <= i < n[0] and 0 <= j < n[1] and 0 <= k < n[2]: m[i, j, k] = True
    return m
def rivets(pts, rgb=BRASSL):                       # rivet heads: single proud bricks (pid 0 = no seam halo)
    m = np.zeros(n, bool)
    for p in pts: m |= cell(*p)
    put(m, rgb, p=0)


# ================================================================ FEET (big clawed brass feet: 3 toes with dark claws + heel spur)
for s in (1, -1):
    fx = 21.0
    put(box(fx - 8.5, fx + 8.5, -1, 3, -11, 9, s), IROND, l=0)                                     # sole / dark toe gaps
    put(box(fx - 8, fx + 8, -1, 6, -10, 8, s), BRASS, l=1)                                         # foot block
    put(box(fx - 7, fx + 7, 5.5, 7, -8, 6, s), BRASSD, l=2)                                        # raised top plate
    for t in range(3):
        a = fx - 8.5 + 6 * t; f = 2 if t == 1 else 0
        put(box(a, a + 5, -1, 5, -16 - f, -9, s), BRASS, l=1)                                      # toe
        put(box(a + 1, a + 4, 4.5, 6, -14 - f, -9, s), BRASSL, l=1)                                # toe top
        put(box(a, a + 5, -1, 3.5, -18 - f, -15.9 - f, s), IROND, l=2)                             # claw
        put(box(a + 1, a + 4, -1, 2, -20 - f, -17.9 - f, s), IROND, l=2)
    put(box(fx - 2.5, fx + 2.5, -1, 4, 7, 13, s), BRASS, l=1)                                      # heel spur
    put(box(fx - 1.5, fx + 1.5, -1, 2.5, 12.9, 15, s), IROND, l=2)
    rivets([(s * (fx + xx), 7, zz) for xx in (-6.5, 6.5) for zz in (-6.5, -3.5, -.5, 2.5, 5.5)])
    put(box(fx - 5, fx + 5, 5, 11, -3, 7, s), IRON, l=1)                                           # ankle housing

# ================================================================ LEGS (reverse joint: knee forward, shin back) + pistons + gears
for s in (1, -1):
    H = (14.0 * s, 33.0, 2.0); K = (22.0 * s, 20.0, -8.0); A = (21.0 * s, 7.0, 3.0)
    put(obox(H, K, 5.5, 5.5, 1.5), BROWN, l=1)                                                     # thigh (rust brick)
    put(obox(H, K, 6.3, 4.6, -1.0) & ~obox(H, K, 5.5, 9, 3), BRASS, l=2)                           # side plates
    put(obox(H, K, 6.2, 6.2) & ~obox(H, K, 9, 9, -2.2) | obox(K, H, 6.2, 6.2) & ~obox(K, H, 9, 9, -2.2), BRASSD, l=2)  # end cuffs
    put(obox(K, A, 4.6, 5.0, 1.0), BRASS, l=1)                                                     # shin plate
    put(obox(K, A, 2.4, 5.8) & ~obox(K, A, 9, 9, -2.5) & ~obox(A, K, 9, 9, -2.5), BRASSD, l=2)     # shin ridge
    put(obox(K, A, 5.2, 5.6) & ~obox(K, A, 9, 9, -4.5) & ~obox(A, K, 9, 9, -4.5), BROWN, l=2)      # shin band
    put(cylx(K[1], K[2], 4.4, 15, 27.5, s), IRON, l=2)                                              # knee axle housing
    g, t = gear(K, 'x', 6.0, 7.8, 12, 27 if s > 0 else -29.5, 29.5 if s > 0 else -27)
    put(g, BRASS, l=3); put(t, BRASSD, l=3); put(cylx(K[1], K[2], 1.8, 27, 30.5, s), IROND, l=4)
    put(cylx(H[1], H[2], 4.6, 9, 21, s), IRON, l=2)                                                 # hip axle housing
    g, t = gear(H, 'x', 4.5, 6.0, 10, 20 if s > 0 else -22.5, 22.5 if s > 0 else -20)
    put(g, BRASS, l=3); put(t, BRASSD, l=3); put(cylx(H[1], H[2], 1.6, 20, 23.5, s), IROND, l=4)
    put(cylx(A[1], A[2], 3.4, 15, 27, s), IROND, l=2)                                               # ankle axle
    put(pipe([(16.5 * s, 30, 7.5), (21.0 * s, 9, 8.5)], 1.6), COPPER, l=3)                          # rear piston rod
    put(pipe([(16.5 * s, 30, 7.5), (18.2 * s, 23, 7.8)], 2.2), IRON, l=3)                           # piston cylinder
    put(pipe([(21.0 * s, 29, -4.0), (24.5 * s, 22, -10.5)], 1.1), COPPER, l=3)
    put(pipe([(26.0 * s, 17, -6.5), (25.5 * s, 9, 1.5)], 1.2), COPPER, l=4)                         # shin piston (outside)
    put(sph((26.0 * s, 17, -6.5), 1.7) | sph((25.5 * s, 9, 1.5), 1.7), IROND, l=4)                      # thigh pipe

# ---------------------------------------------------------------- LIFT: everything above the legs is modelled 8 units lower
Y0 = Y; LIFT = 8.0; Y = Y0 - LIFT; YOFF[0] = LIFT
# ================================================================ PELVIS
put(box(0, 13, 17, 27, -7, 9), IRON, l=0)
put(box(0, 14, 19, 23, -8, 10), BRASSD, l=1)                                                       # belt
rivets([(x, 21, -8.5) for x in (-12.5, -9.5, -6.5, -3.5, -.5, 3.5, 6.5, 9.5, 12.5)])

# ================================================================ CABIN (iron core, proud panels with iron frame lines, chamfered)
hw = np.clip(14.0 + (Y - 26.0) * .5, 14.0, 18.0)
core = (AX < hw) & (Y > 25) & (Y < 62) & (Z > -14) & (Z < 14)
core &= ~(((AX - hw) + (Y - 62)) > -2.5) & ~(((AX - hw) + (-Z - 14)) > -2.5) & ~(((Y - 62) + (-Z - 14)) > -2.5)
core &= ~(((AX - hw) + (Z - 14)) > -2.5) & ~(((Y - 62) + (Z - 14)) > -2.5)
put(core, IRON, l=0)
put(box(0, 16.5, 61, 63, -12, 12), IRONL, l=1)                                                     # roof plate
put(box(0, 14.5, 62.5, 64, -10, 10), BRASSD, l=2)                                                  # roof hood
FR = (Z > -15) & (Z < -14)                                                                          # front panel layer
put(FR & (AX < 11) & (Y > 39.5) & (Y < 61), BRASS, l=1)                                            # eye plate
put(FR & (AX > 12) & (AX < hw) & (Y > 45.5) & (Y < 61), BROWN, l=1)                                # upper side plates
put(FR & (AX > 12) & (AX < hw) & (Y > 55.5) & (Y < 61), BRASS, l=1)                                # upper corner plates
put(FR & (AX < 11) & (Y > 39.5) & (Y < 61) & ((AX + np.abs(Y - 50)) > 16.5), BROWN, l=1)          # eye plate: octagon corners
put(FR & (AX > 12) & (AX < hw) & (Y > 34.5) & (Y < 45), BROWN, l=1)                                # side brick plates
put(FR & (AX > 10.5) & (AX < hw - .5) & (Y > 25.5) & (Y < 34), BROWN, l=1)                         # lower brick plates
SD = (AX > 18) & (AX < 19)                                                                          # side panels under the pauldrons
put(SD & (Y > 31) & (Y < 39.5) & (Z > -12) & (Z < -.5), BROWN, l=1)
put(SD & (Y > 31) & (Y < 39.5) & (Z > .5) & (Z < 12), BROWN, l=1)
BK = (Z > 14) & (Z < 15)                                                                            # back panels
put(BK & (AX < 10) & (Y > 26) & (Y < 61), BROWN, l=1)
put(BK & (AX > 11) & (AX < hw - .5) & (Y > 26) & (Y < 43), BRASS, l=1)
put(BK & (AX > 11) & (AX < hw - .5) & (Y > 43.5) & (Y < 61), BROWN, l=1)
rivets([(s * x, y, -15.5) for s in (1, -1) for x in (12.5, 14.5, 16.5) for y in (47, 60)])        # rivet rows (front)
rivets([(s * x, y, -15.5) for s in (1, -1) for x in (12.5, 14.5, 16.5) for y in (36, 44)], BRASSD)
rivets([(s * x, y, 15.5) for s in (1, -1) for x in (11.5, 13.5, 15.5) for y in (28, 42)])           # rivet rows (back)

# ---- cyclops eye: brass gear rim (proud) around a recessed red lens
E = (0.0, 50.0, -14.5)
g, t = gear(E, 'z', 9.2, 10.7, 14, -16, -14, phase=.11)
put(g, BRASS, l=3); put(t, BRASSL, l=3)
put(((X ** 2 + (Y - E[1]) ** 2) < 7.8 ** 2) & (Z > -16) & (Z < -15), BRASSD, l=3)                 # inner bevel ring
carve(((X ** 2 + (Y - E[1]) ** 2) < 6.7 ** 2) & (Z > -16) & (Z < -14))
put(((X ** 2 + (Y - E[1]) ** 2) < 6.7 ** 2) & (Z > -14) & (Z < -13), BLACK, l=0)                  # socket wall
put(((X ** 2 + (Y - E[1]) ** 2) < 6.0 ** 2) & (Z > -14) & (Z < -13), GLOW[2], k=2)                # lens
rivets([(8.5 * math.cos(math.radians(a + 22.5)), E[1] + 8.5 * math.sin(math.radians(a + 22.5)), -16.5) for a in range(0, 360, 45)], IRONL)

# ---- furnace: copper frame, recessed grille of vertical glowing bars
put((AX < 9.5) & (Y > 26.5) & (Y < 39.5) & (Z > -16) & (Z < -14), COPPER, l=3)
put((AX < 10) & (Y > 26) & (Y < 28.5) & (Z > -16.5) & (Z < -14), COPPERD, l=3)                   # sill
carve((AX < 7) & (Y > 28.5) & (Y < 38) & (Z > -16) & (Z < -14))
gi = np.floor(X + 7.0).astype(int)
bar = (AX < 7) & (Y > 28.5) & (Y < 38) & (Z > -14) & (Z < -13)
put(bar, IROND, l=0)
put(bar & (gi % 3 != 2), GLOW[5], k=5)
put(bar & (gi % 3 != 2) & (Y > 30.5) & (Y < 35.5), GLOW[6], k=6)
put((AX < 7) & (Y > 28.5) & (Y < 38) & (Z > -16) & (Z < -14) & (gi % 3 == 2), IROND, l=2)          # grille bars (proud, dark)
rivets([(s * 8.5, y, -16.5) for s in (1, -1) for y in (30, 33, 36)] + [(x, 39, -16.5) for x in (-7.5, -4.5, -1.5, 1.5, 4.5, 7.5)], COPPERD)

# ---- copper pipes framing the furnace, up to side vents with steam
for s in (1, -1):
    put(pipe([(s * 11.5, 27, -15.5), (s * 11.5, 41, -15.5), (s * 15.5, 41, -15.5), (s * 15.5, 44, -15.5)], 1.7), COPPER, l=4)
    put(cylx(28, -15.5, 2.0, 10, 13, s), BRASSD, l=4)                                               # pipe clamp
    put(cyly(s * 15.5, -15.5, 2.0, 43, 46.5), IRON, l=4)                                            # vent stub
    put(cyly(s * 15.5, -15.5, 1.1, 45.5, 47), BLACK, l=4)
    for (dx, y, dz, r) in ((0, 48.6, -.6, 2.4), (.9, 51.2, -1.0, 2.2), (.3, 53.6, -1.4, 1.7)):  # steam cloud
        put(sph((s * (15.5 + dx), y, -15.5 + dz), r), STEAM, l=5)

# ================================================================ PAULDRONS (brass over rust brick, hazard-striped top blocks) + shoulder gears
for s in (1, -1):
    pd = box(16.5, 37, 39, 62, -12, 12, s) & ~(((X * s - 37) + (Y - 62)) > -4) & ~(((X * s - 37) + (39 - Y)) > -3)
    pd &= ~(((-Z - 12) + (X * s - 37)) > -2.5) & ~(((Z - 12) + (X * s - 37)) > -2.5)
    put(pd, BROWN, l=2)
    put(pd & (Z < -10.5) & (X * s > 18) & (X * s < 35) & (((Y > 41.5) & (Y < 47.5)) | ((Y > 48.5) & (Y < 55))), BRASS, l=2)   # front plates
    put(pd & (X * s > 35.5) & (Z > -9) & (Z < 9) & (Y > 41.5) & (Y < 55), BRASS, l=2)                # outer plate
    put(pd & (Z > 10.5) & (X * s > 18) & (X * s < 35) & (Y > 48.5) & (Y < 55), BRASS, l=2)            # back plate
    put(pd & (Y < 41.5), BRASSD, l=2)                                                               # lower rim
    hz = box(18.5, 35, 55, 65, -13.5, 2.5, s) & ~(((X * s - 35) + (Y - 65)) > -3.5) & ~(((Y - 65) + (-Z - 13.5)) > -2.5)
    stripe = (np.floor((X * s + Y - Z) / 3.0).astype(int) % 2) == 0
    P = newid(); put(hz & stripe, HAZ, p=P, l=4); put(hz & ~stripe, BLACK, p=P, l=4)
    put(box(18.5, 35, 53.8, 55.2, -13.5, 2.5, s) & ~hz, IROND, l=3)
    cp = box(18.5, 34, 54, 62, 2, 11, s) & ~(((X * s - 34) + (Y - 62)) > -3) & ~(((Y - 62) + (Z - 11)) > -2.5)
    put(cp, BRASS, l=3); put(cp & (Y > 60.5), BRASSL, l=3)                                         # brass cap behind the hazard block                                # dark lip under the hazard block
    rivets([(s * x, y, -12.5) for x in (18.5, 20.5, 22.5, 24.5, 26.5, 28.5, 30.5, 32.5) for y in (43, 53)])
    rivets([(s * x, y, 12.5) for x in (18.5, 22.5, 26.5, 30.5) for y in (43, 53)])
    rivets([(s * 37.5, y, z) for y in (43, 52) for z in (-10.5, -7.5, 7.5, 10.5)])
    g, t = gear((0, 47, 1), 'x', 4.8, 6.4, 10, 36.5 if s > 0 else -39.5, 39.5 if s > 0 else -36.5)
    put(g & (np.sign(X) == s), BRASSD, l=5); put(t & (np.sign(X) == s), BRASS, l=5)
    put(cylx(47, 1, 1.8, 36.5, 40.5, s), IROND, l=6)
    put(cylx(46, 0, 6.0, 15, 28, s), IRON, l=1)                                                     # shoulder joint

# ================================================================ RIGHT ARM (-x): 6-barrel gatling cannon
SH = (-27.0, 44.0, 0.0); EB = (-35.0, 35.0, 1.0)
put(obox(SH, EB, 4.4, 4.4, 1.5), IRON, l=1)                                                         # upper arm
put(obox(SH, EB, 5.0, 5.0) & ~obox(SH, EB, 9, 9, -3.0) & ~obox(EB, SH, 9, 9, -3.0), BROWN, l=2)
GX, GY = -39.0, 29.0
put(cylz(GX, GY, 9.0, -6, 10), BRASS, l=2)                                                          # drum
put(cylz(GX, GY, 9.6, -3, -1) | cylz(GX, GY, 9.6, 6, 8), IRON, l=3)                                 # drum bands
put(cylz(GX, GY, 6.2, 9.5, 12.5), IRON, l=2)
put(cylz(GX, GY, 2.6, 11, 13.5), BRASSD, l=3); put(cylz(GX, GY, 1.0, 12, 14), IROND, l=4)               # rear hub
rivets([(GX + 4.6 * math.cos(math.radians(a)), GY + 4.6 * math.sin(math.radians(a)), 12.5) for a in range(0, 360, 45)], IRONL)                                                        # rear cap
put(cylz(GX, GY, 7.6, -11, -5.5), BRASSD, l=2)                                                       # front collar
put(cylz(GX, GY, 8.4, -9, -7), BRASS, l=3)
put(cylz(GX, GY, 2.0, -38, -10), IROND, l=1)                                                         # spindle
BAR = np.zeros(n, bool); BORE = np.zeros(n, bool)
for i in range(6):
    a = math.radians(90 + 60 * i); bx, by = GX + 4.9 * math.cos(a), GY + 4.9 * math.sin(a)
    BAR |= cylz(bx, by, 2.35, -39, -10); BORE |= cylz(bx, by, 1.45, -40, -35)
put(BAR, IRON, l=1)
put(cylz(GX, GY, 7.6, -25, -22), BRASS, l=3)                                                         # barrel band
put(cylz(GX, GY, 7.6, -35, -32.5), IRONL, l=3)                                                       # muzzle ring
put(BORE | cylz(GX, GY, 1.0, -40, -35), BLACK, l=0)
carve(cylz(GX, GY, 8.5, -40, -36) & ~BAR)                                                            # barrel tips stand free
rivets([(GX + 10.1 * math.cos(math.radians(a)), GY + 10.1 * math.sin(math.radians(a)), z) for a in range(0, 360, 30) for z in (-2.5, 6.5)], IRONL)
rivets([(GX + 8.9 * math.cos(math.radians(a)), GY + 8.9 * math.sin(math.radians(a)), -8.5) for a in range(15, 360, 30)])
put(pipe([(-36, 36, 9), (-32, 42, 10), (-24, 44, 10)], 1.3), COPPER, l=4)                            # feed pipe drum -> shoulder

# ================================================================ LEFT ARM (+x): 3-finger brass crusher claw
SH = (27.0, 44.0, 0.0); EL = (35.0, 35.0, 2.0); WR = (42.0, 28.0, -9.0)
put(obox(SH, EL, 4.4, 4.4, .5), IRON, l=1)                                                         # upper arm
put(obox(SH, EL, 5.0, 5.0) & ~obox(SH, EL, 9, 9, -3.0) & ~obox(EL, SH, 9, 9, -3.0), BROWN, l=2)
put(cylx(EL[1], EL[2], 4.4, 30, 40, 1), IROND, l=2)                                                  # elbow axle
g, t = gear(EL, 'x', 4.2, 5.8, 9, 39.5, 42); put(g, BRASSD, l=4); put(t, BRASS, l=4)
put(cylx(EL[1], EL[2], 1.6, 39.5, 42.5, 1), IROND, l=5)
put(obox(EL, WR, 5.4, 5.6, .5), BRASS, l=2)                                                          # forearm armour
put(obox(EL, WR, 2.6, 6.2) & ~obox(EL, WR, 9, 9, -2.0) & ~obox(WR, EL, 9, 9, -2.0), BRASSD, l=3)
put(obox(EL, WR, 6.0, 6.2) & ~obox(WR, EL, 9, 9, -1.8) & ~box(36, 48, 21, 31, -15, -3, 1), IRON, l=3)                                    # wrist collar
put(box(36, 48, 21, 31, -15, -3, 1), BRASS, l=2)                                                     # palm block
put(box(37, 47, 30.5, 32, -14, -4, 1), BRASSD, l=3)
put(box(36, 48, 21, 24, -15.5, -2.5, 1), BROWN, l=3)
rivets([(x, y, -15.5) for x in (37.5, 39.5, 41.5, 43.5, 45.5, 47.5) for y in (26, 29)])
def finger(pts, hw):
    for i in range(len(pts) - 1):
        last = i == len(pts) - 2
        put(obox(pts[i], pts[i + 1], hw * (.7 if last else 1), hw * (.7 if last else 1), .7), IROND if last else BRASS, l=3)
for z0 in (-12.0, -5.0):                                                                            # two outer fingers
    finger([(47.5, 24, z0), (51.5, 18, z0 - 3), (51, 11, z0 - 6), (47, 7.5, z0 - 7)], 2.7)
finger([(36.5, 24, -8.5), (32.5, 18, -11.5), (33, 11, -14.5), (37, 7.5, -15.5)], 2.7)              # inner thumb
# ================================================================ BACK: boiler pack, exhaust stacks + smoke, copper pipes, back gear
put(box(0, 13, 40, 60, 13, 19), BRASS, l=2)                                                          # boiler pack
put(box(0, 13.6, 40, 42.5, 12, 19.6) | box(0, 13.6, 57.5, 60, 12, 19.6), IRON, l=3)                  # pack frame bands
put(box(0, 11, 43, 57, 18.5, 20), BRASSD, l=3)
put(box(0, 9.5, 44.5, 55.5, 18.5, 20), BROWN, l=3)
put(pipe([(-8, 50, 20.5), (8, 50, 20.5)], 1.0), COPPER, l=4)
rivets([(s * x, y, 19.5) for s in (1, -1) for x in (11.5,) for y in (44, 47, 50, 53, 56)])
for s in (1, -1):
    sx = 7.0 * s
    put(cyly(sx, 15, 3.2, 54, 77), IRON, l=3)                                                        # stack
    put(cyly(sx, 15, 4.0, 63, 65) | cyly(sx, 15, 4.0, 70, 72), IRONL, l=4)                           # collars
    put(cyly(sx, 15, 4.4, 75, 78), IROND, l=4)                                                        # flared crown
    put(cyly(sx, 15, 2.2, 76, 78.5), BLACK, l=4)
    for (dx, y, dz, r, c) in ((0, 79.5, .5, 3.2, SMOKED), (-.4 * s, 82.3, 2.5, 2.8, SMOKE), (-.8 * s, 84.3, 4.5, 1.8, SMOKE)):
        put(sph((sx + dx, y, 15 + dz), r), c, l=5)
    put(pipe([(s * 16.0, 27, 15.5), (s * 16.0, 37, 15.5), (s * 8.0, 37, 15.5), (s * 8.0, 40.5, 15.5)], 1.3), COPPER, l=4)
    put(pipe([(s * 13.5, 57, 19.5), (s * 13.5, 66, 15.0), (s * 10.0, 66, 15.0)], 1.1), COPPER, l=4)  # pack -> stacks
g, t = gear((0, 32, 15), 'z', 5.0, 6.6, 10, 14, 16.5); put(g, BRASS, l=4); put(t, BRASSD, l=4)
put(cylz(0, 32, 1.8, 14.5, 17.5), IROND, l=5)
for s in (1, -1):
    put(pipe([(s * 15.6, 30, 15.5), (s * 15.6, 61, 15.5)], 1.2), COPPER, l=4)                      # side risers
    put(pipe([(s * 2.5, 25.8, 15.5), (s * 10.5, 25.8, 15.5), (s * 10.5, 31, 15.5)], 1.1), COPPER, l=4)
    for y in (34, 46, 56): put(cylx(y, 15.5, 1.8, 14.5, 16.8, s), BRASSD, l=5)                       # pipe clamps
rivets([(x, 61, -10.5) for x in (-8.5, -5.5, -2.5, 2.5, 5.5, 8.5)])                                # hood rivets
Y = Y0; YOFF[0] = 0.0

# ================================================================ keep only bricks 26-connected to the body (nothing floats)
solid = kind > 0
reach = np.zeros(n, bool); reach[tuple(np.round(np.array((0.5, 45, .5)) - lo - .5).astype(int))] = True
cnt = 1
while True:
    r = reach
    for ax in range(3): r = r | np.roll(r, 1, ax) | np.roll(r, -1, ax)
    r &= solid; c2 = int(r.sum())
    if c2 == cnt: break
    reach = r; cnt = c2
drop = solid & ~reach; kind[drop] = 0
print('DROPPED', int(drop.sum()), 'floating bricks')

# ================================================================ seams + light grading + palette snap
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s_ in (1, -1):
        np_ = np.roll(pid, s_, axis=ax); nl = np.roll(lvl, s_, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & (nl > lvl) & (np.roll(kind, s_, axis=ax) == 1)
col[dark & (kind == 1)] *= .62
col *= np.clip(.9 + .15 * (Y / 66.0), .9, 1.06)[..., None]
col = np.clip(col, 0, 1)
PAL = np.array([BRASSL, BRASS, BRASSD, BRASSDD, COPPER, COPPERD, BROWN, BROWND, IRONL, IRON, IROND, HAZ, BLACK, SMOKE, SMOKED, STEAM])
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
body = build('WarMech', kind == 1, True)
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
    for nm, c, e, loc in (('EyeLight', (1.0, .15, .08), 900, (0, 50, -20)), ('FurnaceLight', (1.0, .45, .1), 700, (0, 33, -20))):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.color = c; L.data.shadow_soft_size = 1.0; L.location = B(*loc)
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
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.42, .42, .44, 1)
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
    for nm, az, el, os_, tg in (('ortho_front', 0, 0, 112, (0, 40, 0)), ('ortho_side', 90, 0, 112, (0, 40, -5)),
                                ('ortho_back', 180, 0, 112, (0, 40, 0)), ('ortho_top', 0, 89.9, 112, (0, 40, -5))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=os_)
    for nm, a in (('rest_34', ((-2, 37, -6), 175, -38, 12)), ('rest_side', ((0, 39, -6), 170, 90, 6)), ('rest_front', ((0, 39, -4), 165, 0, 8)),
                  ('rest_back', ((0, 40, 4), 165, 180, 10)),
                  ('face', ((0, 45, -15), 80, 0, 4)), ('headside', ((-39, 29, -16), 75, -55, 12)), ('head34', ((44, 27, -12), 85, 40, 10)),
                  ('footfront', ((-20, 9, -8), 62, 0, 6)), ('footside', ((-20, 13, -2), 72, -90, 4))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): bones in brick coords, L = +x (claw), R = -x (gatling)
SOL = kind > 0
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('torso', 'root', (0, 25, 0), (0, 33.5, 0)), ('cabin', 'torso', (0, 33.5, 0), (0, 72, 0))]
OVR = [(SOL, 'cabin'), (SOL & (Y < 33.5) & (AX < 14.5) & (Z < 12), 'torso')]
for s, sd in ((1, 'L'), (-1, 'R')):
    H = (14.0 * s, 33.0, 2.0); K = (22.0 * s, 20.0, -8.0); A = (21.0 * s, 7.0, 3.0)
    LEG = [('thigh' + sd, 'torso', H, K), ('shin' + sd, 'thigh' + sd, K, A), ('foot' + sd, 'shin' + sd, A, (21.0 * s, 2, -14))]
    RIG += LEG
    leg = SOL & (X * s > 8.5) & (X * s < 31.5) & (Y < 38) & (Z < 12) & ~((Y > 33.5) & (X * s < 15))
    leg |= SOL & ((Y - 33) ** 2 + (Z - 2) ** 2 < 6.6 ** 2) & (X * s > 19.5) & (X * s < 23)              # whole hip gear
    OVR += brick_rig.limb(X, Y, Z, leg & (Y >= 11.5), LEG[:2]) + [(SOL & (X * s > 8.5) & (X * s < 31.5) & (Y < 11.5), 'foot' + sd)]
# gatling (-x): upper arm, drum = lower arm, barrel cluster (spins about its own bone)
SH = (-35.0 + 8, 52.0, 0.0); EB = (-35.0, 43.0, 1.0); GC = (-39.0, 37.0)
RIG += [('gatUpper', 'cabin', SH, EB), ('gatLower', 'gatUpper', EB, (GC[0], GC[1], -6)), ('gatBarrel', 'gatLower', (GC[0], GC[1], -10), (GC[0], GC[1], -40))]
gup = SOL & obox(SH, EB, 5.2, 5.2, 1.6) & (Y < 48)
garm = SOL & ((X < -29.4) | ((X < -28) & (Y > 28.6))) & (Y > 26.5) & (Y < 47.5) & (Z > -11.5) & (Z < 15.5) & ~gup
OVR += [(gup, 'gatUpper'), (garm, 'gatLower'), (SOL & (X < -29.4) & (Y > 26.5) & (Y < 47.5) & (Z <= -11.5), 'gatBarrel')]
# crusher claw (+x): upper, forearm + palm, two jaws (outer fingers / thumb)
SH = (27.0, 52.0, 0.0); EL = (35.0, 43.0, 2.0); WR = (42.0, 36.0, -9.0)
RIG += [('clawUpper', 'cabin', SH, EL), ('clawLower', 'clawUpper', EL, WR),
        ('clawJawA', 'clawLower', (47.5, 30, -8.5), (47, 15.5, -15)), ('clawJawB', 'clawLower', (36.5, 30, -8.5), (37, 15.5, -15.5))]
cup = SOL & obox(SH, EL, 5.2, 5.2, 1.0) & (Y < 48)
OVR += [(cup, 'clawUpper'), (SOL & (X > 29.6) & (Y > 29.5) & ((Y < 47) | ((X > 39.6) & (Y < 49.5))) & (Z < 9) & ~cup, 'clawLower'),
        (SOL & (X > 45.4) & (Y <= 29.5) & (Z < -1), 'clawJawA'), (SOL & (X > 29.6) & (X < 40) & (Y <= 29.5) & (Z < -4), 'clawJawB')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'thighL': (25, 0, 0), 'shinL': (-30, 0, 0), 'cabin': (0, 15, 0), 'gatLower': (-20, 0, 0), 'gatBarrel': (0, 30, 0),
                       'clawLower': (-25, 0, 0), 'clawJawA': (0, 0, -25), 'clawJawB': (0, 0, 25)},
                 render='render' in argv)
print('BL_OK')
