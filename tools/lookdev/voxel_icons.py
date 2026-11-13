"""Stud-voxel HUD icons: shop basket, index book, animals paw, daily calendar, luck clover, present.

Each icon is a small voxel model wearing the same square stud texture as the map
(.claude/skills/lihfolk-stud-voxel/assets/roblox_square_studs.png, one stud per 2x2
voxels), rendered in Cycles with a transparent background, then given the HUD's ink
sticker outline. Same look as the world, so the HUD reads as part of the game.

Run (needs `pip install bpy` 5.x, numpy, Pillow):
    python3 tools/lookdev/voxel_icons.py OUTDIR [name ...]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
STUD_PNG = os.path.join(ROOT, '.claude', 'skills', 'lihfolk-stud-voxel', 'assets', 'roblox_square_studs.png')
INK = (11, 12, 26)


# ---------------------------------------------------------------- voxel helpers
class Grid:
    """Colour-index voxel grid, z up. 0 = empty; palette maps index -> hex."""

    def __init__(self, nx, ny, nz):
        self.v = np.zeros((nx, ny, nz), np.int16)
        self.pal = {}

    def col(self, hexstr):
        for k, h in self.pal.items():
            if h == hexstr:
                return k
        k = len(self.pal) + 1
        self.pal[k] = hexstr
        return k

    def box(self, x0, x1, y0, y1, z0, z1, c):
        """Fill the inclusive-exclusive range [x0,x1) x [y0,y1) x [z0,z1)."""
        self.v[max(0, x0):x1, max(0, y0):y1, max(0, z0):z1] = self.col(c) if c else 0

    def where(self, mask, c):
        self.v[mask] = self.col(c) if c else 0

    def recolour(self, mask, c):
        self.v[mask & (self.v > 0)] = self.col(c)

    def coords(self):
        nx, ny, nz = self.v.shape
        return np.mgrid[0:nx, 0:ny, 0:nz].astype(np.float32) + 0.5


def ellipse2(a, b, ca, cb, ra, rb):
    return ((a - ca) / ra) ** 2 + ((b - cb) / rb) ** 2 <= 1.0


# ---------------------------------------------------------------- the icons
def m_book():
    g = Grid(24, 18, 9)
    X, Y, Z = g.coords()
    blue, blue_d, cream, cream2, gold, red = '#2F7BFF', '#1B4FC4', '#FFF1CF', '#EBD3A0', '#FFC629', '#FF3355'
    g.box(0, 22, 0, 18, 0, 1, blue_d)                 # back cover
    g.box(0, 22, 0, 18, 7, 8, blue)                   # front cover
    g.box(20, 22, 0, 18, 0, 8, blue_d)                # spine (far side)
    g.box(1, 20, 1, 17, 1, 7, cream)                  # pages
    g.where((g.v > 0) & (Z >= 1) & (Z < 7) & (X < 20) & (Y < 17) & ((np.floor(Z) % 2) == 0) & (X >= 1), cream2)
    for cx, cy in [(0, 0), (0, 15)]:                  # gold corner guards on the open side
        g.box(cx, cx + 3, cy, cy + 3, 7, 8, gold)
        g.box(cx, cx + 3, cy, cy + 3, 0, 1, gold)
    # gold star emblem on the cover (5-point star as a polar test)
    cx, cy = 10.0, 9.5
    ang = np.arctan2(Y - cy, X - cx) + np.pi / 2
    r = np.hypot(X - cx, Y - cy)
    k = np.cos(np.pi / 5) / np.cos((ang % (2 * np.pi / 5)) - np.pi / 5)
    star = r < 5.4 * (0.48 + 0.52 * ((k - np.cos(np.pi / 5)) / (1 - np.cos(np.pi / 5))) ** 1.0)
    g.recolour(star & (Z > 7) & (Z < 8), gold)
    g.recolour((X > 11) & (X < 13) & (Y < 2) & (Z > 1), red)   # ribbon over the cover and down the page edge
    return g, dict(yaw=-38, pitch=56)


def m_basket():
    g = Grid(22, 16, 18)
    X, Y, Z = g.coords()
    red, red_l, red_d, steel, steel_d = '#E8102E', '#FF4A60', '#8E0820', '#C9D6E8', '#7E8FA8'
    g.box(1, 21, 1, 15, 0, 9, red)                    # body
    g.box(2, 20, 2, 14, 1, 9, None)                   # hollow
    g.box(0, 22, 0, 16, 8, 10, red_l)                 # rolled rim
    g.box(1, 21, 1, 15, 8, 10, None)
    g.box(1, 21, 1, 15, 8, 9, None)
    g.where((g.v == 0) & (X > 1) & (X < 21) & (Y > 1) & (Y < 15) & (Z < 1), None)
    # slots in the walls (recessed dark)
    for x0 in range(4, 19, 4):
        g.recolour((X > x0) & (X < x0 + 2) & (Z > 3) & (Z < 7) & ((Y < 2) | (Y > 14)), red_d)
    for y0 in range(4, 13, 4):
        g.recolour((Y > y0) & (Y < y0 + 2) & (Z > 3) & (Z < 7) & ((X < 2) | (X > 20)), red_d)
    # goods peeking out: a lime present and a coin stack
    g.box(4, 11, 4, 11, 1, 13, '#5BD82A')
    g.box(7, 8, 4, 11, 1, 13, '#FFC629')
    g.box(4, 11, 7, 8, 1, 13, '#FFC629')
    g.box(6, 9, 6, 9, 13, 14, '#FFC629')
    disc = ellipse2(X, Y, 15.5, 8.5, 3.2, 3.2)
    for z in range(1, 12):
        g.where(disc & (Z > z) & (Z < z + 1), '#FFD23A' if z % 2 else '#F0A010')
    # handle arch, front to back over the middle
    g.box(10, 12, 1, 3, 9, 17, steel)
    g.box(10, 12, 13, 15, 9, 17, steel)
    g.box(10, 12, 1, 15, 16, 18, steel)
    g.recolour((Z > 16) & (Z < 17) & (X > 10) & (X < 12), steel_d)
    return g, dict(yaw=-34, pitch=60)


def m_paw():
    g = Grid(24, 6, 24)
    X, Y, Z = g.coords()
    org, org_l = '#FF9A1F', '#FFC24A'
    pad = ellipse2(X, Z, 12, 7.5, 7.2, 6.2)
    toes = np.zeros_like(pad)
    for cx, cz, rx, rz in [(3.6, 14.2, 2.6, 3.0), (8.9, 19.8, 2.6, 3.1), (15.1, 19.8, 2.6, 3.1), (20.4, 14.2, 2.6, 3.0)]:
        toes |= ellipse2(X, Z, cx, cz, rx, rz)
    shape = (pad | toes)
    g.where(shape & (Y > 0) & (Y < 3), org_l)        # front slab, light
    g.where(shape & (Y > 3) & (Y < 5), '#D4650C')     # back slab, darker: reads as a thick bevel
    g.where(shape & (Y > 2) & (Y < 4), org)
    return g, dict(yaw=-24, pitch=78)


def m_clover():
    g = Grid(26, 6, 30)
    X, Y, Z = g.coords()
    grn, grn_l, grn_d = '#2FCB45', '#8CFF5E', '#118A33'
    leaves = np.zeros(g.v.shape, bool)
    for dx, dz in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        cx, cz = 13 + dx * 5.0, 16.5 + dz * 5.0
        leaves |= ellipse2(X, Z, cx, cz, 4.9, 4.9) & ~ellipse2(X, Z, cx + dx * 4.6, cz + dz * 4.6, 2.6, 2.6)
    gaps = ((np.abs(X - 13) < 1.0) | (np.abs(Z - 16.5) < 1.0)) & (np.hypot(X - 13, Z - 16.5) > 2.6)
    leaves = (leaves & ~gaps) | ellipse2(X, Z, 13, 16.5, 2.8, 2.8)
    g.where(leaves & (Y > 0) & (Y < 3), grn)
    g.where(leaves & (Y > 2) & (Y < 5), grn_d)
    vein = ((np.abs((X - 13) - (Z - 16.5)) < 0.9) | (np.abs((X - 13) + (Z - 16.5)) < 0.9)) & (np.hypot(X - 13, Z - 16.5) < 8)
    g.recolour(leaves & vein & (Y < 1), grn_l)
    stem = (np.abs(X - (13 + (9 - Z) * 0.5)) < 1.1) & (Z < 9) & (Z > 0)
    g.where(stem & (Y > 2) & (Y < 4), grn_d)
    return g, dict(yaw=-22, pitch=80)


def m_present():
    g = Grid(18, 18, 18)
    X, Y, Z = g.coords()
    red, red_l, gold, gold_d = '#FF3355', '#FF6A82', '#FFD23A', '#E59A0E'
    g.box(2, 16, 2, 16, 0, 11, red)
    g.box(1, 17, 1, 17, 11, 14, red_l)
    g.recolour((np.abs(X - 9) < 1.6), gold)
    g.recolour((np.abs(Y - 9) < 1.6), gold)
    # bow: two leaning loops
    for side in (-1, 1):
        loop = ellipse2(X, Z, 9 + side * 3.6, 15.6, 3.4, 2.6) & ~ellipse2(X, Z, 9 + side * 3.6, 15.6, 1.6, 1.1)
        g.where(loop & (np.abs(Y - 9) < 1.6) & (Z >= 14), gold)
    g.box(8, 10, 8, 10, 14, 17, gold_d)
    return g, dict(yaw=-36, pitch=60)


def m_calendar():
    g = Grid(20, 6, 22)
    X, Y, Z = g.coords()
    white, white_d, red, red_l, ring, navy = '#FFFFFF', '#DCE6F2', '#FF3B55', '#FF6A82', '#9AA8BE', '#1E2550'
    g.box(1, 19, 1, 5, 0, 15, white)
    g.box(1, 19, 1, 5, 15, 19, red)
    g.recolour((Z > 18) & (Z < 19), red_l)
    g.recolour((Y > 4) & (Z < 1), white_d)
    for rx in (5, 13):
        g.box(rx, rx + 2, 2, 4, 17, 22, ring)
        g.box(rx, rx + 2, 2, 3, 20, 22, None)
        g.box(rx, rx + 2, 1, 2, 19, 22, ring)
    font = {'3': ['111', '001', '111', '001', '111'], '1': ['010', '110', '010', '010', '111']}
    for k, ch in enumerate('31'):
        rows = font[ch]
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == '1':
                    x0 = 3 + k * 8 + c * 2
                    z0 = 12 - r * 2
                    g.box(x0, x0 + 2, 0, 2, z0, z0 + 2, navy)
    return g, dict(yaw=-26, pitch=74)



def m_snowball():
    g = Grid(20, 20, 20)
    X, Y, Z = g.coords()
    r = np.sqrt((X - 10) ** 2 + (Y - 10) ** 2 + (Z - 10) ** 2)
    g.where(r < 9.2, '#FFFFFF')
    g.recolour((r > 7.6) & (Z < 8), '#CFE6F7')        # cool underside
    return g, dict(yaw=-34, pitch=64)


def m_coin():
    g = Grid(22, 6, 22)
    X, Y, Z = g.coords()
    rr = np.hypot(X - 11, Z - 11)
    g.where((rr < 10) & (Y > 1) & (Y < 5), '#F2A20F')
    g.where((rr < 10) & (Y > 0) & (Y < 2), '#FFC629')
    g.recolour((rr < 7) & (Y < 1.5), '#FFD84A')
    ang = np.arctan2(Z - 11, X - 11) - np.pi / 2
    k = np.cos(np.pi / 5) / np.cos((ang % (2 * np.pi / 5)) - np.pi / 5)
    star = np.hypot(X - 11, Z - 11) < 4.6 * (0.45 + 0.55 * (k - np.cos(np.pi / 5)) / (1 - np.cos(np.pi / 5)))
    g.where(star & (Y > 0) & (Y < 1), '#FFF1A0')       # raised star
    g.box(0, 22, 0, 1, 0, 22, None)
    g.where(star & (Y < 1), '#FFF1A0')
    return g, dict(yaw=-24, pitch=80)


def m_gem():
    """Front-facing cut diamond: table + crown band on top, pavilion point below, facets in 4 tones."""
    g = Grid(26, 6, 24)
    X, Y, Z = g.coords()
    cx = 13
    ax = np.abs(X - cx)
    crown = (Z > 15) & (Z < 22) & (ax < 12 - (Z - 15) * 0.75)
    pav = (Z <= 15) & (Z > 1) & (ax < (Z - 1) * 0.86)
    shape = crown | pav
    g.where(shape & (Y > 0) & (Y < 5), '#9A45F0')
    front = shape & (Y < 1)
    g.recolour(front & crown & (ax < 4.5), '#F0D2FF')                                  # table
    g.recolour(front & crown & (ax >= 4.5), '#C98BFF')                                 # crown facets
    g.recolour(front & pav & (X < cx) & ((cx - X) > (Z - 1) * 0.43), '#7A2EE0')       # pavilion, outer left
    g.recolour(front & pav & (X >= cx) & ((X - cx) < (Z - 1) * 0.43), '#B266FF')      # pavilion, inner right
    g.recolour(front & pav & (X >= cx) & ((X - cx) >= (Z - 1) * 0.43), '#5A1BC8')     # pavilion, outer right
    g.recolour(front & (Z > 14) & (Z < 16), '#FFFFFF')                                 # girdle glint
    return g, dict(yaw=-18, pitch=82)

MODELS = dict(snowball=m_snowball, coin=m_coin, gem=m_gem, book=m_book, basket=m_basket, paw=m_paw, clover=m_clover, present=m_present, calendar=m_calendar)


# ---------------------------------------------------------------- mesh + render
def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def srgb_to_lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def faces_of(g):
    """Exposed quads with per-face colour, plus UVs in voxel units / 16 (one stud per 2 voxels)."""
    v = g.v
    nx, ny, nz = v.shape
    pad = np.zeros((nx + 2, ny + 2, nz + 2), np.int16)
    pad[1:-1, 1:-1, 1:-1] = v
    verts, quads, cols, uvs = [], [], [], []
    dirs = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
            ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
            ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
    filled = np.argwhere(v > 0)
    for (dx, dy, dz), corners in dirs:
        nb = pad[filled[:, 0] + 1 + dx, filled[:, 1] + 1 + dy, filled[:, 2] + 1 + dz]
        for (x, y, z) in filled[nb == 0]:
            base = len(verts)
            fuv = []
            for cx, cy, cz in corners:
                p = (x + cx, y + cy, z + cz)
                verts.append(p)
                if dx:
                    fuv.append((p[1] / 16, p[2] / 16))
                elif dy:
                    fuv.append((p[0] / 16, p[2] / 16))
                else:
                    fuv.append((p[0] / 16, p[1] / 16))
            quads.append((base, base + 1, base + 2, base + 3))
            cols.append(srgb_to_lin(hex_rgb(g.pal[int(v[x, y, z])])))
            uvs.append(fuv)
    return verts, quads, cols, uvs


def render(name, out_dir, size=512):
    import bpy

    g, view = MODELS[name]()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    verts, quads, cols, uvs = faces_of(g)
    ctr = np.array(g.v.shape, np.float32) / 2
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(np.array(p) - ctr) for p in verts], [], quads)
    mesh.update()
    uv = mesh.uv_layers.new(name='UV')
    ca = mesh.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='CORNER')
    for i, poly in enumerate(mesh.polygons):
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = uvs[i][k]
            ca.data[li].color = (*cols[i], 1.0)
    obj = bpy.data.objects.new(name, mesh)
    scn.collection.objects.link(obj)

    mat = bpy.data.materials.new('stud')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.55
    col = nt.nodes.new('ShaderNodeVertexColor')
    col.layer_name = 'Col'
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(STUD_PNG)
    tex.image.colorspace_settings.name = 'Non-Color'
    tex.interpolation = 'Cubic'
    uvn = nt.nodes.new('ShaderNodeUVMap')
    uvn.uv_map = 'UV'
    nt.links.new(uvn.outputs['UV'], tex.inputs['Vector'])
    # colour x (2 x texture): the kit rule, because overlay can't darken white
    mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = 2.0
    nt.links.new(tex.outputs['Color'], mul2.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    nt.links.new(col.outputs['Color'], mix.inputs['A'])
    comb = nt.nodes.new('ShaderNodeCombineColor')
    for ch in ('Red', 'Green', 'Blue'):
        nt.links.new(mul2.outputs[0], comb.inputs[ch])
    nt.links.new(comb.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    obj.data.materials.append(mat)

    # light: warm key from upper left, cool sky fill, rim from behind
    def light(kind, energy, rot, colr=(1, 1, 1), size_=None):
        ld = bpy.data.lights.new(kind + str(energy), kind)
        ld.energy = energy
        ld.color = colr
        if size_ is not None:
            ld.angle = size_
        lo = bpy.data.objects.new(ld.name, ld)
        lo.rotation_euler = [math.radians(a) for a in rot]
        scn.collection.objects.link(lo)
    light('SUN', 2.7, (40, 0, -40), (1.0, 0.95, 0.88), math.radians(6))
    light('SUN', 0.55, (65, 0, 150), (0.8, 0.9, 1.0), math.radians(30))
    light('SUN', 1.2, (-55, 0, 30), (1, 1, 1), math.radians(10))
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.85, 0.9, 1.0, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.32
    scn.world = world

    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = float(max(g.v.shape)) * 1.55
    cam = bpy.data.objects.new('cam', cam_d)
    yaw, pitch = math.radians(view['yaw']), math.radians(view['pitch'])
    dist = 100
    # Euler (pitch, 0, yaw) looks along (-sin(yaw)sin(p), cos(yaw)sin(p), -cos(p)); sit opposite that
    cam.location = (dist * math.sin(pitch) * math.sin(yaw), -dist * math.sin(pitch) * math.cos(yaw), dist * math.cos(pitch))
    cam.rotation_euler = (pitch, 0, yaw)
    scn.collection.objects.link(cam)
    scn.camera = cam

    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 64
    scn.cycles.use_denoising = True
    scn.render.film_transparent = True
    scn.render.resolution_x = scn.render.resolution_y = size
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.look = 'None'
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    raw = os.path.join(out_dir, f'_raw_{name}.png')
    scn.render.filepath = raw
    bpy.ops.render.render(write_still=True)
    return raw


def sticker(raw, out, size=512, ink=INK, stroke=14):
    """Crop to the model, square it, and add the HUD's ink outline + a hard ink drop."""
    from PIL import Image, ImageFilter
    im = Image.open(raw).convert('RGBA')
    bb = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    im = im.crop(bb)
    w, h = im.size
    s = int(max(w, h) * 1.0) + stroke * 4
    canvas = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    canvas.paste(im, ((s - w) // 2, (s - h) // 2), im)
    a = canvas.getchannel('A')
    grown = a.filter(ImageFilter.MaxFilter(3))
    for _ in range(stroke // 2 - 1):
        grown = grown.filter(ImageFilter.MaxFilter(3))
    grown = grown.filter(ImageFilter.GaussianBlur(0.8)).point(lambda v: 255 if v > 100 else 0)
    outline = Image.new('RGBA', (s, s), ink + (255,))
    base = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    drop = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    drop.paste(outline, (0, stroke // 2), grown)
    base = Image.alpha_composite(base, drop)
    ol = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ol.paste(outline, (0, 0), grown)
    base = Image.alpha_composite(base, ol)
    base = Image.alpha_composite(base, canvas)
    base.resize((size, size), Image.LANCZOS).save(out)


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    names = sys.argv[2:] or list(MODELS)
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        raw = render(n, out_dir)
        sticker(raw, os.path.join(out_dir, f'icon_{n}.png'))
        os.remove(raw)
        print('icon', n)
