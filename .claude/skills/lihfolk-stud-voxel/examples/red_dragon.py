# Red Dragon pet: chunky quadruped. Signature traits: big bat wings with gold trim, cream horns + centre crest horn,
# open fanged roar mouth, gold belly plates, back spikes, long tail with a diamond tip.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'RedDragon'
STUDS = 5.0
# red in 4 tones with fixed jobs (R2 tops, R1 main, R3 sides, R4 underside/dark) + gold belly/trim, bone horns/claws
PALETTE = dict(R1='c63a2b', R2='dc5236', R3='a02a26', R4='6e1a1f', DK='3d1416',
               G1='ffd27e', G2='f0b456', BN='f2e4cc', PK='f07aa0', EY='1d1418', YE='ffe23a', WH='ffffff')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.5), (0, 0.05, 0.8), 'root'),
         ('head', (0, -0.42, 0.86), (0, -0.42, 1.3), 'body'),
         ('jaw', (0, -0.70, 0.86), (0, -0.98, 0.84), 'head'),
         ('tail1', (0, 0.45, 0.55), (0, 0.80, 0.48), 'body'),
         ('tail2', (0, 0.80, 0.48), (0, 1.08, 0.42), 'tail1'),
         ('tail3', (0, 1.08, 0.42), (0, 1.40, 0.38), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.26 * sx, -0.05, 0.80), (0.70 * sx, 0.05, 1.20), 'body'),
              (f'wtip.{s}', (0.70 * sx, 0.05, 1.20), (1.05 * sx, 0.10, 1.10), f'wing.{s}'),
              (f'leg.{s}', (0.22 * sx, -0.24, 0.36), (0.22 * sx, -0.24, 0.0), 'body'),
              (f'hind.{s}', (0.22 * sx, 0.30, 0.36), (0.22 * sx, 0.30, 0.0), 'body')]
HEAD = dict(scale=1.3, pivot=(0, -0.42, 0.86), bones=('head', 'jaw'))


def build(K):
    span, sym, spike = K.span, K.sym, K.spike
    # body: big stepped barrel, gold chest/belly plates
    span(-0.30, 0.42, -0.26, 0.26, 0.24, 0.30, 'R4', 'body')         # underside
    span(-0.38, 0.48, -0.34, 0.34, 0.30, 0.74, 'R1', 'body')         # core
    sym(-0.30, 0.40, 0.34, 0.39, 0.36, 0.68, 'R3', 'body')           # side step
    span(-0.32, 0.42, -0.28, 0.28, 0.74, 0.80, 'R2', 'body')         # back
    span(-0.20, 0.32, -0.16, 0.16, 0.80, 0.83, 'R2', 'body')         # back cap
    for i, z0 in enumerate((0.34, 0.44, 0.54, 0.64)):                # chest plates, stepping forward with height
        span(-0.46 - 0.02 * i, -0.38, -0.22 + 0.02 * i, 0.22 - 0.02 * i, z0, z0 + 0.09, 'G1' if i % 2 else 'G2', 'body')
    for y0 in (-0.24, -0.06, 0.12, 0.30):                            # belly plates
        span(y0, y0 + 0.15, -0.20, 0.20, 0.235, 0.245, 'G1', 'body')
    for i, y in enumerate((-0.22, -0.04, 0.14, 0.32)):               # back spikes (dark)
        spike((0, y, 0.82), (0, 0.4, 1), 0.16 - 0.015 * i, 0.10, 'R4', 'DK', 'body')
    # legs: thick, big paws with cream claws
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.34, -0.14), (f'hind.{s}', 0.20, 0.40)):
            span(y0 - 0.03, y1 + 0.03, 0.10 * sx, 0.34 * sx, 0.08, 0.40, 'R1', b)
            sym_x = 0.32 * sx
            span(y0 + 0.02, y1 - 0.02, sym_x, sym_x + 0.03 * sx, 0.12, 0.34, 'R3', b)
            span(y0 - 0.07, y1 + 0.05, 0.08 * sx, 0.36 * sx, 0.0, 0.08, 'R3', b)
            for dx in (0.14, 0.22, 0.30):                                 # claws
                span(y0 - 0.12, y0 - 0.07, (dx - 0.03) * sx, (dx + 0.03) * sx, 0.0, 0.06, 'BN', b)
        span(0.12, 0.48, 0.34 * sx, 0.42 * sx, 0.34, 0.64, 'R3', f'hind.{s}')   # haunch
        span(-0.30, -0.08, 0.34 * sx, 0.40 * sx, 0.40, 0.66, 'R3', f'leg.{s}')  # shoulder
    # head (scaled 1.3 around the neck): blocky skull, square snout, open roaring jaw
    span(-0.54, -0.36, -0.20, 0.20, 0.76, 0.92, 'R1', 'head')        # neck
    span(-0.76, -0.38, -0.28, 0.28, 0.88, 1.22, 'R1', 'head')        # skull
    span(-0.72, -0.42, -0.22, 0.22, 1.22, 1.27, 'R2', 'head')        # crown
    sym(-0.70, -0.44, 0.28, 0.33, 0.90, 1.12, 'R3', 'head')          # cheeks
    span(-1.02, -0.76, -0.17, 0.17, 0.98, 1.14, 'R1', 'head')        # snout
    span(-1.00, -0.76, -0.13, 0.13, 1.14, 1.18, 'R2', 'head')        # snout ridge
    sym(-1.03, -1.01, 0.06, 0.11, 1.08, 1.12, 'DK', 'head')          # nostrils
    span(-0.98, -0.76, -0.14, 0.14, 0.94, 0.98, 'PK', 'head')        # palate
    for sx in (1, -1):                                               # upper fangs
        span(-1.00, -0.96, 0.10 * sx, 0.14 * sx, 0.88, 0.98, 'BN', 'head')
        span(-0.90, -0.86, 0.12 * sx, 0.15 * sx, 0.91, 0.98, 'BN', 'head')
    span(-0.98, -0.72, -0.15, 0.15, 0.80, 0.86, 'R3', 'jaw')         # lower jaw
    span(-0.94, -0.74, -0.11, 0.11, 0.86, 0.87, 'PK', 'jaw')         # tongue
    span(-0.72, -0.56, -0.18, 0.18, 0.80, 0.90, 'G1', 'jaw')         # throat plate
    for sx in (1, -1):
        span(-0.97, -0.93, 0.09 * sx, 0.13 * sx, 0.86, 0.93, 'BN', 'jaw')   # lower fangs
        # angry eyes: dark block, yellow iris, shine, heavy brow stepping down to the snout
        span(-0.78, -0.76, 0.08 * sx, 0.24 * sx, 1.04, 1.15, 'EY', 'head')
        span(-0.785, -0.78, 0.11 * sx, 0.21 * sx, 1.05, 1.11, 'YE', 'head')
        span(-0.79, -0.785, 0.17 * sx, 0.20 * sx, 1.08, 1.105, 'WH', 'head')
        span(-0.80, -0.74, 0.06 * sx, 0.27 * sx, 1.15, 1.19, 'R4', 'head')   # brow
        span(-0.81, -0.76, 0.05 * sx, 0.12 * sx, 1.13, 1.16, 'R4', 'head')
        # horns: cream, out then up and back
        spike((0.20 * sx, -0.52, 1.24), (0.55 * sx, 0.35, 1), 0.30, 0.13, 'BN', 'BN', 'head')
        sym(-0.66, -0.50, 0.33, 0.37, 0.94, 1.04, 'R2', 'head') if sx > 0 else None   # ear fins
    spike((0, -0.58, 1.26), (0, 0.15, 1), 0.36, 0.12, 'R3', 'R4', 'head')   # centre crest horn
    # wings: arm bone + finger membrane, crimson inside, gold trailing edge
    for sx, s in K.sides():
        w, t = f'wing.{s}', f'wtip.{s}'
        span(-0.06, 0.04, 0.26 * sx, 0.72 * sx, 1.14, 1.24, 'R1', w)     # arm
        span(-0.02, 0.02, 0.26 * sx, 0.70 * sx, 0.78, 1.14, 'R4', w)     # inner membrane
        span(-0.02, 0.02, 0.40 * sx, 0.70 * sx, 0.70, 0.78, 'R4', w)
        span(-0.02, 0.02, 0.50 * sx, 0.70 * sx, 0.64, 0.70, 'G2', w)     # gold edge
        span(-0.02, 0.02, 0.30 * sx, 0.50 * sx, 0.72, 0.78, 'G2', w)
        span(-0.03, 0.03, 0.70 * sx, 1.08 * sx, 1.18, 1.32, 'R1', t)     # top bone up to the claw
        span(-0.03, 0.03, 1.02 * sx, 1.10 * sx, 1.32, 1.40, 'BN', t)     # wing claw
        span(-0.02, 0.02, 0.70 * sx, 1.04 * sx, 0.84, 1.18, 'R4', t)     # outer membrane
        span(-0.02, 0.02, 0.70 * sx, 0.94 * sx, 0.74, 0.84, 'R4', t)
        span(-0.02, 0.02, 0.94 * sx, 1.06 * sx, 0.76, 0.84, 'G2', t)     # gold scallops
        span(-0.02, 0.02, 0.70 * sx, 0.90 * sx, 0.66, 0.74, 'G2', t)
        span(-0.02, 0.02, 1.04 * sx, 1.10 * sx, 0.84, 1.18, 'G2', t)
    # tail: 3 tapering segments with gold underside and spikes, diamond tip
    for b, y0, y1, w, z0, z1 in (('tail1', 0.46, 0.80, 0.22, 0.40, 0.66), ('tail2', 0.80, 1.08, 0.17, 0.36, 0.56),
                                 ('tail3', 1.08, 1.30, 0.12, 0.33, 0.49)):
        span(y0, y1, -w, w, z0, z1, 'R1', b)
        span(y0, y1, -w * 0.6, w * 0.6, z0 - 0.03, z0, 'G2', b)
        spike((0, (y0 + y1) / 2, z1), (0, 0.4, 1), 0.12, 0.08, 'R4', 'DK', b)
    for i, (h, d) in enumerate(((0.06, 0.06), (0.14, 0.06), (0.20, 0.06), (0.14, 0.06), (0.06, 0.05))):   # diamond
        span(1.30 + 0.06 * i, 1.36 + 0.06 * i, -0.03, 0.03, 0.39 - h, 0.39 + h, 'R3', 'tail3')
        span(1.30 + 0.06 * i, 1.36 + 0.06 * i, -0.07, 0.07, 0.39 - h * 0.5, 0.39 + h * 0.5, 'R1', 'tail3')


def idle(f):
    ph = TAU * f / 90
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 8 * S(TAU * f / 180)), 'jaw': (3 + 3 * S(ph), 0, 0),
            'wing.L': (0, 6 * S(ph), 0), 'wing.R': (0, -6 * S(ph), 0),
            'wtip.L': (0, 8 * S(ph - 0.5), 0), 'wtip.R': (0, -8 * S(ph - 0.5), 0),
            'tail1': (0, 0, 8 * S(ph)), 'tail2': (0, 0, 10 * S(ph - 0.6)), 'tail3': (0, 0, 12 * S(ph - 1.2))}


def walk(f):   # stomp trot: diagonal pairs, wings bob, tail swings late
    ph = TAU * f / 22; c = math.cos(ph)
    a = 26 * S(ph)
    return {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
            'body': (0, 3 * c, 2 * S(ph)), 'head': (-3 * abs(S(ph)), -3 * c, -2 * S(ph)),
            'wing.L': (0, 8 * abs(c), 0), 'wing.R': (0, -8 * abs(c), 0),
            'tail1': (0, 0, 10 * S(ph - 0.8)), 'tail2': (0, 0, 12 * S(ph - 1.4)), 'tail3': (0, 0, 14 * S(ph - 2.0)),
            'root_loc': (0, 0, 0.04 * abs(S(ph)))}


def flap(f):   # hop up with big wing flaps, settle
    ph = TAU * f / 12
    up = S(math.pi * min(f / 36, 1))
    fl = 35 * S(ph)
    return {'wing.L': (0, fl, 0), 'wing.R': (0, -fl, 0), 'wtip.L': (0, fl * 0.7, 0), 'wtip.R': (0, -fl * 0.7, 0),
            'body': (-8 * up, 0, 0), 'head': (6 * up, 0, 0), 'jaw': (6 * up, 0, 0),
            'leg.L': (-20 * up, 0, 0), 'leg.R': (-20 * up, 0, 0), 'hind.L': (20 * up, 0, 0), 'hind.R': (20 * up, 0, 0),
            'tail1': (-12 * up, 0, 0), 'tail2': (-8 * up, 0, 0), 'root_loc': (0, 0, 0.45 * up)}


def roar(f):   # rear back, jaw wide, wings spread, settle
    t = EASE(min(f / 8, 1)) * (1 - EASE(max(0, (f - 30) / 10)))
    sh = 2 * S(TAU * f / 4) * t
    return {'body': (-6 * t, 0, sh), 'head': (-14 * t, 0, sh), 'jaw': (28 * t, 0, 0),
            'wing.L': (0, -22 * t, 0), 'wing.R': (0, 22 * t, 0), 'wtip.L': (0, -15 * t, 0), 'wtip.R': (0, 15 * t, 0),
            'tail1': (-10 * t, 0, 0), 'tail2': (-10 * t, 0, 0), 'tail3': (-10 * t, 0, 0)}


CLIPS = {'Idle': (90, idle), 'Walk': (22, walk), 'Flap': (36, flap), 'Roar': (40, roar)}
PREVIEW = dict(target=(0, 0.2, 0.9), ortho=3.8, shots=[('Flap', 9), ('Roar', 15)], loop='Walk')
