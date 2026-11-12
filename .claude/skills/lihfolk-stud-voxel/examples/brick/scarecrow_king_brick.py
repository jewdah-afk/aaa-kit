# Pumpkin Scarecrow King (stud-voxel brick pipeline). Reference = ScarecrowKing/concept_sheet.jpg
# GLOW: subtle   (eyes / mouth / inner head light only; point light inside the head)
# Design coords: x right (= the character's LEFT), y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
# Copied from stud-voxel-creatures/examples/brick/war_rhino_brick.py (mesh + render), model part rewritten.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'ScarecrowKing'

lo = np.array((-78.0, -0.5, -38.0)); hi = np.array((44.0, 132.5, 26.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
XW, YW, ZW = X, Y, Z
LEAN = .12                                   # upper body leans forward: body z = world z + LEAN * (y - 50) above the hips
TILT = math.radians(9)                       # head tilts toward +x, pivot (0, 88) in the body frame
def frame(kind_='world'):
    """switch the coordinate arrays every shape function reads: 'world', 'body' (lean), 'head' (lean + tilt)"""
    global X, Y, Z, AX
    X, Y, Z = XW, YW, ZW
    if kind_ in ('body', 'head'): Z = ZW + LEAN * np.clip(YW - 50, 0, None)
    if kind_ == 'head':
        X = XW * math.cos(TILT) - (YW - 88) * math.sin(TILT); Y = 88 + XW * math.sin(TILT) + (YW - 88) * math.cos(TILT)
    AX = np.abs(X)
def tobody(pw): return (pw[0], pw[1], pw[2] + LEAN * max(pw[1] - 50, 0))
TAG = np.zeros(n, np.int8); TAGNOW = [0]      # 0 other, 1 pole/blade, 2 gripping fist (voxel clearance test)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
PK_L, PK, PK_D = hx('f59a2c'), hx('e2701c'), hx('a8460f')          # pumpkin
GR_L, GR, GR_D = hx('7f8a3a'), hx('5e6a2a'), hx('3c4220')          # coat
WD_L, WD, WD_D = hx('9c6638'), hx('6e4424'), hx('3f2412')          # wood
HAT = hx('5e3b34'); STR_L, STR_D = hx('f2c84c'), hx('c08a2a'); TAN = hx('d8b67e')
MET, MET_L = hx('848a93'), hx('b8bdc4'); BLACK = hx('17171c')
GLOW = {2: hx('ff6410'), 3: hx('ffae22'), 4: hx('fff2a6')}

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l; TAG[m] = TAGNOW[0]

def sd_ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def bx(x0, x1, y0, y1, z0, z1):                     # plain box (signed x)
    return (X > x0) & (X < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def capd(a, b, ra, rb):                              # capsule distance - radius
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d - (ra + (rb - ra) * t)
def chaind(pts, radii):
    d = np.full(n, 1e9)
    for i in range(len(pts) - 1): d = np.minimum(d, capd(pts[i], pts[i + 1], radii[i], radii[i + 1]))
    return d
def chain(pts, radii): return chaind(pts, radii) <= 0
def h3(a, b, c, s=1.0):                              # hash noise 0..1 on cells of size s
    v = np.sin(np.floor(a / s) * 12.9898 + np.floor(b / s) * 78.233 + np.floor(c / s) * 37.719) * 43758.5453
    return v - np.floor(v)
def mir(p): return (-p[0], p[1], p[2])

rng = np.random.RandomState(11)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
def wood(m, p, l, grain=True):                       # bark with vertical grain streaks
    put(m, WD, p=p, l=l)
    g = h3(X, Y, Z * 1.7, 1.0) if grain else np.zeros(n)
    s = h3(X + 3, np.floor(Y / 4), Z, 1.0)
    put(m & (s < .22), WD_D, p=p, l=l); put(m & (s > .82), WD_L, p=p, l=l)

# ---------------------------------------------------------------- legs: gnarled sticks, knees bent, left foot forward, right foot back
LEGS = {1: ((5.5, 47, 0.5), (8.0, 27, -6.5), (9.5, 5, -6.0), -6.0), -1: ((-5.5, 47, 1.0), (-8.5, 26, -1.5), (-11.5, 5, 4.0), 4.0)}
for sx in (1, -1):
    hip, knee, ank, fz = LEGS[sx]
    d = chaind([hip, knee, ank], [2.6, 2.4, 2.6])
    for t, r in ((.18, 3.0), (.42, 2.8), (.5, 3.5), (.66, 2.9), (.86, 3.1)):     # knots along thigh / shin
        q = np.array(hip) + (np.array(knee) - np.array(hip)) * t * 2 if t < .5 else np.array(knee) + (np.array(ank) - np.array(knee)) * (t - .5) * 2
        o = 1.0 if (int(t * 100) % 2) else -1.0
        d = smin(d, sd_ell((q[0] + .7 * o * sx, q[1], q[2] - .5), (r, r * 1.15, r)), 1.0)
    p = newid(); wood(d < 0, p, 1)
    put((d < 0) & (np.abs(Y - knee[1]) < .6), WD_D, p=p, l=1)            # knee ring
    k_ = np.array(knee); h_ = np.array(hip); a_ = np.array(ank)
    s1 = h_ + (k_ - h_) * .55; s2 = k_ + (a_ - k_) * .55
    put(chain([tuple(s1), tuple(s1 + (3.0 * sx, 2.5, -1.5))], [1.1, .5]), WD, p=newid(), l=2)   # broken twig stubs
    put(chain([tuple(s2), tuple(s2 + (2.5 * sx, -1.5, -2.5))], [1.0, .45]), WD, p=newid(), l=2)
    # foot: small stepped block + 5 tapering roots spreading over the ground
    fx0 = ank[0]
    put(bx(fx0 - 4, fx0 + 4, -1, 3, fz - 4.5, fz + 4.5), WD, p=newid(), l=0)
    put(bx(fx0 - 3, fx0 + 3, 2.9, 5, fz - 3, fz + 3.5), WD_L, p=newid(), l=1)
    for ang_, L in ((-150, 9), (-115, 12), (-85, 13), (-55, 11), (25, 7)):  # degrees in the x-z plane, -90 = forward
        a_r = math.radians(ang_ if sx < 0 else 180 - ang_)
        e = (fx0 + L * math.cos(a_r), .5, fz + L * math.sin(a_r))
        mid = (fx0 + L * .5 * math.cos(a_r), 2.2, fz + L * .5 * math.sin(a_r))
        put(chain([(fx0, 3.0, fz), mid, e], [2.2, 1.4, .6]), WD_D, p=newid(), l=2)

frame('body')
# ---------------------------------------------------------------- coat: narrow, open at the front, lower coat = long ragged strips
dT = sd_ell((0, 77.5, 0.5), (6.6, 10.0, 4.8))
dT = smin(dT, sd_ell((0, 82.5, 0.5), (11.0, 3.8, 5.4)), 2.5)
for sx in (1, -1): dT = smin(dT, sd_ell((13.8 * sx, 82.5, 0.5), (4.8, 3.6, 5.2)), 1.5)
w = 7.4 + np.clip(71 - Y, 0, None) * .13; dz = 5.0 + np.clip(71 - Y, 0, None) * .055
sk = (np.abs(X / w) ** 2.6 + np.abs((Z - .5) / dz) ** 2.2) ** (1 / 2.4) - 1
dSf = np.where(Y < 72, sk * np.minimum(w, dz), 9)
a = np.arctan2(X, -(Z - .5)); SEC = .42
si = np.floor(a / SEC); fr = a / SEC - si
hs = h3(si, 7, 1, 1.0); hs2 = h3(si, 3, 9, 1.0)
sbot = 18 + 22 * hs2                                                       # each strip ends at its own height
gap0 = .14 + .1 * hs                                                       # gap on each side of a strip
cen = np.abs(fr - .5) * 2                                                  # 0 strip middle, 1 strip edge
inner = (fr > gap0) & (fr < 1 - gap0)
tipy = sbot + 5 * cen                                                      # pointed strip ends
strip_ok = (Y > 60) | (inner & (Y > tipy))                                 # solid band under the belt, strips below
dS = np.where(strip_ok, dSf, 9)
skirt = (dS < 0) & (dS > -2.6)
coat = (dT < 0) | skirt
opening = (np.abs(X) < 1.6 + np.clip(86 - Y, 0, 16) * .1) & (Z < -1) & (Y > 60)          # open front
coat &= ~opening
PC = newid()
put(coat, GR, p=PC, l=2)
big = h3(X, Y, Z, 7.0)                                                     # big flat colour zones
put(coat & (big < .3), GR_D, p=PC, l=2); put(coat & (big > .8), GR_L, p=PC, l=2)
put(skirt & (Y < 60) & (hs > .62), GR_D, p=PC, l=2)                        # whole darker strips
put(skirt & (Y < 60) & (hs < .18), GR_L, p=PC, l=2)
put(skirt & (Y < tipy + 2.5) & (Y < 60), GR_D, p=PC, l=2)                 # strip ends darker
put(skirt & (dS < -1.6), WD_D, p=PC, l=2)                                  # dark lining
# wooden torso stick (seen through the open front) + crossbar inside the shoulders
wood(chain([(0, 44, 0.5), (0, 89, -0.5)], [2.5, 2.3]), newid(), 1)
put(chain([(0, 44, 0.5), (0, 89, -0.5)], [2.5, 2.3]) & (np.abs(Y % 6 - 3) < .6), WD_D, p=newid(), l=1)   # lashing marks
# patches (proud plates) with stitches on the border
dcS = np.minimum(dT, dS)
def patch(xa, xb, ya, yb, front, rgb, st=TAN):
    reg = bx(xa, xb, ya, yb, -30 if front else 0, 0 if front else 30)
    m_ = reg & (dcS < 1.0) & (dcS >= -.2) & ~opening & strip_ok
    pp = newid(); put(m_, rgb, p=pp, l=3)
    edge = m_ & ((X < xa + 1.1) | (X > xb - 1.1) | (Y < ya + 1.1) | (Y > yb - 1.1))
    put(edge & ((np.floor(X) + np.floor(Y)) % 2 == 0), st, p=pp, l=3)
patch(-10.5, -2.0, 47, 59, True, WD_L)
patch(2.5, 10.5, 61, 69, True, TAN, WD_D)
patch(-7.5, -1.5, 75, 83, True, WD_L)
patch(0.5, 10.5, 44, 57, False, PK_D)
patch(-10.5, -3.5, 62, 70, False, TAN, WD_D)
# belt: twisted rope + knot + hanging ends
belt = (dcS < 1.2) & (dcS > -1.5) & (np.abs(Y - 70) < 1.3) | ((np.abs(X) < 3.5) & (np.abs(Y - 70) < 1.3) & (Z < -1) & (Z > -6.5))
PB = newid(); put(belt, TAN, p=PB, l=4)
put(belt & ((np.floor(X) + np.floor(Z) + 2 * np.floor(Y)) % 4 == 0), STR_D, p=PB, l=4)
put(sd_ell((0, 70, -6.6), (2.4, 2.1, 1.7)) < 0, TAN, p=PB, l=5)
for ex, ez in ((-1.3, -7.0), (1.6, -6.7)):
    put(chain([(ex, 69, ez), (ex * 1.2, 63, ez - .4), (ex * 1.4, 56, ez - .2)], [.9, .8, .7]), TAN, p=PB, l=5)
    put(chain([(ex * 1.4, 56.5, ez - .2), (ex * 1.4, 54.5, ez - .2)], [1.1, .6]), STR_D, p=PB, l=5)

# ---------------------------------------------------------------- arms: right arm reaches out to the scythe fist, left claw raised and spread
FIST = np.array((-31.0, 60.0, -11.0))                                  # world centre of the right fist (the pole runs through it)
PB0 = np.array((-26.0, 1.0, -5.0))                                   # pole foot (world); the pole is a straight line foot -> fist -> top
PAX = (FIST - PB0) / np.linalg.norm(FIST - PB0)
PTOP = PB0 + PAX * ((117.0 - PB0[1]) / PAX[1])
ARM = {}
FB = np.array(tobody(FIST))
ARMS = {-1: ((-14.5, 83, 0.5), (-22.5, 66.0, -2.5), tuple(FB + (3.5, -.8, 1.2))),        # wrist enters the fist from the body side
        1: ((14.5, 83, 0.5), (23.0, 71.0, -6.0), (18.0, 76.0, -17.0))}                  # grabbing: elbow bent out, forearm reaching forward at chest height
for sx in (1, -1):
    sh, el, wr = ARMS[sx]
    ARM[sx] = (sh, el, wr)
    wood(chain([sh, el, wr], [1.9, 1.8, 1.6 if sx > 0 else 1.2]), newid(), 1)      # slim right wrist into the fist
    wood(sd_ell(el, (2.6, 2.6, 2.6)) < 0, newid(), 1)
    ax_ = np.array(el) - np.array(sh); L_ = np.linalg.norm(ax_); u = ax_ / L_
    t = ((X - sh[0]) * u[0] + (Y - sh[1]) * u[1] + (Z - sh[2]) * u[2])
    rad = np.sqrt((X - sh[0] - u[0] * t) ** 2 + (Y - sh[1] - u[1] * t) ** 2 + (Z - sh[2] - u[2] * t) ** 2)
    ang = np.arctan2(Z - sh[2] - u[2] * t, X - sh[0] - u[0] * t)
    tend = 8.5 + 4.0 * np.abs(((ang * 6 / math.pi) % 2) - 1) * (1 + .6 * h3(np.floor(ang * 6 / math.pi), sx, 0))
    sl = (t > -1) & (t < tend) & (rad < 4.2 + t * .2) & (rad > 1.2)
    put(sl & ~coat, GR, p=PC, l=2)
    put(sl & ~coat & (h3(X, Y, Z, 6.0) < .35), GR_D, p=PC, l=2)

def strand(a, b, r0, r1, rgb, p, l=6):
    put(chain([a, b], [r0, r1]), rgb, p=p, l=l)
def tuft(base, dirs, L, p, rad=(1.5, .8)):
    for i, dv in enumerate(dirs):
        dv = np.array(dv, float); dv /= np.linalg.norm(dv)
        ll = L * (.75 + .5 * rng.rand())
        strand(base, tuple(np.array(base) + dv * ll), rad[0], rad[1], STR_L if i % 2 == 0 else STR_D, p)
def fan(base, dirv, side, L, k=7, spread=1.1, p=0, rad=(1.5, .8)):          # bushy fan of straw in the plane of dirv and side
    dirv = np.array(dirv, float); dirv /= np.linalg.norm(dirv); side = np.array(side, float); side /= np.linalg.norm(side)
    ds = [dirv * math.cos(s) + side * math.sin(s) for s in np.linspace(-spread / 2, spread / 2, k)]
    tuft(base, ds, L, p, rad)

# left hand (+x): reaching toward the viewer at chest height, long twig fingers hooked forward/down (grabbing)
wr = np.array(ARM[1][2]); fw = wr - np.array(ARM[1][1]); fw /= np.linalg.norm(fw)
pc = tuple(wr + fw * 2.4)
wood(sd_ell(pc, (2.8, 2.4, 2.8)) < 0, newid(), 2)
for i, ox in enumerate((-2.4, -.8, .8, 2.4)):
    L = 1.0 if i in (1, 2) else .85
    b0 = np.array(pc) + (ox, .3, -2.0)
    pts = [tuple(b0), tuple(b0 + (ox * .5, 1.0, -5.0 * L)), tuple(b0 + (ox * .7, -1.5, -9.5 * L)), tuple(b0 + (ox * .6, -6.0 * L, -11.0 * L)), tuple(b0 + (ox * .5, -8.5 * L, -9.5 * L))]
    put(chain(pts, [1.15, 1.0, .85, .65, .45]), WD, p=newid(), l=3)
    put(sd_ell(pts[1], (1.35, 1.35, 1.35)) < 0, WD_L, p=newid(), l=3)      # knuckle knot
    put(chain(pts[3:], [.65, .45]), WD_D, p=newid(), l=3)                  # dark claw tips
th = np.array(pc) + (-2.6, -.8, -1.0)
put(chain([tuple(th), tuple(th + (-2.0, -1.5, -4.5)), tuple(th + (-1.0, -5.0, -6.5))], [1.15, .9, .5]), WD, p=newid(), l=3)   # thumb

# ---------------------------------------------------------------- right fist: 4 separate twig fingers wrapped AROUND the pole (world frame)
frame('world')
TAGNOW[0] = 2
WRW = np.array(ARM[-1][2]); WRW = np.array((WRW[0], WRW[1], WRW[2] - LEAN * max(WRW[1] - 50, 0)))     # wrist back in world coords
bk = (WRW - FIST) - PAX * ((WRW - FIST) @ PAX); E1 = bk / np.linalg.norm(bk)                      # palm side (toward the wrist)
E2 = np.cross(PAX, E1)
PF = newid()
put(chaind([tuple(FIST + E1 * 2.9 + PAX * -3.6), tuple(FIST + E1 * 2.9 + PAX * 3.6)], [1.5, 1.5]) <= 0, WD, p=PF, l=3)   # palm behind the shaft
def ring(t, r_, a0, a1, k=10): return [tuple(FIST + PAX * t + r_ * (math.cos(math.radians(a)) * E1 + math.sin(math.radians(a)) * E2)) for a in np.linspace(a0, a1, k)]
for k_, t in enumerate((-3.3, -1.1, 1.1, 3.3)):                              # 2-brick fingers, ~1-brick gaps between them
    pts = ring(t, 2.85, 15, 300 - 12 * k_)
    put(chain(pts, [1.0] * 8 + [.9, .75]), WD_L, p=PF, l=3)
    kn = ring(t, 3.35, 150, 150, 1)[0]
    put(sd_ell(kn, (1.15, 1.15, 1.15)) < 0, WD, p=PF, l=3)                  # knuckle bump
    put(chain(pts[-2:], [.9, .75]), WD_D, p=PF, l=3)                         # fingertip
tp = [tuple(FIST + E1 * 2.9 + PAX * 3.6), tuple(FIST + PAX * 5.0 + E1 * 1.5 + E2 * 2.0)] + ring(5.2, 2.6, 110, 200, 4)
put(chain(tp, [1.1, 1.0, .95, .85, .75, .6]), WD, p=PF, l=3)                # thumb hooking over the top
TAGNOW[0] = 0
# ---------------------------------------------------------------- scythe: wrapped pole + big rusty hook blade over the head
TAGNOW[0] = 1
PP = newid()
def axd(t0, t1, r0, r1): return chaind([tuple(PB0 + PAX * t0), tuple(PB0 + PAX * t1)], [r0, r1])
PLEN = np.linalg.norm(PTOP - PB0)
pole = axd(0, PLEN + 1, 1.8, 1.65) <= 0
wood(pole, PP, 2)
tP = (np.stack([X - PB0[0], Y - PB0[1], Z - PB0[2]], -1) @ PAX)
tf = (FIST - PB0) @ PAX
put(pole & (np.abs(tP - tf) < 4.6), WD_D, p=PP, l=2)                      # shaft darker inside the grip (dark gaps between the fingers)
for c_ in (24, tf + 9, 88, 102):                                          # tan wraps (one just above the fist)
    t_ = (c_ - PB0[1]) / PAX[1] if c_ != tf + 9 else c_
    band = (axd(t_ - 2, t_ + 2, 2.45, 2.45) <= 0) & (np.abs(tP - t_) < 2)
    bp_ = newid(); put(band, TAN, p=bp_, l=3); put(band & (np.abs(tP - t_) < .55), WD_L, p=bp_, l=3)
BZ = (np.abs(Z - PTOP[2]) < 1.0)                                   # blade: 2 bricks thick, a tapered hook in the x-y plane
BC, BR = (PTOP[0] - 13.0, PTOP[1] - 12.0), 15.0
def arc_d(a0, a1, r0, r1, steps=24):                                           # 2-D distance to a tapered arc (minus radius)
    d = np.full(n, 1e9)
    for k_ in range(steps):
        t0, t1 = k_ / steps, (k_ + 1) / steps
        A = np.radians(a0 + (a1 - a0) * t0); B_ = np.radians(a0 + (a1 - a0) * t1)
        p0 = np.array((BC[0] + BR * math.cos(A), BC[1] + BR * math.sin(A))); p1 = np.array((BC[0] + BR * math.cos(B_), BC[1] + BR * math.sin(B_)))
        ab = p1 - p0; t = np.clip(((X - p0[0]) * ab[0] + (Y - p0[1]) * ab[1]) / ab.dot(ab), 0, 1)
        rr_ = r0 + (r1 - r0) * (t0 + (t1 - t0) * t) ** 1.2
        d = np.minimum(d, np.hypot(X - p0[0] - ab[0] * t, Y - p0[1] - ab[1] * t) - rr_)
    return d
bd = arc_d(28, 236, 4.2, .55)
rB = np.hypot(X - BC[0], Y - BC[1])
blade = BZ & (bd < 0) & (X < PTOP[0] - 1.0) & ~(axd(0, PLEN + 1, 1.9, 1.9) <= 0)
PBL = newid()
put(blade, MET, p=PBL, l=4)
put(blade & (rB > BR + 1.6), hx('5c6068'), p=PBL, l=4)                     # dark spine
put(blade & (rB < BR - 1.4), MET_L, p=PBL, l=4)                            # bright cutting edge (inner curve)
rust = blade & (rB > BR - 1.4) & (h3(X, Y, 0, 2.0) < .55)
put(rust, PK_D, p=PBL, l=4); put(rust & (h3(X, Y, 1, 1.0) < .3), PK, p=PBL, l=4)
put(blade & (rB > BR + 2.4) & ((np.floor(X) + np.floor(Y)) % 3 == 0), WD_D, p=PBL, l=4)    # notched rusty spine
put(axd(PLEN - 7, PLEN + 1, 1.95, 1.95) <= 0, hx('5c6068'), p=newid(), l=5)   # socket
put(axd(PLEN + 1, PLEN + 3, 1.3, .8) <= 0, MET, p=newid(), l=5)
TAGNOW[0] = 0
frame('head')

# ---------------------------------------------------------------- head: ribbed jack-o-lantern, recessed glowing face
HC = (0, 95.5, -2.5)
ang = np.arctan2(X - HC[0], -(Z - HC[2]))
rib = np.clip((np.cos(10 * ang) - .55) / .45, 0, 1)
dH = sd_ell(HC, (10.8, 8.8, 9.6))
head = dH < -.7 * rib
HID = newid()
put(head, PK, p=HID, l=3)
put(head & (rib > .35), PK_D, p=HID, l=3)
put(head & (rib < .05) & (np.cos(10 * ang) < -.6) & (Y > HC[1] - 2), PK_L, p=HID, l=3)
put(head & (Y < HC[1] - 6.0), PK_D, p=HID, l=3)
# neck stick under the head (hidden by the ruff)
wood(chain([(0, 84, 0.5), (0, 89, -1.5)], [2.2, 2.2]), newid(), 1)
# face: pixel map in the front (x, y) plane (row keys = integer y centres), left half mirrored. '#' = carved hole (glow at the back), 'o' = hot eye centre
FACE = {100: "..##.......",
        99:  "..####.....",
        98:  "...#oo##...",
        97:  "....####...",
        96:  ".....##....",
        93:  ".#.........",
        92:  "..##.##.##.",
        91:  "..#########",
        90:  "...##.##.##"}
face = np.zeros(n, bool); eyec = np.zeros(n, bool)
for yv, row in FACE.items():
    full = row + row[::-1]
    for i, ch in enumerate(full):
        if ch == '.': continue
        m_ = (np.abs(X - (-10.5 + i)) <= .5) & (np.abs(Y - yv) < .5)        # exact cover also in the tilted head frame
        face |= m_
        if ch == 'o': eyec |= m_
zf = np.argmax(head, axis=2)[..., None]; hasf = head.any(axis=2)[..., None]
dep = np.arange(n[2])[None, None, :] - zf
fz = face & hasf & (Z < HC[2])
kind[fz & (dep < 2)] = 0; col[fz & (dep < 2)] = 0
put(fz & (dep >= 2) & (dep < 4), GLOW[3], k=3, st=False)
# EYEFIX: one flat face glow (no hot eye centre)
rim = head & ~face & (Z < HC[2]) & (dep < 3)                                       # darker cut walls around each hole
nb = np.zeros(n, bool)
for ax_ in (0, 1):
    for s_ in (1, -1): nb |= np.roll(face & hasf & (dep < 2), s_, axis=ax_)
put(rim & nb & (dep >= 1), PK_D, p=HID, l=3)

# ---------------------------------------------------------------- hat: crooked witch hat, tattered drooping brim, buckle band, bent tip
rr = np.hypot(X - 0, Z - (-1.5)); ha = np.arctan2(X, Z + 1.5)
HS = .40; hsi = np.floor(ha / HS); ht = np.abs((ha / HS - hsi) - .5) * 2
redge = 17.5 + 4.5 * h3(hsi, 5, 0, 1.0) * (1 - ht) + 1.0 * ht
by = 105.0 + .09 * X - .035 * np.clip(rr - 9, 0, None) ** 2 + 1.3 * np.cos(2 * ha) * (rr / 24) + .5 * np.sin(3 * ha) * (rr / 24)   # sides droop, front lifts
brim = (rr < redge) & (Y > by - 1.6) & (Y < by + .7)
PH = newid()
put(brim, HAT, p=PH, l=5)
put(brim & (rr > redge - 2.4) & (h3(X, 0, Z, 1.0) < .45), WD_D, p=PH, l=5)
put(brim & (Y < by - .6) & (rr > 9), WD_D, p=PH, l=5)                          # dark underside
# crown: short cone, leans back, the top third bends over to the character's right (-x) in a crooked zigzag
cyc = np.clip((Y - 104) / 17.5, 0, 1)
ccx = -6.5 * np.clip((Y - 112) / 9.5, 0, 1) ** 1.6
ccz = -1.5 + 3.5 * np.clip((Y - 106) / 15, 0, 1) ** 1.5
crad = 8.4 * (1 - cyc) ** .85 + .9
crown = (np.hypot(X - ccx, Z - ccz) < crad) & (Y > 104) & (Y < 121.5)
crown |= chain([(-6.0, 120.8, 2.0), (-9.5, 123.0, 2.6), (-12.0, 121.0, 3.0), (-15.5, 122.6, 3.2), (-18.0, 125.4, 3.2)], [1.7, 1.35, 1.1, .85, .55])
put(crown, HAT, p=PH, l=6)
put(crown & (h3(X, Y, Z, 2.0) < .22), WD_D, p=PH, l=6)
put(crown & (np.cos(7 * np.arctan2(X - ccx, Z - ccz)) > .88) & (Y < 118), WD_D, p=PH, l=6)      # dent folds
band = (np.hypot(X - ccx, Z - ccz) < crad + 1.0) & (Y > 105.4) & (Y < 109.0) & ~(np.hypot(X - ccx, Z - ccz) < crad - 2.2)
PBd = newid(); put(band, PK_D, p=PBd, l=7)
bk = band & (Z < -6) & (AX < 3.6)
put(bk, STR_L, p=newid(), l=8)
put(bk & (AX < 2.0) & (Y > 106.4) & (Y < 108.0), HAT, p=newid(), l=8)

frame('body')
# ---------------------------------------------------------------- straw: collar ruff, wrist cuffs, waist and hem clumps
PS = newid()
for ring, (y0, rad0, n_, L, dy) in enumerate(((87.0, 5.5, 26, 11.0, -.45), (88.8, 4.5, 20, 8.0, -.12))):
    for i in range(n_):
        th = (i + .5 * ring) / n_ * 2 * math.pi
        b = (rad0 * math.sin(th), y0, -0.5 - rad0 * math.cos(th) * .9)
        dv = np.array((math.sin(th), dy + .2 * rng.randn(), -math.cos(th) * .9)); dv /= np.linalg.norm(dv)
        ll = L * (.7 + .5 * rng.rand())
        strand(b, tuple(np.array(b) + dv * ll), 1.5, .75, STR_L if (i + ring) % 2 == 0 else STR_D, PS, 6 + ring)
for sx in (1, -1):
    sh, el, wr = ARM[sx]
    u = np.array(wr) - np.array(el); u /= np.linalg.norm(u)
    pa = np.cross(u, (0, 0, 1)); pa /= np.linalg.norm(pa); pb = np.cross(u, pa)
    base = np.array(wr) - u * (7.5 if sx < 0 else .5)                       # right cuff sits up the forearm, clear of the pole
    for k in range(11):
        dv = math.cos(k * 2 * math.pi / 11) * pa + math.sin(k * 2 * math.pi / 11) * pb + u * .5; dv /= np.linalg.norm(dv)
        if sx < 0 and (dv[0] < -.25 or dv[2] < -.45): continue                    # no straw toward the pole
        strand(tuple(base + dv * 1.2), tuple(base + dv * ((4.0 if sx < 0 else 5.5) + 2 * rng.rand())), 1.4, .7, STR_L if k % 2 == 0 else STR_D, PS, 6)
    fan((8.0 * sx, 67.0, -1.0), (sx, -.8, -.2), (0, 0, 1), 8.0, 7, 1.4, PS)            # waist, bursting out sideways
    fan((5.5 * sx, 56.0, -6.5), (sx * .3, -1, -.5), (1, 0, 0), 9.0, 6, 1.2, PS)        # between the front strips
    fan((7.0 * sx, 54.0, 5.5), (sx * .3, -1, .5), (1, 0, 0), 8.0, 5, 1.1, PS)          # between the back strips
    fan((9.5 * sx, 52.0, 0.0), (sx, -1, 0), (0, 0, 1), 7.5, 5, 1.1, PS)                # sides
fan((0, 72.5, -4.5), (0, .2, -1), (1, 0, 0), 4.0, 5, 1.6, PS, (1.1, .6))               # poking out over the belt / open front

# ---------------------------------------------------------------- crow on the right shoulder (-x, image left in the front view)
CW = (-18.5, 92.0, 2.0)
dc_ = sd_ell(CW, (3.8, 4.6, 6.2))
dc_ = smin(dc_, sd_ell((-18.5, 98.0, -2.6), (3.3, 3.3, 3.4)), 1.4)
dc_ = smin(dc_, chaind([(-18.5, 91, 6.5), (-18.5, 86.5, 12.0)], [2.4, 1.1]), .6)        # tail
pc_ = newid(); put(dc_ < 0, BLACK, p=pc_, l=7)
for wx in (-1, 1):
    wing = (sd_ell((-18.5 + 3.1 * wx, 92.4, 3.2), (1.2, 3.6, 5.2)) < 0) & ~(dc_ < -1.4)
    put(wing, hx('2a2a35'), p=newid(), l=8)                                         # folded wings
put(chain([(-18.5, 97.6, -5.6), (-18.5, 96.8, -10.4)], [1.45, .45]), MET, p=newid(), l=8)                      # beak
eye = (sd_ell((-18.5, 98.6, -3.4), (4.0, 1.25, 1.25)) < 0) & (dc_ < 0) & (dc_ > -1.4)
put(eye, STR_L, p=newid(), l=8)                                                    # yellow eyes, flush on both sides
put(eye & (np.abs(Y - 98) < .6) & (Z > -3.5), BLACK, p=newid(), l=8)                # pupil
put(chain([(-17.4, 88.0, 2.0), (-16.6, 84.0, 1.5)], [.8, .7]) | chain([(-19.6, 88.0, 2.0), (-19.6, 84.0, 1.5)], [.8, .7]), WD_D, p=newid(), l=7)

frame('world')
# ---------------------------------------------------------------- voxel test: the pole touches nothing but its fist (2-brick clearance)
def dil(m, r):
    for _ in range(r):
        g = m.copy()
        for ax_ in range(3): g = g | np.roll(g, 1, axis=ax_) | np.roll(g, -1, axis=ax_)
        m = g
    return m
polec = (TAG == 1) & (kind > 0)
nearF = np.linalg.norm(np.stack([X - FIST[0], Y - FIST[1], Z - FIST[2]], -1), axis=-1) < 6.0
clash = dil(polec, 2) & (kind > 0) & (TAG == 0) & ~nearF
lost = pole & ~polec                                                           # pole cells overwritten by another part
print('VOX_OK POLE_TEST clash', int(clash.sum()), 'overwritten', int(lost.sum()), 'fist', int(((TAG == 2) & (kind > 0)).sum()))
if clash.any():
    w_ = np.argwhere(clash); print('VOX_OK POLE_TEST first clashes', [tuple(np.round(lo + .5 + q_, 1)) for q_ in w_[:6]])
# ---------------------------------------------------------------- keep only bricks 26-connected to the main body
sol = kind > 0
seed = np.zeros(n, bool); seed[:, :4, :] = sol[:, :4, :]
reach = seed.copy()
for it in range(400):
    g = reach.copy()
    for ax_ in range(3): g = g | np.roll(g, 1, axis=ax_) | np.roll(g, -1, axis=ax_)
    g &= sol
    if (g == reach).all(): break
    reach = g
drop = sol & ~reach
print('FLOOD dropped', int(drop.sum()), 'bricks')
kind[drop] = 0

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .5
col *= np.clip(.82 + .28 * (Y / 120.0), .82, 1.12)[..., None]                      # lit tops, dark underside
col = np.clip(col, 0, 1)
# voxel-style: VOXEL SIZE = 1 unit (= 2.5 studs in game). PALETTE <= 16: snap every solid brick to its nearest entry.
PAL = np.array([hx(h) for h in ('f59a2c', 'e2701c', 'a8460f',            # pumpkin light / main / dark (also rust, hat band)
                                 '7f8a3a', '5e6a2a', '3c4220',            # coat green
                                 '9c6638', '6e4424', '3f2412',            # wood / patches
                                 '5e3b34',                                # hat
                                 'f2c84c', 'c08a2a', 'd8b67e',            # straw light / dark / rope tan
                                 '848a93', 'b8bdc4', '17171c')])          # metal / blade edge / crow black
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
body = build('ScarecrowKing', kind == 1, True)
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
    for nm_, loc, en in (('HeadLight', (0, 95.5, -2.5), 600), ('FaceLight', (0, 95.0, -15.0), 220)):   # inner head light + spill on the face
        L = bpy.data.objects.new(nm_, bpy.data.lights.new(nm_, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = en; L.data.color = tuple(GLOW[3]); L.data.shadow_soft_size = 1.5; L.location = B(*loc)
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
    cen = (-8, 64, -2); D = 245
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (-11, 64, 0), 400, az, el, ortho=146)
    for nm, a in (('rest_34', (cen, D, -35, 10)), ('rest_side', (cen, D, 90, 6)), ('rest_front', (cen, D, 0, 6)), ('rest_back', (cen, D, 150, 14)),
                  ('face', ((0, 95, -8), 62, 0, 4)), ('headside', ((0, 100, 0), 80, 90, 4)), ('head34', ((-3, 98, -4), 80, -38, 10)),
                  ('scythe', ((-36, 112, -7), 90, -20, 6)), ('crow', ((-18, 93, 0), 50, -40, 10)), ('hands', ((0, 56, -4), 120, 0, 4)),
                  ('feet', ((0, 8, -4), 90, -25, 12)), ('grip', (tuple(FIST[[0, 1, 2]]), 34, -35, 12))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): biped, L = +x; upper-body points are in the lean frame -> world
def tw(p): return (p[0], p[1], p[2] - LEAN * max(p[1] - 50, 0))
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('hips', 'root', (0, 44, .5), tw((0, 60, .5))), ('spine', 'hips', tw((0, 60, .5)), tw((0, 74, .3))),
       ('chest', 'spine', tw((0, 74, .3)), tw((0, 86, 0))), ('head', 'chest', tw((0, 87, -.5)), tw((0, 106, -2)))]
sol_ = kind > 0
OVR = [((pid == PS) & (Y > 40) & (Y < 70) & (AX < 18), 'hips')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    sh, el, wr = ARM[sx]; hip, knee, ank, fz = LEGS[sx]
    tip = np.array(wr) + ((0, -6, -10) if sx > 0 else (np.array(tobody(FIST)) - np.array(wr)) * 1.6)
    RIG += [('shoulder' + sd, 'chest', tw((5 * sx, 83, .5)), tw(sh)), ('upperarm' + sd, 'shoulder' + sd, tw(sh), tw(el)),
            ('forearm' + sd, 'upperarm' + sd, tw(el), tw(wr)), ('hand' + sd, 'forearm' + sd, tw(wr), tw(tip))]
    LG = [('thigh' + sd, 'hips', hip, knee), ('shin' + sd, 'thigh' + sd, knee, ank), ('foot' + sd, 'shin' + sd, ank, (ank[0], 1.0, fz - 8))]
    RIG += LG; OVR += brick_rig.limb(X, Y, Z, sol_ & (pid > 0) & (pid < PC) & (X * sx > 0) & (Y < 50), LG)
stick = (AX < 3.2) & (np.abs(Z - .5) < 3.2)
strips = sol_ & (Y < 60) & (pid >= PC) & (pid <= PB) & ~stick
for sx, sd in ((1, 'L'), (-1, 'R')):
    for sz, fb in ((-1, 'F'), (1, 'B')):
        pts = [(6 * sx, 60, .5 + 4.5 * sz), (7 * sx, 40, .5 + 5.5 * sz), (8 * sx, 20, .5 + 6.5 * sz)]
        ch_ = [('strip%s%s%d' % (fb, sd, i + 1), 'hips' if i == 0 else 'strip%s%s%d' % (fb, sd, i), pts[i], pts[i + 1]) for i in range(2)]
        RIG += ch_; OVR += brick_rig.limb(X, Y, Z, strips & (X * sx >= 0) & ((Z - .5) * sz >= 0), ch_)
OVR += [((((pid >= HID) & (pid < PS)) | ((kind >= 2) & (Y > 86))) & sol_, 'head'), ((pid >= pc_) & sol_, 'shoulderR'), ((TAG > 0) & sol_, 'handR')]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (15, 0, 0), 'upperarmL': (-30, 0, 0), 'thighR': (25, 0, 0), 'stripFL2': (30, 0, 0), 'shoulderR': (0, 0, 12)},
                 render='render' in argv)
print('BL_OK')
