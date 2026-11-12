# Terrain pieces (static, brick pipeline, no rig), one per run:
#   blender -b --factory-startup --python terrain_brick.py -- render <Piece>     Pieces: Cliff Waterfall Wall WallCorner
# bld.Grid R=3 fine bricks. Cliffs = terraced rock face (strata bands by height, lumpy face, cracks), grass cap with a
# dripping edge, boulders at the foot. Waterfall = cliff with a notch, water sheet in vertical streaks (light/dark lanes),
# foam lip at the top, white splash + ripple rings in a stepped pool. Walls = stone running bond, crenels, moss, buttress.
# Pieces are modular: Cliff/Wall are 60 fine wide (50 studs) so they line up side by side.
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/lihfolk-stud-voxel/scripts')) if os.path.exists(os.path.join(p, 'bld.py'))))
from bld import Grid, hx

ROCK = [hx('5c5348'), hx('7a6e5f'), hx('948777'), hx('6b6154')]       # strata bands (by height job)
CRACK = hx('3d362f')
GRASS, GRASSD, GRASSL = hx('4f9a35'), hx('3a7a2a'), hx('6cc04a')
STONE, STONED, STONEL = hx('7a7f8a'), hx('4f535c'), hx('a3a9b3')
MOSS = hx('6aa83a')
WATER = [hx('2f7fd0'), hx('4aa0e8'), hx('7cc4f5')]
FOAM = hx('eef8ff')
GLOW = {}
W2 = 30                                                              # half width (fine) = 60 wide modules


def strata(y):
    return np.array(ROCK)[(y // 7).astype(int) % 4]


def cliff_mask(H, notch=None):
    def front(X, Y):                                                  # front face z (more negative = further out)
        terrace = -14 + 4 * np.floor(Y / 16)                          # steps back every 16 bricks going up
        bump = 1.6 * np.sin(X * .35 + np.floor(Y / 5)) + 1.2 * np.sin(Y * .45 + X * .12)
        return terrace + bump
    def fn(X, Y, Z):
        m = (Y < H) & (np.abs(X) < W2) & (Z > front(X, Y)) & (Z < 14)
        if notch: m &= ~((np.abs(X) < notch) & (Z < -4 + 0 * X))
        return m
    def col(X, Y, Z):
        c = strata(Y)
        crack = (np.abs(np.sin(X * .5 + Y * .08)) < .06) & (Z < front(X, Y) + 2)
        c = np.where(crack[:, None], CRACK, c)
        c = np.where(((Y % 7) == 0)[:, None], c * .82, c)             # dark line under each stratum
        return c
    return fn, col, front


def grass_cap(g, H, front, notch=None):
    def fn(X, Y, Z):
        f = front(X, np.full_like(X, H - 1))
        drip = (Y >= H - 3 - 3 * (np.sin(X * .9) > .4)) & (Y < H) & (Z > f - 1) & (Z < f + 2)   # grass drips over the edge
        top = (Y >= H) & (Y < H + 2) & (Z > f - 1) & (Z < 14)
        m = (np.abs(X) < W2) & (top | drip)
        if notch: m &= ~(np.abs(X) < notch)
        return m
    g.fshape(fn, lambda X, Y, Z: np.where((Y >= H + 1)[:, None], np.where((np.sin(X * 1.7 + Z * 1.3) > .6)[:, None], GRASSL, GRASS), GRASSD))
    for (x, z) in ((-22, 4), (-9, 8), (6, 2), (19, 9), (25, 0)):      # tufts on top (part of the grass, not floating)
        if notch and abs(x) < notch: continue
        g.fbox(x, x + 1, H + 2, H + 4, z, z + 1, GRASSL); g.fbox(x + 1, x + 2, H + 2, H + 3, z, z + 1, GRASS)


def foot_rocks(g, seed):
    rng = np.random.default_rng(seed)
    for _ in range(5):
        x = rng.uniform(-26, 26); r = rng.uniform(2.5, 5)
        g.blob(x, r * .6, -17 - rng.uniform(0, 4), r, r * .8, r, (lambda X, Y, Z: np.where((Y > 2.5)[:, None], ROCK[2], ROCK[1])), lumpy=.25, seed=int(x))


def cliff(g):
    H = 48
    fn, col, front = cliff_mask(H); g.fshape(fn, col)
    grass_cap(g, H, front); foot_rocks(g, 2)
    for (x, y) in ((-18, 20), (12, 34), (22, 12)):                    # small ledge plants
        g.blob(x, y + 1, front(np.array([x]), np.array([y]))[0] - 1, 3, 2, 2, GRASS, seed=x)


def waterfall(g):
    H, N = 48, 8
    fn, col, front = cliff_mask(H, notch=N); g.fshape(fn, col)
    grass_cap(g, H, front, notch=N); foot_rocks(g, 5)
    # channel bed behind the water (dark wet rock) + river on top
    g.fshape(lambda X, Y, Z: (np.abs(X) < N) & (Y < H - 1) & (Z >= -4) & (Z < -2), hx('3a4148'))
    g.fshape(lambda X, Y, Z: (np.abs(X) < N + 2) & (np.abs(X) >= N) & (Y < H + 1) & (Z >= -6) & (Z < 14), ROCK[1])   # banks
    g.fshape(lambda X, Y, Z: (np.abs(X) < N) & (Y >= H - 2) & (Y < H) & (Z >= -6) & (Z < 14), WATER[1])
    # falling sheet: lanes of 3 tones (streaks), bulges out as it falls, foam lip at the top
    def sheet(X, Y, Z):
        out = -6 - 2.5 * ((H - Y) / H) ** .6
        return (np.abs(X) < N) & (Y >= 5) & (Y < H) & (Z >= out - 2) & (Z < out)
    g.fshape(sheet, lambda X, Y, Z: np.array(WATER)[((X.astype(int) * 7 + (Y // 6).astype(int) * 3) % 5 > 2).astype(int) + ((X.astype(int) % 4) == 0).astype(int)])
    g.fshape(lambda X, Y, Z: (np.abs(X) < N) & (Y >= H - 3) & (Y < H) & (Z >= -9) & (Z < -6), FOAM)
    # stepped stone pool + water + splash foam + ripple rings
    def pool_rim(X, Y, Z):
        d = np.sqrt(X * X / 1.4 + (Z + 22) ** 2)
        return (Y < 4) & (d < 18) & (d >= 15.5) & (Z < -7)
    g.fshape(pool_rim, lambda X, Y, Z: np.where((Y >= 3)[:, None], STONEL, STONE))
    g.fshape(lambda X, Y, Z: (Y < 3) & (np.sqrt(X * X / 1.4 + (Z + 22) ** 2) < 15.5) & (Z < -7), WATER[0])
    g.blob(0, 3, -11, N + 1, 3, 4, FOAM, lumpy=.35, seed=4)
    for r in (6, 10):
        g.fshape(lambda X, Y, Z, r=r: (Y >= 2) & (Y < 3) & (np.abs(np.sqrt(X * X + (Z + 12) ** 2) - r) < .7) & (Z < -12), WATER[2])


def wall(g, corner=False):
    """straight wall module (60 fine) or an L corner (arms +x and +z from a round turret at the origin)."""
    L = W2
    arms = [((-L, L), None)] if not corner else [((-5, L), 'x'), ((-5, L), 'z')]
    def body(X, Y, Z):
        if not corner: return (Y < 36) & (np.abs(X) < L) & (np.abs(Z) < 5)
        return (Y < 36) & (((X > -5) & (X < L) & (np.abs(Z) < 5)) | ((Z > -5) & (Z < L) & (np.abs(X) < 5)))
    def stone(X, Y, Z):
        row = (Y // 3).astype(int)
        u = np.where(np.abs(X) < 5, Z, X) if corner else X               # run along the arm the cell belongs to
        k = np.floor((u + (row % 2) * 3) / 6)
        seam = (Y % 3 == 0) | (((u + (row % 2) * 3) % 6) == 0)
        h = np.sin(k * 12.9898 + row * 78.233) * 43758.5453; h = h - np.floor(h)   # one tone per block
        c = np.where((h > .78)[:, None], STONEL, np.where((h < .15)[:, None], STONED * 1.15, STONE))
        c = np.where(seam[:, None], STONED, c)
        c = np.where(((Y < 6) & (h > .5) & ~seam)[:, None], MOSS, c)      # moss on some base blocks
        return c
    g.fshape(body, stone)
    for (r0, r1), ax in arms:
        if ax == 'z':
            box = lambda x0, x1, y0, y1, z0, z1: g.fbox(z0, z1, y0, y1, x0, x1, STONE)
        else:
            box = lambda x0, x1, y0, y1, z0, z1: g.fbox(x0, x1, y0, y1, z0, z1, STONE)
        def put(x0, x1, y0, y1, z0, z1, c):
            if ax == 'z': g.fbox(z0, z1, y0, y1, x0, x1, c)
            else: g.fbox(x0, x1, y0, y1, z0, z1, c)
        put(r0, r1, 0, 3, -7, 7, STONED)                                   # plinth
        put(r0, r1, 36, 38, -6, 6, STONEL)                                 # walkway lip
        for x in range(r0 + 8 if corner else r0, r1 - 2, 8):              # crenels both faces
            for z0 in (-6, 3):
                put(x, x + 5, 38, 44, z0, z0 + 3, STONE); put(x, x + 5, 44, 45, z0, z0 + 3, STONEL)
        for x in ((r1 - 8,) if corner else (r0 + 4, r1 - 8)):              # stepped buttresses
            for i, y in enumerate((0, 10, 20)):
                put(x, x + 4, y, y + 10, -8 + i, -5, STONE); put(x, x + 4, y + 9, y + 10, -8 + i, -5, STONEL)
        for x in ((14,) if corner else (-12, 12)):                         # arrow slits + lintel
            if ax == 'z': g.fcut(-5, -2, 16, 26, x, x + 2)
            else: g.fcut(x, x + 2, 16, 26, -5, -2)
            put(x - 1, x + 3, 26, 27, -6, -5, STONEL)
    if corner:
        g.fshape(lambda X, Y, Z: (Y < 50) & (X * X + Z * Z < 9 ** 2), stone)                 # round turret
        g.fshape(lambda X, Y, Z: (Y >= 50) & (Y < 52) & (X * X + Z * Z < 10.5 ** 2), STONEL)
        g.fshape(lambda X, Y, Z: (Y < 3) & (X * X + Z * Z < 11 ** 2), STONED)
        for i in range(10):
            a = i * 6.283 / 10
            if i % 2 == 0: g.fbox(int(np.cos(a) * 9) - 2, int(np.cos(a) * 9) + 2, 52, 57, int(np.sin(a) * 9) - 2, int(np.sin(a) * 9) + 2, STONE)


PIECES = {'Cliff': (cliff, (26, 20, 18)), 'Waterfall': (waterfall, (26, 20, 28)),
          'Wall': (wall, (26, 18, 8)), 'WallCorner': (lambda g: wall(g, True), (26, 22, 26))}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
name = next((a for a in argv if a in PIECES), 'Cliff')
fn, size = PIECES[name]
g = Grid(*size, R=3); fn(g); g.export(name, HERE, glow=GLOW or None)
