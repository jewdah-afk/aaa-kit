"""Rig + Roblox export for the BRICK pipeline (always run it: every brick model ships animation-ready).

In the model script (after the grid is final, i.e. after palette snapping, at the very end after render_all()):
    sys.path.insert(0, <skill>/scripts); import brick_rig
    RIG = [(bone, parent, head_xyz, tail_xyz), ...]        # brick coords (x, y up, z back); root first, parent None
    brick_rig.export(ID, OUT, lo, kind, col, RIG, overrides=[(mask, bone), ...], glow=GLOW, pose={bone: (rx, ry, rz)})

- Every solid brick goes to the nearest bone SEGMENT; `overrides` (applied in order, after) force masks onto a bone.
  A bone named 'root' gets no bricks unless an override gives it some (it is the static ground/mover bone).
- Each child bone also gets a copy of its parent's bricks that touch it (1-brick overlap), so posed joints show no holes.
- Greedy meshing (coplanar, same colour) per bone; one mesh object per bone (+ one per glow colour), split until each
  piece is <= MAX_TRIS triangles. Rigid weights (1.0 to its bone), all skinned to one armature.
- Output: <OUT>/<ID>_rig.glb (1 brick = 2.5 studs, glTF Y-up, front = Roblox LookVector after the importer's 180 turn),
  <OUT>/<ID>_rig.json (bones, pivots in studs, tris per piece), <OUT>/stud_mul.png (texture baked into the glb),
  then the GLB is re-imported into an empty scene, checked, posed and rendered to <OUT>/render/<ID>_rigrest.png + _posed.png.
  Prints RIG_OK on success. NOTE: it resets the Blender session (read_factory_settings), so call it last.
- Colours: vertex colours (COLOR_0, exact) x base texture (stud_mul.png = 2 x stud overlay, the box-rig rule).
  Glow pieces: emissive material in the glow colour, no texture.
"""
import json, math, os
import numpy as np

MAX_TRIS = 20000
S = 2.5                                   # studs per brick (bld.py lowers it for fine buildings)
UVD = 16.0                                # bricks per stud-texture tile
HERE = os.path.dirname(os.path.abspath(__file__))


def assign(X, Y, Z, solid, RIG, overrides=()):
    """int label per voxel (index into RIG, -1 = empty)."""
    names = [r[0] for r in RIG]
    P = np.stack([X[solid], Y[solid], Z[solid]], 1)
    best = np.full(len(P), np.inf); bi = np.zeros(len(P), np.int32)
    for i, (name, _, h, t) in enumerate(RIG):
        if name == 'root': continue
        a = np.array(h, float); ab = np.array(t, float) - a
        tt = np.clip((P - a) @ ab / max(ab @ ab, 1e-9), 0, 1)
        d = np.linalg.norm(P - a - tt[:, None] * ab, axis=1)
        w = d < best; best[w] = d[w]; bi[w] = i
    label = np.full(solid.shape, -1, np.int32); label[solid] = bi
    for m, bone in overrides: label[m & solid] = names.index(bone)
    return label


def limb(X, Y, Z, mask, bones):
    """overrides that split `mask` (e.g. one tentacle) between its own bones only, by nearest segment."""
    lab = assign(X, Y, Z, mask, bones)
    return [(lab == i, b[0]) for i, b in enumerate(bones)]


def _dilate6(m):
    o = m.copy()
    for ax in range(3):
        for s in (1, -1):
            r = np.roll(m, s, axis=ax); sl = [slice(None)] * 3; sl[ax] = 0 if s > 0 else -1; r[tuple(sl)] = False; o |= r
    return o


def _greedy2d(K):
    """K: 2D int keys (-1 = none). Returns rectangles (i, j, di, dj, key) covering every key cell."""
    K = K.copy(); out = []; H, W = K.shape
    for i in range(H):
        for j in np.flatnonzero(K[i] >= 0):
            k = K[i, j]
            if k < 0: continue                # taken by an earlier rectangle
            j1 = j + 1
            while j1 < W and K[i, j1] == k: j1 += 1
            i1 = i + 1
            while i1 < H and (K[i1, j:j1] == k).all(): i1 += 1
            K[i:i1, j:j1] = -1; out.append((i, j, i1 - i, j1 - j, k))
    return out


def _quads(occ, keys, lo):
    """greedy quads of the exposed faces of cells with keys >= 0, exposure tested against occ (own bone set).
    Returns corners (N,4,3) in Blender studs, uvs (N,4,2), key (N,)."""
    idx = np.argwhere(keys >= 0)
    if not len(idx): return np.zeros((0, 4, 3)), np.zeros((0, 4, 2)), np.zeros(0, int)
    a0 = idx.min(0); a1 = idx.max(0) + 2                                         # +1 pad for the far neighbour
    a0p = np.maximum(a0 - 1, 0); sl = tuple(slice(a0p[k], min(a1[k], occ.shape[k])) for k in range(3))
    O = occ[sl]; Kc = np.where(keys[sl] >= 0, keys[sl], -1); off = a0p
    C, U, Kq, D = [], [], [], []
    for ax in range(3):
        u, w = [k for k in range(3) if k != ax]
        for s in (1, -1):
            nb = np.roll(O, -s, axis=ax); e = [slice(None)] * 3; e[ax] = -1 if s > 0 else 0; nb[tuple(e)] = False
            F = np.where(nb, -1, Kc)
            F = np.moveaxis(F, (ax, u, w), (0, 1, 2))
            for k in np.flatnonzero((F >= 0).any((1, 2))):
                for (i, j, di, dj, key) in _greedy2d(F[k]):
                    g = np.zeros((4, 3)); pl = off[ax] + k + (1 if s > 0 else 0)
                    for c, (du, dw) in enumerate(((0, 0), (di, 0), (di, dj), (0, dj))):
                        g[c, ax] = pl; g[c, u] = off[u] + i + du; g[c, w] = off[w] + j + dw
                    C.append(g); Kq.append(key); D.append(ax * 2 + (s > 0))
                    U.append(np.stack([g[:, u], g[:, w]], 1) / UVD)             # same world stud grid as build(); UVD = 16 x finer-brick factor
    if not C: return np.zeros((0, 4, 3)), np.zeros((0, 4, 2)), np.zeros(0, int)   # cells fully enclosed
    C = np.array(C); U = np.array(U); Kq = np.array(Kq); D = np.array(D)
    P = ((C + lo) * S)[..., [0, 2, 1]]                                           # brick -> studs, B(x, y, z) = (x, z, y)
    want = np.zeros((len(C), 3)); want[np.arange(len(C)), np.array([0, 2, 1])[D // 2]] = np.where(D % 2, 1, -1)
    nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    flip = (nrm * want).sum(1) < 0                                               # outward winding
    P[flip] = P[flip][:, ::-1]; U[flip] = U[flip][:, ::-1]
    return P, U, Kq


def export(ID, OUT, lo, kind, col, RIG, overrides=(), glow=None, pose=None, stud_png=None, render=True):
    import bpy
    from mathutils import Vector
    lo = np.asarray(lo, float); n = kind.shape
    cx, cy, cz = (lo[k] + .5 + np.arange(n[k]) for k in range(3))
    X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij')
    solid = kind > 0
    label = assign(X, Y, Z, solid, RIG, overrides)
    names = [r[0] for r in RIG]; parent = {r[0]: r[1] for r in RIG}
    # colour keys: one id per (kind, rgb)
    rgb = np.round(np.clip(col, 0, 1) * 255).astype(int)
    code = (kind.astype(np.int64) << 24) | (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    ucode, cid = np.unique(np.where(solid, code, -1), return_inverse=True); cid = cid.reshape(n)
    ukind = ucode >> 24; ucol = np.stack([(ucode >> 16) & 255, (ucode >> 8) & 255, ucode & 255], 1) / 255.0
    if glow:
        for k, c in glow.items(): ucol[ukind == k] = c
    def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)

    # --- stud multiply texture (sRGB stored, linear value = min(1, 2 x overlay value))
    stud_png = stud_png or next(p for p in (os.path.join(HERE, '..', 'assets', 'roblox_square_studs.png'),
                                            os.path.expanduser('~/.claude/skills/stud-voxel-creatures/assets/roblox_square_studs.png')) if os.path.exists(p))
    src = bpy.data.images.load(stud_png); w_, h_ = src.size
    px = np.empty(w_ * h_ * 4, np.float32); src.pixels.foreach_get(px); px = px.reshape(-1, 4)
    m = np.clip(2 * px[:, :3], 0, 1); srgb = np.where(m > .0031308, 1.055 * m ** (1 / 2.4) - .055, 12.92 * m)
    im = bpy.data.images.new('stud_mul', w_, h_); im.pixels.foreach_set(np.concatenate([srgb, np.ones((len(m), 1))], 1).astype(np.float32).ravel())
    im.filepath_raw = os.path.join(OUT, 'stud_mul.png'); im.file_format = 'PNG'; im.save()

    sc = bpy.context.scene
    for o in sc.objects: o.select_set(False)
    arm_d = bpy.data.armatures.new(ID + '_Armature'); arm = bpy.data.objects.new(ID + '_Rig', arm_d)
    sc.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bv(p): return Vector((p[0] * S, p[2] * S, p[1] * S))
    for name, par, h, t in RIG:
        eb = arm_d.edit_bones.new(name); eb.head = bv(h); eb.tail = bv(t)
        if par: eb.parent = arm_d.edit_bones[par]
    bpy.ops.object.mode_set(mode='OBJECT')

    mb = bpy.data.materials.new('StudBrick'); mb.use_nodes = True; nt = mb.node_tree
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im
    nt.links.new(tx.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    gmats = {}
    def gmat(k):
        if k not in gmats:
            g = bpy.data.materials.new('Glow%d' % k); g.use_nodes = True; b = g.node_tree.nodes['Principled BSDF']
            c = (*lin(ucol[ukind == k][0]), 1); b.inputs['Base Color'].default_value = c
            b.inputs['Emission Color'].default_value = c; b.inputs['Emission Strength'].default_value = 1.0; gmats[k] = g
        return gmats[k]

    pieces = []
    def piece(pname, bone, P, U, K, mat):
        if 2 * len(P) > MAX_TRIS:                                               # split by region along the longest extent
            cen = P.mean(1); ax = int(np.argmax(np.ptp(cen, 0))); o = np.argsort(cen[:, ax]); hf = len(o) // 2
            piece(pname + 'a', bone, P[o[:hf]], U[o[:hf]], K[o[:hf]], mat); piece(pname + 'b', bone, P[o[hf:]], U[o[hf:]], K[o[hf:]], mat)
            return
        me = bpy.data.meshes.new(pname); nq = len(P)
        me.from_pydata(P.reshape(-1, 3).tolist(), [], np.arange(4 * nq).reshape(nq, 4).tolist())
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        cc = np.repeat(lin(ucol[K]), 4, axis=0)
        ca.data.foreach_set('color', np.concatenate([cc, np.ones((len(cc), 1))], 1).ravel())
        me.color_attributes.active_color = ca
        ul = me.uv_layers.new(name='UVMap'); li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
        ul.data.foreach_set('uv', U.reshape(-1, 2)[li].ravel())
        me.materials.append(mat)
        ob = bpy.data.objects.new(pname, me); sc.collection.objects.link(ob); ob.parent = arm
        vg = ob.vertex_groups.new(name=bone); vg.add(list(range(4 * nq)), 1.0, 'REPLACE')
        ob.modifiers.new('Armature', 'ARMATURE').object = arm; ob.select_set(True)
        pieces.append((pname, bone, 2 * nq))

    for bi, name in enumerate(names):
        own = label == bi
        if not own.any(): continue
        occ = own.copy()
        if parent[name] in names: occ |= (label == names.index(parent[name])) & _dilate6(own)   # 1-brick overlap into the parent
        for kk in np.unique(kind[occ]):
            keys = np.where(occ & (kind == kk), cid, -1)
            P, U, K = _quads(occ, keys, lo)
            if len(P): piece(name if kk == 1 else '%s_glow%d' % (name, kk), name, P, U, K, mb if kk == 1 else gmat(int(kk)))

    glb = os.path.join(OUT, ID + '_rig.glb')
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_yup=True, export_skins=True,
                              export_vertex_color='ACTIVE', export_animations=False, export_apply=False)
    def rb(p): return [round(-p[0] * S, 3), round(p[1] * S, 3), round(p[2] * S, 3)]   # Roblox space after the importer's 180 turn
    info = dict(id=ID, glb=os.path.basename(glb), studs_per_brick=S, max_tris_per_piece=MAX_TRIS,
                note='pivots: roblox = model space in studs after the 3D Importer (Y up, front = -Z); blender = studs in the .glb source scene',
                bones=[dict(name=r[0], parent=r[1], roblox_head=rb(r[2]), roblox_tail=rb(r[3]),
                            blender_head=list(bv(r[2])), blender_tail=list(bv(r[3])),
                            bricks=int((label == i).sum())) for i, r in enumerate(RIG)],
                pieces=[dict(name=p, bone=b, tris=t) for p, b, t in pieces])
    json.dump(info, open(os.path.join(OUT, ID + '_rig.json'), 'w'), indent=1)
    print('RIG_EXPORT', len(RIG), 'bones', len(pieces), 'pieces, max tris', max(t for _, _, t in pieces), '->', glb)
    return verify(glb, RIG, pose or {}, os.path.join(OUT, 'render'), ID, render)


def verify(glb, RIG, pose, ren, ID, render=True):
    """fresh session: import the GLB, check bones + rigid weights, pose, render rest + posed."""
    import bpy
    from mathutils import Vector, Euler
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    sc = bpy.context.scene
    arms = [o for o in sc.objects if o.type == 'ARMATURE']; meshes = [o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]   # skip importer bone-shape helpers
    assert len(arms) == 1, 'expected one armature, got %d' % len(arms)
    arm = arms[0]; want = [r[0] for r in RIG]; got = [b.name for b in arm.data.bones]
    assert sorted(want) == sorted(got), 'bones differ: %s' % (set(want) ^ set(got))
    for r in RIG:
        assert (arm.data.bones[r[0]].parent.name if arm.data.bones[r[0]].parent else None) == r[1], 'parent of ' + r[0]
    bad = 0; tris = 0
    assert meshes, 'no skinned meshes'
    for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: o.hide_render = True
    for o in meshes:
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
        for v in o.data.vertices:
            ws = [g.weight for g in v.groups if g.weight > 0]
            if len(ws) != 1 or abs(ws[0] - 1) > 1e-4: bad += 1
    assert bad == 0, '%d vertices without a single 1.0 weight' % bad
    if render:
        sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
        sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = False; sh.show_cavity = True
        sc.render.resolution_x = sc.render.resolution_y = 900; sc.view_settings.view_transform = 'Standard'
        sc.world = bpy.data.worlds.new('W'); sc.world.color = (.75, .8, .9)
        pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
        mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
        cen = (mn + mx) / 2; size = (mx - mn).length
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.05; cam.data.clip_end = size * 10
        az, el = math.radians(-35), math.radians(18)
        cam.location = cen + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * size * 2
        cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(ren, ID + '_rigrest.png'); bpy.ops.render.render(write_still=True)
        keng = sc.render.engine                                        # textured preview (stud texture x vertex colour)
        sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
        if not any(o.type == 'LIGHT' for o in sc.objects):
            for nm, e, rot in (('Sun', 3.0, (50, 0, -25)), ('Fill', 1.2, (60, 0, 120))):
                L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
                L.data.energy = e; L.rotation_euler = tuple(math.radians(v) for v in rot)
        sc.render.filepath = os.path.join(ren, ID + '_tex.png'); bpy.ops.render.render(write_still=True)
        sc.render.engine = keng
    for b, r in pose.items():
        pb = arm.pose.bones[b]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler([math.radians(v) for v in r])
    bpy.context.view_layer.update()
    if render:
        sc.render.filepath = os.path.join(ren, ID + '_posed.png'); bpy.ops.render.render(write_still=True)
    print('RIG_OK', ID, 'bones', len(got), 'meshes', len(meshes), 'tris', tris, 'posed', list(pose))
    return True
