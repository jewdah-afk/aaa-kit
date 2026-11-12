"""Measure a material board against the approved baseline GIF.

    python3 -m tools.celestialrithm.foundry.qa --board media/celestialrithm/frontier/board-core12 \
        --baseline media/celestialrithm/approved-material-visual-target.gif --out media/celestialrithm/frontier/qa-core12

Per face, for both boards (ours is also measured downsampled to the baseline's
face size so resolution can't flatter it):
  colourfulness   Hasler & Suesstrunk 2003 M (sRGB)
  detail          mean |Laplacian| of luminance (structure per pixel)
  motion          mean |frame(t+0.11 s) - frame(t)| (same time step for both)
  hot             fraction of pixels with OKLab L > 0.92 (bright-pixel budget)
  unique          distinct colours after 5-bit quantisation
and board-wide: min/mean pairwise OKLab distance between the 12 faces' mean colours
(material distinctness). Numbers do not decide quality; the side-by-side PNG
written next to the JSON is for the human gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from . import keycap as kc
from .optics import linear_to_oklab, srgb_to_linear

# Face rectangles in the 414x219 approved GIF (x0, y0, x1, y1), inset 4 px from the glass edge.
# Measured from the frame; verified by the crop montage this script writes.
BASE_COLS = [(42, 110), (133, 196), (218, 286), (307, 373)]
BASE_ROWS = [(33, 68), (93, 129), (152, 188)]
BASE_RECTS = [(c[0], r[0], c[1], r[1]) for r in BASE_ROWS for c in BASE_COLS]


def board_rects(meta):
    """Face rects of our board from its saved layout parameters."""
    from .board import Board
    b = Board.__new__(Board)
    W, H = meta['size']; cols = meta['cols']; ids = meta['ids']
    sh = kc.Shell()
    rows = -(-len(ids) // cols)
    gapx, gapy = 30, 34
    bw = cols * sh.w + (cols - 1) * gapx; bh = rows * sh.h + (rows - 1) * gapy
    ox = (W - bw) // 2 + sh.w // 2; oy = (H - bh) // 2 + sh.h // 2 - 6
    g = kc.geometry(sh)
    out = []
    for i in range(len(ids)):
        cx = ox + (i % cols) * (sh.w + gapx); cy = oy + (i // cols) * (sh.h + gapy)
        x0 = int(cx - sh.w / 2) - sh.pad + g['fx0'] + 3; y0 = int(cy - sh.h / 2) - sh.pad + g['fy0'] + 3
        out.append((x0, y0, x0 + sh.face_w - 6, y0 + sh.face_h - 6))
    return out


def read_mp4(path, every=1):
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                    '-of', 'json', str(path)], capture_output=True, text=True, check=True).stdout)['streams'][0]
    W, H = pr['width'], pr['height']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    return fr[::every]


def read_gif(path):
    im = Image.open(path); out = []
    for i in range(im.n_frames):
        im.seek(i); out.append(np.asarray(im.convert('RGB')))
    return np.stack(out), im.info.get('duration', 100) / 1000.0


def colourfulness(rgb):
    r, g, b = [rgb[..., i].astype(np.float64) for i in range(3)]
    rg = r - g; yb = .5 * (r + g) - b
    return float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + .3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))


def lum(rgb):
    return (rgb[..., 0] * .2126 + rgb[..., 1] * .7152 + rgb[..., 2] * .0722).astype(np.float64)


def detail(rgb):
    L = lum(rgb)
    lap = np.abs(4 * L[1:-1, 1:-1] - L[:-2, 1:-1] - L[2:, 1:-1] - L[1:-1, :-2] - L[1:-1, 2:])
    return float(lap.mean())


def face_stats(frames, rect, dt_frames, size=None):
    x0, y0, x1, y1 = rect
    crops = frames[:, y0:y1, x0:x1]
    if size is not None:
        crops = np.stack([np.asarray(Image.fromarray(c).resize(size, Image.LANCZOS)) for c in crops])
    lin = srgb_to_linear(crops.astype(np.float32) / 255)
    lab = linear_to_oklab(lin)
    q = (crops >> 3).astype(np.int32)
    uniq = np.mean([len(np.unique(c[..., 0] * 1024 + c[..., 1] * 32 + c[..., 2])) for c in q])
    mot = np.mean(np.abs(crops[dt_frames:].astype(np.float32) - crops[:-dt_frames].astype(np.float32))) if len(crops) > dt_frames else 0.0
    return {
        'colourfulness': round(float(np.mean([colourfulness(c) for c in crops])), 1),
        'detail': round(float(np.mean([detail(c) for c in crops])), 2),
        'motion': round(float(mot), 2),
        'hot': round(float((lab[..., 0] > .92).mean()), 4),
        'unique': int(uniq),
        'mean_oklab': [round(float(v), 4) for v in lab.reshape(-1, 3).mean(0)],
    }


def distinct(stats):
    m = np.array([s['mean_oklab'] for s in stats])
    d = np.sqrt(((m[:, None] - m[None]) ** 2).sum(-1))
    iu = np.triu_indices(len(m), 1)
    return {'min_pair_dE': round(float(d[iu].min()), 4), 'mean_pair_dE': round(float(d[iu].mean()), 4)}


def summarise(stats):
    keys = ['colourfulness', 'detail', 'motion', 'hot', 'unique']
    return {k: round(float(np.median([s[k] for s in stats])), 4) for k in keys}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', required=True, help='stem of a board render (needs .mp4 + .json)')
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    meta = json.loads(Path(a.board + '.json').read_text())
    base, bdt = read_gif(a.baseline)
    ours = read_mp4(a.board + '.mp4', every=2)              # 30 samples/s is plenty for statistics
    fps = 60 / 2
    step = 0.11                                             # baseline frame interval; same Δt for both
    our_dt = max(1, round(step * fps)); base_dt = 1
    rects = board_rects(meta)
    bsz = (BASE_RECTS[0][2] - BASE_RECTS[0][0], BASE_RECTS[0][3] - BASE_RECTS[0][1])
    b_stats = [face_stats(base, r, base_dt) for r in BASE_RECTS]
    o_stats = [face_stats(ours, r, our_dt) for r in rects]
    o_small = [face_stats(ours, r, our_dt, size=bsz) for r in rects]
    rep = {
        'baseline': {'faces': b_stats, 'median': summarise(b_stats), 'distinct': distinct(b_stats), 'face_px': list(bsz), 'frames': int(len(base))},
        'ours_native': {'ids': meta['ids'], 'faces': o_stats, 'median': summarise(o_stats), 'distinct': distinct(o_stats)},
        'ours_at_baseline_size': {'faces': o_small, 'median': summarise(o_small), 'distinct': distinct(o_small)},
        'notes': ['motion = mean absolute 8-bit change per 0.11 s; baseline is a 16-frame 9 fps loop so its motion is sampled coarser',
                  'colourfulness/detail are descriptive, not a quality verdict; see the montage for the human gate'],
    }
    Path(a.out + '.json').write_text(json.dumps(rep, indent=1))
    # montage: baseline face crops (upscaled) next to ours, row by row, same frame index ratio
    rows = []
    for k in range(12):
        bx = BASE_RECTS[k]; ox = rects[k]
        bc = Image.fromarray(base[len(base) // 2][bx[1]:bx[3], bx[0]:bx[2]]).resize((ox[2] - ox[0], ox[3] - ox[1]), Image.LANCZOS)
        oc = Image.fromarray(ours[len(ours) // 2][ox[1]:ox[3], ox[0]:ox[2]])
        row = Image.new('RGB', (bc.width * 2 + 6, bc.height), (0, 0, 0)); row.paste(bc, (0, 0)); row.paste(oc, (bc.width + 6, 0))
        rows.append(row)
    Wm = rows[0].width; Hm = sum(r.height + 4 for r in rows[:6])
    mont = Image.new('RGB', (Wm * 2 + 12, Hm), (0, 0, 0))
    y = 0
    for k, r in enumerate(rows):
        col = k // 6; yy = (k % 6) * (r.height + 4)
        mont.paste(r, (col * (Wm + 12), yy))
    mont.save(a.out + '-montage.png', optimize=True)
    print(json.dumps({'baseline': rep['baseline']['median'], 'ours_native': rep['ours_native']['median'],
                      'ours_at_baseline_size': rep['ours_at_baseline_size']['median'],
                      'distinct': [rep['baseline']['distinct'], rep['ours_native']['distinct']]}, indent=1))


if __name__ == '__main__':
    main()
