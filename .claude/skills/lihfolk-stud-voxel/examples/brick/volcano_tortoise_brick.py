# Volcano Tortoise (boss, brick pipeline). Copied from examples/brick/war_rhino_brick.py, model part rewritten.
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference: VolcanoTortoise/concept_sheet.jpg. Broad flat-bottomed basalt dome split into raised plates by lava seams, a smaller
# volcano cone on top (crater + lava rivers), thin drips from the seam ends over the rim, stacked smoke puffs; olive block-scale
# skin, thick elephant legs, visible neck, big head with a hooked V beak, open roaring mouth, recessed glowing eyes.
# Glow kinds: 2/3 = lava (emissive, faint bloom only, so the plates stay charcoal), 4/5/6 = eyes + crater (full strong bloom).
# Run: run_brick.ps1 volcano_tortoise_brick.py [views]. Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'VolcanoTortoise'

lo = np.array((-68.0, -0.5, -144.0)); hi = np.array((68.0, 190.5, 100.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
ROCK = hx('3a3236'); ROCKL = hx('5e5357'); ROCKD = hx('221c1f')
SKIN = hx('8a7f45'); SKINL = hx('a2964f'); SKIND = hx('6b6234')
CREAM = hx('dcc28a'); CREAMD = hx('b39463'); MOUTH = hx('5a1712'); TONGUE = hx('8f2f22'); BLACK = hx('0c0a0c')
SMOKE = hx('8c8788'); SMOKEL = hx('b5b0b0'); SMOKED = hx('6e696a')
GLOW = {2: hx('ff5a0a'), 3: hx('ffb21e'),                    # lava edge / lava hot (faint bloom)
        4: hx('fff07a'), 5: hx('ff6a10'), 6: hx('ffc030')}    # white-hot / eye+crater orange / eye+crater yellow (full bloom)
BLOOM_FULL = (4, 5, 6)

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
def sd_cap(a, b, ra, rb):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d - (ra + (rb - ra) * t)
def hashv(a, b, c, s=0):
    v = np.sin(a * 12.9898 + b * 78.233 + c * 37.719 + s * 4.581) * 43758.5453
    return v - np.floor(v)
rng = np.random.RandomState(7)

# ---------------------------------------------------------------- proportions (measured from concept front + side views; W = rim width = 122)
Y0, Y1, CTOP = 35.0, 43.0, 104.0          # rim underside / lip top / crater top
YM = Y1 + .6 * (CTOP - Y1)                # trapezoid -> cone break
ZC, SZ = 0.0, 1.07                        # shell centre z, front-back stretch
RPROF = ([Y0, Y1, 52.0, YM, CTOP], [59.0, 60.0, 50.5, 32.0, 14.5])
HY, HZ = 56.0, -110.0
TILT = math.radians(15); TPY, TPZ = HY - 6.0, HZ + 18.0             # head pivot at the neck joint
def head_frame(on):
    global Y, Z
    if on:
        globals()['_YW'], globals()['_ZW'] = Y, Z
        yy, zz = _YW - TPY, _ZW - TPZ
        Y = TPY + yy * math.cos(TILT) + zz * math.sin(TILT); Z = TPZ - yy * math.sin(TILT) + zz * math.cos(TILT)
    else:
        Y, Z = _YW, _ZW                     # skull centre (head held forward, ~45% of crater height)

# ---------------------------------------------------------------- body masses: elephant column legs, barrel body, thick neck, big boxy head
LEGS = ((38, 34, -44, 40, -52), (38, 33, 40, 40, 46))              # (hip x, hip y, hip z, foot x, foot z)  (mirrored in x)
dleg = np.full(n, 99.0)
for hxp, hy, hz, fx, fz in LEGS:
    for sx in (1, -1):
        d_ = sd_cap((hxp * sx, hy, hz), (fx * sx, 5, fz), 14.0, 13.5)
        d_ = smin(d_, sd_ell((hxp * sx, hy - 4, hz), (16.0, 13, 16.0)), 3)     # upper-leg / elbow mass
        d_ = smin(d_, sd_ell((fx * sx, 3.0, fz - 1), (15.5, 4.5, 15.5)), 2)    # flared foot pad
        dleg = np.minimum(dleg, d_)
dbody = sd_ell((0, 27, 0), (43, 12, 52))                               # barrel body under the shell
dneck = smin(sd_cap((0, 29, -50), (0, HY - 8, HZ + 15), 15.5, 14.0), sd_ell((0, 29, -56), (17, 13, 14)), 3)
dtail = smin(sd_cap((0, 20, 48), (0, 16, 70), 9.0, 6.0), sd_cap((0, 16, 70), (0, 9, 95), 6.0, 1.6), 1)
head_frame(True)
XW = X / (1.0 - .22 * np.clip((HZ + 4 - Z) / 22.0, 0, 1))            # wedge: narrows toward the beak
dh = ((np.abs(XW / 25.0) ** 4 + np.abs((Y - HY) / 19.0) ** 4 + np.abs((Z - HZ - 3) / 20.5) ** 4) ** (1 / 4) - 1) * 19.0
dh = np.maximum(dh, Y - (HY + 19.0 - .45 * np.clip(HZ + 8 - Z, 0, None) - .022 * X ** 2))          # forehead slopes down to the beak   # boxy skull
for sx in (1, -1): dh = smin(dh, sd_ell((13 * sx, HY - 8, HZ + 4), (10, 11, 12)), 3)   # jaw muscles / cheeks
djaw = smin(sd_ell((0, HY - 26, HZ + 2), (14, 5.5, 12)), sd_ell((0, HY - 15, HZ + 2), (18, 11, 12)), 3)
dskull = dh
dh = np.minimum(dh, djaw)
head_frame(False)

# ---------------------------------------------------------------- skin: block-scale rows (3-brick courses, staggered joints)
dskin = np.minimum.reduce([dleg, dneck, dtail, dh, dbody])
SK = dskin < 0
row = np.floor(Y / 4); odd = np.mod(row, 2) * 2
sxi = np.floor((X + odd) / 4); szi = np.floor((Z + odd) / 4)
tv = hashv(row, sxi, szi, 1)
tone = np.where(tv > .8, 2, np.where(tv < .1, 0, 1))
skc = np.stack([SKIN * .93, SKIN, SKINL])[tone]
col[SK] = skc[SK]; kind[SK] = 1; stud[SK] = True
pid[SK] = (5000 + np.mod(row * 7919 + sxi * 131 + szi * 17, 90000)).astype(np.int32)[SK]; lvl[SK] = tv[SK]   # every tile edge: one side darker = grout
# toes: 4 big cream nails per foot, front-facing, black gaps
for hxp, hy, hz, fx, fz in LEGS:
    for sx in (1, -1):
        for k_, ox in enumerate((-10.0, -3.3, 3.3, 10.0)):
            xc = fx * sx + ox; zt = fz - 17.5 - (1.0 if k_ in (1, 2) else 0)
            cl = (np.abs(X - xc) < 2.5) & (Y < 6.0 - .7 * np.clip(zt + 3 - Z, 0, 3)) & (Z > zt) & (Z < zt + 6)
            put(cl, CREAM, st=False, p=6000, l=2)
            put((np.abs(X - xc) < 2.5) & (Y < 1.0) & (Z > zt) & (Z < zt + 6), CREAMD, st=False, p=6000, l=2)
            gap = (np.abs(X - (xc + 3.3)) < .6) & (Y < 5.5) & (Z > zt - .5) & (Z < zt + 3.5) & (k_ < 3)
            put(gap & (kind > 0), BLACK, st=False)

# ---------------------------------------------------------------- shell = volcano mountain: flared lip, straight trapezoid flank, straight cone
PP = 2.4                                                             # chunky (slightly square) plan
ZS = (Z - ZC) / SZ
RR = (np.abs(X) ** PP + np.abs(ZS) ** PP) ** (1 / PP)
TH = np.arctan2(X, -ZS)
rY = np.interp(Y, *RPROF)
Yq = np.floor(Y / 5) * 5
crag = hashv(Yq, np.mod(np.floor((TH + math.pi) * 24 / (2 * math.pi)), 24), 0, 3)   # rough stepped edge
rY = rY + np.where(Y > Y1, 1.4 * crag - .7, 0)
fac = np.where(Y > Y1, .8, 1.0)
ds = np.maximum((RR - rY) * fac, np.maximum(Y0 - Y, Y - CTOP))
ds = np.where(Z < -30, np.maximum(ds, -(((X / 17.5) ** 2 + ((Y - 33) / 13.0) ** 2) - 1) * 6), ds)   # nuchal arch: neck comes out under the rim
BAND = (ds < 3.5) & (ds > -3.5) & (Y > Y0 - .5) & (Y < CTOP + .5)
ii = np.where(BAND)
P3 = np.stack([X[ii], Y[ii], Z[ii]], 1)
seeds = []
for yk, cnt, off in ((40, 8, 0.0), (58, 7, .5), (75, 5, .15), (90, 4, .6), (99, 3, .3)):
    for j in range(cnt):
        th = (j + off) / cnt * 2 * math.pi + rng.uniform(-.13, .13); yy = yk + rng.uniform(-2, 2)
        rr = float(np.interp(yy, *RPROF))
        s_ = math.sin(th); c_ = math.cos(th); k_ = (abs(s_) ** PP + abs(c_) ** PP) ** (1 / PP)
        seeds.append((rr * s_ / k_, yy, ZC - rr * SZ * c_ / k_))
S = np.array(seeds)
D2 = np.stack([((P3 - s) ** 2).sum(1) for s in S], 1)
o2 = np.argsort(D2, 1)[:, :2]
d1 = D2[np.arange(len(P3)), o2[:, 0]]; d2 = D2[np.arange(len(P3)), o2[:, 1]]
sep = np.linalg.norm(S[o2[:, 0]] - S[o2[:, 1]], axis=1)
gap = np.full(n, 99.0); gap[ii] = (d2 - d1) / (2 * sep + 1e-6)      # bricks to the bisector = to the seam
plate = np.full(n, -1); plate[ii] = o2[:, 0]
raise_ = np.floor(np.clip((gap - 2.0) / 1.3, 0, 3.0))                # plates stand 1-2 bricks proud, stepped edges
shell = (ds < raise_) & (Y > Y0 - .5) & (Y < CTOP + .5)
seam = shell & (gap < 2.0) & (ds > -2.6)
put(shell, ROCKD * .7, st=False, p=1, l=0)
surf = shell & ~seam
col[surf] = np.where((plate[surf] % 2 == 0)[:, None], ROCK, ROCK * .92)
stud[surf] = True
col[surf & (raise_ >= 3) & (ds > raise_ - 1.5)] = ROCKL                      # slab top step lighter
col[surf & (raise_ == 2) & (ds > raise_ - 1.5)] = ROCK                       # bevel ring round the top step
col[surf & (raise_ < 2) & (ds > raise_ - 1.5)] = ROCKD                       # outer steps darker
pid[surf] = 2000 + plate[surf]; lvl[surf] = 1 + raise_[surf]
seam = seam | ((ds < .6) & (gap < 2.0) & (Y > Y0 - .5) & (Y < CTOP + .5))           # lava fills the trench a brick up
put(seam & (gap >= .55), GLOW[2], k=2, st=False)
put(seam & (gap < .55), GLOW[3], k=3, st=False)
put(shell & (Y < Y0 + 1.1) & (ds > -6), ROCKD, st=False, p=1)        # dark underside edge of the rim
put((sd_ell((0, Y0 - 1.0, ZC), (54, 2.5, 58)) < 0) & (kind == 0), ROCKD, st=False, p=1)   # underside (hidden plastron)

# ---------------------------------------------------------------- crater: glowing pool in a notched lip, lava rivers down the cone
rc = 14.5
kind[shell & (Y > CTOP - 1.5) & (RR < rc - 2.5)] = 0
pool = (RR < rc - .5) & (Y > CTOP - 2.5) & (sd_ell((0, CTOP - 1.0, ZC), (rc - .5, 10.5, (rc - .5) * SZ)) < 0)   # big raised lava dome
put(pool, GLOW[6], k=6, st=False)
put(pool & (sd_ell((0, CTOP - 1.0, ZC), (rc - 3.5, 9.0, (rc - 3.5) * SZ)) < 0), GLOW[4], k=4, st=False)   # yellow-hot core shows through the top
put(shell & (kind == 1) & (Y > CTOP - 9) & (ds > -1.5) & (hashv(np.floor(Y / 2), np.floor(TH * 9), 0, 5) < np.clip((Y - (CTOP - 9)) / 9, 0, 1) * 1.3), GLOW[2], k=2, st=False)   # lava sheet spilling down the cone top
for i, th0 in enumerate((-.45, .35, 1.9, 3.3, 4.6)):
    th = th0 + .18 * np.sin(Y * .3 + i * 1.7)
    dth = np.abs((TH - th + math.pi) % (2 * math.pi) - math.pi)
    w = 2.6 + .6 * np.clip((CTOP - Y) / 35, 0, 1) + 2.5 * np.clip((Y - (CTOP - 14)) / 14, 0, 1)   # wide overflow tongues, widest at the top
    riv = (dth * np.maximum(RR, 4) < w) & (Y > YM - 10 + 5 * (i % 2)) & (Y < CTOP + 1.5)
    put(riv & (kind == 1) & (((pid >= 2000) & (pid < 3000)) | (pid == 1)) & (ds > -1.0), GLOW[2], k=2, st=False)
    put(riv & (dth * np.maximum(RR, 4) < 1.0) & (kind == 2), GLOW[3], k=3, st=False)
    put(riv & (kind == 0) & (Y > CTOP - .5) & (Y < CTOP + 1.5) & (RR < rc + .5) & (RR > rc - 3.5), GLOW[3], k=3, st=False)   # lava spilling over the lip

# ---------------------------------------------------------------- drips: lava runs down the lip face at seam ends and hangs below the rim
def cell(x, y, z): return tuple(np.clip(np.floor(np.array((x, y, z)) - lo).astype(int), 0, np.array(n) - 1))
se = np.argwhere(seam & (Y > Y0) & (Y < Y0 + 4) & (ds > -1.5)); sp = lo + .5 + se
sang = np.unique(np.round(np.arctan2(sp[:, 0], -(sp[:, 2] - ZC) / SZ) / .05) * .05)   # where seams hit the rim
rng.shuffle(sang)
ang = np.arange(-math.pi, math.pi, .1); ang = ang + rng.uniform(-.04, .04, len(ang)); rng.shuffle(ang)
ang = np.concatenate([sang, ang])
pts = np.stack([np.sin(ang) * 50, np.full(len(ang), Y0 + 2), ZC - np.cos(ang) * 50 * SZ], 1)
used = []
for k_ in range(len(pts)):
    a_ = ang[k_]
    if math.cos(a_) > .9: continue                                   # face kept clear
    if any(abs((a_ - u + math.pi) % (2 * math.pi) - math.pi) < .12 for u in used): continue
    dx, dz = math.sin(a_), -math.cos(a_)
    x_, z_ = pts[k_, 0], pts[k_, 2]
    r = 0.0                                                          # walk out to the lip's outer face
    while r < 12 and kind[cell(x_ + dx * r, Y0 + 2.5, z_ + dz * r)] > 0: r += .5
    ex, ez = x_ + dx * (r - 1.0), z_ + dz * (r - 1.0)                # outermost lip column
    used.append(a_)
    tx, tz = -dz, dx                                                 # along the rim
    streams = [(0.0, int((3, 5, 7, 9, 12, 15)[rng.randint(6)]), float(rng.uniform(1.2, 2.5)))]
    if rng.rand() < .3: streams.append((float(rng.choice((-1, 1)) * rng.uniform(2.6, 3.6)), int(rng.randint(3, 8)), float(rng.uniform(1.0, 1.6))))   # merging pair
    for off, L, wid in streams:
        cxs, czs = ex + tx * off, ez + tz * off
        t = np.clip((Y - (Y0 - L)) / (L + 6.0), 0, 1)
        yb = Y0 - L * rng.uniform(.35, .65)
        rad = wid + 1.7 * t ** 1.5 + .9 * np.exp(-((Y - yb) / 1.8) ** 2)      # taper + mid bulge
        wob = .6 * np.sin(Y * .7 + a_ * 9)                           # slight wobble
        rr_ = np.sqrt((X - cxs - tx * wob) ** 2 + (Z - czs - tz * wob) ** 2)
        put((rr_ < rad) & (Y > Y0 - L) & (Y < Y1 + .5) & ((kind == 0) | ((pid >= 2000) & (pid < 3000)) | (pid == 1)), GLOW[2], k=2, st=False)
        put((sd_ell((cxs, Y0 - L - 1.0, czs), (wid + 1.0, wid + 2.0, wid + 1.0)) < 0) & (Y < Y0 - L + 1.5) & ((kind == 0) | (kind == 2)), GLOW[3], k=3, st=False)   # teardrop end
    if len(used) >= 42: break

# ---------------------------------------------------------------- beak: short compact hooked beak (overbite hook, V from the front)
head_frame(True)
def prof(P):
    P = np.array(P, float); zs = HZ + P[:, 0]
    return [np.interp(Z, zs, P[:, k]) for k in (1, 2, 3)]
UP = [(-32.5, -18.5, -14.0, 1.6), (-31.5, -19.0, -7.0, 3.4), (-29, -14.0, -1.5, 6.4), (-25, -10.5, 3.0, 9.4),
      (-19.5, -9.0, 5.5, 11.6), (-12, -8.5, 7.0, 12.6), (-6, -8.5, 7.0, 12.6)]                       # (dz, bottom, top, half width) upper beak
ub, ut, uw = prof(UP)
tU = np.clip((Y - (HY + ub)) / np.maximum(ut - ub, .1), 0, 1)
BEAK = (Z > HZ - 32.5) & (Z < HZ - 5) & (Y > HY + ub) & (Y < HY + ut) & (AX < uw * (.12 + .88 * tU ** .8))   # pointed V from the front
LOW = [(-22, -29.5, -25.0, 2.6), (-20, -30.5, -24.5, 6.0), (-12, -31, -24.0, 10.5), (-2, -30.5, -23.5, 13.0)]   # lower beak (jaw dropped)
lb, lt, lw = prof(LOW)
tL = np.clip(((HY + lt) - Y) / np.maximum(lt - lb, .1), 0, 1)
LBEAK = (Z > HZ - 21) & (Z < HZ - 1) & (Y > HY + lb) & (Y < HY + lt) & (AX < lw * (.35 + .65 * tL))
MO = AX < 15.0 * (1 - .3 * np.clip((HY - 12 - Y) / 12, 0, 1)) * np.sqrt(np.clip(1 - ((Y - (HY - 16.5)) / 8.3) ** 2, 0, 1)) + .5   # oval / trapezoid opening
MOI = AX < 8.5 * np.sqrt(np.clip(1 - ((Y - (HY - 16.5)) / 5.5) ** 2, 0, 1))
mouthv = (Z < HZ - 1) & MO & (Y > HY - 25) & (Y < HY - 8)                  # wide open roaring mouth
kind[mouthv & (dh < 0)] = 0
put(BEAK, CREAM, st=False, p=7000, l=3)
put(BEAK & (Y < HY + ub + 1.2), CREAMD, st=False, p=7000, l=3)               # cutting edge
put(BEAK & (AX > uw * (.12 + .88 * tU ** .8) - 1.6), CREAMD, st=False, p=7000, l=3)   # shaded beak sides
put(BEAK & (Z < HZ - 29) & (Y < HY - 13), CREAMD * .8, st=False, p=7000, l=3)  # darker hook tip
put(LBEAK, CREAM, st=False, p=7001, l=3)
put(LBEAK & (Y < HY + lb + 1.2), CREAMD, st=False, p=7001, l=3)
put(LBEAK & (Y > HY + lt - 1.2) & (AX < lw * .6 - .4), MOUTH, st=False)      # red mouth floor
put(BEAK & (Y < HY + ub + 1.2) & (AX < uw * .45 - .5) & (Z > HZ - 25), MOUTH, st=False)   # palate
put(box(0, 16, HY - 25, HY - 8, HZ - 5, HZ - 2.5) & (dh < .5) & ~MOI, MOUTH * .8, st=False)   # throat wall
put(box(0, 9, HY - 22, HY - 11, HZ - 5, HZ - 2.5) & (dh < .5) & MOI, BLACK, st=False)       # dark oval throat
put(box(0, 16, HY - 25, HY - 8, HZ - 5, HZ + 2) & MO & (kind == 0) & (dh < 0), MOUTH, st=False)
put(box(0, 5.5, HY - 24.3, HY - 22.7, HZ - 15, HZ - 3) & (kind == 0), TONGUE, st=False)          # tongue
put(box(0, 4, HY - 22.9, HY - 21.9, HZ - 12, HZ - 4) & (kind == 0), TONGUE, st=False)        # tongue ridge
put((kind == 0) & (Y > HY + ub - 1.3) & (Y < HY + ub) & (AX < uw * .3 + .2) & (Z > HZ - 20) & (Z < HZ - 4), TONGUE, st=False)   # gum line under the beak
put(BEAK & box(3.4, 4.6, HY + 3.0, HY + 4.0, HZ - 24, HZ - 21.5), CREAMD * .55, st=False)   # nostrils

# ---------------------------------------------------------------- eyes: crisp almond glow (outer corner high), black lid ring, heavy angry brow
EX, EY = 12.5, HY + 4.0
eu = AX - EX; ev = (Y - EY) - .4 * eu                                 # tilt: outer corner high
alm = (eu / 4.6) ** 2 + (ev / 1.35) ** 2                              # slit
SURF = (dskull < 0) & (dskull > -1.3) & (Z < HZ - 11) & ~BEAK
put(SURF & (alm < 1.7) & (alm >= 1), BLACK, st=False)                  # lid ring
put(SURF & (alm < 1), GLOW[6], k=6, st=False)                          # iris
# EYEFIX: one flat eye colour (GLOW[6]), no white-hot centre
blo = HY + 5.5 + .38 * (AX - 3.0)                                     # brow V: inner ends meet low over the beak
brow = (dskull < 3.6) & (dskull > -2) & (AX < 22.5) & (Y >= blo + .4) & (Y < np.minimum(blo + 5.0, HY + 20)) & (Z < HZ - 2) & ~BEAK & (alm >= 1.7)
put(brow, SKIND, p=7100, l=4)
put(brow & (Y > blo + 1.8), SKIN, p=7100, l=4)

head_frame(False)
# ---------------------------------------------------------------- tail spikes (dark basalt)
for zs, L in ((66, 8.5), (74, 8.0), (82, 6.5), (89, 5.0)):
    zi = int(round(zs - lo[2] - .5)); xi = int(round(-lo[0] - .5))
    c_ = np.where(kind[xi, :, zi] == 1)[0]
    if not len(c_): continue
    yt = lo[1] + .5 + c_.max()
    put((sd_cap((0, yt - 1, zs), (0, yt + L, zs + 3.5), 3.8, .7) < 0) & (kind == 0), ROCKD, st=False, p=8000, l=5)

# ---------------------------------------------------------------- smoke: soft cloud rising from the crater, widening, drifting back + right
PUFFS = [(1, 116, 2, 8), (6, 126, 6, 12.5), (-10, 134, 8, 12), (18, 137, 16, 14), (3, 146, 18, 15.5),
         (-16, 151, 20, 12), (28, 152, 28, 14), (12, 162, 32, 14), (36, 165, 38, 11)]   # few big rounded puffs, drifting back + right
dsm = np.full(n, 99.0)
for k_, (x_, y_, z_, r_) in enumerate(PUFFS):
    dp = sd_ell((x_, y_, z_), (r_, r_ * .85, r_))
    for a_ in range(3):                                              # soft lumps round each puff
        th = a_ / 3 * 2 * math.pi + k_
        dp = smin(dp, sd_ell((x_ + math.cos(th) * r_ * .6, y_ + r_ * .25, z_ + math.sin(th) * r_ * .6), (r_ * .55, r_ * .5, r_ * .55)), 3.0)
    dsm = smin(dsm, dp, 2.5)
SM = (dsm < 0) & (kind == 0)
put(SM, SMOKE, st=False, p=9000, l=0)
put(SM & (np.roll(dsm, -2, 1) > 0), SMOKEL, st=False, p=9001, l=1)          # light puff tops
put(SM & (np.roll(dsm, 2, 1) > 0), SMOKED, st=False, p=9002, l=.5)          # dark undersides

# ---------------------------------------------------------------- seams: lower part darkens where it meets a higher neighbour
LAVA = (kind == 2) | (kind == 3); LAVC = col[LAVA].copy()
kind[LAVA] = 1; stud[LAVA] = False; pid[LAVA] = 0
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 1) & (np_ > 1) & (np_ != pid) & (nl > lvl)
dk = dark & (kind == 1)
col[dk] *= np.where((pid[dk] >= 5000) & (pid[dk] < 95000), .7, .62)[:, None]   # skin tiles: softer outlines (calm), shell: deep seams
col *= np.clip(.74 + .42 * (Y / 70.0), .74, 1.12)[..., None]
col = np.clip(col, 0, 1)
col[LAVA] = LAVC
PAL = np.array([hx(h) for h in ('5a4f53', '332b2e', '1d181a', 'ff6a14',      # basalt: light / main / dark | lava orange
                                 'a2964f', '8a7f45', '6b6234', '4a4322',      # skin (olive-khaki): light / main / dark / crease
                                 'e2c98f', 'b39463',                          # beak + claws / shade
                                 '5a1712', '93321f',                          # mouth / tongue
                                 '0c0a0c',                                    # black
                                 'b5b0b0', '8c8788', 'ffc23a')])              # smoke light / smoke | lava yellow
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- audit: drop bricks not connected to the body (smoke excluded)
if True:
    body_ = (kind > 0) & ~((pid >= 9000) & (pid < 9003)); reach = body_ & (Y < 1)
    for _ in range(400):
        g = reach.copy()
        for ax in range(3):
            for s_ in (1, -1): g |= np.roll(reach, s_, ax)
        g &= body_
        if g.sum() == reach.sum(): break
        reach = g
    fl = body_ & ~reach; print('FLOAT removed', int(fl.sum())); kind[fl] = 0; solid = kind > 0
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
    if not verts: return None                                          # fully buried glow set
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
body = build('VolcanoTortoise', kind == 1, True)
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
    if o is None: continue
    gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
    cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
    b2.inputs['Emission Strength'].default_value = 5.0; gm.diffuse_color = cl
    o.data.materials.append(gm); o.color = cl if k in BLOOM_FULL else (cl[0] * (.3 if k == 3 else .15), cl[1] * (.3 if k == 3 else .15), cl[2] * (.3 if k == 3 else .15), 1); GL.append(o)   # lava: faint bloom only
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for sx in (1, -1):                                                         # eye lights: the glow spills onto brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 2500; L.data.color = (1.0, .527, .030); L.data.shadow_soft_size = 1.0   # = GLOW[6] ffc030 (linear)
        L.location = B(13.0 * sx, HY + 9.0, HZ - 25.0); L.data.energy = 1800
    L = bpy.data.objects.new('CraterLight', bpy.data.lights.new('CraterLight', 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 2500; L.data.color = (1.0, .4, .08); L.data.shadow_soft_size = 3.0; L.location = B(0, CTOP + 4, ZC)
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
    cen = (0, 80, -16); D = 420
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 82, -16), 400, az, el, ortho=250)
    for nm, a in (('rest_34', (cen, D, -40, 12)), ('rest_side', (cen, D, -90, 6)), ('rest_front', (cen, D, 0, 6)), ('rest_back', (cen, D, 180, 12)),
                  ('face', ((0, 50, -122), 110, 0, 4)), ('headside', ((0, 52, -112), 120, -90, 4)), ('head34', ((0, 52, -114), 120, -38, 8)),
                  ('footfront', ((-40, 9, -55), 58, 0, 6)), ('feet', ((0, 18, 0), 200, -90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): body (shell + smoke), neck + head + jaw, 4 column legs, tail; L = +x
head_frame(True); HEADR = (Z < HZ + 17) & (Y > 18); JAWR = HEADR & (Y < HY - 20.5); head_frame(False)
hid = kind > 0                                                                     # glow fully buried in the crater dome (never seen) -> dome glow,
for ax_ in range(3):                                                               # so no rig piece is all-hidden faces
    for s_ in (1, -1): hid &= np.roll(kind > 0, s_, axis=ax_)
kind[hid & (kind == 4)] = 6
SOL = kind > 0
SHELL = SOL & (((pid >= 2000) & (pid < 3000)) | (pid == 1) | (kind >= 2)) & (Y > 14) & ~HEADR
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('body', 'root', (0, 30, 40), (0, 30, -40)),
       ('neck', 'body', (0, 30, -45), (0, 50, -92)), ('head', 'neck', (0, 50, -92), (0, 56, -142)), ('jaw', 'head', (0, 42, -104), (0, 38, -136))]
TL = [('tail1', 'body', (0, 20, 46), (0, 16, 70)), ('tail2', 'tail1', (0, 16, 70), (0, 9, 96))]
RIG += TL
OVR = [(SOL, 'body'), (((dneck < 1) | (dh < 2)) & SOL & (Z < -40) & ~SHELL, 'neck'), (HEADR & SOL, 'head'), (JAWR & SOL, 'jaw')]
OVR += brick_rig.limb(X, Y, Z, ((dtail < 1) | (pid == 8000)) & SOL & (Z > 50), TL)
for sx, sd in ((1, 'L'), (-1, 'R')):
    for (hxp, hy, hz, fx, fz), fb in zip(LEGS, 'FB'):
        up, lw = 'leg%s%s_up' % (fb, sd), 'leg%s%s_low' % (fb, sd)
        ch = [(up, 'body', (hxp * sx, hy, hz), (hxp * sx, 19, hz)), (lw, up, (hxp * sx, 19, hz), (fx * sx, 2, fz - 12))]
        RIG += ch
        leg = SOL & (X * sx > 0) & (np.abs(Z - hz) < 30) & (Y < Y0 - .5) & ((dleg < .5) | (pid == 6000) | (Y < 8)) & ~SHELL
        OVR += brick_rig.limb(X, Y, Z, leg, ch)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'neck': (20, 0, 0), 'head': (0, 20, 0), 'jaw': (-20, 0, 0), 'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail1': (0, 25, 0)},
                 render='render' in argv)
print('BL_OK')
