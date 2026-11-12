"""Stud voxelizer + greedy mesher (pure NumPy, deterministic).

voxelize(): column ray-parity inside test for one closed triangle mesh (works for any watertight
mesh, not just boxes). Run it per closed part and OR the grids, so overlapping parts don't break parity.
greedy_quads(): merges coplanar exposed voxel faces that share a colour key into rectangles
(Lysenko-style greedy meshing), per axis and direction.
"""
from __future__ import annotations

import numpy as np


def voxelize(tri, origin, s, dims):
    """tri (T,3,3) world verts of ONE closed mesh; grid origin (3,), voxel size s, dims (nx,ny,nz).
    Returns bool (nx,ny,nz): True where the voxel centre is inside the mesh."""
    nx, ny, nz = dims
    occ = np.zeros(dims, bool)
    eps = 1.37e-4 * s   # irrational-ish nudge so column centres never sit exactly on an edge
    cx = origin[0] + (np.arange(nx) + .5) * s + eps
    cy = origin[1] + (np.arange(ny) + .5) * s + eps * 0.71
    hits = {}
    for t in tri:
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = t
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue   # edge-on to the column direction: never crossed by a ray
        i0 = np.searchsorted(cx, min(x0, x1, x2)); i1 = np.searchsorted(cx, max(x0, x1, x2))
        j0 = np.searchsorted(cy, min(y0, y1, y2)); j1 = np.searchsorted(cy, max(y0, y1, y2))
        if i0 >= i1 or j0 >= j1:
            continue
        X = cx[i0:i1][:, None]; Y = cy[j0:j1][None, :]
        e0 = ((x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)) / area
        e1 = ((x0 - x2) * (Y - y2) - (y0 - y2) * (X - x2)) / area
        e2 = 1 - e0 - e1
        ins = (e0 >= 0) & (e1 >= 0) & (e2 >= 0)
        zs = e0 * z0 + e1 * z1 + e2 * z2
        for a, b in zip(*np.nonzero(ins)):
            hits.setdefault((i0 + a, j0 + b), []).append(zs[a, b])
    cz = origin[2] + (np.arange(nz) + .5) * s
    for (i, j), zl in hits.items():
        zl = sorted(zl)
        for k in range(0, len(zl) - 1, 2):
            occ[i, j, (cz > zl[k]) & (cz < zl[k + 1])] = True
    return occ


def greedy_quads(occ, key_fn):
    """occ bool (nx,ny,nz). key_fn(axis, sign) -> int grid (same shape) of colour keys (>0) for the
    face of each voxel pointing along (axis, sign). Returns a list of quads:
    (axis, sign, layer, (u0, v0, u1, v1), key) in voxel units, where layer is the face plane index."""
    quads = []
    dims = occ.shape
    for axis in range(3):
        u_ax, v_ax = [a for a in range(3) if a != axis]
        for sign in (-1, 1):
            nb = np.zeros_like(occ)
            if sign > 0:
                sl_a = [slice(None)] * 3; sl_b = [slice(None)] * 3
                sl_a[axis] = slice(0, dims[axis] - 1); sl_b[axis] = slice(1, None)
                nb[tuple(sl_a)] = occ[tuple(sl_b)]
            else:
                sl_a = [slice(None)] * 3; sl_b = [slice(None)] * 3
                sl_a[axis] = slice(1, None); sl_b[axis] = slice(0, dims[axis] - 1)
                nb[tuple(sl_a)] = occ[tuple(sl_b)]
            exposed = occ & ~nb
            keys = np.where(exposed, key_fn(axis, sign), 0)
            for layer in range(dims[axis]):
                m = np.take(keys, layer, axis=axis)   # 2D (u, v) in axis order u_ax < v_ax
                if not m.any():
                    continue
                m = m.copy()
                nu, nv = m.shape
                for u in range(nu):
                    v = 0
                    while v < nv:
                        k = m[u, v]
                        if k == 0:
                            v += 1
                            continue
                        h = 1
                        while v + h < nv and m[u, v + h] == k:
                            h += 1
                        w = 1
                        while u + w < nu and np.all(m[u + w, v:v + h] == k):
                            w += 1
                        m[u:u + w, v:v + h] = 0
                        plane = layer + (1 if sign > 0 else 0)
                        quads.append((axis, sign, plane, (u, v, u + w, v + h), int(k)))
                        v += h
    return quads


def quads_to_mesh(quads, origin, s):
    """Quads -> (V (4Q,3) bind-space verts, tris (2Q,3), per-tri quad index, per-vert UV in voxel units,
    per-quad normal). Winding is outward counter-clockwise (same convention as the avatar boxes)."""
    V, T, TQ, UV, N = [], [], [], [], []
    for qi, (axis, sign, plane, (u0, v0, u1, v1), key) in enumerate(quads):
        u_ax, v_ax = [a for a in range(3) if a != axis]

        def P(u, v):
            p = np.zeros(3)
            p[axis] = plane; p[u_ax] = u; p[v_ax] = v
            return origin + p * s
        corners = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]
        uvs = [(0, 0), (u1 - u0, 0), (u1 - u0, v1 - v0), (0, v1 - v0)]
        n = np.zeros(3); n[axis] = sign
        if np.dot(np.cross(corners[1] - corners[0], corners[2] - corners[0]), n) < 0:
            corners = corners[::-1]; uvs = uvs[::-1]
        b = len(V)
        V += corners; UV += uvs; N.append(n)
        T += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        TQ += [qi, qi]
    return (np.array(V, np.float32), np.array(T, np.int32), np.array(TQ, np.int32),
            np.array(UV, np.float32), np.array(N, np.float32))


def _self_test():
    # a 2x1x1 box from two cubes: voxel count and greedy face count must be exact
    def cube(lo, hi):
        lo, hi = np.array(lo, float), np.array(hi, float)
        c = np.array([[lo[0] if i & 4 == 0 else hi[0], lo[1] if i & 2 == 0 else hi[1], lo[2] if i & 1 == 0 else hi[2]] for i in range(8)])
        f = [(0, 4, 5, 1), (6, 2, 3, 7), (2, 0, 1, 3), (4, 6, 7, 5), (1, 5, 7, 3), (2, 6, 4, 0)]
        return np.array([[c[q[0]], c[q[1]], c[q[2]]] for q in f] + [[c[q[0]], c[q[2]], c[q[3]]] for q in f])
    occ = voxelize(cube((0, 0, 0), (2, 1, 1)), np.zeros(3), .25, (10, 6, 6))
    assert occ.sum() == 8 * 4 * 4, occ.sum()
    q = greedy_quads(occ, lambda a, s: np.ones(occ.shape, np.int32))
    assert len(q) == 6, len(q)
    V, T, *_ = quads_to_mesh(q, np.zeros(3), .25)
    assert len(T) == 12
    return True


if __name__ == '__main__':
    print('voxel self-test', _self_test())
