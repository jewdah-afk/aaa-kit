# Castle gate (static building example, brick pipeline, no rig). bld.Grid units 2.5 studs, R=3 fine bricks.
# ~65 studs wide, ~55 tall, opening ~20 x 25 studs (walkable). Two square towers with crenels + glowing slits,
# arched gatehouse with portcullis, wooden doors open, stone voussoir arch, gold crest with gem, torches, wall stubs.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/lihfolk-stud-voxel/scripts')) if os.path.exists(os.path.join(p, 'bld.py'))))
from bld import Grid, hx
def flame(g, cx, cy, cz, h, w):                      # stepped flame: wide base, narrow tip, hot core inside
    for i in range(h):
        r = max(1, round(w * (1 - i / h) ** .7))
        g.fbox(cx - r, cx + r, cy + i, cy + i + 1, cz - r, cz + r, 'ff7a1a' if i < h * .5 else 'ffb347')
    g.fbox(cx - 1, cx + 1, cy, cy + h // 2, cz - 1, cz + 1, '000000', k=2)

STONE, STONED, STONEL = '8a8f99', '565a63', 'b0b5be'
WOOD, WOODD, IRON = '8a5a32', '5a341b', '3a3d45'
GOLD, CLOTH = 'f2b630', 'c43a3a'
GLOW = {2: hx('ffb347'), 3: hx('7cf4ff')}
F = 3

g = Grid(30, 26, 14, R=F)
g.box(-14, 14, 0, 1, -5, 5, STONED, pat='stone')                       # foundation
g.box(-6, 6, 1, 15, -4, 4, STONE, pat='stone')                          # gatehouse
for s in (-1, 1):                                                       # towers
    x0, x1 = (6, 13) if s > 0 else (-13, -6)
    g.box(x0, x1, 1, 18, -5, 5, STONE, pat='stone')
    g.box(x0 - 1 if s < 0 else x0, x1 + 1 if s > 0 else x1, 1, 3, -6, 6, STONED, pat='stone')   # battered foot
    g.box(x0 - (1 if s < 0 else 0), x1 + (1 if s > 0 else 0), 18, 19, -6, 6, STONEL, pat='stone')  # corbel band
    for i, x in enumerate(range(x0 - (1 if s < 0 else 0), x1 + (1 if s > 0 else 0))):
        for z in (-6, 5):
            if i % 2 == 0: g.box(x, x + 1, 19, 21, z, z + 1, STONE, pat='stone')
    for z in range(-6, 6):
        if z % 2 == 0:
            xe = x1 if s > 0 else x0 - 1
            g.box(xe, xe + 1, 19, 21, z, z + 1, STONE, pat='stone')
    g.box(x0 - 2 if s < 0 else x1, x0 if s < 0 else x1 + 2, 1, 10, -3, 3, STONE, pat='stone')    # wall stubs
g.box(-6, 6, 15, 16, -5, 5, STONEL, pat='stone')                        # gatehouse crenel band
for x in range(-6, 6, 2):
    for z in (-5, 4): g.box(x, x + 1, 16, 18, z, z + 1, STONE, pat='stone')

zf = -4 * F                                                             # gatehouse front fine z
# arched opening through the gatehouse: 24 fine wide, 30 tall, round top
for y in range(3, 42):
    hw = 12 if y < 30 else int((144 - (y - 30) ** 2 * 1.2) ** .5) if 144 - (y - 30) ** 2 * 1.2 > 0 else 0
    if hw: g.fcut(-hw, hw, y, y + 1, zf - 1, -zf + 1)
for y in range(3, 45):                                                  # voussoirs round the arch, light stone, seams
    hw = 15 if y < 30 else int(max(0, 225 - (y - 30) ** 2 * 1.1) ** .5)
    hi = 12 if y < 30 else int(max(0, 144 - (y - 30) ** 2 * 1.2) ** .5)
    if hw > hi:
        c = hx(STONEL) * (.75 if y % 4 == 0 else 1)
        g.fbox(-hw, -hi, y, y + 1, zf - 1, zf, c); g.fbox(hi, hw, y, y + 1, zf - 1, zf, c)
g.fbox(-2, 2, 40, 45, zf - 2, zf - 1, GOLD)                             # keystone
# portcullis raised half way (iron grid in the arch, a little inside)
for x in range(-12, 12, 3): g.fbox(x, x + 1, 22, 40, zf + 3, zf + 4, IRON)
for y in range(22, 40, 3): g.fbox(-12, 12, y, y + 1, zf + 3, zf + 4, IRON)
for x in range(-12, 12, 3): g.fbox(x, x + 1, 21, 22, zf + 2, zf + 5, IRON)   # spikes
# doors swung open against the passage walls
for s in (-1, 1):
    for z in range(zf + 6, zf + 18):
        g.fbox(s * 12 - (1 if s > 0 else 0) - s * 1, s * 12 - (1 if s > 0 else 0) - s * 1 + 1, 3, 30, z, z + 1, WOOD if z % 2 else WOODD)
    for y in (8, 22): g.fbox(s * 11 - (1 if s > 0 else 0) - s * 1, s * 11 - (1 if s > 0 else 0) - s * 1 + 1, y, y + 2, zf + 6, zf + 18, IRON)
# crest above the arch: gold shield with a gem, red cloth band behind
g.fbox(-7, 7, 47, 49, zf - 4, zf - 3, CLOTH)
for y in range(48, 58):
    w = 5 if y > 51 else 5 - (51 - y)
    g.fbox(-w, w, y, y + 1, zf - 5, zf - 4, GOLD)
for i in range(7):                                                      # crossed swords emblem
    g.fbox(-3 + i, -2 + i, 50 + i, 51 + i, zf - 6, zf - 5, 'd7dce3'); g.fbox(3 - i - 1, 3 - i, 50 + i, 51 + i, zf - 6, zf - 5, 'd7dce3')
g.fbox(-4, -1, 50, 51, zf - 7, zf - 6, CLOTH); g.fbox(1, 4, 50, 51, zf - 7, zf - 6, CLOTH)
# tower details: glowing slits (2 levels) + torches by the arch
tzf = -5 * F
for s in (-1, 1):
    cx = s * 28
    for yy in (18, 36):
        g.fcut(cx - 1, cx + 1, yy, yy + 8, tzf, tzf + 3); g.fbox(cx - 1, cx + 1, yy, yy + 8, tzf + 3, tzf + 4, '000000', k=2)
        g.fbox(cx - 2, cx + 2, yy + 8, yy + 9, tzf - 1, tzf, STONEL); g.fbox(cx - 2, cx + 2, yy - 1, yy, tzf - 1, tzf, STONEL)
    tx = s * 16
    g.fbox(tx - 1, tx + 1, 20, 26, zf - 2, zf, IRON); g.fbox(tx - 2, tx + 2, 26, 27, zf - 3, zf, IRON)
    flame(g, tx, 27, zf - 2, 6, 2)
g.export('CastleGate', HERE, glow=GLOW)
