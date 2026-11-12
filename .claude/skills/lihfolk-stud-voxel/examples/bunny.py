# Bunny: cute chibi pet. Signature traits: long upright ears (right tip folded over), cream pom-pom tail,
# big head, big back feet with cream soles, twitchy nose.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'Bunny'
STUDS = 5.0
# honey fur in 4 tones with fixed jobs (C2 tops, C1 main, C3 sides, C4 underside) + cream + pink accents
PALETTE = dict(C1='eeb26a', C2='ffd28e', C3='dc9b52', C4='b47a40', CR='fff0cc', CL='fff9ea',
               EY='231816', IR='8a5428', WH='ffffff', NS='ff7d9c', PK='ffa3b8', PI='ffbccb', DK='5e3d25')
GLOW = set()
HP = (0, -0.25, 0.70)   # head pivot (neck)
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.02, 0.30), (0, 0.02, 0.62), 'root'),
         ('head', HP, (0, -0.25, 1.05), 'body'),
         ('nose', (0, -0.56, 0.84), (0, -0.62, 0.84), 'head'),
         ('tail', (0, 0.34, 0.32), (0, 0.52, 0.34), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'ear.{s}', (0.15 * sx, -0.36, 1.04), (0.15 * sx, -0.36, 1.48), 'head'),
              (f'leg.{s}', (0.12 * sx, -0.31, 0.20), (0.12 * sx, -0.31, 0.0), 'body'),
              (f'hind.{s}', (0.26 * sx, 0.14, 0.30), (0.26 * sx, 0.14, 0.0), 'body')]
HEAD = dict(scale=1.4, pivot=HP, bones=('head', 'nose', 'ear.L', 'ear.R'))


def build(K):
    span, sym = K.span, K.sym
    # body: round sitting loaf, cream belly on the front
    span(-0.28, 0.30, -0.26, 0.26, 0.10, 0.18, 'C4', 'body')        # underside
    span(-0.32, 0.34, -0.32, 0.32, 0.18, 0.56, 'C1', 'body')        # core
    sym(-0.24, 0.28, 0.32, 0.35, 0.24, 0.50, 'C3', 'body')          # side step
    span(-0.26, 0.30, -0.26, 0.26, 0.56, 0.65, 'C1', 'body')        # shoulders
    span(-0.16, 0.24, -0.18, 0.18, 0.65, 0.70, 'C2', 'body')        # back cap
    span(-0.36, -0.32, -0.21, 0.21, 0.20, 0.54, 'CR', 'body')       # belly
    span(-0.38, -0.36, -0.13, 0.13, 0.26, 0.46, 'CR', 'body')
    # front paws: small cream-tipped stubs
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.37, -0.25, 0.06 * sx, 0.17 * sx, 0.04, 0.20, 'C1', b)
        span(-0.40, -0.25, 0.055 * sx, 0.175 * sx, 0.0, 0.04, 'CR', b)
        span(-0.405, -0.40, 0.10 * sx, 0.11 * sx, 0.0, 0.03, 'DK', b)   # toe groove
    # haunches + big back feet (cream soles show on hops)
    for sx, s in K.sides():
        b = f'hind.{s}'
        span(-0.02, 0.32, 0.30 * sx, 0.41 * sx, 0.12, 0.40, 'C1', b)     # thigh
        span(0.02, 0.28, 0.29 * sx, 0.39 * sx, 0.40, 0.46, 'C2', b)      # thigh top
        span(-0.06, -0.02, 0.30 * sx, 0.39 * sx, 0.16, 0.34, 'C3', b)    # thigh front step
        span(0.32, 0.36, 0.30 * sx, 0.39 * sx, 0.16, 0.36, 'C3', b)      # thigh back step
        span(-0.26, 0.34, 0.20 * sx, 0.38 * sx, 0.03, 0.12, 'C1', b)     # foot
        span(-0.26, 0.34, 0.20 * sx, 0.38 * sx, 0.0, 0.03, 'CR', b)      # sole
        span(0.34, 0.36, 0.22 * sx, 0.36 * sx, 0.0, 0.10, 'CR', b)       # heel pad
        span(-0.30, -0.26, 0.21 * sx, 0.37 * sx, 0.0, 0.08, 'CR', b)     # toes
        for dx in (0.26, 0.32):
            span(-0.305, -0.30, (dx - 0.006) * sx, (dx + 0.006) * sx, 0.0, 0.06, 'DK', b)
    # tail: big round stepped pom-pom
    span(0.34, 0.54, -0.16, 0.16, 0.16, 0.52, 'CR', 'tail')
    span(0.36, 0.58, -0.21, 0.21, 0.21, 0.47, 'CR', 'tail')
    span(0.38, 0.54, -0.11, 0.11, 0.52, 0.56, 'CL', 'tail')
    span(0.58, 0.61, -0.13, 0.13, 0.26, 0.42, 'CL', 'tail')
    sym(0.40, 0.54, 0.21, 0.24, 0.26, 0.42, 'CR', 'tail')
    # head (scaled 1.4 around the neck)
    span(-0.40, -0.18, -0.18, 0.18, 0.64, 0.74, 'C1', 'head')       # neck
    span(-0.50, -0.24, -0.20, 0.20, 0.68, 0.72, 'C4', 'head')       # chin underside
    span(-0.56, -0.18, -0.27, 0.27, 0.76, 1.00, 'C1', 'head')       # skull
    span(-0.54, -0.20, -0.23, 0.23, 1.00, 1.04, 'C1', 'head')       # skull top row
    span(-0.54, -0.20, -0.23, 0.23, 0.72, 0.76, 'C1', 'head')       # skull bottom row
    sym(-0.50, -0.22, 0.27, 0.31, 0.78, 0.98, 'C3', 'head')          # fluffy cheeks
    span(-0.50, -0.24, -0.20, 0.20, 1.04, 1.08, 'C2', 'head')       # crown
    span(-0.18, -0.14, -0.21, 0.21, 0.78, 0.98, 'C3', 'head')       # back of head step
    span(-0.60, -0.50, -0.12, 0.12, 0.72, 0.86, 'CR', 'head')       # muzzle
    span(-0.58, -0.56, -0.16, 0.16, 0.74, 0.84, 'CR', 'head')
    span(-0.61, -0.60, -0.005, 0.005, 0.74, 0.81, 'DK', 'head')     # mouth line
    for sx in (1, -1):
        for x, z in ((0.075, 0.80), (0.10, 0.77), (0.10, 0.83)):   # whisker dots
            span(-0.605, -0.60, (x - 0.008) * sx, (x + 0.008) * sx, z - 0.008, z + 0.008, 'DK', 'head')
        # eyes: dark block, brown iris, 2 white shines, proud of the face
        span(-0.58, -0.56, 0.08 * sx, 0.21 * sx, 0.87, 1.00, 'EY', 'head')
        span(-0.585, -0.58, 0.11 * sx, 0.18 * sx, 0.88, 0.94, 'IR', 'head')
        span(-0.59, -0.58, 0.145 * sx, 0.195 * sx, 0.95, 0.99, 'WH', 'head')
        span(-0.59, -0.58, 0.105 * sx, 0.125 * sx, 0.895, 0.915, 'WH', 'head')
        span(-0.575, -0.56, 0.19 * sx, 0.26 * sx, 0.79, 0.84, 'PK', 'head')   # blush
    span(-0.62, -0.60, -0.04, 0.04, 0.82, 0.87, 'NS', 'nose')        # nose
    span(-0.625, -0.62, -0.025, 0.025, 0.85, 0.865, 'WH', 'nose')
    # ears: tall, slightly bulged, rounded tips, pink inside on the front face
    for sx, s in K.sides():
        b = f'ear.{s}'
        top = 1.50 if s == 'L' else 1.34
        span(-0.41, -0.31, 0.09 * sx, 0.21 * sx, 1.04, 1.12, 'C1', b)
        span(-0.41, -0.31, 0.07 * sx, 0.23 * sx, 1.12, top - 0.06, 'C1', b)
        span(-0.415, -0.41, 0.11 * sx, 0.19 * sx, 1.08, top - 0.06, 'PI', b)
        if s == 'L':
            span(-0.41, -0.31, 0.09 * sx, 0.21 * sx, top - 0.06, top, 'C2', b)
            span(-0.40, -0.32, 0.115 * sx, 0.185 * sx, top, top + 0.04, 'C2', b)
    # right ear tip folds over outward
    K.limb((-0.15, -0.36, 1.28), (-0.36, -0.36, 1.12), 0.10, 0.16, 'C2', 'ear.R', extend=0.06)
    K.limb((-0.15, -0.411, 1.27), (-0.33, -0.411, 1.13), 0.01, 0.08, 'PI', 'ear.R')


def idle(f):
    ph = TAU * f / 90
    tw = max(0, S(TAU * f / 30) - 0.6) * 2.5            # nose twitch bursts
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-2 * S(ph + 0.6), 0, 6 * S(TAU * f / 180)),
            'nose': (8 * tw * S(TAU * f / 4), 0, 0),
            'ear.L': (-3 * S(ph), 5 * S(ph + 0.4), 0), 'ear.R': (-3 * S(ph + 0.8), -4 * S(ph + 1.2), 0),
            'tail': (0, 0, 6 * S(ph * 2))}


def hop(f):    # walk loop as hops: crouch -> spring -> land (in place)
    if f < 5: cr, up = EASE(f / 5), 0
    elif f < 17: u = (f - 5) / 12; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    else: u = (f - 17) / 7; cr, up = S(math.pi * u) * 0.8, 0
    return {'body': (6 * cr - 10 * up, 0, 0), 'head': (-5 * cr + 8 * up, 0, 0),
            'leg.L': (-30 * up, 0, 0), 'leg.R': (-30 * up, 0, 0),
            'hind.L': (35 * up - 8 * cr, 0, 0), 'hind.R': (35 * up - 8 * cr, 0, 0),
            'ear.L': (-18 * up + 8 * cr, 0, 0), 'ear.R': (-18 * up + 8 * cr, 0, 0),
            'tail': (-15 * up, 0, 0), 'root_loc': (0, 0, 0.32 * up - 0.05 * cr)}


def big_jump(f):   # deep crouch -> big leap with a twist wiggle -> land + settle
    if f < 12: cr, up = EASE(f / 12), 0
    elif f < 30: u = (f - 12) / 18; cr, up = 1 - EASE(min(u * 3, 1)), S(math.pi * u)
    elif f < 38: cr, up = S(math.pi * (f - 30) / 8) * 0.9, 0
    else: cr, up = 0, 0
    tw = 25 * S(TAU * max(0, f - 12) / 18) * up
    return {'body': (10 * cr - 15 * up, 0, tw), 'head': (-8 * cr + 12 * up, 0, -tw * 0.5),
            'leg.L': (-45 * up + 10 * cr, 0, 0), 'leg.R': (-45 * up + 10 * cr, 0, 0),
            'hind.L': (45 * up - 12 * cr, 0, 0), 'hind.R': (45 * up - 12 * cr, 0, 0),
            'ear.L': (-25 * up + 12 * cr, 12 * up, 0), 'ear.R': (-25 * up + 12 * cr, -12 * up, 0),
            'tail': (-20 * up, 0, 0), 'root_loc': (0, 0, 0.85 * up - 0.10 * cr)}


def ear_wiggle(f):   # happy: ears flop side to side in turn, head tilt
    ph = TAU * f / 10
    t = EASE(min(f / 6, 1)) * EASE(min((30 - f) / 6, 1))
    return {'head': (-3 * t, 10 * t * S(TAU * f / 30), 0),
            'ear.L': (0, 22 * t * S(ph), 0), 'ear.R': (0, 22 * t * S(ph + math.pi), 0),
            'nose': (6 * t * S(ph * 2), 0, 0), 'tail': (0, 0, 12 * t * S(ph))}


CLIPS = {'Idle': (90, idle), 'Hop': (24, hop), 'BigJump': (40, big_jump), 'EarWiggle': (30, ear_wiggle)}
PREVIEW = dict(target=(0, 0.0, 0.92), ortho=2.6, shots=[('BigJump', 21), ('EarWiggle', 4)], loop='Hop')
