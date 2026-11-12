# Mimic Chest (stud-voxel treasure-chest boss on spider legs, brick pipeline). Reference = concept_sheet.jpg (this folder).
# GLOW: subtle   (only the 2 slit eyes + the keyhole eye glow; everything else is solid bricks)
# Built from the brick examples (war_rhino / venom_widow): box body + hinged lid frame -> plates with stepped seams -> brick faces + square-stud overlay -> EEVEE.
# Run: powershell -File <skill>\scripts\run_brick.ps1 mimic_chest_brick.py [views]
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'MimicChest'

lo = np.array((-64.0, -0.5, -60.0)); hi = np.array((64.0, 100.5, 54.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij')
XW, YW, ZW = X, Y, Z
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
SEAM = hx('1a120e'); WD = hx('3d2618'); WM = hx('5a3a22'); WL = hx('7a5232')
IRD = hx('3a3d45'); IRON = hx('5c616b')
GOLDD = hx('8a5a10'); GOLD = hx('d9a21e'); GOLDL = hx('ffd34a')
BONE = hx('e8dcc0'); BONES = hx('b0a184')
MOUTHD = hx('4a0a12'); MOUTH = hx('8c1a24')
PURP = hx('7a3a9c'); PURPL = hx('a95ccc'); BLUE = hx('2f7fe0')
GLOW = {2: hx('ffb21c'), 3: hx('fff27a'), 4: hx('fffbe0')}   # orange edge / hot yellow centre / glint
WOODS = (WD, WM, WL)

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def cap(a, b, ra, rb, flat=False):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t0 = ((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab); t = np.clip(t0, 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    m = d <= ra + (rb - ra) * t
    return m & (t0 >= 0) & (t0 <= 1) if flat else m
def cube(c, h):
    return (np.abs(X - c[0]) < h) & (np.abs(Y - c[1]) < h) & (np.abs(Z - c[2]) < h)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
rng = np.random.default_rng(11)
KEEP = np.zeros(n, bool)
def nb6(m):                                           # voxels 6-adjacent to mask m
    o = np.zeros_like(m)
    for ax in range(3):
        for s in (1, -1): o |= np.roll(m, s, axis=ax)
    return o

# ---------------------------------------------------------------- frames
SH = 0.10                                             # lunge: body sheared so the front sits lower (vertical faces stay flat)
PHI = math.radians(42); HY, HZ = 50.0, 24.0            # lid opened PHI about the back-top hinge line
DROP = 7.0                                             # body modelled at y 22..50, lands DROP lower
def body_to_world(p): return np.array((p[0], p[1] + SH * p[2] - DROP, p[2]))
def lid_to_body(p):
    ry, rz = p[1] - HY, p[2] - HZ
    return np.array((p[0], HY + ry * math.cos(PHI) - rz * math.sin(PHI), HZ + ry * math.sin(PHI) + rz * math.cos(PHI)))
def lid_to_world(p): return body_to_world(lid_to_body(p))
def set_body():
    global X, Y, Z
    X, Y, Z = XW, YW - SH * ZW + DROP, ZW
def set_lid():
    global X, Y, Z
    yb = YW - SH * ZW + DROP; ry, rz = yb - HY, ZW - HZ
    X, Y, Z = XW, HY + ry * math.cos(PHI) + rz * math.sin(PHI), HZ - ry * math.sin(PHI) + rz * math.cos(PHI)
def set_world():
    global X, Y, Z
    X, Y, Z = XW, YW, ZW

def planks(m, coord, base, h, seg):                   # random brown per (plank row, segment); dark seam row at each row bottom
    row = np.floor((coord - base) / h).astype(int); fr = (coord - base) / h - row
    for r_ in np.unique(row[m]):
        for s_ in np.unique(seg[m & (row == r_)]):
            mm = m & (row == r_) & (seg == s_)
            c_ = WOODS[rng.integers(3)]
            put(mm, c_, p=100 + r_ * 7 + s_, l=1)
            sp = mm & (rng.random(n) < .07); put(sp, WOODS[rng.integers(3)], p=100 + r_ * 7 + s_, l=1)
    put(m & (fr * h < 1.0), SEAM, st=False, p=99, l=0)

# ================================================================ BODY (box)
set_body()
AXb = np.abs(X)
BX, BZ, BY0, BY1 = 30.0, 24.0, 19.0, 50.0
box = (AXb < BX) & (np.abs(Z) < BZ) & (Y > BY0) & (Y < BY1)
seg_x = np.digitize(AXb, (15, 19)) + 3 * (X > 0)
seg_z = np.digitize(np.abs(Z), (8,)) + 10 * (Z > 0)
side = box & (AXb > BX - 1.0) & (np.abs(Z) < BZ - 1.0)
planks(box & ~side, Y, BY0, 5.6, seg_x)                 # front/back/top/bottom: horizontal planks
planks(side, Y, BY0, 5.6, seg_z)                        # sides: horizontal planks
# nail heads at plank ends (small iron dots next to the corner caps)
rowc = np.floor((Y - BY0) / 5.6)
nails = box & (np.abs(Z) > BZ - 1) & (np.abs(AXb - 23.5) < .6) & (np.abs((Y - BY0) - (rowc * 5.6 + 3.3)) < .55)
put(nails, IRD, st=False, p=98, l=2)
nails2 = side & (np.abs(np.abs(Z) - 12.5) < .6) & (np.abs((Y - BY0) - (rowc * 5.6 + 3.3)) < .55)
put(nails2, IRD, st=False, p=98, l=2)
# scratch marks (front, left of the lock) + one on the side
for i, sx_ in ((0, -1), (1, -1), (2, -1), (0, 1), (1, 1), (2, 1)):          # 3 thin claw slashes each side of the lock
    a = (sx_ * (14.5 - i * 3.0), 41.0, -BZ + .5); b = (sx_ * (11.5 - i * 3.0), 31.5, -BZ + .5)
    put(cap(a, b, .55, .55) & box & (np.abs(Z) > BZ - 1.2), MOUTH, st=False, p=97, l=0)
for i in range(3):
    a = (-30.4, 42.0 - i * 1.5, 2 + i * 2.6); b = (-30.4, 33.5 - i * 1.5, 8 + i * 2.6)
    s_ = cap(a, b, .62, .62) & box & (X < -BX + 1.2)
    put(s_, MOUTH, st=False, p=97, l=0)
# iron: vertical bands, rim trim, base trim (1 brick proud)
shell1 = (AXb < BX + 1) & (np.abs(Z) < BZ + 1) & (Y > BY0 - 1) & (Y < BY1)
vb = shell1 & (np.abs(AXb - 17) < 2) & (Y < BY1 - 0.01)
rim = shell1 & (Y > BY1 - 4)
bot = shell1 & (Y < BY0 + 3)
for m_, pp in ((bot, 201), (vb, 202), (rim, 203)):
    put(m_, IRON, st=True, p=pp, l=3)
put((vb | rim | bot) & (np.abs(Y - BY1 + 2) < 1.1) & (np.abs(AXb - 17) < .6), IRD, st=False, p=pp, l=3)   # band/rim rivet
riv = vb & (np.abs(((Y - BY0) % 5.6) - 3.3) < .55) & (np.abs(AXb - 17) < .6) & (Y > BY0 + 3) & (Y < BY1 - 4)
put(riv, IRD, st=False, p=202, l=3)
rivR = rim & (np.abs(((X + 30) % 6) - 3) < .55) & (np.abs(Y - BY1 + 2) < .6) & (AXb < BX - 2) & (AXb > 20)
put(rivR, IRD, st=False, p=203, l=3)
# gold corner caps (8)
for sx in (1, -1):
    for sz in (1, -1):
        for yc in (BY0 + 2.5, BY1 - 3.0):
            c_ = (sx * (BX - 2.5), yc, sz * (BZ - 2.5))
            m_ = (np.abs(X - c_[0]) < 4.0) & (np.abs(Y - c_[1]) < 3.6) & (np.abs(Z - c_[2]) < 4.0)
            m_ &= (AXb < BX + 1.5) & (np.abs(Z) < BZ + 1.5) & (Y < BY1)
            put(m_, GOLD, p=newid(), l=5); KEEP[m_] = True
            put(m_ & (np.abs(Y - yc) > 2.6), GOLDD, p=pid.max(), l=5)
            pc = (sx * (BX + 1.0), yc, sz * (BZ - 2.5)); put(cube(pc, .6) & m_, GOLDL, st=False, p=pid.max(), l=5)
            pc = (sx * (BX - 2.5), yc, sz * (BZ + 1.0)); put(cube(pc, .6) & m_, GOLDL, st=False, p=pid.max(), l=5)
# lock plate (front centre) + glowing keyhole eye
lockO = (AXb < 7.5) & (Y > 27.5) & (Y < 45.5) & (Z < -BZ + 1) & (Z > -BZ - 2.2)
put(lockO, GOLDD, p=300, l=6); KEEP[lockO] = True
lockI = (AXb < 6.2) & (Y > 28.8) & (Y < 44.2) & (Z < -BZ - 1) & (Z > -BZ - 2.2)
put(lockI, GOLD, p=301, l=6.5)
put(lockI & (Y > 41.5), GOLDL, p=301, l=6.5)
for xr in (-4.5, 4.5):
    for yr in (30.5, 42.5): put(cube((xr, yr, -BZ - 1.7), .6) & lockI, GOLDL, st=False, p=301, l=6.5)
kh_c = (X ** 2 + (Y - 38.0) ** 2 < 2.9 ** 2)
kh_s = (AXb < 1.6) & (Y > 31.0) & (Y < 37.0) & (np.abs(X) < .6 + (37.0 - Y) * .18)
kh = (kh_c | kh_s)
khr = ((X ** 2 + (Y - 38.0) ** 2 < 4.0 ** 2) | ((AXb < 2.8) & (Y > 30.0) & (Y < 37.5))) & ~kh
put(khr & (Z < -BZ - .3) & (Z > -BZ - 2.2), SEAM, st=False, p=302, l=7)
kind[kh & (Z < -BZ - 1.0)] = 0                                 # keyhole recessed 1 brick into the plate
put(kh & (Z < -BZ + .5) & (Z > -BZ - 1.2), GLOW[3], k=3, st=False)   # EYEFIX: one flat yellow
# hinge plates (back) + hinge barrels
for xh in (-16.5, 16.5):
    hp = (np.abs(X - xh) < 3.2) & (Y > BY1 - 8) & (Y < BY1) & (Z > BZ - 1) & (Z < BZ + 1.6)
    put(hp, IRD, p=newid(), l=4)
    put(cap((xh - 4, BY1 + .4, BZ + .6), (xh + 4, BY1 + .4, BZ + .6), 1.9, 1.9, flat=True), IRON, p=newid(), l=5)
# interior: hollow mouth, heap of coins, gems
IX, IZ, IFLOOR = BX - 3, BZ - 3, 27.0
cav = (AXb < IX) & (np.abs(Z) < IZ) & (Y > IFLOOR) & (Y < BY1 + 6)
kind[cav & (Y < BY1)] = 0
heapH = 47.5 + 6.0 * np.clip(1 - (X / IX) ** 2, 0, 1) * np.clip(1 - (Z / IZ) ** 2, 0, 1) ** .5
bumps = np.zeros(n)
for _ in range(14):
    bc = (rng.uniform(-22, 22), rng.uniform(-9, 9)); br = rng.uniform(3, 6)
    bumps = np.maximum(bumps, 2.6 * np.clip(1 - ((X - bc[0]) ** 2 + (Z - bc[1]) ** 2) / br ** 2, 0, 1))
heap = cav & (Y < heapH + bumps)
put(heap, GOLD, p=400, l=2); KEEP[heap] = True
top = heap & ~np.roll(heap, -1, axis=1)
r_ = rng.random(n)
put(top & (r_ < .35), GOLDL, p=400, l=2); put(top & (r_ > .82), GOLDD, p=400, l=2)
for _ in range(16):                                    # loose coins lying on the heap: light disc with a dark rim
    cc = (rng.uniform(-22, 22), rng.uniform(-9, 9))
    d2 = (X - cc[0]) ** 2 + (Z - cc[1]) ** 2
    put(top & (d2 < 2.3 ** 2), GOLDD, p=401, l=2); put(top & (d2 < 1.3 ** 2), GOLDL, p=401, l=2)
lining = nb6(cav) & (kind == 1) & box & ~heap & (Y > IFLOOR)
put(lining & (Y > BY1 - 1.5), MOUTH, st=False, p=402, l=0)
put(lining & (Y <= BY1 - 1.5), MOUTH, st=False, p=402, l=0)
cavE = cav & (kind == 0)
deep = nb6(cavE) & (kind == 1) & box & ~heap & (Y < 47)
put(deep, MOUTHD, st=False, p=402, l=0)
for gc, gr, gcol in (((-9.0, 51.0, -3.5), 2.3, MOUTH), ((11.5, 50.0, 3.0), 2.3, BLUE), ((-19.0, 49.5, 5.0), 2.0, PURPL)):
    g_ = sd_ell(gc, (gr, gr * 1.15, gr)) < 0
    put(g_, gcol, st=False, p=newid(), l=3); KEEP[g_] = True
    put(cube((gc[0] - .8, gc[1] + 1.2, gc[2] - .8), .6) & g_, BONE, st=False, p=pid.max(), l=3)

# ================================================================ LID (closed frame, then hinged open)
set_lid()
AXl = np.abs(X)
LX, LZ0, LZ1, LY0 = 31.0, -BZ - 1.0, BZ + 1.0, 50.0
ltop = 60.0 + 7.0 * np.sqrt(np.clip(1 - (Z / (LZ1 + .5)) ** 2, 0, 1))
lid = (AXl < LX) & (Z > LZ0) & (Z < LZ1) & (Y > LY0) & (Y < ltop)
lseg = np.digitize(AXl, (15, 19)) + 3 * (X > 0)
planks(lid, -Z, -LZ1, 5.4, lseg)                       # lid planks run left-right, rows step front-to-back
front = lid & (Z < LZ0 + 1.0)
planks(front, Y, LY0, 20, lseg)                         # lid front face = one plank band
lsh = (AXl < LX + 1) & (Z > LZ0 - 1) & (Z < LZ1) & (Y > LY0) & (Y < ltop + 1)
lvb = lsh & (np.abs(AXl - 17) < 2)
lrim = lsh & (Y < LY0 + 2.2) & ~((AXl < LX - 1) & (Z > LZ0 + 1))
put(lrim, IRON, p=210, l=3); put(lvb, IRON, p=211, l=3)
put(lvb & (np.abs(((-Z + LZ1) % 5.4) - 2.7) < .55) & (np.abs(AXl - 17) < .6) & (Y > ltop - .5), IRD, st=False, p=211, l=3)
put(lvb & (np.abs(Y - 58.5) < .6) & (np.abs(AXl - 17) < .6) & (Z < LZ0 + .2), IRD, st=False, p=211, l=3)
for sx in (1, -1):
    for zc in (LZ0 + 2.5, LZ1 - 2.5):
        m_ = (np.abs(X - sx * (LX - 2.5)) < 4.0) & (np.abs(Z - zc) < 4.0) & (Y > LY0 - .01) & (Y < ltop + 1.2)
        m_ &= (AXl < LX + 1.5) & (Z > LZ0 - 1.5) & (Z < LZ1 + .5) & (Y < 62.5)
        put(m_, GOLD, p=newid(), l=5); KEEP[m_] = True
        put(m_ & (Y < LY0 + 1.2), GOLDD, p=pid.max(), l=5)
        put(cube((sx * (LX + 1.0), 56.0, zc), .6) & m_, GOLDL, st=False, p=pid.max(), l=5)
        put(cube((sx * (LX - 2.5), 56.0, LZ0 - 1.0), .6) & m_ & (zc < 0), GOLDL, st=False, p=pid.max(), l=5)
# hollow underside = upper mouth (red roof)
lcav = (AXl < LX - 3) & (Z > LZ0 + 3) & (Z < LZ1 - 3) & (Y > LY0 - 3) & (Y < LY0 + 5)
kind[lcav & lid] = 0
llin = nb6(lcav) & (kind == 1) & ((AXl < LX + 2) & (Z > LZ0 - 2) & (Z < LZ1 + 2) & (Y > LY0 - .5)) & ~lcav
put(llin & (Y < LY0 + 5.6), MOUTH, st=False, p=403, l=0)
put(llin & (Y > LY0 + 4.6), MOUTHD, st=False, p=403, l=0)
# upper jaw band: a forward-facing slab hung under the lid's front lip; the eyes sit on it, the top fangs hang from it
set_body()
AXb = np.abs(X)
E_ = lid_to_body((0.0, LY0, LZ0)); BZF, BZB, BYB, BYT = E_[2] - 2.0, E_[2] + 3.5, E_[1] - 11.0, E_[1] + 1.5
JAWBOT = BYB
band = (AXb < LX) & (Z > BZF) & (Z < BZB) & (Y > BYB) & (Y < BYT)
put(band, WM, p=420, l=2)
put(band & (Y < BYB + 2.2), IRON, p=421, l=3)                                # iron trim along the jaw edge
put(band & (Y > BYT - 1.6), IRON, p=421, l=3)
put(band & (np.abs(AXb - 17) < 2), IRON, p=422, l=3)
put(band & (Z > BZB - 1.0) & (Y > BYB + 2.2), MOUTHD, st=False, p=423, l=0)    # back face = mouth roof
for sx in (1, -1):
    m_ = band & (np.abs(X - sx * (LX - 2.5)) < 3.6)
    put(m_, GOLD, p=newid(), l=5); KEEP[m_] = True
    put(cube((sx * (LX + .0), (BYB + BYT) / 2, BZF + 2), .6) & m_, GOLDL, st=False, p=pid.max(), l=5)
EYC = (BYB + BYT) / 2 + .6
for sx in (1, -1):                                   # angry slit eyes: recessed, dark socket, orange edge, hot centre
    xr = sx * X
    yt = EYC + 1.9 + .40 * (xr - 9.0); yb = EYC - 1.7 + .10 * (xr - 9.0)
    slit = (xr > 3.6) & (xr < 14.2) & (Y < yt) & (Y > yb) & (Z < BZF + 1.6) & (Z > BZF - .2)
    sock = (xr > 2.6) & (xr < 15.0) & (Y < yt + 1.1) & (Y > yb - 1.1) & (Z < BZF + 2.2) & (Z > BZF - .2) & ~slit & band
    put(sock, SEAM, st=False, p=404, l=0)
    put(slit, GLOW[3], k=3, st=False)   # EYEFIX: one flat yellow
    kind[slit & (Z < BZF + .6)] = 0

# ================================================================ FANGS (world frame, bone white, top hang down, bottom point up)
set_world()
def fang(base, tip, r):                             # axis-aligned stepped pyramid: a clean triangle from the front and the side
    base = np.array(base, float); tip = np.array(tip, float); h = tip[1] - base[1]
    t = (Y - base[1]) / h
    cxp = base[0] + (tip[0] - base[0]) * t; czp = base[2] + (tip[2] - base[2]) * t
    m_ = (t >= 0) & (t <= 1) & (np.abs(X - cxp) < r * (1 - t) + .35) & (np.abs(Z - czp) < r * .75 * (1 - t) + .35)
    put(m_, BONE, p=newid(), l=6); KEEP[m_] = True
    put(m_ & (X > cxp + .2) & (t > .15), BONES, p=pid.max(), l=6)
for xf in np.arange(-23.0, 24, 9.2):                     # bottom front row: 6 big triangles
    b = body_to_world((xf, BY1 - 1.0, -BZ + 1.5)); fang(b, b + (0, 10.0 - .06 * abs(xf), -.4), 4.3)
for sx in (1, -1):
    for zf in (-14.0, -4.0, 6.0):
        b = body_to_world((sx * (BX - 1.5), BY1 - 1.0, zf)); fang(b, b + (-sx * .4, 8.0, 0), 3.4)
for xf in np.arange(-23.0, 24, 9.2):                     # top row: 6 big triangles hanging from the jaw band
    b = body_to_world((xf, JAWBOT + 1.0, BZF + 2.2)); fang(b, b + (0, -10.5 + .06 * abs(xf), -.4), 4.5)
for sx in (1, -1):
    for zf in (-16.0, -7.0):
        b = lid_to_world((sx * (LX - 1.5), LY0 + 1.0, zf)); fang(b, b + (-sx * .4, -6.5, 0), 2.6)

# ================================================================ TONGUE (segmented, purple, curling out over the front)
TP = [body_to_world(p) for p in ((2.0, 48.0, -6.0), (0.5, 55.0, -14.0), (-3.0, 58.0, -26.0), (-6.0, 57.0, -36.0),
                                 (-9.0, 52.0, -42.5), (-11.0, 46.0, -43.0), (-11.5, 43.5, -38.0), (-11.0, 46.0, -34.5))]
RT = [4.2, 4.6, 4.6, 4.3, 3.9, 3.3, 2.6, 1.8]
samples = []
for i in range(len(TP) - 1):
    L_ = np.linalg.norm(TP[i + 1] - TP[i]); k_ = max(2, int(L_ / .8))
    for t in np.linspace(0, 1, k_, endpoint=False):
        samples.append((TP[i] + (TP[i + 1] - TP[i]) * t, RT[i] + (RT[i + 1] - RT[i]) * t))
samples.append((TP[-1], RT[-1]))
acc = 0.0; prev = samples[0][0]; segi = []
for p_, r_ in samples: acc += np.linalg.norm(p_ - prev); prev = p_; segi.append(int(acc / 3.6))
for j in range(len(samples) - 1):
    (pa, ra), (pb, rb) = samples[j], samples[j + 1]
    m_ = cap(pa, pb, ra, rb) & ((kind == 0) | (pid == 400) | (pid == 401))
    s_ = segi[j]
    put(m_, PURP if s_ % 2 == 0 else PURPL, p=600 + s_, l=4 + (s_ % 2) * .6); KEEP[m_] = True

# ================================================================ LEGS (4, spider style: brown segments, gold joint caps, long bone tips)
for s in (1, -1):
    for zf, ky, tz in ((-1, 46.0, -37.0), (1, 48.0, 35.0)):
        A = body_to_world((s * (BX + 1.0), 31.0, zf * 14.0))
        K = np.array((s * 40.0, ky, zf * 25.0)); J = np.array((s * 44.0, 17.0 if zf < 0 else 18.0, zf * 31.0 + (-1.5 if zf < 0 else 0)))
        T = np.array((s * 45.0, .6, tz))
        lg = cap(A, K, 5.0, 4.6); put(lg, WM, p=newid(), l=3); KEEP[lg] = True
        lg = cap(K, J, 4.6, 4.2); put(lg, WD, p=newid(), l=3); KEEP[lg] = True
        f = cap(J - np.array((0, 2.5, 0)), T, 4.0, .5); put(f, BONE, p=newid(), l=4); KEEP[f] = True
        put(f & (Y < J[1] * .55) & (Y > 2.5) & ((X - T[0]) * s > -.2), BONES, p=pid.max(), l=4)
        for c_, h_ in ((A, 5.6), (K, 5.6), (J, 4.8)):
            m_ = cube(c_, h_); put(m_, GOLD, p=newid(), l=6); KEEP[m_] = True
            put(m_ & (Y < c_[1] - h_ + 1.2), GOLDD, p=pid.max(), l=6)
            put(m_ & (Y > c_[1] + h_ - 1.0), GOLDL, p=pid.max(), l=6)
set_world()
for (cx_, cz_, h_) in ((-18, -40, 2), (-8, -45, 1), (4, -38, 3), (15, -43, 1), (24, -36, 2), (-27, -33, 1), (9, -49, 1), (-14, -51, 2)):
    for k_ in range(h_):                                 # small coin stacks resting on the ground, each coin nudged
        ox, oz = (k_ % 2) * .7, (k_ // 2) * -.6
        d2 = (X - cx_ - ox) ** 2 + (Z - cz_ - oz) ** 2
        cn = (d2 < 2.5 ** 2) & (np.abs(Y - k_) < .5) & (kind == 0)
        put(cn, GOLD if k_ % 2 == 0 else GOLDD, st=k_ == h_ - 1, p=newid(), l=1 + k_); KEEP[cn] = True
        put(cn & (d2 < 1.3 ** 2) & (k_ == h_ - 1), GOLDL, st=True, p=pid.max(), l=1 + k_)
topx = (kind == 1) & ~np.roll(kind > 0, -1, axis=1) & np.all(np.isclose(col, WD), -1) & (Y < 50) & (np.abs(X) > 32)
col[topx] = WL
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
if _a[1] == 0: _reach[:, 0, :] |= _sc[:, 0, :]                                  # anything resting on the ground plane is kept (coin stacks)
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
# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1) & ~KEEP] *= .7
col *= np.where(KEEP, np.clip(.9 + .2 * (Y / 60.0), .9, 1.1), np.clip(.78 + .4 * (Y / 60.0), .78, 1.15))[..., None]
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('1a120e', '3d2618', '5a3a22', '7a5232', '3a3d45', '5c616b', '8a5a10', 'd9a21e', 'ffd34a',
                                 'e8dcc0', 'b0a184', '4a0a12', '8c1a24', '7a3a9c', 'a95ccc', '2f7fe0')])
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
body = build('MimicChest', kind == 1, True)
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
    for nm, p, e in (('EyeL', tuple(body_to_world((9.0, EYC, BZF - 4.0))), 500), ('EyeR', tuple(body_to_world((-9.0, EYC, BZF - 4.0))), 500), ('Key', tuple(body_to_world((0, 37.0, -30.0))), 260)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e * .35; L.data.color = tuple(GLOW[3]); L.data.shadow_soft_size = 1.0
        L.location = B(*p)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.78, .78, .8)
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.5, .5, .52, 1)
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
    cen = (0, 36, -4); D = 215
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 44, -2), 400, az, el, ortho=125)
    for nm, a in (('rest_34', (cen, D, -35, 14)), ('rest_side', (cen, D, 90, 6)), ('rest_front', (cen, D, 0, 6)), ('rest_back', (cen, D, 180, 8)),
                  ('back34', (cen, D, 145, 14)), ('face', ((0, 56, -24), 115, 0, 6)), ('footfront', ((-30, 10, -40), 80, -40, 12))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): box body, lid = jaw (hinge at the back top edge), tongue chain, 4 legs x 3
sol_ = kind > 0
set_body(); bbox = (np.abs(X) < BX + 2) & (np.abs(Z) < BZ + 2) & (Y < 60.5)          # box, coin heap, gems, bottom fangs
jawB = (Y > 60.5) & (Z > -17) & (np.abs(X) < LX + 2)                                    # jaw band + top fangs (body frame)
shell = (np.abs(X) < BX + 1.6) & (np.abs(Z) < BZ + 1.6) & (Y < BY1)
set_lid(); jawL = ((Y > LY0) | ((Y > LY0 - 7) & (Z < 10) & (np.abs(X) > LX - 5))) & (np.abs(X) < LX + 2) & (Z > LZ0 - 2) & (Z < LZ1 + 1) & (Y < 70)   # lid + its side fangs (lid frame)
set_world()
HW = body_to_world((0, HY, HZ)); LF = lid_to_world((0, LY0 + 8, LZ0))
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('body', 'root', (0, 14, 0), (0, 42, 0)), ('jaw', 'body', tuple(HW), tuple(LF))]
bodyM = bbox & sol_
jaw_m = sol_ & (jawB | (jawL & ~shell))
OVR = [(bodyM, 'body')]
for s, sd in ((1, 'L'), (-1, 'R')):
    for zf, ky, tz in ((-1, 46.0, -37.0), (1, 48.0, 35.0)):
        fb = 'F' if zf < 0 else 'B'
        A = body_to_world((s * (BX + 1.0), 31.0, zf * 14.0))
        K = np.array((s * 40.0, ky, zf * 25.0)); J = np.array((s * 44.0, 17.0 if zf < 0 else 18.0, zf * 31.0 + (-1.5 if zf < 0 else 0)))
        T = np.array((s * 45.0, .6, tz))
        lg = (cap(A, K, 5.0, 4.6) | cap(K, J, 4.6, 4.2) | cap(J - np.array((0, 2.5, 0)), T, 4.0, .5) | cube(A, 5.6) | cube(K, 5.6) | cube(J, 4.8)) & sol_
        ch_ = [('leg%s%s_up' % (fb, sd), 'body', tuple(A), tuple(K)), ('leg%s%s_low' % (fb, sd), 'leg%s%s_up' % (fb, sd), tuple(K), tuple(J)),
               ('leg%s%s_tip' % (fb, sd), 'leg%s%s_low' % (fb, sd), tuple(J), tuple(T))]
        RIG += ch_; OVR += brick_rig.limb(X, Y, Z, lg, ch_)
OVR += [(jaw_m, 'jaw')]
TB = [('tongue%d' % (i + 1), 'body' if i == 0 else 'tongue%d' % i, tuple(TP[a]), tuple(TP[b])) for i, (a, b) in enumerate(((0, 2), (2, 4), (4, 7)))]
tng = np.zeros(n, bool)
for j in range(len(samples) - 1): tng |= cap(samples[j][0], samples[j + 1][0], samples[j][1], samples[j + 1][1])
RIG += TB; OVR += brick_rig.limb(X, Y, Z, sol_ & tng & (pid >= 600) & (pid < 700), TB)
OVR += [(sol_ & (Y < 4) & (Z < -30) & (np.abs(X) < 32), 'root')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'jaw': (-25, 0, 0), 'tongue2': (25, 0, 0), 'legFL_up': (0, 0, 20), 'legBR_low': (30, 0, 0)},
                 render='render' in argv)
print('BL_OK')
