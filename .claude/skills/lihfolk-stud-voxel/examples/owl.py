# Owl: chibi stud-voxel critter (copied from the stud-voxel-creatures duck.py and edited).
# Units: metres, Z up, front = -Y, left = +X. STUDS 5.
import math
S, TAU = math.sin, math.tau
EASE = lambda u: u * u * (3 - 2 * u)

NAME = 'Owl'
STUDS = 5.0
# Brown 4 tones with fixed jobs: B2 tops/caps (light), B1 main, B3 wings/side steps, B4 underside/dark tips.
# CR cream disc + chest, CH chevrons, IR amber iris, EY dark, BK/BD beak, OR/OD feet, PK blush.
PALETTE = dict(B1='c48c52', B2='e6b877', B3='a8733f', B4='7e522d', CR='fbeccf', CH='c08e5e',
               IR='ffd23a', EY='1c1a22', WH='ffffff', BK='ffb52e', BD='c9720f', OR='ff9a1f', OD='cf6a10',
               PK='ff9e9e')
GLOW = set()
BONES = [('root', (0, 0, 0), (0, 0, 0.3), None),
         ('body', (0, 0.0, 0.5), (0, 0.0, 0.85), 'root'),
         ('head', (0, -0.05, 0.95), (0, -0.05, 1.4), 'body'),
         ('tail', (0, 0.40, 0.42), (0, 0.62, 0.34), 'body')]
for s, sx in (('L', 1), ('R', -1)):
    BONES += [(f'wing.{s}', (0.50 * sx, -0.2, 0.86), (0.50 * sx, 0.4, 0.86), 'body'),
              (f'leg.{s}', (0.19 * sx, -0.10, 0.22), (0.19 * sx, -0.10, 0.0), 'root')]
HEAD = dict(scale=1.35, pivot=(0, -0.05, 0.93), bones=('head',))


def build(K):
    span, sym = K.span, K.sym
    # body: upright stepped egg
    span(-0.30, 0.30, -0.32, 0.32, 0.18, 0.26, 'B4', 'body')        # belly plate
    span(-0.40, 0.36, -0.46, 0.46, 0.26, 0.90, 'B1', 'body')        # core
    sym(-0.32, 0.28, 0.46, 0.50, 0.32, 0.84, 'B3', 'body')          # side step
    span(-0.30, 0.32, -0.38, 0.38, 0.90, 0.96, 'B2', 'body')        # shoulders top
    span(0.36, 0.42, -0.34, 0.34, 0.32, 0.84, 'B1', 'body')         # back round
    # cream chest patch + chevron rows
    span(-0.44, -0.40, -0.32, 0.32, 0.30, 0.84, 'CR', 'body')
    span(-0.47, -0.44, -0.22, 0.22, 0.34, 0.74, 'CR', 'body')
    for r, cols in ((0.64, (-0.11, 0.11)), (0.53, (-0.15, 0.0, 0.15)), (0.42, (-0.11, 0.11))):
        for c in cols:
            span(-0.48, -0.47, c - 0.055, c - 0.02, r + 0.02, r + 0.045, 'CH', 'body')
            span(-0.48, -0.47, c - 0.02, c + 0.02, r, r + 0.025, 'CH', 'body')
            span(-0.48, -0.47, c + 0.02, c + 0.055, r + 0.02, r + 0.045, 'CH', 'body')
    # tail fan
    span(0.42, 0.52, -0.24, 0.24, 0.30, 0.52, 'B3', 'tail')
    span(0.52, 0.60, -0.30, 0.30, 0.24, 0.44, 'B1', 'tail')
    span(0.60, 0.66, -0.24, 0.24, 0.22, 0.36, 'B3', 'tail')
    for x in (-0.15, 0.0, 0.15):
        span(0.52, 0.58, x - 0.03, x + 0.03, 0.44, 0.46, 'B2', 'tail')
    # folded wings: light bars, dark tips sweeping back
    for sx, s in K.sides():
        b = f'wing.{s}'
        span(-0.26, 0.36, 0.50 * sx, 0.58 * sx, 0.36, 0.84, 'B3', b)
        span(-0.20, 0.30, 0.50 * sx, 0.58 * sx, 0.84, 0.88, 'B2', b)
        span(0.36, 0.48, 0.50 * sx, 0.57 * sx, 0.36, 0.70, 'B3', b)
        span(0.48, 0.58, 0.50 * sx, 0.55 * sx, 0.38, 0.56, 'B3', b)
        span(-0.20, 0.30, 0.50 * sx, 0.57 * sx, 0.32, 0.36, 'B3', b)
        for z0 in (0.70, 0.58, 0.46):
            span(-0.18, 0.30, 0.58 * sx, 0.59 * sx, z0, z0 + 0.04, 'B2', b)
    # neck + head (scaled 1.35 around the neck)
    span(-0.30, 0.22, -0.30, 0.30, 0.90, 0.98, 'B1', 'head')
    span(-0.40, 0.30, -0.40, 0.40, 0.98, 1.32, 'B1', 'head')        # skull core
    span(-0.40, 0.27, -0.37, 0.37, 1.32, 1.40, 'B1', 'head')        # rounded top, step 1
    span(-0.40, 0.22, -0.33, 0.33, 1.40, 1.44, 'B1', 'head')        # rounded top, step 2
    sym(-0.32, 0.22, 0.40, 0.44, 1.04, 1.32, 'B3', 'head')           # cheek step
    span(-0.30, 0.16, -0.28, 0.28, 1.44, 1.50, 'B2', 'head')        # crown
    span(-0.20, 0.10, -0.16, 0.16, 1.50, 1.53, 'B2', 'head')        # crown cap
    span(0.30, 0.34, -0.30, 0.30, 1.04, 1.32, 'B1', 'head')         # back round
    for sx in (1, -1):   # ear tufts, stepping out and up, dark tip
        span(-0.28, 0.02, 0.18 * sx, 0.38 * sx, 1.32, 1.56, 'B1', 'head')
        span(-0.24, -0.02, 0.26 * sx, 0.42 * sx, 1.56, 1.66, 'B2', 'head')
        span(-0.20, -0.06, 0.33 * sx, 0.44 * sx, 1.66, 1.74, 'B1', 'head')
    # heart facial disc: dark rim, cream disc (two lobes with a notch, point at the beak)
    span(-0.405, -0.40, -0.39, 0.39, 0.98, 1.32, 'B3', 'head')
    span(-0.405, -0.40, -0.36, 0.36, 1.32, 1.40, 'B3', 'head')
    span(-0.405, -0.40, -0.32, 0.32, 1.40, 1.43, 'B3', 'head')
    span(-0.415, -0.405, -0.37, 0.37, 1.04, 1.32, 'CR', 'head')
    span(-0.415, -0.405, -0.34, 0.34, 1.32, 1.38, 'CR', 'head')
    sym(-0.415, -0.405, 0.04, 0.30, 1.38, 1.42, 'CR', 'head')
    span(-0.415, -0.405, -0.28, 0.28, 1.00, 1.04, 'CR', 'head')
    span(-0.415, -0.405, -0.14, 0.14, 0.96, 1.00, 'CR', 'head')
    for sx in (1, -1):   # HUGE eyes: dark rim, amber iris, pupil, 2 shines
        span(-0.425, -0.415, 0.07 * sx, 0.31 * sx, 1.08, 1.36, 'EY', 'head')     # rounded: cross of 2 boxes
        span(-0.425, -0.415, 0.05 * sx, 0.33 * sx, 1.11, 1.33, 'EY', 'head')
        span(-0.435, -0.425, 0.09 * sx, 0.29 * sx, 1.10, 1.34, 'IR', 'head')
        span(-0.435, -0.425, 0.07 * sx, 0.31 * sx, 1.13, 1.31, 'IR', 'head')
        span(-0.445, -0.435, 0.13 * sx, 0.25 * sx, 1.14, 1.30, 'EY', 'head')
        span(-0.445, -0.435, 0.11 * sx, 0.27 * sx, 1.16, 1.28, 'EY', 'head')
        span(-0.455, -0.445, 0.17 * sx, 0.23 * sx, 1.22, 1.28, 'WH', 'head')
        span(-0.455, -0.445, 0.12 * sx, 0.145 * sx, 1.16, 1.185, 'WH', 'head')
        span(-0.425, -0.415, 0.26 * sx, 0.33 * sx, 1.02, 1.065, 'PK', 'head')   # blush
    # hooked beak between the eyes
    span(-0.49, -0.415, -0.055, 0.055, 1.04, 1.16, 'BK', 'head')
    span(-0.52, -0.49, -0.045, 0.045, 1.00, 1.12, 'BK', 'head')
    span(-0.53, -0.50, -0.035, 0.035, 0.97, 1.02, 'BD', 'head')
    # feathered legs + stubby orange feet, 3 toes
    for sx, s in K.sides():
        b = f'leg.{s}'
        span(-0.16, -0.02, 0.12 * sx, 0.26 * sx, 0.07, 0.22, 'B3', b)
        span(-0.16, 0.0, 0.11 * sx, 0.27 * sx, 0.0, 0.07, 'OR', b)
        for dx in (0.12, 0.19, 0.26):
            span(-0.28, -0.16, (dx - 0.03) * sx, (dx + 0.03) * sx, 0.0, 0.06, 'OR', b)
            span(-0.31, -0.28, (dx - 0.02) * sx, (dx + 0.02) * sx, 0.0, 0.04, 'OD', b)


def idle(f):   # breathing + a cute side tilt and back
    ph = TAU * f / 90
    t = EASE(min(f / 14, 1)) if f < 45 else 1 - EASE(min((f - 45) / 14, 1))
    return {'body': (1.5 * S(ph), 0, 0), 'head': (-3 * t, 16 * t, 4 * S(ph)), 'tail': (0, 0, 6 * S(ph * 2)),
            'wing.L': (0, 3 * S(ph), 0), 'wing.R': (0, -3 * S(ph), 0)}


def walk(f):   # waddle hop
    ph = TAU * f / 24; c = math.cos(ph)
    return {'root': (0, 8 * S(ph), 5 * c), 'body': (3, 0, 0), 'head': (-4 * abs(S(ph)), -6 * S(ph), -4 * c),
            'leg.L': (-24 * S(ph), 0, 0), 'leg.R': (24 * S(ph), 0, 0), 'tail': (6, 0, -14 * S(ph)),
            'wing.L': (0, 8 + 6 * S(2 * ph), 0), 'wing.R': (0, -8 - 6 * S(2 * ph), 0),
            'root_loc': (0, 0, 0.07 * abs(S(ph)))}


def flap(f):
    w = S(TAU * f / 12)
    return {'wing.L': (0, -70 * (w + 1) / 2, 0), 'wing.R': (0, 70 * (w + 1) / 2, 0), 'body': (-5, 0, 0),
            'head': (4, 0, 0), 'tail': (-10 * w, 0, 0), 'root_loc': (0, 0, 0.08 * (1 + S(TAU * f / 12 - 1)))}


def head_turn(f):   # swivel 90, hold, back with a tiny overshoot
    if f < 14: a = EASE(f / 14)
    elif f < 34: a = 1
    elif f < 48: a = 1 - EASE((f - 34) / 14) * 1.06
    else: a = -0.06 * (1 - EASE(min((f - 48) / 8, 1)))
    return {'head': (0, 4 * S(math.pi * min(f / 48, 1)), -90 * a), 'body': (0, 0, 6 * a)}


CLIPS = {'Idle': (90, idle), 'Walk': (24, walk), 'Flap': (12, flap), 'HeadTurn': (60, head_turn)}
PREVIEW = dict(target=(0, -0.1, 0.98), ortho=2.9, shots=[('HeadTurn', 24), ('Flap', 3)], loop='Walk')
