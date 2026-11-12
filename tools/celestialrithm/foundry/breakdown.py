"""Layer breakdown reel for one material (Hydroglass): every stage of the chain, animated.

    python3 -m tools.celestialrithm.foundry.breakdown --out media/celestialrithm/frontier/breakdown-hydroglass --seconds 8

Panels: 1 height field (noise swell + wave sim) | 2 surface normals | 3 photon-splat caustics
        4 graded base + glints | 5 final face | 6 the finished key (shell + face)
A press lands at 3.0 s so the wave ring is visible travelling through every stage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import keycap as kc
from . import materials as M
from .board import encode, make_gif, press_curve, probe
from .fields import F32, resize
from .optics import linear_to_srgb, tonemap

W, H = 1280, 720
FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
LABELS = ['1  height field: 3D-noise swell + wave equation', '2  normals from the height gradient (x4 for display)', '3  caustics: Snell refraction, photon splat',
          '4  graded depth colour + Blinn glints', '5  final face (tonemapped)', '6  in the Stud UI keycap shell']


def to8(rgb):
    return np.clip(linear_to_srgb(rgb) * 255 + .5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=8)
    ap.add_argument('--fps', type=int, default=60)
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    sh = kc.Shell()
    mat = M.Hydroglass(sh.face_w, sh.face_h, seed=4); mat.debug = {}
    pw, ph = 392, 182
    font = ImageFont.truetype(FONT, 15)
    total = int(a.seconds * a.fps)
    keep = {int(total * f) for f in (.3, .42, .7)}
    stills = {}

    def gen():
        for i in range(total):
            t = i / a.fps
            p, _ = press_curve(t - 3.0)
            face, glow = mat.frame(t, max(p, 0))
            d = mat.debug
            h = d['height']; hn = (h - h.min()) / (np.ptp(h) + 1e-6)
            nx, ny, nz = d['normals']
            panels = [np.repeat(hn[..., None], 3, -1) ** 2.2,
                      (np.stack([np.clip(nx * 4, -1, 1) * .5 + .5, np.clip(ny * 4, -1, 1) * .5 + .5, nz], -1)) ** 2.2,
                      tonemap(np.repeat(np.clip(d['caustics'] / 3, 0, 1.5)[..., None], 3, -1) * np.array([.55, .95, 1.0], F32)),
                      tonemap(d['base'] + d['glints'][..., None]),
                      face]
            canvas = np.zeros((H, W, 3), F32) + np.array([.006, .008, .016], F32)
            cells = [(20 + (k % 3) * (pw + 22), 70 + (k // 3) * (ph + 110)) for k in range(6)]
            for k, pan in enumerate(panels):
                x, y = cells[k]
                canvas[y:y + ph, x:x + pw] = resize(pan.astype(F32), pw, ph)
            key = np.zeros((ph + 70, pw + 40, 3), F32) + np.array([.006, .008, .016], F32)
            kc.compose(key, (pw + 40) // 2, (ph + 70) // 2 - 4, sh, face, glow, M.Hydroglass.tint(), t, press=max(p, 0))
            x, y = cells[5]
            canvas[y - 20:y - 20 + ph + 70, x - 20:x - 20 + pw + 40] = key
            img = Image.fromarray(to8(canvas)); dr = ImageDraw.Draw(img)
            for k, (x, y) in enumerate(cells):
                dr.text((x, y + ph + (34 if k == 5 else 8)), LABELS[k], font=font, fill=(205, 220, 245))
            dr.text((20, 8), f'Hydroglass layer breakdown   t = {t:5.2f} s   press = {max(p, 0):.2f}', font=font, fill=(140, 170, 220))
            f = np.asarray(img)
            if i in keep:
                stills[i] = f
            yield f
    n = encode(gen(), out.with_name(out.name + '.mp4'), W, H, a.fps)
    make_gif(out.with_name(out.name + '.mp4'), out.with_name(out.name + '.gif'), width=560, fps=15, start=2.0, dur=5)
    ks = sorted(stills)
    sheet = Image.new('RGB', (W, H * len(ks)))
    for j, k in enumerate(ks):
        sheet.paste(Image.fromarray(stills[k]), (0, H * j))
    sheet.save(out.with_name(out.name + '-sheet.png'), optimize=True)
    st = probe(out.with_name(out.name + '.mp4'))['streams'][0]
    out.with_name(out.name + '.json').write_text(json.dumps({'frames_rendered': n, 'mp4': st, 'material': 'hydroglass', 'seed': 4, 'press_at_s': 3.0}, indent=1))
    print(n, st['avg_frame_rate'])


if __name__ == '__main__':
    main()
