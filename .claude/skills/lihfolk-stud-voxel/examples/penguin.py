# Penguin: chibi emperor-chick pet, box rig (copied from the skill's duck.py and edited).
# Units: metres, Z up, front = -Y, left = +X. STUDS 5.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'Penguin'
STUDS = 5.0
# Slate-navy hue, 4 tones with FIXED jobs: N2 tops/caps, N1 main, N3 side steps, N4 underside/back stub.
# White belly + heart face (W1, W2 = shade), yellow ear patches, orange beak/feet, eyes, blush.
PALETTE = dict(N1='4d669a', N2='7088bc', N3='415788', N4='364a74', W1='f6f8fc', W2='dfe5f0',
               YE='ffd23f', YD='f2a51f', OR='ff8a1f', OD='e0640e',
               EY='171a2c', IR='2f5bc4', WH='ffffff', PK='ff9fb4')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0, 0.45), (0, 0, 0.85), 'root'),
         ('head', (0, -0.05, 0.90), (0, -0.05, 1.40), 'body'),
         ('tuft', (0, -0.10, 1.64), (0, -0.10, 1.80), 'head'),
         ('tail', (0, 0.42, 0.26), (0, 0.58, 0.22), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'flipper.{s}', (0.48 * sx, -0.02, 0.80), (0.64 * sx, -0.02, 0.34), 'body'),
              (f'leg.{s}', (0.20 * sx, -0.10, 0.16), (0.20 * sx, -0.10, 0.0), 'root')]
HEAD = dict(scale=1.35, pivot=(0, -0.05, 0.90), bones=('head', 'tuft'))


def build(K):
    span, sym = K.span, K.sym
    # body: upright stepped egg, slate back, white round belly
    span(-0.34, 0.34, -0.36, 0.36, 0.12, 0.18, 'W2', 'body')        # underside
    span(-0.42, 0.42, -0.48, 0.48, 0.18, 0.64, 'N1', 'body')        # core (wide bottom)
    span(-0.40, 0.40, -0.42, 0.42, 0.64, 0.84, 'N1', 'body')        # upper core (narrower: egg taper)
    sym(-0.32, 0.32, 0.48, 0.54, 0.24, 0.58, 'N3', 'body')          # side step
    span(-0.36, 0.36, -0.42, 0.42, 0.84, 0.90, 'N2', 'body')        # shoulders
    span(0.42, 0.48, -0.36, 0.36, 0.24, 0.80, 'N1', 'body')         # back curve
    span(0.48, 0.52, -0.24, 0.24, 0.34, 0.70, 'N3', 'body')
    span(-0.48, -0.42, -0.38, 0.38, 0.26, 0.62, 'W1', 'body')       # belly plate (rounded by steps)
    span(-0.48, -0.42, -0.32, 0.32, 0.62, 0.76, 'W1', 'body')
    span(-0.48, -0.42, -0.24, 0.24, 0.76, 0.84, 'W1', 'body')
    span(-0.48, -0.42, -0.30, 0.30, 0.20, 0.26, 'W1', 'body')
    span(-0.54, -0.48, -0.30, 0.30, 0.30, 0.66, 'W1', 'body')       # belly bulge
    span(-0.54, -0.48, -0.22, 0.22, 0.66, 0.76, 'W1', 'body')
    span(-0.58, -0.54, -0.20, 0.20, 0.38, 0.62, 'W1', 'body')       # belly front
    span(-0.54, -0.42, -0.30, 0.30, 0.20, 0.28, 'W2', 'body')       # belly shade underneath
    # tail stub
    span(0.48, 0.58, -0.14, 0.14, 0.18, 0.32, 'N4', 'tail')
    span(0.58, 0.64, -0.08, 0.08, 0.18, 0.26, 'N4', 'tail')
    # flippers: held a little out, steps sweep outward and down
    for sx, s in K.sides():
        b = f'flipper.{s}'
        span(-0.20, 0.16, 0.48 * sx, 0.60 * sx, 0.58, 0.80, 'N1', b)
        span(-0.18, 0.14, 0.54 * sx, 0.66 * sx, 0.40, 0.58, 'N1', b)
        span(-0.12, 0.08, 0.58 * sx, 0.70 * sx, 0.30, 0.40, 'N3', b)
        span(-0.16, 0.12, 0.48 * sx, 0.58 * sx, 0.80, 0.84, 'N2', b)
    # head (all 'head' boxes get the chibi scale)
    span(-0.40, 0.30, -0.40, 0.40, 0.90, 1.52, 'N1', 'head')        # skull core
    sym(-0.32, 0.22, 0.40, 0.45, 0.98, 1.46, 'N3', 'head')          # cheek step
    span(-0.32, 0.22, -0.32, 0.32, 1.52, 1.60, 'N2', 'head')        # crown
    span(-0.22, 0.12, -0.20, 0.20, 1.60, 1.64, 'N2', 'head')        # crown cap
    span(0.30, 0.34, -0.30, 0.30, 0.98, 1.44, 'N3', 'head')         # back of head step
    # heart face patch (white), notch at the top centre
    span(-0.43, -0.40, -0.06, 0.06, 0.98, 1.04, 'W1', 'head')
    span(-0.43, -0.40, -0.18, 0.18, 1.04, 1.10, 'W1', 'head')
    span(-0.43, -0.40, -0.28, 0.28, 1.10, 1.18, 'W1', 'head')
    span(-0.43, -0.40, -0.35, 0.35, 1.18, 1.36, 'W1', 'head')
    sym(-0.43, -0.40, 0.06, 0.34, 1.36, 1.44, 'W1', 'head')
    sym(-0.43, -0.40, 0.10, 0.29, 1.44, 1.48, 'W1', 'head')
    sym(-0.43, -0.40, 0.14, 0.24, 1.48, 1.51, 'W1', 'head')
    for sx in (1, -1):   # eyes: dark block + blue iris + 2 white shines, proud of the patch
        span(-0.46, -0.43, 0.08 * sx, 0.23 * sx, 1.17, 1.37, 'EY', 'head')
        span(-0.465, -0.46, 0.12 * sx, 0.21 * sx, 1.19, 1.26, 'IR', 'head')
        span(-0.475, -0.46, 0.15 * sx, 0.21 * sx, 1.29, 1.35, 'WH', 'head')
        span(-0.475, -0.465, 0.10 * sx, 0.13 * sx, 1.20, 1.23, 'WH', 'head')
        span(-0.445, -0.43, 0.24 * sx, 0.32 * sx, 1.08, 1.14, 'PK', 'head')   # blush
        # yellow ear patch on each side of the head
        span(-0.26, 0.06, 0.45 * sx, 0.47 * sx, 1.14, 1.38, 'YE', 'head')
        span(-0.20, 0.02, 0.45 * sx, 0.47 * sx, 1.06, 1.14, 'YD', 'head')
        span(-0.16, -0.02, 0.45 * sx, 0.47 * sx, 1.38, 1.42, 'YE', 'head')
        span(-0.32, -0.26, 0.43 * sx, 0.46 * sx, 1.18, 1.34, 'YE', 'head')
    # beak: short, two steps
    span(-0.56, -0.43, -0.09, 0.09, 1.08, 1.17, 'OR', 'head')
    span(-0.60, -0.56, -0.06, 0.06, 1.09, 1.15, 'OR', 'head')
    span(-0.56, -0.43, -0.07, 0.07, 1.06, 1.08, 'OD', 'head')
    # fluffy tuft on top
    span(-0.18, -0.02, -0.07, 0.07, 1.64, 1.78, 'N2', 'tuft')
    span(-0.14, -0.04, -0.04, 0.04, 1.78, 1.86, 'N2', 'tuft')
    span(-0.22, -0.14, -0.03, 0.03, 1.82, 1.90, 'N2', 'tuft')   # curl forward
    sym(-0.16, -0.04, 0.07, 0.14, 1.64, 1.74, 'N2', 'tuft')
    sym(-0.14, -0.06, 0.14, 0.18, 1.70, 1.78, 'N2', 'tuft')
    # legs + feet
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.14, -0.04, 0.15 * sx, 0.25 * sx, 0.06, 0.14, 'OD', b)
        span(-0.32, 0.00, 0.08 * sx, 0.32 * sx, 0.00, 0.06, 'OR', b)
        for dx in (0.10, 0.20, 0.30):
            span(-0.42, -0.32, (dx - 0.04) * sx, (dx + 0.04) * sx, 0.00, 0.06, 'OR', b)


# ---- clips: fn(frame) -> {bone: (rx, ry, rz) degrees, 'root_loc': (x, y, z) metres} ----
def idle(f):
    ph = TAU * f / 90
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 12 * S(TAU * f / 180)),
            'tuft': (0, 10 * S(2 * ph), 0), 'tail': (0, 0, 8 * S(2 * ph)),
            'flipper.L': (0, -12 - 5 * S(ph), 0), 'flipper.R': (0, 12 + 5 * S(ph), 0)}


def walk(f):   # waddle: big side roll + yaw, stiff little steps, flippers bob out
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 11 * S(ph), 6 * c), 'body': (2, 0, 0), 'head': (-4 * abs(S(ph)), -7 * S(ph), -4 * c),
            'tuft': (0, -14 * S(ph), 0),
            'leg.L': (-22 * S(ph), 0, 0), 'leg.R': (22 * S(ph), 0, 0), 'tail': (6, 0, -16 * S(ph)),
            'flipper.L': (0, -22 - 10 * S(2 * ph), 0), 'flipper.R': (0, 22 + 10 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.04 * abs(S(ph)))}


def slide(f):   # belly-flop: crouch -> dive -> toboggan wobble -> pop back up
    if f < 10: a, k = 0, EASE(f / 10)
    elif f < 18: a, k = EASE((f - 10) / 8), 1 - EASE((f - 10) / 8)
    elif f < 36: a, k = 1, 0
    else: a, k = 1 - EASE(min((f - 36) / 12, 1)), 0
    w = S(TAU * f / 9) if 18 <= f < 36 else 0
    return {'root': (84 * a - 10 * k, 4 * w, 0), 'body': (0, 0, 0), 'head': (-55 * a + 6 * k, 0, 6 * w),
            'tuft': (0, 15 * w, 0),
            'flipper.L': (-20 * a, -70 * a - 10 * k, 0), 'flipper.R': (-20 * a, 70 * a + 10 * k, 0),
            'leg.L': (-70 * a + 20 * a * w, 0, 0), 'leg.R': (-70 * a - 20 * a * w, 0, 0), 'tail': (20 * a, 0, 0),
            'root_loc': (0, 0, 0.52 * a - 0.06 * k)}


def flap(f):
    w = S(TAU * f / 12)
    return {'flipper.L': (0, -15 - 50 * (w + 1) / 2, 0), 'flipper.R': (0, 15 + 50 * (w + 1) / 2, 0),
            'body': (-4, 0, 0), 'head': (4, 0, 0), 'tuft': (0, 0, 12 * w),
            'root_loc': (0, 0, 0.06 * (1 + S(TAU * f / 12 - 1)))}


CLIPS = {'Idle': (90, idle), 'Walk': (24, walk), 'Slide': (48, slide), 'Flap': (12, flap)}
PREVIEW = dict(target=(0, -0.1, 0.95), ortho=3.0, shots=[('Slide', 26), ('Flap', 3)], loop='Walk')
