# Arctic Fox: cute quadruped. Signature traits: huge fluffy curled tail, big triangle ears, cheek ruff, chest ruff, tiny snout.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'ArcticFox'
STUDS = 5.0
# white fur in 4 tones with fixed jobs (W2 tops/fluff, W1 main, W3 sides, W4 underside) + icy accents
PALETTE = dict(W1='f7fafd', W2='ffffff', W3='e2eaf3', W4='c3d0df', IC='bfe2ff',
               EY='1d2030', IR='4f9dff', WH='ffffff', NS='2a2c3a', PK='ffb0c4', PD='9aa9c0')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.5), (0, 0.05, 0.8), 'root'),
         ('head', (0, -0.40, 0.80), (0, -0.40, 1.2), 'body'),
         ('jaw', (0, -0.78, 0.82), (0, -0.92, 0.80), 'head'),
         ('tail1', (0, 0.45, 0.62), (0, 0.80, 0.66), 'body'),
         ('tail2', (0, 0.80, 0.66), (0, 0.98, 1.00), 'tail1'),
         ('tail3', (0, 0.98, 1.00), (0, 0.98, 1.36), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.21 * sx, -0.55, 1.22), (0.24 * sx, -0.55, 1.50), 'head'),
              (f'leg.{s}', (0.18 * sx, -0.24, 0.34), (0.18 * sx, -0.24, 0.0), 'body'),
              (f'hind.{s}', (0.18 * sx, 0.30, 0.34), (0.18 * sx, 0.30, 0.0), 'body')]
HEAD = dict(scale=1.35, pivot=(0, -0.40, 0.80), bones=('head', 'jaw', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: stepped loaf
    span(-0.30, 0.40, -0.24, 0.24, 0.24, 0.30, 'W4', 'body')        # belly
    span(-0.36, 0.46, -0.32, 0.32, 0.30, 0.70, 'W1', 'body')        # core
    sym(-0.28, 0.38, 0.32, 0.36, 0.36, 0.64, 'W3', 'body')          # side step
    span(-0.30, 0.40, -0.26, 0.26, 0.70, 0.76, 'W2', 'body')        # back
    span(-0.18, 0.30, -0.16, 0.16, 0.76, 0.79, 'W2', 'body')        # back cap
    # chest ruff: fluffy bib stepping forward
    span(-0.46, -0.36, -0.28, 0.28, 0.34, 0.76, 'W2', 'body')
    span(-0.52, -0.46, -0.18, 0.18, 0.40, 0.66, 'W2', 'body')
    span(-0.55, -0.52, -0.08, 0.08, 0.44, 0.58, 'W2', 'body')
    # legs: short, paw wider than leg; front on 'leg', back on 'hind' with a haunch bump
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.32, -0.16), (f'hind.{s}', 0.22, 0.38)):
            span(y0, y1, 0.10 * sx, 0.26 * sx, 0.07, 0.34, 'W1', b)
            span(y0 - 0.04, y1 + 0.02, 0.09 * sx, 0.27 * sx, 0.0, 0.07, 'W2', b)
            for dx in (0.13, 0.18, 0.23):                                   # toe grooves
                span(y0 - 0.05, y0 - 0.04, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.05, 'PD', b)
        span(0.14, 0.44, 0.30 * sx, 0.37 * sx, 0.34, 0.62, 'W3', f'hind.{s}')   # haunch
    # head (scaled 1.35 around the neck)
    span(-0.52, -0.36, -0.20, 0.20, 0.74, 0.86, 'W1', 'head')       # neck
    span(-0.78, -0.34, -0.30, 0.30, 0.80, 1.20, 'W1', 'head')       # skull
    span(-0.72, -0.40, -0.24, 0.24, 1.20, 1.26, 'W2', 'head')       # crown
    sym(-0.70, -0.42, 0.30, 0.36, 0.82, 1.06, 'W2', 'head')          # cheek ruff
    sym(-0.66, -0.50, 0.36, 0.41, 0.82, 0.94, 'W2', 'head')          # cheek tuft
    span(-0.94, -0.78, -0.15, 0.15, 0.84, 0.97, 'W1', 'head')       # snout
    span(-0.92, -0.78, -0.11, 0.11, 0.97, 1.00, 'W2', 'head')       # snout top
    span(-1.04, -0.94, -0.09, 0.09, 0.85, 0.95, 'W1', 'head')       # snout tip (taper = fox, not dog)
    span(-1.07, -1.04, -0.05, 0.05, 0.89, 0.95, 'NS', 'head')       # nose
    span(-0.98, -0.78, -0.10, 0.10, 0.79, 0.84, 'W3', 'jaw')        # lower jaw
    span(-0.94, -0.80, -0.06, 0.06, 0.84, 0.845, 'PK', 'jaw')       # mouth (shows when open)
    for sx in (1, -1):   # eyes: dark block, blue iris, 2 white shines, all proud of the face
        span(-0.80, -0.78, 0.09 * sx, 0.23 * sx, 1.00, 1.15, 'EY', 'head')
        span(-0.805, -0.80, 0.12 * sx, 0.20 * sx, 1.01, 1.07, 'IR', 'head')
        span(-0.81, -0.80, 0.16 * sx, 0.21 * sx, 1.09, 1.13, 'WH', 'head')
        span(-0.81, -0.80, 0.115 * sx, 0.135 * sx, 1.025, 1.045, 'WH', 'head')
        span(-0.795, -0.78, 0.23 * sx, 0.29 * sx, 0.90, 0.96, 'PK', 'head')   # blush
    # ears: stepped triangles, pink inside on the front face
    for sx, s in K.sides():
        b = f'ear.{s}'
        for i, (x0, x1, z0, z1) in enumerate(((0.06, 0.36, 1.22, 1.30), (0.10, 0.36, 1.30, 1.38), (0.15, 0.35, 1.38, 1.45),
                                              (0.20, 0.34, 1.45, 1.51), (0.25, 0.33, 1.51, 1.55))):
            span(-0.60, -0.48, x0 * sx, x1 * sx, z0, z1, 'W2' if i == 4 else 'W1', b)
        for x0, x1, z0, z1 in ((0.12, 0.30, 1.24, 1.32), (0.16, 0.30, 1.32, 1.40), (0.21, 0.30, 1.40, 1.46)):
            span(-0.615, -0.60, x0 * sx, x1 * sx, z0, z1, 'PK', b)
    # tail: the hero piece, 3 fat segments curling up, fluff steps on the sides, icy tip
    span(0.44, 0.80, -0.20, 0.20, 0.46, 0.80, 'W1', 'tail1')          # root, fattening backwards
    sym(0.50, 0.78, 0.20, 0.24, 0.50, 0.76, 'W3', 'tail1')
    span(0.50, 0.78, -0.16, 0.16, 0.80, 0.84, 'W2', 'tail1')
    span(0.78, 1.14, -0.28, 0.28, 0.54, 1.00, 'W1', 'tail2')          # fattest part
    sym(0.82, 1.10, 0.28, 0.32, 0.60, 0.94, 'W3', 'tail2')
    span(1.14, 1.20, -0.20, 0.20, 0.60, 0.94, 'W3', 'tail2')
    span(0.82, 1.10, -0.20, 0.20, 0.50, 0.54, 'W4', 'tail2')
    span(0.86, 1.14, -0.24, 0.24, 1.00, 1.28, 'W2', 'tail3')          # curl up
    sym(0.90, 1.10, 0.24, 0.27, 1.04, 1.24, 'W3', 'tail3')
    span(0.90, 1.10, -0.16, 0.16, 1.28, 1.36, 'IC', 'tail3')          # icy tip
    span(0.94, 1.06, -0.08, 0.08, 1.36, 1.41, 'IC', 'tail3')


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 45) - 0.8) * 5               # quick ear twitch now and then
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 10 * S(TAU * f / 180)),
            'ear.L': (0, -15 * tw, 0), 'ear.R': (0, 4 * S(ph * 2), 0),
            'tail1': (0, 0, 8 * S(ph)), 'tail2': (0, 0, 10 * S(ph - 0.6)), 'tail3': (0, 0, 12 * S(ph - 1.2))}


def walk(f):   # trot: diagonal pairs, body bob, head steady, tail swings late
    ph = TAU * f / 20; c = math.cos(ph)
    a = 28 * S(ph)
    return {'leg.L': (-a, 0, 0), 'hind.R': (-a, 0, 0), 'leg.R': (a, 0, 0), 'hind.L': (a, 0, 0),
            'body': (0, 3 * c, 2 * S(ph)), 'head': (-3 * abs(S(ph)), -3 * c, -2 * S(ph)),
            'ear.L': (6 * abs(c), 0, 0), 'ear.R': (6 * abs(c), 0, 0),
            'tail1': (5, 0, 10 * S(ph - 0.8)), 'tail2': (0, 0, 12 * S(ph - 1.4)), 'tail3': (0, 0, 14 * S(ph - 2.0)),
            'root_loc': (0, 0, 0.04 * abs(S(ph)))}


def pounce(f):   # crouch -> leap up with front paws forward -> land + settle
    if f < 10: cr, up = EASE(f / 10), 0
    elif f < 24: u = (f - 10) / 14; cr, up = 1 - EASE(min(u * 2, 1)), S(math.pi * u)
    elif f < 32: cr, up = S(math.pi * (f - 24) / 8) * 0.7, 0
    else: cr, up = 0, 0
    return {'body': (8 * cr - 12 * up, 0, 0), 'head': (-6 * cr + 10 * up, 0, 0), 'jaw': (12 * up, 0, 0),
            'leg.L': (-40 * up + 10 * cr, 0, 0), 'leg.R': (-40 * up + 10 * cr, 0, 0),
            'hind.L': (30 * up - 10 * cr, 0, 0), 'hind.R': (30 * up - 10 * cr, 0, 0),
            'ear.L': (-15 * cr, 0, 0), 'ear.R': (-15 * cr, 0, 0),
            'tail1': (-20 * up + 10 * cr, 0, 0), 'tail2': (-15 * up, 0, 0), 'tail3': (-10 * up, 0, 0),
            'root_loc': (0, -0.15 * up, 0.5 * up - 0.08 * cr)}


def wag(f):    # happy: fast tail wag, head tilt, ears perk
    ph = TAU * f / 10
    t = EASE(min(f / 6, 1))
    return {'head': (-4 * t, 12 * t, 0), 'ear.L': (-8 * t, 0, 0), 'ear.R': (-8 * t, 0, 0),
            'tail1': (0, 0, 22 * S(ph)), 'tail2': (0, 0, 26 * S(ph - 0.8)), 'tail3': (0, 0, 30 * S(ph - 1.6)),
            'body': (0, 0, 4 * S(ph)), 'root_loc': (0, 0, 0.02 * abs(S(ph)))}


CLIPS = {'Idle': (90, idle), 'Walk': (20, walk), 'Pounce': (40, pounce), 'Wag': (30, wag)}
PREVIEW = dict(target=(0, 0.0, 0.95), ortho=3.4, shots=[('Pounce', 17), ('Wag', 4)], loop='Walk')
