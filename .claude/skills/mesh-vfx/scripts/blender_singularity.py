"""Void Singularity (ultimate, tier 1) in headless Blender Cycles.
Real gravitational-lens look: a sphere with Refraction BSDF IOR 0.72 (below 1) bends the starfield behind it into an Einstein ring,
around a pure-black event horizon. Plus a spinning flame accretion disc (inner hot, outer crimson), a photon ring,
twin polar jets, and debris that spirals in, stretches (spaghettification) and vanishes at the horizon.
Timeline (s): pull 0-0.4, collapse-flash 0.4-0.5, feed 0.5-2.0, detonate 2.0-2.4.
  bpyenv/bin/python blender_singularity.py -- OUT [frames=72] [size=400]"""
import sys, os, math, random
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/sing'; FRAMES = int(argv[1]) if len(argv) > 1 else 72; SIZE = int(argv[2]) if len(argv) > 2 else 400
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import meshgen
from bvfx import to_blender, flame_material, solid
scene = bpy.context.scene; rnd = random.Random(9)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 24; scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8; scene.cycles.transmission_bounces = 8
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.003, 0.002, 0.008, 1)
C = (0, 0, 7)  # singularity centre, above the player

def zup(m): m.v = [(x, -z, y) for x, y, z in m.v]; return m

# starfield + nebula wall behind, so the lens has something to bend
star = solid('star', (0.8, 0.85, 1), 30)
for i in range(260):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.02, 0.06), location=(rnd.uniform(-30, 30), rnd.uniform(18, 26), rnd.uniform(-4, 26)))
    bpy.context.active_object.data.materials.append(star)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 28, 10), rotation=(math.radians(90), 0, 0))
neb, nmap = flame_material('neb', (0.25, 0.03, 0.12), 0.6); bpy.context.active_object.data.materials.append(neb)
bpy.context.active_object.data.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
for c in bpy.context.active_object.data.color_attributes['Mask'].data: c.color = (1, 1, 1, 1)
bpy.ops.mesh.primitive_circle_add(radius=40, fill_type='NGON'); bpy.context.active_object.data.materials.append(solid('floor', (0.02, 0.012, 0.02), 0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=5, location=(0, 0, 2.5)); bpy.context.active_object.data.materials.append(solid('fig', (0.01, 0.008, 0.012), 0))

# lens: refraction IOR < 1 -> rays bend outward -> background smears into a ring around the horizon
lens_m = bpy.data.materials.new('lens'); lens_m.use_nodes = True; N = lens_m.node_tree.nodes
for n in list(N): N.remove(n)
rf = N.new('ShaderNodeBsdfRefraction'); rf.inputs['IOR'].default_value = 0.72; rf.inputs['Roughness'].default_value = 0.0
o = N.new('ShaderNodeOutputMaterial'); lens_m.node_tree.links.new(rf.outputs[0], o.inputs['Surface'])
bpy.ops.mesh.primitive_uv_sphere_add(radius=3.2, segments=64, ring_count=32, location=C); lens = bpy.context.active_object
lens.data.materials.append(lens_m); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.25, segments=48, ring_count=24, location=C); horizon = bpy.context.active_object
horizon.data.materials.append(solid('void', (0, 0, 0), 0)); bpy.ops.object.shade_smooth()
# photon ring (thin, white-hot) + accretion disc (two flame layers, counter-scrolling)
bpy.ops.mesh.primitive_torus_add(major_radius=1.4, minor_radius=0.04, location=C); photon = bpy.context.active_object
photon.data.materials.append(solid('photon', (1, 0.9, 0.85), 80))
tilt = (math.radians(14), 0, math.radians(8))  # near edge-on: the disc's far side lenses over the top
d_hot, hmap = flame_material('dhot', (1, 0.45, 0.3), 30); d_out, omap = flame_material('dout', (1, 0.04, 0.09), 18)
disc_in = to_blender(zup(meshgen.shockwave(64, 6, 1.5, 3.2, tiles=3)), 'disc_in'); disc_in.data.materials.append(d_hot)
disc_out = to_blender(zup(meshgen.shockwave(64, 6, 2.6, 6.0, tiles=4)), 'disc_out'); disc_out.data.materials.append(d_out)
for d in (disc_in, disc_out, photon): d.location = C; d.rotation_euler = tilt
# polar jets
jets = []
jm, jmap = flame_material('jet', (0.9, 0.3, 1.0), 25)
for sgn in (1, -1):
    j = to_blender(zup(meshgen.vortex(16, 16, 9, 0.25, 0.9, 500 * sgn)), f'jet{sgn}'); j.data.materials.append(jm)
    j.location = C; j.rotation_euler = (tilt[0] + (0 if sgn > 0 else math.pi), 0, tilt[2]); jets.append(j)
# infalling debris + sparks
debs = []
dm = solid('deb', (0.15, 0.03, 0.04), 3)
for i in range(14):
    o = to_blender(meshgen.debris(i + 3, rnd.uniform(0.3, 0.7)), f'deb{i}'); o.data.materials.append(dm)
    o['a'] = rnd.uniform(0, 6.283); o['r0'] = rnd.uniform(7, 12); o['d'] = rnd.uniform(0, 1.2); o['z'] = rnd.uniform(-1.5, 1.5); debs.append(o)
sp = solid('sp', (1, 0.6, 0.4), 60); sparks = []
for i in range(80):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.05); o = bpy.context.active_object; o.data.materials.append(sp)
    o['a'] = rnd.uniform(0, 6.283); o['r'] = rnd.uniform(1.6, 6); o['w'] = rnd.uniform(0.8, 1.6); sparks.append(o)
frame = bpy.data.objects.new('frame', None); scene.collection.objects.link(frame); frame.location = C; frame.rotation_euler = tilt
for o in debs + sparks: o.parent = frame
lt = bpy.data.lights.new('l', 'POINT'); lt.color = (1, 0.25, 0.3); lo = bpy.data.objects.new('l', lt); lo.location = (0, -3, 5); scene.collection.objects.link(lo)
bpy.ops.object.camera_add(location=(0, -24, 8.5)); cam = bpy.context.active_object; scene.camera = cam; cam.data.lens = 32
aim = bpy.data.objects.new('aim', None); scene.collection.objects.link(aim); aim.location = (0, 0, 6)
tc = cam.constraints.new('TRACK_TO'); tc.target = aim; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
try:
    tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); scene.compositing_node_group = tree
    rl = tree.nodes.new('CompositorNodeRLayers'); gl = tree.nodes.new('CompositorNodeGlare'); out = tree.nodes.new('NodeGroupOutput')
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    gl.inputs['Type'].default_value = 'Fog Glow'; tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], out.inputs[0])
except Exception as e: print('bloom skipped:', e)

def seg(t, a, d): return min(1, max(0, (t - a) / d))
def eo(t): return 1 - (1 - t) ** 4
PULL, FLASH, FEED, DET = 0.4, 0.5, 2.0, 2.4
def rot_tilt(v):  # put a disc-plane point into the tilted frame
    x, y, z = v; ax, _, az = tilt
    y, z = y * math.cos(ax - math.pi / 2) - z * math.sin(ax - math.pi / 2), y * math.sin(ax - math.pi / 2) + z * math.cos(ax - math.pi / 2)
    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
    return (x + C[0], y + C[1], z + C[2])
for f in range(FRAMES):
    t = f / 30
    form = eo(seg(t, 0, PULL)); det = seg(t, FEED, DET - FEED); alive = form * (1 - det)
    hs = 0.05 + 0.95 * form
    horizon.scale = (hs * (1 - det),) * 3; lens.scale = (hs * (1 + det * 2),) * 3; lens.hide_render = det > 0.9
    photon.scale = (hs * (1 + det * 4),) * 3; photon.hide_render = form < 0.3 or det > 0.95
    photon.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 80 + (300 if PULL <= t < FLASH else 0) + 400 * det
    for d, spin in ((disc_in, 3.2), (disc_out, 1.6)):
        d.hide_render = t < PULL or det > 0.95; s = eo(seg(t, PULL, 0.6)) * (1 + det * 3); d.scale = (s, s, 1)
        d.rotation_euler = (tilt[0], tilt[1], tilt[2]); d.rotation_euler.rotate_axis('Z', t * spin)
    hmap.inputs['Location'].default_value[0] = -t * 2.5; omap.inputs['Location'].default_value[0] = -t * 1.2
    for j in jets: j.hide_render = t < FLASH or det > 0.6; j.scale = (1, 1, max(0.02, eo(seg(t, FLASH, 0.5)) * (1 - det)))
    jmap.inputs['Location'].default_value[1] = -t * 6
    lo.data.energy = 800 * alive + (15000 if PULL <= t < FLASH else 0) + 30000 * det * (1 - det) * 4
    for o in debs:  # spiral in with growing angular speed, stretch along the fall, vanish at the horizon
        u = max(0, t - o['d']); r = max(0, o['r0'] * (1 - u / 1.1)); a = o['a'] + 2.5 / (r + 0.6) * u * 3
        o.hide_render = u <= 0 or r < 1.3 or det > 0
        o.location = (math.cos(a) * r, math.sin(a) * r, o['z'] * r / o['r0']); st = 1 + 2.5 * (1 - r / o['r0'])
        o.scale = (st, 1 / st ** 0.5, 1 / st ** 0.5); o.rotation_euler = (0, 0, a + math.pi / 2)
    for o in sparks:
        if det > 0: r = o['r'] + det * 14; a = o['a']
        else: r = o['r']; a = o['a'] + t * o['w'] * 6 / r
        o.location = (math.cos(a) * r, math.sin(a) * r, 0); o.hide_render = t < PULL
    scene.render.filepath = f'{OUT}/frame_{f:03d}.png'; bpy.ops.render.render(write_still=True)
print('rendered', FRAMES)
