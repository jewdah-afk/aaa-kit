"""Headless Blender animatic from a frames file. No GPU and no Blender install needed:

    pip install bpy pillow
    python3 animatic.py frames.json out_dir

frames.json (written by your game's own curve code, e.g. a lune script that calls the same
modules the game runs):
  { "fps": 30,
    "scenery": [ {"lo": [x,y,z], "hi": [x,y,z], "colour": "RRGGBB"} ],        static boxes
    "frames":  [ {"eye": [x,y,z], "look": [x,y,z], "fov": 70,                 vertical degrees
                  "boxes": [ {"pos": [x,y,z], "rot": [9 numbers, row-major], "size": [x,y,z], "colour": "RRGGBB"} ]} ] }
Axes are Roblox's (Y up). The box list must have the same length and order on every frame.
Cycles on the CPU: EEVEE and Workbench need a display or GPU and crash in a container.
"""
import json, math, os, subprocess, sys
import bpy
from mathutils import Matrix, Vector

def to_blender(v):                       # Roblox (x, y up, z) -> Blender (x, -z, y up); a proper rotation
    return Vector((v[0], -v[2], v[1]))

def rot_to_blender(r):
    m = Matrix((r[0:3], r[3:6], r[6:9]))
    b = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    return (b @ m @ b.transposed()).to_4x4()

def colour(h):
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1.0,)

def material(h, cache={}):
    if h not in cache:
        m = bpy.data.materials.new(h); m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour(h); bsdf.inputs["Roughness"].default_value = 0.55
        cache[h] = m
    return cache[h]

def cube(h):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.data.materials.append(material(h)); return o

def main(src, out, width=640, height=360, samples=20):
    data = json.load(open(src)); os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.view_settings.view_transform = "Standard"          # flat game colours, not a filmic curve
    world = bpy.data.worlds.new("Sky"); sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = colour("BFE3FF")
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 3.2; sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-128))
    for s in data.get("scenery", []):
        lo, hi = to_blender(s["lo"]), to_blender(s["hi"])
        o = cube(s["colour"]); o.location = (lo + hi) / 2
        o.scale = (abs(hi.x - lo.x), abs(hi.y - lo.y), abs(hi.z - lo.z))
    movers = [cube(b["colour"]) for b in data["frames"][0]["boxes"]]
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.sensor_fit = "VERTICAL"; cam.data.clip_end = 5000
    for n, f in enumerate(data["frames"]):
        for o, b in zip(movers, f["boxes"]):
            o.matrix_world = Matrix.Translation(to_blender(b["pos"])) @ rot_to_blender(b["rot"]) @ Matrix.Diagonal(Vector(b["size"])).to_4x4()
        eye, look = to_blender(f["eye"]), to_blender(f["look"])
        cam.location = eye
        cam.rotation_euler = (look - eye).to_track_quat("-Z", "Y").to_euler()
        cam.data.angle = math.radians(f.get("fov", 70))
        sc.render.filepath = os.path.abspath(f"{out}/frame_{n:04d}.png")
        bpy.ops.render.render(write_still=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(data.get("fps", 30)), "-i", f"{out}/frame_%04d.png",
                    "-pix_fmt", "yuv420p", f"{out}/animatic.mp4"], check=True)
    print(f"{len(data['frames'])} frames -> {out}/animatic.mp4")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
