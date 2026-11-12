"""Field primitives for the Celestialrithm material foundry.

Pure NumPy, deterministic for a given seed. Every function works on float32
arrays shaped (H, W). No per-frame allocation discipline here: this is the
offline reference renderer; the Luau ports in lib/celestialrithm/ carry the
runtime constraints.
"""
from __future__ import annotations

import numpy as np

F32 = np.float32


# ---------------------------------------------------------------- utilities
def grid(w: int, h: int, aspect: bool = True):
    """Pixel-centre coordinates. x in [0, w/h] (aspect) or [0, 1], y in [0, 1]."""
    xs = (np.arange(w, dtype=F32) + .5) / (h if aspect else w)
    ys = (np.arange(h, dtype=F32) + .5) / h
    return np.meshgrid(xs, ys)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return a + (b - a) * t


def box_blur(f: np.ndarray, r: int, axis_wrap: bool = False) -> np.ndarray:
    """Separable box blur via cumulative sums (edge-clamped)."""
    if r <= 0:
        return f
    out = f
    for ax in (0, 1):
        pad = [(0, 0)] * f.ndim
        pad[ax] = (r + 1, r)
        p = np.pad(out, pad, mode='wrap' if axis_wrap else 'edge')
        c = np.cumsum(p, axis=ax, dtype=np.float64)
        n = out.shape[ax]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax)
        lo = np.take(c, np.arange(0, n), axis=ax)
        out = ((hi - lo) / (2 * r + 1)).astype(F32)
    return out


def blur(f: np.ndarray, sigma: float, wrap: bool = False) -> np.ndarray:
    """Three box passes approximate a Gaussian (Wells 1986)."""
    r = max(0, int(round(sigma * 0.85)))
    for _ in range(3):
        f = box_blur(f, r, wrap)
    return f


def resize(f: np.ndarray, w: int, h: int) -> np.ndarray:
    """Bilinear resample of (H, W[, C]) to (h, w[, C])."""
    H, W = f.shape[:2]
    ys = (np.arange(h, dtype=F32) + .5) * H / h - .5
    xs = (np.arange(w, dtype=F32) + .5) * W / w - .5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1); y1 = np.clip(y0 + 1, 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1); x1 = np.clip(x0 + 1, 0, W - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None]; fx = np.clip(xs - x0, 0, 1)[None, :]
    if f.ndim == 3:
        fy = fy[..., None]; fx = fx[..., None]
    a = f[y0][:, x0]; b = f[y0][:, x1]; c = f[y1][:, x0]; d = f[y1][:, x1]
    return ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy).astype(F32)


def bilinear_sample(f: np.ndarray, x: np.ndarray, y: np.ndarray, wrap: bool = True) -> np.ndarray:
    """Sample field f (H, W) at fractional pixel coords x, y."""
    H, W = f.shape
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = (x - x0).astype(F32); fy = (y - y0).astype(F32)
    if wrap:
        x0 %= W; y0 %= H; x1 = (x0 + 1) % W; y1 = (y0 + 1) % H
    else:
        x0 = np.clip(x0, 0, W - 1); y0 = np.clip(y0, 0, H - 1)
        x1 = np.clip(x0 + 1, 0, W - 1); y1 = np.clip(y0 + 1, 0, H - 1)
    return ((f[y0, x0] * (1 - fx) + f[y0, x1] * fx) * (1 - fy)
            + (f[y1, x0] * (1 - fx) + f[y1, x1] * fx) * fy)


def gradient(f: np.ndarray, wrap: bool = False):
    if wrap:
        gx = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) * .5
        gy = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) * .5
        return gx, gy
    gy, gx = np.gradient(f)
    return gx.astype(F32), gy.astype(F32)


# ---------------------------------------------------------------- noise
class Noise:
    """3D gradient (Perlin-style) noise on a permutation table; t is the 3rd axis.

    Using time as a true noise dimension (instead of sliding 2D noise) gives
    evolving, non-translating motion: the core difference from sine-sum fields.
    """

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.perm = np.concatenate([rng.permutation(256)] * 2).astype(np.int32)
        g = rng.normal(size=(256, 3)).astype(F32)
        self.g = g / np.linalg.norm(g, axis=1, keepdims=True)

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def __call__(self, x, y, z=0.0):
        x = np.asarray(x, F32); y = np.asarray(y, F32)
        z = np.broadcast_to(np.asarray(z, F32), x.shape)
        xi = np.floor(x).astype(np.int32); yi = np.floor(y).astype(np.int32); zi = np.floor(z).astype(np.int32)
        xf = x - xi; yf = y - yi; zf = z - zi
        xi &= 255; yi &= 255; zi &= 255
        p, g = self.perm, self.g
        u, v, w = self._fade(xf), self._fade(yf), self._fade(zf)

        def dot(ix, iy, iz, dx, dy, dz):
            h = p[p[p[ix] + iy] + iz]
            gg = g[h]
            return gg[..., 0] * dx + gg[..., 1] * dy + gg[..., 2] * dz

        x1 = (xi + 1) & 255; y1 = (yi + 1) & 255; z1 = (zi + 1) & 255
        n000 = dot(xi, yi, zi, xf, yf, zf); n100 = dot(x1, yi, zi, xf - 1, yf, zf)
        n010 = dot(xi, y1, zi, xf, yf - 1, zf); n110 = dot(x1, y1, zi, xf - 1, yf - 1, zf)
        n001 = dot(xi, yi, z1, xf, yf, zf - 1); n101 = dot(x1, yi, z1, xf - 1, yf, zf - 1)
        n011 = dot(xi, y1, z1, xf, yf - 1, zf - 1); n111 = dot(x1, y1, z1, xf - 1, yf - 1, zf - 1)
        nx00 = mix(n000, n100, u); nx10 = mix(n010, n110, u)
        nx01 = mix(n001, n101, u); nx11 = mix(n011, n111, u)
        return (mix(mix(nx00, nx10, v), mix(nx01, nx11, v), w) * 1.6).astype(F32)

    def fbm(self, x, y, z=0.0, octaves=5, lac=2.0, gain=.5):
        a, f, s, norm = 1.0, 1.0, 0.0, 0.0
        for i in range(octaves):
            s = s + a * self(x * f + 17.3 * i, y * f - 9.1 * i, z * (1 + .35 * i))
            norm += a; a *= gain; f *= lac
        return (s / norm).astype(F32)

    def ridged(self, x, y, z=0.0, octaves=5, lac=2.1, gain=.55):
        """Ridged multifractal: sharp bright filaments (plasma, lightning-like veins)."""
        a, f, s, norm, prev = 1.0, 1.0, 0.0, 0.0, 1.0
        for i in range(octaves):
            n = 1 - np.abs(self(x * f + 5.7 * i, y * f + 3.3 * i, z * (1 + .4 * i)))
            n = n * n * prev
            prev = np.clip(n * 1.6, 0, 1)
            s = s + a * n; norm += a; a *= gain; f *= lac
        return (s / norm).astype(F32)

    def warp(self, x, y, z=0.0, amount=1.0, octaves=4):
        """Two-level domain warp (Quilez): f(p + a*g(p + a*h(p)))."""
        qx = self.fbm(x, y, z, octaves); qy = self.fbm(x + 5.2, y + 1.3, z, octaves)
        rx = self.fbm(x + amount * qx + 1.7, y + amount * qy + 9.2, z * 1.2, octaves)
        ry = self.fbm(x + amount * qx + 8.3, y + amount * qy + 2.8, z * 1.2, octaves)
        return self.fbm(x + amount * rx, y + amount * ry, z, octaves), qx, qy, rx, ry

    def curl(self, x, y, z=0.0, eps=.01, octaves=3):
        """Divergence-free 2D velocity from the curl of a scalar potential (Bridson 2007)."""
        n1 = self.fbm(x, y + eps, z, octaves); n2 = self.fbm(x, y - eps, z, octaves)
        n3 = self.fbm(x + eps, y, z, octaves); n4 = self.fbm(x - eps, y, z, octaves)
        return (n1 - n2) / (2 * eps), -(n3 - n4) / (2 * eps)


# ---------------------------------------------------------------- Voronoi
def voronoi(x, y, seed=0, t=0.0, jitter=.85, wander=.25):
    """Worley F1, F2, cell id and nearest-point offset. Points wander on circles over time."""
    xi = np.floor(x).astype(np.int64); yi = np.floor(y).astype(np.int64)
    f1 = np.full(x.shape, 9.0, F32); f2 = np.full(x.shape, 9.0, F32)
    cid = np.zeros(x.shape, np.int64)
    dx1 = np.zeros(x.shape, F32); dy1 = np.zeros(x.shape, F32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx = xi + ox; cy = yi + oy
            h = (cx * 374761393 + cy * 668265263 + (seed % 65536) * 2147483647) & 0x7fffffff
            h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
            r1 = (h & 0xffff) / 65535.0; r2 = ((h >> 16) & 0x7fff) / 32767.0
            ph = r1 * 6.2832 + t * (0.6 + r2)
            px = cx + .5 + jitter * (r1 - .5) + wander * np.cos(ph)
            py = cy + .5 + jitter * (r2 - .5) + wander * np.sin(ph * 1.3)
            ddx = px - x; ddy = py - y
            d = np.sqrt(ddx * ddx + ddy * ddy).astype(F32)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            f1 = np.where(closer, d, f1)
            cid = np.where(closer, h, cid)
            dx1 = np.where(closer, ddx, dx1); dy1 = np.where(closer, ddy, dy1)
    return f1, f2, cid, dx1, dy1


def hash01(i):
    """Integer hash -> [0, 1)."""
    i = np.asarray(i, np.int64)
    i = ((i ^ 61) ^ (i >> 16)) * 9 & 0xffffffff
    i = (i ^ (i >> 4)) * 0x27d4eb2d & 0xffffffff
    i = i ^ (i >> 15)
    return ((i & 0xffffff) / float(0x1000000)).astype(F32)


# ---------------------------------------------------------------- simulations
class WaveSim:
    """2D damped wave equation on a grid (verlet). Drives water heights and press ripples."""

    def __init__(self, w, h, c=.42, damp=.996, seed=0):
        self.h = np.zeros((h, w), F32); self.p = np.zeros((h, w), F32)
        self.c2 = c * c; self.damp = damp
        self.rng = np.random.default_rng(seed)

    def drop(self, x, y, r, amp):
        H, W = self.h.shape
        yy, xx = np.mgrid[0:H, 0:W]
        bump = amp * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (r * r)).astype(F32)
        self.h += bump; self.p += bump          # displacement only, zero initial velocity

    def step(self, n=1):
        for _ in range(n):
            h = self.h
            lap = (np.roll(h, 1, 0) + np.roll(h, -1, 0) + np.roll(h, 1, 1) + np.roll(h, -1, 1) - 4 * h)
            nh = (2 * h - self.p + self.c2 * lap) * self.damp
            self.p, self.h = h, nh.astype(F32)
        return self.h


class GrayScott:
    """Gray-Scott reaction-diffusion (Pearson 1993 parameter map). Periodic boundary."""

    def __init__(self, w, h, f=.037, k=.06, seed=0):
        self.rng = np.random.default_rng(seed)
        self.u = np.ones((h, w), F32); self.v = np.zeros((h, w), F32)
        self._seed_spots(int(w * h / 300) + 8)
        self.f, self.k = f, k

    def _seed_spots(self, n):
        h, w = self.u.shape
        for _ in range(n):
            x, y = self.rng.integers(0, w - 6), self.rng.integers(0, h - 6)
            self.u[y:y + 6, x:x + 6] = .5; self.v[y:y + 6, x:x + 6] = .5
        self.v += self.rng.random((h, w), dtype=F32) * .02

    @staticmethod
    def _lap(a):
        return (.2 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
                + .05 * (np.roll(np.roll(a, 1, 0), 1, 1) + np.roll(np.roll(a, 1, 0), -1, 1)
                         + np.roll(np.roll(a, -1, 0), 1, 1) + np.roll(np.roll(a, -1, 0), -1, 1)) - a)

    def step(self, n=8, f=None, k=None):
        f = self.f if f is None else f; k = self.k if k is None else k
        u, v = self.u, self.v
        for _ in range(n):
            uvv = u * v * v
            u = u + (1.0 * self._lap(u) - uvv + f * (1 - u))
            v = v + (.5 * self._lap(v) + uvv - (f + k) * v)
        self.u, self.v = u.astype(F32), v.astype(F32)
        if self.v.max() < 1e-3:                       # pattern died out (small grids): re-nucleate
            self._seed_spots(int(self.u.size / 300) + 8)
        return self.v


class StableFluid:
    """Stam 1999 stable fluids: semi-Lagrangian advection + Jacobi pressure projection.

    Periodic domain, dye in 3 channels. Vorticity confinement keeps small swirls alive.
    """

    def __init__(self, w, h, seed=0):
        self.w, self.h = w, h
        self.u = np.zeros((h, w), F32); self.v = np.zeros((h, w), F32)
        self.dye = np.zeros((h, w, 3), F32)
        self.X, self.Y = np.meshgrid(np.arange(w, dtype=F32), np.arange(h, dtype=F32))

    def splat(self, x, y, fx, fy, color, r=4.0):
        g = np.exp(-((self.X - x) ** 2 + (self.Y - y) ** 2) / (r * r)).astype(F32)
        self.u += fx * g; self.v += fy * g
        self.dye += g[..., None] * np.asarray(color, F32)[None, None, :]

    def _advect(self, f, dt):
        x = self.X - dt * self.u; y = self.Y - dt * self.v
        if f.ndim == 3:
            return np.stack([bilinear_sample(f[..., c], x, y) for c in range(f.shape[2])], -1)
        return bilinear_sample(f, x, y)

    def step(self, dt=1.0, iters=20, vort=.25, fade=.995):
        u, v = self.u, self.v
        # vorticity confinement
        curl = (np.roll(v, -1, 1) - np.roll(v, 1, 1) - np.roll(u, -1, 0) + np.roll(u, 1, 0)) * .5
        ac = np.abs(curl)
        gx = (np.roll(ac, -1, 1) - np.roll(ac, 1, 1)) * .5; gy = (np.roll(ac, -1, 0) - np.roll(ac, 1, 0)) * .5
        n = np.sqrt(gx * gx + gy * gy) + 1e-5
        u = u + vort * (gy / n) * curl; v = v - vort * (gx / n) * curl
        self.u, self.v = u.astype(F32), v.astype(F32)
        self.u, self.v = self._advect(self.u, dt), self._advect(self.v, dt)
        div = (np.roll(self.u, -1, 1) - np.roll(self.u, 1, 1) + np.roll(self.v, -1, 0) - np.roll(self.v, 1, 0)) * .5
        # Poisson solve with the stencil that matches central-difference div/grad
        # (div(grad p) = (p[i+2] - 2p[i] + p[i-2]) / 4 per axis), so the projection
        # removes the divergence we measure instead of leaving a checkerboard mode.
        p = np.zeros_like(div)
        for _ in range(iters):
            p = (np.roll(p, 2, 0) + np.roll(p, -2, 0) + np.roll(p, 2, 1) + np.roll(p, -2, 1) - 4 * div) * .25
        self.u -= (np.roll(p, -1, 1) - np.roll(p, 1, 1)) * .5
        self.v -= (np.roll(p, -1, 0) - np.roll(p, 1, 0)) * .5
        self.dye = self._advect(self.dye, dt) * fade
        return self.dye


# ---------------------------------------------------------------- lightning
def lightning_path(rng, a, b, depth=7, disp=.28, branch_p=.35, out=None, level=0):
    """Midpoint-displacement bolt with random branches. Returns list of (x0,y0,x1,y1,level)."""
    if out is None:
        out = []
    a = np.asarray(a, F32); b = np.asarray(b, F32)
    if depth == 0:
        out.append((a[0], a[1], b[0], b[1], level))
        return out
    mid = (a + b) / 2
    d = b - a
    nrm = np.array([-d[1], d[0]], F32)
    mid = mid + nrm * rng.normal() * disp
    lightning_path(rng, a, mid, depth - 1, disp * .55, branch_p, out, level)
    lightning_path(rng, mid, b, depth - 1, disp * .55, branch_p, out, level)
    if level < 2 and depth > 3 and rng.random() < branch_p:
        ang = rng.normal() * .7
        c, s = np.cos(ang), np.sin(ang)
        rot = np.array([[c, -s], [s, c]], F32)
        end = mid + rot @ (d * .5 * rng.uniform(.5, .9))
        lightning_path(rng, mid, end, depth - 2, disp * .5, branch_p * .6, out, level + 1)
    return out


def segment_distance(x, y, segs):
    """Min distance from every pixel to a set of segments, plus the level of the nearest one."""
    d = np.full(x.shape, 1e9, F32); lv = np.zeros(x.shape, np.int32)
    for (x0, y0, x1, y1, level) in segs:
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy + 1e-9
        t = np.clip(((x - x0) * dx + (y - y0) * dy) / L, 0, 1)
        px = x0 + t * dx - x; py = y0 + t * dy - y
        dd = np.sqrt(px * px + py * py)
        closer = dd < d
        d = np.where(closer, dd, d); lv = np.where(closer, level, lv)
    return d, lv
