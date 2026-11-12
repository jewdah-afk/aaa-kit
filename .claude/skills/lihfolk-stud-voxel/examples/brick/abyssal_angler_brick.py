# SKILL-STYLE brick model (copied from examples/brick/war_rhino_brick.py). Reference = AbyssalAngler/concept_sheet.jpg
# GLOW: strong   (read by scripts/run_brick.ps1). Per-colour glow mask: eyes (3, 6) + lure (4, 5) bloom fully;
#        flank spots (2) draw at 18% in the glow pass, so they glow without tinting the body cyan.
# Giant Abyssal Anglerfish boss: round navy head-body with black blotches, teal underbite jaw + belly, dark-red maw with
# bone needle teeth, angry brow over small recessed cyan eyes, arched lure stalk with a yellow-white bulb, cyan spot rows,
# spiky teal dorsal row, ragged pectorals, fan tail. Hovers (no legs). Static.
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'AbyssalAngler'

lo = np.array((-42.0, -0.5, -62.0)); hi = np.array((42.0, 94.5, 66.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
NAVY = hx('1a2c4c'); NAVYL = hx('25406a'); NAVYD = hx('121e36'); BLACK = hx('0b0d12')
TEAL = hx('1f6e72'); TEALL = hx('2f9a96'); TEALD = hx('164e55')
BONE = hx('efe6cc'); BONES = hx('c9b994'); RED = hx('8a2030'); REDD = hx('3a0a12')
GLOW = {2: hx('39e8ff'), 3: hx('c8fdff'), 4: hx('ffe680'), 5: hx('fffbe0'), 6: hx('39e8ff')}   # spots / eye hot / lure / lure hot / eye
BLOOM_FULL = (3, 4, 5, 6)

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l
def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1):
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / max(ab.dot(ab), 1e-9), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def ix(v, a): return int(np.clip(np.floor(v - lo[a]), 0, n[a] - 1))
def front_z(x, y):                                   # front-most solid z at (x, y), or None
    zs = np.where(kind[ix(x, 0), ix(y, 1), :] == 1)[0]
    return None if not len(zs) else lo[2] + .5 + zs.min()
def side_x(y, z):                                    # outer-most solid +x at (y, z)
    xs = np.where(kind[:, ix(y, 1), ix(z, 2)] == 1)[0]
    return None if not len(xs) else lo[0] + .5 + xs.max()
def top_y(x, z):
    ys = np.where(kind[ix(x, 0), :, ix(z, 2)] == 1)[0]
    return None if not len(ys) else lo[1] + .5 + ys.max()
def cell(x, y, z):
    m = np.zeros(n, bool); m[ix(x, 0), ix(y, 1), ix(z, 2)] = True; return m

rng = np.random.RandomState(7)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ---------------------------------------------------------------- body field: huge round head-body, underslung jaw, tapering tail
d = sd_ell((0, 44, -2), (21.0, 22.0, 24.0))                           # head-body globe
d = smin(d, sd_ell((0, 43, 9), (15.5, 16.5, 13.0)), 6)              # rear body
d = smin(d, sd_ell((0, 42, 22), (6.5, 8.0, 8.0)), 5)                # tail stock
d = smin(d, sd_ell((0, 48, -15), (18.0, 9.5, 22.0)), 7)              # upper jaw / snout pushed forward
d = smin(d, sd_ell((0, 50.5, -31), (16.0, 4.5, 6.0)), 3)              # bulbous upper-lip roll overhanging the fangs
dj = sd_ell((0, 31, -14), (20.0, 11.5, 25.0))                         # lower jaw: juts forward (underbite)
d = smin(d, dj, 4)
gape = sd_ell((0, 39.0, -36), (17.5, 10.5, 22.0))                     # the open maw: wide oval across the lower face
tt = np.clip((-6 - Z) / 32, 0, 1)                                        # 0 at the mouth corner (far back) .. 1 at the snout
yu = 39 + 11 * tt; yl = 37 - 8 * tt                                       # upper edge slopes up to the snout, lower edge down
wedge = np.maximum(np.maximum(Y - yu, yl - Y), Z + 6)
gape = np.minimum(gape, np.where(AX > 12.0, wedge, 99))                     # diagonal side opening: the maw reads from the side
BODY = newid(); JAW = newid()
put(d < 0, NAVY, p=BODY, l=1)
# colour zones: teal lower jaw band + teal belly
put((kind == 1) & ((dj < .8) | (Y < 30 + .25 * np.maximum(Z, 0))) & (Y < 38), TEAL, p=JAW, l=2)
put((kind == 1) & (pid == JAW) & (Y < 24 + .3 * np.maximum(Z, 0)), TEALL, p=JAW, l=2)
# black blotches on the navy (2x2x2 cell noise)
def patches(sz, p, off):                                                  # random sz-brick cubes
    g = rng.rand(n[0] // sz + 2, n[1] // sz + 2, n[2] // sz + 2) < p
    I, J, K = np.meshgrid((np.arange(n[0]) + off) // sz, (np.arange(n[1]) + off) // sz, (np.arange(n[2]) + off) // sz, indexing='ij')
    return g[I, J, K]
blot = patches(5, .2, 0) | patches(3, .14, 1) | patches(4, .12, 2)          # bold 3-5 brick blotches
put((kind == 1) & (pid == BODY) & blot, BLACK, st=False, p=BODY, l=1)
put((kind == 1) & (pid == JAW) & blot & (rng.rand(*n) < .35), TEALD, p=JAW, l=2)
lipband = (dj > -2.5) & (dj < 2.0) & (Y > 23.0) & (Y < 29.5) & (Z < -16) & (AX < 21)
put(lipband, TEALL, p=JAW, l=2.5)

# carve the maw; inner walls dark red, back of the throat deeper
kind[(gape < 0) & (kind == 1)] = 0
gp = np.minimum(gape, wedge)
inner = (kind == 1) & (gp < 2.2) & (d < -2.0)
put(inner, RED, st=False)
put(inner & (Z > -13), REDD, st=False)
put((gape < 0) & (d < 0) & (AX < 9) & (Z > -25), RED, st=False)                           # throat block: red behind the fangs, blocks see-through
put((kind == 1) & (gp < 2.2) & (d >= -2.0) & (Y > 38), NAVYD, p=BODY, l=1)      # upper lip rim
put((kind == 1) & (gape < 2.2) & (d >= -2.0) & (Y <= 38), TEALL, p=JAW, l=2.5)    # lower lip rim (part of the bright band)

# ---------------------------------------------------------------- teeth: long bone needles. Upper hang down, lower (taller) point up
TUP = np.zeros(n, bool); TLO = np.zeros(n, bool); TM = [TUP]           # rig: which fangs belong to the jaw
def tooth(root, tip, hw=2.2):                       # triangle fang: hw-wide base narrowing to a 1-brick point, 2 bricks deep
    root = np.array(root, float); tip = np.array(tip, float)
    L = int(round(abs(tip[1] - root[1])))
    for k in range(L + 1):
        t = k / max(L, 1); c = root + (tip - root) * t
        w = max(.5, hw * (1 - t))
        wz = max(.5, 2.0 * (1 - t))                                   # 4 bricks deep at the root -> real cone from the side
        m_ = (np.abs(X - c[0]) <= w) & (np.abs(Z - c[2]) <= wz) & (np.abs(Y - c[1]) < .5)
        put(m_, BONE if t < .7 else BONES, st=False); TM[0] |= m_
def lip_cell(x, upper):                             # front-most mouth roof (upper) / floor cell at column x
    xi = ix(x, 0); g = gape[xi] < 0; s_ = kind[xi] == 1
    nbm = np.zeros_like(s_)
    if upper: nbm[1:] = g[:-1]
    else: nbm[:-1] = g[1:]
    c = np.argwhere(s_ & nbm)
    if not len(c): return None
    c = c[c[:, 1].argmin()]; return (x, lo[1] + .5 + c[0], lo[2] + .5 + c[1])
def rim(upper):                                      # lip-edge cells all round the maw (front + both cheeks), spaced out
    g = gape < 0; nbm = np.zeros(n, bool)
    if upper: nbm[:, 1:, :] = g[:, :-1, :]
    else: nbm[:, :-1, :] = g[:, 1:, :]
    c = np.argwhere((kind == 1) & nbm & (d > -3.5))
    c = c[np.argsort(c[:, 2])]; pick = []                              # front-most first
    for e in c:
        p = lo + .5 + e
        if all((p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2 > 3.7 ** 2 for q in pick): pick.append(p)
    return pick
UPX = (-14.4, -9.6, -4.8, 0.0, 4.8, 9.6, 14.4)                            # 7 upper triangle fangs
for i, x in enumerate(UPX):
    c = lip_cell(x, True)
    if c is None: continue
    L = (4, 7, 7, 8, 7, 7, 4)[i]
    sl = -np.sign(x) * (1.5 if abs(x) > 8 else 0)                     # outer fangs slant inward
    tooth((c[0], c[1], c[2] + 2.5), (c[0] + sl, c[1] - L, c[2] + 2.5), 2.2 if abs(x) < 12 else 1.7)
TM[0] = TLO
LOX = (-12.0, -7.2, -2.4, 2.4, 7.2, 12.0)                                  # 6 lower fangs between them
for i, x in enumerate(LOX):
    c = lip_cell(x, False)
    if c is None: continue
    L = (8, 12, 9, 9, 12, 8)[i]
    sl = -np.sign(x) * (1.5 if abs(x) > 8 else 0)
    tooth((c[0], c[1], c[2] + 2.5), (c[0] + sl, c[1] + L, c[2] + 2.5), 2.6 if abs(x) < 11 else 2.0)
def side_row(upper):                                                  # cone fangs along the side opening, +x side, mirrored
    g = gp < 0; nbm = np.zeros(n, bool)                               # lip-edge cells of the side opening (outermost per z)
    if upper: nbm[:, 1:, :] = g[:, :-1, :]
    else: nbm[:, :-1, :] = g[:, 1:, :]
    c = np.argwhere((kind == 1) & nbm & (X > 12.5) & (d > -2.5))
    best = {}
    for e in c:
        p = lo + .5 + e
        if p[2] not in best or p[0] > best[p[2]][0]: best[p[2]] = p
    ps = [best[z] for z in sorted(best)]
    if not ps: return []
    z0, z1 = ps[0][2], ps[-1][2]
    out = []
    for p in ps:
        if p[2] - z0 < 3 or (out and p[2] - out[-1][2] < 5.0): continue  # skip the front corner (front row covers it), 5 apart
        out.append(p)
    return [(p, (p[2] - z0) / max(z1 - z0, 1)) for p in out]
for upper in (True, False):
    TM[0] = TUP if upper else TLO
    for p, tz in side_row(upper):
        if tz > .9: continue                                          # nothing right at the mouth corner
        L = (3.5 + 5.5 * math.sin(math.pi * (.15 + .7 * tz))) if upper else (4 + 6 * math.sin(math.pi * (.15 + .7 * tz)))
        for sx in (1, -1):
            x = sx * (p[0] - 1.0)
            if upper: tooth((x, p[1], p[2]), (x, p[1] - L, p[2]), 1.2)                   # hang from the lip curve
            else: tooth((x, p[1], p[2]), (x, p[1] + L, p[2]), 1.2)                       # rise along the jaw
# ---------------------------------------------------------------- eyes: small, recessed, flush cyan under a heavy V brow
EYE = []
BROW = newid()
for sx in (1, -1):
    ex, ey = 9.5 * sx, 57.0   # half-brick x: eye cells sit on brick centres
    zf = front_z(ex, ey)
    SL = [(dx, dy) for dx in (-3, -2, -1, 0, 1, 2, 3)                   # slit: 2 rows, outer end high
          for dy in ((0,) if dx * sx < -1 else (0, 1) if dx * sx < 2 else (1, 2))]
    zs_ = [front_z(ex + dx, ey + dy) for dx, dy in SL]
    zp = lo[2] + .5 + int(round(np.mean(zs_) - lo[2] - .5))           # one flat plane at the mean surface depth: shallow, filled slit
    for (dx, dy), z0 in zip(SL, zs_):
        col_ = (np.abs(X - (ex + dx)) < .5) & (np.abs(Y - (ey + dy)) < .5)
        put(col_ & (Z < zp - .1) & (kind == 1), np.zeros(3), k=0)
        put(col_ & (Z > zp - .1) & (Z < max(zp, z0) + 1.5), GLOW[6], k=6, st=False)
    zf = zp
    EYE.append((ex, ey, zf))
    # heavy angry brow: slab over the eye, stepping down toward the centre line, juts forward
    for dx in range(-5, 6):
        xb = ex + dx * sx
        yb = ey + 2 + (1 if dx > 0 else 0) + (1 if dx > 3 else 0) - (1 if dx < -3 else 0)   # heavy brow right over the slit, outer end high
        for dy in (0, 1, 2, 3):
            z0 = front_z(xb, yb + dy)
            if z0 is None: continue
            put((np.abs(X - xb) < .5) & (np.abs(Y - (yb + dy)) < .5) & (Z > z0 - 4.2 + .7 * dy) & (Z < z0 + 1) & (kind < 2), NAVYD, p=BROW, l=4)
under = (pid == BROW) & (kind == 1) & (np.roll(pid, 1, 1) != BROW)
put(under, BLACK, st=False)                                                      # brow underside shadow

# ---------------------------------------------------------------- bioluminescent spot rows along both flanks
for (y, zs) in ((48, range(-15, 22, 6)), (39, range(-10, 24, 6))):
    for z in zs:
        xs = side_x(y, z)
        if xs is None or xs < 6: continue
        for sx in (1, -1):
            for dy in (0, 1):
                for dz in (0, 1):
                    put(cell(sx * xs, y + dy, z + dz), GLOW[2], k=2, st=False)
STR = (kind == 1) & (AX > 2.4) & (AX < 6.5) & (d > -1.5) & (Z > -8) & ((Y > 46) | ((Z > 6) & (Y > 38)))
put(STR, TEALL, p=JAW, l=2)                                            # teal stripe down the spine
for z in range(-4, 24, 4):
    for sx in (1, -1):
        yt_ = top_y(7.5 * sx, z)
        if yt_ is not None and yt_ > 40: put(cell(7.5 * sx, yt_, z), GLOW[2], k=2, st=False)
# ---------------------------------------------------------------- fins (teal): dorsal spike row, ragged pectorals, fan tail
FIN = newid()
ZS = list(range(-9, 24, 5))
TOPS = {z: top_y(0, z) for z in ZS}                                   # body tops before any spine is added
HT = {}
for i, z in enumerate(ZS):                                            # chunky triangle spikes: 5 wide base, back-raked, tallest mid-back
    yt = TOPS[z]
    if yt is None: continue
    L = 7 + 7.5 * math.sin(math.pi * (i + .6) / (len(ZS) + .2)) + (1.5 if i % 2 else -1)
    HT[z] = (yt, L)
    for k in range(int(L) + 1):
        t = k / L; hz = max(.5, 3.6 * (1 - t) ** .8); zc = z + 2.0 + 2.0 * t   # wide base, slight back-rake
        put((AX <= 1.0) & (np.abs(Y - (yt - 1 + k)) < .5) & (np.abs(Z - zc) <= hz), TEAL if i % 2 else TEALL, p=FIN, l=3)
zz = sorted(HT)
for za, zb in zip(zz, zz[1:]):                                        # dark membrane joining the lower halves
    (ya, La), (yb, Lb) = HT[za], HT[zb]
    for z in np.arange(za + 2, zb + 2.5, 1.0):
        f = (z - za - 2) / (zb - za); yt_ = ya + (yb - ya) * f; h = .45 * (La + (Lb - La) * f)
        put((AX <= .5) & (Y > yt_ - 1) & (Y < yt_ + h) & (np.abs(Z - z) < .5) & (kind == 0), TEALD, p=FIN, l=2.8)
for sx in (1, -1):                                                   # pectoral: filled fan membrane + jagged spikes
    root = (17.5 * sx, 33, 1)
    for j, a in enumerate(np.linspace(-.95, .85, 41)):
        L = 14.0 + 8.0 * (1 - abs((j % 8) - 4) / 4) ** 1.5
        tip = (root[0] + sx * L * math.cos(a), root[1] + L * math.sin(a), root[2] + 6 + 3 * abs(a))
        put(chain([root, tip], [1.9, .75]), TEAL if j % 8 == 0 else TEALL if j % 4 == 0 else TEALD if j % 2 else TEAL, p=FIN, l=3)
# tail: navy stock -> big teal fan, rays splay up/down, alternating length
for j, a in enumerate(np.linspace(-1.15, 1.15, 57)):
    L = 20 + 9.0 * (1 - abs((j % 8) - 4) / 4) ** 1.5 + 5 * abs(a)
    tip = (0, 42 + L * math.sin(a), 28 + L * math.cos(a))
    put(chain([(0, 42, 27), tip], [1.2, .75]), TEALL if j % 8 == 0 else TEAL if j % 4 == 0 else TEALD if j % 2 else TEAL, p=FIN, l=3)
put(sd_ell((0, 42, 28), (3.5, 7, 3)) < 0, TEALD, p=FIN, l=3)
for a in (-1.2, -1.0, -.8):                                          # ventral fin under the tail stock
    tip = (0, 34 + 9 * math.sin(a), 16 + 9 * math.cos(a))
    put(chain([(0, 35, 15), tip], [1.4, .8]), TEAL, p=FIN, l=3)

# ---------------------------------------------------------------- lure: stalk from the forehead arching forward, glowing bulb
yt = top_y(0, -10)
STALK = [(0, yt - 1, -10), (0, yt + 9, -14), (0, yt + 16, -22), (0, yt + 18, -32), (0, yt + 15, -42), (0, yt + 8, -48)]
put(chain(STALK, [3.2, 2.5, 2.1, 1.9, 1.8, 1.6]), NAVYD, p=newid(), l=5)
bc = (0, STALK[-1][1] - 5, -48)
put((AX < 2) & (Y > bc[1] + 2) & (Y < bc[1] + 4) & (np.abs(Z - bc[2]) < 2), BLACK, st=False)         # dark cap
put((AX < 3) & (np.abs(Y - bc[1]) < 2.6) & (np.abs(Z - bc[2]) < 2.6), GLOW[4], k=4, st=False)         # square bulb
put((X > -2) & (X < 1) & (Y > bc[1]) & (Y < bc[1] + 2) & (Z < bc[2] - 1.5) & (Z > bc[2] - 2.6), GLOW[5], k=5, st=False)
LURE = bc
print('ANGLER eyes', EYE, 'lure', LURE)

# ---------------------------------------------------------------- seams: the lower part darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .6
col *= np.clip(.72 + .5 * ((Y - 22) / 50.0), .72, 1.15)[..., None]               # lit tops, dark underside
col[lipband & (kind == 1) & (pid == JAW)] = hx('3fb8ae')                      # lower-lip band stays bright (not shaded down)
col[lipband & (kind == 1) & (pid == JAW) & (Y > 32)] = hx('2f9a96')
col = np.clip(col, 0, 1)
# PALETTE <= 16: snap every solid brick to its nearest entry.
PAL = np.array([hx(h) for h in ('25406a', '1a2c4c', '121e36', '0c1424', '0b0d12',     # navy light / main / dark / deep / black
                                 '3fb8ae', '2f9a96', '1f6e72', '164e55', '0f3439',    # teal lip / light / main / dark / deep
                                 'efe6cc', 'c9b994',                                  # bone / bone shade
                                 '7a1c28', '5a1420', '3a0a12')])                      # mouth red / mid / deep
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

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
body = build('AbyssalAngler', kind == 1, True)
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
    o.data.materials.append(gm); f_ = 1.0 if k in (4, 5) else .8 if k in (3, 6) else .18; o.color = (cl[0] * f_, cl[1] * f_, cl[2] * f_, 1); GL.append(o)
# drop any solid brick with no face neighbour (stray single bricks at thin tips)
nbc = sum(np.roll(kind > 0, sh, ax) for ax in range(3) for sh in (1, -1))
lone = (kind > 0) & (nbc == 0)
print('LONE_BRICKS', int(lone.sum()))
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for i, (ex, ey, ez) in enumerate(EYE):                                     # cyan eye lights spill on brow + lips
        L = bpy.data.objects.new('EyeLight%d' % i, bpy.data.lights.new('EyeLight%d' % i, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 350; L.data.color = (.224, .91, 1.0); L.data.shadow_soft_size = 1.0
        L.location = B(ex, ey, ez - 2.5)
    L = bpy.data.objects.new('LureLight', bpy.data.lights.new('LureLight', 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 3500; L.data.color = (1.0, .9, .5); L.data.shadow_soft_size = 2.0; L.location = B(LURE[0], LURE[1], LURE[2] - 1)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', 1.8, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .8, .9)
    sc.world.use_nodes = True; wn = sc.world.node_tree; bg = wn.nodes.get('Background') or wn.nodes.new('ShaderNodeBackground')
    lp = wn.nodes.new('ShaderNodeLightPath'); mxw = wn.nodes.new('ShaderNodeMix'); mxw.data_type = 'RGBA'
    mxw.inputs[6].default_value = (.0508, .0508, .0508, 1); mxw.inputs[7].default_value = (.356, .546, .275, 1)   # lighting grey / ground green
    wn.links.new(lp.outputs['Is Camera Ray'], mxw.inputs[0]); wn.links.new(mxw.outputs[2], bg.inputs['Color'])
    ow = wn.nodes.get('World Output') or wn.nodes.new('ShaderNodeOutputWorld'); wn.links.new(bg.outputs[0], ow.inputs[0])
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (.26, .4, .2, 1)
    gb.inputs['Roughness'].default_value = 1.0; gb.inputs['Specular IOR Level'].default_value = 0.0   # flat matte ground = one even colour, no horizon band
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
    cen = (0, 46, 0); D = 230
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 48, 1), 400, az, el, ortho=132)
    for nm, a in (('rest_34', (cen, D, -40, 16)), ('rest_side', (cen, D, 90, 6)), ('rest_front', ((0, 48, -10), 200, 0, 4)), ('rest_back', ((0, 48, 4), 215, 165, 14)),
                  ('face', ((0, 50, -30), 140, 0, 3)), ('headside', ((0, 48, -25), 120, 90, 3)), ('head34', ((0, 46, -25), 120, -38, 8))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): bones in brick coords, L = +x
SOL = kind > 0; STALKP = NEXT[0]                                       # the lure stalk got the last id
G = gape < 0; gy = np.where(G.any(1), lo[1] + .5 + G.argmax(1), 37 - 8 * np.clip((-6 - cz[None, :]) / 32, 0, 1))
JAWM = SOL & (Z < -5) & (Y < gy[:, None, :])                           # everything under the mouth floor, in front of the hinge
BULB = (AX < 3.5) & (np.abs(Y - bc[1]) < 4.6) & (np.abs(Z - bc[2]) < 3)
LURE_B = [('lure1', 'body', STALK[0], STALK[2]), ('lure2', 'lure1', STALK[2], STALK[4]), ('lure3', 'lure2', STALK[4], bc)]
TAIL_B = [('tail1', 'body', (0, 43, 13), (0, 42, 21)), ('tail2', 'tail1', (0, 42, 21), (0, 42, 28.5))]
FAN = SOL & (Z > 28.5) & (AX < 4)
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('body', 'root', (0, 44, 14), (0, 44, -24)), ('jaw', 'body', (0, 37, -5), (0, 30, -40))]
RIG += TAIL_B + [('fan', 'tail2', (0, 42, 28.5), (0, 42, 58))] + LURE_B
def grow(m, seed):                                                     # 6-connected part of m that touches seed
    r = m & seed
    while True:
        r2 = r.copy()
        for ax in range(3): r2 |= np.roll(r, 1, ax) | np.roll(r, -1, ax)
        r2 &= m
        if r2.sum() == r.sum(): return r
        r = r2
JAWC = grow((JAWM | TLO) & ~TUP, JAWM & (Y < 26))                       # fang tips cut off by an upper fang stay with the head
OVR = [(SOL, 'body'), (JAWC, 'jaw')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    RIG += [('fin' + sd, 'body', (17.5 * sx, 33, 1), (36 * sx, 33, 9))]
    OVR += [((pid == FIN) & (X * sx > 15.5) & (Z > -8) & (Z < 16), 'fin' + sd)]
OVR += brick_rig.limb(X, Y, Z, SOL & (Z > 13) & (AX < 15.5) & ~FAN, TAIL_B) + [(SOL & (Z > 13) & (Z < 28.5) & (Y < 36) & (AX < 2), 'tail1'), (FAN, 'fan')]
OVR += brick_rig.limb(X, Y, Z, SOL & ((pid == STALKP) | BULB), LURE_B)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'jaw': (22, 0, 0), 'lure1': (15, 0, 0), 'lure2': (15, 0, 0), 'tail1': (0, 0, 15), 'fan': (0, 0, 20), 'finL': (0, 0, 30)},
                 render='render' in argv)
print('BL_OK')
