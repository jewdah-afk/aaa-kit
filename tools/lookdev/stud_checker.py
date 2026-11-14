"""Bake the HUD's 4x4 on/off stud checker from the map's square stud tile.

The map floor reads as a checker of light and dark 4x4-stud blocks; the HUD's clickable
buttons and hotbar slots wear the same pattern. Input: the kit's roblox_square_studs.png
(8x8 studs, 64 px per stud, studs centred in their cells). Output, all 512 px = 8x8 studs:
  studs_checker_overlay.png  neutral grey, for a Figma IMAGE fill (TILE, OVERLAY)
  studs_checker_light.png / studs_checker_dark.png  Roblox stand-ins for the overlay
  studs_checker_blocks.png  the 4x4 on/off blocks alone (NORMAL blend), visible on any face colour
1:1 rule: in the UI one stud is always STUD_PX (12 px at 1080p), so the tile is drawn at
8 * STUD_PX = 96 px and every studded face is a multiple of 4 studs (48 px).

Run: python3 tools/lookdev/stud_checker.py OUTDIR [block_offset] [contrast]
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = os.path.join(HERE, '..', '..', '.claude', 'skills', 'lihfolk-stud-voxel', 'assets', 'roblox_square_studs.png')
STUD = 64          # px per stud in the source tile
BLOCK = 4          # studs per checker block


def bake(out_dir, offset=42.0, contrast=1.9):
    a = np.asarray(Image.open(TILE).convert('L'), np.float32)
    a = 128 + (a - a.mean()) * contrast
    y, x = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    parity = ((x // (STUD * BLOCK)) + (y // (STUD * BLOCK))) % 2      # 0 = light block, 1 = dark block
    a = np.clip(a + np.where(parity == 0, offset, -offset), 0, 255)
    Image.fromarray(a.astype(np.uint8)).convert('RGB').save(os.path.join(out_dir, 'studs_checker_overlay.png'))
    light = np.clip((a - 128) / 127, 0, 1)
    dark = np.clip((128 - a) / 128, 0, 1)
    for name, rgb, al in (('studs_checker_light', 255, light), ('studs_checker_dark', 0, dark)):
        im = np.zeros(a.shape + (4,), np.uint8)
        im[..., :3] = rgb
        im[..., 3] = (al * 255).astype(np.uint8)
        Image.fromarray(im, 'RGBA').save(os.path.join(out_dir, name + '.png'))
    # block mask: the on/off pattern alone, so it reads even on white faces where overlay can't
    blk = np.zeros(a.shape + (4,), np.uint8)
    blk[..., :3] = np.where(parity[..., None] == 1, 0, 255)
    blk[..., 3] = np.where(parity == 1, 38, 22).astype(np.uint8)        # dark blocks 15% black, light 9% white
    Image.fromarray(blk, 'RGBA').save(os.path.join(out_dir, 'studs_checker_blocks.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    bake(out, *(float(v) for v in sys.argv[2:4]))
    print('wrote studs_checker_overlay.png, studs_checker_light.png, studs_checker_dark.png')
