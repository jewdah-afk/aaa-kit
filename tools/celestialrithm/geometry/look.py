"""Stylized stud look for headless Blender (Workbench engine) + media helpers.

Why Workbench: on this box EEVEE costs ~5 s per 640x360 frame (software EGL);
Workbench costs ~0.1-0.4 s, which makes real 60 fps renders feasible.

How the look is made (all baked, so the render is exactly what we art-direct):
  * Flat lighting + Texture colour mode. Every (palette colour, face direction)
    pair gets a tiny material whose image is colour x direction tone x stud tile.
    Tones are a fixed 'one hue, four jobs' ladder: light top, main front, side,
    dark underside, with a cool shift into shadow.
  * Top faces carry our procedural square stud (world-aligned UVs, one stud per unit).
  * Outline = inverted hull (voxel.hull_quads) in black + Workbench backface culling.
  * Animated panels (keycap face, gem) are images rewritten every frame from the
    foundry materials.
  * Background is a soft vertical gradient composited after render (film transparent).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np

# direction tones (linear multipliers) for a light from upper-left-front; order = voxel.DIRS
TONE = np.array([0.66, 0.86, 0.58, 0.80, 1.00, 0.42], np.float32)       # +X -X +Y -Y +Z -Z
SHADOW_TINT = np.array([0.93, 0.96, 1.06], np.float32)                   # cool shift on dark faces


def hex_lin(h):
    h = h.lstrip('#')
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def tone_colour(lin, d):
    t = TONE[d]
    shade = lin * t
    k = (1 - t) / (1 - TONE.min())                       # 0 on the top face, 1 on the underside
    return shade * (1 + (SHADOW_TINT - 1) * k)


def stud_tile(n=64):
    """Our own square stud as a multiplier tile (n x n, 1.0 = plate). Raised square
    boss with a lit upper-left bevel, shaded lower-right bevel, a soft contact shadow
    on the plate and a faint seam at the tile border."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    u = x / n - 0.5; v = 0.5 - y / n                        # v up
    half, bev = 0.25, 0.045
    m = np.ones((n, n), np.float32)
    # contact shadow (offset down-right) on the plate
    sd = np.maximum(np.abs(u - 0.03), np.abs(v + 0.03)) - half
    m *= 1 - 0.18 * np.clip(1 - sd / 0.06, 0, 1) * (sd > 0)
    d = np.maximum(np.abs(u), np.abs(v)) - half
    inside = d <= 0
    top = d <= -bev
    m[inside] = 1.03
    # bevel ring: lit if the outward direction faces up-left
    ring = inside & ~top
    face_up_left = np.where(np.abs(u) > np.abs(v), -np.sign(u), np.sign(v))
    m[ring] = np.where(face_up_left[ring] > 0, 1.20, 0.80)
    m[top] = 1.04 + 0.04 * np.clip((v[top] - u[top]) * 2, -1, 1)
    edge = np.minimum(np.minimum(x, n - x), np.minimum(y, n - y))
    m *= np.where(edge < 1.0, 0.93, 1.0)
    return m


# ---------------------------------------------------------------- Blender scene

def reset():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_workbench(sc, w, h, aa='16', cavity=True):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.display.render_aa = aa
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'TEXTURE'
    sh.show_backface_culling = True
    sh.show_specular_highlight = False
    sh.show_object_outline = False
    sh.show_cavity = cavity
    if cavity:
        sh.cavity_type = 'WORLD'
        sh.cavity_ridge_factor = 0.6
        sh.cavity_valley_factor = 0.9
        sc.display.matcap_ssao_distance = 0.35
        sc.display.matcap_ssao_attenuation = 1.0
        sc.display.matcap_ssao_samples = 16
    return sh


def image_from_array(name, rgb_srgb, alpha=None):
    """bpy image from an (h, w, 3) sRGB float array (row 0 = top)."""
    import bpy
    h, w = rgb_srgb.shape[:2]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h, alpha=True)
    set_pixels(img, rgb_srgb, alpha)
    return img


def set_pixels(img, rgb_srgb, alpha=None):
    h, w = rgb_srgb.shape[:2]
    a = np.ones((h, w, 1), np.float32) if alpha is None else alpha[..., None].astype(np.float32)
    px = np.concatenate([np.clip(rgb_srgb, 0, 1).astype(np.float32), a], -1)[::-1]
    img.pixels.foreach_set(px.ravel())
    img.update()


def tex_material(name, img, interp='Linear', extension='REPEAT'):
    import bpy
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img; tex.interpolation = interp; tex.extension = extension
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    nt.nodes.active = tex
    mat.use_backface_culling = True
    return mat


class Palette:
    """Materials for (colour id, direction) pairs. `studded` ids get the stud tile on
    top faces; `panels` maps colour id -> a shared bpy image (animated material)."""

    def __init__(self, colours, studded=(), stud_n=64, panels=None, ink='#05060b'):
        self.colours = {k: hex_lin(v) for k, v in colours.items()}
        self.studded = set(studded)
        self.panels = panels or {}
        self.stud = stud_tile(stud_n)
        self.slots, self.mats = {}, []
        self.ink = hex_lin(ink)

    def slot(self, cid, d):
        key = (int(cid), int(d))
        if key in self.slots:
            return self.slots[key]
        if cid in self.panels:
            img = self.panels[cid][d] if isinstance(self.panels[cid], dict) else self.panels[cid]
            mat = tex_material(f'panel_{cid}_{d}', img, extension='EXTEND')
        else:
            lin = tone_colour(self.colours[cid], d)
            if cid in self.studded and d == 4:
                rgb = lin_srgb(lin[None, None, :] * self.stud[..., None])
            else:
                rgb = np.broadcast_to(lin_srgb(lin), (4, 4, 3)).copy()
            img = image_from_array(f'c{cid}_d{d}', rgb.astype(np.float32))
            mat = tex_material(f'c{cid}_d{d}', img)
        self.slots[key] = len(self.mats)
        self.mats.append(mat)
        return self.slots[key]

    def ink_slot(self):
        if ('ink', 0) not in self.slots:
            img = image_from_array('ink', np.broadcast_to(lin_srgb(self.ink), (4, 4, 3)).copy().astype(np.float32))
            self.slots[('ink', 0)] = len(self.mats)
            self.mats.append(tex_material('ink', img))
        return self.slots[('ink', 0)]


def add_voxel_object(name, mesh, pal: Palette, studs_per_unit=1.0, outline=0.06, uv_override=None,
                     weights=None):
    """Greedy mesh + inverted hull -> one bpy object. uv_override: {colour id: 'planar'}.
    weights: {group: bool mask over quads}; the hull copies the weights of its quad."""
    from voxel import build_bpy, hull_quads
    uv = mesh.stud_uv(studs_per_unit)
    for cid, mode in (uv_override or {}).items():
        m = mesh.colour == cid
        if m.any() and mode == 'planar':
            uv[m] = mesh.planar_uv(m)[m]
    quads = mesh.world()
    slots = np.array([pal.slot(c, d) for c, d in zip(mesh.colour, mesh.dirs)], np.int32)
    cols = np.ones((mesh.n_quads, 4), np.float32)
    cols[:, :3] = [pal.colours.get(int(c), np.ones(3)) for c in mesh.colour]
    w = weights
    if outline > 0:
        hq = hull_quads(mesh, outline)
        quads = np.concatenate([quads, hq])
        uv = np.concatenate([uv, np.zeros_like(uv)])
        slots = np.concatenate([slots, np.full(mesh.n_quads, pal.ink_slot(), np.int32)])
        cols = np.concatenate([cols, np.tile([0, 0, 0, 1], (mesh.n_quads, 1)).astype(np.float32)])
        if weights:
            w = {k: np.concatenate([v, v]) for k, v in weights.items()}
    return build_bpy(name, quads, uv, cols, slots, pal.mats, w)


def add_camera(sc, loc, target, lens=50, ortho=None):
    import bpy
    from mathutils import Vector
    cam = bpy.data.cameras.new('cam')
    if ortho:
        cam.type = 'ORTHO'; cam.ortho_scale = ortho
    cam.lens = lens
    cam.clip_start = 0.1; cam.clip_end = 500
    ob = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(ob)
    sc.camera = ob
    aim(ob, loc, target)
    return ob


def aim(cam_ob, loc, target):
    from mathutils import Vector
    cam_ob.location = Vector(loc)
    cam_ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def render_rgba(sc, path):
    """Render the current frame; returns float RGBA array (h, w, 4) sRGB, row 0 = top."""
    import bpy
    from PIL import Image
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return np.asarray(Image.open(path).convert('RGBA'), np.float32) / 255


def backdrop(w, h, top='#232a4a', bottom='#0b0d1a', glow=None):
    """Vertical gradient with a soft centre lift, sRGB float (h, w, 3)."""
    y = np.linspace(0, 1, h)[:, None, None]
    a = np.array([int(top[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    b = np.array([int(bottom[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    g = a * (1 - y) + b * y
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (0.55 * w)) ** 2 + ((yy - h * 0.45) / (0.55 * h)) ** 2)
    lift = np.clip(1 - r, 0, 1)[..., None] ** 2
    col = np.array([0.20, 0.24, 0.40]) if glow is None else np.asarray(glow)
    return np.clip(g + lift * col * 0.35, 0, 1).astype(np.float32)


def drop_shadow(bg, alpha, dy=20, sigma=12.0, k=0.5):
    """Darken the backdrop under a blurred, downward-offset copy of the alpha."""
    from PIL import Image, ImageFilter
    a = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    s = np.asarray(a, np.float32) / 255
    s = np.roll(s, dy, 0)
    s[:dy] = 0
    return bg * (1 - k * s)[..., None]


def composite(rgba, bg):
    a = rgba[..., 3:4]
    return rgba[..., :3] * a + bg * (1 - a)


# ---------------------------------------------------------------- encoding + metadata

class Encoder:
    """Pipe raw RGB frames to ffmpeg -> H.264 yuv420p MP4."""

    def __init__(self, path, w, h, fps, crf=20):
        self.path = str(path)
        self.p = subprocess.Popen(
            ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
             '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
             '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', self.path],
            stdin=subprocess.PIPE)

    def write(self, rgb01):
        self.p.stdin.write((np.clip(rgb01, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def make_gif(mp4, gif, width=480, fps=20, max_mb=4.0):
    for w, f in ((width, fps), (int(width * 0.8), fps), (int(width * 0.66), 15)):
        vf = f'fps={f},scale={w}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(mp4), '-vf', vf, str(gif)], check=True)
        if Path(gif).stat().st_size <= max_mb * 1e6:
            return {'width': w, 'fps': f, 'bytes': Path(gif).stat().st_size}
    return {'width': w, 'fps': f, 'bytes': Path(gif).stat().st_size, 'warning': 'over size cap'}


def contact_sheet(frames, path, cols=4, cell_w=320, labels=None):
    from PIL import Image, ImageDraw
    ims = [Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8)) for f in frames]
    ar = ims[0].height / ims[0].width
    cw, chh = cell_w, int(cell_w * ar)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw + (cols + 1) * 6, rows * chh + (rows + 1) * 6), (8, 9, 16))
    dr = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x = 6 + (i % cols) * (cw + 6); y = 6 + (i // cols) * (chh + 6)
        sheet.paste(im.resize((cw, chh), Image.LANCZOS), (x, y))
        if labels:
            dr.text((x + 6, y + 4), labels[i], fill=(235, 235, 245))
    sheet.save(path)


def ffprobe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                          '-show_entries', 'stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration',
                          '-of', 'json', str(path)], capture_output=True, text=True, check=True)
    s = json.loads(out.stdout)['streams'][0]
    num, den = s['r_frame_rate'].split('/')
    return {'codec': s['codec_name'], 'pix_fmt': s['pix_fmt'], 'width': s['width'], 'height': s['height'],
            'fps': round(int(num) / int(den), 3), 'frames': int(s['nb_read_frames']),
            'duration_s': float(s.get('duration', 0))}


class Timer:
    def __init__(self):
        self.t = {}

    def add(self, k, dt):
        self.t[k] = self.t.get(k, 0) + dt

    def __call__(self, k):
        timer = self

        class _C:
            def __enter__(s):
                s.t0 = time.perf_counter()

            def __exit__(s, *a):
                timer.add(k, time.perf_counter() - s.t0)
        return _C()
