#!/usr/bin/env python3
"""Tests for the Celestialrithm material foundry. Run from the repo root:

    python3 tools/celestialrithm/foundry/test_foundry.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.celestialrithm.foundry import board as B  # noqa: E402
from tools.celestialrithm.foundry import fields as fl  # noqa: E402
from tools.celestialrithm.foundry import keycap as kc  # noqa: E402
from tools.celestialrithm.foundry import materials as M  # noqa: E402
from tools.celestialrithm.foundry import optics as op  # noqa: E402

REQUIRED_SPEC = ['id', 'name', 'family', 'method', 'palette', 'bevel', 'ink', 'geometry', 'optics', 'motion',
                 'interaction', 'hierarchy', 'tiers', 'reduced_motion', 'rarity', 'cost']
checks = []


def check(name, ok):
    checks.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name)


def run_frames(mid, n, press=0.0, seed=3, fw=96, fh=44):
    m = M.REGISTRY[mid](fw, fh, seed=seed)
    out = None
    for i in range(n):
        out = m.frame(i / 60, press)
    return out


# --- registry and specs
check('16 materials registered', len(M.REGISTRY) == 16)
check('core 12 + extra 4 are registered ids', all(i in M.REGISTRY for i in M.ORDER_12 + M.ORDER_EXTRA))
for mid, cls in M.REGISTRY.items():
    sp = cls.spec()
    check(f'{mid}: full spec', all(k in sp and sp[k] for k in REQUIRED_SPEC))
    check(f'{mid}: palette has base/highlight/shadow/rim', all(k in sp['palette'] for k in ('base', 'highlight', 'shadow', 'rim')))

# --- per material: determinism, range, animation, interaction
for mid in M.REGISTRY:
    a, ga = run_frames(mid, 4)
    b, gb = run_frames(mid, 4)
    check(f'{mid}: deterministic for a seed', np.array_equal(a, b) and np.array_equal(ga, gb))
    check(f'{mid}: finite, in [0,1], right shape', a.shape == (44, 96, 3) and np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1 and ga.shape == (44, 96))
    late, _ = run_frames(mid, 40)
    check(f'{mid}: animates (t=0.05 vs t=0.65 differ)', np.abs(late - a).mean() > 1e-3)
    pressed, _ = run_frames(mid, 40, press=1.0)
    check(f'{mid}: press changes the frame', np.abs(pressed - late).mean() > 1e-4)

# --- optics sanity
film = op.thin_film(np.array([0.0, 120.0, 300.0]))
check('thin film: zero thickness reflects ~nothing (destructive)', film[0].max() < .05)
check('thin film: 300 nm is coloured (channels differ)', np.ptp(film[2]) > .1)
bb = op.blackbody(np.array([1500.0, 6500.0, 11000.0]))
check('blackbody: 1500 K is red-dominant, 11000 K is blue-dominant', bb[0, 0] > bb[0, 2] and bb[2, 2] > bb[2, 0])
h = np.zeros((64, 64), np.float32)
check('caustics: flat water gives uniform light', np.ptp(op.caustics(h, sigma=0)) < 1e-6)
yy, xx = np.mgrid[0:64, 0:64]
lens = -((xx - 32) ** 2 + (yy - 32) ** 2) / 100.0
c = op.caustics(lens.astype(np.float32), depth=100, sigma=0, wrap=False)
check('caustics: a converging lens concentrates light at the centre', c[28:36, 28:36].mean() > 1.5 * c.mean())
cw = op.caustics((np.sin(xx / 64 * 6.2832) * 2).astype(np.float32), depth=20, sigma=0)
check('caustics: energy conserved (wrap)', abs(cw.sum() - 64 * 64) < 1e-2 * 64 * 64)
lab = op.linear_to_oklab(np.array([[1.0, 1.0, 1.0]], np.float32))
check('OKLab: white L = 1, a = b = 0', abs(lab[0, 0] - 1) < 1e-3 and abs(lab[0, 1]) < 1e-3 and abs(lab[0, 2]) < 1e-3)

# --- simulations
gs = fl.GrayScott(48, 48, seed=1); v0 = gs.v.copy(); gs.step(200)
check('Gray-Scott evolves and stays bounded', np.abs(gs.v - v0).mean() > 1e-3 and gs.v.min() >= -1e-3 and gs.v.max() <= 1.001)
def _div(f):
    return np.abs((np.roll(f.u, -1, 1) - np.roll(f.u, 1, 1) + np.roll(f.v, -1, 0) - np.roll(f.v, 1, 0)) * .5).mean()
sf = fl.StableFluid(32, 24); rng = np.random.default_rng(0)
sf.u = rng.normal(size=(24, 32)).astype(np.float32); sf.v = rng.normal(size=(24, 32)).astype(np.float32)
d0 = _div(sf); sf.step(dt=0.0, iters=60, vort=0.0); d1 = _div(sf)
check(f'stable fluid: pressure projection cuts divergence >= 4x ({d0:.3f} -> {d1:.3f})', d1 * 4 < d0)
ws = fl.WaveSim(40, 40, damp=1.0); ws.drop(20, 20, 3, 1); ws.step(30)
check('wave sim: a still drop spreads outward (centre falls, ring rises)', ws.h[20, 20] < .5 and np.abs(ws.h[20, 30:36]).max() > .02)

# --- keycap: geometry is static, press never moves the face
sh = kc.Shell()
cv1 = np.zeros((300, 400, 3), np.float32); cv2 = cv1.copy()
face = np.full((sh.face_h, sh.face_w, 3), .5, np.float32); g = np.zeros((sh.face_h, sh.face_w), np.float32)
r1 = kc.compose(cv1, 200, 150, sh, face, g, M.Hydroglass.tint(), 0.0, press=0.0)
r2 = kc.compose(cv2, 200, 150, sh, face, g, M.Hydroglass.tint(), 0.0, press=1.0)
check('keycap: face rect identical at rest and pressed (stationary key)', r1 == r2)
ink = cv1[150, 200 - sh.w // 2 + 1]
check('keycap: outer silhouette pixel is near-black ink', ink.max() < .02)
cvc = np.zeros((100, 100, 3), np.float32)
kc.compose(cvc, 10, 95, sh, face, g, M.Hydroglass.tint(), 0.0)
check('keycap: clips safely at the canvas edge', np.isfinite(cvc).all())

# --- timeline
phases = [B.press_curve(t / 100)[1] for t in range(0, 220)]
order = [p for i, p in enumerate(phases) if i == 0 or p != phases[i - 1]]
check('press curve runs anticipation -> activation -> peak -> recovery -> settle -> idle',
      order == ['anticipation', 'activation', 'peak', 'recovery', 'settle', 'idle'])
check('press curve peaks at 1 and rests at 0', max(B.press_curve(t / 100)[0] for t in range(0, 220)) == 1.0 and B.press_curve(5.0)[0] == 0.0)

failed = [n for n, ok in checks if not ok]
print(f'{len(checks) - len(failed)}/{len(checks)} passed')
sys.exit(1 if failed else 0)
