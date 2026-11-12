# Snowman Grunt (stud-voxel mob, brick pipeline on brick_core). DRAFT: first pass only, not an approved look (arms too thick, eyes too flat).
# Reference: concept_snowman-grunt.png on branch codex/christmas-concept-sheets (refs/lihfolk-voxel/concepts/).
# GLOW: none
# The smallest brick_core example: copy it for simple mobs made of a few big stepped masses.
# Chunky look: every shape is tested on coordinates quantised to U = 4 bricks, so one concept voxel = 4x4x4 bricks = 2x2 studs.
# Run: bash <skill>/scripts/run_brick.sh snowman_grunt_brick.py [views]
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from brick_core import Model, hx
import brick_rig

U = 4
M = Model('SnowmanGrunt', __file__, lo=(-64, 0, -36), hi=(64, 88, 36))
X, Y, Z = M.X, M.Y, M.Z
q = lambda v: M.step(v, U)
Xq, Yq, Zq = q(X), q(Y), q(Z)

SNOW_L, SNOW, SNOW_D = hx('fbfbfa'), hx('e9ebef'), hx('c9ced9')        # lit tops / main / underside
SCARF, SCARF_D = hx('8e2338'), hx('6a1629')
COAL = hx('2b2b30')
STICK, STICK_D = hx('8a5630'), hx('5f391d')


def ball(c, r):
    return ((Xq - c[0]) / r[0]) ** 2 + ((Yq - c[1]) / r[1]) ** 2 + ((Zq - c[2]) / r[2]) ** 2 < 1


def snow(mask, cy, ry, p):
    t = (Yq - cy) / ry
    M.put(mask & (t > .38), SNOW_L, p=p); M.put(mask & (t <= .38) & (t > -.5), SNOW, p=p); M.put(mask & (t <= -.5), SNOW_D, p=p)


# ---------------------------------------------------------------- body + head: two stepped balls, the lower one flattened on the ground
BC, BR = (0, 24, 0), (27, 27, 25)
HC, HR = (0, 64, 0), (19, 19, 18)
body = ball(BC, BR) & (Y > 0)
head = ball(HC, HR)
P_BODY, P_HEAD = M.part(), M.part()
snow(body, BC[1], BR[1], P_BODY)
snow(head & ~body, HC[1], HR[1], P_HEAD)
dent = ball((14, 20, -22), (9, 7, 6)) & body                           # the scooped dent low on the front right
M.put(dent & M.surface(), SNOW_D, p=P_BODY, keep=True)

# ---------------------------------------------------------------- face: flush coal eyes and a 5-coal smile (painted on the surface layer)
front = M.surface(head) & (Z < -8)
def coal(x, y, w=U, h=U):
    m = front & (Xq > x - w / 2) & (Xq < x + w / 2) & (Yq > y - h / 2) & (Yq < y + h / 2)
    M.put(m, COAL, p=P_HEAD, keep=True)
for sx in (-1, 1): coal(sx * 8, 70, 2 * U - 1, 2 * U - 1)               # eyes: 1 voxel each, wide apart
for x, y in ((-10, 58), (-6, 54), (-2, 54), (2, 54), (6, 54), (10, 58)): coal(x, y)

# ---------------------------------------------------------------- scarf: a ring at the neck + one hanging tail with a notched end
P_SCARF = M.part()
rr = np.sqrt(Xq ** 2 + Zq ** 2)
ring = (Yq > 42) & (Yq < 52) & (rr < 23) & ~head & ~body
ring |= (Yq > 42) & (Yq < 52) & (rr < 23) & (rr > 15)
M.put(ring & (Yq > 46), SCARF, p=P_SCARF, l=2); M.put(ring & (Yq <= 46), SCARF_D, p=P_SCARF, l=2)
tail = (Xq > -16) & (Xq < -4) & (Yq > 20) & (Yq < 46) & (Z < 0)
tail_m = tail & ~body & (np.roll(body, -U, axis=2) | np.roll(body, -2 * U, axis=2))      # one voxel proud of the belly
tail_m &= ~((Xq > -12) & (Xq < -8) & (Yq < 28))                                          # notch between the two tassels
M.put(tail_m, SCARF, p=P_SCARF, l=3); M.put(tail_m & (Yq < 28), SCARF_D, p=P_SCARF, l=3)

# ---------------------------------------------------------------- stick arms: up and out, forked ends (1 voxel thick, stepped)
P_ARM = M.part()
ARMS = {}
for s, nm in ((1, 'L'), (-1, 'R')):
    pts = [(s * 22, 38, 0), (s * 36, 44, 0), (s * 46, 56, 0), (s * 54, 64, 0)]
    m = np.zeros(M.n, bool)
    for a, b in zip(pts, pts[1:]): m |= M.cap(a, b, 2.4)
    m |= M.cap(pts[2], (s * 46, 70, 0), 2.2) | M.cap(pts[3], (s * 60, 60, 0), 2.0) | M.cap(pts[3], (s * 56, 72, 0), 2.0)   # forks
    mq = np.zeros(M.n, bool)                                                     # snap the capsules to whole voxels
    ix = np.argwhere(m); cell = np.unique(ix // U, axis=0)
    for c in cell: mq[c[0] * U:(c[0] + 1) * U, c[1] * U:(c[1] + 1) * U, c[2] * U:(c[2] + 1) * U] = True
    mq &= (np.abs(Z) < U / 2 + .1) & ~body & ~head
    M.put(mq, STICK, p=P_ARM); M.put(mq & (Yq < 44), STICK_D, p=P_ARM)
    ARMS[nm] = (mq, pts)

# ---------------------------------------------------------------- rig + finish
sol = M.kind > 0
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('body', 'root', (0, 6, 0), (0, 44, 0)), ('head', 'body', (0, 46, 0), (0, 82, 0)),
       ('scarf', 'body', (-10, 44, -24), (-10, 22, -28))]
OVR = [(sol, 'body'), (sol & (Y > 52), 'head'), (sol & ring, 'body'), (sol & tail_m, 'scarf')]
for nm, (mq, pts) in ARMS.items():
    ch = [('arm%s' % nm, 'body', pts[0], pts[2]), ('hand%s' % nm, 'arm%s' % nm, pts[2], pts[3])]
    RIG += ch; OVR += brick_rig.limb(X, Y, Z, mq & sol, ch)
M.finish(rig=RIG, overrides=OVR, pose={'head': (0, 20, 8), 'armL': (0, 0, 25), 'armR': (0, 0, 20), 'scarf': (-20, 0, 0)},
         face=((0, 62, -20), 120), shade=(1.0, 1.0))
