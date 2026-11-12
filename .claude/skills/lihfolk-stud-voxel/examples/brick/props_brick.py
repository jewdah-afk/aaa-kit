# Nature + town props (static, brick pipeline, no rig), one model per run:
#   blender -b --factory-startup --python props_brick.py -- render <Prop>     Props: Oak Pine Bush Rocks Well Cart Lamp Fence
# bld.Grid R=3 fine bricks. Foliage = several lumpy leaf clumps (blob), shaded light top -> dark underside by job,
# the top clump just takes the lit tone (no separate tufts stuck on top: user called them weird); trunks taper with root flare and bark rows. No smooth spheres, no lone glow cubes.
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/lihfolk-stud-voxel/scripts')) if os.path.exists(os.path.join(p, 'bld.py'))))
from bld import Grid, hx

BARK, BARKD = hx('7a4a28'), hx('543119')
LEAF = [hx('2f7a2c'), hx('3f9a35'), hx('5cbf45'), hx('8ee05a')]       # dark underside / main / lit / top tufts
PINE = [hx('1f5a3a'), hx('2b7448'), hx('3d9157')]
STONE, STONED, STONEL = hx('7a7f8a'), hx('4f535c'), hx('a3a9b3')
WOOD, WOODD, IRON, GOLD = hx('a8703f'), hx('6e4426'), hx('3a3d45'), hx('f2b630')
MOSS = hx('6aa83a')
GLOW = {2: hx('ffcf6a')}


def leaf_col(cy, ry, pal=LEAF):
    def c(x, y, z):
        t = (y - cy) / ry                                    # -1 underside .. 1 top
        idx = np.clip(np.floor((t + 1) * 1.5 + .25 * np.sin(x * 1.3 + z * .9)), 0, len(pal) - 2).astype(int)
        return np.array(pal)[idx]
    return c


def trunk(g, x, z, y0, y1, r0, r1, lean=(0, 0)):
    """tapered trunk: radius r0 at the base -> r1 at the top, root flare at the bottom, bark rows."""
    def fn(X, Y, Z):
        t = np.clip((Y - y0) / (y1 - y0), 0, 1)
        cx = x + lean[0] * t * t; cz = z + lean[1] * t * t
        r = r0 + (r1 - r0) * t + 2.5 * np.exp(-(Y - y0) / 2.0)
        return (Y >= y0) & (Y < y1) & ((X - cx) ** 2 + (Z - cz) ** 2 < r * r)
    g.fshape(fn, lambda X, Y, Z: np.where(((Y.astype(int) % 4) == 0)[:, None], BARKD, BARK))


def branch(g, a, b, r):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    def fn(X, Y, Z):
        t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
        return (X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2 < r * r
    g.fshape(fn, BARK)


def grass_base(g, R, seed=1):
    """mossy ground disc with stepped edge + a few grass tufts so the prop sits on the ground."""
    g.fshape(lambda X, Y, Z: (Y < 2) & (X * X + Z * Z < (R - Y * 1.5) ** 2), lambda X, Y, Z: np.where((Y > 1)[:, None], MOSS, hx('4f8a2e')))
    rng = np.random.default_rng(seed)
    for _ in range(8):
        a = rng.uniform(0, 6.28); d = rng.uniform(R * .5, R * .9); x = int(np.cos(a) * d); z = int(np.sin(a) * d)
        g.fbox(x, x + 1, 2, 4, z, z + 1, LEAF[2]); g.fbox(x + 1, x + 2, 2, 3, z, z + 1, LEAF[1])


def oak(g):
    grass_base(g, 16)
    trunk(g, 0, 0, 2, 34, 4.5, 2.5, lean=(2, 0))
    branch(g, (1, 22, 0), (-10, 32, 2), 1.8); branch(g, (2, 26, 0), (11, 34, -3), 1.6); branch(g, (1, 28, 0), (2, 38, 8), 1.5)
    for (x, y, z, rx, ry, rz, s) in ((0, 42, 0, 15, 10, 14, 1), (-11, 35, 3, 9, 7, 9, 2), (12, 37, -3, 9, 7, 9, 3),
                                     (3, 38, 10, 9, 7, 8, 4), (-3, 37, -10, 9, 7, 8, 5), (2, 50, -1, 9, 6, 9, 6)):
        g.blob(x, y, z, rx, ry, rz, leaf_col(y, ry), seed=s)


def pine(g):
    grass_base(g, 13, seed=3)
    trunk(g, 0, 0, 2, 60, 3.5, 1.2)
    for i, (y, r) in enumerate(((14, 15), (24, 13), (33, 11), (41, 9), (48, 7), (54, 5), (59, 3))):
        h = 9
        def fn(X, Y, Z, y=y, r=r, h=h):                                    # tier = cone with drooping, notched rim
            t = (Y - y) / h
            rr = r * (1 - t) + .8 * np.sin(np.arctan2(Z, X) * 7)
            return (t >= 0) & (t < 1) & (X * X + Z * Z < rr * rr)
        g.fshape(fn, lambda X, Y, Z, y=y: np.array(PINE)[np.clip(((Y - y) / 3).astype(int), 0, 2)])
    g.fbox(0, 1, 68, 70, 0, 1, PINE[2])


def bush(g):
    grass_base(g, 12, seed=5)
    for (x, y, z, rx, ry, rz, s) in ((0, 7, 0, 10, 6, 8, 1), (-6, 6, 4, 6, 5, 6, 2), (6, 6, -3, 6, 5, 6, 3), (1, 11, 1, 6, 4, 5, 4)):
        g.blob(x, y, z, rx, ry, rz, leaf_col(y, ry), seed=s)
    rng = np.random.default_rng(7)
    for _ in range(14):                                                    # flowers: petal cross + yellow centre
        a = rng.uniform(0, 6.28); x = int(np.cos(a) * 9); z = int(np.sin(a) * 7); y = int(5 + rng.uniform(0, 8))
        pc = [hx('ff6fa8'), hx('f4efe2'), hx('b57cff')][rng.integers(3)]
        g.fbox(x - 1, x + 2, y, y + 1, z, z + 1, pc); g.fbox(x, x + 1, y, y + 1, z - 1, z + 2, pc); g.fbox(x, x + 1, y + 1, y + 2, z, z + 1, hx('ffd34a'))


def rocks(g):
    grass_base(g, 15, seed=9)
    for (x, y, z, rx, ry, rz, s) in ((0, 6, 0, 10, 8, 8, 1), (-9, 4, 5, 6, 5, 6, 2), (8, 3, 6, 5, 4, 5, 3), (5, 11, -2, 5, 4, 5, 4)):
        g.blob(x, y, z, rx, ry, rz, (lambda cy, ry: lambda X, Y, Z: np.where(((Y - cy) / ry > .55)[:, None], MOSS,
               np.where(((X + Z).astype(int) % 7 == 0)[:, None], STONED, np.where(((Y - cy) / ry > 0)[:, None], STONEL, STONE))))(y, ry),
               lumpy=.28, seed=s)
    for (x, z) in ((-3, -7), (11, -5)): g.blob(x, 2, z, 2, 2, 2, STONE, seed=x)


def well(g):
    grass_base(g, 15, seed=11)
    def ring(X, Y, Z): d = np.sqrt(X * X + Z * Z); return (Y >= 2) & (Y < 12) & (d < 10) & (d >= 6.5)
    g.fshape(ring, lambda X, Y, Z: np.where((((np.arctan2(Z, X) * 4).astype(int) + (Y // 3).astype(int)) % 2 == 0)[:, None], STONE, STONEL))
    g.fshape(lambda X, Y, Z: (Y >= 12) & (Y < 13) & (X * X + Z * Z < 11 ** 2) & (X * X + Z * Z >= 6 ** 2), STONED)
    g.fshape(lambda X, Y, Z: (Y >= 2) & (Y < 8) & (X * X + Z * Z < 6.5 ** 2), hx('2f6fb0'))    # water
    for x in (-9, 8):
        g.fbox(x, x + 2, 12, 32, -1, 1, WOODD)
    g.fbox(-9, 10, 26, 28, -1, 1, WOOD)                                    # crank beam
    g.fbox(-1, 1, 18, 26, 0, 1, IRON); g.fbox(-2, 2, 15, 19, -2, 2, WOOD); g.fbox(-2, 2, 15, 16, -2, 2, IRON)   # rope + bucket
    g.fbox(10, 11, 24, 27, -1, 1, IRON); g.fbox(10, 13, 23, 24, 0, 1, IRON)
    for i in range(13):                                                    # little shingle roof
        h = 13 - i
        g.fbox(-12, 13, 32 + i // 2, 33 + i // 2, -h, -h + 2, hx('d2463c') * (.8 if i % 3 == 0 else 1))
        g.fbox(-12, 13, 32 + i // 2, 33 + i // 2, h - 2, h, hx('d2463c') * (.8 if i % 3 == 0 else 1))


def cart(g):
    for s in (-1, 1):                                                      # 2 spoked wheels
        x = s * 10
        def wheel(X, Y, Z, x=x):
            d = np.sqrt((Y - 8) ** 2 + (Z) ** 2); a = np.arctan2(Y - 8, Z)
            spoke = (np.abs(np.sin(a * 3)) < .18) & (d < 7)
            return (np.abs(X - x) < 1.5) & (((d < 8) & (d >= 6.2)) | spoke | (d < 1.6))
        g.fshape(wheel, lambda X, Y, Z: np.where((np.sqrt((Y - 8) ** 2 + Z ** 2) >= 6.2)[:, None], WOODD, WOOD))
        g.fbox(x - 2 if s < 0 else x + 1, x - 1 if s < 0 else x + 2, 6, 10, -2, 2, IRON)
    g.fbox(-9, 9, 8, 10, -1, 1, IRON)                                      # axle
    g.fbox(-9, 9, 10, 12, -12, 12, WOODD)                                  # bed
    for (x0, x1, z0, z1) in ((-9, 9, -12, -11), (-9, 9, 11, 12), (-9, -8, -12, 12), (8, 9, -12, 12)):
        for y in range(12, 18): g.fbox(x0, x1, y, y + 1, z0, z1, WOOD if y % 2 else WOODD)
    g.fbox(-3, -2, 9, 11, -28, -12, WOODD); g.fbox(2, 3, 9, 11, -28, -12, WOODD)   # shafts
    for (x, y, z, c) in ((-4, 18, -4, hx('d2463c')), (3, 18, 3, hx('5cbf45')), (0, 19, 6, hx('ff9a1f')), (-5, 18, 6, hx('d2463c'))):
        g.blob(x, y, z, 3, 2.5, 3, c, lumpy=.1, seed=x)                    # produce
    g.fbox(2, 8, 12, 20, -9, -3, WOOD); g.fbox(2, 8, 19, 20, -9, -3, WOODD)   # crate


def lamp(g):
    g.fbox(-4, 4, 0, 2, -4, 4, STONED); g.fbox(-3, 3, 2, 4, -3, 3, STONE)
    g.fbox(-1, 1, 4, 40, -1, 1, IRON); g.fbox(-2, 2, 14, 15, -2, 2, IRON); g.fbox(-2, 2, 30, 31, -2, 2, IRON)
    g.fbox(1, 9, 40, 41, -1, 1, IRON); g.fbox(8, 9, 36, 40, 0, 1, IRON)   # arm + hook
    g.fbox(5, 12, 35, 36, -3, 4, IRON); g.fbox(5, 12, 28, 29, -3, 4, IRON); g.fbox(6, 11, 36, 37, -2, 3, IRON)
    for (a, b) in ((5, -3), (11, -3), (5, 3), (11, 3)): g.fbox(a, a + 1, 29, 35, b, b + 1, IRON)
    g.fbox(6, 11, 29, 35, -2, 3, '000000', k=2)


def fence(g):
    pass
    for x in range(-24, 25, 8):
        g.fbox(x - 1, x + 1, 0, 14, -1, 1, WOODD); g.fbox(x - 1, x, 14, 15, -1, 1, WOODD)   # posts with notched tops
    for y in (4, 10):
        g.fbox(-24, 25, y, y + 2, -2, -1, WOOD)
    for x in range(-23, 24, 3): g.fbox(x, x + 2, 1, 13, -3, -2, WOOD if x % 2 else hx('b97c46'))   # pickets
    for x in range(-23, 24, 3): g.fbox(x, x + 2, 13, 14, -3, -2, WOODD)


PROPS = {'Oak': (oak, (16, 26, 16)), 'Pine': (pine, (12, 26, 12)), 'Bush': (bush, (10, 8, 10)), 'Rocks': (rocks, (12, 8, 12)),
         'Well': (well, (12, 18, 12)), 'Cart': (cart, (10, 10, 20)), 'Lamp': (lamp, (10, 16, 6)), 'Fence': (fence, (20, 7, 4))}
def gym(g):
    """strength-sim weight station: rubber mat, flat bench, rack uprights with J-hooks, loaded barbell, dumbbell rack."""
    MAT, MATL = hx('2b2e35'), hx('3a3e47')
    RED, REDD, BLK, CHROME, CHROMED, PAD, PADD = hx('e0393a'), hx('a82a2b'), hx('25272c'), hx('cfd5dd'), hx('8d949e'), hx('2f6fd0'), hx('2353a0')
    g.fbox(-30, 30, 0, 1, -18, 18, MAT)                                   # rubber floor mat with tile seams
    for x in range(-30, 30, 10): g.fbox(x, x + 1, 1, 2, -18, 18, MATL)
    g.fbox(-4, 4, 1, 9, -2, 14, BLK); g.fbox(-3, 3, 1, 2, -3, 15, CHROMED)   # bench frame + feet
    g.fbox(-5, 5, 9, 12, -4, 16, PAD); g.fbox(-5, 5, 9, 10, -4, 16, PADD)    # padded top, dark lower edge
    for z in (2, 9): g.fbox(-6, 6, 10, 11, z, z + 1, PADD)                     # stitching lines
    for x in (-9, 8):                                                     # rack uprights + base + J-hooks
        g.fbox(x - 1, x + 2, 1, 3, -6, 2, CHROMED)
        g.fbox(x, x + 1, 3, 30, -3, -1, BLK)
        g.fbox(x - 1, x + 2, 22, 23, -5, -1, CHROME); g.fbox(x - 1, x + 2, 23, 25, -5, -4, CHROME)
    g.fbox(-26, 26, 23, 24, -4, -3, CHROME)                               # bar on the hooks
    for s in (-1, 1):                                                     # plates: big red, small black, collar
        for (x0, w, r, c, cd) in ((16, 3, 8, RED, REDD), (19, 2, 6, BLK, BLK)):
            xa = s * x0 if s > 0 else s * x0 - w
            def plate(X, Y, Z, xa=xa, w=w, r=r): return (X >= xa) & (X < xa + w) & ((Y - 23.5) ** 2 + (Z + 3.5) ** 2 < r * r)
            g.fshape(plate, lambda X, Y, Z, r=r, c=c, cd=cd: np.where((((Y - 23.5) ** 2 + (Z + 3.5) ** 2) > (r - 1.5) ** 2)[:, None], cd * .8, c))
        xc = s * 21 if s > 0 else s * 21 - 1
        g.fshape(lambda X, Y, Z, xc=xc: (X >= xc) & (X < xc + 1) & ((Y - 23.5) ** 2 + (Z + 3.5) ** 2 < 2.5 ** 2), CHROME)
    g.fbox(-28, -14, 1, 6, 8, 16, BLK); g.fbox(-28, -14, 6, 7, 8, 16, CHROMED)   # dumbbell rack
    for i, (x, r, c) in enumerate(((-25, 2.2, RED), (-18, 2.6, PAD))):     # 2 dumbbells on the rack
        for zz in (9, 15):
            g.fshape(lambda X, Y, Z, x=x, r=r, zz=zz: (np.abs(X - x) < 3) & ((Y - 9) ** 2 + (Z - zz) ** 2 < r * r), c)
        g.fbox(x - 1, x + 1, 8, 10, 10, 14, CHROME)


PROPS['Gym'] = (gym, (22, 12, 14))
def crimson_blade(g):
    """sleek long sword after a user reference (R=12, ~29 studs): long thin blade with a white core and red edges,
    asymmetric shoulders (stepped notch on one side, a hooked spur on the other), charcoal swept guard (one arm
    flat with a down-hook, the other angled down with a curl), long thin charcoal grip, pommel cap with an inset red
    stone. Blade points up; grip centre x 0 z 0, y 6..56."""
    WHITE, WHITED = hx('f4f4f6'), hx('c9ccd4')
    RED, REDD = hx('b8141c'), hx('7c0c12')
    CH, CHL, CHD = hx('3a3a3e'), hx('55555b'), hx('242427')
    for y in range(0, 7):                                                  # pommel cap + inset red stone
        r = (2, 3, 3, 3, 3, 3, 2)[y]
        g.fbox(-r, r, y, y + 1, -2, 2, CH if y not in (0, 6) else CHD)
    g.fbox(-1, 1, 2, 5, -3, -2, RED); g.fbox(-1, 1, 2, 5, 2, 3, RED)
    g.fbox(-1, 0, 4, 5, -3, -2, hx('ff5a5a'))                              # tiny highlight on the stone
    for y in range(7, 56):                                                 # long thin grip, faint wrap ridges
        g.fbox(-1, 2, y, y + 1, -1, 2, CHL if y % 4 == 0 else CH)
    g.fbox(-2, 3, 55, 58, -2, 3, CHD)                                      # collar
    for i in range(16):                                                    # guard arm A (+x): flat, then hooks down
        x = 3 + i; y = 58 if i < 11 else 58 - (i - 10)
        g.fbox(x, x + 1, y, y + 4, -2, 3, CH); g.fbox(x, x + 1, y + 3, y + 4, -1, 2, CHL)
    g.fbox(17, 19, 50, 54, -2, 3, CH)
    for i in range(18):                                                    # guard arm B (-x): angled down, curls up
        x = -3 - i; y = 59 - int(i * .55) if i < 14 else 59 - 7 + (i - 13)
        g.fbox(x - 1, x, y, y + 4, -2, 3, CH); g.fbox(x - 1, x, y + 3, y + 4, -1, 2, CHL)
    g.fbox(-6, 6, 58, 64, -3, 4, CH); g.fbox(-6, 6, 63, 64, -2, 3, CHL)   # guard block
    for k in range(5): g.fbox(-3 + k, 4 - k, 64 + k, 65 + k, -2, 3, CHD)  # stepped block top into the blade
    top = 196
    for y in range(64, top):                                               # blade: long gentle taper, sharp point last 26
        t = (y - 64) / (top - 64)
        w = 6 - 1.2 * t if t < .8 else (6 - 1.2 * .8) * (1 - t) / .2
        wl, wr = w, w
        if y < 80: wr = w + 2 + (80 - y) * .12                             # hooked spur side (+x) swells into the guard
        if 70 <= y < 78: wl = w - 2                                        # stepped notch on the -x side
        L, Rr = -int(round(wl)), int(round(wr))
        if Rr - L <= 0: break
        g.fbox(L, Rr, y, y + 1, -1, 2, RED)                                # red body = edges
        if Rr - L > 4:
            g.fbox(L + 2, Rr - 2, y, y + 1, -1, 2, WHITE)                  # white core
            g.fbox(L + 2, L + 3, y, y + 1, -1, 2, WHITED)                  # soft bevel line between core and edge
        g.fbox(L, L + 1, y, y + 1, 0, 1, REDD); g.fbox(Rr - 1, Rr, y, y + 1, 0, 1, REDD)   # dark edge line
    g.fbox(-1, 1, top - 2, top, 0, 1, RED)
    for y in range(64, 82):                                                # white spine hook over the spur
        x = 7 + int((82 - y) * .25)
        g.fbox(x, x + 1, y, y + 1, -1, 2, WHITE)
    g.fbox(-5, -3, 66, 72, -1, 2, WHITE)                                   # white lip on the notch side


PROPS['CrimsonBlade'] = (crimson_blade, (4, 17, 1), 12)
def void_crystal_blade(g):
    """crystal sword after a user reference (R=16, ~22 studs): broad faceted lilac-white blade with serrated edges,
    a violet crystal lens set in a dark-blue channel in the upper half, an OPEN slot through the lower half (dark rim),
    pink facet accents where the blade pinches in, ornate dark-violet guard (medallion with a gem socket, horns curling
    up into the slot, swept wing spikes), long dark grip with rings, faceted pommel. Grip x 0 z 0, y 8..66."""
    WH, LIL, LILD = hx('eeeaff'), hx('c9c0f2'), hx('9a8fd6')
    PINK, PINKD = hx('e7a6e6'), hx('b46ac0')
    VIO, VIOL, VIOD = hx('6a3fd0'), hx('9a6cff'), hx('2c2a8a')
    GD, GDL, GDD = hx('4a2470'), hx('7a3f9e'), hx('22123a')
    GEM = hx('ff7ad9')
    Y0, YM, Y1 = 92, 168, 270                                             # blade base / pinch / tip
    YS, YT = YM - 14, Y1 - 50                                            # shoulder top / tip start
    def half(Y):                                                           # angular segmented silhouette
        lo = 12 + 3 * np.clip((Y - Y0) / (YS - Y0), 0, 1)                 # lower section flares out to a shoulder
        dn = 15 - 6 * np.clip((Y - YS) / 14, 0, 1)                         # sharp diagonal cut in to the pinch
        up = 9 + 4.5 * np.clip((Y - YM) / 10, 0, 1)                        # diagonal back out
        tip = 13.5 * np.clip((Y1 - Y) / (Y1 - YT), 0, 1)                   # straight taper to the point
        return np.where(Y < YS, lo, np.where(Y < YM, dn, np.where(Y < YT, np.minimum(up, 13.5 - .03 * (Y - YM)), tip)))
    def lens(Y, ya, yb, wmax):
        u = np.clip((Y - ya) / (yb - ya), 0, 1)
        return wmax * np.sin(np.pi * u) ** .8
    def blade(X, Y, Z):
        w = half(Y); ax = np.abs(X)
        th = 4.0 * (1 - .65 * ax / np.maximum(w, .1))                       # diamond-ish section, thin sharp edges
        saw = (ax > w - 1.2) & ((np.floor(Y) % 3) == 0) & ((Y > YT) | (Y < YS))   # fine teeth on tip + lower edges
        slot = (ax < lens(Y, Y0 + 6, YM - 4, 6.0)) & (Y > Y0 + 6) & (Y < YM - 4)
        return (Y >= Y0) & (Y < Y1) & (ax < w) & ~saw & (np.abs(Z) < th + .5) & ~slot
    def blade_col(X, Y, Z):
        w = half(Y); ax = np.abs(X)
        fac = ((np.floor((Y + ax * 1.4) / 9)) % 2 == 0)                    # chevron facets angled up toward the spine
        c = np.where(fac[:, None], WH, LIL)
        c = np.where(((X > 0) & ~fac)[:, None], LILD * 1.1, c)               # shaded right half darker
        c = np.where((ax > w - 2)[:, None], LILD, c)                       # edge bevel
        pink = (np.abs(Y - (YS + 7)) < 16) & (ax > 3) & (ax < w - 1.5) & (((Y + ax * 1.4) % 9) < 4)
        c = np.where(pink[:, None], np.where((X < 0)[:, None], PINK, PINKD), c)
        slr = lens(Y, Y0 + 6, YM - 4, 6.0)
        c = np.where(((ax < slr + 2.2) & (Y > Y0 + 4) & (Y < YM - 2))[:, None], VIOD, c)
        chan = lens(Y, YM + 4, Y1 - 24, 7.0)
        c = np.where(((ax < chan + 2) & (Y > YM + 2) & (Y < Y1 - 22))[:, None], VIOD, c)
        core = (ax < chan) & (Y > YM + 4) & (Y < Y1 - 24)
        cf = ((np.floor((Y - ax * 1.6) / 7)) % 2 == 0)                      # faceted crystal: alternating chevrons
        c = np.where(core[:, None], np.where(cf[:, None], VIOL, VIO), c)
        c = np.where((core & (ax < chan * .3))[:, None], hx('c9a8ff'), c)
        return c
    g.fshape(blade, blade_col)
    g.fshape(lambda X, Y, Z: (Y >= YS - 10) & (Y < YS + 1) & (np.abs(X) >= 12) & (np.abs(X) < 12 + (Y - (YS - 10)) * .55)
             & (np.abs(Z) < 2.2), lambda X, Y, Z: np.where((X < 0)[:, None], WH, LILD))                 # shoulder barbs, pointing up
    g.fshape(lambda X, Y, Z: (Y >= YM + 1) & (Y < YM + 9) & (np.abs(X) >= 9) & (np.abs(X) < 9 + (Y - YM) * .6) & (np.abs(Z) < 2),
             lambda X, Y, Z: np.where((X < 0)[:, None], PINK, PINKD))                                    # pink spurs at the pinch
    # crystal lens stands slightly proud of the channel (front + back)
    g.fshape(lambda X, Y, Z: (np.abs(X) < lens(Y, YM + 10, Y1 - 30, 5.5)) & (Y > YM + 10) & (Y < Y1 - 30) & (np.abs(Z) < 4.6),
             lambda X, Y, Z: np.where((X < 0)[:, None], VIOL, VIO))
    # ---- guard
    def medal(X, Y, Z): return (X * X + (Y - 82) ** 2 < 12 ** 2) & (np.abs(Z) < 5)
    g.fshape(medal, lambda X, Y, Z: np.where((np.sqrt(X * X + (Y - 82) ** 2) > 10)[:, None], GDL, GD))
    g.fshape(lambda X, Y, Z: (X * X + (Y - 82) ** 2 < 5 ** 2) & (np.abs(Z) < 6), GDD)                 # gem socket
    g.fshape(lambda X, Y, Z: (X * X + (Y - 82) ** 2 < 3.2 ** 2) & (np.abs(Z) < 6.6), GEM)             # gem in it
    for s_ in (-1, 1):
        def horn(X, Y, Z, s_=s_):                                          # horns curl up into the slot base
            a = (Y - 86) / 26
            cx = s_ * (9 + 3 * np.sin(a * 3.0))
            return (Y >= 86) & (Y < 112) & (np.abs(X - cx) < 2.6 - a * 1.6) & (np.abs(Z) < 3)
        g.fshape(horn, GDL)
        def wing(X, Y, Z, s_=s_):                                          # swept wing spike, down then out
            u = (s_ * X - 10) / 22
            yc = 80 - 10 * u + 6 * u * u
            return (u >= 0) & (u <= 1) & (np.abs(Y - yc) < 4.5 * (1 - u) + .8) & (np.abs(Z) < 3.5 - u * 2)
        g.fshape(wing, lambda X, Y, Z: np.where((Y > 80 - 10 * ((np.abs(X) - 10) / 22))[:, None], GDL, GD))
        def spur(X, Y, Z, s_=s_):                                          # small lower spurs on the collar
            return (np.abs(s_ * X - 7) < 2) & (Y > 64) & (Y < 72) & (np.abs(Z) < 2.5) & ((s_ * X - 5) > (Y - 64) * .3)
        g.fshape(spur, GDL)
    g.fshape(lambda X, Y, Z: (np.abs(X) < 6) & (Y >= 64) & (Y < 72) & (np.abs(Z) < 4), GD)            # collar
    g.fshape(lambda X, Y, Z: (np.abs(X) < 7) & (Y >= 88) & (Y < Y0 + 1) & (np.abs(Z) < 4), GD)        # blade seat
    # ---- grip + pommel
    g.fshape(lambda X, Y, Z: (Y >= 12) & (Y < 64) & (X * X + Z * Z < 3.6 ** 2),
             lambda X, Y, Z: np.where(((np.floor(Y) % 6) == 0)[:, None], GDD * 1.6, GDD))
    for y0 in (12, 61):
        g.fshape(lambda X, Y, Z, y0=y0: (Y >= y0) & (Y < y0 + 3) & (X * X + Z * Z < 4.8 ** 2), GD)
    g.fshape(lambda X, Y, Z: (Y >= 2) & (Y < 12) & (np.abs(X) + np.abs(Z) * .7 < 6 - np.abs(Y - 7) * .6), lambda X, Y, Z: np.where((X < 0)[:, None], GDL, GD))


PROPS['VoidCrystal'] = (void_crystal_blade, (4, 18, 1), 16)
def poly(g, pts, z, c, k=1):
    """side-profile polygon (x, y fine coords) extruded through |Z| < z: the way to draw gun / bow silhouettes."""
    P = np.array(pts, float)
    def fn(X, Y, Z):
        inside = np.zeros(np.shape(X), bool)
        j = len(P) - 1
        for i in range(len(P)):
            xi, yi = P[i]; xj, yj = P[j]
            cond = ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi + 1e-9) + xi)
            inside ^= cond; j = i
        return inside & (np.abs(Z) < z)
    g.fshape(fn, c, k)


def stroke(g, pts, r, z, c, k=1):
    """thick polyline (bow limbs, strings, thorns) through |Z| < z."""
    for (ax_, ay), (bx, by) in zip(pts, pts[1:]):
        def fn(X, Y, Z, ax_=ax_, ay=ay, bx=bx, by=by):
            dx, dy = bx - ax_, by - ay; L2 = dx * dx + dy * dy + 1e-9
            u = np.clip(((X - ax_) * dx + (Y - ay) * dy) / L2, 0, 1)
            return ((X - ax_ - dx * u) ** 2 + (Y - ay - dy * u) ** 2 < r * r) & (np.abs(Z) < z)
        g.fshape(fn, c, k)


BLK, BLK2, STEEL2, STEEL3 = hx('15171c'), hx('262a33'), hx('9aa6b8'), hx('d9e2ee')
GOLD2, ORNG, NEON = hx('c8922a'), hx('d87a2a'), hx('6fb8ff')
HOLE = '000000'


def thorn_bow(g):
    """dark thorn bow (R=8): limbs curling back with silver inlay, thorn spikes off the backs, gold eyes, taut
    string, an arrow nocked across the grip (silver-veined shaft, star head, gold-tipped fletching). Bow centre y 0."""
    OY = 92                                                                # lift so the lower limb sits in the grid
    def L(pts): return [(x, y + OY) for x, y in pts]
    for s_ in (1, -1):
        Lp = [(0, 6 * s_), (-6, 24 * s_), (-10, 42 * s_), (-8, 58 * s_), (-2, 72 * s_), (6, 82 * s_)]
        stroke(g, L(Lp), 4.2, 3, BLK)
        stroke(g, L(Lp[:-1]), 1.6, 3.6, STEEL2)
        for (bx, by, dx, dy) in ((-6, 24, -14, 4), (-10, 42, -16, 6), (-9, 54, -12, 10), (-4, 66, -8, 12), (-8, 34, -6, 14)):
            stroke(g, L([(bx, by * s_), (bx + dx, (by + dy) * s_)]), 1.3, 2, BLK)
            stroke(g, L([(bx + dx, (by + dy) * s_), (bx + dx - 2, (by + dy + 3) * s_)]), .9, 1.6, BLK)
        for (ex, ey) in ((-7, 22), (-9, 40)):
            g.fshape(lambda X, Y, Z, ex=ex, ey=ey * s_ + OY: ((X - ex) ** 2 + (Y - ey) ** 2 < 2.2 ** 2) & (np.abs(Z) < 4), GOLD2)
        stroke(g, L([(6, 82 * s_), (8, 84 * s_)]), 1.5, 2.5, STEEL3)
    poly(g, L([(-4, -9), (5, -9), (5, 9), (-4, 9)]), 4, STEEL2)
    g.fshape(lambda X, Y, Z: (np.abs(X) < 1.5) & (np.abs(Y - OY) < 1.5) & (np.abs(Z) < 4.6), GOLD2)
    stroke(g, L([(7, 83), (36, 0), (7, -83)]), .7, .8, BLK2)
    stroke(g, L([(-58, 0), (36, 0)]), 1.4, 1.4, BLK)
    for x in range(-50, 30, 9): stroke(g, L([(x, .6), (x + 5, .6)]), .6, 1.6, STEEL2)
    for (dx, dy) in ((0, 4), (0, -4), (-4, 0), (4, 0)):
        stroke(g, L([(-60, 0), (-60 + dx, dy)]), 1.5, 1.6, STEEL3)
    g.fshape(lambda X, Y, Z: ((X + 60) ** 2 + (Y - OY) ** 2 < 2.2 ** 2) & (np.abs(Z) < 2), GOLD2)
    for sy in (1, -1):
        poly(g, L([(26, 1 * sy), (36, 1 * sy), (40, 6 * sy), (31, 4 * sy)]), 1.2, BLK)
        poly(g, L([(36, 4 * sy), (41, 5 * sy), (39, 7 * sy)]), 1.4, GOLD2)


def sniper(g):
    """silver + gold sniper rifle, muzzle up: barrel, black muzzle brake with a glow slit, gold-trimmed receiver,
    scope on rings, bolt knob, skeleton stock with a cut-out and gold butt plate."""
    O = 60
    def P(pts): return [(x, y + O) for x, y in pts]
    poly(g, P([(-2, 70), (2, 70), (2, 190), (-2, 190)]), 2.2, STEEL3)
    poly(g, P([(-3, 186), (3, 186), (3, 204), (-3, 204)]), 3, BLK)
    poly(g, P([(-4, 192), (4, 192), (4, 196), (-4, 196)]), 3.4, BLK)
    poly(g, P([(-2, 199), (2, 199), (2, 201), (-2, 201)]), 3.4, NEON, 2)
    poly(g, P([(-6, 20), (4, 20), (4, 78), (-1, 92), (-6, 92)]), 3.4, STEEL2)
    poly(g, P([(-9, 82), (-1, 82), (-1, 96), (-9, 96)]), 3, GOLD2)
    poly(g, P([(-6, 86), (-4, 86), (-4, 92), (-6, 92)]), 3.6, BLK); poly(g, P([(-8, 88), (-2, 88), (-2, 90), (-8, 90)]), 3.6, BLK)
    for y0 in (40, 54): poly(g, P([(4, y0), (14, y0), (14, y0 + 3), (4, y0 + 3)]), 3.2, GOLD2)
    poly(g, P([(9, 28), (15, 28), (15, 76), (9, 76)]), 2.8, STEEL2)
    poly(g, P([(8, 70), (16, 70), (16, 82), (8, 82)]), 3.2, STEEL3); poly(g, P([(8, 22), (16, 22), (16, 32), (8, 32)]), 3.2, STEEL3)
    for y in range(34, 70, 4): poly(g, P([(9, y), (15, y), (15, y + 1), (9, y + 1)]), 3, GOLD2)
    poly(g, P([(-12, 52), (-6, 52), (-6, 60), (-12, 60)]), 3, GOLD2)
    poly(g, P([(-6, 20), (-10, 14), (-10, -40), (2, -50), (4, -50), (4, 20)]), 3.2, BLK)
    poly(g, P([(-6, -4), (0, -4), (0, -32), (-6, -26)]), 4, HOLE, 0)
    poly(g, P([(-10, -40), (4, -50), (4, -58), (-10, -48)]), 3.4, GOLD2)
    poly(g, P([(-6, 12), (-2, 12), (-2, 4), (-8, -2)]), 3.6, STEEL2)


def scifi_pistol(g):
    """white + silver sci-fi pistol, muzzle up: stepped slide with a dark slot of glowing pips set INTO the slot,
    angled grip with lines, open trigger loop."""
    O = 14
    def P(pts): return [(x, y + O) for x, y in pts]
    poly(g, P([(-6, 20), (8, 20), (8, 82), (4, 88), (-6, 88)]), 3, STEEL3)
    poly(g, P([(6, 30), (10, 30), (10, 78), (6, 84)]), 3.2, STEEL2)
    poly(g, P([(-3, 38), (2, 38), (2, 80), (-3, 80)]), 3.4, BLK2)
    for y in range(42, 78, 7): poly(g, P([(-2, y), (1, y), (1, y + 3), (-2, y + 3)]), 3.6, NEON, 2)
    poly(g, P([(-6, 20), (2, 20), (-20, -6), (-34, -10), (-34, -2), (-14, 26)]), 3.2, BLK2)
    poly(g, P([(-30, -9), (-20, -6), (-20, -2), (-32, -4)]), 3.4, STEEL2)
    for t in range(0, 18, 3): stroke(g, P([(-4 - t, 18 - t * 1.2), (-6 - t, 15 - t * 1.2)]), .5, 3.4, STEEL2)
    stroke(g, P([(4, 20), (4, 6), (-4, 2), (-8, 8)]), 1.2, 2.2, STEEL2)
    poly(g, P([(-6, 84), (-10, 84), (-10, 74), (-6, 70)]), 3, STEEL2)


def assault_rifle(g):
    """dark assault rifle, muzzle up: body with rail teeth, orange stripes, blue checker power panel set into a
    frame, glowing side cell in a frame, mag, grip, stock with an open frame."""
    O = 30
    def P(pts): return [(x, y + O) for x, y in pts]
    poly(g, P([(-6, 30), (6, 30), (6, 150), (-6, 150)]), 3.6, BLK)
    poly(g, P([(-2, 150), (2, 150), (2, 186), (-2, 186)]), 2, BLK2)
    for y in range(40, 150, 4): poly(g, P([(6, y), (9, y), (9, y + 2), (6, y + 2)]), 3, BLK2)
    for (ya, yb) in ((128, 138), (116, 124), (40, 48), (50, 56), (4, 12)):
        poly(g, P([(-6, ya), (6, ya + 6), (6, yb + 6), (-6, yb)]), 3.8, ORNG)
    poly(g, P([(-4, 78), (4, 78), (4, 112), (-4, 112)]), 3.8, BLK2)
    g.fshape(lambda X, Y, Z: (np.abs(X) < 3) & (Y >= 80 + O) & (Y < 110 + O) & (np.abs(Z) < 4) & (((np.floor(X / 2) + np.floor(Y / 2)) % 2) == 0), NEON, 2)
    poly(g, P([(-24, 92), (-8, 92), (-8, 102), (-24, 102)]), 3.4, BLK2)
    poly(g, P([(-22, 94), (-10, 94), (-10, 100), (-22, 100)]), 3.8, NEON, 2)
    poly(g, P([(-6, 60), (-22, 50), (-22, 30), (-14, 26), (-6, 40)]), 3.2, BLK)
    poly(g, P([(-6, 38), (-16, 28), (-14, 14), (-6, 24)]), 3.4, BLK2)
    poly(g, P([(-6, 30), (6, 30), (6, -10), (-6, -10)]), 3, BLK)
    poly(g, P([(-14, -10), (6, -10), (6, -26), (-14, -26)]), 3.4, BLK2)
    poly(g, P([(-10, -14), (2, -14), (2, -22), (-10, -22)]), 4, HOLE, 0)


GUNGLOW = {2: hx('6fb8ff')}
PROPS['ThornBow'] = (thorn_bow, (17, 24, 2), 8)
PROPS['Sniper'] = (sniper, (5, 34, 2), 8, GUNGLOW)
PROPS['Pistol'] = (scifi_pistol, (10, 14, 2), 8, GUNGLOW)
PROPS['Rifle'] = (assault_rifle, (8, 28, 2), 8, GUNGLOW)
def traced(name):
    """weapon traced 1:1 from a user reference (refs/<name>.npz made by scripts/trace_ref.py from refs/ref_ranged.png)."""
    def fn(g):
        g.uvd = 16.0 * g.R / 6                                             # studs ~ the same world size as elsewhere
        g.trace(os.path.join(HERE, 'refs', name + '.npz'), depth=3, y0=1, stroke=1)
    return fn


for _n, _sz in (('ThornBow', (7, 9, 1)), ('Sniper', (3, 12, 1)), ('Pistol', (3, 6, 1)), ('Rifle', (3, 10, 1))):
    PROPS[_n] = (traced(_n), _sz, 24, {2: hx('7cc8ff')})
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
name = next((a for a in argv if a in PROPS), 'Oak')
fn, size, *rr = PROPS[name]
g = Grid(*size, R=rr[0] if rr else 3)
if len(rr) > 1: GLOW = rr[1]
fn(g); g.export(name, HERE, glow=GLOW)
