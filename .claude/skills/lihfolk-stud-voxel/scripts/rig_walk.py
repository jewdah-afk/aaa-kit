"""Render a walk loop from an exported rig, to check that the model holds together when it moves.

    python3 scripts/rig_walk.py <ID_rig.glb> <out.mp4> [frames=16] [res=480]      (needs bpy + ffmpeg)

Imports the GLB that brick_rig.export wrote (bones, vertex colours x stud texture), poses the bones per frame with a
simple quadruped walk (diagonal leg pairs, head bob, jaw, tail sway; walks in place) and renders each frame in EEVEE.
Bones it does not find are skipped, so it also runs on bipeds and tentacle rigs, just with less motion.
Also writes <out>.gif. This is a motion check, not a shipped animation: the game animates the rig in Studio.
"""
import os, sys, math, subprocess, tempfile
import bpy
from mathutils import Vector, Euler

glb, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 16
RES = int(sys.argv[4]) if len(sys.argv) > 4 else 480

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: o.hide_render = True
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
cen = (mn + mx) / 2; size = (mx - mn).length

sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = sc.render.resolution_y = RES; sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W'); sc.world.color = (.75, .8, .9)
for nm, e, rot in (('Sun', 3.0, (50, 0, -25)), ('Fill', 1.4, (60, 0, 120)), ('Back', .8, (60, 0, 200))):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
    L.data.energy = e; L.rotation_euler = tuple(math.radians(v) for v in rot)
me = bpy.data.meshes.new('G'); s = size * 20
me.from_pydata([(-s, -s, mn.z), (s, -s, mn.z), (s, s, mn.z), (-s, s, mn.z)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
gm = bpy.data.materials.new('Gnd'); gm.diffuse_color = (.26, .4, .2, 1); me.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * .95; cam.data.clip_end = size * 10
az, el = math.radians(-40), math.radians(14)
cam.location = cen + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * size * 2
cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()

names = {b.name for b in arm.pose.bones}
def rot(b, rx=0, ry=0, rz=0):
    if b in names:
        pb = arm.pose.bones[b]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler([math.radians(v) for v in (rx, ry, rz)])

tmp = tempfile.mkdtemp()
for f in range(N):
    t = 2 * math.pi * f / N; s1 = math.sin(t); s2 = math.sin(t + math.pi)
    for up, ph in (('legFL', s1), ('legBR', s1), ('legFR', s2), ('legBL', s2)):       # diagonal pairs
        rot(up + '_up', 24 * ph); rot(up + '_low', -16 * max(0.0, -ph) - 4)
    rot('head', 5 * math.sin(2 * t) + 4); rot('jaw', 6 + 5 * math.sin(2 * t + 1)); rot('neck', 3 * math.sin(2 * t + .6))
    rot('spine', 0, 0, 2.0 * s1); rot('hips', 0, 0, -2.5 * s1); rot('tail', 0, 0, 16 * math.sin(t - .8))
    if 'root' in names: arm.pose.bones['root'].location = Vector((0, .6 * abs(math.sin(t)), 0))
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(tmp, 'f%03d.png' % f); bpy.ops.render.render(write_still=True)
pat = os.path.join(tmp, 'f%03d.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-stream_loop', '3', '-framerate', '12', '-i', pat, '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', out], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', pat, '-vf', 'split[a][b];[a]palettegen[p];[b][p]paletteuse', os.path.splitext(out)[0] + '.gif'], check=True)
print('WALK_OK', N, 'frames ->', out)
