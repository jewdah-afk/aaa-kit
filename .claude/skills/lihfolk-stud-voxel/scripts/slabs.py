"""Faceted slabs: turn labelled patches of a body shell into flat, brick-friendly armour slabs (research ch. 92).

Used after a plate map exists (traced from a concept by trace_match.py, or voronoi cells). Works on POINTS, not grids,
so it is cheap on big models: pass the shell's brick centres, their signed distance to the body surface, and a plate
label per point.

    on, tone, wall = slabs.fit(P, dv, label, level, outward, rise=1.4, base=-.9)

    P        (N, 3) brick centres of the shell (mirror x with abs() first for a symmetric body)
    dv       (N,)   signed distance of each point to the body surface (negative inside), same units as P
    label    (N,)   plate number per point (ints >= 0)
    level    array  height level per plate number (1 = lowest)
    outward  (N, 3) any vector pointing roughly away from the body at each point (e.g. P minus the body's axis)
    rise     height per level, base = offset of level 0; the slab's outer face sits rise*level+base above the surface
    returns  on   (N,) bool   bricks that belong to a slab
             tone (N,) float  colour multiplier: faces that look up are lighter, higher plates slightly lighter
             wall (N,) bool   bricks under the slab's outer layer: paint these dark (tone already includes it)

How: per plate, fit a plane to the surface points under it, snap the plane's tilt to SNAP slopes (flat, 1:2, 1:1) so
its staircase is regular, lift it by the plate's level, and keep every shell brick under that plane. `cap` stops a
slab from standing far off a curved body; `floor` keeps the surface covered where the plane dips inside it.
"""
import numpy as np

SNAP = np.array([0, .5, 1.0])


def snap_normal(nrm, snap=SNAP):
    q = nrm / np.abs(nrm).max()
    q = np.sign(q) * snap[np.argmin(np.abs(np.abs(q)[:, None] - snap[None]), 1)]
    return q / np.linalg.norm(q)


def fit(P, dv, label, level, outward, rise=1.4, base=-.9, cap=1.1, floor=.5, layer=1.0, min_pts=12, up=1,
        tone_base=.86, tone_up=.34, tone_level=.04, wall_tone=.58):
    P = np.asarray(P, float); N = len(P)
    on = np.zeros(N, bool); tone = np.ones(N, np.float32); wall = np.zeros(N, bool)
    order = np.argsort(label, kind='stable'); lab_s = label[order]
    ids, starts = np.unique(lab_s, return_index=True); ends = list(starts[1:]) + [N]
    for c, a, b in zip(ids, starts, ends):
        ii = order[a:b]; r = rise * float(level[c]) + base
        sf = ii[np.abs(dv[ii]) < .8]
        if len(sf) < min_pts:                                            # too small to fit: a plain offset skin
            on[ii] = dv[ii] < max(r, floor); continue
        c0 = P[sf].mean(0); nrm = np.linalg.svd(P[sf] - c0, full_matrices=False)[2][2]
        if nrm.dot(outward[sf].mean(0)) < 0: nrm = -nrm
        nrm = snap_normal(nrm)
        h = P[ii].dot(nrm); top = np.median(P[sf].dot(nrm)) + r
        on[ii] = ((h <= top) & (dv[ii] < r + cap)) | (dv[ii] < floor)
        w = (h <= top - layer) & (dv[ii] < r + cap - layer)
        t = np.full(len(ii), tone_base + tone_up * max(nrm[up], 0) + tone_level * float(level[c]), np.float32)
        t[w] *= wall_tone
        tone[ii] = t; wall[ii] = w & on[ii]
    return on, tone, wall


def _selftest():
    """a ball of radius 12 cut into 8 octant plates: every surface brick stays covered, slabs are flat, walls exist"""
    g = np.arange(-18, 19) + .5; X, Y, Z = np.meshgrid(g, g, g, indexing='ij')
    d = np.sqrt(X * X + Y * Y + Z * Z) - 12; m = (d < 6) & (d > -3)
    P = np.stack([X[m], Y[m], Z[m]], 1); dv = d[m]
    label = ((P[:, 0] > 0) * 1 + (P[:, 1] > 0) * 2 + (P[:, 2] > 0) * 4).astype(int)
    level = np.array([1, 2, 3, 1, 2, 3, 1, 2])
    on, tone, wall = fit(P, dv, label, level, P)
    assert on[dv < .5].all(), 'surface not covered'
    assert not on[dv > 3 * 1.4 - .9 + 1.1 + 1e-6].any(), 'slab stands too far off the body'
    assert wall.any() and (tone[wall] < tone[on & ~wall].mean()).all(), 'walls are not darker'
    for c in range(8):                                                   # the outer face of each plate is one plane
        k = on & (label == c) & (dv > .5)
        n_ = snap_normal(np.linalg.svd(P[k] - P[k].mean(0), full_matrices=False)[2][2])
        assert np.isin(np.round(np.abs(n_ / np.abs(n_).max()), 3), SNAP).all(), 'tilt not snapped'
    a = fit(P, dv, label, level, P); b = fit(P, dv, label, level, P)
    assert all(np.array_equal(x, y) for x, y in zip(a, b)), 'not deterministic'
    print('SLABS_OK', int(on.sum()), 'bricks in 8 slabs,', int(wall.sum()), 'wall bricks')


if __name__ == '__main__':
    _selftest()
