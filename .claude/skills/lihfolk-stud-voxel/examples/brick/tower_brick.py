# Watchtower (static building example, brick pipeline, no rig). bld.Grid units 2.5 studs, R=3 fine bricks.
# ~27-stud base, ~75 studs tall. Bands: battered stone base with quoins / plaster shaft with stone courses, timber
# cross-bracing and glowing arrow slits / corbelled timber lookout with railing / stepped blue cone roof + gold finial + beacon.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/lihfolk-stud-voxel/scripts')) if os.path.exists(os.path.join(p, 'bld.py'))))
from bld import Grid, hx
def flame(g, cx, cy, cz, h, w):                      # stepped flame: wide base, narrow tip, hot core inside
    for i in range(h):
        r = max(1, round(w * (1 - i / h) ** .7))
        g.fbox(cx - r, cx + r, cy + i, cy + i + 1, cz - r, cz + r, 'ff7a1a' if i < h * .5 else 'ffb347')
    g.fbox(cx - 1, cx + 1, cy, cy + h // 2, cz - 1, cz + 1, '000000', k=2)
IRON_RIM = '3a3d45'

STONE, STONED, STONEL = '7a7f8a', '4f535c', 'a3a9b3'
PLAST, WOOD, WOODD = 'ece0c4', '8a5a32', '5a341b'
ROOF, ROOFD, GOLD = '3b62c8', '27428f', 'f2b630'
GLOW = {2: hx('ffcf6a'), 3: hx('7cf4ff')}
F = 3

g = Grid(20, 38, 20, R=F)
g.box(-6, 6, 0, 1, -6, 6, STONED, pat='stone')                 # plinth
g.box(-5, 5, 1, 4, -5, 5, STONE, pat='stone')                  # stone base
g.box(-4, 4, 4, 18, -4, 4, PLAST); g.cut(-3, 3, 1, 18, -3, 3)  # plaster shaft (hollow)
for y in (4, 10, 17): g.box(-4, 4, y, y + 1, -4, 4, STONE, pat='stone')   # courses
for x0 in (-5, 3):                                             # quoins: long / short blocks alternate by height
    for z0 in (-5, 3):
        for y in range(4, 18):
            if y % 2: g.box(x0, x0 + 2, y, y + 1, z0, z0 + 2, STONEL, pat='stone')
            else: g.box(x0 + (1 if x0 < 0 else 0), x0 + 1 + (1 if x0 < 0 else 0), y, y + 1, z0 + (1 if z0 < 0 else 0), z0 + 1 + (1 if z0 < 0 else 0), STONEL, pat='stone')
zf = -4 * F                                                    # front wall outer fine z
# timber cross braces on the plaster between courses (front + back)
for (ya, yb) in ((5 * F, 10 * F), (11 * F, 17 * F)):
    for zz in (zf - 1, 4 * F):
        for t in range(yb - ya):
            x = -9 + int(18 * t / (yb - ya))
            g.fbox(x, x + 2, ya + t, ya + t + 1, zz, zz + 1, WOOD); g.fbox(-x - 2, -x, ya + t, ya + t + 1, zz, zz + 1, WOOD)
# door: arched, recessed, studded planks, stone surround, steps
g.fcut(-4, 4, 3, 15, zf - 3 + 3 - 6, zf + 3)
for x in range(-4, 4): g.fbox(x, x + 1, 3, 15, zf + 2, zf + 3, WOOD if x % 2 else WOODD)
for y in (6, 11): g.fbox(-4, 4, y, y + 1, zf + 1, zf + 2, STONED)
g.fbox(-5, 5, 15, 17, zf - 4, zf - 3, STONEL); g.fbox(-6, -4, 3, 17, zf - 4, zf - 3, STONEL); g.fbox(4, 6, 3, 17, zf - 4, zf - 3, STONEL)
g.fbox(-3, 3, 17, 18, zf - 4, zf - 3, STONEL)
g.fbox(-6, 6, 0, 2, zf - 8, zf - 3, STONED); g.fbox(-5, 5, 2, 3, zf - 6, zf - 3, STONED)
# arrow slits on all 4 sides, two levels: tall narrow opening, glow inside, stone lintel
for yy in (30, 42):
    g.fcut(-1, 1, yy, yy + 7, zf, zf + 3); g.fbox(-1, 1, yy, yy + 7, zf + 3, zf + 4, '000000', k=2); g.fbox(-2, 2, yy + 7, yy + 8, zf - 1, zf, STONEL)
    g.fcut(-1, 1, yy, yy + 7, -zf - 3, -zf); g.fbox(-1, 1, yy, yy + 7, -zf - 4, -zf - 3, '000000', k=2)
    g.fcut(zf, zf + 3, yy, yy + 7, -1, 1); g.fbox(zf + 3, zf + 4, yy, yy + 7, -1, 1, '000000', k=2); g.fbox(zf - 1, zf, yy + 7, yy + 8, -2, 2, STONEL)
    g.fcut(-zf - 3, -zf, yy, yy + 7, -1, 1); g.fbox(-zf - 4, -zf - 3, yy, yy + 7, -1, 1, '000000', k=2); g.fbox(-zf, -zf + 1, yy + 7, yy + 8, -2, 2, STONEL)
# corbels under the lookout (stepped timber brackets)
yl = 18 * F
for k in range(3):
    for s in (-1, 1):
        for x in (-9, -3, 3, 9):
            g.fbox(x - 1, x + 1, yl - 3 + k, yl - 2 + k, s * (12 + k) - (1 if s < 0 else 0), s * (12 + k) + (0 if s < 0 else 1), WOODD)
            g.fbox(s * (12 + k) - (1 if s < 0 else 0), s * (12 + k) + (0 if s < 0 else 1), yl - 3 + k, yl - 2 + k, x - 1, x + 1, WOODD)
# lookout deck + railing + posts
g.fbox(-18, 18, yl, yl + 2, -18, 18, WOODD)
for i in range(-18, 18):
    g.fbox(i, i + 1, yl + 2, yl + 8 if i % 4 == 0 else yl + 3, -18, -17, WOOD); g.fbox(i, i + 1, yl + 2, yl + 8 if i % 4 == 0 else yl + 3, 17, 18, WOOD)
    g.fbox(-18, -17, yl + 2, yl + 8 if i % 4 == 0 else yl + 3, i, i + 1, WOOD); g.fbox(17, 18, yl + 2, yl + 8 if i % 4 == 0 else yl + 3, i, i + 1, WOOD)
for a in ((-18, 18, -18, -17), (-18, 18, 17, 18), (-18, -17, -18, 18), (17, 18, -18, 18)):
    g.fbox(a[0], a[1], yl + 7, yl + 9, a[2], a[3], WOODD)
for x in (-15, 14):
    for z in (-15, 14): g.fbox(x, x + 2, yl + 2, yl + 20, z, z + 2, WOODD)
g.fbox(-2, 2, yl + 2, yl + 4, -2, 2, STONED); g.fbox(-4, 4, yl + 4, yl + 6, -4, 4, STONE)   # brazier: foot + bowl
g.fcut(-3, 3, yl + 5, yl + 6, -3, 3); g.fbox(-5, 5, yl + 6, yl + 7, -5, 5, IRON_RIM)
flame(g, 0, yl + 6, 0, 9, 3)
# stepped cone roof with shingle rows, darker eave, gold finial + beacon gem
yr = yl + 20
for i in range(22):
    h = 21 - i
    c = ROOFD if i < 2 else hx(ROOF) * (.8 if i % 3 == 0 else 1)
    g.fbox(-h, h, yr + i, yr + i + 1, -h, h, c)
g.fbox(-3, 3, yr + 22, yr + 23, -3, 3, GOLD); g.fbox(-2, 2, yr + 23, yr + 25, -2, 2, GOLD)   # finial: collar, knob, spire
g.fbox(-3, 3, yr + 25, yr + 28, -2, 2, GOLD); g.fbox(-2, 2, yr + 25, yr + 28, -3, 3, GOLD)
g.fbox(-1, 1, yr + 28, yr + 33, -1, 1, GOLD); g.fbox(0, 1, yr + 33, yr + 35, 0, 1, GOLD)
g.export('Watchtower', HERE, glow=GLOW)
