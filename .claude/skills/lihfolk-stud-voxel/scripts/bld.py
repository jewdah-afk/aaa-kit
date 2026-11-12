# Static building helper for the brick pipeline (no rig).
# Author the big shapes in UNITS (1 unit = 2.5 studs) with box()/cut(); each box can carry a surface pattern
# (plank, stone, shingle, log) that is carved at FINE resolution (R bricks per unit, default 3 -> 0.83 studs per brick).
# Small details go in fine bricks with fbox()/fcut() (fine index = unit * R). Coords: x right, y up, z back, front = -z.
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brick_rig


def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
def _c(c): return hx(c) if isinstance(c, str) else np.asarray(c, float)

STROKE = np.array((.03, .03, .04))                                     # black stroke colour
PATS = {'': 0, 'plank': 1, 'stone': 2, 'shingle': 3, 'log': 4}


class Grid:
    def __init__(self, nx, ny, nz, R=3):
        self.R = R; self.n = (nx, ny, nz)
        self.kind = np.zeros(self.n, np.int8); self.col = np.zeros((*self.n, 3)); self.pat = np.zeros(self.n, np.int8)
        self.fine = []                                   # ('box'|'cut', slices, colour, kind) applied after upscaling

    def _sl(self, x0, x1, y0, y1, z0, z1, f=1):
        cx, cz = self.n[0] * f // 2, self.n[2] * f // 2
        return (slice(max(cx + x0, 0), cx + x1), slice(max(y0, 0), y1), slice(max(cz + z0, 0), cz + z1))

    def box(self, x0, x1, y0, y1, z0, z1, c, k=1, pat=''):
        s = self._sl(x0, x1, y0, y1, z0, z1); self.kind[s] = k; self.col[s] = _c(c); self.pat[s] = PATS[pat]

    def cut(self, x0, x1, y0, y1, z0, z1):
        self.kind[self._sl(x0, x1, y0, y1, z0, z1)] = 0

    def fbox(self, x0, x1, y0, y1, z0, z1, c, k=1):
        self.fine.append(('box', self._sl(x0, x1, y0, y1, z0, z1, self.R), _c(c), k))

    def fcut(self, x0, x1, y0, y1, z0, z1):
        self.fine.append(('cut', self._sl(x0, x1, y0, y1, z0, z1, self.R), None, 0))

    def fshape(self, fn, c, k=1):
        """organic shape in fine bricks: fn(x, y, z) -> bool mask, x/z centred, y up (fine units).
        c = colour or fn(x, y, z, mask) -> (N,3) colours for the masked cells (shade leaves by height, bark by row...)."""
        self.fine.append(('shape', fn, c, k))

    def blob(self, cx, cy, cz, rx, ry, rz, c, k=1, lumpy=.18, seed=0):
        """leafy clump / boulder: ellipsoid with a lumpy surface (no smooth sphere)."""
        def fn(x, y, z):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
            n = np.sin(x * .9 + seed) * np.sin(y * .7 + 2 * seed) * np.sin(z * .8 + 3 * seed)
            return d < 1 + lumpy * n
        self.fshape(fn, c, k)

    def trace(self, npz, depth=4, x0=0, y0=0, glow_k=2, stroke=1):
        """extrude a traced reference map (scripts/trace_ref.py) in fine bricks: 1 cell = 1 fine brick, centred on x,
        bottom at y0. Depth |Z| < depth, one brick shallower on silhouette edge cells (bevel); glow cells -> kind glow_k."""
        d = np.load(npz); col, occ, gl = d['col'], d['occ'], d['glow']
        if stroke:                                                         # black stroke: 1-cell ring round the silhouette (and holes)
            pad = lambda a: np.pad(a, ((stroke, stroke), (stroke, stroke)) + ((0, 0),) * (a.ndim - 2))
            col, occ, gl = pad(col), pad(occ), pad(gl)
            ring = occ.copy()
            for _ in range(stroke):
                r2 = ring.copy()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1): r2 |= np.roll(ring, (dy, dx), (0, 1))
                ring = r2
            ring &= ~occ
            col = col.copy(); col[ring] = STROKE; occ = occ | ring
            y0 -= stroke
        H, W = occ.shape
        e = occ.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            e &= np.roll(occ, (dy, dx), (0, 1))
        dep = np.where(e, depth, depth - 1)
        def fn(X, Y, Z):
            i = np.floor(Y - y0).astype(int); j = np.floor(X - x0 + W / 2).astype(int)
            ok = (i >= 0) & (i < H) & (j >= 0) & (j < W)
            ic, jc = np.clip(i, 0, H - 1), np.clip(j, 0, W - 1)
            return ok & occ[ic, jc] & (np.abs(Z) < dep[ic, jc])
        def cf(X, Y, Z):
            i = np.clip(np.floor(Y - y0).astype(int), 0, H - 1); j = np.clip(np.floor(X - x0 + W / 2).astype(int), 0, W - 1)
            return col[i, j]
        self.fshape(fn, cf, 1)
        def gfn(X, Y, Z):
            i = np.floor(Y - y0).astype(int); j = np.floor(X - x0 + W / 2).astype(int)
            ok = (i >= 0) & (i < H) & (j >= 0) & (j < W)
            return ok & gl[np.clip(i, 0, H - 1), np.clip(j, 0, W - 1)] & (np.abs(Z) < depth + .5)
        if gl.any(): self.fshape(gfn, '000000', glow_k)

    def window(self, x0, x1, y0, y1, zf, frame, glow=2, sill=None):
        """front-facing window in fine bricks; zf = fine z of the wall's outer layer. Pane recessed 2, glowing,
        frame 1 proud, cross mullion, sill 2 proud."""
        self.fcut(x0, x1, y0, y1, zf, zf + 2)
        self.fbox(x0, x1, y0, y1, zf + 2, zf + 3, '000000', k=glow)
        for a in ((x0 - 1, x0, y0 - 1, y1 + 1), (x1, x1 + 1, y0 - 1, y1 + 1), (x0 - 1, x1 + 1, y1, y1 + 1)):
            self.fbox(a[0], a[1], a[2], a[3], zf - 1, zf, frame)
        mx = (x0 + x1) // 2; my = (y0 + y1) // 2
        self.fbox(mx, mx + 1, y0, y1, zf + 1, zf + 2, frame); self.fbox(x0, x1, my, my + 1, zf + 1, zf + 2, frame)
        self.fbox(x0 - 1, x1 + 1, y0 - 1, y0, zf - 2, zf, sill if sill is not None else frame)

    def export(self, ID, here, glow=None):
        R = self.R
        kind = self.kind.repeat(R, 0).repeat(R, 1).repeat(R, 2)
        col = self.col.repeat(R, 0).repeat(R, 1).repeat(R, 2)
        pat = self.pat.repeat(R, 0).repeat(R, 1).repeat(R, 2)
        N = kind.shape
        fx, fy, fz = np.meshgrid(np.arange(N[0]), np.arange(N[1]), np.arange(N[2]), indexing='ij')
        mul = np.ones(N)
        row = fy // R
        # plank: dark seam on the bottom brick of every unit row
        mul[(pat == 1) & (fy % R == 0)] = .78
        # stone: running bond, blocks 2 units long x 1 unit high, seams darker, each block +-5% by its position
        bx = (fx + fz + (row % 2) * R) // (2 * R)
        seam = (fy % R == 0) | (((fx + fz + (row % 2) * R) % (2 * R)) == 0)
        mul[pat == 2] *= np.where(seam, .72, 1 + .05 * np.sin(bx * 2.3 + row * 1.7))[pat == 2]
        # shingle: each unit row darkens toward its bottom edge (overlap shadow) + staggered tab seams
        tab = ((fx + fz + (row % 2) * R) % (2 * R)) == 0
        sh = np.choose(np.clip(fy % R, 0, 2), [.72, .9, 1.04])
        mul[pat == 3] *= np.where(tab, .8, sh)[pat == 3]
        # log: rounded look = darker bottom and top brick of each unit row
        mul[(pat == 4) & ((fy % R == 0) | (fy % R == R - 1))] *= .82
        col = col * mul[..., None]
        cxs, czs = N[0] // 2, N[2] // 2
        for op, s, c, k in self.fine:
            if op == 'cut': kind[s] = 0
            elif op == 'box': kind[s] = k; col[s] = c
            else:
                m = s(fx - cxs + .5, fy + .5, fz - czs + .5)
                kind[m] = k
                col[m] = c(fx[m] - cxs + .5, fy[m] + .5, fz[m] - czs + .5) if callable(c) else _c(c)
        y = fy[..., None] / max(N[1], 1)
        col = np.clip(col * (.9 + .18 * y), 0, 1)        # light from above
        brick_rig.S = 2.5 / R; brick_rig.UVD = getattr(self, 'uvd', 16.0)   # default one stud per 2x2 fine bricks; traced weapons set g.uvd
        lo = np.array((-N[0] / 2, 0.0, -N[2] / 2))
        out = os.path.join(here, 'out_' + ID); os.makedirs(os.path.join(out, 'render'), exist_ok=True)
        RIG = [('root', None, (0, 0, 0), (0, N[1] + 2, 0))]
        argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
        brick_rig.export(ID, out, lo, kind, col, RIG, [], glow=glow, pose={}, render='render' in argv)
        print('BL_OK', ID, 'bricks', int((kind > 0).sum()))
