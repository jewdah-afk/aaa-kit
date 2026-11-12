"""Small deterministic NumPy triangle rasterizer for the avatar studies.

Writes a G-buffer (view depth, triangle id, perspective-correct barycentrics) so every shading
attribute is gathered afterwards in one vectorised pass. Also: additive transparent triangles
(depth-tested, no depth write), gaussian sprite splats, jump-flood distance transform, blur.
Offline reference only; the Roblox runtime equivalents are listed in docs/celestialrithm/frontier/avatar.md.
"""
from __future__ import annotations

import numpy as np

F32 = np.float32


class Camera:
    def __init__(self, view, proj, W, H, loc):
        self.view = np.asarray(view, np.float64)
        self.proj = np.asarray(proj, np.float64)
        self.W, self.H = W, H
        self.loc = np.asarray(loc, np.float64)

    def project(self, P):
        """World (N,3) -> screen x, y (pixels, y down) and w (view distance)."""
        P = np.asarray(P, np.float64)
        ph = np.concatenate([P, np.ones((len(P), 1))], 1)
        clip = ph @ self.view.T @ self.proj.T
        w = clip[:, 3]
        sx = (clip[:, 0] / w * .5 + .5) * self.W
        sy = (1 - (clip[:, 1] / w * .5 + .5)) * self.H
        return sx, sy, w

    def rays(self):
        """Per-pixel world ray directions (H, W, 3) through pixel centres."""
        inv = np.linalg.inv(self.proj @ self.view)
        xs = (np.arange(self.W) + .5) / self.W * 2 - 1
        ys = 1 - (np.arange(self.H) + .5) / self.H * 2
        X, Y = np.meshgrid(xs, ys)
        p = np.stack([X, Y, np.ones_like(X), np.ones_like(X)], -1) @ inv.T
        p = p[..., :3] / p[..., 3:]
        d = p - self.loc
        return (d / np.linalg.norm(d, axis=-1, keepdims=True)).astype(F32)


class GBuffer:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.depth = np.full((H, W), np.inf, F32)
        self.tid = np.full((H, W), -1, np.int32)
        self.b1 = np.zeros((H, W), F32)
        self.b2 = np.zeros((H, W), F32)

    def clear(self):
        self.depth.fill(np.inf)
        self.tid.fill(-1)


def _cover(x, y, w, W, H):
    """Yield (ys, xs slices, inside mask, e0, e1, e2 screen barycentrics, depth) for one triangle."""
    x0, x1, x2 = x
    y0, y1, y2 = y
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(area) < 1e-9:
        return None
    minx = max(int(np.floor(min(x))), 0)
    maxx = min(int(np.ceil(max(x))), W - 1)
    miny = max(int(np.floor(min(y))), 0)
    maxy = min(int(np.ceil(max(y))), H - 1)
    if minx > maxx or miny > maxy:
        return None
    X = (np.arange(minx, maxx + 1, dtype=F32) + .5)[None, :]
    Y = (np.arange(miny, maxy + 1, dtype=F32) + .5)[:, None]
    e0 = ((x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)) / area
    e1 = ((x0 - x2) * (Y - y2) - (y0 - y2) * (X - x2)) / area
    e2 = 1 - e0 - e1
    inside = (e0 >= 0) & (e1 >= 0) & (e2 >= 0)
    if not inside.any():
        return None
    iw = e0 / w[0] + e1 / w[1] + e2 / w[2]
    depth = 1 / np.maximum(iw, 1e-9)
    return slice(miny, maxy + 1), slice(minx, maxx + 1), inside, e0, e1, e2, depth, iw, area


def raster_opaque(gb: GBuffer, cam: Camera, V, tris, ids, cull=True):
    """Depth-tested opaque triangles. V (N,3) world verts, tris (T,3) int, ids (T,) written to gb.tid.
    Back faces (screen area > 0 with y-down, i.e. clockwise from the camera) are culled."""
    sx, sy, sw = cam.project(V)
    n = 0
    for k in range(len(tris)):
        a, b, c = tris[k]
        x = (sx[a], sx[b], sx[c]); y = (sy[a], sy[b], sy[c]); w = (sw[a], sw[b], sw[c])
        if min(w) <= 0.05:
            continue
        if cull and ((x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])) > 0:
            continue
        r = _cover(x, y, np.array(w), gb.W, gb.H)
        if r is None:
            continue
        ys, xs, inside, e0, e1, e2, depth, iw, _ = r
        sub = gb.depth[ys, xs]
        upd = inside & (depth < sub)
        if not upd.any():
            continue
        sub[upd] = depth[upd]
        gb.tid[ys, xs][upd] = ids[k]
        gb.b1[ys, xs][upd] = (e1 / w[1] / iw)[upd]
        gb.b2[ys, xs][upd] = (e2 / w[2] / iw)[upd]
        n += 1
    return n


def raster_additive(acc, cam: Camera, V, tris, rgba, zbuf, bias=0.0):
    """Additive transparent triangles, depth-tested against zbuf (no write).
    rgba (N,4) per-vertex linear colour + alpha; accumulates rgb*alpha into acc (H, W, 3)."""
    H, W = acc.shape[:2]
    sx, sy, sw = cam.project(V)
    for k in range(len(tris)):
        a, b, c = tris[k]
        w = np.array((sw[a], sw[b], sw[c]))
        if w.min() <= 0.05:
            continue
        r = _cover((sx[a], sx[b], sx[c]), (sy[a], sy[b], sy[c]), w, W, H)
        if r is None:
            continue
        ys, xs, inside, e0, e1, e2, depth, iw, _ = r
        vis = inside & (depth < zbuf[ys, xs] + bias)
        if not vis.any():
            continue
        p0 = e0 / w[0] / iw; p1 = e1 / w[1] / iw; p2 = e2 / w[2] / iw
        col = p0[..., None] * rgba[a] + p1[..., None] * rgba[b] + p2[..., None] * rgba[c]
        add = col[..., :3] * col[..., 3:4] * vis[..., None]
        acc[ys, xs] += add.astype(F32)


def splat(acc, cx, cy, radius, color, hard=False):
    """Gaussian (or crisp diamond) sprite into acc (H, W, 3) at pixel (cx, cy)."""
    H, W = acc.shape[:2]
    r = int(np.ceil(radius * 2.5)) + 1
    x0, x1 = max(int(cx) - r, 0), min(int(cx) + r + 1, W)
    y0, y1 = max(int(cy) - r, 0), min(int(cy) + r + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    X = np.arange(x0, x1, dtype=F32)[None, :] + .5 - cx
    Y = np.arange(y0, y1, dtype=F32)[:, None] + .5 - cy
    if hard:
        d = (np.abs(X) + np.abs(Y)) / max(radius, 1e-3)
        f = np.clip((1.0 - d) * radius, 0, 1)
    else:
        f = np.exp(-(X * X + Y * Y) / (2 * radius * radius))
    acc[y0:y1, x0:x1] += f[..., None] * np.asarray(color, F32)


def downsample(img, k):
    """Box-filter downsample by integer k (anti-aliasing resolve)."""
    H, W = img.shape[:2]
    sh = (H // k, k, W // k, k) + img.shape[2:]
    return img[:H // k * k, :W // k * k].reshape(sh).mean(axis=(1, 3)).astype(F32)


def gauss_blur(img, sigma):
    """Separable gaussian (explicit kernel, edge clamp). img (H, W[, C])."""
    if sigma <= 0:
        return img
    r = int(np.ceil(sigma * 3))
    k = np.exp(-(np.arange(-r, r + 1) ** 2) / (2 * sigma * sigma)).astype(F32)
    k /= k.sum()
    out = img.astype(F32)
    for ax in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[ax] = (r, r)
        p = np.pad(out, pad, mode='edge')
        n = out.shape[ax]
        acc = np.zeros_like(out)
        for i, kv in enumerate(k):
            acc += kv * np.take(p, np.arange(i, i + n), axis=ax)
        out = acc
    return out


def jump_flood(mask):
    """Exact-ish Euclidean distance (pixels) to the nearest True pixel via jump flooding (Rong & Tan 2006)."""
    H, W = mask.shape
    INF = 1 << 20
    sy = np.where(mask, np.arange(H)[:, None], INF).astype(np.int64)
    sx = np.where(mask, np.arange(W)[None, :], INF).astype(np.int64)
    yy, xx = np.mgrid[0:H, 0:W]
    step = 1 << int(np.ceil(np.log2(max(H, W))))
    steps = []
    while step >= 1:
        steps.append(step)
        step //= 2
    steps += [2, 1]   # JFA+2: two extra passes fix most of the classic errors
    for s in steps:
        best_d = (sy - yy) ** 2 + (sx - xx) ** 2
        best_y, best_x = sy.copy(), sx.copy()
        for dy in (-s, 0, s):
            for dx in (-s, 0, s):
                if dy == 0 and dx == 0:
                    continue
                ny = np.clip(yy + dy, 0, H - 1); nx = np.clip(xx + dx, 0, W - 1)
                cy, cx = sy[ny, nx], sx[ny, nx]
                d = (cy - yy) ** 2 + (cx - xx) ** 2
                better = d < best_d
                best_d = np.where(better, d, best_d)
                best_y = np.where(better, cy, best_y); best_x = np.where(better, cx, best_x)
        sy, sx = best_y, best_x
    return np.sqrt(((sy - yy) ** 2 + (sx - xx) ** 2).astype(np.float64)).astype(F32)
