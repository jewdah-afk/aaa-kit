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

def to_blender(m, name):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in m.v], [], [tuple(f) for f in m.f]); me.update()
    uv = me.uv_layers.new(name='UVMap'); col = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices): uv.data[li].uv = m.uv[vi]
    for i, c in enumerate(m.col): col.data[i].color = (c, c, c, 1)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob

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
def flame_material(name, color, strength, scroll_driver=True):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); mix = N.new('ShaderNodeMixShader'); tr = N.new('ShaderNodeBsdfTransparent'); em = N.new('ShaderNodeEmission')
    uv = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 2.5, 1)
    noise = N.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 2.5; noise.inputs['Detail'].default_value = 4; noise.inputs['Roughness'].default_value = 0.65
    vor = N.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 3
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'B_SPLINE'
    ramp.color_ramp.elements[0].position = 0.18; ramp.color_ramp.elements[1].position = 0.42
    attr = N.new('ShaderNodeAttribute'); attr.attribute_name = 'Mask'; mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    L.new(uv.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs['Vector'], noise.inputs['Vector'])
    L.new(mp.outputs['Vector'], add.inputs[0]); L.new(noise.outputs['Color'], add.inputs[1]); L.new(add.outputs['Vector'], vor.inputs['Vector'])
    L.new(vor.outputs['Distance'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], mul.inputs[0]); L.new(attr.outputs['Fac'], mul.inputs[1])
    L.new(mul.outputs['Value'], mix.inputs['Fac']); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs['Surface'])
    mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None
    return mat, mp

def solid(name, color, strength):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree; p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = strength
    return mat

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
