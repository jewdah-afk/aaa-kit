# Red Panda: chibi quadruped. Signature traits: big ringed curled tail, white face mask + tear marks, rounded white-rimmed ears, dark legs.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'RedPanda'
STUDS = 5.0
# rusty fur in 4 tones with fixed jobs (R2 tops, R1 main, R3 sides, R4 dark underside) + near-black legs,
# cream/white face mask, dark tail rings
PALETTE = dict(R1='f27a2a', R2='ffa04a', R3='d2601f', R4='6e2c18', LG='2e1a14', LP='1f110d',
               CW='fffaf0', CR='f2e2c8', TR='a23c16', RD='b4441a', RS='94381a', ER='3a1f18',
               EY='1d1414', IR='a8683a', WH='ffffff', NS='1e1414', PK='ff9fb4', PD='120a08')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.05, 0.5), (0, 0.05, 0.8), 'root'),
         ('head', (0, -0.40, 0.80), (0, -0.40, 1.2), 'body'),
         ('jaw', (0, -0.78, 0.82), (0, -0.92, 0.80), 'head'),
         ('tail1', (0, 0.45, 0.62), (0, 0.80, 0.66), 'body'),
         ('tail2', (0, 0.80, 0.66), (0, 1.00, 1.00), 'tail1'),
         ('tail3', (0, 1.00, 1.00), (0, 1.00, 1.40), 'tail2')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.22 * sx, -0.55, 1.22), (0.26 * sx, -0.55, 1.46), 'head'),
              (f'leg.{s}', (0.18 * sx, -0.24, 0.30), (0.18 * sx, -0.24, 0.0), 'body'),
              (f'hind.{s}', (0.18 * sx, 0.30, 0.30), (0.18 * sx, 0.30, 0.0), 'body')]
HEAD = dict(scale=1.38, pivot=(0, -0.40, 0.80), bones=('head', 'jaw', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: stepped loaf, rusty top, dark red-brown belly
    span(-0.30, 0.40, -0.24, 0.24, 0.24, 0.32, 'R4', 'body')        # belly
    span(-0.36, 0.46, -0.32, 0.32, 0.32, 0.70, 'R1', 'body')        # core
    span(-0.30, 0.40, -0.322, 0.322, 0.32, 0.42, 'R4', 'body')      # dark lower flank band
    sym(-0.28, 0.38, 0.32, 0.36, 0.42, 0.64, 'R3', 'body')          # side step
    span(-0.30, 0.40, -0.26, 0.26, 0.70, 0.76, 'R2', 'body')        # back
    span(-0.18, 0.30, -0.16, 0.16, 0.76, 0.79, 'R2', 'body')        # back cap
    # chest: dark bib (red panda chest is black-brown)
    span(-0.44, -0.36, -0.26, 0.26, 0.30, 0.70, 'R4', 'body')
    span(-0.48, -0.44, -0.16, 0.16, 0.36, 0.60, 'R4', 'body')
    # legs: short, near-black, paw wider than leg
    for sx, s in K.sides():
        for b, y0, y1 in ((f'leg.{s}', -0.32, -0.16), (f'hind.{s}', 0.22, 0.38)):
            span(y0, y1, 0.10 * sx, 0.26 * sx, 0.07, 0.34, 'LG', b)
            span(y0 - 0.04, y1 + 0.02, 0.09 * sx, 0.27 * sx, 0.0, 0.07, 'LP', b)
            for dx in (0.13, 0.18, 0.23):                                   # toe grooves
                span(y0 - 0.05, y0 - 0.04, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.05, 'PD', b)
        span(0.14, 0.44, 0.30 * sx, 0.37 * sx, 0.36, 0.60, 'R3', f'hind.{s}')   # haunch
        span(0.14, 0.44, 0.30 * sx, 0.37 * sx, 0.30, 0.36, 'R4', f'hind.{s}')   # dark haunch base
    # head (scaled around the neck): round, wide
    span(-0.52, -0.36, -0.20, 0.20, 0.74, 0.86, 'R1', 'head')       # neck
    span(-0.78, -0.34, -0.31, 0.31, 0.80, 1.20, 'R1', 'head')       # skull
    span(-0.74, -0.38, -0.25, 0.25, 1.20, 1.26, 'R2', 'head')       # crown
    # puffy white cheeks wrapping the side
    sym(-0.72, -0.48, 0.31, 0.37, 0.82, 1.00, 'CW', 'head')
    sym(-0.66, -0.54, 0.37, 0.41, 0.84, 0.94, 'CW', 'head')
    # face mask on the front face (proud 0.01)
    for sx in (1, -1):
        span(-0.79, -0.78, 0.22 * sx, 0.31 * sx, 0.82, 1.02, 'CW', 'head')     # cheek patch
        span(-0.79, -0.78, 0.09 * sx, 0.21 * sx, 1.16, 1.21, 'CW', 'head')     # eyebrow spot
        span(-0.795, -0.78, 0.16 * sx, 0.22 * sx, 0.84, 1.01, 'TR', 'head')    # tear stripe
    # muzzle: short, white
    span(-0.90, -0.78, -0.16, 0.16, 0.82, 0.98, 'CW', 'head')
    span(-0.88, -0.78, -0.11, 0.11, 0.98, 1.01, 'CW', 'head')       # muzzle top
    span(-0.79, -0.78, -0.06, 0.06, 1.01, 1.17, 'CW', 'head')       # white bridge up the forehead
    span(-0.93, -0.90, -0.06, 0.06, 0.90, 0.97, 'NS', 'head')       # nose
    span(-0.905, -0.90, -0.012, 0.012, 0.85, 0.90, 'NS', 'head')    # philtrum
    span(-0.88, -0.78, -0.11, 0.11, 0.78, 0.82, 'CR', 'jaw')        # lower jaw
    span(-0.86, -0.80, -0.06, 0.06, 0.82, 0.825, 'PK', 'jaw')       # mouth (shows when open)
    for sx in (1, -1):   # eyes: dark block, brown iris, 2 white shines, blush on the white cheek
        span(-0.80, -0.78, 0.08 * sx, 0.20 * sx, 1.01, 1.15, 'EY', 'head')
        span(-0.805, -0.80, 0.10 * sx, 0.17 * sx, 1.02, 1.08, 'IR', 'head')
        span(-0.81, -0.80, 0.14 * sx, 0.19 * sx, 1.09, 1.13, 'WH', 'head')
        span(-0.81, -0.80, 0.095 * sx, 0.115 * sx, 1.03, 1.05, 'WH', 'head')
        span(-0.80, -0.79, 0.25 * sx, 0.30 * sx, 0.92, 0.97, 'PK', 'head')    # blush
    # ears: rounded steps, white rim, dark inside on the front face
    for sx, s in K.sides():
        b = f'ear.{s}'
        span(-0.58, -0.48, 0.10 * sx, 0.36 * sx, 1.20, 1.40, 'R1', b)       # rusty ear
        span(-0.56, -0.50, 0.14 * sx, 0.32 * sx, 1.40, 1.46, 'R1', b)       # rounded top
        span(-0.57, -0.49, 0.36 * sx, 0.39 * sx, 1.22, 1.40, 'CW', b)      # white rim: outer edge
        span(-0.57, -0.49, 0.14 * sx, 0.36 * sx, 1.46, 1.49, 'CW', b)      # white rim: top
        span(-0.57, -0.49, 0.32 * sx, 0.37 * sx, 1.40, 1.46, 'CW', b)      # white rim: corner
        span(-0.59, -0.58, 0.16 * sx, 0.32 * sx, 1.24, 1.40, 'ER', b)      # dark inner

    # tail: the hero piece, oversized, ringed (main / dark alternating), curls up, dark tip
    def ring(y0, y1, z0, z1, w, c, b):
        cs = 'R3' if c == 'R1' else 'RS'
        span(y0, y1, -w, w, z0, z1, c, b)
        sym(y0 + 0.02, y1 - 0.02, w, w + 0.04, z0 + 0.04, z1 - 0.04, cs, b)
        span(y0 + 0.02, y1 - 0.02, -w + 0.06, w - 0.06, z1, z1 + 0.04, 'R2' if c == 'R1' else c, b)

    ring(0.44, 0.58, 0.46, 0.80, 0.20, 'R1', 'tail1')
    ring(0.58, 0.70, 0.46, 0.80, 0.22, 'RD', 'tail1')
    ring(0.70, 0.82, 0.48, 0.84, 0.24, 'R1', 'tail1')
    ring(0.80, 0.94, 0.52, 1.02, 0.30, 'RD', 'tail2')
    ring(0.94, 1.08, 0.52, 1.04, 0.31, 'R1', 'tail2')
    ring(1.08, 1.20, 0.56, 1.00, 0.27, 'RD', 'tail2')
    span(0.84, 1.18, -0.24, 0.24, 1.02, 1.14, 'R1', 'tail3')          # curl up
    sym(0.88, 1.14, 0.24, 0.28, 1.04, 1.12, 'R3', 'tail3')
    span(0.84, 1.18, -0.24, 0.24, 1.14, 1.26, 'RD', 'tail3')
    sym(0.88, 1.14, 0.24, 0.28, 1.16, 1.24, 'RS', 'tail3')
    span(0.88, 1.14, -0.20, 0.20, 1.26, 1.34, 'R1', 'tail3')
    span(0.92, 1.10, -0.14, 0.14, 1.34, 1.40, 'RD', 'tail3')          # dark tip
    span(0.96, 1.06, -0.07, 0.07, 1.40, 1.44, 'R4', 'tail3')


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
