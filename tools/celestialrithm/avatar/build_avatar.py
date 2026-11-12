"""Build the reproducible blocky R15-proportioned test avatar in headless Blender (bpy).

Original geometry only (boxes, a generic hair block, a drawn face): no Roblox assets, no IP.
Rigged with an armature (one bone per R15 part, rigid weights) and animated with the phase
timeline parsed from lib/celestialrithm/avatar/AuraConfig.luau (idle -> anticipation ->
activation -> peak -> recovery -> settle). Deterministic: no randomness at all.

Exports a cache (.npz) with per-frame evaluated vertices, bone deform matrices, topology, UVs,
camera matrices and Workbench reference alpha masks (used to cross-check the NumPy renderer).

    python3 tools/celestialrithm/avatar/build_avatar.py --out <cache.npz> [--fps 60] [--size 640]
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CONFIG = os.path.join(ROOT, 'lib', 'celestialrithm', 'avatar', 'AuraConfig.luau')

# ---- avatar definition (Blender axes: X = avatar's left, -Y = forward, Z = up; units = studs) ----
# name, bone, size (x, y, z), centre (x, y, z), colour key
PARTS = [
    ('LowerTorso', 'LowerTorso', (2.0, 1.0, 0.40), (0.0, 0.0, 2.20), 'pants'),
    ('UpperTorso', 'UpperTorso', (2.0, 1.0, 1.55), (0.0, 0.0, 3.205), 'shirt'),
    ('Head', 'Head', (1.25, 1.2, 1.15), (0.0, 0.0, 4.60), 'skin'),
    ('Hair', 'Head', (1.37, 1.32, 0.42), (0.0, 0.04, 5.20), 'hair'),
    ('HairBack', 'Head', (1.37, 0.30, 0.80), (0.0, 0.55, 4.82), 'hair'),
    ('LeftUpperArm', 'LeftUpperArm', (0.92, 0.95, 1.05), (1.48, 0.0, 3.43), 'shirt'),
    ('LeftLowerArm', 'LeftLowerArm', (0.88, 0.9, 0.85), (1.48, 0.0, 2.45), 'skin'),
    ('LeftHand', 'LeftHand', (0.84, 0.86, 0.32), (1.48, 0.0, 1.85), 'skin'),
    ('RightUpperArm', 'RightUpperArm', (0.92, 0.95, 1.05), (-1.48, 0.0, 3.43), 'shirt'),
    ('RightLowerArm', 'RightLowerArm', (0.88, 0.9, 0.85), (-1.48, 0.0, 2.45), 'skin'),
    ('RightHand', 'RightHand', (0.84, 0.86, 0.32), (-1.48, 0.0, 1.85), 'skin'),
    ('LeftUpperLeg', 'LeftUpperLeg', (0.96, 0.96, 0.95), (0.5, 0.0, 1.50), 'pants'),
    ('LeftLowerLeg', 'LeftLowerLeg', (0.94, 0.94, 0.80), (0.5, 0.0, 0.62), 'pants'),
    ('LeftFoot', 'LeftFoot', (0.96, 1.12, 0.24), (0.5, -0.07, 0.12), 'shoe'),
    ('RightUpperLeg', 'RightUpperLeg', (0.96, 0.96, 0.95), (-0.5, 0.0, 1.50), 'pants'),
    ('RightLowerLeg', 'RightLowerLeg', (0.94, 0.94, 0.80), (-0.5, 0.0, 0.62), 'pants'),
    ('RightFoot', 'RightFoot', (0.96, 1.12, 0.24), (-0.5, -0.07, 0.12), 'shoe'),
]
COLORS = {  # sRGB, stylised and generic
    'skin': '#f2c48d', 'shirt': '#3f6fd8', 'pants': '#2c3344', 'shoe': '#eef0f4', 'hair': '#3a2a22',
}
# bone, joint position (head), parent
BONES = [
    ('Root', (0.0, 0.0, 2.0), None),
    ('LowerTorso', (0.0, 0.0, 2.0), 'Root'),
    ('UpperTorso', (0.0, 0.0, 2.42), 'LowerTorso'),
    ('Head', (0.0, 0.0, 3.99), 'UpperTorso'),
    ('LeftUpperArm', (1.48, 0.0, 3.85), 'UpperTorso'),
    ('LeftLowerArm', (1.48, 0.0, 2.90), 'LeftUpperArm'),
    ('LeftHand', (1.48, 0.0, 2.02), 'LeftLowerArm'),
    ('RightUpperArm', (-1.48, 0.0, 3.85), 'UpperTorso'),
    ('RightLowerArm', (-1.48, 0.0, 2.90), 'RightUpperArm'),
    ('RightHand', (-1.48, 0.0, 2.02), 'RightLowerArm'),
    ('LeftUpperLeg', (0.5, 0.0, 1.98), 'LowerTorso'),
    ('LeftLowerLeg', (0.5, 0.0, 1.03), 'LeftUpperLeg'),
    ('LeftFoot', (0.5, 0.0, 0.23), 'LeftLowerLeg'),
    ('RightUpperLeg', (-0.5, 0.0, 1.98), 'LowerTorso'),
    ('RightLowerLeg', (-0.5, 0.0, 1.03), 'RightUpperLeg'),
    ('RightFoot', (-0.5, 0.0, 0.23), 'RightLowerLeg'),
]
# Euler degrees in armature axes (X right-hand: + tilts a hanging limb backward / an upright one forward)
# Y: + swings a hanging limb toward -X (avatar's right). Root carries a z offset in 'lift'.
POSES = {
    'idle': {
        'LeftUpperArm': (0, -6, 0), 'RightUpperArm': (0, 6, 0),
        'LeftLowerArm': (-8, 0, 0), 'RightLowerArm': (-8, 0, 0),
        'lift': 0.0,
    },
    'crouch': {
        'UpperTorso': (14, 0, 0), 'Head': (6, 0, 0),
        'LeftUpperArm': (28, -14, 0), 'RightUpperArm': (28, 14, 0),
        'LeftLowerArm': (-82, 0, 0), 'RightLowerArm': (-82, 0, 0),
        'LeftHand': (-10, 0, 0), 'RightHand': (-10, 0, 0),
        'LeftUpperLeg': (-36, -4, 0), 'RightUpperLeg': (-36, 4, 0),
        'LeftLowerLeg': (70, 0, 0), 'RightLowerLeg': (70, 0, 0),
        'LeftFoot': (-34, 0, 0), 'RightFoot': (-34, 0, 0),
        'lift': -0.32,
    },
    'power': {
        'UpperTorso': (-7, 0, 0), 'Head': (-4, 0, 0),
        'LeftUpperArm': (-12, -128, 0), 'RightUpperArm': (-12, 128, 0),
        'LeftLowerArm': (0, -14, 0), 'RightLowerArm': (0, 14, 0),
        'LeftUpperLeg': (-4, -7, 0), 'RightUpperLeg': (4, 7, 0),
        'LeftLowerLeg': (10, 0, 0), 'RightLowerLeg': (14, 0, 0),
        'LeftFoot': (18, 0, 0), 'RightFoot': (16, 0, 0),
        'lift': 0.28,
    },
}

CAMERA = {'location': (-4.6, -12.2, 3.9), 'target': (0.0, 0.0, 3.0), 'lens': 50.0, 'sensor': 36.0}


def parse_phases(path=CONFIG):
    """Read the phase rows from AuraConfig.luau so the animation and the Luau timeline stay in sync."""
    rows = []
    pat = re.compile(r'\{\s*name\s*=\s*"(\w+)",\s*duration\s*=\s*([\d.]+),\s*intensity\s*=\s*\{\s*([\d.]+),\s*([\d.]+)\s*\},'
                     r'\s*shell\s*=\s*\{\s*([\d.]+),\s*([\d.]+)\s*\},\s*orbit\s*=\s*\{\s*([\d.]+),\s*([\d.]+)\s*\},\s*ease\s*=\s*"(\w+)"')
    for m in pat.finditer(open(path).read()):
        rows.append({'name': m.group(1), 'duration': float(m.group(2)),
                     'intensity': (float(m.group(3)), float(m.group(4))),
                     'shell': (float(m.group(5)), float(m.group(6))),
                     'orbit': (float(m.group(7)), float(m.group(8))), 'ease': m.group(9)})
    assert [r['name'] for r in rows] == ['idle', 'anticipation', 'activation', 'peak', 'recovery', 'settle'], rows
    t = 0.0
    for r in rows:
        r['start'] = t
        t += r['duration']
        r['end'] = t
    return rows


def ease(name, a):
    a = min(max(a, 0.0), 1.0)
    if name == 'inCubic':
        return a ** 3
    if name == 'outCubic':
        return 1 - (1 - a) ** 3
    if name == 'inOutSine':
        return 0.5 - 0.5 * math.cos(math.pi * a)
    if name == 'outBack':
        u = a - 1
        return 1 + 2.70158 * u ** 3 + 1.70158 * u ** 2
    return a


def pose_at(t, phases):
    """Returns ({bone: (rx, ry, rz) degrees}, root lift) for time t (seconds)."""
    ph = {r['name']: r for r in phases}

    def get(p, b):
        return np.array(POSES[p].get(b, (0, 0, 0)), float)

    def blend(pa, pb, w):
        out = {b: get(pa, b) * (1 - w) + get(pb, b) * w for b, _, _ in BONES}
        return out, POSES[pa]['lift'] * (1 - w) + POSES[pb]['lift'] * w

    breathe = math.sin(2 * math.pi * 0.45 * t)
    if t < ph['anticipation']['start']:
        rot, lift = blend('idle', 'idle', 0)
    elif t < ph['activation']['start']:
        r = ph['anticipation']
        rot, lift = blend('idle', 'crouch', ease('inOutSine', (t - r['start']) / r['duration']))
    elif t < ph['peak']['start']:
        r = ph['activation']
        rot, lift = blend('crouch', 'power', ease('outBack', (t - r['start']) / r['duration']))
    elif t < ph['recovery']['start']:
        r = ph['peak']
        rot, lift = blend('power', 'power', 0)
        lift += 0.06 * math.sin(2 * math.pi * 0.9 * (t - r['start']))
        for b in ('LeftUpperArm', 'RightUpperArm'):
            rot[b] = rot[b] + np.array([0, 4 * math.sin(2 * math.pi * 0.9 * (t - r['start'])) * (1 if b[0] == 'R' else -1), 0])
    elif t < ph['settle']['start']:
        r = ph['recovery']
        a = (t - r['start']) / r['duration']
        rot, lift = blend('power', 'idle', ease('inOutSine', a))
        lift -= 0.10 * math.sin(math.pi * min(max((a - 0.55) / 0.45, 0), 1))   # small landing dip
    else:
        rot, lift = blend('idle', 'idle', 0)
    # idle breathing everywhere it is calm (fades out under the big poses)
    calm = 1.0 if (t < ph['anticipation']['start'] or t >= ph['settle']['start']) else 0.0
    rot['UpperTorso'] = rot['UpperTorso'] + np.array([1.5 * breathe * calm, 0, 0])
    rot['Head'] = rot['Head'] + np.array([-1.0 * breathe * calm, 0, 1.5 * math.sin(2 * math.pi * 0.2 * t) * calm])
    lift += 0.02 * breathe * calm
    return rot, lift


def box(size, centre):
    sx, sy, sz = (s / 2 for s in size)
    cx, cy, cz = centre
    v = [(cx + x * sx, cy + y * sy, cz + z * sz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    # index = (x>0)*4 + (y>0)*2 + (z>0); quads wound outward; each quad's UV origin bottom-left as seen from outside
    faces = {
        '-Y': (0, 4, 5, 1), '+Y': (6, 2, 3, 7), '-X': (2, 0, 1, 3),
        '+X': (4, 6, 7, 5), '+Z': (1, 5, 7, 3), '-Z': (2, 6, 4, 0),
    }
    return v, faces


def build(args):
    import bpy
    from mathutils import Euler, Matrix, Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    phases = parse_phases()
    total = phases[-1]['end']
    nframes = int(round(total * args.fps))
    scene.render.fps = args.fps
    scene.frame_start, scene.frame_end = 0, nframes - 1

    # --- mesh ---
    verts, quads, quad_part, quad_side = [], [], [], []
    for pi, (name, bone, size, centre, col) in enumerate(PARTS):
        v, faces = box(size, centre)
        base = len(verts)
        verts += v
        for side, q in faces.items():
            quads.append(tuple(base + i for i in q))
            quad_part.append(pi)
            quad_side.append(side)
    me = bpy.data.meshes.new('AvatarMesh')
    me.from_pydata(verts, [], quads)
    me.update()
    uv = me.uv_layers.new(name='UV')
    for poly in me.polygons:
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[k]
    mats = {}
    for key, hexc in COLORS.items():
        m = bpy.data.materials.new(key)
        c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        m.diffuse_color = (*[(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c], 1)
        me.materials.append(m)
        mats[key] = len(me.materials) - 1
    for poly, pi in zip(me.polygons, quad_part):
        poly.material_index = mats[PARTS[pi][4]]
    obj = bpy.data.objects.new('Avatar', me)
    scene.collection.objects.link(obj)
    for name, bone, *_ in PARTS:
        if bone not in obj.vertex_groups:
            obj.vertex_groups.new(name=bone)
    for pi, (name, bone, *_ ) in enumerate(PARTS):
        obj.vertex_groups[bone].add(list(range(pi * 8, pi * 8 + 8)), 1.0, 'REPLACE')

    # --- armature: every bone points along +Y with roll 0, so rest orientation = identity ---
    arm = bpy.data.armatures.new('Rig')
    rig = bpy.data.objects.new('Rig', arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name, head, parent in BONES:
        eb = arm.edit_bones.new(name)
        eb.head = head
        eb.tail = (head[0], head[1] + 0.3, head[2])
        eb.roll = 0
        if parent:
            eb.parent = arm.edit_bones[parent]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    obj.parent = rig

    # --- animation: keyframe every frame from the procedural pose ---
    action_t0 = time.time()
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    for f in range(nframes):
        t = f / args.fps
        rot, lift = pose_at(t, phases)
        for pb in rig.pose.bones:
            e = rot.get(pb.name, np.zeros(3))
            pb.rotation_quaternion = Euler([math.radians(a) for a in e], 'XYZ').to_quaternion()
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if pb.name == 'Root':
                pb.location = (0, 0, lift)   # bone-local axes == armature axes (identity rest)
                pb.keyframe_insert('location', frame=f)
    action_s = time.time() - action_t0

    # --- camera + light (Workbench reference only) ---
    cam_data = bpy.data.cameras.new('Cam')
    cam_data.lens, cam_data.sensor_width = CAMERA['lens'], CAMERA['sensor']
    cam = bpy.data.objects.new('Cam', cam_data)
    scene.collection.objects.link(cam)
    cam.location = CAMERA['location']
    d = Vector(CAMERA['target']) - Vector(CAMERA['location'])
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.film_transparent = True
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.render_aa = 'OFF'
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    proj = np.array(cam.calc_matrix_camera(depsgraph, x=args.size, y=args.size))
    view = np.array(cam.matrix_world.inverted())

    # --- export per-frame evaluated geometry + deform matrices ---
    bone_names = [b[0] for b in BONES]
    V = len(verts)
    pos = np.zeros((nframes, V, 3), np.float32)
    deform = np.zeros((nframes, len(bone_names), 4, 4), np.float32)
    ex_t0 = time.time()
    for f in range(nframes):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        m = ev.to_mesh()
        co = np.zeros(V * 3, np.float32)
        m.vertices.foreach_get('co', co)
        mw = np.array(ev.matrix_world, np.float32)
        p = co.reshape(V, 3)
        pos[f] = p @ mw[:3, :3].T + mw[:3, 3]
        ev.to_mesh_clear()
        for bi, bn in enumerate(bone_names):
            pb = rig.pose.bones[bn]
            deform[f, bi] = np.array(rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted(), np.float32)
    export_s = time.time() - ex_t0

    # --- Workbench reference masks at a few frames ---
    ref_frames = [int(nframes * x) for x in (0.05, 0.27, 0.36, 0.5, 0.75)]
    ref = np.zeros((len(ref_frames), args.size, args.size), np.uint8)
    wb_times = []
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.out)), '_wb_ref.png')
    for k, f in enumerate(ref_frames):
        scene.frame_set(f)
        scene.render.filepath = tmp
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        wb_times.append(time.time() - t0)
        from PIL import Image
        ref[k] = np.array(Image.open(tmp).convert('RGBA'))[:, :, 3]
    if os.path.exists(tmp):
        os.remove(tmp)
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))

    tris, tri_uv, tri_part, tri_side = [], [], [], []
    quad_uv = ((0, 0), (1, 0), (1, 1), (0, 1))
    for q, pi, side in zip(quads, quad_part, quad_side):
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            tris.append((q[a], q[b], q[c]))
            tri_uv.append((quad_uv[a], quad_uv[b], quad_uv[c]))
            tri_part.append(pi)
            tri_side.append(side)
    bind = np.array(verts, np.float32)
    np.savez_compressed(
        args.out, fps=args.fps, size=args.size, pos=pos, deform=deform, bind=bind,
        tris=np.array(tris, np.int32), tri_uv=np.array(tri_uv, np.float32), tri_part=np.array(tri_part, np.int32),
        tri_side=np.array(tri_side), part_names=np.array([p[0] for p in PARTS]),
        part_bone=np.array([bone_names.index(p[1]) for p in PARTS], np.int32),
        part_color=np.array([p[4] for p in PARTS]), part_size=np.array([p[2] for p in PARTS], np.float32),
        part_centre=np.array([p[3] for p in PARTS], np.float32), bone_names=np.array(bone_names),
        bone_heads=np.array([b[1] for b in BONES], np.float32),
        proj=proj.astype(np.float64), view=view.astype(np.float64), cam_loc=np.array(CAMERA['location'], np.float64),
        ref_frames=np.array(ref_frames, np.int32), ref_masks=ref,
        timing=np.array([action_s, export_s, float(np.mean(wb_times))]),
        blender=np.array(bpy.app.version_string),
    )
    print(f'frames={nframes} verts={V} tris={len(tris)} keyframing={action_s:.1f}s export={export_s:.1f}s '
          f'workbench={np.mean(wb_times):.2f}s/frame -> {args.out}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--size', type=int, default=640)
    ap.add_argument('--blend', default='', help='optional path to save the .blend')
    args = ap.parse_args()
    build(args)


if __name__ == '__main__':
    sys.exit(main())
