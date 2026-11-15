"""Blender (bpy) twin of meshgen.crescent: run inside Blender 4.x. UNTESTED here (no Blender in CI); meshgen.py is the tested path.
blender -b -P blender_gen.py -- out.fbx"""
import bpy, sys, math
out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/slash.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=1)
ob = bpy.context.active_object
ob.scale = (8.0, 1.2, 1); bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=15); bpy.ops.object.mode_set(mode='OBJECT')
for v in ob.data.vertices:  # taper toward both ends
    t = (v.co.x + 4) / 8; v.co.y *= max(0.02, 1 - abs(2 * t - 1) ** 1.8)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.unwrap(margin=0.03); bpy.ops.object.mode_set(mode='OBJECT')
m = ob.modifiers.new('bend', 'SIMPLE_DEFORM'); m.deform_method = 'BEND'; m.angle = math.radians(210); m.deform_axis = 'Z'
bpy.ops.object.modifier_apply(modifier='bend')
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, apply_unit_scale=True, axis_forward='-Z', axis_up='Y')
print('wrote', out)
