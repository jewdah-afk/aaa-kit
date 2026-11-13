"""Split the map's stud tile into two Roblox-ready layers, plus the plate glow.

Roblox ImageLabels have no overlay blend. Overlay on a neutral-grey tile is "lighten
where it is brighter than 128, darken where it is darker", so we bake those halves:
  studs_light.png  white, alpha = how much brighter than mid grey
  studs_dark.png   black, alpha = how much darker than mid grey
Stacked as two tiled ImageLabels over any face colour they read like the Figma overlay.
glow_9slice.png is a soft white rounded rect for the plate glow (SliceCenter 64,64,64,64).

Run: python3 tools/lookdev/stud_overlay_split.py OUTDIR [contrast]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = os.path.join(HERE, '..', '..', '.claude', 'skills', 'lihfolk-stud-voxel', 'assets', 'roblox_square_studs.png')


def split(out_dir, contrast=2.1):
    a = np.asarray(Image.open(TILE).convert('L'), np.float32)
    a = np.clip(128 + (a - a.mean()) * contrast, 0, 255)       # same boost as the Figma UI tile
    light = np.clip((a - 128) / 127, 0, 1)
    dark = np.clip((128 - a) / 128, 0, 1)
    for name, rgb, alpha in (('studs_light', 255, light), ('studs_dark', 0, dark)):
        im = np.zeros(a.shape + (4,), np.uint8)
        im[..., :3] = rgb
        im[..., 3] = (alpha * 255).astype(np.uint8)
        Image.fromarray(im, 'RGBA').save(os.path.join(out_dir, name + '.png'))


def glow(out_dir, size=256, inset=64, radius=40, blur=22):
    m = Image.new('L', (size, size), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).rounded_rectangle((inset, inset, size - inset, size - inset), radius=radius, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    im = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    im.putalpha(m)
    im.save(os.path.join(out_dir, 'glow_9slice.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    split(out, float(sys.argv[2]) if len(sys.argv) > 2 else 2.1)
    glow(out)
    print('wrote studs_light.png, studs_dark.png, glow_9slice.png')
