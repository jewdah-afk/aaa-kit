# Living Armor (stud-voxel brick pipeline): a giant cursed suit of armour, empty inside, purple ghost-fire leaking from
# every joint. Reference = LivingArmor/concept_sheet.jpg. Static model.
# GLOW: subtle
# Run: powershell -File stud-voxel-creatures/scripts/run_brick.ps1 living_armor_brick.py views
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game). Character's right = -x.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'LivingArmor'

lo = np.array((-80.0, -0.5, -44.0)); hi = np.array((56.0, 115.5, 40.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
STEEL = hx('55535f'); STEELL = hx('6d6b78'); STEELD = hx('3e3d47'); STEELX = hx('2c2b33')
GOLD = hx('d9a531'); GOLDL = hx('f2c650'); GOLDD = hx('95691a')
CAPE = hx('6a3486'); CAPEL = hx('8a4aa8'); CAPED = hx('4a2262')
BLADE = hx('7d7b88'); BLACK = hx('0c0d10'); GRIP = hx('2a1c22')
GLOW = {2: hx('9a2cf0'), 3: hx('c86cff'), 4: hx('f0d0ff'), 5: hx('b030ff')}   # ghost-fire edge / core / white-hot

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def sd_ellS(c, r):                                   # mirrored in x (c[0] = |x| centre)
    px, py, pz = (AX - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def boxa(x0, x1, y0, y1, z0, z1):                   # absolute x
    return (X > x0) & (X < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb, xs=X):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((xs - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((xs - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii, xs=X):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1], xs)
    return m
def col4(x, z, hx_, hz_, xs=AX):                     # rounded-square column section at (|x|, z)
    return ((xs - x) / hx_) ** 4 + ((Z - z) / hz_) ** 4 < 1

rng = np.random.RandomState(7)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
def shell(m, t=1.2):                                 # outer surface layer of a mask (for trims / cracks)
    inner = m.copy()
    for ax in range(3):
        for s in (1, -1): inner &= np.roll(m, s, axis=ax)
    return m & ~inner

# ================================================================ cape (behind) - painted first, armour wins over it
# a curved shell round the back half of the body: hangs from the shoulders, wraps forward beside the legs, flares out,
# long shredded tatters at the bottom. Thick (3 bricks) so it reads from the side.
def sup(c, r, pw=4, xs=None):                        # rounded box (superellipse); xs None = current X
    xs = X if xs is None else xs
    return ((xs - c[0]) / r[0]) ** pw + ((Y - c[1]) / r[1]) ** pw + ((Z - c[2]) / r[2]) ** pw < 1
def cap(a, b, ra, rb, xs=None):
    xs = X if xs is None else xs
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((xs - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((xs - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii, xs=None):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1], xs)
    return m
# upper-body twist toward the sword side: body-local coords rotate with height (0 at the hips -> 8 deg at the chest)
XW, ZW = X, Z
TH = np.radians(8.0) * np.clip((Y - 52.0) / 20.0, 0, 1)
def twist(on):
    global X, Z, AX
    if on: X = XW * np.cos(TH) - ZW * np.sin(TH); Z = XW * np.sin(TH) + ZW * np.cos(TH)
    else: X, Z = XW, ZW
    AX = np.abs(X)
def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def band(a, b, r):                                   # flat cylinder segment a->b (no round caps): trim rings
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = ((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return (t >= 0) & (t <= 1) & (d <= r)
CY = 82.0
yy = np.clip(CY - Y, 0, None)
crx = 27.0 + .21 * yy; crz = 16.0 + .14 * yy                                   # flare out and back going down
ang = np.arctan2(X, Z)                                                           # 0 = straight back
fold = np.sin(ang * 9.0)
rn = np.sqrt((X / crx) ** 2 + ((Z - 1.0) / crz) ** 2)
cth = np.abs(rn - 1) * np.minimum(crx, crz)
hem = np.zeros(n)
abin = np.floor((ang + np.pi) / .085).astype(int)
tab = rng.choice([1, 2, 4, 6, 9, 12, 15, 19, 23], size=abin.max() + 2)
hem = tab[abin] + 3.0 * (np.abs(ang) > 1.1)
cape = (Y < CY) & (Y > hem) & (cth < 1.5 + .4 * fold) & (Z > 3.0) & (np.abs(ang) < 1.62)
put(cape, CAPE, p=newid(), l=0)
put(cape & (fold > .5), CAPEL, p=0)
put(cape & (fold < -.6), CAPED, p=0)
put(cape & (Y < hem + 2.5), CAPED, p=0)
# mantle: short shoulder cape over the top with a deep scalloped / torn edge
mrx = 29.5 + .1 * yy; mrz = 18.5 + .08 * yy
mrn = np.sqrt((X / mrx) ** 2 + ((Z - 1.0) / mrz) ** 2)
mhem = 60 + 5 * np.abs(np.sin(ang * 5.5)) + tab[abin] * .35
mant = (Y < CY + 2) & (Y > mhem) & (np.abs(mrn - 1) * np.minimum(mrx, mrz) < 1.3) & (Z > 5) & (np.abs(ang) < 1.35)
put(mant, CAPEL, p=newid(), l=1)
put(mant & (Y < mhem + 2), CAPE, p=0)
put((sd_ell((0, 82, 9), (22, 5.5, 9)) < 0) & (Z > 4), CAPE, p=newid(), l=1)   # fabric bunched under the helmet

# ================================================================ legs: wide stance, knees slightly bent
LEGS = {}
for sx in (1, -1):
    hip, knee, ank = {1: ((17.0, 51.0, 0.0), (19.5, 28.0, -1.5), (20.0, 10.5, 1.0)),                 # planted, straight
                      -1: ((-17.0, 51.0, 0.0), (-25.0, 28.0, -6.0), (-27.5, 10.5, -3.0))}[sx]       # stepped out, bent
    LEGS[sx] = (hip, knee, ank)
    put(chain([hip, knee], [10.2, 9.0]), STEEL, p=newid(), l=1)                                  # cuisse
    put(chain([lerp(hip, knee, .1), lerp(hip, knee, .75)], [9.2, 8.2]) & (Z < -6), STEELL, p=newid(), l=2)   # front thigh plate
    put(band(lerp(hip, knee, .52), lerp(hip, knee, .62), 10.1), GOLD, st=False, p=newid(), l=3)
    put(chain([knee, ank], [8.4, 7.8]), STEEL, p=newid(), l=1)                                   # greave
    put(chain([lerp(knee, ank, .15), lerp(knee, ank, .85)], [6.4, 5.8]) & (Z < -5.2), STEELL, p=newid(), l=2)   # shin plate
    kc = (knee[0], knee[1], knee[2] - 1.5)
    kd = sd_ell(kc, (10.0, 6.4, 9.6))                                                             # knee cop
    put(kd < 0, STEELL, p=newid(), l=4)
    put((kd < 0) & (Y < kc[1] - 3.2), GOLD, st=False)
    put(sd_ell((kc[0], kc[1] - .5, kc[2] - 9.4), (2.6, 2.6, 1.5)) < 0, GOLDL, st=False)            # knee boss
    put(sd_ell((ank[0], 11.0, ank[2]), (9.8, 2.0, 10.2)) < 0, GOLD, st=False, p=newid(), l=3)      # ankle cuff
    # heavy flared sabaton: 3 stepped rounded lames + toe cap, gold sole rim
    put(sup((ank[0], 3.0, ank[2] - 5.0), (12.0, 3.2, 16.0), 4), STEELD, p=newid(), l=0)
    put(sup((ank[0], 6.0, ank[2] - 3.5), (10.8, 2.6, 12.5), 4), STEEL, p=newid(), l=1)
    put(sup((ank[0], 8.5, ank[2] - 1.5), (9.4, 2.2, 9.6), 4), STEEL, p=newid(), l=2)
    put(sd_ell((ank[0], 3.5, ank[2] - 17.0), (9.4, 4.0, 5.2)) < 0, STEELL, p=newid(), l=3)               # toe cap
    put(sup((ank[0], .6, ank[2] - 5.0), (12.6, .9, 16.6), 4), GOLD, st=False, p=newid(), l=4)          # sole rim
    put(sup((ank[0], 4.6, ank[2] - 5.0), (12.2, .6, 16.2), 4) & (Z < ank[2] - 12), GOLDD, st=False)
for i, (yc, g) in enumerate(((49.0, 0.0), (44.5, 1.0))):                                          # tassets over the hips
    tm = (sd_ell((0, yc, 0), (26.5 + g, 3.6, 16.5 + g)) < 0) & (AX > 9.5)
    put(tm, STEEL if i else STEELL, p=newid(), l=4 + i)
    put(tm & (Y < yc - 1.8), GOLD, st=False)

twist(True)
# ================================================================ torso: deep convex breastplate, tapered waist
d = sd_ell((0, 73, 0), (22.5, 9.5, 17.5))                                      # chest (depth 0.8 of width)
d = smin(d, sd_ell((0, 78, 1), (24, 5.0, 16.5)), 4)                            # upper chest to the shoulders
d = smin(d, sd_ell((0, 63, 0), (13.5, 6, 12.5)), 4)                            # narrow waist
d = smin(d, sd_ell((0, 53, 0), (21, 6, 14.5)), 4)                              # hips
torso = d < 0
put(torso, STEEL, p=newid(), l=2)
for i, yc in enumerate((58.5, 61.5, 64.5)):                                     # abdomen lames: stepped rings
    put(torso & (sd_ell((0, yc, 0), (15.5 - i * .4, 1.6, 13.6)) < 0), STEELL if i % 2 else STEEL, p=newid(), l=3 + (i % 2))
put(torso & (Y > 66) & (Y < 68) & (d > -2), GOLD, st=False, p=newid(), l=4)
CH = newid()
for sx in (1, -1):                                                              # convex pec plates
    pc = sd_ell((8.5 * sx, 73.5, -11.5), (9.8, 7.0, 8.0))
    put(pc < 0, STEELL, p=CH, l=4)
    put((pc < 0) & (Y < 67.5), GOLD, st=False)
put(shell(torso | (kind == 1)) & (Z < -6) & (np.abs(AX - (Y - 61.0) * 1.05) < .95) & (Y > 63) & (Y < 82), GOLD, st=False)   # gold V edging
put(torso & (AX < 1.5) & (Z < -10) & (Y > 67), STEELL, p=newid(), l=5)        # centre ridge
belt = (sd_ell((0, 56.5, 0), (19.0, 2.8, 15.2)) < 0) & (Y > 54) & (Y < 59)
put(belt, GOLD, st=False, p=newid(), l=5)
put(belt & (np.abs(Y - 56.5) < .6), GOLDD, st=False)
put(sup((0, 56.5, -14.8), (3.8, 3.6, 1.6), 4), GOLDL, st=False)             # buckle
put(sup((0, 56.5, -16.0), (1.6, 1.4, .8), 4), BLACK, st=False)
put(torso & (Z > 12) & (AX < 1.5) & (Y > 64), STEELD, st=False)
for pts in (((-14, 76, -13), (-11, 73, -15.5), (-12, 70, -15.5), (-8, 67, -14)), ((9, 79, -13), (13, 76, -14.5), (12, 73, -15.5))):
    put(chain(pts, [.8] * len(pts)) & (kind == 1) & (d > -1.8), BLACK, st=False)

# ================================================================ loincloth (front): dark purple drape, torn V hem
lw = 9.0 + .06 * np.clip(54 - Y, 0, None)
lhem = np.zeros(n)
for xi in range(-14, 15):
    lhem[(X >= xi - .5) & (X < xi + .5)] = 11 + abs(xi) * 1.4 + rng.choice([0, 0, 2, 4, 7])
loin = (np.abs(X) < lw) & (Y < 54.5) & (Y > lhem) & (Z > -17.2) & (Z < -14.6)
put(loin, CAPED, p=newid(), l=6)
put(loin & (np.sin(X * .7) > .5), CAPE, p=0)
put(loin & (Y < lhem + 2.5), CAPED * .7, p=0)

# ================================================================ arms: angled out, bent elbows, bulky gauntlets
ARMS = {1: ((31, 77, 0), (38.5, 58, 1.0), (40.0, 47.5, -7.5), (40.5, 42.0, -12.0)),          # left: fist clenched forward
        -1: ((-31, 77, 0), (-42.0, 58.5, 4.0), (-44.0, 57.0, -8.0), (-45.0, 56.5, -16.5))}   # right: reaches out to the hilt
HAND = np.zeros(n, bool)
for sx, (sh, el, wr, fc) in ARMS.items():
    put(chain([sh, el], [7.2, 6.8]), STEEL, p=newid(), l=1)
    put(band(lerp(sh, el, .55), lerp(sh, el, .64), 7.6), STEELD, p=newid(), l=2)
    ed = sd_ell(el, (8.4, 6.2, 8.4))
    put(ed < 0, STEELL, p=newid(), l=3)
    put((ed < 0) & (Y < el[1] - 3.4), GOLD, st=False)
    put(chain([el, wr], [6.6, 7.2]), STEEL, p=newid(), l=1)
    put(chain([lerp(el, wr, .45), lerp(el, wr, 1.08)], [8.0, 9.0]), STEELL, p=newid(), l=2)     # flared gauntlet cuff
    put(band(lerp(el, wr, .42), lerp(el, wr, .55), 8.6), GOLD, st=False)
    put(band(lerp(el, wr, .96), lerp(el, wr, 1.08), 9.0), GOLD, st=False)
    FI = newid()                                                                                 # big clenched fist
    put(sup(fc, (7.4, 6.4, 7.8), 4), STEELD, p=FI, l=2)
    if sx == -1: HAND |= sup(fc, (8.6, 7.6, 9.0), 4)
    put(sup((fc[0], fc[1] - 2.0, fc[2] - 1.0), (7.8, 3.0, 7.6), 4), STEEL, p=newid(), l=3)  # finger roll
    for kx in (-4.5, -1.5, 1.5, 4.5):
        put(sup((fc[0] + kx * sx * .9, fc[1] - 1.5, fc[2] - 8.0), (1.2, 1.2, 1.0), 2), GOLD, st=False)   # knuckle studs
    put(sup((fc[0] - 6.5 * sx, fc[1] + .5, fc[2] - 4.0), (2.2, 3.4, 2.6), 4), STEEL, p=newid(), l=3)   # thumb

# ================================================================ pauldrons: huge rounded stepped plates bulging forward and back
for sx in (1, -1):
    c1 = (27.5 * sx, 83.5, 0.0); c2 = (30.5 * sx, 78.5, .5); c3 = (33.0 * sx, 74.0, 1.0)
    p1 = sd_ell(c1, (12.5, 7.0, 17.0)) < 0
    p2 = (sd_ell(c2, (12.5, 5.0, 18.0)) < 0) & (Y < 81.5)
    p3 = (sd_ell(c3, (11.5, 4.6, 17.2)) < 0) & (Y < 77)
    for m_, l_, c_ in ((p3, 3, STEEL), (p2, 4, STEEL), (p1, 5, STEELL)):
        put(m_ & (X * sx > 13.5), c_, p=newid(), l=l_)
    for m_, cc in ((p1, c1), (p2, c2), (p3, c3)):                                            # gold rim on each lame's lower edge
        put(m_ & (X * sx > 13.5) & (Y < cc[1] - 2.6) & (kind == 1), GOLD, st=False)
    put(shell(p1) & (X * sx > 13.5) & (np.abs(X - c1[0]) < 1.3) & (Y > 84), GOLD, st=False)   # gold ridge front to back
    for zr in (-12, -6, 0, 6, 12):
        put(sup((c1[0] + 9.5 * sx, 79.5, zr), (1.0, .9, 1.0), 2), GOLDL, st=False)
    put(chain([(26 * sx, 89, -10), (23.5 * sx, 86.5, -13.5), (26 * sx, 83, -16.0)], [.8, .8, .8]) & (kind == 1), BLACK, st=False)

# ================================================================ helmet: big horned great helm, pointed-arch T-visor, gold crest
HY = 83.0
hm = ((AX / 11.0) ** 4 + ((Z + .5) / 12.0) ** 4 < 1) & (Y > HY) & (Y < 98)
hm |= (sd_ell((0, 98, -.5), (11.0, 6.5, 12.0)) < 0) & (Y >= 98)
put(hm, STEEL, p=newid(), l=6)
put(hm & (Z < -8) & (Y > 85), STEELL, p=newid(), l=7)
put(((AX / 12.0) ** 4 + ((Z + .5) / 13.0) ** 4 < 1) & (Y > HY - 1.5) & (Y < HY + 2.5), GOLD, st=False, p=newid(), l=8)   # neck rim
put(shell(hm) & (AX < 2.2) & (Y > 96) & (Z < 10), GOLD, st=False)                                   # crest band
put(shell(hm) & (AX < 2.2) & (Y > 96.5) & (Z < -11), GOLD, st=False)
for zr in (-8, -3, 2, 7):
    put(shell(hm) & (AX < 1.0) & (np.abs(Z - zr) < .6) & (Y > 103), GOLDL, st=False)
put(shell(hm) & (Y > 97) & (Y < 99) & (Z < -10) & (AX < 10.5), GOLD, st=False)                     # brow rim
# pointed-arch visor: wide eye band tapering to a point at the chin + T stem
VIS = ((AX < 9.0) & (Y > 90.5) & (Y < 96.5)) | ((AX < 9.0 * (Y - 84.5) / 6.0) & (Y > 84.5) & (Y <= 90.5)) | ((AX < 2.6) & (Y > 84.5) & (Y < 96.5))
kind[VIS & (Z < -10)] = 0
put(VIS & (Z > -10) & (Z < -9), BLACK, st=False)
for sx in (1, -1):
    m_e = (((X * sx > 2.5) & (X * sx < 6.5) & (Y > 92.6) & (Y < 93.4)) | ((X * sx > 4.5) & (X * sx < 8.5) & (Y > 93.6) & (Y < 94.4))) & (Z > -10) & (Z < -9)
    put(m_e, GLOW[5], k=5, st=False)                                          # eyes: ONE flat glow colour
for (rx, ry) in ((10.0, 88), (10.0, 95), (6.0, 100.5), (10.0, 100)):
    put(box(rx - .6, rx + .6, ry - .6, ry + .6, -13.5, -10.5) & (Y > 84), GOLDL, st=False)
put(chain([(-6, 104, -8.5), (-8, 101, -11.3), (-7, 98.5, -12.0)], [.75, .75, .75]) & (kind == 1), BLACK, st=False)
for sx in (1, -1):                                                                                   # chunky gold horns curving up
    hpts = [(10 * sx, 96, 0), (14 * sx, 97, 0), (17 * sx, 100, -.5), (18 * sx, 104.5, -1), (16.5 * sx, 109, -1.5), (14 * sx, 112.5, -1.5)]
    horn = chain(hpts, [3.9, 3.6, 3.2, 2.6, 1.9, 1.1])
    put(horn, GOLD, st=False, p=newid(), l=8)
    put(horn & (np.round(Y) % 4 == 0), GOLDD, st=False)                                              # stepped ring bands
    put(chain(hpts[:2], [4.3, 4.0]), GOLDD, st=False)

# ================================================================ ghost-fire: wavy multi-tip purple flames at every joint
def flame(b, h, w, ph=0.0, sway=1.0):
    sY = (Y - b[1]) / h
    on = (sY >= 0) & (sY <= 1)
    cxx = b[0] + sway * np.sin(sY * 5 + ph) * (.4 + sY); czz = b[2] + .5 * sway * np.cos(sY * 4 + ph)
    r = w * (1 - sY) ** .85 + .45
    m = on & (((X - cxx) / r) ** 2 + ((Z - czz) / (r * .85)) ** 2 < 1)
    core = m & (((X - cxx) / (r * .5)) ** 2 + ((Z - czz) / (r * .45)) ** 2 < 1) & (sY < .6)
    put(m & (kind != 1), GLOW[2], k=2, st=False)
    put(core & (kind != 1), GLOW[3], k=3, st=False)
def tuft(b, h, w, seed):                                    # one tall tongue + 3-4 shorter licks round it
    r_ = np.random.RandomState(seed)
    flame(b, h, w, r_.rand() * 6)
    for k in range(4):
        an = k * 1.57 + r_.rand()
        flame((b[0] + w * .9 * np.cos(an), b[1], b[2] + w * .9 * np.sin(an)), h * r_.uniform(.45, .75), w * .6, r_.rand() * 6, .7)
def ring(c, rx, rz, y0, nt, hmin, hmax, w, skip=None, seed=0):
    r_ = np.random.RandomState(seed)
    for k in range(nt):
        an = 2 * np.pi * (k + r_.rand() * .5) / nt
        if skip and skip(an): continue
        flame((c[0] + rx * np.sin(an), y0, c[1] - rz * np.cos(an)), r_.uniform(hmin, hmax), w * r_.uniform(.8, 1.2), r_.rand() * 6, .8)
def seam(m, y0, y1):
    put(shell(m) & (Y > y0) & (Y < y1) & (kind == 1), GLOW[2], k=2, st=False)

put((AX ** 2 + Z ** 2 < 9.5 ** 2) & (Y > 79) & (Y < 84) & (kind == 0), STEELX, st=False)          # dark neck opening
ring((0, .5), 13.0, 14.0, 80.5, 24, 6, 12, 2.4, skip=lambda a: abs(np.sin(a)) < .28 and np.cos(a) > 0, seed=1)
ring((0, .5), 11.0, 12.0, 80.5, 8, 4, 7, 1.8, skip=lambda a: np.cos(a) > 0, seed=2)
for sx in (1, -1):
    tuft((19.5 * sx, 87.5, -4), 12, 2.6, 10 + sx)                                                   # shoulders
    tuft((21 * sx, 87.5, 6), 10, 2.3, 12 + sx)
    tuft((37 * sx, 86.5, 0), 11, 2.5, 14 + sx)
    sh, el, wr, fc = ARMS[sx]
    seam(chain([el, wr], [7.4, 7.8]), el[1] - 6.8, el[1] - 5.2)                                   # elbow gap
    tuft((el[0] + 7.5 * sx, el[1] - 5, el[2]), 9, 2.2, 20 + sx)
    tuft((el[0] + 1 * sx, el[1] - 5, el[2] + 7.5), 7, 1.8, 22 + sx)
    hip, knee, ank = LEGS[sx]
    seam(chain([knee, ank], [8.8, 8.2]), knee[1] - 7.2, knee[1] - 5.8)                             # knee gap
    ring((knee[0], knee[2]), 10.0, 10.0, knee[1] - 6.0, 12, 4, 9, 2.0, seed=30 + sx)
seam(torso, 59.6, 61.4)                                                                              # waist gap
ring((0, 0), 15.5, 13.5, 60.5, 20, 4, 9, 2.1, skip=lambda a: abs(np.sin(a)) < .22 and np.cos(a) > 0, seed=9)
twist(False)

# ================================================================ greatsword: right hand at the waist, angled down and forward
FC = np.array(ARMS[-1][3]); T = np.array((-58.0, 1.0, -26.0))
a_ = (T - FC) / np.linalg.norm(T - FC)
G = FC + a_ * 10.2; P = FC - a_ * 9.0
L = np.linalg.norm(T - G)
w_ = np.cross(a_, (0, 0, 1.0)); w_ /= np.linalg.norm(w_); v_ = np.cross(w_, a_)
before = kind > 0
DX, DY, DZ = X - G[0], Y - G[1], Z - G[2]
tt = DX * a_[0] + DY * a_[1] + DZ * a_[2]; uu = DX * w_[0] + DY * w_[1] + DZ * w_[2]; vv = DX * v_[0] + DY * v_[1] + DZ * v_[2]
s = tt / L
hw = np.where(s < .8, 7.2, 7.2 * (1 - (s - .8) / .2)) + .3
saw = (np.floor(tt / 3.0) % 2 == 0) * 1.6
blade = (tt > 0) & (tt < L + .5) & (np.abs(uu) < hw + saw * (s < .82)) & (np.abs(vv) < 1.4)
put(blade, BLADE, st=False, p=newid(), l=3)
put(blade & (np.abs(uu) > hw - 1.0), STEEL, st=False)
put(blade & (np.abs(uu) > hw + .3), STEELD, st=False)
kt = np.arange(0, L + 4, 3.5); ku = np.clip(np.cumsum(rng.choice([-1.6, -1.0, 1.0, 1.6], size=len(kt))), -2.5, 2.5); ku[0] = 0
zig = np.interp(tt, kt, ku)                                                       # one continuous jagged crack
put(blade & (np.abs(uu - zig) < 1.0) & (tt > 1.5) & (s < .9), GLOW[2], k=2, st=False)
put(blade & (np.abs(uu - zig) < .55) & (tt > 2.5) & (s < .86), GLOW[3], k=3, st=False)
guard = (np.abs(tt + .5) < 2.6) & (np.abs(uu) < 13) & (np.abs(vv) < 2.4)
put(guard, GOLD, st=False, p=newid(), l=5)
put(guard & (np.abs(tt + .5) > 1.9), GOLDD, st=False)
put((np.abs(tt + .5) < 3.4) & (np.abs(uu) > 10.5) & (np.abs(uu) < 13.6) & (np.abs(vv) < 2.7), GOLDL, st=False)   # flared ends
put((np.abs(tt + .5) < 3.4) & (np.abs(uu) < 3.4) & (np.abs(vv) < 3.2) & (np.abs(vv) > 1.8), GOLDL, st=False)
put((np.abs(tt + .5) < 2.2) & (np.abs(uu) < 2.2) & (np.abs(vv) > 1.6) & (np.abs(vv) < 3.5), GLOW[5], k=5, st=False)  # gem
grip = (tt < 0) & (tt > -np.linalg.norm(P - G)) & (uu ** 2 + vv ** 2 < 2.1 ** 2)
put(grip & (kind == 0), GRIP, st=False)
put(sd_ell(tuple(P), (2.8, 2.8, 2.8)) < 0, GOLD, st=False)

SWORD = blade | guard | grip | (sd_ell(tuple(P), (2.8, 2.8, 2.8)) < 0) | ((np.abs(tt + .5) < 3.4) & (np.abs(uu) < 13.6) & (np.abs(vv) < 3.5) & (kind > 0))
other = before & ~HAND
dil = other.copy()
for _ in range(2):
    for ax in range(3): dil = dil | np.roll(dil, 1, axis=ax) | np.roll(dil, -1, axis=ax)
ov = int((SWORD & other).sum()); cl = int((blade & (tt > 3) & dil).sum()); gh = int((grip & ~HAND & other).sum())
PM = sd_ell(tuple(P), (2.8, 2.8, 2.8)) < 0
parts = ' '.join('%s=%d' % (k, int((m & other).sum())) for k, m in (('blade', blade), ('guard', guard), ('grip', grip), ('pommel', PM)))
occ = np.argwhere(SWORD & other); parts += ' at ' + str((lo + .5 + occ.mean(0)).round(1) if len(occ) else '-')
msg = 'SWORD_TEST overlap_non_hand=%d blade_within_2_of_armor=%d grip_outside_hand_touching=%d ' % (ov, cl, gh) + parts
open(os.path.join(OUT, 'sword_test.txt'), 'w').write(msg + '\n')
print(msg if ov == 0 and cl == 0 else 'Error ' + msg)

# ================================================================ keep only bricks 26-connected to the body
solid0 = kind > 0
reach = np.zeros(n, bool); reach[tuple(np.argwhere(solid0 & (Y < 3))[0])] = True
while True:
    g_ = reach.copy()
    for ax in range(3): g_ = g_ | np.roll(g_, 1, axis=ax) | np.roll(g_, -1, axis=ax)
    g_ &= solid0
    if g_.sum() == reach.sum(): break
    reach = g_
print('FLOAT_DROPPED', int(solid0.sum() - reach.sum()))
kind[~reach] = 0

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s_ in (1, -1):
        np_ = np.roll(pid, s_, axis=ax); nl = np.roll(lvl, s_, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.clip(.8 + .25 * (Y / 95.0), .8, 1.05)[..., None]
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('7a7886', '615f6c', '4c4a56', '393842', '25242b', '0c0d10',     # steel light..seam, black
                                 'f2c650', 'd29e2c', '95691a',                                  # gold
                                 '8c4cab', '6c3688', '4c2462', '30143e',                        # cape purples
                                 '2a1c22')])                                                    # grip leather
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
body = build('LivingArmor', kind == 1, True)
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
    for nm, pos, e in (('EyeL', (5.5, 93.5, -12), 60), ('EyeR', (-5.5, 93.5, -12), 60)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.color = (.72, .3, 1.0); L.data.shadow_soft_size = 1.0
        L.location = B(*pos)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .76, .8)
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
    for nm, az, el, os_, tg in (('ortho_front', 0, 0, 128, (-12, 55, 0)), ('ortho_side', 90, 0, 128, (0, 55, 0)),
                                ('ortho_back', 180, 0, 128, (-12, 55, 0)), ('ortho_top', 0, 89.9, 128, (-12, 50, 0))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=os_)
    for nm, a in (('rest_34', ((-14, 52, 0), 235, -35, 10)), ('rest_side', ((0, 54, 0), 290, 90, 5)), ('rest_front', ((-12, 54, 0), 290, 0, 6)),
                  ('rest_back', ((-8, 52, 0), 290, 160, 12)),
                  ('face', ((0, 95, -10), 74, 0, 4)), ('headside', ((0, 97, 0), 100, 90, 30)), ('head34', ((0, 96, -6), 82, -38, 10)),
                  ('footfront', ((22, 9, -8), 60, 0, 6)), ('footside', ((22, 9, -6), 66, 90, 4)), ('sword', ((-50, 24, -18), 105, -40, 8)), ('grip', ((-45, 55, -16), 50, -35, 14))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a not in ('render', 'views')]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): biped + cape; L = +x (character's left)
def tw(p):                                            # upper-body points are in twisted coords: back to world
    t = np.radians(8.0) * np.clip((p[1] - 52.0) / 20.0, 0, 1)
    return (p[0] * np.cos(t) + p[2] * np.sin(t), p[1], -p[0] * np.sin(t) + p[2] * np.cos(t))
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', (0, 50, 0), (0, 62, 0)), ('spine', 'hips', (0, 62, 0), (0, 72, 0)),
       ('chest', 'spine', (0, 72, 0), (0, 82, 0)), ('neck', 'chest', (0, 82, 0), (0, 86, 0)), ('head', 'neck', (0, 86, 0), (0, 104, 0))]
OVR = [(((Y > 83) & (AX < 12.5)) | (Y > 100), 'head'), (loin, 'hips')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    sh, el, wr, fc = (tw(q) for q in ARMS[sx]); hip, knee, ank = LEGS[sx]
    RIG += [('shoulder' + sd, 'chest', tw((12 * sx, 80, 0)), sh), ('upperarm' + sd, 'shoulder' + sd, sh, el), ('forearm' + sd, 'upperarm' + sd, el, wr),
            ('hand' + sd, 'forearm' + sd, wr, fc), ('thigh' + sd, 'hips', hip, knee), ('shin' + sd, 'thigh' + sd, knee, ank),
            ('foot' + sd, 'shin' + sd, ank, (ank[0], 2.0, ank[2] - 16))]
OVR += [(HAND, 'handR'), (SWORD, 'handR')]
CAPE_B = []
for sd, a in (('L', .75), ('R', -.75)):
    pts = [(np.clip(27 + .21 * (82 - y), 0, None) * np.sin(a), y, 1 + (16 + .14 * (82 - y)) * np.cos(a)) for y in (82, 56, 30, 4)]
    CAPE_B += [('cape%s%d' % (sd, i + 1), 'chest' if i == 0 else 'cape%s%d' % (sd, i), pts[i], pts[i + 1]) for i in range(3)]
RIG += CAPE_B
OVR += brick_rig.limb(X, Y, Z, cape & (kind == 1) & (col[..., 2] - col[..., 1] > .12), CAPE_B)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (0, 0, 25), 'upperarmL': (-40, 0, 0), 'forearmR': (30, 0, 0), 'thighL': (30, 0, 0), 'capeR2': (25, 0, 0)},
                 render='render' in argv)

print('BL_OK')
