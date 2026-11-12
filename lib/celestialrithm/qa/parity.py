#!/usr/bin/env python3
"""Statistical parity: Luau runtime materials vs the Python foundry reference.

Renders each material in Python (tools/celestialrithm/foundry) and in Luau (lune, via
dump_materials.luau) at the same size, seed and frame sequence, then compares the final frame:

  * mean OKLab (L, a, b) and mean sRGB bytes
  * OKLab-L standard deviation (contrast)
  * a 16-bin OKLab-L histogram, as total-variation distance (0 = identical, 1 = disjoint)

Exact pixel equality is NOT expected: the gradient-noise permutation tables and the drop RNG
differ (Worley cells and hash01 are bit-exact ports, noise is not). Tolerances below are what
"the same material" means here; they are honest bounds from the measured runs, not tuned to
whatever passes. Writes side-by-side PNGs (Luau left, Python right) to qa/out/.

Usage: python3 lib/celestialrithm/qa/parity.py [--w 240 --h 112 --frames 30 --tier high --press 0]
Exit code 1 if any material is outside tolerance.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'celestialrithm'))

from foundry import materials as M  # noqa: E402
from foundry import optics as op  # noqa: E402

IDS = ['hydroglass', 'solar_plasma', 'crystal_ice', 'molten_core']

# Tolerances (absolute differences of the statistic).
TOL = {
    'L': 0.05,        # mean OKLab lightness (0..1)
    'ab': 0.03,       # mean OKLab a and b
    'Lstd': 0.05,     # OKLab-L standard deviation
    'hist_tv': 0.30,  # total-variation distance of 16-bin L histograms
}


def oklab_from_bytes(rgb8: np.ndarray) -> np.ndarray:
    lin = op.srgb_to_linear(rgb8.astype(np.float32) / 255.0)
    return op.linear_to_oklab(lin)


def stats(rgb8: np.ndarray) -> dict:
    lab = oklab_from_bytes(rgb8).reshape(-1, 3)
    L = lab[:, 0]
    hist, _ = np.histogram(np.clip(L, 0, 1), bins=16, range=(0, 1))
    return {
        'rgb': rgb8.reshape(-1, 3).mean(0).round(1).tolist(),
        'L': float(L.mean()), 'a': float(lab[:, 1].mean()), 'b': float(lab[:, 2].mean()),
        'Lstd': float(L.std()), 'hist': (hist / hist.sum()).tolist(),
    }


def render_python(mid: str, w: int, h: int, frames: int, fps: float, press: float, seed: int, tier: str) -> np.ndarray:
    m = M.REGISTRY[mid](w, h, seed, tier)
    rgb = None
    for f in range(frames + 1):
        rgb, _ = m.frame(f / fps, press)
    return np.clip(op.linear_to_srgb(rgb) * 255 + .5, 0, 255).astype(np.uint8)


def run_lune(w: int, h: int, frames: int, fps: float, press: float, tier: str, seed: int) -> None:
    lune = shutil.which('lune') or os.path.expanduser('~/.local/bin/lune')
    subprocess.run([lune, 'run', 'dump_materials.luau', str(w), str(h), str(frames), str(fps), str(press), tier, str(seed)],
                   cwd=HERE, check=True, stdout=subprocess.DEVNULL)


def load_lune(mid: str, w: int, h: int, tier: str) -> np.ndarray:
    raw = np.fromfile(os.path.join(HERE, 'out', f'{mid}_{w}x{h}_{tier}.rgba'), np.uint8)
    rgba = raw.reshape(h, w, 4)
    assert (rgba[..., 3] == 255).all(), f'{mid}: alpha not 255'
    return rgba[..., :3]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--w', type=int, default=240)
    ap.add_argument('--h', type=int, default=112)
    ap.add_argument('--frames', type=int, default=30)
    ap.add_argument('--fps', type=float, default=30)
    ap.add_argument('--press', type=float, default=0.0)
    ap.add_argument('--tier', default='high')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--json', help='write results here')
    a = ap.parse_args()

    run_lune(a.w, a.h, a.frames, a.fps, a.press, a.tier, a.seed)
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    results, failed = {}, 0
    print(f'parity {a.w}x{a.h} tier={a.tier} t={a.frames / a.fps:.2f}s press={a.press}')
    print(f'{"material":14} {"dL":>7} {"da":>7} {"db":>7} {"dLstd":>7} {"histTV":>7}  luau rgb / python rgb')
    for mid in IDS:
        lu = load_lune(mid, a.w, a.h, a.tier)
        py = render_python(mid, a.w, a.h, a.frames, a.fps, a.press, a.seed, a.tier)
        sl, sp = stats(lu), stats(py)
        d = {
            'dL': abs(sl['L'] - sp['L']), 'da': abs(sl['a'] - sp['a']), 'db': abs(sl['b'] - sp['b']),
            'dLstd': abs(sl['Lstd'] - sp['Lstd']),
            'histTV': 0.5 * float(np.abs(np.array(sl['hist']) - np.array(sp['hist'])).sum()),
        }
        ok = (d['dL'] <= TOL['L'] and d['da'] <= TOL['ab'] and d['db'] <= TOL['ab']
              and d['dLstd'] <= TOL['Lstd'] and d['histTV'] <= TOL['hist_tv'])
        failed += 0 if ok else 1
        results[mid] = {'ok': ok, 'diff': d, 'luau': sl, 'python': sp}
        print(f'{mid:14} {d["dL"]:7.4f} {d["da"]:7.4f} {d["db"]:7.4f} {d["dLstd"]:7.4f} {d["histTV"]:7.4f}  '
              f'{sl["rgb"]} / {sp["rgb"]}  {"ok" if ok else "FAIL"}')
        side = np.concatenate([lu, np.zeros((a.h, 4, 3), np.uint8), py], 1)
        Image.fromarray(side).save(os.path.join(HERE, 'out', f'{mid}_{a.tier}_luau_vs_python.png'), optimize=True)
    print(f'tolerances: {TOL}')
    print(f'@@PARITY {failed} failed')
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump({'args': vars(a), 'tol': TOL, 'results': results}, fh, indent=1)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
