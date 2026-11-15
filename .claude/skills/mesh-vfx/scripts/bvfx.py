"""Shared Blender helpers for mesh-vfx scripts (pip bpy 5.x)."""
import bpy
scene = bpy.context.scene

def to_blender(m, name):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in m.v], [], [tuple(f) for f in m.f]); me.update()
    uv = me.uv_layers.new(name='UVMap'); col = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices): uv.data[li].uv = m.uv[vi]
    for i, c in enumerate(m.col): col.data[i].color = (c, c, c, 1)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

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

