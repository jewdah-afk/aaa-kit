# Duck: the approved reference creature (cute critter). Copy this file to start a new creature.
# Units: metres, Z up, front = -Y, left = +X. STUDS 5 -> ~8 studs tall in Roblox.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'Duck'
STUDS = 5.0
# One hue, 4 tones with FIXED jobs: Y2 tops/caps (light), Y1 main, Y3 wings/side steps, Y4 underside. Accents: bill, eyes, blush.
PALETTE = dict(Y1='ffd83f', Y2='fff08a', Y3='ffc62e', Y4='e89a18', OR='ff9a1f', OD='ec7410',
               EY='1c1a22', WH='ffffff', MO='7a2a12', PK='ff9e9e')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.5), (0, 0.05, 0.8), 'root'),
         ('head', (0, -0.32, 0.88), (0, -0.32, 1.3), 'body'),
         ('jaw', (0, -0.70, 1.07), (0, -0.95, 1.07), 'head'),
         ('tail', (0, 0.62, 0.62), (0, 0.85, 0.85), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.58 * sx, -0.2, 0.64), (0.58 * sx, 0.4, 0.6), 'body'),
              (f'leg.{s}', (0.22 * sx, -0.08, 0.22), (0.22 * sx, -0.08, 0.0), 'root')]
# chibi: head + bill built at normal size, then scaled 1.3x around the neck (what made it "super cute")
HEAD = dict(scale=1.3, pivot=(0, -0.32, 0.86), bones=('head', 'jaw'))


def build(K):
    span, sym = K.span, K.sym
    # body: stepped egg, light on top, dark underneath
    span(-0.40, 0.48, -0.36, 0.36, 0.20, 0.27, 'Y4', 'body')        # belly plate
    span(-0.55, 0.60, -0.50, 0.50, 0.27, 0.70, 'Y1', 'body')        # core
    sym(-0.45, 0.50, 0.50, 0.56, 0.33, 0.64, 'Y3', 'body')          # side step (rounds the sides)
    span(-0.64, -0.55, -0.38, 0.38, 0.32, 0.66, 'Y1', 'body')       # chest
    span(-0.68, -0.64, -0.26, 0.26, 0.40, 0.62, 'Y1', 'body')       # chest front
    span(-0.46, 0.54, -0.40, 0.40, 0.70, 0.79, 'Y2', 'body')        # back top
    span(-0.30, 0.44, -0.26, 0.26, 0.79, 0.84, 'Y2', 'body')        # back cap
    # tail: rising steps
    span(0.60, 0.74, -0.32, 0.32, 0.46, 0.78, 'Y1', 'tail')
    span(0.74, 0.84, -0.22, 0.22, 0.62, 0.90, 'Y1', 'tail')
    span(0.84, 0.92, -0.12, 0.12, 0.76, 0.98, 'Y2', 'tail')
    span(0.74, 0.84, -0.22, 0.22, 0.90, 0.93, 'Y2', 'tail')
    # wings: two rows, tip sweeps back and up, grooves stand 0.01 proud
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(-0.28, 0.36, 0.56 * sx, 0.64 * sx, 0.38, 0.66, 'Y3', b)
        span(-0.22, 0.30, 0.56 * sx, 0.64 * sx, 0.66, 0.70, 'Y2', b)
        span(0.36, 0.54, 0.56 * sx, 0.62 * sx, 0.48, 0.70, 'Y3', b)
        span(0.54, 0.64, 0.56 * sx, 0.60 * sx, 0.58, 0.74, 'Y4', b)
        for y0 in (0.06, 0.20):
            span(y0, y0 + 0.03, 0.64 * sx, 0.65 * sx, 0.40, 0.58, 'Y4', b)
    # neck + head (all 'head' boxes get the chibi scale)
    span(-0.50, -0.14, -0.26, 0.26, 0.79, 0.94, 'Y1', 'head')
    span(-0.70, -0.06, -0.36, 0.36, 0.94, 1.44, 'Y1', 'head')       # skull core
    sym(-0.62, -0.14, 0.36, 0.41, 1.00, 1.38, 'Y1', 'head')          # cheek step
    span(-0.62, -0.14, -0.28, 0.28, 1.44, 1.52, 'Y2', 'head')       # crown
    span(-0.52, -0.24, -0.18, 0.18, 1.52, 1.56, 'Y2', 'head')       # crown cap
    span(-0.40, -0.32, -0.05, 0.05, 1.56, 1.66, 'Y1', 'head')       # tuft
    span(-0.34, -0.24, -0.05, 0.05, 1.66, 1.71, 'Y1', 'head')       # tuft curl
    for sx in (1, -1):   # eyes: dark block + 2 white shines, all standing proud of the face
        span(-0.73, -0.70, 0.11 * sx, 0.27 * sx, 1.18, 1.38, 'EY', 'head')
        span(-0.745, -0.73, 0.18 * sx, 0.24 * sx, 1.29, 1.35, 'WH', 'head')
        span(-0.745, -0.73, 0.13 * sx, 0.16 * sx, 1.21, 1.24, 'WH', 'head')
        span(-0.72, -0.70, 0.27 * sx, 0.34 * sx, 1.04, 1.12, 'PK', 'head')   # blush
    # bill: upper on head, lower on jaw (opens for Quack)
    span(-0.98, -0.70, -0.25, 0.25, 1.07, 1.17, 'OR', 'head')
    span(-0.94, -0.70, -0.18, 0.18, 1.17, 1.21, 'OR', 'head')
    span(-1.02, -0.98, -0.18, 0.18, 1.08, 1.15, 'OR', 'head')
    for sx in (1, -1):
        span(-0.90, -0.86, 0.06 * sx, 0.10 * sx, 1.21, 1.22, 'OD', 'head')
    span(-0.92, -0.70, -0.21, 0.21, 0.99, 1.07, 'OD', 'jaw')
    span(-0.88, -0.72, -0.16, 0.16, 1.07, 1.08, 'MO', 'jaw')
    # legs + webbed feet
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.12, -0.02, 0.17 * sx, 0.27 * sx, 0.06, 0.20, 'OD', b)
        span(-0.30, 0.02, 0.10 * sx, 0.34 * sx, 0.00, 0.06, 'OR', b)
        for dx in (0.08, 0.20, 0.32):
            span(-0.40, -0.30, (dx - 0.04) * sx, (dx + 0.04) * sx, 0.00, 0.06, 'OR', b)


# ---- clips: fn(frame) -> {bone: (rx, ry, rz) world degrees, 'root_loc': (x, y, z) metres} ----
def idle(f):
    ph = TAU * f / 90
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 14 * S(TAU * f / 180)), 'tail': (0, 0, 8 * S(ph * 2)),
            'wing.L': (0, 3 * S(ph), 0), 'wing.R': (0, -3 * S(ph), 0)}


def walk(f):   # waddle: whole-body side roll + yaw, head counter-bob, legs out of phase, tail + wings secondary
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 9 * S(ph), 5 * c), 'body': (3, 0, 0), 'head': (-5 * abs(S(ph)), -6 * S(ph), -4 * c),
            'leg.L': (-26 * S(ph), 0, 0), 'leg.R': (26 * S(ph), 0, 0), 'tail': (8, 0, -18 * S(ph)),
            'wing.L': (0, 10 + 8 * S(2 * ph), 0), 'wing.R': (0, -10 - 8 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.05 * abs(S(ph)))}


def quack(f):   # anticipation -> two snaps -> settle
    if f < 8: a, o = EASE(f / 8), 0
    elif f < 22: a, o = 1, abs(S(TAU * (f - 8) / 14))
    else: a, o = 1 - EASE(min((f - 22) / 8, 1)), 0
    return {'body': (6 * a, 0, 0), 'head': (-14 * a + 10 * o, 0, 0), 'jaw': (28 * o, 0, 0),
            'tail': (-20 * o, 0, 0), 'wing.L': (0, -15 * o, 0), 'wing.R': (0, 15 * o, 0)}


def flap(f):
    w = S(TAU * f / 12)
    return {'wing.L': (0, -55 * (w + 1) / 2, 0), 'wing.R': (0, 55 * (w + 1) / 2, 0), 'body': (-6, 0, 0),
            'head': (4, 0, 0), 'tail': (-12 * w, 0, 0), 'root_loc': (0, 0, 0.06 * (1 + S(TAU * f / 12 - 1)))}


CLIPS = {'Idle': (90, idle), 'Walk': (24, walk), 'Quack': (30, quack), 'Flap': (12, flap)}
PREVIEW = dict(target=(0, -0.2, 0.95), ortho=3.0, shots=[('Quack', 12), ('Flap', 3)], loop='Walk')
