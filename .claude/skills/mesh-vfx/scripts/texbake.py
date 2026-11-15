"""Procedural VFX texture baker (numpy): the node chains from the skill, baked to grayscale-alpha PNGs that tile.
  flame     : UV -> Mapping (x1, y4.5) -> Noise (scale 6.5, 8 octaves, rough 0.65) added into Voronoi distance-to-edge (scale 8)
              -> ColorRamp b-spline black 0.18 / white 0.42           (organic anime flame tongues, scrolls along v)
  streaks   : Wave bands on X, distortion 12, 10 octaves -> ColorRamp constant at 0.68   (shockwave speed streaks)
  flipbook  : 16 frames of the flame with the noise W advanced, packed 4x4
All periodic (lattice wraps), so left/right and top/bottom edges match.  python3 texbake.py flame out.png --size 512"""
import argparse, math
import numpy as np
from PIL import Image

def _lattice(rng, n): return rng.random((n, n))
def pnoise(x, y, period, rng_grid):
    """Periodic value noise: lattice size = period, wraps at the borders."""
    xi = np.floor(x).astype(int); yi = np.floor(y).astype(int); xf = x - xi; yf = y - yi
    u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf)
    g = rng_grid; P = period
    a = g[xi % P, yi % P]; b = g[(xi + 1) % P, yi % P]; c = g[xi % P, (yi + 1) % P]; d = g[(xi + 1) % P, (yi + 1) % P]
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v

def fbm(x, y, base, octaves, rough, seed):
    rng = np.random.default_rng(seed); total = np.zeros_like(x); amp = 1.0; norm = 0.0
    for o in range(octaves):
        p = base * 2 ** o
        total += amp * pnoise(x * p, y * p, p, _lattice(rng, p)); norm += amp; amp *= rough
    return total / norm

def voronoi_edge(x, y, cells, seed):
    """Periodic Voronoi distance-to-edge (F2 - F1), cells x cells feature points, wraps."""
    rng = np.random.default_rng(seed); pts = rng.random((cells, cells, 2))
    X = x * cells; Y = y * cells; xi = np.floor(X).astype(int); yi = np.floor(Y).astype(int)
    d1 = np.full(x.shape, 9.0); d2 = np.full(x.shape, 9.0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx = xi + dx; cy = yi + dy
            fp = pts[cx % cells, cy % cells]
            d = np.hypot(cx + fp[..., 0] - X, cy + fp[..., 1] - Y)
            nd2 = np.where(d < d1, d1, np.minimum(d2, d)); d1 = np.minimum(d1, d); d2 = nd2
    return (d2 - d1)

def ramp_bspline(v, lo, hi):
    t = np.clip((v - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)

def fbm2(x, y, bx, by, octaves, rough, seed):
    """Anisotropic periodic fBm: bx lattice cells along x, by along y (long tongues when bx < by)."""
    rng = np.random.default_rng(seed); total = np.zeros_like(x); amp = 1.0; norm = 0.0
    for o in range(octaves):
        px, py = bx * 2 ** o, by * 2 ** o; g = rng.random((px, py))
        X = x * px; Y = y * py; xi = np.floor(X).astype(int); yi = np.floor(Y).astype(int); xf = X - xi; yf = Y - yi
        u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf)
        a = g[xi % px, yi % py]; b = g[(xi + 1) % px, yi % py]; c = g[xi % px, (yi + 1) % py]; d = g[(xi + 1) % px, (yi + 1) % py]
        total += amp * (a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v); norm += amp; amp *= rough
    return total / norm

def flame(size=512, w=0.0, seed=7):
    """Long flame tongues along u (the slash length): anisotropic fBm, domain-warped, ridged, then a soft ramp."""
    s = np.linspace(0, 1, size, endpoint=False); x, y = np.meshgrid(s, s)
    wx = fbm2((x + w) % 1, y, 2, 4, 4, 0.55, seed + 3)
    n = fbm2((x + (wx - 0.5) * 0.25 + w) % 1, (y + (wx - 0.5) * 0.15) % 1, 3, 12, 5, 0.6, seed)
    ridge = 1 - np.abs(2 * n - 1)
    return (ramp_bspline(ridge ** 5 * (0.5 + n), 0.25, 0.75) * 255).astype(np.uint8)

def _old_flame(size=512, w=0.0, seed=7):
    s = np.linspace(0, 1, size, endpoint=False); x, y = np.meshgrid(s, s)
    # Mapping scale (1, 4.5): stretch along v so tongues are long; keep periodic by using integer lattice periods
    n = fbm(x + w * 0.37, y * 4.5 / 4.5 + w * 0.11, 6, 5, 0.65, seed)
    warped_x = (x + (n - 0.5) * 0.35) % 1.0; warped_y = (y + (n - 0.5) * 0.35) % 1.0
    e = voronoi_edge(warped_x, warped_y, 8, seed + 1)
    v = e / e.max()
    a = ramp_bspline(v * (0.6 + 0.8 * n), 0.18, 0.42)
    return (a * 255).astype(np.uint8)

def streaks(size=512, seed=11):
    s = np.linspace(0, 1, size, endpoint=False); x, y = np.meshgrid(s, s)
    d = fbm(x, y, 4, 6, 0.6, seed)
    bands = 0.5 + 0.5 * np.sin(2 * math.pi * (x * 6 + d * 12 / (2 * math.pi)))  # Wave bands along X, distortion 12
    return np.where(bands > 0.68, 255, 0).astype(np.uint8)

def to_png(alpha, path):
    rgba = np.dstack([np.full_like(alpha, 255)] * 3 + [alpha]); Image.fromarray(rgba, 'RGBA').save(path)

def flipbook(path, frames=16, size=256, seed=7):
    n = int(math.sqrt(frames)); sheet = np.zeros((n * size, n * size), np.uint8)
    for k in range(frames):
        f = flame(size, w=k / frames * 2.0, seed=seed); r, c = divmod(k, n)
        sheet[r * size:(r + 1) * size, c * size:(c + 1) * size] = f
    to_png(sheet, path)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('kind', choices=['flame', 'streaks', 'flipbook']); ap.add_argument('out'); ap.add_argument('--size', type=int, default=512)
    a = ap.parse_args()
    if a.kind == 'flame': to_png(flame(a.size), a.out)
    elif a.kind == 'streaks': to_png(streaks(a.size), a.out)
    else: flipbook(a.out, 16, a.size // 4 if a.size >= 256 else 64)
    print('wrote', a.out)
