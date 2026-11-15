"""Eclipse Vortex (ultimate, tier 1, Hero/Showcase only) rendered in headless Blender Cycles.
Layers: twisted flame column, counter-spinning white-hot inner core, 3 helix ribbons, black eclipse disc with a burning
corona ring, ground shockwave, spiral sparks and rising debris.  Timeline (s): gather 0-0.35, ignite 0.35-0.45,
sustain 0.45-1.8, collapse 1.8-2.4.   bpyenv/bin/python blender_vortex.py -- OUT [frames=72] [size=400]"""
import sys, os, math, random
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/vortex'; FRAMES = int(argv[1]) if len(argv) > 1 else 72; SIZE = int(argv[2]) if len(argv) > 2 else 400
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import meshgen
from bvfx import to_blender, flame_material, solid
scene = bpy.context.scene; rnd = random.Random(4)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 16; scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.004, 0.002, 0.008, 1)

def helix(turns=1.6, h=10.0, r0=2.0, r1=4.0, width=0.09, steps=120, phase=0.0):
    m = meshgen.Mesh(); idx = []
    for i in range(steps + 1):
        t = i / steps; a = phase + t * turns * 2 * math.pi; r = r0 + (r1 - r0) * t; w = width * math.sin(math.pi * t) + 0.02
        row = []
        for s in (-1, 1):
            row.append(m.add((math.cos(a) * r, math.sin(a) * r, h * t + s * w), meshgen.uv_inset(t, (s + 1) / 2), 1.0))
        idx.append(row)
    for i in range(steps): m.quad(idx[i][0], idx[i + 1][0], idx[i + 1][1], idx[i][1])
    return m

def zup(m):  # meshgen is Y-up; Blender is Z-up
    m.v = [(x, -z, y) for x, y, z in m.v]; return m

outer_m, outer_map = flame_material('outer', (1, 0.03, 0.07), 26)
inner_m, inner_map = flame_material('inner', (1, 0.35, 0.3), 14)
ring_m, ring_map = flame_material('ring', (1, 0.15, 0.2), 9)
outer = to_blender(zup(meshgen.vortex(32, 24, 10, 1.2, 3.4, 320)), 'outer'); outer.data.materials.append(outer_m)
inner = to_blender(zup(meshgen.vortex(20, 24, 10, 0.45, 0.9, -420, pinch=0.35)), 'inner'); inner.data.materials.append(inner_m)
ribbons = []
for k in range(3):
    rb = to_blender(helix(phase=k * 2 * math.pi / 3), f'rib{k}'); rb.data.materials.append(solid(f'rib{k}', (1, 0.08, 0.15), 6)); ribbons.append(rb)
ground = to_blender(zup(meshgen.shockwave(48, 4, 0.3, 2.5)), 'shock'); ground.data.materials.append(ring_m)
# eclipse: black disc + burning corona
bpy.ops.mesh.primitive_circle_add(radius=2.2, fill_type='NGON', location=(0, 0, 11.5)); disc = bpy.context.active_object
disc.data.materials.append(solid('void', (0, 0, 0), 0)); disc.rotation_euler = (math.radians(70), 0, 0)
bpy.ops.mesh.primitive_torus_add(major_radius=2.3, minor_radius=0.12, location=(0, 0, 11.5)); corona = bpy.context.active_object
corona.data.materials.append(solid('corona', (1, 0.35, 0.25), 60)); corona.rotation_euler = disc.rotation_euler
corona2 = to_blender(zup(meshgen.shockwave(48, 3, 2.2, 4.2, tiles=3)), 'corona2'); corona2.data.materials.append(flame_material('cor2', (1, 0.12, 0.15), 12)[0])
corona2.location = disc.location; corona2.rotation_euler = (math.radians(70 - 90), 0, 0)
# floor + figure for scale (5 studs)
bpy.ops.mesh.primitive_circle_add(radius=40, fill_type='NGON'); bpy.context.active_object.data.materials.append(solid('floor', (0.03, 0.015, 0.025), 0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=5, location=(0, -0.2, 2.5)); bpy.context.active_object.data.materials.append(solid('fig', (0.01, 0.008, 0.012), 0))
# sparks + debris
sp_mat = solid('spark', (1, 0.55, 0.35), 50); sparks = []
for i in range(90):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.05); o = bpy.context.active_object; o.data.materials.append(sp_mat)
    o['a'] = rnd.uniform(0, 6.283); o['r'] = rnd.uniform(5, 11); o['h'] = rnd.uniform(0, 10); o['sp'] = rnd.uniform(0.6, 1.4); sparks.append(o)
deb_mat = solid('deb', (0.12, 0.02, 0.03), 2); debs = []
for i in range(10):
    o = to_blender(meshgen.debris(i + 1, rnd.uniform(0.4, 0.9)), f'deb{i}'); o.data.materials.append(deb_mat)
    o['a'] = rnd.uniform(0, 6.283); o['r'] = rnd.uniform(2.6, 4.2); o['d'] = rnd.uniform(0, 0.4); debs.append(o)
light = bpy.data.lights.new('l', 'POINT'); light.color = (1, 0.15, 0.2); lo = bpy.data.objects.new('l', light); lo.location = (0, -2, 3); scene.collection.objects.link(lo)
bpy.ops.object.camera_add(location=(0, -24, 7)); cam = bpy.context.active_object; scene.camera = cam; cam.data.lens = 30
aim = bpy.data.objects.new('aim', None); scene.collection.objects.link(aim); aim.location = (0, 0, 5.8)
tc = cam.constraints.new('TRACK_TO'); tc.target = aim; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
try:
    tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); scene.compositing_node_group = tree
    rl = tree.nodes.new('CompositorNodeRLayers'); gl = tree.nodes.new('CompositorNodeGlare'); o = tree.nodes.new('NodeGroupOutput')
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    gl.inputs['Type'].default_value = 'Fog Glow'; tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], o.inputs[0])
except Exception as e: print('bloom skipped:', e)

def seg(t, a, d): return min(1, max(0, (t - a) / d))
def eo(t): return 1 - (1 - t) ** 4
G, IG, SU, CO = 0.35, 0.45, 1.8, 2.4
for f in range(FRAMES):
    t = f / 30
    grow = eo(seg(t, G, 0.5)); col = 1 - eo(seg(t, SU, CO - SU)); live = grow * col
    for o, spin in ((outer, 2.2), (inner, -4.0)):
        o.hide_render = live < 0.02; o.scale = (0.4 + 0.6 * live + (0.25 * (1 - col)), ) * 2 + (max(0.02, live),); o.rotation_euler.z = t * spin
    outer_map.inputs['Location'].default_value[1] = -t * 2.5; inner_map.inputs['Location'].default_value[1] = -t * 5
    outer_m.node_tree.nodes['Emission'].inputs['Strength'].default_value = 26 + (40 if IG > t >= G else 0)
    for k, rb in enumerate(ribbons):
        rb.hide_render = live < 0.05; rb.scale = (1, 1, max(0.02, live)); rb.rotation_euler.z = t * 3.0
    sw = eo(seg(t, G, 0.8)); ground.hide_render = not (G <= t < G + 0.8); ground.scale = (0.5 + 5 * sw, 0.5 + 5 * sw, 1)
    ring_map.inputs['Location'].default_value[1] = -t * 3
    ec = eo(seg(t, 0.8, 0.5)) * col
    for o in (disc, corona, corona2): o.hide_render = ec < 0.03; o.scale = (ec,) * 3
    corona2.rotation_euler.z = t * 1.5
    lo.data.energy = 1500 * live + (12000 if G <= t < IG else 0)
    for o in sparks:
        if t < G:  # gather: sparks spiral inward
            k = eo(t / G); r = o['r'] * (1 - k) + 0.6 * k; a = o['a'] + k * 3; z = o['h'] * (1 - k) + 1 * k
        else:      # sustain: ride the column up, collapse: fly out
            u = (t - G) * o['sp']; a = o['a'] + u * 4; r = 1.4 + u * 1.2 + (6 * (t - SU) if t > SU else 0); z = (1 + u * 6) % 11
        o.location = (math.cos(a) * r, math.sin(a) * r, z); o.hide_render = t > CO - 0.1
    for o in debs:
        u = max(0, t - G - o['d']); a = o['a'] + u * 2.5; z = 0.3 + u * 4.5
        o.location = (math.cos(a) * o['r'], math.sin(a) * o['r'], z); o.rotation_euler = (u * 3, u * 4, 0); o.hide_render = u <= 0 or z > 11
    scene.render.filepath = f'{OUT}/frame_{f:03d}.png'; bpy.ops.render.render(write_still=True)
print('rendered', FRAMES)
