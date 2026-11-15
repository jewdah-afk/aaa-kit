"""Full mesh-VFX pipeline inside headless Blender (pip `bpy` 5.x):
  1. builds every meshgen shape as a Blender mesh (same tested geometry + UVs + mask colour attribute), exports FBX per shape
  2. bakes the flame alpha with Blender nodes (Noise -> Voronoi distance-to-edge -> ColorRamp) to PNG
  3. renders the slash timeline in Cycles with emission + compositor Glare (bloom) to PNG frames
  bpyenv/bin/python blender_pipeline.py -- OUTDIR [frames=48] [size=480]"""
import sys, os, math
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshgen

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/meshvfx'; FRAMES = int(argv[1]) if len(argv) > 1 else 48; SIZE = int(argv[2]) if len(argv) > 2 else 480
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

from bvfx import to_blender, flame_material, solid

shapes = {
    'body': meshgen.crescent(200, 4, 1.6, mask='core'), 'core': meshgen.crescent(170, 4, 0.45, mask='core'),
    'shell': meshgen.shell(meshgen.crescent(200, 4, 1.6, mask='core')), 'ring': meshgen.shockwave(),
    'vortex': meshgen.vortex(), 'debris': meshgen.debris(2),
}
obs = {}
for n, m in shapes.items():
    ob = obs[n] = to_blender(m, n)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=f'{OUT}/{n}.fbx', use_selection=True, apply_unit_scale=True, axis_forward='-Z', axis_up='Y')
    print('fbx', n, len(ob.data.polygons), 'faces')

# 2. node bake: emission plane, 1:1 ortho camera render (simpler + exact vs. bake API)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 12; scene.cycles.use_denoising = False  # bake: no denoise
scene.render.resolution_x = scene.render.resolution_y = SIZE; scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.006, 0.003, 0.01, 1)

# bake flame: plane filling an ortho camera
bake_mat, _ = flame_material('bake', (1, 1, 1), 1.0)
bpy.ops.mesh.primitive_plane_add(size=2); plane = bpy.context.active_object; plane.data.materials.append(bake_mat)
plane.data.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
for c in plane.data.color_attributes['Mask'].data: c.color = (1, 1, 1, 1)
bpy.ops.object.camera_add(location=(0, 0, 5)); cam = bpy.context.active_object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2; scene.camera = cam
for o in obs.values(): o.hide_render = True
scene.render.filepath = f'{OUT}/flame_blender.png'; bpy.ops.render.render(write_still=True); print('baked flame_blender.png')
plane.hide_render = True

# 3. slash render
bmat, bmap = flame_material('body', (1, 0.08, 0.12), 14); smat, smap = flame_material('shell', (0.5, 0.02, 0.1), 5)
obs['body'].data.materials.append(bmat); obs['shell'].data.materials.append(smat)
obs['core'].data.materials.append(solid('core', (0, 0, 0), 0)); obs['ring'].data.materials.append(flame_material('ring', (1, 0.15, 0.2), 8)[0])
rim = to_blender(meshgen.crescent(172, 4, 0.6, mask='core'), 'rim'); rim.data.materials.append(solid('rim', (1, 0.85, 0.8), 40))
pivot = bpy.data.objects.new('slash', None); scene.collection.objects.link(pivot); pivot.location = (-3.2, 0.4, 2.6); pivot.rotation_euler = (math.radians(20), 0, math.radians(-30))
for n in ('body', 'shell', 'core'): obs[n].parent = pivot; obs[n].hide_render = False
rim.parent = pivot; obs['core'].location.z = 0.03; obs['ring'].hide_render = False
gnd = bpy.data.objects.new('g', bpy.data.meshes.new('g')); bpy.ops.mesh.primitive_circle_add(radius=30, fill_type='NGON'); g = bpy.context.active_object
g.data.materials.append(solid('g', (0.02, 0.012, 0.02), 0)); g.location.z = -0.02
cam.data.type = 'PERSP'; cam.location = (0, -17, 9); aim = bpy.data.objects.new('aim', None); scene.collection.objects.link(aim); aim.location = (0, 0, 1.8)
tc = cam.constraints.new('TRACK_TO'); tc.target = aim; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
scene.cycles.use_denoising = True; scene.cycles.samples = 16
# compositor bloom (Blender 5: compositing node group)
try:
    tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); scene.compositing_node_group = tree
    rl = tree.nodes.new('CompositorNodeRLayers'); gl = tree.nodes.new('CompositorNodeGlare'); o = tree.nodes.new('NodeGroupOutput')
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    try: gl.inputs['Type'].default_value = 'Fog Glow'
    except Exception: gl.glare_type = 'FOG_GLOW'
    tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], o.inputs[0]); print('bloom on')
except Exception as e: print('bloom skipped:', e)
A, I, E = 0.15, 0.07, 0.63
def ease(t): return 1 - (1 - t) ** 5
def seg(t, a, d): return min(1, max(0, (t - a) / d))
for f in range(FRAMES):
    t = f / 30
    pre = t < A; a = seg(t, 0, A); x = ease(seg(t, A, I + E)); fd = ease(seg(t, A + I, E)); impact = A <= t < A + I
    sw = 0.3 + 0.7 * a if pre else 1 + 0.35 * x
    for n in ('body', 'core'): obs[n].scale = (sw, sw, 1)
    rim.scale = (sw * 1.01, sw * 1.01, 1); pivot.rotation_euler.z = math.radians(-30 - (40 * (1 - a) if pre else 0))
    em = bmat.node_tree.nodes['Emission']; em.inputs['Strength'].default_value = 30 if impact else (14 * a if pre else 14 * (1 - fd))
    rim.hide_render = not impact and t > A + I + 0.15 or pre
    obs['core'].hide_render = pre or t > A + I + 0.3
    s2 = 1 + 0.6 * ease(seg(t, A, E)); obs['shell'].scale = (s2, s2, 1); obs['shell'].hide_render = pre or t > A + E
    rr = ease(seg(t, A + I, E)); obs['ring'].scale = (0.3 + 3 * rr,) * 2 + (1,); obs['ring'].hide_render = t < A + I or rr > 0.97
    bmap.inputs['Location'].default_value[0] = -t * 1.8; smap.inputs['Location'].default_value[0] = -t * 0.9
    scene.render.filepath = f'{OUT}/frame_{f:03d}.png'; bpy.ops.render.render(write_still=True)
print('rendered', FRAMES)
