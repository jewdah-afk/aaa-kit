# Axolotl: chibi pastel pet. Signature traits: 3 pairs of big feathery magenta gills, wide flat head with a big smile,
# long flat tail with a fin ridge top and bottom, short splayed legs with 4 tiny toes.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'Axolotl'
STUDS = 5.0
# pink skin in 4 tones with fixed jobs (P2 tops, P1 main, P3 sides, P4 underside) + gills / fin / face accents
PALETTE = dict(P1='ffb6cb', P2='ffd6e3', P3='f79ab6', P4='e57c9f', FN='ffc9da',
               GM='ff3f8e', GL='ff86bb', GD='d41f6c', TO='e0849f',
               EY='2b1d2c', WH='ffffff', MO='7d2846', BL='ff7aa3')
GLOW = set()
GILLS = (('gill1', 0.48, (0.45, 0.30, 0.85)),   # top frond: mostly up
         ('gill2', 0.40, (0.85, 0.32, 0.35)),   # middle: out
         ('gill3', 0.32, (0.85, 0.25, -0.20)))  # low: out and a little down
GLEN = 0.33
BONES = [('root', (0, 0, 0), (0, 0, 0.2), None),
         ('body', (0, 0.0, 0.28), (0, 0.0, 0.5), 'root'),
         ('head', (0, -0.36, 0.34), (0, -0.36, 0.6), 'body'),
         ('tail1', (0, 0.40, 0.30), (0, 0.80, 0.30), 'body'),
         ('tail2', (0, 0.80, 0.30), (0, 1.06, 0.31), 'tail1'),
         ('tail3', (0, 1.06, 0.31), (0, 1.34, 0.32), 'tail2')]


def _unit(v):
    n = math.sqrt(sum(a * a for a in v)); return tuple(a / n for a in v)


def gill_base(sx, z): return (0.29 * sx, -0.44, z)


for _s, _sx in (('L', 1), ('R', -1)):
    for _g, _z, _d in GILLS:
        _u = _unit((_d[0] * _sx, _d[1], _d[2])); _b = gill_base(_sx, _z)
        BONES.append((f'{_g}.{_s}', _b, tuple(_b[i] + _u[i] * GLEN for i in range(3)), 'head'))
    BONES += [(f'leg.{_s}', (0.24 * _sx, -0.22, 0.20), (0.24 * _sx, -0.22, 0.0), 'body'),
              (f'hind.{_s}', (0.24 * _sx, 0.30, 0.20), (0.24 * _sx, 0.30, 0.0), 'body')]
HEAD = dict(scale=1.4, pivot=(0, -0.36, 0.34),
            bones=('head',) + tuple(f'{g}.{s}' for g, _, _ in GILLS for s in 'LR'))


def build(K):
    span, sym = K.span, K.sym
    # body: low stepped loaf
    span(-0.30, 0.36, -0.20, 0.20, 0.07, 0.14, 'P4', 'body')        # belly
    span(-0.38, 0.42, -0.26, 0.26, 0.14, 0.42, 'P1', 'body')        # core
    sym(-0.32, 0.36, 0.26, 0.30, 0.18, 0.38, 'P3', 'body')          # side step
    span(-0.32, 0.38, -0.20, 0.20, 0.42, 0.47, 'P2', 'body')        # back
    span(0.02, 0.42, -0.035, 0.035, 0.47, 0.51, 'FN', 'body')      # dorsal fin ridge starts on the back
    # legs: short stubby, splayed out; 4 tiny toes poking forward
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.28, -0.15), (f'hind.{s}', 0.24, 0.37)):
            span(y0, y1, 0.22 * sx, 0.36 * sx, 0.04, 0.22, 'P1', b)       # leg
            span(y0 + 0.02, y1 - 0.02, 0.24 * sx, 0.34 * sx, 0.22, 0.24, 'P2', b)   # top of the leg
            span(y0 - 0.02, y1 + 0.01, 0.26 * sx, 0.42 * sx, 0.0, 0.05, 'P3', b)    # foot
            for dx in (0.275, 0.315, 0.355, 0.395):                          # 4 toes
                span(y0 - 0.06, y0 - 0.02, (dx - 0.014) * sx, (dx + 0.014) * sx, 0.0, 0.035, 'TO', b)
    # head (scaled 1.4 around the neck): wide, flat, rounded with steps
    span(-0.44, -0.34, -0.22, 0.22, 0.18, 0.44, 'P1', 'head')       # neck
    span(-0.76, -0.40, -0.30, 0.30, 0.20, 0.50, 'P1', 'head')       # skull
    span(-0.72, -0.44, -0.24, 0.24, 0.50, 0.54, 'P2', 'head')       # crown
    sym(-0.70, -0.44, 0.30, 0.33, 0.24, 0.46, 'P3', 'head')          # cheek side step
    span(-0.72, -0.42, -0.24, 0.24, 0.17, 0.20, 'P4', 'head')       # chin underside
    span(-0.80, -0.76, -0.26, 0.26, 0.23, 0.47, 'P1', 'head')       # front plate (rounded snout)
    span(-0.79, -0.76, -0.20, 0.20, 0.47, 0.50, 'P2', 'head')       # snout top step
    span(-0.79, -0.76, -0.20, 0.20, 0.20, 0.23, 'P4', 'head')       # snout bottom step
    # face on the front plate (y -0.80): wide smile, small eyes with 2 shines, blush
    span(-0.805, -0.80, -0.17, 0.17, 0.28, 0.30, 'MO', 'head')      # smile line
    sym(-0.805, -0.80, 0.17, 0.21, 0.30, 0.32, 'MO', 'head')         # upturned corners
    sym(-0.805, -0.80, 0.21, 0.23, 0.32, 0.34, 'MO', 'head')
    for sx in (1, -1):
        span(-0.81, -0.80, 0.09 * sx, 0.19 * sx, 0.35, 0.45, 'EY', 'head')
        span(-0.815, -0.81, 0.15 * sx, 0.18 * sx, 0.415, 0.44, 'WH', 'head')
        span(-0.815, -0.81, 0.115 * sx, 0.13 * sx, 0.375, 0.39, 'WH', 'head')
        span(-0.805, -0.80, 0.19 * sx, 0.25 * sx, 0.36, 0.40, 'BL', 'head')   # blush
    # gills: 3 fronds a side, magenta stalk with stepped feathery paddles, dark tip
    for sx, s in K.sides():
        for g, z, d in GILLS:
            b = f'{g}.{s}'; a = gill_base(sx, z); u = _unit((d[0] * sx, d[1], d[2]))
            p = lambda t, a=a, u=u: tuple(a[i] + u[i] * GLEN * t for i in range(3))
            K.limb(p(-0.08), p(1.0), 0.06, 0.06, 'GM', b)
            for t, w, k in ((0.26, 0.15, 'GL'), (0.44, 0.21, 'GL'), (0.62, 0.22, 'GL'), (0.80, 0.17, 'GL'), (0.94, 0.11, 'GM')):
                K.limb(p(t - 0.07), p(t + 0.05), w, w * 0.55, k, b)        # stepped feathery fringe round the stalk
            K.limb(p(0.98), p(1.12), 0.08, 0.05, 'GD', b)                  # tip
    # tail: long, flat (narrow x, tall z), fin ridge top and bottom
    span(0.40, 0.80, -0.17, 0.17, 0.16, 0.42, 'P1', 'tail1')
    span(0.42, 0.80, -0.12, 0.12, 0.42, 0.45, 'P2', 'tail1')
    span(0.42, 0.80, -0.035, 0.035, 0.45, 0.50, 'FN', 'tail1')
    span(0.56, 0.80, -0.035, 0.035, 0.08, 0.16, 'FN', 'tail1')
    span(0.80, 1.06, -0.12, 0.12, 0.20, 0.40, 'P1', 'tail2')
    span(0.80, 1.06, -0.04, 0.04, 0.40, 0.51, 'FN', 'tail2')
    span(0.80, 1.06, -0.04, 0.04, 0.10, 0.20, 'FN', 'tail2')
    span(1.06, 1.32, -0.08, 0.08, 0.24, 0.38, 'P1', 'tail3')
    span(1.06, 1.30, -0.035, 0.035, 0.38, 0.50, 'FN', 'tail3')
    span(1.06, 1.28, -0.035, 0.035, 0.14, 0.24, 'FN', 'tail3')
    span(1.32, 1.42, -0.03, 0.03, 0.20, 0.44, 'FN', 'tail3')          # tail tip fin


def gills(rot_l):   # rot_l(i) -> (rx, ry, rz) for left gill i; right mirrored (ry, rz flip)
    p = {}
    for i, (g, _, _) in enumerate(GILLS):
        rx, ry, rz = rot_l(i)
        p[f'{g}.L'] = (rx, ry, rz); p[f'{g}.R'] = (rx, -ry, -rz)
    return p


def idle(f):
    ph = TAU * f / 90
    p = {'body': (1.2 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 6 * S(TAU * f / 180)),
         'tail1': (0, 0, 6 * S(ph)), 'tail2': (0, 0, 8 * S(ph - 0.6)), 'tail3': (0, 0, 10 * S(ph - 1.2))}
    p.update(gills(lambda i: (0, -10 * S(TAU * f / 45 - 0.9 * i), 6 * S(TAU * f / 45 - 0.9 * i + 1))))
    return p


def walk(f):   # crawl: diagonal pairs, body S-sway, head counter-turns, tail lags
    ph = TAU * f / 24; c = math.cos(ph); a = 26 * S(ph)
    p = {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
         'body': (0, 2 * c, 6 * S(ph)), 'head': (0, -2 * c, -7 * S(ph)),
         'tail1': (0, 0, -10 * S(ph - 0.6)), 'tail2': (0, 0, -12 * S(ph - 1.2)), 'tail3': (0, 0, -14 * S(ph - 1.8)),
         'root_loc': (0, 0, 0.025 * abs(S(ph)))}
    p.update(gills(lambda i: (0, -8 * c, 8 * S(ph - 0.5 * i))))
    return p


def swim(f):   # S-wave down the body and tail, legs tucked back, gills streamlined
    ph = TAU * f / 30; t = EASE(max(0, min(f / 6, 1, (40 - f) / 6)))
    p = {'head': (0, 0, -12 * S(ph + 0.9) * t), 'body': (0, 0, 14 * S(ph) * t),
         'tail1': (0, 0, -24 * S(ph - 0.9) * t), 'tail2': (0, 0, -32 * S(ph - 1.8) * t), 'tail3': (0, 0, -38 * S(ph - 2.7) * t),
         'root_loc': (0, 0, 0.06 * t + 0.02 * S(2 * ph) * t)}
    for s in 'LR':
        p[f'leg.{s}'] = (-60 * t, 0, 0); p[f'hind.{s}'] = (-60 * t, 0, 0)
    p.update(gills(lambda i: (0, 6 * t, (22 + 6 * S(ph - 0.7 * i)) * t)))
    return p


def happy(f):  # gills flare wide + bounce, head tilt
    t = EASE(max(0, min(f / 6, 1, (36 - f) / 6))); ph = TAU * f / 12
    b = abs(S(ph))
    p = {'head': (-6 * t, 10 * t * S(TAU * f / 36), 0), 'body': (-3 * b * t, 0, 0),
         'tail1': (-8 * b * t, 0, 14 * S(ph) * t), 'tail2': (0, 0, 18 * S(ph - 0.8) * t), 'tail3': (0, 0, 22 * S(ph - 1.6) * t),
         'root_loc': (0, 0, 0.14 * b * t)}
    for s in 'LR':
        p[f'leg.{s}'] = (12 * b * t, 0, 0); p[f'hind.{s}'] = (-12 * b * t, 0, 0)
    p.update(gills(lambda i: (0, (-30 + 10 * i) * t - 10 * b * t, -24 * t)))
    return p


CLIPS = {'Idle': (90, idle), 'Walk': (24, walk), 'Swim': (40, swim), 'Happy': (36, happy)}
PREVIEW = dict(target=(0, 0.20, 0.45), ortho=3.2, shots=[('Swim', 10), ('Happy', 9)], loop='Walk')
