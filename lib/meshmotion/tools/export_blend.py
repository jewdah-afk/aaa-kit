"""Export a segmented Blender creature to a meshmotion blueprint (JSON).

    blender -b creature.blend -P export_blend.py -- out.json [--weights-attr Jiggle] [--scale 1]

Every visible mesh object is one segment. Its Blender parent (if also a mesh) is the segment parent, and its
object origin is the pivot. Modifiers are applied (evaluated mesh), quads are triangulated, and coordinates
are converted from Blender (Z up, -Y forward) to Roblox (Y up): (x, y, z) -> (x, z, -y).
Optional per-vertex jiggle weight comes from a float point attribute (default name "Jiggle"), or the vertex
group of the same name. Vertices are welded per segment on exact position so the runtime matcher in
Adapter.bind finds them after Roblox splits UV seams.
"""
import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("usage: -- out.json [--weights-attr NAME] [--scale S]")
out_path = argv[0]
weights_attr = "Jiggle"
scale = 1.0
if "--weights-attr" in argv:
    weights_attr = argv[argv.index("--weights-attr") + 1]
if "--scale" in argv:
    scale = float(argv[argv.index("--scale") + 1])


def to_rbx(v):
    return [round(v[0] * scale, 5), round(v[2] * scale, 5), round(-v[1] * scale, 5)]


depsgraph = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get() and not o.hide_render]
names = {o.name for o in objs}

verts, tris, vseg, weights, segments = [], [], [], [], []
for o in objs:
    parent = o.parent.name if o.parent and o.parent.name in names else None
    segments.append({"name": o.name, "parent": parent, "pivot": to_rbx(o.matrix_world.translation)})
    ev = o.evaluated_get(depsgraph)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    mw = o.matrix_world
    attr = me.attributes.get(weights_attr)
    vg = o.vertex_groups.get(weights_attr)
    weld = {}
    local = []
    for v in me.vertices:
        p = to_rbx(mw @ v.co)
        k = tuple(p)
        if k not in weld:
            w = 0.0
            if attr is not None and attr.domain == "POINT" and attr.data_type == "FLOAT":
                w = attr.data[v.index].value
            elif vg is not None:
                try:
                    w = vg.weight(v.index)
                except RuntimeError:
                    w = 0.0
            weld[k] = len(verts) // 3
            verts.extend(p)
            vseg.append(o.name)
            weights.append(round(w, 4))
        local.append(weld[k])
    for t in me.loop_triangles:
        a, b, c = (local[i] for i in t.vertices)
        if a != b and b != c and a != c:
            # Blender CCW + handedness flip of the axis swap -> keep order (det of the swap is +1)
            tris.extend([a, b, c])
    ev.to_mesh_clear()

name = bpy.path.display_name_from_filepath(bpy.data.filepath) or "Creature"
bp = {"name": name, "verts": verts, "tris": tris, "vseg": vseg, "weights": weights, "segments": segments}
with open(out_path, "w") as f:
    json.dump(bp, f, separators=(",", ":"))
print(f"meshmotion export: {name} {len(verts)//3} verts {len(tris)//3} tris {len(segments)} segments -> {out_path}")
