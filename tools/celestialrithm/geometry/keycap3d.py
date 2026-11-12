#!/usr/bin/env python3
"""Stepped-bevel Stud UI keycap as a real mesh, face textured with an animated foundry
material, black inverted-hull outline, rendered as a slow camera turntable/tilt.
The key itself never moves (VISUAL_APPROVAL_CONTRACT: stationary keys).

    python3 tools/celestialrithm/geometry/keycap3d.py [--material hydroglass] [--fps 60]
        [--seconds 7] [--w 960] [--h 540] [--frames N (debug: render only N frames)]
"""
import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(REPO))
import voxel as V  # noqa: E402
import look as L   # noqa: E402

OUT = REPO / 'media/celestialrithm/frontier/geometry'

# ---- shape (world units; Z up). One voxel = 1/8 unit. Numbers are data, kept here.
VOX = 0.125
FACE_HALF = (2.5, 1.5)          # material face
BEZEL = 0.5                     # bezel ring width around the face
RECESS = 2                      # face sits this many voxels below the bezel top
BANDS = [                       # (outward step from bezel, z0, z1) top band first
    (0.25, 0.75, 1.125),
    (0.50, 0.375, 0.75),
    (0.75, 0.0, 0.375),
]
CAP_Z = (1.125, 1.625)
CORNER_R = 0.0
DIST, LENS = 17.0, 50

FACE, RIM, BEZ, B1, B2, B3, LIP_BEZ, LIP1, LIP2, LIP3 = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10


def palette_for(mat_cls):
    p = mat_cls.PALETTE
    b1, b2, b3 = _mix(p['base'], '#2a3350', .45), _mix(p['shadow'], '#1d2440', .3), _mix(p['shadow'], '#0e1226', .45)
    return {FACE: p['base'], RIM: p['rim'], BEZ: '#3a4363', LIP_BEZ: _mix('#3a4363', p['highlight'], .32),
            B1: b1, B2: b2, B3: b3,
            LIP1: _mix(b1, p['highlight'], .26), LIP2: _mix(b2, p['highlight'], .22), LIP3: _mix(b3, p['highlight'], .18)}


def _mix(a, b, t):
    ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)]); cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)])
    c = (ca * (1 - t) + cb * t).round().astype(int)
    return '#%02x%02x%02x' % tuple(c)


def build_grid():
    fx, fy = FACE_HALF
    bx, by = fx + BEZEL, fy + BEZEL
    top = CAP_Z[1]
    g = V.make_grid((-bx - 1, -by - 1, 0), (bx + 1, by + 1, top), VOX)
    for i, (step, z0, z1) in enumerate(BANDS):
        hz = (z1 - z0) / 2
        V.voxelize(g, lambda p, s=step, z0=z0, hz=hz: V.sd_round_box(p, (0, 0, z0 + hz), (bx + s, by + s, hz), CORNER_R),
                   (B1, B2, B3)[i])
    hz = (CAP_Z[1] - CAP_Z[0]) / 2
    V.voxelize(g, lambda p: V.sd_round_box(p, (0, 0, CAP_Z[0] + hz), (bx, by, hz), CORNER_R), BEZ)
    # controlled highlight: the outer 1-voxel ring of every step's top layer is a lighter lip
    for (step, z0, z1), lip in zip(BANDS, (LIP1, LIP2, LIP3)):
        ring = lambda p, s=step, z1=z1: V.op_subtract(V.sd_box(p, (0, 0, z1 - VOX / 2), (bx + s, by + s, VOX / 2)),
                                                    V.sd_box(p, (0, 0, z1 - VOX / 2), (bx + s - VOX, by + s - VOX, VOX)))
        V.paint(g, ring, lip)
    ring = lambda p: V.op_subtract(V.sd_box(p, (0, 0, top - VOX / 2), (bx, by, VOX / 2)),
                                   V.sd_box(p, (0, 0, top - VOX / 2), (bx - VOX, by - VOX, VOX)))
    V.paint(g, ring, LIP_BEZ)
    # recess: carve RECESS voxels, then paint the floor FACE and the walls RIM
    rz = RECESS * VOX
    V.carve(g, lambda p: V.sd_box(p, (0, 0, top - rz / 2 + VOX), (fx, fy, rz / 2 + VOX)))
    V.paint(g, lambda p: V.sd_box(p, (0, 0, top - rz - VOX / 2), (fx + VOX, fy + VOX, VOX / 2)), RIM)
    V.paint(g, lambda p: V.sd_box(p, (0, 0, top - rz - VOX / 2), (fx - .01, fy - .01, VOX / 2)), FACE)
    V.paint(g, lambda p: V.sd_box(p, (0, 0, top - rz / 2), (fx + VOX, fy + VOX, rz / 2)), RIM)
    removed = V.keep_connected(g)
    return g, removed


def face_overlay(fw, fh):
    """Static glass treatment baked over the face: inner AO at the recess walls and a
    thin clearcoat lip along the top edge (multiplier, additive) in linear."""
    y, x = np.mgrid[0:fh, 0:fw].astype(np.float32)
    e = np.minimum(np.minimum(x, fw - 1 - x), np.minimum(y, fh - 1 - y))
    ao = 0.72 + 0.28 * np.clip(e / (fh * .09), 0, 1)
    lip = np.exp(-((y - fh * .05) / (fh * .022)) ** 2) * np.clip((fw * .47 - np.abs(x - fw / 2)) / (fw * .06), 0, 1)
    return ao.astype(np.float32), lip.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--material', default='hydroglass')
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--seconds', type=float, default=7.0)
    ap.add_argument('--w', type=int, default=960); ap.add_argument('--h', type=int, default=540)
    ap.add_argument('--frames', type=int, default=0)
    ap.add_argument('--debug-at', type=float, default=-1, help='debug: render one still at this time')
    ap.add_argument('--tmp', default=None)
    a = ap.parse_args()
    from tools.celestialrithm.foundry import materials as M
    from tools.celestialrithm.foundry.optics import linear_to_srgb

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(a.tmp or tempfile.mkdtemp(prefix='keycap3d_'))
    tmp.mkdir(parents=True, exist_ok=True)
    T = L.Timer()
    with T('build'):
        g, removed = build_grid()
        naive, greedy = V.mesh_grid(g, False), V.mesh_grid(g, True)
        assert V.is_watertight(greedy)[0]
    mat_cls = M.REGISTRY[a.material]
    cols = palette_for(mat_cls)
    fw, fh = 320, 192
    mat = mat_cls(fw, fh, seed=1)
    ao, lip = face_overlay(fw, fh)

    sc = L.reset()
    L.setup_workbench(sc, a.w, a.h)
    face_img = L.image_from_array('face', np.zeros((fh, fw, 3), np.float32))
    pal = L.Palette(cols, panels={FACE: face_img})
    L.add_voxel_object('keycap', greedy, pal, outline=0.045, uv_override={FACE: 'planar'})
    cam = L.add_camera(sc, (0, -9, 7), (0, 0, 0.6), lens=LENS)
    bg = L.backdrop(a.w, a.h, top='#39436e', bottom='#121628', glow=(.30, .34, .50))

    n = a.frames or int(round(a.seconds * a.fps))
    total = int(round(a.seconds * a.fps))
    enc = L.Encoder(OUT / 'keycap3d.mp4', a.w, a.h, a.fps)
    sheet, labels = [], []
    sheet_at = set(np.linspace(0, n - 1, 8).round().astype(int).tolist())
    dist, tgt = DIST, np.array([0, -0.2, 0.25])
    t_start = time.perf_counter()
    for f in range(n):
        t = f / a.fps
        ph = t / a.seconds
        az = math.radians(-26 * math.cos(2 * math.pi * ph))                 # slow turntable
        el = math.radians(38 + 8 * math.sin(2 * math.pi * ph))               # slow tilt
        loc = tgt + dist * np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        L.aim(cam, loc.tolist(), tgt.tolist())
        press = float(np.clip(1 - abs(t - 3.6) / 0.25, 0, 1)) if 3.35 < t < 3.85 else 0.0
        with T('material'):
            rgb, glow = mat.frame(t, press)
            # view-dependent sheen: the clearcoat lip and a soft band follow the camera azimuth
            s = (np.arange(fw)[None, :] / fw - 0.5) - math.sin(az) * 0.9
            band = np.exp(-(s / 0.06) ** 2) * 0.06
            lin = rgb * ao[..., None] * (1 + 0.25 * press) + (lip * 0.16 + band)[..., None] * np.array([.85, .95, 1.0])
            L.set_pixels(face_img, linear_to_srgb(np.clip(lin, 0, 1)))
        if a.debug_at >= 0 and abs(t - a.debug_at) > 0.5 / a.fps:
            continue
        with T('render'):
            rgba = L.render_rgba(sc, tmp / 'f.png')
        with T('composite'):
            frame = L.composite(rgba, L.drop_shadow(bg, rgba[..., 3], dy=int(a.h * .05), sigma=a.h * .03, k=.55))
            enc.write(frame)
        if f in sheet_at:
            sheet.append(frame); labels.append(f't={t:.2f}s az={math.degrees(az):+.0f} el={math.degrees(el):.0f}')
        if a.debug_at >= 0:
            from PIL import Image
            Image.fromarray((frame * 255).astype(np.uint8)).save(tmp / f'still_{a.debug_at:.2f}.png'); break
    enc.close()
    wall = time.perf_counter() - t_start
    if n < total or a.debug_at >= 0:
        print('debug run', n, 'frames', T.t); return
    L.contact_sheet(sheet, OUT / 'keycap3d_sheet.png', cols=4, cell_w=360, labels=labels)
    gif = L.make_gif(OUT / 'keycap3d.mp4', OUT / 'keycap3d.gif', width=480, fps=20)
    probe = L.ffprobe(OUT / 'keycap3d.mp4')
    meta = {
        'what': 'stepped-bevel Stud UI keycap mesh, animated foundry material face, inverted-hull outline',
        'material': a.material, 'engine': 'BLENDER_WORKBENCH (flat lighting, baked direction tones, world cavity)',
        'blender': __import__('bpy').app.version_string,
        'video': probe, 'requested_fps': a.fps, 'interpolated_frames': 0,
        'seconds_per_frame': {k: round(v / n, 4) for k, v in T.t.items() if k != 'build'},
        'wall_seconds_per_frame': round(wall / n, 4), 'build_seconds': round(T.t['build'], 3),
        'mesh': {**V.report(naive, greedy), 'voxels': g.count(), 'voxel_size': VOX, 'islands_removed': removed,
                 'outline_hull_quads': greedy.n_quads, 'tris_rendered_incl_hull': 4 * greedy.n_quads},
        'face_texture_px': [fw, fh], 'gif': gif,
        'bytes': {p.name: p.stat().st_size for p in OUT.glob('keycap3d*') if p.suffix != '.json'},
        'camera': f'azimuth -26..+26 deg, elevation 30..46 deg, distance {DIST}, lens {LENS} mm; key static',
        'press': 'one light-only press at t=3.6 s (material drop + exposure lift, no movement)',
    }
    (OUT / 'keycap3d.json').write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
