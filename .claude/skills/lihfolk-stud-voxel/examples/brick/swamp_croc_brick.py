# Giant Swamp Crocodile boss (stud-voxel, brick pipeline). Machinery copied from skill examples/brick/war_rhino_brick.py.
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference = concept_sheet.jpg. Long low armoured body + tail as long as the body, open jaws with ivory teeth outside,
# cream belly, 3-tone moss green tiles, dark-olive stepped ridge rows, toxic slit eyes on raised bumps, hanging moss strands.
# Run: blender -b --factory-startup --python swamp_croc.py -- render
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'SwampCroc'

lo = np.array((-36.0, -0.5, -108.0)); hi = np.array((36.0, 40.5, 118.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)                                      # plate id / plate height level

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
GL_ = hx('7a9632'); GM = hx('4c6420'); GS = hx('3d5219'); GD = hx('2d3f12')
RIDGE = hx('34361c'); RIDGEL = hx('4f5030'); CREAM = hx('efe0aa'); CREAMS = hx('c9b57c'); IVORY = hx('fbf1d6')
MOUTH = hx('8a2c30'); MOUTHD = hx('4d161b'); MOSS = hx('b6f03a'); MOSSM = hx('8acc1e'); BLACK = hx('0c0e0a')
GLOW = {2: hx('2fe81c'), 3: hx('b4ff3c'), 4: hx('f2ffd6')}   # toxic green edge / hot centre / glint

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb):                               # capsule a->b (symmetric in x)
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((AX - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((AX - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m

rng = np.random.RandomState(7)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
def hsh(a, b, c=0): return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xffff

# ---------------------------------------------------------------- body + tail: one long low profile (z, bottom, top, half width)
BP = np.array([(-62, 9.0, 21.0, 11.0), (-54, 6.5, 23.5, 14.5), (-44, 5.0, 27.0, 17.0), (-25, 4.5, 29.0, 18.5), (-5, 4.5, 29.0, 18.5),
               (10, 5.0, 28.0, 17.0), (22, 5.5, 25.0, 14.0), (40, 5.5, 21.0, 10.5), (60, 5.5, 16.5, 7.5), (80, 5.0, 13.0, 5.0),
               (98, 4.5, 9.5, 2.8), (113, 4.5, 7.0, 1.1)])
def prof(z, P): return [np.interp(z, P[:, 0], P[:, i]) for i in (1, 2, 3)]
bb, bt, bw = prof(Z, BP); bm = (bb + bt) / 2; bh = (bt - bb) / 2
def sup(a=0.0): return ((AX / (bw + a)) ** 3 + (np.abs(Y - bm) / (bh + a)) ** 4 < 1) & (Z > -62) & (Z < 113.5)
def top_at(x, z):
    b_, t_, w_ = prof(z, BP); m_ = (b_ + t_) / 2; h_ = (t_ - b_) / 2
    return m_ + h_ * max(0.0, 1 - (abs(x) / w_) ** 3) ** .25
body = sup()
BID = 2000
put(body, GM, p=BID, l=1)
tone = hsh(np.floor(X / 3).astype(np.int64), np.floor(Z / 3).astype(np.int64)) % 3
up = Y > bm + .35 * bh
put(body & up & (tone == 0), GL_, p=BID, l=1)
put(body & ~up & (Y > bm - .05 * bh), GS, p=BID, l=1)                         # flank
belly = body & (Y < bb + .36 * (bt - bb)) & (Z < 104)
put(belly, CREAM, p=BID, l=1)
put(belly & ((np.floor(Z) % 5) == 0), CREAMS, p=BID, l=1)                       # belly plate lines
put(body & ~belly & (Y < bb + .45 * (bt - bb)) & (Y >= bb + .36 * (bt - bb)) & (Z < 104), GD, p=BID, l=1)   # dark band over the cream
# raised scute tiles on the back (3x3 with 1 gaps, rows offset): every tile edge is a brick step
sh = sup(1.0) & ~body & (Y > bm + .15 * bh)
zt = np.floor((Z + 200) / 4); xt = np.floor((X + 200 + 2 * (zt % 2)) / 4)
tilem = sh & (((X + 200 + 2 * (zt % 2)) % 4) < 3) & (((Z + 200) % 4) < 3)
tid = (xt * 1000 + zt).astype(np.int64)
for t in np.unique(tid[tilem]):
    m_ = tilem & (tid == t)
    c_ = (GL_, GM, GL_ * .92 + GM * .08)[hsh(int(t), 3) % 3]
    put(m_, c_, p=newid(), l=2)

# ---------------------------------------------------------------- ridge plates: dark-olive stepped pyramids raked back
def pyramid(xc, zc, a, b, H, tz=.65):
    y0 = int(round(top_at(xc, zc))) - 1; p_ = newid()
    for k in range(H):
        s = k / max(H, 1); ak = max(a * (1 - .55 * s), 1.2); bk = max(b * (1 - tz * s), 1.2)
        m_ = (np.abs(AX - xc) < ak) & (np.abs(Y - (y0 + k)) < .5) & (np.abs(Z - (zc + .5 * k)) < bk)
        put(m_, RIDGEL if k == H - 1 else RIDGE, p=p_, l=3 + k)
for zc in range(-52, 24, 10):                                                   # back: double spine row (big triangles, read in the silhouette)
    H = int(round(4 + 5.0 * math.sin(math.pi * (zc + 56) / 84)))
    pyramid(2.5, zc, 3.6, 5.4, H, .7)
for zc in range(-46, 20, 8):                                                    # back: flank rows (smaller)
    pyramid(10.0, zc + 3, 2.0, 2.2, 2)
for zc in range(26, 112, 7):                                                    # tail: both edges, merge near the tip
    w_ = prof(zc, BP)[2]; xc = max(w_ * .55, 0.0)
    H = int(round(6.0 - 3.5 * (zc - 24) / 88))
    if xc < 1.6: pyramid(0.0, zc, 1.8, 2.6, max(H, 2))
    else: pyramid(xc, zc, 2.2, 3.4, max(H, 2), .6)

# ---------------------------------------------------------------- moss: bright strands hanging from the back down the flanks
def xi_of(x): return int(np.floor(x - lo[0]))
def zi_of(z): return int(np.floor(z - lo[2]))
def strand(z0, side, L, wz=2):
    zi = zi_of(z0); ys = np.where((kind[xi_of(6 * side), :, zi] == 1))[0]
    if not len(ys): return
    ytop = ys.max(); p_ = newid()
    for j in range(L + 1):
        yi = ytop - j
        if yi < 1: break
        for dz in range(wz + (1 if j >= L - 1 else 0)):
            z_ = zi + dz - (1 if j >= L - 1 else 0)
            row = np.where(kind[:, yi, z_] == 1)[0]
            if not len(row): continue
            i = row.max() if side > 0 else row.min()
            o = i + side
            if 0 <= o < n[0]:
                col[o, yi, z_] = MOSS if (j + dz) % 3 else MOSSM; kind[o, yi, z_] = 1; pid[o, yi, z_] = p_; lvl[o, yi, z_] = 4
            col[i, yi, z_] = MOSSM; pid[i, yi, z_] = p_; lvl[i, yi, z_] = 4
    # patch on top of the back where the strand starts
    for dx in range(-1, 2):
        for dz in range(0, wz):
            xx = xi_of((6 - 1.5) * side) + dx; zz = zi + dz
            ys2 = np.where(kind[xx, :, zz] == 1)[0]
            if len(ys2) and rng.rand() < .45:
                yy = ys2.max(); col[xx, yy, zz] = MOSS; pid[xx, yy, zz] = p_; lvl[xx, yy, zz] = 4
MOSSZ = [(-48, 13), (-34, 16), (-20, 12), (-6, 17), (8, 13), (22, 15), (38, 10), (54, 8), (72, 6), (90, 5)]
for side in (1, -1):
    for k_, (z0, L) in enumerate(MOSSZ):
        zz = z0 + (3 if side < 0 else 0) + rng.randint(-1, 2)
        strand(zz, side, L + rng.randint(-2, 3), 3)                              # clump: a main strand + 1-2 thinner ones
        strand(zz + 4, side, max(3, L - 4 - rng.randint(0, 4)), 1)
        if k_ % 2 == 0: strand(zz - 2, side, max(3, L // 2), 1)

# ---------------------------------------------------------------- legs: short, thick, sprawled out; 4 toes with cream claws
LID = newid()
def leg(sh_, el, wr, r1, r2, r3, fx, fz, big):
    m_ = chain([sh_, el, wr], [r1, r2, r3])
    put(m_ & (kind == 0) | m_ & (pid == BID), GM, p=LID, l=1.5)
    put(m_ & (Y > el[1] + 1), GL_, p=LID, l=1.5)
    put(m_ & (Y < 4.5), GS, p=LID, l=1.5)
    w = 2 if not big else 2
    x0 = fx - 5.5 - (1 if big else 0)
    put(box(x0, x0 + 11 + (2 if big else 0), -1, 3.5, fz - 4, fz + 5), GD, p=LID, l=1.5)                 # foot pad
    for t in range(4):
        a = x0 + .5 + 3 * t + (.5 if big else 0); lng = 5 + (1 if t in (1, 2) else 0) + (1 if big else 0)
        put(box(a, a + w, -1, 3.5, fz - 4 - lng, fz - 3), GM, p=newid(), l=2)                          # toe
        put(box(a, a + w, 2.5, 4.5, fz - 3 - lng + 2, fz - 3), GL_, p=newid(), l=2.5)
        put(box(a, a + w, -1, 2.5, fz - 6 - lng, fz - 3 - lng), IVORY, st=False)                      # claw
        put(box(a, a + w, -1, 0.5, fz - 7 - lng, fz - 6 - lng), CREAMS, st=False)                    # claw tip (down)
leg((12, 14, -40), (24, 11, -41), (27, 3, -43), 6.8, 5.8, 5.0, 27, -43, False)
leg((11, 15, 7), (24, 12, 9), (28, 3, 10), 9.0, 7.0, 5.6, 28, 10, True)

# ---------------------------------------------------------------- head: upper skull/snout + open lower jaw (z, bottom, top, half width)
UP = np.array([(-104, 16.5, 21.0, 10.0), (-100, 16.0, 21.5, 11.0), (-94, 15.5, 21.0, 10.5), (-84, 14.8, 21.5, 11.0),
               (-76, 14.0, 22.5, 12.5), (-68, 13.0, 24.5, 14.0), (-62, 12.5, 25.5, 15.0), (-54, 12.0, 26.0, 15.0)])
ub, ut, uw = prof(Z, UP); um = (ub + ut) / 2; uh = (ut - ub) / 2
upper = ((AX / uw) ** 4 + (np.abs(Y - um) / uh) ** 4 < 1) & (Z > -104.5) & (Z < -54)
HU = newid()
put(upper, GM, p=HU, l=1.2)
put(upper & (Y > um + .2 * uh) & (tone == 0), GL_, p=HU, l=1.2)
put(upper & (Y < um - .1 * uh), GS, p=HU, l=1.2)
put(upper & (Y < ub + 1.0) & (AX > uw - 1.6), CREAMS, p=HU, l=1.2)                  # lip line
put(upper & (Y < ub + 1.0) & (AX <= uw - 1.6), MOUTHD, st=False)                   # mouth roof
# snout scute rows (raised 2x2 blocks with gaps)
sn = (((AX / (uw + 1)) ** 4 + (np.abs(Y - um) / (uh + 1)) ** 4) < 1) & ~upper & (Y > um + .3 * uh) & (Z > -96) & (Z < -60)
snt = sn & (((X + 201) % 3) < 2) & (((Z + 200) % 3) < 2)
for t in np.unique((np.floor((X + 201) / 3) * 1000 + np.floor((Z + 200) / 3))[snt]):
    m_ = snt & ((np.floor((X + 201) / 3) * 1000 + np.floor((Z + 200) / 3)) == t)
    put(m_, (GL_, GM)[hsh(int(t), 5) % 2], p=newid(), l=2)
# nose bump with 2 nostrils on its front
NB = newid()
put(box(0, 5.5, 19.5, 23.5, -105, -96), GL_, p=NB, l=2.5)
put(box(0, 4.5, 22.5, 24.5, -104, -97), GM, p=NB, l=3)
put(box(1, 4, 20.5, 22.5, -105, -104), BLACK, st=False)
# lower jaw (open): cream with green outer sides, red tongue floor
LP = np.array([(-103, -0.6, 4.6, 10.0), (-92, 0.4, 5.6, 10.6), (-80, 2.0, 7.6, 11.5), (-70, 3.5, 9.6, 12.5), (-62, 5.0, 11.5, 13.5), (-54, 6.0, 12.5, 14.5)])
lb, lt, lw = prof(Z, LP); lm = (lb + lt) / 2; lh = (lt - lb) / 2
lower = ((AX / lw) ** 4 + (np.abs(Y - lm) / lh) ** 4 < 1) & (Z > -103.5) & (Z < -54)
HL = newid()
put(lower, CREAM, p=HL, l=1.2)
put(lower & (Y > lm) & (AX > lw - 2.0), GS, p=HL, l=1.2)                         # green outer upper band of the jaw
put(lower & (Y > lb + .3) & (Y < lb + 1.5) & ((np.floor(Z) % 4) == 0), CREAMS, p=HL, l=1.2)
put(lower & (Y > lt - 1.0) & (AX <= lw - 1.6), MOUTH, st=False)                  # tongue / floor
put((AX < 3.5) & (Z > -96) & (Z < -64) & (np.abs(Y - (lt + .5)) < .6) & ~upper, MOUTH, st=False)  # tongue ridge
put((AX < np.minimum(uw, lw) - 2.5) & (Y < ub) & (Y > lt) & (Z > -90) & (Z < -58) & ~upper & ~lower, MOUTHD, st=False)   # mouth cavity (dark red behind the teeth)
# eye bumps: raised blocks on top of the skull, glow slit eyes on their front/outer faces, heavy angry brow
EB = newid()
put(box(4.5,12.5, 20, 27.5, -74, -62), GM, p=EB, l=2.5)
put(box(4.5,12.5, 25.5, 27.5, -74, -62), GL_, p=EB, l=2.5)
put(box(5.0,12.0, 20.5, 27.5, -74.2, -72.8), BLACK, st=False)                        # socket (front face)
put(box(11.0,12.0, 20.5, 26.5, -74, -67), BLACK, st=False)                       # socket (outer face)
put(box(6.0,11.0, 21.5, 26.5, -74.2, -72.8), GLOW[2], k=2, st=False)                 # big toxic eye
put(box(11.0,12.0, 21.5, 25.5, -73, -68), GLOW[2], k=2, st=False)                    # side view eye
put(box(11.0,12.0, 21.5, 25.5, -71, -70), BLACK, st=False)                           # side slit
BR = newid()                                                                       # brow: steps down toward the snout centre
put(box(9.5,13.5, 26.5, 29.5, -76, -66), GL_, p=BR, l=4)
put(box(7.0,9.5, 25.5, 28.5, -76, -67), GL_, p=BR, l=4)
put(box(4.0,7.0, 24.5, 27.5, -76, -68), GL_, p=BR, l=4)
put(box(4.0,13.5, 24.5, 25.5, -76.2, -75) & ~(kind > 1) & (kind == 1) & (pid == BR), GD, st=False)
# teeth: jagged ivory, half outside the jaw edge. Upper point down, lower point up.
def tooth(xc, zc, y0, L, down):                                                   # 2x2 root, 1x1 point, cream tip
    for k in range(L):
        y = y0 - k if down else y0 + k
        if k < max(1, int(L * .55)): m_ = (AX > xc - 1) & (AX < xc + 1) & (np.abs(Y - y) < .5) & (Z > zc - 1) & (Z < zc + 1)
        else: m_ = (AX > xc - 1) & (AX < xc) & (np.abs(Y - y) < .5) & (Z > zc - 1) & (Z < zc)
        put(m_, IVORY if k < L - 1 else CREAMS, st=False)
for i, zc in enumerate(range(-99, -64, 4)):
    b_, t_, w_ = prof(zc, UP); L = (7 if i in (1, 5) else 4 + (i % 2))
    tooth(int(round(w_)), zc + rng.randint(-1, 1), int(np.floor(b_)), L, True)
for i, zc in enumerate(range(-97, -66, 4)):
    b_, t_, w_ = prof(zc, LP); L = (6 if i in (0, 4) else 4 + ((i + 1) % 2))
    tooth(int(round(w_)), zc + rng.randint(-1, 1), int(np.ceil(t_)), L, False)
for xc in (2, 7):                                                                  # front teeth at the snout and chin tips
    tooth(xc, -103, 16, 5 if xc == 7 else 4, True)
    tooth(xc, -102, 5, 5 if xc == 7 else 4, False)

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.clip(.74 + .45 * (Y / 30.0), .74, 1.15)[..., None]                      # lit tops, dark underside
col = np.clip(col, 0, 1)
# voxel-style: PALETTE <= 16: snap every solid brick to its nearest entry.
PAL = np.array([hx(h) for h in ('809c36', '4e6622', '3e541a', '2d4013', '1c2a0b',      # moss-green light / mid / side / dark / seam
                                 '34361c', '4f5030', '22230f',                        # ridge olive / light / shade
                                 'efe0aa', 'c9b57c',                                  # cream belly / shade
                                 'fbf1d6', '8a2c30', '4d161b',                        # ivory teeth / mouth red / mouth dark
                                 'b6f03a', '8acc1e', '0c0e0a')])                      # moss bright / moss mid / black
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
    """exposed brick faces as flat quads; UVs = brick coords / 16 (one stud per 2x2 bricks)"""
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
body = build('Croc', kind == 1, True)
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
    for sx in (1, -1):                                                         # eye lights: toxic green spill on brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 2200; L.data.color = (0x2f / 255, 0xe8 / 255, 0x1c / 255); L.data.shadow_soft_size = 1.0
        L.location = B(9.0 * sx, 24.0, -77.0)
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
    for nm, az, el, os_, tg in (('ortho_front', 0, 0, 90, (0, 15, 0)), ('ortho_side', 90, 0, 240, (0, 15, 4)),
                                ('ortho_back', 180, 0, 90, (0, 15, 0)), ('ortho_top', 0, 89.9, 240, (0, 15, 4))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=os_)
    cen = (0, 12, 2)
    for nm, a in (('rest_34', ((0, 12, -22), 300, 42, 16)), ('rest_side', (cen, 330, 90, 6)), ('rest_front', ((0, 14, -40), 190, 0, 8)), ('rest_back', (cen, 300, 150, 20)),
                  ('face', ((0, 16, -88), 78, 0, 6)), ('headside', ((0, 15, -80), 110, 90, 4)), ('head34', ((0, 16, -82), 105, -40, 12)),
                  ('footfront', ((-26, 4, -44), 40, 0, 6)), ('footside', ((-26, 5, -44), 46, -90, 4)), ('feet', ((0, 9, 4), 330, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): spine + 4-bone tail, head + jaw, 4 sprawled legs (up / low / foot); L = +x
SOL = kind > 0
SPINE = [('hips', 'root', (0, 17, 22), (0, 17, -10)), ('chest', 'hips', (0, 17, -10), (0, 17, -54)),
         ('tail1', 'hips', (0, 15, 22), (0, 13, 45)), ('tail2', 'tail1', (0, 13, 45), (0, 11, 68)),
         ('tail3', 'tail2', (0, 11, 68), (0, 9, 90)), ('tail4', 'tail3', (0, 9, 90), (0, 6, 114))]
RIG = [('root', None, (0, 0, 0), (0, 6, 0))] + SPINE + [('head', 'chest', (0, 17, -54), (0, 19, -104)), ('jaw', 'head', (0, 10, -56), (0, 3, -103))]
OVR = brick_rig.limb(X, Y, Z, SOL, SPINE)
OVR += [(SOL & (Z < -54) & (AX < 16), 'head')]
cav = (AX < np.minimum(uw, lw) - 2.5) & (Z > -90) & (Z < -58) & (Y < ub) & (Y > lt)   # mouth cavity stays with the skull
cand = SOL & (Z < -54) & ~upper & ~cav
JAW = lower & SOL
for yi in range(1, n[1]): JAW[:, yi, :] |= cand[:, yi, :] & JAW[:, yi - 1, :]            # lower teeth: grow up from the jaw
OVR += [(JAW, 'jaw')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    for (sh_, el, wr, fx, fz, rr), fb in ((((12, 14, -40), (24, 11, -41), (27, 3, -43), 27, -43, (6.8, 5.8, 5.0)), 'F'), (((11, 15, 7), (24, 12, 9), (28, 3, 10), 28, 10, (9.0, 7.0, 5.6)), 'B')):
        P = lambda q: (q[0] * sx, q[1], q[2])
        LB = [('leg%s%s_up' % (fb, sd), 'chest' if fb == 'F' else 'hips', P(sh_), P(el)), ('leg%s%s_low' % (fb, sd), 'leg%s%s_up' % (fb, sd), P(el), P(wr))]
        RIG += LB + [('foot%s%s' % (fb, sd), LB[1][0], P(wr), (fx * sx, 1, fz - 12))]
        side = X * sx > 0
        FOOT = SOL & side & (AX > fx - 9) & (AX < fx + 9) & (Y < 4.5) & (Z > fz - 17) & (Z < fz + 6)
        OVR += brick_rig.limb(X, Y, Z, SOL & side & (pid == LID) & chain([sh_, el, wr], [r + 1 for r in rr]) & ~FOOT, LB) + [(FOOT, 'foot%s%s' % (fb, sd))]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (-15, 0, 0), 'jaw': (20, 0, 0), 'tail2': (0, 0, 20), 'tail3': (0, 0, 20), 'legFL_up': (0, 0, 25), 'legBR_up': (25, 0, 0)},
                 render='render' in argv)
print('BL_OK')
