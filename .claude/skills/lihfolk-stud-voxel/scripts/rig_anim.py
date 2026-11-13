"""Render motion clips from an exported rig: a fast way to try animations before building them in Studio.

    python3 scripts/rig_anim.py <ID_rig.glb> <out.mp4> [clips=walk,charge,idle] [res=480] [engine=workbench|eevee]

Imports the GLB that brick_rig.export wrote, poses its bones per frame and renders. `workbench` (default) draws the
vertex colours with flat studio light in about a second a frame, so motion can be iterated; `eevee` is the slow,
textured look. Bones a rig does not have are skipped, so quadruped clips also run on other rigs with less motion.
Writes <out>.mp4 and <out>.gif. These are motion studies, not shipped animations.

Clips (each is fn(u) with u in 0..1 over the loop -> {bone: (rx, ry, rz)} in degrees, plus 'root_y' lift in bricks):
  walk    four-beat walk: each foot swings forward fast (30 % of the cycle) and pushes back slowly (70 %), hind before
          fore on each side; body bobs twice a cycle, hips and spine counter-roll, head and tail lag behind
  charge  anticipation (rear back, head up, front foot paws), a fast lunge with the head down, then a decaying settle
  idle    slow breathing, a head turn, tail flick
"""
import os, sys, math, subprocess, tempfile
import bpy
from mathutils import Vector, Euler

glb, out = sys.argv[1], sys.argv[2]
CLIPS = (sys.argv[3] if len(sys.argv) > 3 else 'walk,charge,idle').split(',')
RES = int(sys.argv[4]) if len(sys.argv) > 4 else 480
ENGINE = sys.argv[5] if len(sys.argv) > 5 else 'workbench'
TAU = 2 * math.pi


def swing(u):
    """leg angle over one cycle, -1..1: slow push back for 70 %, quick swing forward for 30 %"""
    u %= 1.0
    return 1 - 2 * (u / .7) if u < .7 else -1 + 2 * (.5 - .5 * math.cos(math.pi * (u - .7) / .3))


def lift(u):
    """knee bend, 0..1: only while the foot swings forward"""
    u %= 1.0
    return math.sin(math.pi * (u - .7) / .3) if u >= .7 else 0.0


def walk(u):
    p = {}
    for leg, ph in (('legBL', 0.0), ('legFL', .25), ('legBR', .5), ('legFR', .75)):
        p[leg + '_up'] = (17 * swing(u + ph), 0, 0); p[leg + '_low'] = (-26 * lift(u + ph), 0, 0)
    bob = math.sin(2 * TAU * u)
    p['hips'] = (1.5 * bob, 0, 3.0 * math.sin(TAU * u)); p['spine'] = (-1.0 * bob, 0, -2.2 * math.sin(TAU * u))
    p['neck'] = (3 * math.sin(2 * TAU * u - .9), 0, 0); p['head'] = (4 + 4 * math.sin(2 * TAU * u - 1.5), 0, 0)
    p['jaw'] = (4, 0, 0); p['tail'] = (0, 0, 18 * math.sin(TAU * u - 1.2))
    p['root_y'] = .5 * (1 - abs(bob))
    return p


def charge(u):
    ease = lambda a, b, x: min(1.0, max(0.0, (x - a) / (b - a)))
    ant = math.sin(math.pi / 2 * ease(0, .38, u))                       # wind-up
    hit = ease(.38, .5, u) ** 2                                          # fast lunge
    k = max(0.0, u - .5); settle = math.exp(-7 * k) * math.cos(TAU * 3 * k) if u >= .5 else 1.0
    lean = -7 * ant * (1 - hit) + 9 * hit * settle
    paw = math.sin(TAU * 2.5 * u) if u < .38 else 0.0
    p = {'spine': (lean, 0, 0), 'hips': (-lean * .5, 0, 0), 'neck': (-10 * ant * (1 - hit) + 16 * hit * settle, 0, 0),
         'head': (-12 * ant * (1 - hit) + 30 * hit * settle, 0, 0), 'jaw': (4 + 22 * hit * settle, 0, 0),
         'tail': (0, 0, 10 * math.sin(TAU * 2 * u) * (1 - hit) + 0), 'legFL_up': (22 * max(0, paw), 0, 0), 'legFL_low': (-30 * max(0, paw), 0, 0),
         'legFR_up': (-14 * hit * settle, 0, 0), 'legBL_up': (12 * hit * settle, 0, 0), 'legBR_up': (12 * hit * settle, 0, 0)}
    p['root_y'] = -.8 * ant * (1 - hit)
    return p


def idle(u):
    br = math.sin(TAU * u)
    return {'spine': (1.2 * br, 0, 0), 'neck': (1.5 * br, 6 * math.sin(TAU * u - .6), 0), 'head': (3 + 2 * br, 9 * math.sin(TAU * u - 1.0), 0),
            'jaw': (3 + 2 * max(0, br), 0, 0), 'tail': (0, 0, 14 * math.sin(2 * TAU * u) * max(0, math.sin(TAU * u))), 'root_y': .25 * br}


FRAMES = dict(walk=24, charge=30, idle=20); FN = dict(walk=walk, charge=charge, idle=idle)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: o.hide_render = True
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
cen = (mn + mx) / 2; size = (mx - mn).length
sc.render.resolution_x = sc.render.resolution_y = RES; sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W'); sc.world.color = (.62, .7, .78)
me = bpy.data.meshes.new('G'); s = size * 20
me.from_pydata([(-s, -s, mn.z), (s, -s, mn.z), (s, s, mn.z), (-s, s, mn.z)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g); g.color = (.3, .44, .26, 1)
if ENGINE == 'eevee':
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for nm, e, r in (('Sun', 3.0, (50, 0, -25)), ('Fill', 1.4, (60, 0, 120)), ('Back', .8, (60, 0, 200))):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.rotation_euler = tuple(math.radians(v) for v in r)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = g.color; me.materials.append(gm)
else:
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = True; sh.show_cavity = True; sh.shadow_intensity = .35
    g.hide_render = True                                                # vertex-colour mode would draw the ground white
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.0; cam.data.clip_end = size * 10
az, el = math.radians(-42), math.radians(13)
cam.location = cen + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * size * 2
cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()

names = {b.name for b in arm.pose.bones}
tmp = tempfile.mkdtemp(); k = 0
for clip in CLIPS:
    N = FRAMES[clip]
    for rep in range(2 if clip != 'charge' else 1):                     # loops play twice, the attack once
        for f in range(N):
            pose = FN[clip](f / N)
            for b in names:
                pb = arm.pose.bones[b]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler([math.radians(v) for v in pose.get(b, (0, 0, 0))])
            if 'root' in names: arm.pose.bones['root'].location = Vector((0, pose.get('root_y', 0.0), 0))
            bpy.context.view_layer.update()
            sc.render.filepath = os.path.join(tmp, 'f%04d.png' % k); bpy.ops.render.render(write_still=True); k += 1
pat = os.path.join(tmp, 'f%04d.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '15', '-i', pat, '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', out], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '15', '-i', pat, '-vf', 'split[a][b];[a]palettegen[p];[b][p]paletteuse', os.path.splitext(out)[0] + '.gif'], check=True)
print('ANIM_OK', k, 'frames', CLIPS, '->', out)
