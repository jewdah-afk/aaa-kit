"""Render a lihfolk box-rig critter (penguin, duck, fox...) as a HUD icon, headless, no GPU.

studlib's own preview uses EEVEE, which needs a GPU. This builds the critter through
studlib's `export` mode (scene only), then renders it in Cycles on a transparent
background at a 3/4 view. Give it the HUD sticker outline with voxel_icons.sticker().

Run (needs `pip install bpy`):
    python3 tools/lookdev/critter_icon.py .claude/skills/lihfolk-stud-voxel/examples/penguin.py OUT/raw_penguin.png
"""
import sys, os, math
creature, out_png = sys.argv[1], sys.argv[2]
tmp = os.path.dirname(out_png) + '/_export'
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'lihfolk-stud-voxel', 'scripts', 'studlib.py')
sys.argv = ['blender', '--', creature, 'export', tmp]
import __main__
__main__.__file__ = LIB
exec(compile(open(LIB).read(), LIB, 'exec'), __main__.__dict__)
import bpy
from mathutils import Vector
sc = bpy.context.scene
PV = getattr(__main__.C, 'PREVIEW', {})
for o in list(sc.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.88, 1.0, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45
for nm, en, rot, col in (('Key', 3.2, (35, 10, -40), (1, .96, .9)), ('Fill', 0.7, (65, 0, 150), (.8, .9, 1)), ('Rim', 1.6, (-50, 0, 20), (1, 1, 1))):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
    L.data.energy = en; L.data.color = col; L.rotation_euler = [math.radians(a) for a in rot]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = PV.get('ortho', 3.0) * 1.05
tgt = Vector(PV.get('target', (0, 0, 1))); yaw, pitch = -32, 12
d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))))
cam.location = tgt + d * 30; cam.data.clip_end = 100; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 640
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = out_png; bpy.ops.render.render(write_still=True)
print('ICON_OK', out_png)
