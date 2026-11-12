# Frost Mammoth (stud-voxel boss, brick pipeline). Reworked from the skill's War Rhino example.
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference = concept_sheet.jpg (same folder). Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs).
# Run: powershell -File <skill>\scripts\run_brick.ps1 frost_mammoth.py
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'FrostMammoth'

lo = np.array((-38.0, -0.5, -92.0)); hi = np.array((38.0, 80.5, 52.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
FUR_D = hx('3e271d'); FUR_M = hx('7a4f3d'); FUR_L = hx('9a6a50'); FUR_S = hx('28180f'); FUR_M2 = hx('664231'); DEEP = hx('170e0a')
BLACK = hx('0c0e12'); IVORY = hx('efe0c0'); IVORY_S = hx('c7b28c'); FOOT = hx('2e1d16')
ICE_L = hx('c3daf6'); ICE = hx('9fbee8'); ICE_S = hx('7898c6')
GLOW = {2: hx('16b6ee'), 3: hx('7eeaff'), 4: hx('e8fdff')}   # crystal / bright facet + eye centre / white glint

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def chain_t(pts, radii, sym=False):                 # capsule chain -> (mask, t along the whole chain 0..1); sym = mirrored in x
    pts = [np.array(p, float) for p in pts]; L = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    acc = np.concatenate([[0], np.cumsum(L)]) / sum(L)
    XX = AX if sym else X
    best = np.full(n, 1e9); T = np.zeros(n)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a
        t = np.clip(((XX - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
        dd = np.sqrt((XX - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2) - (radii[i] + (radii[i + 1] - radii[i]) * t)
        w = dd < best; best[w] = dd[w]; T[w] = acc[i] + (acc[i + 1] - acc[i]) * t[w]
    return best <= 0, T
def chain(pts, radii, sym=False): return chain_t(pts, radii, sym)[0]
def col4(x, z, hx_, hz_):
    return ((AX - x) / hx_) ** 4 + ((Z - z) / hz_) ** 4 < 1

def hashv(a, b, s=0):                                # deterministic 0..1 per integer cell
    v = np.sin(a * 12.9898 + b * 78.233 + s * 37.719) * 43758.5453
    return v - np.floor(v)
SX = np.floor(X / 2); SZ = np.floor(Z / 2)          # 2-voxel strips (fur strands / frost drips)
RAG = hashv(SX, SZ, 1)

# ---------------------------------------------------------------- body: high domed head, big shoulder hump, back sloping down to a low round rump
d = sd_ell((0, 39, 6), (20, 14, 21))                                # barrel (belly ~25)
d = smin(d, sd_ell((0, 48, -10), (21, 15.5, 14)), 6)                # massive shoulders / hump (top ~63)
d = smin(d, sd_ell((0, 44, 8), (19, 11.5, 15)), 6)                # back sloping down ...
d = smin(d, sd_ell((0, 37, 24), (17.5, 10.5, 10.5)), 6)             # ... to the low rump (top ~47)
d = smin(d, sd_ell((0, 48, -26), (14, 12, 9)), 5)                   # neck into the head
d = smin(d, sd_ell((0, 58, -33), (14, 12, 10.5)), 4)              # high domed skull (top ~70)
d = smin(d, sd_ell((0, 46, -39), (12, 11, 6.5)), 3)                 # face plate (eyes / trunk root)
for sx in (1, -1):
    d = smin(d, sd_ell((13.5 * sx, 33, -12), (8, 11, 8)), 3)      # shoulder / upper front leg
    d = smin(d, sd_ell((13.5 * sx, 33, 21), (8, 11, 8.5)), 3)     # thigh
body = d < 0
put(body, FUR_D, p=1, l=0)
LEGS = ((13.5, -12), (13.5, 21))
dleg = np.full(n, 1e9)                                              # leg pillars (rounded squares) as a distance field
for (lx, lz) in LEGS:
    q = (((AX - lx) / 8.2) ** 4 + ((Z - lz) / 8.4) ** 4) ** .25
    dleg = np.minimum(dleg, (q - 1) * 8.2)
legm = (dleg < 0) & (Y > 3) & (Y < 32)
put(legm & (kind == 0), FUR_D, p=1, l=0)

# hanging fur tiers: 7-high bands whose bottoms are big zigzag teeth (stepped strand clumps); the coat swells toward
# each band's bottom so every tier overhangs the one below = real brick steps. Body + legs share the bands.
U = Z + 1.6 * X + 12 * hashv(np.floor((74 - Y) / 9), 0, 21)                                                      # runs along every face (side: z, front/back: x)
TP = 12.0; tri = np.abs(((U / TP) % 1) - .5) * 2                     # 0 at tooth tip .. 1 between teeth
tooth = (5.0 + 5.0 * hashv(np.floor(U / TP), 1, 12)) * (1 - tri) + 2.0 * hashv(np.floor(U / TP), 0, 11)
fy = 74 - Y - tooth
tk = np.floor(fy / 9.0); frac = (fy - tk * 9.0) / 9.0               # 0 top of band .. 1 bottom (tooth tip)
coat = (d < .3 + 3.6 * frac) & (Y > 17) & (Z > -36)
legcoat = (dleg < .3 + 2.6 * frac) & (Y > 10) & (Y < 34)
coatall = (coat | legcoat) & ~body & ~legm
for k_ in np.unique(tk[coatall]).astype(int):
    m_ = coatall & (tk == k_)
    put(m_, FUR_M if k_ % 2 == 0 else FUR_M2, p=100 + k_, l=-k_)
    put(m_ & (frac > .75) & (tri < .4), FUR_L, p=100 + k_, l=-k_)    # lighter tooth tips
put(coatall & (frac < .2), FUR_D)                                                          # shadow line under each tier lip

# belly fringe: ragged strand clumps hanging below the barrel (jagged under-silhouette, also between the legs)
solb = (kind == 1) & (Y > 14)
bot = np.where(solb, Y, 1e9).min(axis=1)                             # lowest body/coat voxel per (x, z)
U0 = U[:, 0, :] if False else (Z + 1.6 * X)[:, 0, :]
tri0 = np.abs(((U0 / 6.0) % 1) - .5) * 2
hang = np.floor((2 + 7 * hashv(np.floor(U0 / 6.0), 3, 13)) * (1 - tri0) + 1)
has = bot < 1e8
fr = has[:, None, :] & (Y < bot[:, None, :]) & (Y >= (bot - hang)[:, None, :]) & (Y > 11) & (kind == 0) & ~legm
put(fr, FUR_M, p=150, l=-30)
put(fr & (Y < (bot - hang + 1.5)[:, None, :]), FUR_L, p=150, l=-30)
put(fr & (Y > (bot - 1.5)[:, None, :]), FUR_D, p=150, l=-30)

# ---------------------------------------------------------------- legs: thick fur pillars, dark feet, ivory toenails
for (lx, lz) in LEGS:
    put(col4(lx, lz, 8.7, 8.9) & (Y > 3) & (Y < 6) & ((Y > 4) | (RAG > .5)), FUR_M, p=201, l=-19)   # shaggy ankle cuff
    put(col4(lx, lz, 9.0, 9.2) & (Y > -1) & (Y < 3.5), FOOT, st=False)                              # foot pad
    zf = lz - 9.2
    for (a, b) in ((lx - 7, lx - 3.5), (lx - 2, lx + 2), (lx + 3.5, lx + 7)):
        put(box(a, b, -1, 3.5, zf - 1.5, zf + 2.5), IVORY, st=False)                               # front nails
        put(box(a, b, -1, .5, zf - 1.5, zf + 2.5), IVORY_S, st=False)
    put(box(lx + 8.9, lx + 10, -1, 3.5, lz - 3, lz + 1), IVORY, st=False)                          # outer side nail
    put(box(lx - 10, lx - 8.9, -1, 3.5, lz - 3, lz + 1), IVORY, st=False)                          # inner side nail
    # frost band round the knee
    put(col4(lx, lz, 11.5, 11.7) & (Y > 8) & (Y < 15) & (kind == 1) & (Y < 9 + 6 * hashv(np.floor(X / 3), np.floor(Z / 3), 14)) & (hashv(np.floor(X / 3), np.floor(Z / 3), 15) > .3), ICE, p=300, l=5)

# ---------------------------------------------------------------- head
# ears: small flaps on the sides of the skull
for y in range(45, 56):
    w = 3.4 - abs(y - 50) * .4
    put((AX > 13.5) & (AX < 17.5) & (np.abs(Y - y) < .5) & (np.abs(Z + 28) < w), FUR_M, p=400, l=2)
    if 47 <= y <= 53: put((AX > 16) & (AX < 17.5) & (np.abs(Y - y) < .5) & (np.abs(Z + 28) < w - 1.2), FUR_S, p=400, l=2)
# brow: heavy stepped ridge over the eyes, inner end lower (angry V)
BR = 410
for (xa, xb, y0, y1) in ((2, 6.5, 49.5, 52.5), (6, 10, 50.5, 53.5), (9.5, 13.5, 51.5, 54.5)):
    m_ = box(xa, xb, y0, y1, -48, -30) & ~body & (sd_ell((0, 50, -40), (14.5, 8, 8.5)) < 0)
    put(m_, FUR_M, p=BR, l=4)
# vertical ridge plates down the forehead
put(box(0, 2.5, 49.5, 60.5, -48, -30) & ~body & (sd_ell((0, 55, -38), (6, 8, 8.5)) < 0), FUR_M, p=420, l=3)

# eyes: flush with the face, found on the surface, nothing in front of them
def surf_z(x, y):
    xi = int(round(x - lo[0] - .5)); yi = int(round(y - lo[1] - .5))
    c = np.where(kind[xi, yi, :] > 0)[0]
    return c.min() if len(c) else None
EYE = []
def xidx(x): return int(round(x - lo[0] - .5))
for sx in (1, -1):
    for (xa, xb, y, row) in ((5, 8, 47, 0), (5, 9, 48, 0), (7, 10, 49, 1)):   # slit 3 rows, outer corner high
        for x in range(xa, xb + 1):
            xi = xidx(sx * (x + .5)); yi = int(y - lo[1] - .5)
            c = np.where(kind[xi, yi, :] > 0)[0]
            if not len(c): continue
            zi = c.min()
            k = 2                                                    # one flat eye colour (no centre / glint)
            for dz in (0, 1):
                col[xi, yi, zi + dz] = GLOW[k]; kind[xi, yi, zi + dz] = k
            EYE.append((xi, yi, zi))
EYESET = {(a, b) for a, b, _ in EYE}
for (xi, yi, zi) in EYE:                                             # dark socket ring on the surface around the slit
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        a, b = xi + dx, yi + dy
        if (a, b) in EYESET: continue
        c = np.where(kind[a, b, :] > 0)[0]
        if len(c) and kind[a, b, c.min()] == 1:
            col[a, b, c.min()] = BLACK; pid[a, b, c.min()] = 0; stud[a, b, c.min()] = False

# ---------------------------------------------------------------- trunk: raised and curled up in front of the face, ringed segments
TR, tt = chain_t([(0, 44, -42), (0, 38, -48), (0, 32, -53), (.5, 29, -60), (1, 31, -67), (1.5, 38, -72), (2, 47, -74),
                  (4.5, 56, -72.5), (8, 63, -68), (9.5, 66, -62), (9, 62, -58)], [6.0, 5.6, 5.2, 4.8, 4.3, 3.9, 3.6, 3.4, 3.2, 2.9, 2.6])
TR &= kind == 0
ringc = ((tt * 24) % 1) < .28
put(TR, FUR_M, p=500, l=1)
put(TR & ringc, FUR_D, p=501, l=0)
put(TR & (tt > .97), FUR_S)
# ---------------------------------------------------------------- tusks: huge ivory, sweeping forward-out-down then up, ice-crystal tips
TU, ut = chain_t([(8.5, 40, -41), (12, 33, -48), (15, 28.5, -57), (16.5, 28.5, -66), (16.5, 33, -75), (15, 41, -81), (13, 49, -83)],
                 [5.0, 4.9, 4.6, 4.2, 3.7, 2.9, 1.6], sym=True)
TUo = TU & (kind == 0)
put(TUo & (ut < .74), IVORY, st=False)
put(TUo & (ut < .74) & (np.floor(ut * 18) % 2 == 1) & (Y < 34 + 0 * ut), IVORY_S, st=False)     # segment bands (shadowed underside)
put(TUo & (ut < .74) & (np.floor(ut * 18) % 3 == 1), IVORY_S, st=False)
# ice tip: crystal sheath + a few shards on the last quarter
ICEC = chain([(16.5, 36, -76.5), (15, 41, -81), (13, 49, -83), (12, 54, -83)], [3.1, 2.6, 1.8, .4], sym=True)
for (a, b, r) in (((17, 38, -77), (19.5, 41, -78), 1.2), ((15, 44, -82), (17, 46, -86), 1.0)):
    ICEC |= chain([a, b], [r, .4], sym=True)
put(ICEC & ((kind == 0) | TU), GLOW[2], k=2, st=False)
put(ICEC & ((kind == 2)) & (hashv(np.floor(Y / 2), np.floor(Z / 2), 6) > .55), GLOW[3], k=3, st=False)

# ---------------------------------------------------------------- tail
put(chain([(0, 40, 38), (0, 36, 41), (0, 31, 42)], [1.8, 1.5, 1.3]) & (kind == 0), FUR_D)
put(sd_ell((0, 28.5, 42), (2.2, 3.2, 2.2)) < 0, FUR_S)

# ---------------------------------------------------------------- frost cap: icy layer over the top of the back + skull with ragged drips
sol = kind == 1
ys = np.where(sol & (pid != 500), Y, -1e9).max(axis=1)              # top height per (x, z) (trunk excluded)
topY = ys[:, None, :]
DX = np.floor(X / 4); DZ = np.floor(Z / 4)
depth = 2 * np.floor((3 + 15 * hashv(DX, DZ, 7) ** 1.7) / 2)                             # drip length per 2-voxel strip
frost = sol & (Y > topY - depth) & (topY > 40) & (Z > -46) & (pid != 500) & (pid != 410) & ((Z > -36) | (Y > 60))
put(frost, ICE, p=600, l=6)
put(frost & (Y < topY - depth + 1.5), ICE_S, p=600, l=6)
# raised ice slabs (one brick proud) in 4x4 patches on top
up = np.roll(sol, 1, axis=1) & ~sol & (Y == np.floor(topY) + 1) & (topY > 46) & (Z > -38) & (hashv(np.floor(X / 6), np.floor(Z / 6), 9) > .55)
put(up, ICE_L, p=600, l=6)

# ---------------------------------------------------------------- spine crystals: big glowing cyan ice spikes, raked back
xi0 = lambda x: int(round(x - lo[0] - .5)); zi0 = lambda z: int(round(z - lo[2] - .5))
CRY = [(-21, .5, 10, 1.05), (-12, -1.5, 14, 1.3), (-3, 1.5, 16, 1.45), (6, -1.5, 15, 1.4), (15, 1.5, 12, 1.2), (23, -1, 9, 1.0), (30, .5, 6, .8),
       (-8, 12, 8, .9), (3, -12, 8, .9), (12, 12, 7, .8), (-15, -11, 7, .8)]
CRYM = []                                                          # each crystal's mask (rig: one bone per crystal)
for (zs, xs, L, s) in CRY:
    c = np.where((kind[xi0(xs), :, zi0(zs)] == 1))[0]
    if not len(c): continue
    yt = lo[1] + .5 + c.max()
    tx = .22 * np.sign(xs) * L if abs(xs) > 4 else 0
    m_, t_ = chain_t([(xs, yt - 2.5, zs), (xs + tx * .5, yt + L * .5, zs + .22 * L), (xs + tx, yt + L, zs + .4 * L)], [3.0 * s, 2.3 * s, .5])
    CRYM.append((m_, zs))
    put(m_ & (kind != 2) & (kind != 3), GLOW[2], k=2, st=False)
    put(m_ & ((X - xs - tx * t_) + (Z - zs) * .3 < -.5) & (t_ > .12), GLOW[3], k=3, st=False)  # lit facet
    put(m_ & (t_ > .92), GLOW[4], k=4, st=False)                                                 # white tip

# ---------------------------------------------------------------- seams: the lower part darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.clip(.84 + .26 * (Y / 66.0), .8, 1.08)[..., None]          # lit tops, dark underside
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('a0705a', '7e5442', '5f3e2f', '432a1f', '2d1b13', '1a0f0a',   # fur: light / mid / main / dark / shadow / deep
                                 '0b0d11',                                                     # black
                                 'f6ead0', 'd2bd96', 'a4916d',                                 # ivory / shade / nail shadow
                                 'd2e5fb', 'a8c6ee', '86a6d6', '6584b4', '4b6390')])           # frost: white / light / main / shade / deep
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
body = build('Mammoth', kind == 1, True)
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
    for sx in (1, -1):                                                         # eye lights: the glow spills onto brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 1800; L.data.color = (0x16 / 255, 0xb6 / 255, 0xee / 255); L.data.shadow_soft_size = 1.0
        L.location = B(7.5 * sx, 48.5, -50.0)
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
    cen = (0, 36, -14); D = 235
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 38, -16), 400, az, el, ortho=150)
    for nm, a in (('rest_34', (cen, D, -35, 14)), ('rest_side', (cen, D, 90, 8)), ('rest_front', (cen, D, 0, 8)), ('rest_back', (cen, D, 150, 18)),
                  ('face', ((0, 46, -44), 110, 0, -4)), ('headside', ((0, 46, -45), 110, 90, 4)), ('head34', ((0, 46, -45), 100, -38, 10)), ('hero', ((0, 36, -14), 235, -55, 10)),
                  ('footfront', ((-10.5, 5, -16), 40, 0, 6)), ('footside', ((-10.5, 5, -16), 44, -90, 4)), ('feet', ((0, 9, 5), 170, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): quadruped + 4-bone trunk; L = +x
RIG = [('root', None, (0, 0, 4), (0, 6, 4)), ('hips', 'root', (0, 40, 30), (0, 43, 8)), ('spine', 'hips', (0, 43, 8), (0, 50, -14)),
       ('neck', 'spine', (0, 50, -14), (0, 52, -28)), ('head', 'neck', (0, 54, -28), (0, 46, -46)), ('tail', 'hips', (0, 40, 37), (0, 27, 42))]
TRK = [('trunk1', 'head', (0, 44, -42), (0, 32, -53)), ('trunk2', 'trunk1', (0, 32, -53), (1, 31, -67)),
       ('trunk3', 'trunk2', (1, 31, -67), (2, 47, -74)), ('trunk4', 'trunk3', (2, 47, -74), (9, 62, -58))]
RIG += TRK
TORSO = [b for b in RIG if b[0] in ('hips', 'spine', 'neck')]
OVR = brick_rig.limb(X, Y, Z, kind > 0, TORSO)                       # body bricks only on hips / spine / neck ...
OVR += [((Z < -29) | ((AX > 13) & (Z < -24) & (Y > 44)), 'head'), ((AX < 3.5) & (Z > 36.5) & (Y < 41), 'tail')]   # ... then head, tail
for sx, sd in ((1, 'L'), (-1, 'R')):
    for lz, fb in ((-12, 'F'), (21, 'B')):
        up, lw = 'leg%s%s_up' % (fb, sd), 'leg%s%s_low' % (fb, sd)
        RIG += [(up, 'spine' if fb == 'F' else 'hips', (13.5 * sx, 30, lz), (13.5 * sx, 15, lz)), (lw, up, (13.5 * sx, 15, lz), (13.5 * sx, 1, lz - 1))]
        q = (((X * sx - 13.5) / 8.2) ** 4 + ((Z - lz) / 8.4) ** 4) ** .25
        leg = (X * sx > 0) & (((q - 1) * 8.2 < 3.2) & (Y < 27) | (q < 1.45) & (Y < 4))
        OVR += [(leg & (Y >= 15), up), (leg & (Y < 15), lw)]
OVR += brick_rig.limb(X, Y, Z, TR & (kind > 0), TRK)
OVR += [((TU | ICEC) & (kind > 0), 'head')]
for m_, zs in CRYM:                                                  # whole crystal on the bone under its base
    OVR.append((m_ & (kind > 1), 'hips' if zs > 8 else 'spine' if zs > -14 else 'neck'))
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (20, 0, 0), 'trunk2': (35, 0, 0), 'trunk3': (30, 0, 0), 'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail': (0, 0, 20)},
                 render='render' in argv)
print('BL_OK')
