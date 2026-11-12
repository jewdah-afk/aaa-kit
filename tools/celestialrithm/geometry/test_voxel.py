#!/usr/bin/env python3
"""Tests for voxel.py (stdlib + numpy). Run: python3 tools/celestialrithm/geometry/test_voxel.py"""
import hashlib
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxel as V  # noqa: E402


def blob(seed):
    """Seeded SDF sculpt: smooth-min of random ellipsoids, two colours."""
    rng = np.random.default_rng(seed)
    g = V.make_grid((-6, -6, -6), (6, 6, 6), 0.5)
    parts = [(rng.uniform(-2.5, 2.5, 3), rng.uniform(1.2, 2.8, 3)) for _ in range(5)]

    def sdf(p):
        d = V.sd_ellipsoid(p, parts[0][0], parts[0][1])
        for c, r in parts[1:]:
            d = V.smin(d, V.sd_ellipsoid(p, c, r), 0.8)
        return d
    V.voxelize(g, sdf, lambda X, Y, Z, d: np.where(Z > 0, 2, 1))
    return g


def test_greedy_same_area():
    g = blob(3)
    naive, greedy = V.mesh_grid(g, False), V.mesh_grid(g, True)
    assert naive.area_by_key() == greedy.area_by_key(), 'area per (dir, colour) differs'
    assert sum(naive.area_by_key().values()) == naive.n_quads
    assert greedy.n_quads < naive.n_quads
    return V.report(naive, greedy)


def test_watertight():
    g = blob(5)
    for greedy in (False, True):
        m = V.mesh_grid(g, greedy)
        ok, bad = V.is_watertight(m)
        assert ok, f'greedy={greedy}: {bad} unmatched unit edges'
        vols = V.signed_volume(m)
        assert vols == [g.count()] * 3, (vols, g.count())


def test_euler_closed_solids():
    g = V.make_grid((0, 0, 0), (8, 8, 8), 1.0)
    V.voxelize(g, lambda p: V.sd_box(p, (4, 4, 4), (2.5, 2.5, 2.5)), 1)
    assert V.euler_characteristic(V.mesh_grid(g, False)) == 2          # sphere-like
    V.carve(g, lambda p: V.sd_box(p, (4, 4, 4), (0.9, 0.9, 5)))           # punch a hole through
    assert V.euler_characteristic(V.mesh_grid(g, False)) == 0          # torus (genus 1)
    ok, _ = V.is_watertight(V.mesh_grid(g, True))
    assert ok


def test_flood_fill_removes_islands():
    g = V.make_grid((0, 0, 0), (20, 20, 20), 1.0)
    V.voxelize(g, lambda p: V.sd_box(p, (6, 6, 6), (3, 3, 3)), 1)     # voxels 3..8
    body = g.count()
    g.col[18, 18, 18] = 2                       # floating islands
    g.col[0, 0, 15] = 2
    g.col[9, 9, 9] = 3                          # touches the body by one corner only
    g.col[14, 3, 3] = 2; g.col[15, 4, 4] = 2    # a 2-voxel island joined by a corner
    removed = V.keep_connected(g)
    assert removed == 4, removed
    assert g.count() == body + 1 and g.col[9, 9, 9] == 3, '26-connected corner voxel lost'
    labels, sizes = V.components26(g.occ)
    assert sizes == [body + 1], sizes


def test_deterministic():
    def run():
        g = blob(11)
        m = V.mesh_grid(g, True)
        with tempfile.TemporaryDirectory() as td:
            V.export_obj(m, Path(td) / 'b.obj', {1: (.5, .3, .2), 2: (.2, .6, .3)})
            txt = (Path(td) / 'b.obj').read_bytes()
        return hashlib.sha256(g.col.tobytes() + m.corners.tobytes() + txt).hexdigest()
    a, b = run(), run()
    assert a == b
    assert run() != hashlib.sha256(blob(12).col.tobytes()).hexdigest()


def test_stud_uv_continuous():
    """Two boxes side by side: the shared seam has identical UVs on both sides."""
    g = V.make_grid((0, 0, 0), (8, 4, 2), 0.5)
    V.voxelize(g, lambda p: V.sd_box(p, (2, 2, 1), (2, 2, 1)), 1)
    V.voxelize(g, lambda p: V.sd_box(p, (6, 2, 1), (2, 2, 1)), 2)
    m = V.mesh_grid(g, True)
    uv = m.stud_uv(1.0); w = m.world()
    top = m.dirs == 4
    for q in np.nonzero(top)[0]:
        assert np.allclose(uv[q], w[q][:, :2])              # UV = world XY x studs/unit
    assert top.sum() == 2                                   # two colours -> two top quads


def test_hull_offsets_outward():
    g = V.make_grid((0, 0, 0), (2, 2, 2), 1.0)
    g.col[:] = 1
    m = V.mesh_grid(g, True)
    h = V.hull_quads(m, 0.1)
    assert np.isclose(h.min(), -0.1) and np.isclose(h.max(), 2.1)
    assert m.n_quads == 6


def main():
    tests = [(k, v) for k, v in globals().items() if k.startswith('test_')]
    failed = 0
    rep = None
    for name, fn in tests:
        try:
            r = fn()
            if name == 'test_greedy_same_area':
                rep = r
            print(f'PASS {name}')
        except AssertionError as e:
            failed += 1
            print(f'FAIL {name}: {e}')
    print('triangle reduction (seeded blob):', rep)
    print(f'{len(tests) - failed} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
