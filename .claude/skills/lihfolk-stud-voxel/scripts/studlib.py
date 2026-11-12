"""Stud-voxel creature runner (headless Blender).

blender -b --factory-startup --python studlib.py -- <creature.py> [all|render|export|video] [outdir]

The creature file defines (see examples/duck.py):
  NAME, STUDS (studs per metre), PALETTE {key: hex}, GLOW {keys}, BONES [(name, head, tail, parent)],
  HEAD = dict(scale, pivot, bones, offset=(0,0,0)) or None   (those bones' boxes scale round pivot, then move by offset)
  build(K)          K = this module: K.span / K.sym / K.box / K.limb / K.spike ...
  CLIPS {name: (length_frames, fn(frame) -> pose)}
  PREVIEW = dict(target=(x,y,z), ortho=3.0, pitch=14, shots=[('Clip', frame)], loop='Walk')
Axes: metres, Z up, front = -Y, left side = +X.  Pose = {bone: (rx, ry, rz) world-axis degrees, 'root_loc': (x,y,z)}.
"""
import bpy, bmesh, math, json, os, sys, importlib.util
TAU = math.tau
from mathutils import Matrix, Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
STUD_PNG = os.path.join(HERE, '..', 'assets', 'roblox_square_studs.png')   # default Roblox square stud: 8x8 studs per tile, 0.5-grey background
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC = os.path.abspath(argv[0]); MODE = argv[1] if len(argv) > 1 else 'all'
spec = importlib.util.spec_from_file_location('creature', SRC); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
OUT = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.join(os.path.dirname(SRC), 'out', C.NAME)
UVK = C.STUDS / 8                                                   # one texture stud per Roblox stud (8 studs per tile)

def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)

# ---------- chibi head transform ----------
HEAD = getattr(C, 'HEAD', None) or {}
HK = HEAD.get('scale', 1.0); HP = Vector(HEAD.get('pivot', (0, 0, 0))); HEADISH = set(HEAD.get('bones', ()))
HO = Vector(HEAD.get('offset', (0, 0, 0)))                       # optional move (e.g. raise a lowered head in the bind pose)
xf = lambda v: tuple(HP + (Vector(v) - HP) * HK + HO)
BONES = [(n, xf(h), xf(t), p) if n in HEADISH else (n, tuple(h), tuple(t), p) for n, h, t, p in C.BONES]
BI = {b[0]: i for i, b in enumerate(BONES)}

# ---------- scene + rig ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rig = bpy.data.objects.new(C.NAME + 'Rig', bpy.data.armatures.new(C.NAME + 'Rig')); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n, h, t, p in BONES:
    eb = rig.data.edit_bones.new(n); eb.head, eb.tail = h, t
    if p: eb.parent = rig.data.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')

bm = bmesh.new(); dl = bm.verts.layers.deform.verify()
colL = bm.loops.layers.color.new('Col'); glL = bm.loops.layers.color.new('Glow'); uvl = bm.loops.layers.uv.new('UVMap'); nul = bm.loops.layers.uv.new('StudN')
BOXES = []
# eyes never get studs: eye keys (default EY/IR/WH/SH/PU or C.NOSTUD) and glow keys render plain
NOSTUD = set(getattr(C, 'NOSTUD', ('EY', 'IR', 'WH', 'SH', 'PU'))) | set(getattr(C, 'GLOW', ()))

# ---------- primitives (everything is a box owned by ONE bone) ----------
def box(c, s, k, bone, rot=(0, 0, 0), R=None):
    R = R if R is not None else Euler([math.radians(a) for a in rot]).to_matrix()
    if bone in HEADISH: c, s = xf(c), tuple(a * HK for a in s)
    BOXES.append((tuple(c), tuple(s), k, bone, tuple(tuple(r) for r in R), 'Box'))
    # anti z-fight: every later box is a hair bigger (0.2 mm + 0.06 mm per box), so where two boxes share a face plane the
    # later one wins cleanly instead of flickering (shows once the stud texture is on). Export keeps the true size.
    e = 2e-4 + 6e-5 * len(BOXES)
    M = Matrix.Translation(c) @ R.to_4x4() @ Matrix.Diagonal((s[0] + e, s[1] + e, s[2] + e, 1))
    vs = set(bmesh.ops.create_cube(bm, size=1.0, matrix=M)['verts'])
    for v in vs: v[dl][BI[bone]] = 1.0
    col = lin(C.PALETTE[k]); gv = (1, 1, 1, 1) if k in getattr(C, 'GLOW', ()) else (0, 0, 0, 1)
    # STUDS: like the train, one continuous model-wide grid of exact 1x1 studs, so studs carry straight across neighbouring
    # boxes (the face looks like one surface). Axis-aligned boxes sample the shared world grid; tilted boxes can't share it,
    # so they get their own whole, centred 1x1 studs (never stretched; 0.65-1 stud faces get one slightly smaller stud).
    aligned = all(abs(abs(R[r][cc]) - (1.0 if r == cc else 0.0)) < 1e-4 for r in range(3) for cc in range(3))
    Mi = M.inverted(); Ls = [si * C.STUDS for si in s]; nst = [math.floor(L + .35) for L in Ls]
    for f in {f for v in vs for f in v.link_faces}:
        f.normal_update()
        if aligned:
            ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
            for l in f.loops:
                l[colL] = col; l[glL] = gv
                l[uvl].uv = (l.vert.co[a] * C.STUDS + 1000, l.vert.co[b] * C.STUDS + 1000)   # world grid (offset keeps it positive)
                l[nul].uv = (0, 0) if k in NOSTUD else (1e6, 1e6)                              # no clipping on the shared grid (eyes: plain)
            continue
        cl = sum((Mi @ v.co for v in f.verts), Vector()) / 4
        ax = max(range(3), key=lambda i: abs(cl[i])); a, b = [i for i in range(3) if i != ax]
        for l in f.loops:
            lc = Mi @ l.vert.co
            l[colL] = col; l[glL] = gv
            l[uvl].uv = tuple((lc[i] + .5) * nst[i] if nst[i] > Ls[i] else (lc[i] + .5) * Ls[i] - (Ls[i] - nst[i]) / 2 for i in (a, b))
            l[nul].uv = (0, 0) if k in NOSTUD else (nst[a], nst[b])

def _emit(vs_local, faces, Mw, k, bone, shape, c, sz, R):
    """add a custom solid (local unit coords) transformed by Mw; same colour / glow / stud UV rules as box()"""
    BOXES.append((tuple(c), tuple(sz), k, bone, tuple(tuple(r) for r in R), shape))
    vs = [bm.verts.new(Mw @ Vector(v)) for v in vs_local]
    for v in vs: v[dl][BI[bone]] = 1.0
    col = lin(C.PALETTE[k]); gv = (1, 1, 1, 1) if k in getattr(C, 'GLOW', ()) else (0, 0, 0, 1)
    for fi in faces:
        f = bm.faces.new([vs[i] for i in fi]); f.normal_update()
        ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
        for l in f.loops: l[colL] = col; l[glL] = gv; l[uvl].uv = (l.vert.co[a] * C.STUDS, l.vert.co[b] * C.STUDS); l[nul].uv = (0, 0)   # wedges/cylinders: plain (no partial studs)

def wedge(c, s, k, bone, rot=(0, 0, 0), R=None):
    """Ramp (Roblox WedgePart): full height at local +y (back), sloping down to the bottom edge at local -y (front).
    rot turns it: e.g. rot=(0,0,180) slopes down toward the back, (0,0,90) toward +x."""
    R = R if R is not None else Euler([math.radians(a) for a in rot]).to_matrix()
    if bone in HEADISH: c, s = xf(c), tuple(a * HK for a in s)
    Mw = Matrix.Translation(c) @ R.to_4x4() @ Matrix.Diagonal((*s, 1))
    V = [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5), (-.5, .5, .5), (.5, .5, .5)]
    F = [(0, 3, 2, 1), (3, 4, 5, 2), (0, 1, 5, 4), (0, 4, 3), (1, 2, 5)]
    _emit(V, F, Mw, k, bone, 'Wedge', c, s, R)

def cyl(a, b, r, k, bone, seg=10):
    """Cylinder from point a to point b, radius r (Roblox Part.Shape Cylinder, axis = local x)."""
    a, b = Vector(a), Vector(b)
    if bone in HEADISH: a, b, r = Vector(xf(a)), Vector(xf(b)), r * HK
    x = (b - a).normalized(); up = Vector((0, 0, 1)) if abs(x.z) < 0.95 else Vector((0, 1, 0))
    y = up.cross(x).normalized(); z = x.cross(y)
    R = Matrix((x, y, z)).transposed(); c = (a + b) / 2; s = ((b - a).length, 2 * r, 2 * r)
    Mw = Matrix.Translation(c) @ R.to_4x4() @ Matrix.Diagonal((*s, 1))
    V = [(sx, .5 * math.cos(TAU * i / seg), .5 * math.sin(TAU * i / seg)) for sx in (-.5, .5) for i in range(seg)]
    F = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    F += [tuple(reversed(range(seg))), tuple(range(seg, 2 * seg))]
    _emit(V, F, Mw, k, bone, 'Cyl', c, s, R)

def ramp(y0, y1, x0, x1, z0, z1, k, bone, up='back'):
    """Wedge by ranges; the slope rises toward `up` (back = +y, front = -y, left = +x, right = -x)."""
    rz = {'back': 0, 'front': 180, 'left': 90, 'right': -90}[up]
    sx, sy = abs(x1 - x0), abs(y1 - y0)
    if rz in (90, -90): sx, sy = sy, sx
    wedge(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (sx, sy, abs(z1 - z0)), k, bone, rot=(0, 0, rz))

def span(y0, y1, x0, x1, z0, z1, k, bone):
    """Box by ranges: easy to make neighbours touch without overlapping. Args are (y, x, z) order on purpose:
    creatures are built in front-to-back slices."""
    box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), k, bone)

def sym(y0, y1, x0, x1, z0, z1, k, bone):
    """Mirrored pair. Use '%' in the bone name for sided bones: sym(..., 'wing.%')."""
    for sx, s in ((1, 'L'), (-1, 'R')):
        span(y0, y1, x0 * sx, x1 * sx, z0, z1, k, bone.replace('%', s))

def sides():
    """for sx, s in K.sides(): ... -> (1,'L'), (-1,'R')"""
    return ((1, 'L'), (-1, 'R'))

def frame(a, c):
    z = (Vector(c) - Vector(a)).normalized(); up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((0, 1, 0))
    x = up.cross(z).normalized(); return Matrix((x, z.cross(x), z)).transposed()

def limb(a, c, w, d, k, bone, extend=0.0):
    """Box from point a to point c (w x d cross-section). For tails, necks, tentacle segments."""
    a, c = Vector(a), Vector(c)
    box((a + c) / 2, (w, d, (c - a).length + extend), k, bone, R=frame(a, c))

def spike(base, d, L, w, k, tip, bone):
    """Tapering spike/horn: 3 boxes 1 / .66 / .36 wide; tip key on the last one. Base width >= 0.35*size or it reads as a stick."""
    d = Vector(d).normalized(); R = Vector((0, 0, 1)).rotation_difference(d).to_matrix()
    for i, (t0, t1, s) in enumerate(((0, .45, 1), (.45, .75, .66), (.75, 1, .36))):
        box(Vector(base) + d * (L * (t0 + t1) / 2), (w * s, w * s, L * (t1 - t0) + .02), tip if i == 2 else k, bone, R=R)

def stack(y0, y1, w, z0, rows, k_list, bone):
    """Stepped dome/egg: rows = [(half_width_frac, height)] from bottom; each row narrower -> rounded look with steps."""
    z = z0
    for (f, h), k in zip(rows, k_list):
        span(y0, y1, -w * f, w * f, z, z + h, k, bone); z += h
    return z

# ---------- build ----------
C.build(sys.modules[__name__])
me = bpy.data.meshes.new(C.NAME); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new(C.NAME, me); sc.collection.objects.link(ob)
for n, *_ in BONES: ob.vertex_groups.new(name=n)
ob.parent = rig; ob.modifiers.new('Armature', 'ARMATURE').object = rig
# material: vertex colour x the square-stud texture (see below)
mat = bpy.data.materials.new(C.NAME + 'Stud'); mat.use_nodes = True
nt = mat.node_tree; P = nt.nodes['Principled BSDF']; P.inputs['Roughness'].default_value = 0.55
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
uvA = nt.nodes.new('ShaderNodeUVMap'); uvA.uv_map = 'UVMap'
uvN = nt.nodes.new('ShaderNodeUVMap'); uvN.uv_map = 'StudN'
sc8 = nt.nodes.new('ShaderNodeVectorMath'); sc8.operation = 'SCALE'; sc8.inputs['Scale'].default_value = 1 / 8
nt.links.new(uvA.outputs['UV'], sc8.inputs[0])
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); nt.links.new(sc8.outputs['Vector'], tx.inputs['Vector'])
sa = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uvA.outputs['UV'], sa.inputs[0])
sn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uvN.outputs['UV'], sn.inputs[0])
def _m(op, a, b=None):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: nt.links.new(v, m.inputs[i])
    return m.outputs[0]
ins = _m('MULTIPLY', _m('MULTIPLY', _m('GREATER_THAN', sa.outputs['X'], -1e-4), _m('LESS_THAN', _m('SUBTRACT', sa.outputs['X'], sn.outputs['X']), 1e-4)),
         _m('MULTIPLY', _m('GREATER_THAN', sa.outputs['Y'], -1e-4), _m('LESS_THAN', _m('SUBTRACT', sa.outputs['Y'], sn.outputs['Y']), 1e-4)))
gate = nt.nodes.new('ShaderNodeMix'); gate.data_type = 'RGBA'; gate.inputs[6].default_value = (.5, .5, .5, 1)
nt.links.new(ins, gate.inputs['Factor']); nt.links.new(tx.outputs['Color'], gate.inputs[7])
tx.image.colorspace_settings.name = 'Non-Color'
# colour x (2 x texture): 0.5 grey = unchanged, stud shadows darken even PURE WHITE (overlay can't: the white fox lost its studs)
x2 = nt.nodes.new('ShaderNodeVectorMath'); x2.operation = 'SCALE'; x2.inputs['Scale'].default_value = 2.0
nt.links.new(gate.outputs[2], x2.inputs[0])
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
nt.links.new(vc.outputs['Color'], mx.inputs[6]); nt.links.new(x2.outputs['Vector'], mx.inputs[7])
nt.links.new(mx.outputs[2], P.inputs['Base Color'])
gn = nt.nodes.new('ShaderNodeVertexColor'); gn.layer_name = 'Glow'      # GLOW keys emit (preview of Neon)
sep = nt.nodes.new('ShaderNodeMath'); sep.operation = 'MULTIPLY'; sep.inputs[1].default_value = 2.5
nt.links.new(gn.outputs['Color'], sep.inputs[0]); nt.links.new(sep.outputs[0], P.inputs['Emission Strength'])
nt.links.new(vc.outputs['Color'], P.inputs['Emission Color'])
me.materials.append(mat)

# ---------- clips ----------
def apply(p):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        R = Euler([math.radians(a) for a in p.get(pb.name, (0, 0, 0))], 'XYZ').to_matrix()
        B = pb.bone.matrix_local.to_3x3()
        pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()   # world-axis degrees -> local
        pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    r = rig.pose.bones[BONES[0][0]]
    r.location = r.bone.matrix_local.to_3x3().inverted() @ Vector(p.get('root_loc', (0, 0, 0)))

def make(name, length, fn):
    rig.animation_data_create(); act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data.action = act
    apply(fn(0)); bpy.context.view_layer.update()          # depsgraph lags one eval: prime it or frame 0 jumps
    for f in range(0, length + 1, 2):
        apply(fn(f))
        for pb in rig.pose.bones: pb.keyframe_insert('rotation_quaternion', frame=f)
        rig.pose.bones[BONES[0][0]].keyframe_insert('location', frame=f)
    for fc in act.layers[0].strips[0].channelbag(act.slots[0]).fcurves:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    rig.animation_data.action = None

for n, (L, fn) in C.CLIPS.items(): make(C.NAME + '_' + n, L, fn)
os.makedirs(OUT, exist_ok=True)

# ---------- preview renders (Eevee + studs; silhouette mask for post.py outline) ----------
def render_all(video=False):
    PV = getattr(C, 'PREVIEW', {})
    for e in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try: sc.render.engine = e; break
        except TypeError: pass
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.42, 0.55, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.4
    for nm, en, rot in (('Sun', 3.0, (30, 15, -35)), ('Fill', 1.4, (60, 0, 150))):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = en; L.rotation_euler = [math.radians(a) for a in rot]
    gp = bpy.data.meshes.new('G'); gp.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', gp); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gm'); gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.42, 0.2, 1); gp.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = PV.get('ortho', 3.0)
    tgt = Vector(PV.get('target', (0, 0, 1)))
    # scale reference: a grey 9-stud player dummy beside the model (opt-in: PREVIEW player=9; default 0 = none, as in the approved previews)
    dummy = None
    ph = PV.get('player', 0)
    if ph:
        u = ph / 9 / C.STUDS                                           # metres per 'dummy stud' (9-stud character)
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
        gap = min(xs) - 9 * u; dy = min(ys) * 0.55                    # camera side, toward the front
        dm = bpy.data.meshes.new('Dummy'); dbm = bmesh.new()
        for (cx, cz, sx, sy, sz) in ((-1, 2, 1.8, 1.8, 4), (1, 2, 1.8, 1.8, 4), (0, 6, 4, 2, 4), (-3, 6, 1.8, 1.8, 4), (3, 6, 1.8, 1.8, 4), (0, 8.9, 1.9, 1.9, 1.8)):
            bmesh.ops.create_cube(dbm, size=1.0, matrix=Matrix.Translation((gap + cx * u, dy, cz * u)) @ Matrix.Diagonal((sx * u, sy * u, sz * u, 1)))
        dbm.to_mesh(dm); dbm.free(); dummy = bpy.data.objects.new('Dummy', dm); sc.collection.objects.link(dummy)
        dmat = bpy.data.materials.new('Dm'); dmat.use_nodes = True
        dmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.45, 0.47, 0.52, 1); dm.materials.append(dmat)

    def shoot(path, yaw, pitch=PV.get('pitch', 14)):
        d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)),
                    -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))))
        cam.location = tgt + d * 30; cam.data.clip_end = 100
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
        eng = sc.render.engine; g.hide_render = True; sc.render.film_transparent = True
        if dummy: dummy.hide_render = True
        sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'
        sc.render.filepath = path[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
        sc.render.engine = eng; g.hide_render = False; sc.render.film_transparent = False
        if dummy: dummy.hide_render = False

    R = os.path.join(OUT, 'render'); os.makedirs(R, exist_ok=True)
    if video:   # every clip, every 2nd frame (15 fps = real speed), 3/4 view -> post.py makes <Clip>.mp4
        rig.animation_data_create(); sc.render.resolution_x = sc.render.resolution_y = PV.get('video_res', 640)
        for clip, (L, _) in C.CLIPS.items():
            rig.animation_data.action = bpy.data.actions[C.NAME + '_' + clip]
            d = os.path.join(R, 'clips', clip); os.makedirs(d, exist_ok=True)
            for f in range(0, L, 2):
                sc.frame_set(f); shoot(os.path.join(d, f'f{f:03d}.png'), PV.get('video_yaw', -40))
        rig.animation_data.action = None; sc.frame_set(0)
        return
    for nm, yaw in (('front', 0), ('q34', -40), ('side', -90), ('back', 160)):
        shoot(os.path.join(R, f'view_{nm}.png'), yaw)
    rig.animation_data_create()
    for clip, fr in PV.get('shots', ()):
        rig.animation_data.action = bpy.data.actions[C.NAME + '_' + clip]; sc.frame_set(fr)
        shoot(os.path.join(R, f'pose_{clip}_{fr:02d}.png'), -40)
    loop = PV.get('loop')
    if loop:
        L = C.CLIPS[loop][0]; rig.animation_data.action = bpy.data.actions[C.NAME + '_' + loop]
        sc.render.resolution_x = sc.render.resolution_y = 560
        d = os.path.join(R, 'loop'); os.makedirs(d, exist_ok=True)
        for f in range(0, L, 2):
            sc.frame_set(f); shoot(os.path.join(d, f'f{f:03d}.png'), -40)
    rig.animation_data.action = None; sc.frame_set(0)

# ---------- export (Roblox: Data + Clips modules for ModelBuild / ModelAnimator, + json) ----------
def export():
    M = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))          # Blender (x,y,z) -> Roblox (-x, z, y); front -> -Z
    S = C.STUDS; rv = lambda b: M @ Vector(b) * S; r4 = lambda x: round(x, 4)
    J = {'name': C.NAME, 'fps': 30, 'colors': C.PALETTE, 'glow': sorted(getattr(C, 'GLOW', ())), 'bones': [], 'boxes': [], 'order': [], 'clips': {}}
    for b in rig.data.bones:
        J['bones'].append([b.name, b.parent.name if b.parent else None, [r4(a) for a in rv(b.head_local)]])
    for c, s, k, bone, Rb, shape in BOXES:
        if shape == 'Box':
            R = M @ Matrix(Rb); cols = [R.col[i] for i in range(3)]      # same contract as the approved Gatito/Yeti export
            J['boxes'].append([bone, k] + [r4(a) for a in (*(Vector(s) * S), *rv(c), *cols[0], *cols[1], *cols[2])])
        else:   # wedges / cylinders are not symmetric: proper rotation (M R M^T) and local axes (x, z, y)
            R = M @ Matrix(Rb) @ M.transposed(); cols = [R.col[i] for i in range(3)]
            size = Vector((s[0], s[2], s[1])) * S
            J['boxes'].append([bone, k] + [r4(a) for a in (*size, *rv(c), *cols[0], *cols[1], *cols[2])] + [shape])
    ad = rig.animation_data; ad.use_nla = False
    J['order'] = [pb.name for pb in rig.pose.bones]
    n3 = lambda x: float('%.3f' % x) if abs(x) > 0.0005 else 0
    root = rig.pose.bones[BONES[0][0]]
    for name, (L, fn) in C.CLIPS.items():
        ad.action = bpy.data.actions[C.NAME + '_' + name]; keys = []
        for f in range(0, L + 1, 2):
            sc.frame_set(f)
            Q = {pb.name: M @ (pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()).normalized() @ M.transposed() for pb in rig.pose.bones}
            nums = []
            for pb in rig.pose.bones:
                qt = ((Q[pb.parent.name].transposed() @ Q[pb.name]) if pb.parent else Q[pb.name]).to_quaternion()
                nums += [qt.x, qt.y, qt.z, qt.w]
            nums += list(M @ (root.head - root.bone.head_local) * S)
            keys.append([f, [n3(x) for x in nums]])
        J['clips'][name] = {'length': L, 'keys': keys}
    ad.action = None; sc.frame_set(0)
    json.dump(J, open(os.path.join(OUT, C.NAME.lower() + '.json'), 'w', encoding='utf8'), separators=(',', ':'))
    v3 = lambda v: 'Vector3.new(%s)' % ', '.join('%.4f' % a for a in v)
    Ld = ['-- %s (generated by studlib.py; build with ModelBuild)' % C.NAME, 'return {', '\tScale = %g,' % S,
          '\tColors = {' + ', '.join('%s = "%s"' % kv for kv in C.PALETTE.items()) + '},',
          '\tGlow = {' + ', '.join('%s = true' % k for k in sorted(getattr(C, 'GLOW', ()))) + '},', '\tBones = {']
    Ld += ['\t\t{ "%s", %s, %s },' % (b[0], '"%s"' % b[1] if b[1] else 'nil', v3(b[2])) for b in J['bones']]
    Ld += ['\t},', '\tBoxes = {'] + ['\t\t{ "%s", "%s", %s, %s, %s, %s, %s%s },' % (b[0], b[1], v3(b[2:5]), v3(b[5:8]), v3(b[8:11]), v3(b[11:14]), v3(b[14:17]),
           (', "%s"' % b[17]) if len(b) > 17 else '') for b in J['boxes']] + ['\t},', '\tFps = 30,', '}']
    Lc = ['-- %s clips (generated; play with ModelAnimator)' % C.NAME, 'return {', '\tBones = { %s },' % ', '.join('"%s"' % n for n in J['order']), '\tClips = {']
    for name, c in J['clips'].items():
        Lc.append('\t\t%s = { Length = %d, Keys = {' % (name, c['length']))
        Lc += ['\t\t\t{%d,{%s}},' % (f, ','.join(repr(x) for x in v)) for f, v in c['keys']]
        Lc.append('\t\t} },')
    Lc += ['\t},', '}']
    for fn, L in ((C.NAME + 'Data.luau', Ld), (C.NAME + 'Clips.luau', Lc)):
        txt = '\n'.join(L) + '\n'; open(os.path.join(OUT, fn), 'w', encoding='utf8').write(txt)
        if len(txt) > 199000: print('WARNING', fn, len(txt), 'chars > Script.Source cap: split clips per module')

if MODE in ('all', 'render'): render_all()
if MODE == 'video': render_all(video=True)
if MODE in ('all', 'export'): export()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, C.NAME + '.blend'))
tris = sum(len(p.vertices) - 2 for p in me.polygons)
print('STUD_RESULT', C.NAME, len(BOXES), 'boxes', tris, 'tris', len(BONES), 'bones', 'out=' + OUT)
