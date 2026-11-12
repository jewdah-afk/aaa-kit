"""Stud map guide: one readable area built from the LihFolk Stud Voxel pack pieces.

Run headless from the repo root:
    blender -b --factory-startup --python examples/map-guide/build_map.py -- render plan close export
Units are studs (the pack's GLBs are in studs). Blender axes: X east, Y north, Z up. The camera looks
north, so tall things go on the north half (docs/playbooks/world-hierarchy.md).

Every material is colour x the pack's stud texture (stud_mul.png, already 2x the square stud) with
world-aligned UVs, so the same studs survive the .glb export and the Roblox 3D Importer.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PACK = os.path.join(ROOT, '.claude', 'skills', 'lihfolk-stud-voxel')
BRICK = os.path.join(PACK, 'examples', 'brick')
STUD_MUL = os.path.join(BRICK, 'out_Oak', 'stud_mul.png')  # 8 x 8 studs per tile, 2 x overlay baked in
OUT = os.path.join(HERE, 'out')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def lin(hexcol):
    """sRGB hex -> linear RGB (Blender colour inputs are linear)."""
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# one job per colour; ground (tier 6) stays a step below the foliage greens
PALETTE = {
    'GrassA': '#4FAE35', 'GrassB': '#3E9429', 'Dirt': '#E07A2C',
    'Path': '#C9A66B', 'Plaza': '#8E95A0',
    'Shirt': '#F2F2F2', 'Shirt2': '#FF4F4F', 'Pants': '#2B5FD9', 'Skin': '#FFD27F',
}
SKY = lin('#9CCBF2')
CELL = 8  # grass checker cell, studs

# ---------------------------------------------------------------- materials

_mats = {}


def mat(key):
    """Principled: base colour = colour x stud texture (exports as glTF baseColorFactor x baseColorTexture)."""
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    bsdf = n['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.85
    img = n.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(STUD_MUL, check_existing=True)
    mix = n.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    mix.inputs['A'].default_value = (*lin(PALETTE[key]), 1)
    l.new(img.outputs['Color'], mix.inputs['B'])
    l.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    _mats[key] = m
    return m


# ---------------------------------------------------------------- stud geometry


class StudMesh:
    """Collects axis-aligned quads and writes them as one object with world-aligned stud UVs."""

    def __init__(self, name, key, col):
        self.name, self.key, self.col = name, key, col
        self.quads = []

    def quad(self, corners, axis):
        self.quads.append((corners, axis))

    def box(self, x0, x1, y0, y1, z0, z1, faces='NSEWTB'):
        if 'T' in faces:
            self.quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 'Z')
        if 'B' in faces:
            self.quad([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], 'Z')
        if 'S' in faces:
            self.quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], 'Y')
        if 'N' in faces:
            self.quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], 'Y')
        if 'E' in faces:
            self.quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], 'X')
        if 'W' in faces:
            self.quad([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], 'X')

    def build(self):
        me = bpy.data.meshes.new(self.name)
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new('UVMap')
        for corners, axis in self.quads:
            f = bm.faces.new([bm.verts.new(c) for c in corners])
            for lp in f.loops:
                x, y, z = lp.vert.co
                a, b = {'Z': (x, y), 'Y': (x, z), 'X': (y, z)}[axis]
                lp[uv].uv = (a / 8, b / 8)  # 8 studs per texture tile -> 1 stud per stud
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(self.name, me)
        me.materials.append(mat(self.key))
        self.col.objects.link(o)
        return o


def checker_top(name, x0, x1, y0, y1, z, col):
    """Top surface as 8-stud cells in two greens (two objects, one per tone)."""
    a, b = StudMesh(name + 'A', 'GrassA', col), StudMesh(name + 'B', 'GrassB', col)
    for i in range(math.floor(x0 / CELL), math.ceil(x1 / CELL)):
        for j in range(math.floor(y0 / CELL), math.ceil(y1 / CELL)):
            cx0, cx1 = max(x0, i * CELL), min(x1, (i + 1) * CELL)
            cy0, cy1 = max(y0, j * CELL), min(y1, (j + 1) * CELL)
            (a if (i + j) % 2 == 0 else b).quad([(cx0, cy0, z), (cx1, cy0, z), (cx1, cy1, z), (cx0, cy1, z)], 'Z')
    return a.build(), b.build()


# ---------------------------------------------------------------- pack pieces

_cache = {}
_count = {}


def piece(kind, x, y, z=0.0, yaw=0.0, col=None):
    """Imports `kind` from the pack once (rig dropped: static props), then places linked copies."""
    if kind not in _cache:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(BRICK, f'out_{kind}', f'{kind}_rig.glb'))
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH']
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            o.modifiers.clear()
            o.vertex_groups.clear()
            for c in list(o.users_collection):
                c.objects.unlink(o)
        for o in new:
            if o.type != 'MESH':
                bpy.data.objects.remove(o)
        _cache[kind] = meshes
    _count[kind] = _count.get(kind, 0) + 1
    out = []
    for i, src in enumerate(_cache[kind]):
        o = src.copy()
        o.name = f'{kind}{_count[kind]}' + (f'_{i}' if len(_cache[kind]) > 1 else '')
        o.location = (x, y, z + 1.0)  # base discs sit 1 stud below the pivot
        o.rotation_euler = (0, 0, math.radians(yaw))
        col.objects.link(o)
        out.append(o)
    return out


def player(x, y, z, shirt, col):
    """A 5-stud blocky stand-in so every screenshot shows scale (tier 1: the brightest thing on screen)."""
    parts = [('Pants', -1, -0.05, -0.5, 0.5, 0, 2), ('Pants', 0.05, 1, -0.5, 0.5, 0, 2), (shirt, -1, 1, -0.5, 0.5, 2, 4),
             (shirt, -1.6, -1, -0.5, 0.5, 2, 4), (shirt, 1, 1.6, -0.5, 0.5, 2, 4), ('Skin', -0.6, 0.6, -0.6, 0.6, 4, 5.2)]
    s = {}
    for key, a0, a1, b0, b1, c0, c1 in parts:
        s.setdefault(key, StudMesh(f'Player_{x}_{y}_{key}', key, col)).box(x + a0, x + a1, y + b0, y + b1, z + c0, z + c1)
    for m in s.values():
        m.build()


# ---------------------------------------------------------------- the area

# Plan (studs): ground 300 x 300. Spawn on the south edge; the path runs north to a plaza with the well, on up
# the terrace steps to the castle gate. East: the shop. West: the training yard. North: a 12-stud terrace with
# the watchtower (the one landmark), fenced; the castle wall, a cliff and a waterfall close the back. The south
# (foreground) half keeps only low bushes and rocks so nothing hides the player.
GX0, GX1, GY0, GY1 = -150, 150, -150, 150
TER_X1, TER_Y0, TER_H = 60, 40, 12


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    cols = {}
    for name in ['Ground', 'Backdrop', 'Landmarks', 'Interactables', 'Props', 'Foliage', 'Rocks', 'Actors']:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
        cols[name] = c
    G = cols['Ground']

    # tier 6 ground: grass checker over an orange stud-dirt slab (its edge reads as one clean band)
    checker_top('Grass', GX0, GX1, GY0, GY1, 0, G)
    dirt = StudMesh('GroundDirt', 'Dirt', G)
    dirt.box(GX0, GX1, GY0, GY1, -20, 0, faces='NSEWB')
    dirt.build()
    checker_top('TerraceGrass', GX0, TER_X1, TER_Y0, GY1, TER_H, G)
    tw = StudMesh('TerraceDirt', 'Dirt', G)
    tw.box(GX0, TER_X1, TER_Y0, GY1, 0, TER_H, faces='SE')
    tw.build()
    # tier 4 structure: spawn path from the south edge to the plaza, east/west branches, steps up the terrace
    # straight north to the gate (the path points at the goal and frames the landmark)
    path = StudMesh('Path', 'Path', G)
    path.box(-6, 6, GY0, -18, 0, 0.4, faces='TEW')
    path.box(18, 98, -6, 6, 0, 0.4, faces='TNS')
    path.box(-98, -18, -6, 6, 0, 0.4, faces='TNS')
    path.box(-6, 6, 18, TER_Y0 - 16, 0, 0.4, faces='TEW')
    for i in range(4):  # 3-stud rises, 4-stud treads, 12 wide
        path.box(-6, 6, TER_Y0 - 16 + 4 * i, TER_Y0, 0, 3 * (i + 1))
    path.box(-6, 6, TER_Y0, GY1 - 26, TER_H, TER_H + 0.4, faces='TEW')
    path.build()
    plaza = StudMesh('Plaza', 'Plaza', G)
    plaza.box(-18, 18, -18, 18, 0, 0.5)
    plaza.build()

    # tier 7 backdrop: the castle wall and gate close the north edge of the terrace, a cliff and a waterfall the rest
    piece('CastleGate', 0, GY1 - 16, TER_H, col=cols['Backdrop'])
    for x in (-63, -114):
        piece('Wall', x, GY1 - 12, TER_H, col=cols['Backdrop'])
    piece('Cliff', 35, GY1 - 18, TER_H, col=cols['Backdrop'])
    piece('Waterfall', 105, GY1 - 24, 0, col=cols['Backdrop'])
    # tier 3 landmark: one tall silhouette, north-west, framing the play area
    piece('Watchtower', -100, 86, TER_H, col=cols['Landmarks'])
    # tier 2 interactables: shop (east), training yard (west), well (plaza centre)
    piece('Shop', 122, 0, yaw=90, col=cols['Interactables'])
    piece('Gym', -122, 0, yaw=-90, col=cols['Interactables'])
    piece('Well', 0, 0, 0.5, col=cols['Interactables'])
    # tier 4 props: lamps along the spawn path, fences on the terrace edge (gap for the steps), a cart by the shop
    for y in (-50, -95):
        for x in (-13, 13):
            piece('Lamp', x, y, col=cols['Props'])
    for x in (-128, -86, -44, 38):
        piece('Fence', x, TER_Y0 + 3, TER_H, col=cols['Props'])
    piece('Cart', 92, -34, yaw=-25, col=cols['Props'])
    # tier 5 dressing: tall trees on the side edges and behind; the south foreground keeps only low bushes and rocks
    for kind, x, y, z, yaw in [
        ('Oak', -122, -60, 0, 15), ('Oak', 124, -66, 0, -30), ('Pine', -138, 34, 0, 0), ('Pine', 138, 60, 0, 40),
        ('Pine', -136, -20, 0, 50), ('Oak', 60, 40, 0, 20), ('Pine', 30, 110, TER_H, 10), ('Oak', -40, 100, TER_H, 60),
        ('Pine', -138, 120, TER_H, 20), ('Bush', -50, -40, 0, 0), ('Bush', 46, -52, 0, 30), ('Bush', -110, 60, TER_H, 0),
        ('Bush', 84, 30, 0, 70), ('Bush', -70, -116, 0, 15), ('Bush', 72, -136, 0, 50), ('Bush', -26, 58, TER_H, 0),
        ('Bush', 26, 60, TER_H, 30), ('Bush', -122, -100, 0, 0), ('Bush', 134, -114, 0, 40),
    ]:
        piece(kind, x, y, z, yaw, col=cols['Foliage'])
    for x, y, z, yaw in [(-34, -100, 0, 20), (34, -112, 0, -40), (80, 92, 0, -15), (-70, 64, TER_H, 45), (134, -30, 0, 0)]:
        piece('Rocks', x, y, z, yaw, col=cols['Rocks'])
    # tier 1 actors: scale stand-ins
    player(3, -30, 0.4, 'Shirt2', cols['Actors'])
    player(-6, 8, 0.5, 'Shirt', cols['Actors'])
    player(2, 96, TER_H + 0.4, 'Shirt2', cols['Actors'])
    player(100, 2, 0.4, 'Shirt', cols['Actors'])
    return sc


# ---------------------------------------------------------------- render


def setup_render(sc):
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    w = bpy.data.worlds.new('Sky')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (*SKY, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(6)
    sun.rotation_euler = (math.radians(48), math.radians(-18), math.radians(-35))
    sc.collection.objects.link(sun)


def camera(sc, name, loc, target, lens=40, ortho=None):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    cam.data.clip_end = 5000
    return cam


def render(sc, cam, name, res=None):
    sc.camera = cam
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    sc = build()
    setup_render(sc)
    if 'render' in ARGS:
        render(sc, camera(sc, 'Hero', (0, -430, 300), (0, 8, 0), lens=40), 'map_hero.png')
    if 'plan' in ARGS:
        render(sc, camera(sc, 'Plan', (0, 0, 600), (0, 0, 0), ortho=310), 'map_plan.png', (1400, 1400))
    if 'close' in ARGS:
        render(sc, camera(sc, 'Close', (46, -44, 20), (-2, 14, 9), lens=30), 'map_close.png', (1920, 1080))
    if 'export' in ARGS:
        for o in sc.objects:
            o.select_set(o.type == 'MESH')
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'StudMapGuide.glb'), export_format='GLB',
                                  use_selection=True, export_apply=True)
        print('EXPORTED')
    meshes = [o for o in sc.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print('MAP_OK', len(meshes), 'meshes', tris, 'tris')
