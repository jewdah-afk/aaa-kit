"""Stud voxel kit: SDF sculpting -> occupancy/colour grid -> greedy-meshed stud geometry.

Own implementation (numpy only; bpy only inside `build_bpy`). Pipeline:

    sdf (primitives + smooth min)  ->  voxelize  ->  keep_connected (26-conn flood fill)
    ->  exposed faces  ->  greedy merge (coplanar, same colour)  ->  world-aligned stud UVs
    ->  OBJ export / bpy mesh (vertex colours + UVs + per-face material slots)

Conventions
  * Grid index (i, j, k) maps to world (X, Y, Z); Z is up (Blender native).
  * `col` is a uint8 grid of palette ids; 0 means empty, so occupancy is `col > 0`.
  * Voxel (i, j, k) spans [origin + idx*size, origin + (idx+1)*size].
  * Quads are kept in integer grid coordinates, so merging and the tests are exact.
  * Directions: 0 +X, 1 -X, 2 +Y, 3 -Y, 4 +Z (top), 5 -Z (bottom).

Greedy meshing follows the public algorithm described by Mikola Lysenko,
"Meshing in a Minecraft Game" (0fps.net, 2012): per slice, grow a run along u,
then grow it along v while the whole run still matches, emit one quad, mark it used.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DIRS = ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1))   # (axis, sign) per direction id
DIR_NAMES = ('+X', '-X', '+Y', '-Y', '+Z', '-Z')


# ---------------------------------------------------------------- SDF primitives
# Every primitive takes p = (X, Y, Z) arrays (any matching shape) and returns signed distance.

def sd_sphere(p, c, r):
    return np.sqrt((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2) - r


def sd_box(p, c, half):
    q = [np.abs(p[i] - c[i]) - half[i] for i in range(3)]
    outside = np.sqrt(sum(np.maximum(qi, 0.0) ** 2 for qi in q))
    inside = np.minimum(np.maximum(np.maximum(q[0], q[1]), q[2]), 0.0)
    return outside + inside


def sd_round_box(p, c, half, r):
    return sd_box(p, c, [h - r for h in half]) - r


def sd_ellipsoid(p, c, radii):
    """Bound-corrected ellipsoid distance (Quilez approximation): exact on the surface."""
    q = [(p[i] - c[i]) for i in range(3)]
    k0 = np.sqrt(sum((q[i] / radii[i]) ** 2 for i in range(3)))
    k1 = np.sqrt(sum((q[i] / radii[i] ** 2) ** 2 for i in range(3)))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_cylinder(p, c, r, half_len, axis=2):
    """Capped cylinder along `axis` (0 X, 1 Y, 2 Z)."""
    a = [0, 1, 2]; a.remove(axis)
    radial = np.sqrt((p[a[0]] - c[a[0]]) ** 2 + (p[a[1]] - c[a[1]]) ** 2) - r
    along = np.abs(p[axis] - c[axis]) - half_len
    outside = np.sqrt(np.maximum(radial, 0) ** 2 + np.maximum(along, 0) ** 2)
    return outside + np.minimum(np.maximum(radial, along), 0.0)


def sd_octahedron(p, c, s):
    """Bound for a regular octahedron of 'radius' s (good enough for voxel occupancy)."""
    return (np.abs(p[0] - c[0]) + np.abs(p[1] - c[1]) + np.abs(p[2] - c[2]) - s) * 0.57735027


def smin(a, b, k):
    """Polynomial smooth minimum (blend radius k, in world units). k <= 0 gives min."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def op_union(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.minimum(out, d)
    return out


def op_subtract(a, b):
    return np.maximum(a, -b)


def op_intersect(a, b):
    return np.maximum(a, b)


# ---------------------------------------------------------------- grid

@dataclass
class Grid:
    col: np.ndarray                       # uint8 (nx, ny, nz), 0 = empty
    origin: tuple = (0.0, 0.0, 0.0)       # world position of the grid's min corner
    size: float = 1.0                     # voxel edge in world units

    @property
    def occ(self):
        return self.col > 0

    @property
    def shape(self):
        return self.col.shape

    def centres(self):
        nx, ny, nz = self.col.shape
        ax = [self.origin[i] + (np.arange(n) + 0.5) * self.size for i, n in enumerate((nx, ny, nz))]
        return np.meshgrid(ax[0], ax[1], ax[2], indexing='ij')

    def count(self):
        return int(np.count_nonzero(self.col))

    def copy(self):
        return Grid(self.col.copy(), tuple(self.origin), self.size)


def make_grid(lo, hi, size):
    """Empty grid covering world box [lo, hi] with voxel edge `size` (snapped outward)."""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    n = np.maximum(np.ceil((hi - lo) / size - 1e-9).astype(int), 1)
    return Grid(np.zeros(tuple(n), np.uint8), tuple(lo), float(size))


def voxelize(grid: Grid, sdf, colour, overwrite=True):
    """Fill voxels whose centre has sdf <= 0. `colour` is an int palette id or a
    function (X, Y, Z, d) -> int array. Later calls paint over earlier ones."""
    X, Y, Z = grid.centres()
    d = sdf((X, Y, Z))
    inside = d <= 0
    c = colour(X, Y, Z, d) if callable(colour) else np.full(grid.shape, colour, np.uint8)
    c = np.asarray(c, np.uint8)
    if overwrite:
        grid.col[inside] = c[inside]
    else:
        m = inside & (grid.col == 0)
        grid.col[m] = c[m]
    return int(np.count_nonzero(inside))


def carve(grid: Grid, sdf):
    X, Y, Z = grid.centres()
    m = sdf((X, Y, Z)) <= 0
    grid.col[m] = 0
    return int(np.count_nonzero(m))


def paint(grid: Grid, sdf, colour, only_solid=True):
    """Recolour voxels inside sdf (keeps occupancy)."""
    X, Y, Z = grid.centres()
    m = sdf((X, Y, Z)) <= 0
    if only_solid:
        m &= grid.col > 0
    grid.col[m] = colour
    return int(np.count_nonzero(m))


# ---------------------------------------------------------------- 26-connected cleanup

def _dilate26(m):
    """Binary dilation with the full 3x3x3 cube (26-neighbourhood), no wraparound."""
    out = m.copy()
    for axis in range(3):
        a = out.copy()
        sl_dst = [slice(None)] * 3; sl_src = [slice(None)] * 3
        sl_dst[axis] = slice(1, None); sl_src[axis] = slice(None, -1)
        a[tuple(sl_dst)] |= out[tuple(sl_src)]
        sl_dst[axis] = slice(None, -1); sl_src[axis] = slice(1, None)
        a[tuple(sl_dst)] |= out[tuple(sl_src)]
        out = a                       # separable: x then y then z covers all 26 neighbours
    return out


def components26(occ):
    """Label 26-connected components. Returns (labels int32 grid, sizes list, 1-based).
    Frontier expansion with separable dilation; deterministic (seeds in C order)."""
    labels = np.zeros(occ.shape, np.int32)
    sizes = []
    remaining = occ.copy()
    while remaining.any():
        seed = np.unravel_index(np.argmax(remaining), occ.shape)
        comp = np.zeros_like(occ); comp[seed] = True
        while True:
            grown = _dilate26(comp) & occ
            if grown.sum() == comp.sum():
                break
            comp = grown
        sizes.append(int(comp.sum()))
        labels[comp] = len(sizes)
        remaining &= ~comp
    return labels, sizes


def keep_connected(grid: Grid, min_voxels=None):
    """Drop voxels not 26-connected to the largest piece (or, with min_voxels, drop
    every piece smaller than that). Returns the number of voxels removed."""
    labels, sizes = components26(grid.occ)
    if not sizes:
        return 0
    if min_voxels is None:
        keep = {int(np.argmax(sizes)) + 1}
    else:
        keep = {i + 1 for i, s in enumerate(sizes) if s >= min_voxels}
    drop = (labels > 0) & ~np.isin(labels, list(keep))
    n = int(drop.sum())
    grid.col[drop] = 0
    return n


# ---------------------------------------------------------------- faces and meshing

@dataclass
class Mesh:
    """Quad mesh in integer grid coordinates; every quad is axis-aligned."""
    corners: np.ndarray          # int (M, 4, 3) grid-space corners, CCW seen from outside
    colour: np.ndarray           # uint8 (M,) palette id
    dirs: np.ndarray             # uint8 (M,) direction id 0..5
    origin: tuple = (0.0, 0.0, 0.0)
    size: float = 1.0
    tags: dict = field(default_factory=dict)

    @property
    def n_quads(self):
        return int(len(self.colour))

    @property
    def n_tris(self):
        return 2 * self.n_quads

    def world(self):
        return np.asarray(self.origin, float) + self.corners.astype(float) * self.size

    def area_by_key(self):
        """{(dir, colour): area in voxel faces}."""
        out = {}
        for q, c, d in zip(self.corners, self.colour, self.dirs):
            ext = q.max(0) - q.min(0)
            a = int(np.prod([e for e in ext if e != 0]))
            out[(int(d), int(c))] = out.get((int(d), int(c)), 0) + a
        return out

    def stud_uv(self, studs_per_unit=1.0):
        """World-aligned UVs (M, 4, 2): one continuous grid for the whole model, so
        studs line up across neighbouring boxes and never stretch."""
        w = self.world() * studs_per_unit
        uv = np.zeros(self.corners.shape[:2] + (2,), float)
        for d, (axis, sign) in enumerate(DIRS):
            m = self.dirs == d
            if not m.any():
                continue
            if axis == 2:                     # top/bottom: X, Y
                uv[m, :, 0] = w[m, :, 0]; uv[m, :, 1] = w[m, :, 1]
            elif axis == 0:                   # X faces: Y along, Z up
                uv[m, :, 0] = w[m, :, 1] * sign; uv[m, :, 1] = w[m, :, 2]
            else:                             # Y faces: X along, Z up
                uv[m, :, 0] = -w[m, :, 0] * sign; uv[m, :, 1] = w[m, :, 2]
        return uv

    def planar_uv(self, mask):
        """0..1 UVs across the bounding box of the quads in `mask` (for one material
        panel such as a keycap face or a gem)."""
        uv = np.zeros(self.corners.shape[:2] + (2,), float)
        for d, (axis, sign) in enumerate(DIRS):
            m = mask & (self.dirs == d)
            if not m.any():
                continue
            ua, va = [a for a in range(3) if a != axis]
            if axis == 1:
                ua, va = 0, 2
            pts = self.corners[m].astype(float)
            lo = pts.reshape(-1, 3).min(0); hi = pts.reshape(-1, 3).max(0)
            span = np.maximum(hi - lo, 1e-9)
            u = (pts[..., ua] - lo[ua]) / span[ua]
            v = (pts[..., va] - lo[va]) / span[va]
            if (axis == 0 and sign < 0) or (axis == 1 and sign > 0):
                u = 1 - u
            uv[m, :, 0] = u; uv[m, :, 1] = v
        return uv


def exposed_masks(col):
    """For each direction, a (nx, ny, nz) uint8 grid: colour of the solid voxel where
    that face is exposed (neighbour empty or outside), else 0."""
    occ = col > 0
    p = np.pad(occ, 1)
    nx, ny, nz = col.shape
    out = []
    for axis, sign in DIRS:
        sl = [slice(1, nx + 1), slice(1, ny + 1), slice(1, nz + 1)]
        sl[axis] = slice(1 + sign, (nx, ny, nz)[axis] + 1 + sign)
        neigh = p[tuple(sl)]
        out.append(np.where(occ & ~neigh, col, 0).astype(np.uint8))
    return out


def _quad(axis, sign, k, u0, v0, u1, v1):
    """Grid-space corners of a quad on plane `k` (already the plane index)."""
    ua, va = (axis + 1) % 3, (axis + 2) % 3
    pts = []
    for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        c = [0, 0, 0]; c[axis] = k; c[ua] = u; c[va] = v
        pts.append(c)
    if sign < 0:
        pts = pts[::-1]
    return pts


def mesh_faces(col, greedy=True, origin=(0.0, 0.0, 0.0), size=1.0):
    """Exposed faces -> quads. greedy=False gives the naive one-quad-per-face set."""
    masks = exposed_masks(col)
    corners, colours, dirs = [], [], []
    for d, (axis, sign) in enumerate(DIRS):
        ua, va = (axis + 1) % 3, (axis + 2) % 3
        m = masks[d].transpose(axis, ua, va)          # slices along axis, [u, v]
        for k in range(m.shape[0]):
            sl = m[k]
            if not sl.any():
                continue
            plane = k + 1 if sign > 0 else k
            if not greedy:
                us, vs = np.nonzero(sl)
                for u, v in zip(us.tolist(), vs.tolist()):
                    corners.append(_quad(axis, sign, plane, u, v, u + 1, v + 1))
                    colours.append(sl[u, v]); dirs.append(d)
                continue
            used = np.zeros(sl.shape, bool)
            nu, nv = sl.shape
            for v in range(nv):
                u = 0
                while u < nu:
                    c = sl[u, v]
                    if c == 0 or used[u, v]:
                        u += 1
                        continue
                    w = 1
                    while u + w < nu and sl[u + w, v] == c and not used[u + w, v]:
                        w += 1
                    h = 1
                    while v + h < nv:
                        run = sl[u:u + w, v + h]
                        if np.all(run == c) and not used[u:u + w, v + h].any():
                            h += 1
                        else:
                            break
                    used[u:u + w, v:v + h] = True
                    corners.append(_quad(axis, sign, plane, u, v, u + w, v + h))
                    colours.append(c); dirs.append(d)
                    u += w
    return Mesh(np.asarray(corners, np.int64).reshape(-1, 4, 3), np.asarray(colours, np.uint8),
                np.asarray(dirs, np.uint8), tuple(origin), float(size))


def mesh_grid(grid: Grid, greedy=True):
    return mesh_faces(grid.col, greedy, grid.origin, grid.size)


# ---------------------------------------------------------------- checks used by tests and reports

def unit_edges(mesh: Mesh):
    """Directed unit-length boundary segments of every quad: {(a, b): count}.
    A closed, consistently oriented surface (T-junctions allowed) has count(a,b) ==
    count(b,a) for every segment."""
    out = {}
    for q in mesh.corners:
        for i in range(4):
            a = q[i]; b = q[(i + 1) % 4]
            step = np.sign(b - a); n = int(np.abs(b - a).sum())
            for s in range(n):
                p0 = tuple((a + step * s).tolist()); p1 = tuple((a + step * (s + 1)).tolist())
                out[(p0, p1)] = out.get((p0, p1), 0) + 1
    return out


def is_watertight(mesh: Mesh):
    e = unit_edges(mesh)
    bad = [k for k, n in e.items() if e.get((k[1], k[0]), 0) != n]
    return len(bad) == 0, len(bad)


def euler_characteristic(mesh: Mesh):
    """V - E + F with vertices welded by grid position (meaningful for the naive mesh,
    whose quads share full edges)."""
    verts = {tuple(p) for q in mesh.corners.tolist() for p in q}
    edges = set()
    for q in mesh.corners.tolist():
        for i in range(4):
            a, b = tuple(q[i]), tuple(q[(i + 1) % 4])
            edges.add((min(a, b), max(a, b)))
    return len(verts) - len(edges) + mesh.n_quads


def signed_volume(mesh: Mesh):
    """Divergence theorem per axis: sum(plane * area * sign) over quads on that axis.
    Equals the voxel count for a closed outward-oriented surface."""
    vols = []
    for axis in range(3):
        tot = 0
        for q, d in zip(mesh.corners, mesh.dirs):
            ax, sign = DIRS[int(d)]
            if ax != axis:
                continue
            ext = q.max(0) - q.min(0)
            area = int(np.prod([e for i, e in enumerate(ext) if i != axis]))
            tot += sign * int(q[0][axis]) * area
        vols.append(tot)
    return vols


def report(naive: Mesh, greedy: Mesh):
    return {'quads_naive': naive.n_quads, 'tris_naive': naive.n_tris,
            'quads_greedy': greedy.n_quads, 'tris_greedy': greedy.n_tris,
            'verts_greedy_unwelded': 4 * greedy.n_quads,
            'reduction_ratio': round(naive.n_tris / max(greedy.n_tris, 1), 2)}


# ---------------------------------------------------------------- export

def export_obj(mesh: Mesh, path, palette, studs_per_unit=1.0, name='voxel'):
    """OBJ + MTL (one material per palette colour). Vertices welded by position; UVs
    are the world stud grid. Palette: {id: (r, g, b) in 0..1 sRGB}."""
    from pathlib import Path
    path = Path(path)
    w = mesh.world(); uv = mesh.stud_uv(studs_per_unit)
    vid, vlist, tid, tlist, faces = {}, [], {}, [], {}
    normals = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for qi in range(mesh.n_quads):
        idx = []
        for ci in range(4):
            key = tuple(np.round(w[qi, ci], 6).tolist())
            if key not in vid:
                vid[key] = len(vlist) + 1; vlist.append(key)
            tk = tuple(np.round(uv[qi, ci], 6).tolist())
            if tk not in tid:
                tid[tk] = len(tlist) + 1; tlist.append(tk)
            idx.append((vid[key], tid[tk]))
        faces.setdefault(int(mesh.colour[qi]), []).append((idx, int(mesh.dirs[qi]) + 1))
    mtl = path.with_suffix('.mtl')
    with open(mtl, 'w', newline='\n') as f:
        for c in sorted(faces):
            r, g, b = palette.get(c, (1, 0, 1))
            f.write(f'newmtl c{c}\nKd {r:.4f} {g:.4f} {b:.4f}\n\n')
    with open(path, 'w', newline='\n') as f:
        f.write(f'# {name}: greedy-meshed stud voxel model, {mesh.n_tris} tris\nmtllib {mtl.name}\no {name}\n')
        for p in vlist:
            f.write('v %.6f %.6f %.6f\n' % p)
        for t in tlist:
            f.write('vt %.6f %.6f\n' % t)
        for n in normals:
            f.write('vn %d %d %d\n' % n)
        for c in sorted(faces):
            f.write(f'usemtl c{c}\n')
            for idx, ni in faces[c]:
                f.write('f ' + ' '.join(f'{v}/{t}/{ni}' for v, t in idx) + '\n')
    return {'vertices': len(vlist), 'triangles': mesh.n_tris, 'path': str(path)}


def hull_quads(mesh: Mesh, offset):
    """Inverted-hull outline shell (world coords, (M, 4, 3)): each quad pushed out along
    its normal and grown in-plane by `offset`, winding reversed. Grown quads meet at
    convex edges and tuck inside the solid at concave ones, so no welding is needed."""
    w = mesh.world()
    out = np.empty_like(w)
    for qi in range(mesh.n_quads):
        axis, sign = DIRS[int(mesh.dirs[qi])]
        q = w[qi].copy()
        ctr = q.mean(0)
        for a in range(3):
            if a == axis:
                q[:, a] += sign * offset
            else:
                q[:, a] += np.sign(q[:, a] - ctr[a]) * offset
        out[qi] = q[::-1]
    return out


# ---------------------------------------------------------------- Blender builder

def build_bpy(name, quads_world, uvs, colours_rgba, mat_index, materials, weights=None):
    """Create a bpy mesh object from unwelded quads.

    quads_world (M,4,3) float, uvs (M,4,2), colours_rgba (M,4) linear per quad,
    mat_index (M,) int slot per quad, materials list of bpy materials,
    weights: optional {group_name: bool mask (M,)} rigid vertex-group assignment.
    """
    import bpy
    M = len(quads_world)
    verts = quads_world.reshape(-1, 3)
    faces = np.arange(4 * M).reshape(M, 4)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set('co', verts.astype(np.float32).ravel())
    me.loops.add(4 * M); me.loops.foreach_set('vertex_index', faces.ravel().astype(np.int32))
    me.polygons.add(M)
    me.polygons.foreach_set('loop_start', (np.arange(M) * 4).astype(np.int32))
    me.polygons.foreach_set('loop_total', np.full(M, 4, np.int32))
    me.polygons.foreach_set('material_index', np.asarray(mat_index, np.int32))
    me.update(calc_edges=True)
    uvl = me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', np.asarray(uvs, np.float32).reshape(-1))
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    ca.data.foreach_set('color', np.repeat(np.asarray(colours_rgba, np.float32)[:, None, :], 4, 1).ravel())
    for m in materials:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if weights:
        for gname, mask in weights.items():
            vg = ob.vertex_groups.new(name=gname)
            idx = np.nonzero(np.repeat(np.asarray(mask, bool), 4))[0].tolist()
            if idx:
                vg.add(idx, 1.0, 'REPLACE')
    return ob
