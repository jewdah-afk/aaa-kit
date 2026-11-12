# Spectral Lich King (stud-voxel brick pipeline): a giant floating lich in a navy hooded robe, silver trims, cyan soul-fire.
# Reference = LichKing/concept_sheet.jpg. Static model.
# GLOW: subtle
# Run: powershell -File stud-voxel-creatures/scripts/run_brick.ps1 lich_king_brick.py views
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
# Orb hand on -x (viewer's left in the front view), staff on +x, as in the concept's front / 3/4 views.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'LichKing'

lo = np.array((-48.0, -0.5, -28.0)); hi = np.array((54.0, 114.5, 28.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
NAVYL = hx('3d4a94'); NAVY = hx('2b3373'); NAVYD = hx('1d2253'); NAVYX = hx('131634')
SILL = hx('d4d8e0'); SIL = hx('a9aeb9'); SILD = hx('7a7f8c')
BONEL = hx('f1e7cd'); BONE = hx('d8caa8'); BONED = hx('ab9a7c')
IRONL = hx('4c4c58'); IRON = hx('2d2d36'); BLACK = hx('0d0e14')
GLOW = {2: hx('12b4be'), 3: hx('3af0ea'), 4: hx('c8fffb')}   # teal edge / soul cyan / white-hot core

def put(m, rgb, k=1, st=True, p=None, l=None):
    col[m] = rgb; kind[m] = k; stud[m] = st
    if p is not None: pid[m] = p
    if l is not None: lvl[m] = l
def glow(m, k): kind[m] = k; col[m] = GLOW[k]

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def boxa(x0, x1, y0, y1, z0, z1):
    return (X > x0) & (X < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def shift(m, s, ax):                                  # m moved by s cells along ax (no wrap)
    r = np.roll(m, s, axis=ax); sl = [slice(None)] * 3
    sl[ax] = slice(0, s) if s > 0 else slice(s, None); r[tuple(sl)] = False; return r
def dil(m, k=1, axes=(0, 1, 2)):
    for _ in range(k):
        o = m.copy()
        for ax in axes: o |= shift(m, 1, ax) | shift(m, -1, ax)
        m = o
    return m
def ero(m, k=1, axes=(0, 1, 2)):
    for _ in range(k):
        o = m.copy()
        for ax in axes: o &= shift(m, 1, ax) & shift(m, -1, ax)
        m = o
    return m
def front_layer(): s = kind > 0; return ~s & shift(s, -1, 2)      # air cell with a solid cell right behind it
def back_layer(): s = kind > 0; return ~s & shift(s, 1, 2)
def front_face(m): return m & ~shift(kind > 0, 1, 2)              # cells of m whose front neighbour is air
def ci(v, a): return int(round(v - lo[a] - .5))

rng = np.random.RandomState(11)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ================================================================ robe skirt: cone flaring to the hem, vertical folds, torn hem -> soul-flame tongues
t = np.clip((63.0 - Y) / 40.0, 0, 1.3)
zc = 1.0 + 4.5 * t
w = 11.5 + 9.5 * np.clip(t, 0, 1) ** .85; dz = 9.5 + 9.0 * np.clip(t, 0, 1)
th = np.arctan2(Z - zc, X)
rn = np.sqrt((X / w) ** 2 + ((Z - zc) / dz) ** 2)
fold = np.cos(11 * th)
NS = 16
s_ = np.floor((th + np.pi) / (2 * np.pi) * NS).astype(int) % NS
u_ = (th + np.pi) / (2 * np.pi) * NS - np.floor((th + np.pi) / (2 * np.pi) * NS) - .5
ang = (np.arange(NS) + .5) / NS * 2 * np.pi - np.pi                  # strip centre angle
side = np.abs(np.cos(ang))                                            # 1 at the flanks, 0 front / back
nav_end = 24 + 7 * side + rng.choice([-3, -1, 0, 2, 3], NS)
tip = 4 + 15 * side + rng.choice([0, 1, 3, 5], NS)
front_s = np.abs(ang + np.pi / 2) < .3                                # strip under the front panel: long robe
nav_end[front_s] = 19; tip[front_s] = 5
NE = nav_end[s_] + np.where(u_ > .15, 2, 0) - np.where(u_ < -.25, 2, 0) * (~front_s[s_])   # stepped torn hem
TP = tip[s_]
f = np.clip((Y - TP) / (NE - TP), 0, 1)
skirt = (rn < 1 + .045 * fold * np.clip(t, 0, 1)) & (Y < 64)
tongue = (Y < NE) & (Y > TP) & (np.abs(u_) < .5 * f ** .7 + .03) & (rn < .3 + .7 * f ** .8)
core = (Y > 3) & (Y < 26) & ((X / (2.5 + .55 * (Y - 3))) ** 2 + ((Z - zc) / (2.5 + .6 * (Y - 3))) ** 2 < 1)   # soul-fire column the tongues converge into
skirt = skirt & ((Y >= NE) | tongue | core)
# torso: chest, narrow waist, neck into the hood
d = sd_ell((0, 66.5, 1.0), (10.5, 8.0, 9.5))
d = smin(d, sd_ell((0, 73.0, 1.5), (13.0, 4.5, 9.0)), 3)
d = smin(d, sd_ell((0, 79.0, 1.5), (8.0, 5.0, 8.0)), 3)
RB = newid()
body = skirt | (d < 0)
put(body, NAVY, p=RB, l=0)
put(skirt & (Y >= NE) & (fold > .45), NAVYL); put(skirt & (Y >= NE) & (fold < -.5), NAVYD)
put(skirt & (Y >= NE) & (Y < NE + 2.5), NAVYD)                                         # dark band where the robe burns away
tat = np.array([(i % 2 == 0) and not front_s[i] for i in range(NS)])[s_]            # every other strip: navy tatter point
flame = skirt & (Y < NE) & ~(tat & (Y > TP + 5) & (rn > .45))
put(skirt & (Y < NE) & ~flame, NAVYD)
glow(flame, 3)
glow(flame & ((np.abs(u_) > .5 * f ** .7 - .1) | (f > .85)) & (rn > .3), 2)
glow(flame & (((np.abs(u_) < .12) & (f > .25) & (f < .7)) | ((rn < .22) & (Y > 8) & (Y < 18))), 4)
for i in range(NS):                                                                      # cyan licks rising into the robe between tatters
    if i % 2 == 1 and not front_s[i]:
        put(skirt & (s_ == i) & (Y >= NE) & (Y < NE + 4 + (i % 2) * 2) & (np.abs(u_) < .17), GLOW[2], k=2, st=False)

# ================================================================ mantle (shoulder cape) with a silver lower edge
MA = newid()
dm = smin(sd_ell((0, 73.0, 2.0), (24.0, 4.2, 12.5)), sd_ell((0, 70.5, 2.0), (19.0, 6.0, 11.5)), 3)
mant = (dm < 0) & (Y > 66) & ~((AX < 7) & (Z < -3))
put(mant, NAVY, p=MA, l=1)
put(mant & ~(shift(mant, 1, 1) & shift(mant, 2, 1)), SIL)                               # lower edge band (2 rows)
put(mant & ~shift(mant, -1, 1) & (AX > 6), NAVYL)                                       # lit top

# ================================================================ sleeves: wide bell sleeves hanging from the arms (silver bottom + outer edge)
def sleeve(S, E, W, x_in, x_out, yb_in, yb_out, z_in, z_out, sgn, rad=(6.0, 6.0, 5.8)):
    m = chain([S, E, W], list(rad))
    a = np.clip((X * sgn - x_in) / (x_out - x_in), 0, 1)
    yb = yb_in + (yb_out - yb_in) * a ** 1.3
    zc_ = z_in + (z_out - z_in) * a
    yt = S[1] + 2 + (W[1] - S[1]) * a
    m |= (X * sgn > x_in) & (X * sgn < x_out) & (Y > yb) & (Y < yt) & (np.abs(Z - zc_) < 6.0 + 2.5 * (yt - Y) / 30)
    return m
SLL = sleeve((-15, 71, 1), (-23, 63, -1), (-29, 68, -7), 15, 34, 52, 37, 1, -6, -1)
SLR = sleeve((15, 71, 1), (21, 63, 0), (27, 64, -2.5), 14, 25.0, 52, 41, 1, -2, 1, rad=(6.0, 5.5, 3.8))
for m_, sgn in ((SLL, -1), (SLR, 1)):
    SP = newid()
    put(m_, NAVY, p=SP, l=2)
    put(m_ & ~(shift(m_, 1, 1) & shift(m_, 2, 1)), SIL)                                 # hem band
    put(m_ & ~(shift(m_, -sgn, 0) & shift(m_, -2 * sgn, 0)) & dil(front_face(m_), 1, axes=(2,)) & (Y < 66), SIL)   # outer edge, front rim
    inner = m_ & ~(shift(m_, sgn, 0)) & (Y < 62)
    put(inner, SILD)                                                                     # inner edge line
    put(front_face(m_) & (X * sgn > (17 if sgn > 0 else 18)) & (X * sgn < (23 if sgn > 0 else 30)) & (Y > 44) & (Y < 62), NAVYD)  # dark lining panel
    ffm = front_face(m_)
    xr = 20.0 if sgn > 0 else -26.0                                                      # rune column on the lining panel
    for j, yc in enumerate((59, 54, 49)):
        cells = [((0, 0), (0, -1), (1, -2)), ((0, 0), (1, -1), (0, -2)), ((-1, 0), (1, 0), (0, -1), (0, -2))][j]
        for (dx, dy) in cells:
            glow(ffm & (np.abs(X - (xr + dx + .5)) < .5) & (np.abs(Y - (yc + dy)) < .5), 3)

# ================================================================ hood: rounded back, boxy pointed-arch cowl in front, deep face opening
HO = newid()
dh = smin(sd_ell((0, 85.5, 2.5), (11.0, 11.5, 10.5)), sd_ell((0, 92.0, 5.5), (5.0, 5.5, 6.5)), 2)
dh = smin(dh, sd_ell((0, 79.0, 4.0), (14.5, 5.0, 11.0)), 4)                              # hood skirt flaring onto the mantle
cowl = (AX < 10.5 - np.clip(Y - 89, 0, None) * 1.1) & (Y > 77) & (Y < 95) & (Z > -11) & (Z < 0)
hood = ((dh < 0) & (AX < 12.5 - np.clip(Y - 86, 0, None) * .45)) | cowl                # bell-shaped crown of the hood
put(hood, NAVY, p=HO, l=3)
put(hood & (Y > 92) & ~shift(hood, -1, 1), NAVYL)
cav = (AX < 7.0 - np.clip(Y - 89, 0, None) * .9) & (Y > 77.5) & (Y < 94) & (Z < -1)
kind[cav] = 0
lining = (kind > 0) & dil(cav, 1) & (Z > -9)
put(lining, BLACK, st=False, p=0)
fz = np.argmax(hood & (kind > 0), axis=2)                                               # front-most hood cell per column
rim = hood & (kind > 0) & dil(cav, 3, axes=(0, 1)) & (np.arange(n[2])[None, None, :] <= fz[..., None] + 1)
put(rim, SIL, p=newid(), l=4)
put(rim & ~shift(rim, -1, 1), SILL)

# ================================================================ skull face (stamps: 'B' bone, 'K' carved dark, 'G'/'H' carved glow)
def stamp(rows, xc, ytop, zf, depth, pidv, lv, glowk=3, round_rows=()):
    wdt = len(rows[0])
    for r, row in enumerate(rows):
        y = ytop - r
        for c, ch in enumerate(row):
            if ch == '.': continue
            x = xc - (wdt - 1) / 2 + c
            xi, yi = ci(x, 0), ci(y, 1)
            z0 = ci(zf, 2) + (1 if r in round_rows or (c in (0, wdt - 1)) else 0)
            for k in range(z0, ci(zf, 2) + depth):
                kind[xi, yi, k] = 1; col[xi, yi, k] = BONED if k > z0 + 1 else (BONEL if r < 3 else BONE)
                stud[xi, yi, k] = True; pid[xi, yi, k] = pidv; lvl[xi, yi, k] = lv
            if ch in 'KGH':
                kind[xi, yi, z0] = 0                                                     # carve 1 deep: recessed + flush
                if ch == 'K': col[xi, yi, z0 + 1] = BLACK; stud[xi, yi, z0 + 1] = False
                else: kind[xi, yi, z0 + 1] = glowk if ch == 'G' else 4; col[xi, yi, z0 + 1] = GLOW[kind[xi, yi, z0 + 1]]
SKULL = ["..BBBBBBBB..",
         ".BBBBBBBBBB.",
         "BBBBBBBBBBBB",
         "BKKKBBBBKKKB",
         "BKGGKBBKGGKB",
         "BKGGGKKGGGKB",
         "BBKKKBBKKKBB",
         "BBBBBKKBBBBB",
         ".BBBKKKKBBB.",
         ".BBBBBBBBBB.",
         "..BBBBBBBB..",
         "..BKBKKBKB..",
         "..KKKKKKKK..",
         "..BKBKKBKB..",
         "...BBBBBB..."]
stamp(SKULL, 0.0, 92, -9.5, 10, newid(), 2, round_rows=(0, 1, 12, 13, 14))

# ================================================================ crown: black iron band round the hood, spikes all round, cyan gems
CR = newid()
band = dil(hood, 2) & ~hood & (Y > 93.5) & (Y < 97.5)
put(band, IRON, st=False, p=CR, l=5)
put(band & ((Y > 96.5) | (Y < 94.5)), IRONL, st=False)
def band_edge(a):                                     # outermost band cell along heading a (0 = front) at Y 95
    best = (0.0, 0.0)
    for r in np.arange(3, 16, .25):
        x, z = r * math.sin(a), 1.5 - r * math.cos(a)
        xi, zi = ci(x, 0), ci(z, 2)
        if 0 <= xi < n[0] and 0 <= zi < n[2] and band[xi, ci(95, 1), zi]: best = (x, z)
    return best
for adeg, L, r0 in ((0, 13, 2.6), (36, 8.5, 2.1), (-36, 8.5, 2.1), (72, 7, 1.9), (-72, 7, 1.9), (115, 6.5, 1.8), (-115, 6.5, 1.8), (150, 7, 1.8), (-150, 7, 1.8)):
    a = math.radians(adeg); bx, bz = band_edge(a); bx -= .6 * math.sin(a); bz += .6 * math.cos(a)
    sp = chain([(bx, 96.0, bz), (bx, 97 + L * .3, bz), (bx, 97 + L, bz)], [r0, r0 * .7, 0.0])
    put(sp & ~hood, IRON, st=False, p=CR, l=5)
    put(sp & ~hood & (Y > 97 + L * .55), IRONL, st=False)
zb = band_edge(0)[1]
gemF = (np.abs(X) / 2.6 + np.abs(Y - 96.5) / 3.8 < 1) & (Z > zb - 1.6) & (Z < zb + 1)
gemFr = (np.abs(X) / 3.8 + np.abs(Y - 96.5) / 5.2 < 1) & (Z > zb - 1) & (Z < zb + 2) & ~gemF
put(gemFr, IRONL, st=False, p=CR, l=6); glow(gemF, 3); glow(gemF & (X < 0) & (Y > 96.5), 4)
for sx in (1, -1):
    for ad in (18, 54):
        gx, gz = band_edge(math.radians(ad * sx))
        glow(band & (np.abs(X - gx) < 1.0) & (Y > 94.5) & (Y < 96.5) & (np.abs(Z - gz) < 1.0), 3)

# ================================================================ front panel: silver-bordered strip, chevron point, glowing runes
fl = front_layer()
reg = (AX < 5) & (Y > 13 + 1.25 * AX) & (Y < 60) & (Z < -2)
panel = fl & reg
put(panel, NAVYD, st=True, p=newid(), l=3)
pb = panel & ~ero(reg, 2, axes=(0, 1))
put(pb, SIL); put(pb & (X < 0), SILL)
RUNES = {'G': ["###.", "...#", "##.#", "#..#", ".##."],
         'A': [".##.", "#..#", ".##.", "#..#", "#..#"],
         'R': ["#...", "##..", "#.#.", "#..#", "#..."],
         'V': ["#..#", "#..#", ".##.", "#..#", ".##."]}
def rune(mask, key, xc, ytop, k=3):
    rows = RUNES[key]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '#': continue
            m = mask & (np.abs(X - (xc - 1.5 + c)) < .5) & (np.abs(Y - (ytop - r)) < .5)
            glow(m, k)
for key, yt in (('G', 41), ('R', 34), ('V', 27)):
    rune(panel, key, 0.0, yt)

# ================================================================ back panel: wide silver-bordered tabard with a trident rune
bl = back_layer()
regb = (AX < 10.5 - (72 - Y) * .07) & (Y > 37 + 1.3 * AX) & (Y < 72) & (Z > 2)
bpan = bl & regb
put(bpan, NAVYD, p=newid(), l=3)
put(bpan & ~ero(regb, 2, axes=(0, 1)), SIL)
TRI = ["#..##..#", "#..##..#", ".#.##.#.", "..####..", "...##...", "...##...", "...##...", "..####.."]
for r, row in enumerate(TRI):
    for c, ch in enumerate(row):
        if ch == '#': glow(bpan & (np.abs(X - (-3.5 + c)) < .5) & (np.abs(Y - (64 - r)) < .5), 3)

# ================================================================ chest: silver collar V from the shoulders to a cyan brooch
fs_ = front_face(kind == 1) & (Z < -4)
vline = (np.abs(Y - (70.5 + .55 * AX)) < 1.3) & (AX < 10.5) & (Y > 69.5)
put(fs_ & vline & (pid == RB), SIL, p=newid(), l=3)
fl = front_layer()
bro = fl & (np.abs(X) / 2.6 + np.abs(Y - 71.5) / 3.6 < 1) & (Z < -6)
brf = fl & (np.abs(X) / 3.8 + np.abs(Y - 71.5) / 5.0 < 1) & (Z < -6) & ~bro
put(brf, SIL, st=False, p=newid(), l=5); glow(bro, 3); glow(bro & (X < 0) & (Y > 71.5), 4)

# ================================================================ waist chain + 3 hanging bone skulls
def surfz(x, y):
    xi, yi = ci(x, 0), ci(y, 1); col_ = np.where(kind[xi, yi, :] > 0)[0]
    return lo[2] + .5 + col_.min() if len(col_) else 0.0
CH = newid()
def links(pts):
    P = np.array(pts, float); L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    for i, s_ in enumerate(np.arange(0, L[-1] + .01, 2.6)):
        p = np.array([np.interp(s_, L, P[:, j]) for j in range(3)])
        z = surfz(p[0], p[1]) - 1.0
        k = np.searchsorted(L, s_, side='right') - 1; k = min(max(k, 0), len(P) - 2)
        horiz = abs(P[k + 1, 0] - P[k, 0]) > abs(P[k + 1, 1] - P[k, 1])
        pc = np.round(p[:2] - .5) + .5 if True else p                                    # snap the link to cell centres
        pc[1] = np.round(p[1])
        if i % 2 == 0:                                                                   # 3x3 ring, dark hole
            m = (np.abs(X - pc[0]) < 1.6) & (np.abs(Y - pc[1]) < 1.6) & (np.abs(Z - z) < 1.0)
            put(m, SILL, st=False, p=CH, l=6)
            put(m & (np.abs(X - pc[0]) < .6) & (np.abs(Y - pc[1]) < .6) & (Z < z), NAVYX, st=False)
        else:                                                                            # side-on link between rings
            bx_, by_ = (1.1, .6) if horiz else (.6, 1.1)
            m = (np.abs(X - pc[0]) < bx_) & (np.abs(Y - pc[1]) < by_) & (np.abs(Z - z) < 1.0)
            put(m, SILD, st=False, p=CH, l=6)
belt = [(x, 61.5 - .012 * x * x, 0) for x in np.linspace(-11.5, 11.5, 13)]
links(belt)
links([(-10.5, 60.0, 0), (-10.5, 55.5, 0), (-9.5, 52.0, 0)])
links([(0, 59.5, 0), (0, 52.0, 0), (0, 49.5, 0)])
links([(10.0, 60.0, 0), (9.5, 55.0, 0), (8.5, 52.0, 0)])
SMALL = [".BBBBB.", "BBBBBBB", "BKKBKKB", "BKKBKKB", "BBBKBBB", ".BKBKB.", "..BBB.."]
for (xs, yt) in ((-9.5, 51), (-0.5, 48), (8.5, 51)):
    zf = min(surfz(xs - 3, yt - 3), surfz(xs + 3, yt - 3), surfz(xs, yt - 6)) - 2.5
    stamp(SMALL, xs, yt, zf, 5, newid(), 7, round_rows=(0, 6))

# ================================================================ hands: palm-up claw (orb side) + fist round the staff
BO = newid()
put(chain([(-28.5, 68.5, -7), (-31.5, 70.5, -10)], [1.6, 1.4]), BONE, p=BO, l=4)          # wrist
put(boxa(-35, -29, 69.5, 72.5, -13, -7), BONE, p=BO, l=4)                                 # palm
# spell orb: teardrop of soul fire sitting in the palm
orb = (sd_ell((-32.0, 78.5, -10.0), (5.2, 5.2, 5.2)) < 0) | chain([(-32, 82.5, -10), (-31.0, 86, -10.4), (-32.4, 89.0, -10)], [2.6, 1.4, .4])
glow(orb, 3); glow(orb & (sd_ell((-33.6, 80.0, -13.0), (2.6, 2.6, 2.6)) < 0), 4); glow(orb & ((Y < 74.5) | (sd_ell((-32.0, 78.5, -10.0), (5.2, 5.2, 5.2)) > -.9)) & (X > -30), 2)
for (fx, fz, top) in ((-34.5, -12.5, 76.5), (-34.5, -10.5, 77.5), (-34.5, -8.5, 76.5), (-33.5, -6.5, 75.5)):  # claws curling up the orb's side
    put(boxa(fx - .5, fx + .5, 72, top, fz - .5, fz + .5), BONE, p=BO, l=6)
    put(boxa(fx - .5, fx + .5, 73.5, 74.5, fz - .5, fz + .5), BONED, st=False)
    put(boxa(fx + .5, fx + 1.5, top - 1, top, fz - .5, fz + .5), BONEL, p=BO, l=6)         # tip hooks in toward the orb
put(boxa(-30, -28, 72, 74.5, -14, -12), BONE, p=BO, l=6)                                  # thumb
# ================================================================ staff: straight iron shaft held out at the side, leaning slightly outward,
# foot near the ground; the fist is built AROUND the shaft at arm's length (shaft runs through the fist centre)
SZ = -4.0
def AXF(y): return 31.0 + (y - 4.0) * 6.0 / 88.0          # shaft centre x at height y (top leans out)
AXY = AXF(Y)
pre_staff = kind > 0                                       # everything built so far (robe, sleeves, hood, chain, orb hand ...)
ST = newid(); S0 = kind.copy()
shaft = (np.abs(X - AXY) < 1.1) & (np.abs(Z - SZ) < 1.1) & (Y > 5.5) & (Y < 90)
put(shaft, IRON, st=False, p=ST, l=5)
for y0, y1 in ((80.5, 82.5), (40.5, 42.5), (10.5, 13.5)):
    put((np.abs(X - AXY) < 2.1) & (np.abs(Z - SZ) < 2.1) & (Y > y0) & (Y < y1), IRONL, st=False, p=ST, l=6)
put((np.abs(X - AXY) < .6) & (np.abs(Z - SZ) < 1.1) & (Y > 2.5) & (Y < 5.5), IRON, st=False, p=ST, l=5)   # foot spike
put((np.abs(X - AXY) < .6) & (np.abs(Z - SZ) < .6) & (Y > 1.5) & (Y < 2.5), IRON, st=False, p=ST, l=5)
glow((np.abs(X - AXY) < 1.1) & (Y > 8.5) & (Y < 10.5) & (Z > SZ - 2.2) & (Z < SZ - 1), 3)                  # ferrule gem
cage = (np.abs(X - AXY) / 3.0 + np.abs(Y - 87.0) / 4.6 < 1) & (np.abs(Z - SZ) < 1.6)
put(cage, IRON, st=False, p=ST, l=6)
gs = (np.abs(X - AXY) / 1.6 + np.abs(Y - 87.0) / 3.0 < 1) & (Z < SZ - .5) & (Z > SZ - 2.6)
glow(gs, 3); glow(gs & (X < AXY) & (Y > 87), 4)
SX = 37.0                                                  # staff head centre (on the axis at the top)
put(boxa(SX - 4, SX + 4, 89.5, 91.5, SZ - 2.5, SZ + 2.5), IRONL, st=False, p=ST, l=6)    # bracket under the skull
for sx in (1, -1):
    put(boxa(SX + sx * 3.5 - .5, SX + sx * 3.5 + .5, 86.5, 89.5, SZ - 1.5, SZ + 1.5), IRON, st=False, p=ST, l=6)
STAFFSKULL = [".BBBBBB.", "BBBBBBBB", "BKKBBKKB", "BBKBBKBB", "BBBKKBBB", ".BBBBBB.", ".BKBBKB.", "..BBBB.."]
stamp(STAFFSKULL, SX, 99, SZ - 4.5, 8, newid(), 7, round_rows=(0, 7))
for sx in (1, -1):
    hn = chain([(SX + sx * 3.5, 96.5, SZ), (SX + sx * 7.5, 97.0, SZ), (SX + sx * 10.0, 99.5, SZ), (SX + sx * 10.0, 103.0, SZ), (SX + sx * 8.6, 105.5, SZ)], [1.9, 1.7, 1.4, 1.0, .4])
    put(hn & (kind == 0), IRON, st=False, p=ST, l=6)
    put(hn & (Y > 101) & (kind == 1), IRONL, st=False)
# fist round the shaft: palm + curled fingers wrap the front, knuckle gaps, thumb over the top; shaft shows above and below
GY = 64.0; GX = AXF(GY)
# skeletal hand round the shaft: 4 finger bones (2 rows each, 1-row black gaps) curl round the front and outer side,
# a palm bar on the inner side joins them, knuckle bumps on the front, a thumb hooks over the top finger
ring = (np.abs(X - AXY) < 2.6) & (np.abs(Z - SZ) < 2.6) & ~((np.abs(X - AXY) < 1.1) & (np.abs(Z - SZ) < 1.1))
ring &= ~((X > AXY + 1.1) & (Z > SZ + 1.1))                                                # fingertips stop short at the back
palm = (X > AXY - 3.7) & (X < AXY - 1.1) & (Z > SZ - 1.1) & (Z < SZ + 2.6) & (Y > GY - 5.5) & (Y < GY + 5.5)
FIST = palm.copy()
put(palm, BONED, p=BO, l=6)
for k in range(4):
    yc = GY - 5 + 3 * k                                                                    # rows yc, yc+1 ; gap at yc+2
    fg = (ring | ((X > AXY - 3.7) & (X < AXY) & (Z > SZ - 3.1) & (Z < SZ - 1.1))) & (Y > yc - .5) & (Y < yc + 1.5)
    put(fg, BONE, p=BO, l=6); FIST |= fg
    kn = (np.abs(X - (AXY + .6)) < 1.1) & (np.abs(Y - (yc + 1)) < .5) & (np.abs(Z - (SZ - 3.5)) < .5)   # knuckle bump
    put(kn, BONEL, p=BO, l=7); FIST |= kn
    if k < 3:
        gp = (np.abs(X - AXY) < 2.1) & (np.abs(Z - SZ) < 2.1) & ~((np.abs(X - AXY) < 1.1) & (np.abs(Z - SZ) < 1.1)) & (np.abs(Y - (yc + 2)) < .5) & (X > AXY - 3.2)
        put(gp, BLACK, st=False, p=BO, l=6); FIST |= gp                                    # recessed black gap between fingers
thumb = (Y > GY + 5.5) & (Y < GY + 6.5) & (X > AXY - 3.7) & (X < AXY + 1.6) & (Z > SZ - 3.1) & (Z < SZ - 1.1)
thumb |= (np.abs(Y - (GY + 5)) < .5) & (np.abs(X - (AXY + 1.5)) < .6) & (np.abs(Z - (SZ - 2.5)) < .6)   # tip hooks down
put(thumb, BONEL, p=BO, l=7); FIST |= thumb
# slim wrist + forearm from the sleeve mouth into the palm
FORE = (chain([(27.5, 64.0, -2.5), (GX - 4.2, 64.0, SZ)], [1.5, 1.0])) & ~FIST
put(FORE, BONE, p=BO, l=4)
STAFF = shaft | ((kind > 0) & ~(S0 > 0) & ~FIST & ~FORE)                                  # every staff cell (shaft, collars, cage, skull, horns)

# ================================================================ soul flames: staff top, shoulders (tongues rooted in the surface)
def flames(base, tongues):
    for (dx, dz, L, lean, r0) in tongues:
        b = np.array(base, float) + (dx, 0, dz)
        pts = [b, b + (lean * .3, L * .35, 0), b + (-lean * .4, L * .7, 0), b + (lean, L, 0)]
        m = chain(pts, [r0, r0 * .75, r0 * .45, .3]) & (kind == 0)
        glow(m, 3); glow(m & (Y < b[1] + 1.5), 2)
        glow(m & cap(pts[0], pts[2], r0 * .35, .1), 4)
_k0 = kind.copy()
flames((SX, 99.0, SZ), [(0, 0, 7.5, .8, 2.4), (-1.8, .5, 4.5, -1, 1.4), (1.8, -.5, 5.0, 1.2, 1.4)])
STAFF |= (kind > 0) & (_k0 == 0)
for sx in (1, -1):
    flames((17.5 * sx, 75.0, 2.0), [(0, 0, 12.0, sx * 1.6, 2.4), (3.0 * sx, 1.5, 7.5, sx * 2.2, 1.6), (-3.0 * sx, -1, 8.0, -sx * 1.0, 1.6), (.5 * sx, 3.5, 6.0, sx, 1.4)])

# ================================================================ scattered light bricks on the robe (concept's sparkle squares)
navyish = (kind == 1) & ((col == NAVY).all(-1) | (col == NAVYD).all(-1))
surf = navyish & ~(shift(kind > 0, 1, 2) & shift(kind > 0, -1, 2) & shift(kind > 0, 1, 0) & shift(kind > 0, -1, 0))
col[surf & (rng.rand(*n) < .05)] = NAVYL

# ================================================================ keep only bricks 26-connected to the body
solid = kind > 0
reach = np.zeros(n, bool); reach[ci(0, 0), ci(66, 1), ci(1, 2)] = True
while True:
    nr = dil(reach, 1) & solid
    if nr.sum() == reach.sum(): break
    reach = nr
print('DROPPED', int(solid.sum() - reach.sum()), 'floating bricks')
kind[~reach] = 0; solid = kind > 0

# ---------------------------------------------------------------- seams + light + palette
# ---------------------------------------------------------------- grip test: shaft never inside another part; staff >= 2 bricks clear of everything but the fist
def cube_dil(m, k):
    for _ in range(k):
        for ax in range(3): m = m | shift(m, 1, ax) | shift(m, -1, ax)
    return m
STAFF &= kind > 0; FIST &= kind > 0
others = (kind > 0) & ~STAFF & ~FIST
over = int((shaft & pre_staff).sum())
near = int((cube_dil(STAFF, 2) & others).sum())
print('GRIP_TEST shaft_over_prior=%d staff_within2_of_other=%d shaft_in_fist=%d shaft_above=%d shaft_below=%d' % (
    over, near, int((shaft & FIST).sum()), int((shaft & (kind > 0) & ~FIST & (Y > GY + 4)).sum()), int((shaft & (kind > 0) & ~FIST & (Y < GY - 4)).sum())))
assert over == 0 and near == 0, 'staff intersects or touches another part'
pid[kind == 0] = 0                                                                      # carved cells keep no plate id
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.clip(.86 + .2 * (Y / 100.0), .86, 1.06)[..., None]
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('3d4a94', '2b3373', '1d2253', '131634',          # robe light / main / dark / deep
                                 'd4d8e0', 'a9aeb9', '7a7f8c',                    # silver
                                 'f1e7cd', 'd8caa8', 'ab9a7c',                    # bone
                                 '4c4c58', '2d2d36', '0d0e14')])                  # iron light / iron / black
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- mesh: exposed faces (vertex colours) + studs
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb

STUD_PNG = os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png')
def build(name, mask, with_studs):
    verts = []; faces = []; cols = []; uvs = []; nv = 0
    for ax in range(3):
        u, w_ = [k for k in range(3) if k != ax]
        for s in (1, -1):
            e = np.argwhere(exposed(mask, ax, s))
            if not len(e): continue
            base = lo + e; off = np.zeros(3); off[ax] = 1 if s > 0 else 0
            q = []; tt = []
            for du, dw in ((0, 0), (1, 0), (1, 1), (0, 1)):
                dd_ = off.copy(); dd_[u] = du; dd_[w_] = dw; q.append(base + dd_)
                tt.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w_] + dw) / 16.0], 1))
            q = np.stack(q, 1); tt = np.stack(tt, 1); k = len(e)
            idx = nv + np.arange(4 * k).reshape(k, 4)
            if not ((s > 0) != (ax == 1)): idx = idx[:, ::-1]; tt = tt[:, ::-1]; q = q[:, ::-1]; idx = nv + np.arange(4 * k).reshape(k, 4)
            verts.append(q.reshape(-1, 3)); faces.append(idx); nv += 4 * k; uvs.append(tt.reshape(-1, 2))
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
body = build('LichKing', kind == 1, True)
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
    for nm, pos, e in (('EyeL', (3.5, 86.5, -13), 25), ('EyeR', (-3.5, 86.5, -13), 25), ('Orb', (-32, 78, -16), 1400),
                       ('StaffF', (SX, 103, SZ - 4), 700), ('Grip', (GX, 66, SZ - 14), 0), ('CrownGem', (0, 97, -14), 60), ('FaceW', (0, 84, -30), 0), ('HemF', (0, 14, -22), 1800),
                       ('HemL', (-20, 14, 0), 1200), ('HemR', (20, 14, 0), 1200), ('HemB', (0, 14, 22), 1500),
                       ('ShL', (-18, 84, -4), 300), ('ShR', (18, 84, -4), 300)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.color = tuple(GLOW[3]) if nm.startswith('Eye') else (.25, .95, 1.0); L.data.shadow_soft_size = 1.0
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
        t_ = B(*tgt)
        dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
        cam.location = t_ + dv * dist; cam.rotation_euler = (t_ - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
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
    for nm, az, el, tg in (('ortho_front', 0, 0, (3, 56, 0)), ('ortho_side', 90, 0, (3, 56, 0)),
                           ('ortho_back', 180, 0, (3, 56, 0)), ('ortho_top', 0, 89.9, (3, 56, 0))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=122)
    for nm, a in (('rest_34', ((-2, 56, 0), 205, -32, 8)), ('rest_side', ((3, 56, 0), 205, 90, 5)), ('rest_front', ((3, 56, 0), 205, 0, 5)),
                  ('rest_back', ((3, 56, 0), 205, 160, 10)), ('skulls', ((0, 52, -10), 50, -15, 5)),
                  ('face', ((0, 88, -6), 52, 0, 3)), ('headside', ((0, 92, 0), 64, 90, 3)), ('head34', ((0, 92, -4), 64, -35, 8)),
                  ('staff', ((SX, 92, SZ), 62, -20, 5)), ('grip', ((GX - 2, 64, SZ), 34, -35, 12)), ('orb', ((-31, 75, -9), 46, -30, 10)), ('hem', ((0, 24, -4), 110, -25, 4))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a not in ('render', 'views')]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): floating lich, L = +x (staff hand), R = -x (orb hand)
RIG = [('root', None, (0, 0, 1), (0, 6, 1)), ('spine', 'root', (0, 34, 2), (0, 64, 1)), ('chest', 'spine', (0, 64, 1), (0, 80, 2)),
       ('head', 'chest', (0, 80, 3), (0, 100, 3)),
       ('upperarmL', 'chest', (15, 71, 1), (21, 63, 0)), ('forearmL', 'upperarmL', (21, 63, 0), (27, 64, -2.5)), ('handL', 'forearmL', (27, 64, -2.5), (GX, GY, SZ)),
       ('upperarmR', 'chest', (-15, 71, 1), (-23, 63, -1)), ('forearmR', 'upperarmR', (-23, 63, -1), (-29, 68, -7)), ('handR', 'forearmR', (-29, 68, -7), (-33, 72, -10))]
sol_ = kind > 0
OVR = brick_rig.limb(X, Y, Z, SLL & sol_ & (pid != BO), RIG[7:9]) + brick_rig.limb(X, Y, Z, SLR & sol_ & (pid != BO), RIG[4:6])
OVR += [((pid == MA) & sol_, 'chest'), ((Y > 81) & (AX < 17), 'head'), ((kind >= 2) & (Y > 74) & (AX > 12) & (AX < 26) & (Z > -6), 'chest')]
tt_ = np.clip((63.0 - Y) / 40.0, 0, 1.3); zc_r = 1.0 + 4.5 * tt_
hd_ = np.degrees(np.arctan2(X, -(Z - zc_r)))                                     # robe heading, 0 = front
def rob_pt(a, y):
    t_ = np.clip((63.0 - y) / 40.0, 0, 1); r_x = .6 * (11.5 + 9.5 * t_ ** .85); r_z = .6 * (9.5 + 9.0 * t_)
    zc_ = 1.0 + 4.5 * np.clip((63.0 - y) / 40.0, 0, 1.3); a = math.radians(a)
    return (r_x * math.sin(a), y, zc_ - r_z * math.cos(a))
low = sol_ & (Y < 34)
for nm, a, sel in (('F', 0, np.abs(hd_) <= 45), ('L', 90, (hd_ > 45) & (hd_ < 135)), ('B', 180, np.abs(hd_) >= 135), ('R', -90, (hd_ < -45) & (hd_ > -135))):
    p0, p1, p2 = rob_pt(a, 34), rob_pt(a, 19), rob_pt(a, 4)
    ch_ = [('robe%s1' % nm, 'spine', p0, p1), ('robe%s2' % nm, 'robe%s1' % nm, p1, p2)]
    RIG += ch_; OVR += brick_rig.limb(X, Y, Z, low & sel, ch_)
OVR += [((((pid == BO) & (X < 0)) | orb) & sol_, 'handR'), ((((pid == BO) & (X > 0)) | STAFF | FIST | FORE) & sol_, 'handL')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (15, 0, 0), 'upperarmR': (-40, 0, 0), 'forearmL': (30, 0, 0), 'robeF2': (30, 0, 0), 'robeL1': (0, 0, 20)},
                 render='render' in argv)
print('BL_OK')
