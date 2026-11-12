"""Solve per-material rest contrast gains so no material accidentally owns a calm board.

    python3 -m tools.celestialrithm.foundry.calibrate --set core12 --iters 4

Renders the board up to the rest moment (before the first press), measures each key's salience
lift with the kit's model (tools/hierarchy/hierarchy.py salience_map), and updates
gain *= (median / lift) ** 0.6, clamped to director.GAIN_RANGE. Repeats; writes loudness.json
with the history so every number is traceable. Target: max/median <= 1.8 (hierarchy_pass B).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import director as D
from .board import SETS, Board, schedule
from .optics import linear_to_srgb
from .hierarchy_pass import key_box
from .qa import board_rects

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/hierarchy'))
import hierarchy as HA  # noqa: E402


def rest_lifts(ids, cols, gains, seconds=12, seed=7, size=(1280, 720)):
    b = Board(ids, cols, *size, seed=seed, director=True, gains=gains)
    starts = schedule(len(ids), seconds)
    t_rest = min(s[0] for s in starts) - .5
    img = None
    for i in range(int(t_rest * 60) + 1):
        img, _ = b.render(i / 60, starts)
    rgb = img.astype(float) / 255
    sal = HA.salience_map(rgb)
    rects = board_rects({'size': list(size), 'cols': cols, 'ids': ids})
    lifts = []
    for r in rects:
        m = HA._mask(sal.shape, [key_box(r)])
        lifts.append(float(sal[m].sum() / sal.sum()) / float(m.mean()))
    return np.array(lifts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', default='core12'); ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--iters', type=int, default=4); ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    ids = SETS[a.set]
    prev = D.load_gains()
    gains = {k: 1.0 for k in ids}
    hist = []
    for it in range(a.iters + 1):
        L = rest_lifts(ids, a.cols, gains, seed=a.seed)
        med = float(np.median(L))
        hist.append({'iter': it, 'max_over_median': round(float(L.max() / med), 3), 'min_over_median': round(float(L.min() / med), 3),
                     'lifts': {k: round(float(v), 3) for k, v in zip(ids, L)}, 'gains': {k: round(v, 3) for k, v in gains.items()}})
        print(f"iter {it}: max/median {L.max() / med:.2f}  min/median {L.min() / med:.2f}", flush=True)
        if it == a.iters:
            break
        for k, v in zip(ids, L):
            gains[k] = float(np.clip(gains[k] * (med / v) ** .6, *D.GAIN_RANGE))
    best = min(hist, key=lambda h: h['max_over_median'])
    merged = {**{k: v for k, v in prev.items() if k not in ids}, **best['gains']}
    D.LOUDNESS.write_text(json.dumps({'contrast_gain': merged, 'method': 'calibrate.py: salience lift per key at rest, gain *= (median/lift)^0.6',
                                      'target': 'max/median <= 1.8 (hierarchy_pass B)', 'set': a.set, 'seed': a.seed,
                                      'chosen_iter': best['iter'], 'history': hist}, indent=1))
    print('wrote', D.LOUDNESS.relative_to(ROOT), 'iter', best['iter'], 'max/median', best['max_over_median'])


if __name__ == '__main__':
    main()
