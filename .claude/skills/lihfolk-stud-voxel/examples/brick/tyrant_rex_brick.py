# Giant Armored Tyrant Rex boss (stud-voxel, brick pipeline). Machinery copied from skill examples/brick/war_rhino_brick.py.
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Reference = concept_sheet.jpg. Crimson 3-tone scaly hide with black tiger stripes, cream belly bands, huge open-jawed head,
# bone teeth / brow horns / spine spikes, recessed amber eyes, tiny arms, digitigrade legs with 3 clawed toes, long level tail.
# Run: blender -b --factory-startup --python tyrant_rex_brick.py -- render
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'TyrantRex'

lo = np.array((-36.0, -0.5, -94.0)); hi = np.array((36.0, 116.5, 112.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n); skin = np.zeros(n, bool)           # plate id / level / red hide (gets stripes)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
RL = hx('d8463f'); RM = hx('b52a2c'); RS = hx('8e1f24'); RD = hx('651419')
STRIPE = hx('1c1214'); CREAM = hx('ecd9ad'); CREAMS = hx('c7ae7f'); BONE = hx('f4ecd6'); BONES = hx('cdbf9c')
MOUTH = hx('9a2a30'); MOUTHD = hx('4a0d12'); BLACK = hx('0b0909'); SCAR = hx('e88b7e'); CREAMD = hx('a8875a')
GLOW = {2: hx('ff8a0c'), 3: hx('ffd23a'), 4: hx('fff6dc')}   # amber edge / hot centre / white-hot glint

def put(m, rgb, k=1, st=True, p=0, l=0.0, sk=False):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l; skin[m] = sk

def sd_ell(c, r):                                    # ellipsoid signed distance (iq's estimate), symmetric in x
    px, py, pz = (AX - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
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
def prof(z, P): return [np.interp(z, P[:, 0], P[:, i]) for i in (1, 2, 3)]

rng = np.random.RandomState(11)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
def hsh(a, b, c=0): return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xffff
tone = hsh(np.floor(X / 3).astype(np.int64) + 99, np.floor(Y / 3).astype(np.int64) * 7 + np.floor(Z / 3).astype(np.int64)) % 4

tone6 = hsh(np.floor(X / 6).astype(np.int64) + 99, np.floor(Y / 6).astype(np.int64) * 7 + np.floor(Z / 6).astype(np.int64)) % 3
def hide(m, p, l, mid):                              # 3-tone crimson hide: light tops, main, darker lower flanks, random 3x3 tiles
    put(m, RM, p=p, l=l, sk=True)                                                  # big-block tones only (6-brick cells), clean back
    put(m & (Y > mid - 4) & (Y <= mid + 6) & (tone6 == 0), RL, p=p, l=l, sk=True)
    put(m & (Y < mid - 4), RS, p=p, l=l, sk=True)
    put(m & (Y < mid - 4) & (tone6 == 1), RD, p=p, l=l, sk=True)

Yg = Y; YO = 15.0; Y = Yg - YO        # everything above the legs is designed 5 lower, then lifted (legs use real Y)
# ---------------------------------------------------------------- body: deep chest, thick neck, shoulders, hips, huge thighs (pitched forward)
d = sd_ell((0, 34, -38), (18, 17.5, 14))                          # deep chest (lowest front, keel ~26)
d = smin(d, sd_ell((0, 42, -42), (19.5, 12, 10)), 5)
d = smin(d, sd_ell((0, 46, -45), (14.5, 12, 9)), 4)
d = smin(d, sd_ell((0, 54, -48), (13.5, 12, 9)), 4)                  # tall neck: head held high over the chest                  # shoulder / neck root
d = smin(d, sd_ell((0, 59, -52), (14, 12, 9)), 4)                  # neck rising ...
d = smin(d, sd_ell((0, 62, -57), (11.5, 11.5, 9)), 4)               # ... into the raised skull
d = smin(d, sd_ell((0, 38, -24), (16.5, 16.5, 15)), 6)                  # barrel
d = smin(d, sd_ell((0, 43, -10), (15, 15, 13)), 6)                  # hips (back top ~59)
d = smin(d, sd_ell((0, 41, 4), (12.5, 11.5, 13)), 6)                    # tail root
for sx in (1,):
    pass
BID = 2000
BODY = d < 0
# tail: long, heavy, held level, tapering to a point (z, bottom, top, half width)
TP = np.array([(-6, 28, 54, 15), (8, 30.5, 51, 12.5), (22, 32.5, 48, 9.8), (38, 34, 45, 7.4), (54, 35, 43, 6),
               (70, 35.8, 41.2, 4.5), (84, 36.4, 40, 3.1), (96, 37, 39.2, 1.8), (106, 37.4, 38.6, .7)])
tb, tt, tw = prof(Z, TP); tm = (tb + tt) / 2; th = (tt - tb) / 2
def tsup(a=0.0): return ((AX / (tw + a)) ** 2.4 + (np.abs(Y - tm) / (th + a)) ** 2.4 < 1) & (Z > -6) & (Z < 107)
TAIL = tsup()
hide(BODY | TAIL, BID, 1, 38)
put(TAIL & (Z > 10) & (Y < tm - .55 * th), RS, p=BID, l=1, sk=True)                # tail underside darker
put(TAIL & (Z > -4) & (Z < 96) & (Y < tm - .5 * th) & (AX < .62 * tw + .5), CREAM, p=BID, l=1)   # cream strip under the tail
put(TAIL & (Z > -4) & (Z < 96) & (Y < tm - .5 * th) & (AX < .62 * tw + .5) & ((np.floor(Z) % 4) == 0), CREAMS, p=BID, l=1)
# scute shell: raised 3x3 tiles (1 gaps, rows offset) over the back + tail top: every tile edge is a brick step
shell = (((d >= 0) & (d < 1.2) & (Y > 47)) | (tsup(1.0) & ~TAIL & (Y > tm + .2 * th) & (Z > 2))) & (kind == 0)
zt = np.floor((Z + 300) / 4); xt = np.floor((X + 300 + 2 * (zt % 2)) / 4)
tilem = shell & (((X + 300 + 2 * (zt % 2)) % 4) < 3) & (((Z + 300) % 4) < 3)
tid = (xt * 1000 + zt).astype(np.int64)
for t in []:                                                                       # (raised tiles off: they read as speckle)
    m_ = tilem & (tid == t)
    put(m_, (RL, RM, RM)[hsh(int(t), 3) % 3], p=newid(), l=2, sk=True)

# ---------------------------------------------------------------- belly: cream plates in horizontal bands, throat to belly
BL = np.array([(-62, 54.0), (-54, 48.0), (-46, 34.0), (-38, 27.5), (-28, 25.0), (-16, 27.0), (-6, 31.5)])
bline = np.interp(Z, BL[:, 0], BL[:, 1])
belly = (kind == 1) & (pid == BID) & (Z < -14) & ((Y < bline) | ((AX < 8.5) & (Y < 46) & (Z < -26)) | ((Y < bline + 4) & (AX < 12.5 - .3 * np.maximum(0, Z + 20))))
put(belly, CREAM, p=BID, l=1)
put(belly & (((Y - .55 * Z) % 3.4) < 1.2), CREAMD, p=BID, l=1)                         # band lines

# ---------------------------------------------------------------- thigh: huge drumstick, its own raised mass
TH = (sd_ell((15, 27, -6), (12.5, 16, 14)) < 0) & ((kind == 0) | (AX > 9))
THID = newid(); hide(TH, THID, 1.6, 40)
Pj = (TH & (X > 0)).any(0); Ej = np.zeros_like(Pj)                             # silhouette of the drumstick seen from the side
for ax_ in (0, 1):
    for s_ in (1, -1): Ej |= Pj & ~np.roll(Pj, s_, axis=ax_)
put(TH & Ej[None] & (AX > 13), hx('651419'), p=THID, l=1.6)                   # outline it (reads from the side)                                    # outline the drumstick (reads from the side)
Y = Yg
# ---------------------------------------------------------------- legs: digitigrade shin + metatarsus, 3 big toes with bone claws
LX = 14
for (a, b, ra, rb) in (((16, 38, -7), (LX + 5, 25, -4), 9.6, 7.4), ((LX + 5, 25, -4), (LX, 10, 5), 6.2, 5.2), ((LX, 10, 5), (LX, 5.5, -4), 5.2, 5.0)):
    m_ = cap(a, b, ra, rb) & ((kind != 1) | (pid == BID)); p_ = newid()
    put(m_, RM, p=p_, l=1.5, sk=True); LEG = (LEG | m_) if 'LEG' in dir() else m_
put(cap((LX + 5, 25, -4), (LX + 5, 25, -4), 7.8, 7.8) & (kind == 0), RL, p=newid(), l=2, sk=True)    # knee cap
fx, fz = LX, -4
put(box(fx - 7, fx + 7, -1, 4.5, fz - 4, fz + 10), RS, p=newid(), l=1.5)                      # foot pad (lower tier)
put(box(fx - 5.5, fx + 5.5, 4.5, 7.5, fz - 3, fz + 8) & (kind == 0), RM, p=newid(), l=1.6)  # heel (upper tier)
for a_, L in ((-14, 12), (12, 15), (38, 12)):                                       # 3 toes splayed, foot turned out; separate cream claws
    dr = np.array((math.sin(math.radians(a_)), 0, -math.cos(math.radians(a_))))
    s0 = np.array((fx + 4.5 * dr[0], 3.0, fz - 1)); e0 = s0 + L * dr; p_ = newid()
    tm_ = cap(s0, e0, 3.2, 2.7) & (kind == 0) | cap(s0, e0, 3.2, 2.7) & (pid > 0) & ~(cap(s0, e0, 3.2, 2.7) & (kind == 1) & (pid == BID))
    put(tm_, RS, p=p_, l=2); put(tm_ & (Y > 3.5), RM, p=p_, l=2)
    mid = s0 + .55 * L * dr; put(tm_ & (np.abs((X if fx > 0 else X) * 0 + (AX - mid[0]) * dr[0] + (Z - mid[2]) * dr[2]) < .6), RD, p=p_, l=2)   # toe tile joint
    put(cap(e0 + (0, -.5, 0), e0 + 7.5 * dr + (0, -2.5, 0), 2.8, .8), BONE, st=False)    # claw
    put(cap(e0 + 5.5 * dr + (0, -2.0, 0), e0 + 7.5 * dr + (0, -2.5, 0), 1.4, .8), BONES, st=False)
LEGS = LEG & (kind == 1) & skin                                                     # shaped lower legs: lit fronts, shaded backs, ankle crease
put(LEGS & ~np.roll(kind > 0, 1, axis=2) & (Y < 32), RL, p=0, l=1.5, sk=True)
put(LEGS & ~np.roll(kind > 0, -1, axis=2) & (Y < 32), RS, p=0, l=1.5, sk=True)
put(LEGS & (np.abs(Y - 11) < .6), RD, st=False)


Y = Yg - YO
# ---------------------------------------------------------------- arms: small, clawed, held in front of the chest
AR = chain([(14, 26, -47), (17, 20, -52), (15.5, 19, -58)], [4.2, 3.6, 3.0]) & (kind == 0); ARID = newid()
put(AR, RM, p=ARID, l=2, sk=True); put(AR & (Y > 29), RL, p=ARID, l=2, sk=True)
for dx in (-1.6, 0, 1.6):
    put(chain([(15.5 + dx, 18.5, -60.5), (15.5 + dx, 15.5, -62.5), (15.5 + dx, 14, -62)], [1.6, 1.1, .5]), BONE, st=False)

Zg = Z; HO = 8.0; Yw = Yg - YO - HO
Y = Yw; Z = Zg + 5.0                                                               # head pushed 5 forward along a forward-leaning neck
#                                                        # head held 10 higher over the chest
# ---------------------------------------------------------------- head: huge skull, jaws wide open (z, bottom = upper teeth line, top, half width)
UP = np.array([(-77.5, 49.5, 58.5, 7.5), (-75, 48.5, 60.5, 9.8), (-68, 47.0, 64.0, 11.8), (-60, 46.0, 68.0, 13.3), (-53, 45.0, 70.0, 14.2), (-45, 44.5, 67.0, 13.5)])
ub, ut, uw = prof(Z, UP); um = (ub + ut) / 2; uh = (ut - ub) / 2
pw = np.interp(Z, [-78, -66], [2.2, 4.0])                                           # rounded snout corners head-on
upper = ((AX / uw) ** pw + (np.abs(Y - um) / uh) ** np.minimum(pw, 3) < 1) & (Z > -78) & (Z < -44)
HU = newid()
hide(upper, HU, 1.2, 61)
put(upper & (Y < ub + 1.2) & (AX > uw - 1.6), RD, p=HU, l=1.2)                     # dark lip line
put(upper & (Y < ub + 1.2) & (AX <= uw - 1.6), MOUTHD, st=False)                    # palate
# lower jaw: tilted down, red outer, cream chin/throat underside
LP = np.array([(-72, 22.0, 29.0, 9.8), (-64, 23.5, 32.0, 11.2), (-56, 27.0, 36.5, 12.3), (-50, 31.0, 40.0, 12.8), (-45, 35.0, 44.0, 13.0)])
lb, lt, lw = prof(Z, LP); lm = (lb + lt) / 2; lh = (lt - lb) / 2
lower = ((AX / lw) ** pw + (np.abs(Y - lm) / lh) ** pw < 1) & (Z > -72.5) & (Z < -44)
HL = newid()
hide(lower, HL, 1.2, 35)
put(lower & (Y < lm + .5) & (AX < lw - 1.5), CREAM, p=HL, l=1.2)
put(lower & (Y < lm + .5) & (AX < lw - 1.5) & ((np.floor(Z) % 4) == 0), CREAMS, p=HL, l=1.2)
put(lower & (Y > lt - 1.2) & (AX <= lw - 1.6), MOUTH, st=False)                     # tongue / floor
put((AX < 3.0) & (Z > -68) & (Z < -54) & (np.abs(Y - (lt + .5)) < .6) & ~upper, MOUTH, st=False)   # tongue ridge
cav = (Y < ub) & (Y > lt - .5) & ~upper & ~lower & (Z > -80) & (Z < -45)
put(cav & (Z > -63) & (AX < np.minimum(uw, lw) - 1.5), MOUTHD, st=False)          # dark throat behind the teeth
put(cav & (Z > -57) & (AX >= np.minimum(uw, lw) - 1.5) & (AX < np.minimum(uw, lw)), RS, p=HU, l=1.2, sk=True)   # cheek / mouth corner
throat = lower & (Z > -60) & (Y < lm + .3 * (Z + 60))                        # cream throat behind the jaw (reads from the side)
put(throat, CREAM, p=HL, l=1.2)
chin = lower & (Z < -63) & (Y < lt - 1.5) & (AX < lw - 1)
put(chin, CREAM, p=HL, l=1.2); put(chin & ((np.floor(Y) % 3) == 0), CREAMS, p=HL, l=1.2)
put(throat & (((Y - .55 * Z) % 3.2) < .9), CREAMS, p=HL, l=1.2)
# nostrils + snout plates
put(box(1.5, 4.5, 55.0, 57.0, -78.5, -75.5), BLACK, st=False)
# claw scars: 3 slashes across the upper snout side (outer surface only)
sc_ = upper & (Z > -69) & (Z < -61) & (Y > 54) & (Y < 61) & (AX > uw - 1.6)
tsc = Z + .9 * Y
for c_ in (-16.5, -12.5, -8.5):                                                   # 3 claw slashes: pale cut + dark lower lip
    put(sc_ & (np.abs(tsc - c_) < .75), SCAR, st=False)
    put(sc_ & (tsc - c_ >= .75) & (tsc - c_ < 1.6), MOUTHD, st=False)
# eyes: recessed and flush on the skull side; dark socket, slit with the rear corner high, hot centre, glint
sb_ = upper & (AX > uw - 2.6) & box(7.0, 30, 58.5, 64.5, -69, -52)            # eye: clean slanted almond (rear corner high)
alm = np.zeros(n, bool)
for (za, zb, y) in ((-67, -58, 60), (-67, -55, 61), (-65, -54, 62)):   # front end wraps 2 bricks round the skull corner
    alm |= (np.abs(Y - y) < .5) & (Z > za) & (Z < zb)
ring = np.zeros(n, bool)
for dy_, dz_ in ((1, 0), (-1, 0), (0, 1), (0, -1)): ring |= np.roll(np.roll(alm, dy_, 1), dz_, 2)
put(sb_ & alm, GLOW[2], k=2, st=False)                                             # orange rim
# EYEFIX: one flat amber eye (GLOW[2]), no hot centre / glint
# angry brow: steps down toward the snout, hangs over the eye
BR = newid()
put(box(7.0, 15.5, 64.5, 69.5, -65, -50) & (AX < uw + 1.5), RL, p=BR, l=4, sk=True)
for k_ in range(4):                                                                 # curved stepped bone brow plate rising back into the horn
    put(box(7.5 + .4 * k_, 15.0 - .6 * k_, 68.5 + k_, 69.5 + k_, -64 + 2.5 * k_, -51 + .5 * k_), BONE if k_ < 3 else BONES, st=False, p=newid(), l=5 + k_)
put(box(5.0, 11.5, 63.5, 68.5, -67, -60) & (AX < uw + 1.5), RL, p=BR, l=4, sk=True)
put(box(7.0, 15.5, 64.5, 65.5, -65.2, -64) & (kind == 1), RD, st=False)
# bone horns: brow horn over each eye + bigger horn at the back of the skull, raked back
put(chain([(11, 70, -57), (12, 75, -53), (12.5, 79, -48)], [3.6, 2.4, .7]), BONE, st=False)
put(chain([(11, 68, -48), (12.5, 74.5, -43), (13, 79, -35)], [4.8, 3.0, .8]), BONE, st=False)
# teeth: rows of bone-white teeth, half outside the jaw edge. Upper point down, lower point up.
def tooth(xc, zc, y0, L, down):
    for k in range(L):
        y = y0 - k if down else y0 + k
        w = 1.1 if k < L * .5 else .6                                               # cone: 3x3 base -> 1x1 point
        m_ = (np.abs(AX - (xc - .5)) < w) & (np.abs(Y - y) < .5) & (np.abs(Z - (zc + .5)) < w)
        put(m_, BONE if k < L - 1 else BONES, st=False)
def edge(P, zc, y, up=True):                                                       # real half width of the rounded jaw at height y
    b_, t_, w_ = prof(zc, P); m_ = (b_ + t_) / 2; h_ = (t_ - b_) / 2; p_ = np.interp(zc, [-78, -66], [2.2, 4.0])
    q = 1 - (abs(y - m_) / h_) ** (min(p_, 3) if up else p_)
    return w_ * max(q, 0) ** (1 / p_)
for i, zc in enumerate(range(-71, -44, 5)):
    b_, t_, w_ = prof(zc, UP); w_ = edge(UP, zc, np.floor(b_) + 1) + .8; L = (6, 7, 6, 6, 5, 4)[i]; L = max(3, min(L, int(b_ - prof(zc, LP)[1]) + 1))   # never past the lower jaw
    tooth(int(round(w_ - .8)), zc, int(np.floor(b_)), L, True)
for i, zc in enumerate(range(-69, -46, 5)):
    b_, t_, w_ = prof(zc, LP); w_ = edge(LP, zc, np.ceil(t_) - 1, False) + .8; L = (5, 5, 5, 4, 4)[i]; L = max(3, min(L, int(prof(zc, UP)[0] - t_) + 1))
    tooth(int(round(w_ - .8)), zc, int(np.ceil(t_)), L, False)
ub0 = prof(-73, UP)[0]; lt0 = prof(-70, LP)[1]                                     # front fangs on the rounded snout + chin
eu = edge(UP, -73, np.ceil(ub0)); el = edge(LP, -70, np.floor(lt0), False)
for f, L in ((.3, 5), (.75, 6)):
    tooth(max(2, int(round(eu * f))), -73, int(np.ceil(ub0)), L, True)
    tooth(max(2, int(round(el * f))), -70, int(np.floor(lt0)), L - 2, False)

Y = Yg - YO; Z = Zg
# ---------------------------------------------------------------- tiger stripes: black chevron bars across back, neck, head top + tail
def colmax(x, z):
    xi = int(np.floor(x - lo[0])); zi = int(np.floor(z - lo[2])); ys = np.where(kind[xi, :, zi] == 1)[0]
    return lo[1] + .5 + ys.max() if len(ys) else None
sz = Z + .2 * AX                                                                 # clean chevron bands
SZ = list(range(-37, 0, 9)) + list(range(6, 44, 8)) + list(range(50, 104, 7))
for k_, z0 in enumerate(SZ):
    w_ = 4.0 if z0 < 44 else (3.6 if z0 < 80 else 2.8)
    if z0 < -6: yb = np.interp(z0, BL[:, 0], BL[:, 1]) + 3 + (hsh(k_, 5) % 6)
    else: yb = prof(z0, TP)[0] + .5 + (hsh(k_, 7) % 3) * (1.5 if z0 < 60 else .6)
    m_ = skin & (np.abs(sz - z0) < w_ / 2) & (Y > yb) & ~((Z < -40) & (Y > 60 + HO))           # head top stays clean
    col[m_] = STRIPE
sol_ = kind > 0; zlast = n[2] - 1 - np.argmax(sol_[:, :, ::-1], axis=2)              # rearmost solid brick per (x, y) = what the back view sees
rear = np.zeros(n, bool); ii, jj = np.nonzero(sol_.any(2)); rear[ii, jj, zlast[ii, jj]] = True
isc = (np.abs(col - CREAM).sum(-1) < .05) | (np.abs(col - CREAMS).sum(-1) < .05)
col[rear & isc & (Z > -30)] = RS                                                  # no cream patch between the legs from behind
rear &= skin & (Y > 24) & (Z < 26)                                                          # rump, thigh backs, tail steps
col[rear] = RM                                                                     # back view: plain hide, then whole-row bands
col[rear & (((Y + .025 * AX * AX) % 7) < 2.6)] = STRIPE                          # bands curve around the body

# ---------------------------------------------------------------- spine spikes: bone-white, raked back, neck to tail tip
def pyramid(zc, a, b, H, tz=.7):
    yt = colmax(0.5, zc)
    if yt is None: return
    yt -= YO
    y0 = int(round(yt)) - 1; p_ = newid()
    for k in range(H):
        s = k / max(H, 1); ak = max(a * (1 - .6 * s), .6); bk = max(b * (1 - tz * s), .6)
        m_ = (AX < ak) & (np.abs(Y - (y0 + k)) < .5) & (np.abs(Z - (zc + .55 * k)) < bk)
        put(m_, BONE if k < H - 1 else BONES, st=False, p=p_, l=5)
for zc in list(range(-50, -2, 6)) + list(range(3, 104, 6)):
    if zc < -2: H = int(round(5 + 3 * math.sin(math.pi * (zc + 54) / 56)))
    else: H = int(round(7 - 4.5 * (zc - 2) / 100))
    a = 2.2 if zc < 20 else 1.1
    pyramid(zc, a, 3.0 if zc < 20 else 1.8, max(H, 2))
for zc in (-57, -53):                                                              # head crest
    pyramid(zc, 1.6, 2.0, 3)

Y = Yg
# ---------------------------------------------------------------- audit: drop any brick not 6-connected to the body (no floaters)
sol_ = kind > 0; reach = np.zeros(n, bool); reach[tuple(np.argwhere(sol_ & (pid == BID))[0])] = True
while True:
    g = reach | np.roll(reach, 1, 0) | np.roll(reach, -1, 0) | np.roll(reach, 1, 1) | np.roll(reach, -1, 1) | np.roll(reach, 1, 2) | np.roll(reach, -1, 2)
    g &= sol_
    if g.sum() == reach.sum(): break
    reach = g
print('PALETTE-AUDIT floating bricks removed:', int((sol_ & ~reach).sum()))
kind[sol_ & ~reach] = 0
# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .6
col *= np.clip(.68 + .5 * (Y / 55.0), .68, 1.15)[..., None]                       # lit tops, dark underside
col = np.clip(col, 0, 1)
# voxel-style: PALETTE <= 16: snap every solid brick to its nearest entry.
PAL = np.array([hx(h) for h in ('de4a42', 'b52a2c', '8e1f24', '651419', '440c10',      # crimson light / main / side / dark / seam
                                 '1c1214', '2e1e20',                                  # stripe black / stripe lit
                                 'ecd9ad', 'c7ae7f',                                  # cream belly / band
                                 'f4ecd6', 'cdbf9c',                                  # bone / bone shade
                                 '9a2a30', '4a0d12', '0b0909', 'e88b7e', 'a8875a')])            # mouth / mouth dark / black / scar
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
body = build('TRex', kind == 1, True)
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
    for sx in (1, -1):                                                         # eye lights: amber spill on brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 2200; L.data.color = (1.0, .254, .004)   # = GLOW[2] ff8a0c (linear); L.data.shadow_soft_size = 1.0
        L.location = B(18.0 * sx, 85.0, -63.0)
    for nm, e, rot, an in (('Sun', 2.5, (52, 0, -12), 22), ('FillL', 2.3, (62, 0, -80), 40), ('FillR', 2.5, (62, 0, 80), 40), ('Back', 2.6, (55, 0, 170), 40), ('Under', 1.4, (108, 0, 0), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    U = bpy.data.objects.new('ChinLight', bpy.data.lights.new('ChinLight', 'POINT')); sc.collection.objects.link(U)   # fill under the head: cream throat reads cream
    U.data.energy = 9000; U.data.color = (1, .95, .88); U.data.shadow_soft_size = 6; U.location = B(0, 40, -92)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .78, .82)
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
    for nm, az, el, os_, tg in (('ortho_front', 0, 0, 120, (0, 58, 0)), ('ortho_side', 90, 0, 216, (0, 58, 8)),
                                ('ortho_back', 180, 0, 120, (0, 58, 0)), ('ortho_top', 0, 89.9, 212, (0, 35, 8))):
        if not ONLY or nm in ONLY: view(nm, tg, 400, az, el, ortho=os_)
    for nm, a in (('rest_34', ((0, 52, 4), 320, 48, 12)), ('rest_side', ((0, 56, 8), 310, 90, 4)), ('rest_front', ((0, 58, -20), 245, 0, 6)),
                  ('rest_back', ((0, 38, 28), 230, 165, 16)),
                  ('face', ((0, 70, -68), 130, 0, 4)), ('headside', ((0, 78, -64), 115, 90, 4)), ('head34', ((0, 79, -64), 105, 42, 8)),
                  ('footfront', ((-14, 6, -14), 46, 0, 6)), ('footside', ((-14, 6, -12), 50, -90, 4))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): digitigrade biped + jaw + small arms + tail chain; L = +x
Zd = Z + 5.0; Yd = Y - YO - HO                                                     # head design frame (upper / lower jaw split)
mid = (np.interp(Zd, UP[:, 0], UP[:, 1]) + np.interp(Zd, LP[:, 0], LP[:, 2])) / 2
HEADZ = (Zd < -44.5) & (Y > 44)
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', (0, 56, 0), (0, 58, -22)), ('chest', 'hips', (0, 58, -22), (0, 64, -44)),
       ('neck', 'chest', (0, 64, -44), (0, 74, -56)), ('head', 'neck', (0, 74, -56), (0, 80, -82)), ('jaw', 'head', (0, 64, -50), (0, 50, -76))]
TB = [(0, 55, 8), (0, 55, 30), (0, 54, 54), (0, 53.5, 80), (0, 53, 107)]
TAILB = [('tail%d' % (i + 1), 'hips' if i == 0 else 'tail%d' % i, TB[i], TB[i + 1]) for i in range(4)]
RIG += TAILB
OVR = [((kind > 0) & (Z < -26), 'chest'), ((kind > 0) & (Z < -44) & (Y > 62), 'neck'), (HEADZ & (Yd >= mid), 'head'), (HEADZ & (Yd < mid), 'jaw'), ((Y > 86) & (Z < -30) & (Z > -66), 'head')]
OVR += brick_rig.limb(X, Y, Z, (Z > 12) & (kind > 0), TAILB)
for sx, sd in ((1, 'L'), (-1, 'R')):
    ch = [('thigh' + sd, 'hips', (15 * sx, 46, -6), (19 * sx, 25, -4)), ('shin' + sd, 'thigh' + sd, (19 * sx, 25, -4), (14 * sx, 10, 5)),
          ('foot' + sd, 'shin' + sd, (14 * sx, 10, 5), (14 * sx, 2, -16))]
    ar = [('upperarm' + sd, 'chest', (14 * sx, 41, -47), (17 * sx, 35, -52)), ('forearm' + sd, 'upperarm' + sd, (17 * sx, 35, -52), (15.5 * sx, 31, -63))]
    RIG += ch + ar
    side = X * sx > 0
    leg = side & (kind > 0) & ((TH & (Z > -22)) | ((X * sx > 5) & (Y < 37) & (Z > -32) & (Z < 13)))
    arm = side & (kind > 0) & (AR | ((X * sx > 12) & (X * sx < 19.5) & (Z < -58) & (Z > -66) & (Y > 27) & (Y < 36)))   # arm bricks + bone claws
    OVR += brick_rig.limb(X, Y, Z, leg, ch) + brick_rig.limb(X, Y, Z, arm, ar)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'jaw': (-20, 0, 0), 'head': (15, 0, 0), 'thighL': (35, 0, 0), 'shinL': (-30, 0, 0), 'upperarmR': (-40, 0, 0),
                       'tail2': (0, 0, 20), 'tail3': (0, 0, 25)},
                 render='render' in argv)
print('BL_OK')
