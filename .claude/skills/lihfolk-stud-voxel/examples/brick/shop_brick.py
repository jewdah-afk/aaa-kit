# Shop (static building example, brick pipeline, no rig). bld.Grid: units of 2.5 studs, carved at R=3 fine bricks (0.83 studs).
# Footprint ~36 x 30 studs, door ~5 x 9 studs. Bands: stone plinth / plank walls + log corner posts + trim / 45-degree shingle roof
# with overhang + ridge. Accent = gold (sign, frames). Glow = warm panes, lanterns, sign gem. Props: barrels, crates, flower boxes.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/lihfolk-stud-voxel/scripts')) if os.path.exists(os.path.join(p, 'bld.py'))))
from bld import Grid, hx

STONE, STONED = '7a7f8a', '4f535c'
PLANK, POST, POSTD = 'c98b52', '7a4a28', '5a341b'
ROOF, ROOFD, RIDGE = 'd2463c', 'a8332c', '6e211c'
GOLD, GOLDD, DOOR, DOORD = 'f2b630', 'b9821a', '8a5530', '5e381d'
AWN1, AWN2, LEAF, FLOW = 'f4efe2', '3fa0e8', '4fbf4a', 'ff6fa8'
GLOW = {2: hx('ffcf6a'), 3: hx('5ff0ff')}

g = Grid(26, 22, 22, R=3)
W, D = 7, 6
g.box(-W - 1, W + 1, 0, 1, -D - 1, D + 1, STONE, pat='stone')          # plinth, 1 proud
g.box(-W, W, 1, 7, -D, D, PLANK, pat='plank'); g.cut(-W + 1, W - 1, 1, 7, -D + 1, D - 1)
for x0 in (-W - 1, W - 1):
    for z0 in (-D - 1, D - 1): g.box(x0, x0 + 2, 1, 7, z0, z0 + 2, POST, pat='log')
g.box(-W - 1, W + 1, 7, 8, -D - 1, D + 1, POSTD, pat='log')             # trim beam

# ---- fine work (fine = unit * 3)
F = 3
y0 = 8 * F; half0 = (W + 2) * F; zd = (D + 2) * F
for i in range(half0):                               # 45-degree shingle roof, darker eave rows + edge bricks
    h = half0 - i
    c = ROOFD if i < 2 else (hx(ROOF) * (.8 if i % 3 == 0 else 1.0))
    t = min(h, 4)                                    # roof is a shell 4 bricks thick, so the gable shows under it
    g.fbox(-h, -h + t, y0 + i, y0 + i + 1, -zd, zd, c); g.fbox(h - t, h, y0 + i, y0 + i + 1, -zd, zd, c)
    g.fbox(-h, -h + t, y0 + i, y0 + i + 1, -zd, -zd + 1, ROOFD); g.fbox(h - t, h, y0 + i, y0 + i + 1, -zd, -zd + 1, ROOFD)
    g.fbox(-h, -h + t, y0 + i, y0 + i + 1, zd - 1, zd, ROOFD); g.fbox(h - t, h, y0 + i, y0 + i + 1, zd - 1, zd, ROOFD)
g.fbox(-2, 2, y0 + half0 - 1, y0 + half0 + 1, -zd - 1, zd + 1, RIDGE)
for z in range(-zd, zd, 6): g.fbox(-1, 1, y0 + half0 + 1, y0 + half0 + 2, z, z + 2, RIDGE)
zf = -D * F
for zz in (zf, D * F - 1):                           # gable plank infill under the roof
    for i in range(half0 - 2):
        h = half0 - 2 - i
        g.fbox(-h, h, y0 + i, y0 + i + 1, zz, zz + 1, hx(PLANK) * (.8 if (y0 + i) % 3 == 0 else 1))
g.window(-3, 3, y0 + 10, y0 + 16, zf, GOLDD)         # attic window
for y in range(30, 54):                              # chimney, stone courses + cap
    g.fbox(9, 15, y, y + 1, 6, 12, hx(STONE) * (.75 if y % 3 == 0 else 1))
g.fbox(8, 16, 54, 56, 5, 13, STONED)
g.fcut(-4, 4, 3, 16, zf, zf + 3)                     # door
for x in range(-4, 4): g.fbox(x, x + 1, 3, 16, zf + 2, zf + 3, DOOR if x % 2 else DOORD)
g.fbox(-4, 4, 6, 7, zf + 1, zf + 2, POSTD); g.fbox(-4, 4, 12, 13, zf + 1, zf + 2, POSTD)
g.fbox(2, 3, 9, 10, zf, zf + 2, GOLD)
g.fbox(-5, -4, 3, 17, zf - 1, zf, GOLD); g.fbox(4, 5, 3, 17, zf - 1, zf, GOLD); g.fbox(-5, 5, 16, 17, zf - 1, zf, GOLD)
g.fbox(-6, 6, 0, 3, zf - 3, zf, STONED)
for xs in (-16, 8):                                  # shop windows + flower boxes
    g.window(xs, xs + 8, 7, 15, zf, GOLDD, sill=POST)
    g.fbox(xs - 1, xs + 9, 4, 6, zf - 3, zf, POST)
    for x in range(xs, xs + 8, 2): g.fbox(x, x + 1, 6, 7, zf - 3, zf - 1, FLOW if x % 4 else LEAF)
for x in range(-W * F, W * F):                       # striped awning, sloped, scalloped edge
    c = AWN1 if (x // 3) % 2 == 0 else AWN2
    g.fbox(x, x + 1, 18, 19, zf - 3, zf, c); g.fbox(x, x + 1, 17, 18, zf - 6, zf - 3, c)
    if x % 3 == 1: g.fbox(x, x + 1, 16, 17, zf - 6, zf - 5, c)
g.fbox(-7, 7, 33, 40, zf - 2, zf - 1, GOLDD); g.fbox(-6, 6, 34, 39, zf - 3, zf - 2, GOLD)   # sign
for (x0, x1, y0, y1) in ((-2, 2, 34, 35), (-2, 2, 38, 39), (-3, -2, 35, 38), (2, 3, 35, 38)):   # coin ring
    g.fbox(x0, x1, y0, y1, zf - 4, zf - 3, 'ffd34a')
g.fbox(-1, 1, 35, 38, zf - 4, zf - 3, GOLDD); g.fbox(0, 1, 35, 38, zf - 5, zf - 4, 'ffd34a')
for x in (-21, 20):                                  # lantern posts
    g.fbox(x, x + 1, 3, 15, zf - 2, zf - 1, POSTD)
    g.fbox(x - 2, x + 3, 14, 15, zf - 4, zf + 1, POSTD); g.fbox(x - 2, x + 3, 19, 20, zf - 4, zf + 1, POSTD)
    g.fbox(x - 1, x + 2, 20, 21, zf - 3, zf, POSTD)
    for (a, b) in ((x - 2, zf - 4), (x + 2, zf - 4), (x - 2, zf), (x + 2, zf)): g.fbox(a, a + 1, 15, 19, b, b + 1, POSTD)
    g.fbox(x - 1, x + 2, 15, 19, zf - 3, zf, '000000', k=2)
for bx in (-26, -20):                                # barrels
    for y in range(3, 11):
        w = 2 if y in (3, 10) else 3
        g.fbox(bx - w, bx + w, y, y + 1, zf - 9 - w, zf - 9 + w, POSTD if y in (4, 9) else DOOR)
for (cx, cy) in ((19, 3), (25, 3), (22, 9)):          # crates
    g.fbox(cx - 3, cx + 3, cy, cy + 6, zf - 12, zf - 6, PLANK)
    for a in ((cx - 3, cx + 3, cy, cy + 1), (cx - 3, cx + 3, cy + 5, cy + 6), (cx - 3, cx - 2, cy, cy + 6), (cx + 2, cx + 3, cy, cy + 6)):
        g.fbox(a[0], a[1], a[2], a[3], zf - 13, zf - 12, POST)
g.export('Shop', HERE, glow=GLOW)
