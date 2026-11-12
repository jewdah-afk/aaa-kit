# Giant Bone Hydra boss (stud-voxel, brick pipeline). Machinery copied from skill examples/brick/war_rhino_brick.py.
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference = concept_sheet.jpg. Heavy dark-purple reptile body on 4 clawed legs, 3 S-curved necks (centre tallest) with
# bone-white vertebra ridges, bone dragon skulls (open jaws, teeth, swept horns, recessed toxic-green eye sockets),
# exposed rib cage with a glowing green core, green glow cracks, bone spine spikes, long spiked tail.
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'BoneHydra'

lo = np.array((-122.0, -0.5, -150.0)); hi = np.array((122.0, 250.5, 200.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx.astype(np.float32), cy.astype(np.float32), cz.astype(np.float32), indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3), np.float32); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)
pid = np.zeros(n, np.int32); lvl = np.zeros(n, np.float32)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
BONEW = hx('efe5cc'); BONEG = hx('c8bda4'); BONEB = hx('a39277'); BONED = hx('7a6a55')
PURP = hx('4f2d66'); PURPL = hx('64407e'); PURPS = hx('3d2350'); PLUM = hx('231329'); PLUMD = hx('150b19')
CRACK = hx('7ef536'); STONE = hx('7b7a80'); STONED = hx('545259'); BLACK = hx('0c0a0e')
GLOW = {2: hx('4cf21a'), 3: hx('b6ff3a'), 4: hx('effcd0')}   # toxic green edge / hot core / glint

REC = []                                                             # rig: masks recording which puts belong to a part
def unrec(m): REC[:] = [r_ for r_ in REC if r_ is not m]
def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l
    for r_ in REC: r_ |= m

def sl_of(c, R):                                     # index slice around c with radius R
    a = np.floor(np.array(c) - R - lo).astype(int); b = np.ceil(np.array(c) + R - lo).astype(int) + 1
    a = np.clip(a, 0, n); b = np.clip(b, 0, n); return tuple(slice(a[i], b[i]) for i in range(3))
def full(sl, m):
    o = np.zeros(n, bool); o[sl] = m; return o
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
    sl = sl_of((a + b) / 2, np.linalg.norm(ab) / 2 + max(ra, rb) + 1)
    x, y, z = X[sl], Y[sl], Z[sl]
    t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1] + (z - a[2]) * ab[2]) / max(ab.dot(ab), 1e-6), 0, 1)
    d = np.sqrt((x - a[0] - ab[0] * t) ** 2 + (y - a[1] - ab[1] * t) ** 2 + (z - a[2] - ab[2] * t) ** 2)
    return full(sl, d <= ra + (rb - ra) * t)
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def oell(c, S, T, N, r):                             # oriented ellipsoid (axes S,T,N unit vectors, radii r)
    sl = sl_of(c, max(r) + 1); x, y, z = X[sl] - c[0], Y[sl] - c[1], Z[sl] - c[2]
    q = 0
    for ax_, rr in zip((S, T, N), r): q = q + ((x * ax_[0] + y * ax_[1] + z * ax_[2]) / rr) ** 2
    return full(sl, q < 1)
def nrm(v): v = np.array(v, float); return v / np.linalg.norm(v)
def dil(m):
    o = m.copy()
    for ax in range(3):
        for s in (1, -1): o |= np.roll(m, s, axis=ax)
    return o

rng = np.random.RandomState(11)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
BID = 2000

def obox(c, A, B, C, h):                              # oriented box: centre c, unit axes A,B,C, half extents h
    sl = sl_of(c, float(np.linalg.norm(h)) + 1); x, y, z = X[sl] - c[0], Y[sl] - c[1], Z[sl] - c[2]
    m = np.ones(x.shape, bool)
    for ax_, hh in zip((A, B, C), h): m &= np.abs(x * ax_[0] + y * ax_[1] + z * ax_[2]) < hh
    return full(sl, m)
def rblock(c, A, B, C, h, p=4.0):                     # rounded block: superellipse in the A-C plane, flat in B
    sl = sl_of(c, float(np.linalg.norm(h)) + 1); x, y, z = X[sl] - c[0], Y[sl] - c[1], Z[sl] - c[2]
    a_ = np.abs((x * A[0] + y * A[1] + z * A[2]) / h[0]); c_ = np.abs((x * C[0] + y * C[1] + z * C[2]) / h[2])
    return full(sl, (a_ ** p + c_ ** p < 1) & (np.abs(x * B[0] + y * B[1] + z * B[2]) < h[1]))
def rbox(c, h, ch=0):                                 # axis box with chamfered vertical edges (octagon section)
    sl = sl_of(c, max(h) + 1); x, y, z = np.abs(X[sl] - c[0]), np.abs(Y[sl] - c[1]), np.abs(Z[sl] - c[2])
    m = (x < h[0]) & (y < h[1]) & (z < h[2])
    if ch: m &= (x + z) < (h[0] + h[2] - ch)
    return full(sl, m)

# ---------------------------------------------------------------- body scale: body/legs/chest/tail authored in design units, built K x bigger
K = 1.35; KX = 2.1; ZP = 10.0; LXS = 1.6 / KX                  # LXS keeps legs/claws their old width
def W(c): return np.array((c[0] * KX, c[1] * K, ZP + (c[2] - ZP) * K))
Xw, Yw, Zw, AXw, sl_world = X, Y, Z, AX, sl_of
X = Xw / KX; Y = Yw / K; Z = ZP + (Zw - ZP) / K; AX = np.abs(X)
def sl_of(c, R): return sl_world(W(c), R * KX)
# ---------------------------------------------------------------- body: heavy reptile mass, broad shoulders + chest, rump
d = sd_ell((0, 39, 6), (31.0, 23.0, 44.0))                          # long heavy barrel
d = smin(d, sd_ell((0, 46, -24), (31.5, 28.0, 21.0)), 7)            # chest / shoulders (front mass, deep + high)
d = smin(d, sd_ell((0, 57, -26), (26.0, 12.0, 14.0)), 6)            # neck root mound (broad: 3 necks)
d = smin(d, sd_ell((0, 41, 38), (27.0, 19.0, 16.0)), 6)             # rump
d = smin(d, sd_ell((0, 28, 6), (24.5, 12.5, 33.0)), 6)              # deep belly
d = smin(d, sd_ell((0, 55, -4), (25.0, 11.0, 26.0)), 9)             # back
LEGS = ((26.5, -22.0), (26.0, 39.0))
for sx in (1, -1):
    for (lx, lz) in LEGS:
        d = smin(d, sd_ell((lx * sx, 31, lz), (13.0, 15.5, 14.0)), 4)  # shoulder / thigh muscle
body = d < 0
put(body, PURP, p=BID, l=1)
put(body & (Y > 52), PURPL, p=BID, l=1)
put(body & (Y < 25), PURPS, p=BID, l=1)
# hide plates: BIG raised blocks (9 design = 12 bricks), staggered rows, random thickness = chunky stepped silhouette
PT = 11.0; zt = np.floor((Z + 200) / PT); yo = Y + 200 + 5.5 * (zt % 2); yt = np.floor(yo / PT)
inplate = (((Z + 200) % PT) < PT - 1.5) & ((yo % PT) < PT - 1.5)
tid = (yt * 1000 + zt).astype(np.int64); del yo
hsh = (tid * 2654435761) % 97
th = 1.3 + 0.65 * (hsh % 4)                                          # 1.3 .. 3.25 design thick
plate = (d >= 0) & (d < th) & inplate & (Y > 15)
col[(d < 0) & (d >= -1.6) & (Y > 15) & ~inplate] = PLUMD             # deep dark seams between the plates
pc = np.stack([PURP, PURPL, PURP * .85 + PURPS * .15])[(hsh[plate] % 3)]
col[plate] = pc; kind[plate] = 1; pid[plate] = (100000 + tid[plate]).astype(np.int32); lvl[plate] = 2
del th, hsh, inplate, zt
put(body & (Y < 19.0), PLUM, p=BID, l=1)                            # underside

# ---------------------------------------------------------------- rib cage + one round core on the chest
CHC = np.array((0, 46.0, -24.0)); CHR = np.array((31.5, 28.0, 21.0))
def chest_z(x, y):
    q = 1 - (x / CHR[0]) ** 2 - ((y - CHC[1]) / CHR[1]) ** 2
    return CHC[2] - CHR[2] * math.sqrt(max(q, 0.02))
CY = 43.0; CZ = chest_z(0, CY) - 0.5; CRAD = 13.5
CQ = K / KX
COREM = sd_ell((0, CY, CZ), (CRAD * CQ, CRAD, CRAD)) < 0
COREPID = newid(); put(COREM, CRACK, st=False, p=COREPID, l=1.5)                        # solid bright green ball (painted after shading)
put((sd_ell((0, CY, CZ - 4.0), (5.6 * CQ, 5.6, CRAD)) < 0), GLOW[3], k=3, st=False)       # tight hot centre (only glow)
RIB = newid()
def on_chest(x, y, lift): return (x, y, min(chest_z(x, y), CZ - math.sqrt(max(CRAD ** 2 - (x / CQ) ** 2 - (y - CY) ** 2, 0))) - lift)
def bez(P0, P1, P2, k=18): return [tuple((1 - t) ** 2 * np.array(P0) + 2 * (1 - t) * t * np.array(P1) + t * t * np.array(P2)) for t in np.linspace(0, 1, k)]
for sx in (1, -1):                                                    # 3 separate thick bone bars per side: sternum -> around the core side -> down
    for (ys, ye, rad) in ((CY + 12.5, CY + 2, 3.4), (CY + 1.5, CY - 9, 3.4), (CY - 9.5, CY - 19, 3.2)):
        x0 = 2.5 if ys > CY + CRAD - 3 else max(2.5, math.sqrt(max(CRAD ** 2 - (ys - CY) ** 2, 0)) - 1.0)
        P = bez((x0, ys), (CRAD + 6, ys + 1.0), (CRAD + 9, ye), 18)
        pts = [on_chest(sx * CQ * x, y, 1.8) for (x, y) in P]
        put(chain(pts, [rad] * 15 + [rad * .9, rad * .8, rad * .65]), BONEW, st=False, p=newid(), l=4)
CROSSM = (sd_ell((0, CY, CZ - .5), ((CRAD + .5) * CQ, CRAD + .5, CRAD + .5)) < 0) & ((np.abs(X) < 1.2 * CQ) | (np.abs(Y - CY) < 1.2)) & (Z < CZ)
put(CROSSM, PLUMD, st=False, p=newid(), l=1.6)                        # dark cross on the core face
pts = [on_chest(0, y, 1.8) for y in np.linspace(CY + 22, CY + CRAD - 1, 6)]  # sternum bar stops on top of the core
put(chain(pts, [3.0] * len(pts)), BONEG, st=False, p=newid(), l=5)
for sx in (1, -1):                                                    # collarbone ridges over the shoulders
    put(chain([on_chest(4 * sx, 58.0, .4), on_chest(16 * sx, 57.0, .4), (25 * sx, 51.0, -17)], [2.4, 2.2, 1.6]), BONEG, st=False, p=RIB, l=4)

# ---------------------------------------------------------------- tail: thick, back then curls UP and FORWARD into a hook
TAIL = [(0, 42, 42), (0, 35, 60), (0, 29, 78), (0, 28, 94), (0, 33, 108), (0, 44, 117), (0, 57, 118), (0, 66, 111), (0, 70, 101)]
TR = [18.0, 16.5, 15.0, 13.5, 12.0, 10.5, 9.0, 7.6, 6.4]

# ---------------------------------------------------------------- lift the body so the legs show, then short thick blocky legs
LIFT = 18
for arr in (col, kind, stud, pid, lvl):
    arr[:] = np.roll(arr, LIFT, axis=1); arr[:, :LIFT] = 0
COREM = np.roll(COREM, LIFT, axis=1); CROSSM = np.roll(CROSSM, LIFT, axis=1)
def WL(c): return W(c) + np.array((0, LIFT, 0))
dL = LIFT / K
LEGM = {}
for sx in (1, -1):
    for i, (lx, lz) in enumerate(LEGS):
        xo = (lx + 9.0) * sx; LEGM[(sx, i)] = np.zeros(n, bool); REC[:] = [LEGM[(sx, i)]]
        up = rbox((xo, 33, lz), (12.5 * LXS, 12.0, 12.5), 6)                   # thigh / upper arm column
        put(up & ((kind == 0) | (pid == BID)), PURP, p=newid(), l=1.5)
        put(rbox((xo + 1.0 * sx * LXS, 22.5, lz - 1.5), (13.5 * LXS, 3.6, 13.5), 7), PURPL, p=newid(), l=2.2)   # knee / elbow plate
        put(rbox((xo, 13.5, lz - 1), (11.5 * LXS, 6.0, 11.5), 5), PURP, p=newid(), l=1.5)                # shin
        put(rbox((xo, 7.0, lz - 1.5), (12.3 * LXS, 1.6, 12.3), 6), PURPS, p=newid(), l=2)               # ankle band
        put(rbox((xo, 3.0, lz - 4.5), (13.0 * LXS, 3.0, 12.5), 6) & (Y > 0), PURPS, p=newid(), l=1.8)    # foot
        for t, dx in enumerate((-6.6, 0, 6.6)):                         # 3 toes with big bone claws
            cxk = xo + dx * LXS; f = 1.5 if t == 1 else 0
            put(rbox((cxk, 2.6, lz - 16 - f), (2.9 * LXS, 2.6, 2.5)) & (Y > 0), PURPS, p=newid(), l=2)
            cp = newid()
            for k in range(5):
                zc = lz - 19 - f - 2.2 * k; hxk = 2.8 - .45 * k; ytop = 7.2 - 1.35 * k
                put(rbox((cxk, ytop / 2, zc), (hxk * LXS, ytop / 2, 1.15)) & (Y > 0), BONEW if k else BONEG, st=False, p=cp, l=3)
        dc = newid()                                                     # outer dew claw
        for k in range(3):
            put(rbox((xo + (12.5 + 1.8 * k) * sx * LXS, 3.0 - .8 * k, lz - 6 - 1.5 * k), ((1.6 - .3 * k) * LXS, 3.0 - .8 * k, 1.6 - .3 * k)) & (Y > 0), BONEG, st=False, p=dc, l=3)

REC[:] = []
X, Y, Z, AX, sl_of = Xw, Yw, Zw, AXw, sl_world                      # back to world units
# ---------------------------------------------------------------- big stepped bone spikes (pyramids built from shrinking box tiers)
def dspike(base, D, Sx, H, a, b, rake=.35, step=2):
    D = nrm(D); Sx = nrm(np.array(Sx, float) - D * np.dot(Sx, D)); T = nrm(np.cross(Sx, D)); p_ = newid()
    base = np.array(base, float)
    for k in range(0, int(H), step):
        t = (k + step / 2) / H
        ak = max(1.0, round(a * (1 - .88 * t))); bk = max(1.0, round(b * (1 - .88 * t)))
        c = base + D * (k + step / 2) + T * (rake * k)
        put(obox(c, Sx, T, D, (ak, bk, step / 2 + .01)), BONEW if k >= 4 else BONEG, st=False, p=p_, l=6 + k * .01)
def top_y(x, z):
    xi = int(np.floor(x - lo[0])); zi = int(np.floor(z - lo[2]))
    ys = np.where((kind[xi, :, zi] == 1) & (cy < 120))[0]
    return None if not len(ys) else lo[1] + .5 + ys.max()
SPIKEM = np.zeros(n, bool); REC[:] = [SPIKEM]
for z, H, a, b in ((-6, 32, 6, 12), (9, 38, 6.5, 14), (24, 40, 6.5, 14), (39, 38, 6.5, 14), (53, 34, 6, 12), (66, 29, 5.5, 11)):
    yt = top_y(0, z)
    if yt is not None: dspike((0, yt - 4, z), (0, 1, 0), (1, 0, 0), H + 4, a, b)
TAILM = np.zeros(n, bool); REC[:] = [TAILM]
TW = [WL(p) for p in TAIL]
tm = chain(TW, [r * K for r in TR])                                    # tail built in world units (round section)
put(tm & ((kind == 0) | (pid == BID)), PURP, p=newid(), l=1)
def tail_at(s):                                                       # point + tangent at arc fraction s along the tail polyline
    seg = np.array([np.linalg.norm(TW[i + 1] - TW[i]) for i in range(len(TW) - 1)]); cum = np.concatenate([[0], np.cumsum(seg)])
    u = s * cum[-1]; i = min(int(np.searchsorted(cum, u) - 1), len(seg) - 1); i = max(i, 0); f = (u - cum[i]) / seg[i]
    r = TR[i] + (TR[i + 1] - TR[i]) * f
    return TW[i] + (TW[i + 1] - TW[i]) * f, nrm(TW[i + 1] - TW[i]), r * K
CURL = WL((0, 50, 100))
for s_ in np.linspace(.04, .93, 13):                                  # chunky raised hide rings = blocky tail segments
    p, tg, r = tail_at(s_); Sx = np.array((1.0, 0, 0)); Nn = nrm(np.cross(tg, Sx))
    put(obox(p, Sx, tg, Nn, (r + 1.6, 3.6, r + 1.6)) & cap(p - tg * 4, p + tg * 4, r + 1.0, r + 1.0) & (kind == 0), PURPL if int(s_ * 100) % 2 else PURP, p=newid(), l=1.4)
for s in np.linspace(.16, .88, 11):                                  # tail spikes: smaller than the back row, evenly spaced
    p, tg, r = tail_at(s); H, a, b = 18 - 6 * s, 3.5 - 1 * s, 6.5 - 2 * s
    D = np.array((0, 1.0, 0)) if s < .3 else nrm(np.array((0, -tg[2], tg[1])))
    if D[1] < -.75: continue
    D = nrm(D + np.array((0, .45, 0)))
    dspike(p + D * (r - 4), D, (1, 0, 0), H + 4, a, b, rake=.25)
TE = TW[-1]; TD = nrm(TW[-1] - TW[-2])                                  # big tail-end spike continuing the hook
put(rbox(tuple(TE), (6.5, 6.5, 6.5), 4), BONEG, st=False, p=newid(), l=5.5)
dspike(TE - TD * 3, TD, (1, 0, 0), 30, 6, 6, rake=0)
dspike(TE, nrm(TD + np.array((0, 0, 1.2))), (1, 0, 0), 14, 3, 3.5, rake=0)
for sxx in (1, -1): dspike(TE, nrm(TD * .4 + np.array((sxx * 1.0, .3, .6))), (0, 1, 0), 13, 3, 3, rake=0)

# ---------------------------------------------------------------- necks: THICK purple S-curves with chunky bone vertebra plates
def catmull(P, k=10):
    P = [np.array(p, float) for p in P]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        for t in np.linspace(0, 1, k, endpoint=False):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return out
NECKS = [dict(P=[(0, 92, -40), (0, 118, -50), (0, 145, -38), (0, 170, -26), (0, 190, -34), (0, 200, -50)], r0=16.0, r1=12.5, yaw=0, pitch=-12, sc=2.2)]
for s in (1, -1):
    NECKS.append(dict(P=[(34 * s, 90, -38), (54 * s, 102, -66), (70 * s, 120, -86), (80 * s, 140, -90), (86 * s, 158, -84), (88 * s, 168, -98)],
                      r0=15.5, r1=12.0, yaw=22 * s, pitch=-6, sc=2.1))
for nk in NECKS:
    pts = catmull(nk['P'], 9); L_ = len(pts)
    rr = [nk['r0'] + (nk['r1'] - nk['r0']) * (i / (L_ - 1)) for i in range(L_)]
    NID = newid(); nk['M'] = np.zeros(n, bool); REC[:] = [nk['M']]
    nm_ = chain(pts, rr)
    put(nm_ & ((kind == 0) | (pid == BID)), PURP, p=NID, l=1)
    put(nm_ & ((pid == NID)) & (Y < 100), PURPS, p=NID, l=1)
    nk['pts'] = pts; nk['rr'] = rr; nk['NID'] = NID
for nk in NECKS:                                                      # vertebra plates: chunky blocks every ~5.5 units on the front, nubs on the back
    pts, rr = nk['pts'], nk['rr']; acc = 4.0; k_ = 0; REC[:] = [nk['M']]
    a = math.radians(nk['yaw']); F = np.array((math.sin(a) * .6, 0, -1.0))
    for i in range(1, len(pts) - 3):
        acc += np.linalg.norm(pts[i] - pts[i - 1])
        if acc < 10.5: continue
        acc = 0.0; k_ += 1
        T = nrm(pts[i + 1] - pts[i - 1]); N = nrm(F - np.dot(F, T) * T); S = nrm(np.cross(T, N))
        r = rr[i]; p_ = newid(); c0 = np.array(pts[i])
        put(rblock(c0 + N * (r * .45), S, T, N, (r * 1.08, 2.7, r * .55 + 2.2)), BONEW if k_ % 2 else BONEG, st=False, p=p_, l=4)   # rounded bone block, 2 proud
        q_ = newid(); i2, o2 = r * .3, r + 3.4                          # back nub / plate
        put(obox(c0 - N * (i2 + o2) / 2, S, T, N, (r * .55, 1.8, (o2 - i2) / 2)), BONEG if k_ % 2 else BONEW, st=False, p=q_, l=3.5)

# ---------------------------------------------------------------- skulls: bone-white dragon skulls, jaws open, horns swept back
def head(H, yaw, pitch, sc):
    a = math.radians(yaw); p = math.radians(pitch)
    f = np.array((math.sin(a), 0, -math.cos(a))); r = np.array((math.cos(a), 0, math.sin(a)))
    R = 34 * sc; sl = sl_of(H, R)
    dx, dy, dz = X[sl] - H[0], Y[sl] - H[1], Z[sl] - H[2]
    wb = -(dx * f[0] + dz * f[2]); lx = (dx * r[0] + dz * r[2]) / sc
    ly = (dy * math.cos(p) - wb * math.sin(p)) / sc; lz = (wb * math.cos(p) + dy * math.sin(p)) / sc
    ax_ = np.abs(lx)
    def L2W(x, y, z):                                                 # local -> world (for lights / chains)
        x, y, z = x * sc, y * sc, z * sc
        wy = y * math.cos(p) + z * math.sin(p); wb_ = z * math.cos(p) - y * math.sin(p)
        return np.array(H) + r * x + np.array((0, wy, 0)) - f * wb_
    def F(m): return full(sl, m)
    def lcap(pts, radii):                                             # chain in local coords, mirrored in x
        m = np.zeros(n, bool)
        for s in (1, -1):
            w = [L2W(s * q[0], q[1], q[2]) for q in pts]; m |= chain(w, [x_ * sc for x_ in radii])
        return m
    HID = newid()
    cran = (ax_ / 8.0) ** 6 + (np.abs(ly - 5.8) / 6.6) ** 6 + (np.abs(lz - 3.5) / 7.8) ** 6 < 1
    tp = np.interp(lz, [-21, -14, -6, 0], [5.0, 6.5, 8.5, 10.0]); sw = np.interp(lz, [-21, -12, -2, 2], [4.0, 5.0, 6.4, 7.0])
    snout = (ax_ < sw) & (ly > 2.0) & (ly < tp) & (lz > -21.5) & (lz < 2) & ~((ax_ > sw - 1) & (ly > tp - 1) & (lz < -18))
    skull = F(cran | snout)
    put(skull, BONEW, st=True, p=HID, l=3)
    put(skull & F(ly < 4.0), BONEG, st=True, p=HID, l=3)                                              # upper jaw rim
    put(skull & F((ax_ > sw - 1.2) & (lz < -2) & (ly > 4.0) & (ly < 5.0)), BONEB, st=False, p=HID, l=3)  # cheek line
    # lower jaw: hinged at (ly 2, lz 3), opened 34 deg
    ja = math.radians(-34); hy, hz = 2.0, 3.0
    jy = (ly - hy) * math.cos(ja) + (lz - hz) * math.sin(ja); jz = (lz - hz) * math.cos(ja) - (ly - hy) * math.sin(ja)
    jw = np.interp(jz, [-21, -8, 0, 4], [2.8, 4.0, 5.2, 5.6])
    jaw = (ax_ < jw) & (jy > -4.2) & (jy < -.5) & (jz > -20.5) & (jz < 4) & ~((ax_ > jw - 1) & (jy < -3.2))
    JID = newid(); JM = np.zeros(n, bool); REC.append(JM)
    put(F(jaw), BONEG, st=True, p=JID, l=2.5)
    put(F(jaw & (jy < -2.6)), BONEB, st=True, p=JID, l=2.5)
    unrec(JM)
    # mouth: dark gullet between the jaws (set back, so the teeth stand in front of it)
    mouth = (ax_ < np.minimum(sw, jw) - 1.3) & (ly < 2.2) & (jy > -.6) & (lz > -15) & (lz < 4.5)
    put(F(mouth) & (kind == 0), PLUM, st=False, p=newid(), l=1)
    put(F(mouth & (lz < -6)) & (kind != 0) & (pid != HID) & (pid != JID), PLUMD, st=False)
    # teeth: upper fangs hang down from the rim, lower ones rise from the jaw
    TEETH = newid()
    for zt, Ln in ((-20.0, 4.6), (-16.5, 3.4), (-13.0, 4.0), (-9.5, 3.0), (-6.0, 3.4), (-2.5, 2.4)):
        wz = float(np.interp(zt, [-21, -12, -2, 2], [4.0, 5.0, 6.4, 7.0])) - 1.0
        put(lcap([(wz, 2.6, zt), (wz - .2, 2.6 - Ln * .55, zt + .3), (wz - .3, 2.6 - Ln, zt + .6)], [1.05, .75, .35]), BONEW, st=False, p=TEETH, l=5)
    REC.append(JM)
    for jt, Ln in ((-19.0, 3.8), (-15.0, 3.0), (-11.0, 3.6), (-7.0, 2.8), (-3.0, 2.4)):
        wz = float(np.interp(jt, [-21, -8, 0, 4], [2.8, 4.0, 5.2, 5.6])) - 1.0
        def J2L(y_, z_):                                                  # jaw coords -> head local
            return (hy + y_ * math.cos(ja) - z_ * math.sin(ja), hz + z_ * math.cos(ja) + y_ * math.sin(ja))
        y0, z0 = J2L(-.6, jt); y1, z1 = J2L(-.6 + Ln * .55, jt - .2); y2, z2 = J2L(-.6 + Ln, jt - .4)
        put(lcap([(wz, y0, z0), (wz - .2, y1, z1), (wz - .3, y2, z2)], [1.0, .7, .35]), BONEW, st=False, p=TEETH, l=5)
    unrec(JM); HJ.append(JM)
    # nostrils
    put(skull & F((ax_ > .8) & (ax_ < 2.4) & (ly > tp - 1.5) & (lz > -20) & (lz < -17.5)), PLUMD, st=False)
    # brow: heavy bone ridge over the eye, stepping down toward the snout (angry)
    put(F((ax_ > 2.5) & (ax_ < 7.8) & (ly > 8.6 + .12 * (ax_ - 2.5)) & (ly < 10.6 + .2 * (ax_ - 2.5)) & (lz > -5.5) & (lz < 1.5)), BONEW, st=False, p=newid(), l=4.5)
    # eye socket: carve a recessed pit at the brow corner, glow on its floor (flush, visible from front + side)
    E = F((ax_ > 3.8) & (ax_ < 9) & (ly > 5.8) & (ly < 8.4) & (lz > -4.0) & (lz < -.2) & ~((ax_ < 4.5) & (ly < 6.4))) & (kind == 1) & (pid == HID)
    kind[E] = 0
    flo = dil(E) & ~E & (kind == 1) & (pid == HID)
    rim = dil(dil(E)) & ~dil(E) & (kind == 1) & (pid == HID)
    put(rim & F(ly < 8.6), BONEB, st=False, p=HID, l=3)
    put(flo, GLOW[2], k=2, st=False)                                   # EYEFIX: whole socket floor = one flat glow colour (was green floor + hot centre)
    # horns: two big ones swept back + up, a lower cheek horn, jagged crest spikes on the cranium
    HN = newid()
    put(lcap([(4.6, 9.5, 3.0), (5.0, 12.2, 9.5), (5.2, 14.4, 15.5), (5.2, 15.8, 20.5)], [3.6, 2.9, 1.9, .9]), BONEW, st=False, p=HN, l=6)
    put(lcap([(6.4, 5.4, 7.0), (6.8, 6.4, 12.0), (7.0, 7.6, 16.0)], [2.6, 1.8, .9]), BONEG, st=False, p=HN, l=6)
    for zc_, hh in ((0.0, 3.0), (6.0, 2.6)):
        yb = float(np.interp(zc_, [-21, -14, -6, 0, 3.5, 9], [5, 6.5, 8.5, 10, 11.4, 10]))
        put(lcap([(1.8, yb - .6, zc_), (1.8, yb + hh * .6, zc_ + 1.6), (1.8, yb + hh, zc_ + 2.8)], [1.9, 1.4, .8]), BONEW, st=False, p=HN, l=6)
    return [L2W(s * 5.6, 7.0, -2.0) for s in (1, -1)]
EYES = []; HPOS = []; HC = []; HJ = []
for nk in NECKS:
    nk['HM'] = np.zeros(n, bool); REC[:] = [nk['HM']]
    pts = nk['pts']; T = nrm(pts[-1] - pts[-2])
    a = math.radians(nk['yaw']); fwd = np.array((math.sin(a), 0, -math.cos(a)))
    H = pts[-1] + fwd * 2.0 + np.array((0, 1.0, 0))
    nk['H'] = H; EYES += head(H, nk['yaw'], nk['pitch'], nk['sc']); HPOS.append(H); HC.append(H + fwd * 5 * nk['sc'] + np.array((0, 6 * nk['sc'], 0)))


REC[:] = []
# ---------------------------------------------------------------- connectivity: keep only bricks 26-connected to the main body
def keep_main():
    from collections import deque
    sol_ = kind > 0; idx = np.argwhere(sol_); lab = np.full(n, -1, np.int32); comp = []
    offs = [(a_, b_, c_) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1) for c_ in (-1, 0, 1) if (a_, b_, c_) != (0, 0, 0)]
    for st_ in map(tuple, idx):
        if lab[st_] >= 0: continue
        cid = len(comp); lab[st_] = cid; q = deque([st_]); size = 0
        while q:
            i_, j_, k_ = q.popleft(); size += 1
            for a_, b_, c_ in offs:
                u_, v_, w_ = i_ + a_, j_ + b_, k_ + c_
                if 0 <= u_ < n[0] and 0 <= v_ < n[1] and 0 <= w_ < n[2] and sol_[u_, v_, w_] and lab[u_, v_, w_] < 0:
                    lab[u_, v_, w_] = cid; q.append((u_, v_, w_))
        comp.append(size)
    main = int(np.argmax(comp)); drop = sol_ & (lab != main)
    if drop.any():
        e_ = np.argwhere(drop); print('VOX_OK dropped bbox', (lo + e_.min(0)).tolist(), (lo + e_.max(0)).tolist())
    kind[drop] = 0
    print('VOX_OK connectivity: components', len(comp), 'dropped bricks', int(drop.sum()))
keep_main()

# ---------------------------------------------------------------- seams + light + palette
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.clip(.72 + .42 * (Y / 50.0), .72, 1.12)[..., None]
col = np.clip(col, 0, 1)
# ---------------------------------------------------------------- core: solid bright green ball (after shading so it keeps its hue)
col[COREM & (kind == 1) & (pid == COREPID)] = CRACK
# ---------------------------------------------------------------- green glow cracks: bold forked lightning bolts across the hide
def crack(side, knots, xmin, ylim=(0, 999), w=1.5):
    ys_ = lo[1] + .5 + np.arange(n[1]); zs_ = lo[2] + .5 + np.arange(n[2]); YY, ZZ = np.meshgrid(ys_, zs_, indexing='ij')
    dm = np.full(YY.shape, 1e9)
    for (y0_, z0_), (y1_, z1_) in zip(knots[:-1], knots[1:]):
        ay, az = y1_ - y0_, z1_ - z0_; t = np.clip(((YY - y0_) * ay + (ZZ - z0_) * az) / (ay * ay + az * az), 0, 1)
        dm = np.minimum(dm, np.hypot(YY - y0_ - ay * t, ZZ - z0_ - az * t))
    for yi, zi in np.argwhere((dm < w) & (YY > ylim[0]) & (YY < ylim[1])):
        row = np.where((kind[:, yi, zi] == 1) & ((cx * side) > xmin))[0]
        if not len(row): continue
        i = row.max() if side > 0 else row.min()
        for j in (i, i - side):
            if kind[j, yi, zi] == 1 and col[j, yi, zi].max() < .6: col[j, yi, zi] = CRACK
BOLTS = [([(94, -36), (84, -31), (82, -22), (72, -18), (64, -9)], [(82, -22), (74, -30), (66, -33)]),
         ([(98, -4), (88, 2), (86, 12), (76, 16), (66, 26)], [(86, 12), (78, 6), (70, 3)]),
         ([(96, 30), (88, 36), (86, 46), (76, 48), (68, 58)], [(86, 46), (81, 56), (76, 63)]),
         ([(104, 54), (96, 60), (94, 68), (86, 72)], [(94, 68), (90, 60)])]
for sx in (1, -1):
    for main_, fork_ in BOLTS:
        for kn in (main_, fork_): crack(sx, kn, 16, (52, 120), 1.6 if kn is main_ else 1.2)
    for (lx, lz) in LEGS:                                             # one forked bolt down each leg
        zw = ZP + (lz - ZP) * K
        crack(sx, [(50, zw - 3), (42, zw + 3), (35, zw - 1), (27, zw + 4), (18, zw)], 30, (12, 54), 1.4)
        crack(sx, [(35, zw - 1), (29, zw - 6)], 30, (12, 54), 1.1)


PAL = np.array([hx(h) for h in ('f6eedb', 'e3d8bd', 'c6baa0', 'a39277', '76674f',          # bone white light / main / grey / beige / beige dark
                                 '6f4a8a', '553270', '432758', '301b40', '1f1128', '120a16',  # purple light / main / side / dark / plum / deep
                                 '807f86', '58565d', '0b090d', '7ef536')])                             # stone / stone dark / black
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- mesh: exposed faces (vertex colours) + studs
solid = kind > 0
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb

STUD_PNG = os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png')
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
body = build('Hydra', kind == 1, True)
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
    for i, e in enumerate(EYES):                                              # eye lights: toxic green spill on brow + snout
        L = bpy.data.objects.new('EyeLight%d' % i, bpy.data.lights.new('EyeLight%d' % i, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 1400; L.data.color = (.298, .949, .102); L.data.shadow_soft_size = 1.0
        L.location = B(*e)
    L = bpy.data.objects.new('CoreLight', bpy.data.lights.new('CoreLight', 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 900; L.data.color = (.35, 1.0, .12); L.location = B(*WL((0, 34, -48)))
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
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.32, .32, .34, 1)
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
    for nm, az, el, os_, tg in (('ortho_front', 0, 0, 260, (0, 110, 0)), ('ortho_side', 90, 0, 380, (0, 110, 25)),
                                ('ortho_back', 180, 0, 260, (0, 110, 0)), ('ortho_top', 0, 89.9, 380, (0, 110, 25))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=os_)
    for nm, a in (('rest_34', ((0, 118, 10), 540, -38, 14)), ('tail', (tuple(TE), 130, 50, 20)), ('rest_side', ((0, 112, 22), 580, 90, 4)), ('rest_front', ((0, 118, -10), 560, 0, 6)),
                  ('rest_back', ((0, 108, 25), 500, 160, 12)),
                  ('face', (tuple(HC[0]), 170, 0, 4)), ('headside', (tuple(HC[2]), 200, -90, 4)), ('head34', (tuple(HC[0]), 190, -38, 8)),
                  ('footfront', ((-75, 10, -48), 110, 0, 6)), ('chest', ((0, 64, -62), 130, -8, 6))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): bones in brick (= world) coords, L = +x
def L2W_(nk, x, y, z):                                              # head local -> world (same maths as head())
    a = math.radians(nk['yaw']); p = math.radians(nk['pitch']); sc = nk['sc']
    f = np.array((math.sin(a), 0, -math.cos(a))); r = np.array((math.cos(a), 0, math.sin(a)))
    x, y, z = x * sc, y * sc, z * sc
    return tuple(np.array(nk['H']) + r * x + np.array((0, y * math.cos(p) + z * math.sin(p), 0)) - f * (z * math.cos(p) - y * math.sin(p)))
def T_(c): return tuple(float(v) for v in c)
ja = math.radians(-34)
def J2L(y_, z_): return (2.0 + y_ * math.cos(ja) - z_ * math.sin(ja), 3.0 + z_ * math.cos(ja) + y_ * math.sin(ja))
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', T_(WL((0, 41, 38))), T_(WL((0, 41, 6)))), ('spine', 'hips', T_(WL((0, 41, 6))), T_(WL((0, 48, -24))))]
OVR = brick_rig.limb(X, Y, Z, SPIKEM, RIG[1:3])
TP = [TW[0], TW[2], TW[4], TW[5], TW[7], TW[-1] + TD * 30]
TB = [('tail_%d' % (i + 1), 'hips' if i == 0 else 'tail_%d' % i, T_(TP[i]), T_(TP[i + 1])) for i in range(5)]
RIG += TB; OVR += brick_rig.limb(X, Y, Z, TAILM, TB)
for sx, sd in ((1, 'L'), (-1, 'R')):
    for i, (lx, lz) in enumerate(LEGS):
        xo = (lx + 9.0) * sx; fb = 'F' if i == 0 else 'B'
        P_ = [W((xo, 45, lz)), W((xo, 22.5, lz - 1)), W((xo, 7, lz - 1.5)), W((xo, 2, lz - 26))]
        ch = [('leg%s%s_%s' % (fb, sd, nm), ('spine', 'hips')[i] if j == 0 else 'leg%s%s_%s' % (fb, sd, ('up', 'low')[j - 1]), T_(P_[j]), T_(P_[j + 1]))
              for j, nm in enumerate(('up', 'low', 'foot'))]
        RIG += ch; OVR += brick_rig.limb(X, Y, Z, LEGM[(sx, i)], ch)
HO = []
for nk, nmN in zip(NECKS, ('C', 'L', 'R')):
    pts = np.array(nk['pts']); s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    P_ = [pts[np.argmin(np.abs(s_ - s_[-1] * f))] for f in (0, .25, .5, .75)] + [np.array(nk['H'])]
    ch = [('neck%s_%d' % (nmN, i + 1), 'spine' if i == 0 else 'neck%s_%d' % (nmN, i), T_(P_[i]), T_(P_[i + 1])) for i in range(4)]
    RIG += ch + [('head%s' % nmN, 'neck%s_4' % nmN, T_(nk['H']), L2W_(nk, 0, 6, -21)),
                 ('jaw%s' % nmN, 'head%s' % nmN, L2W_(nk, 0, 2, 3), L2W_(nk, 0, *J2L(-2, -20)))]
    OVR += brick_rig.limb(X, Y, Z, nk['M'], ch)
    HO += [(nk['HM'], 'head%s' % nmN)]
OVR += HO + [(jm, 'jaw%s' % nmN) for jm, nmN in zip(HJ, ('C', 'L', 'R'))]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'neckC_2': (15, 0, 0), 'headC': (-15, 0, 0), 'jawC': (25, 0, 0), 'neckL_1': (0, 0, 25), 'jawL': (20, 0, 0),
                       'neckR_3': (-20, 0, 0), 'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail_2': (0, 0, 25)},
                 render='render' in argv)
print('BL_OK')
