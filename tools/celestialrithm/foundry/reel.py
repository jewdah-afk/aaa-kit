"""Comparison reel: approved floor -> previous implementation -> first pass -> after QA -> layer breakdown.

    python3 -m tools.celestialrithm.foundry.reel --out media/celestialrithm/frontier/comparison-reel

Each segment is labelled with what it is and its true source cadence; GIF sources
are frame-held to 60 fps (a 9 fps GIF shown at 60 fps is still 9 unique frames
per second, and the label says so).
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .board import encode, make_gif, probe

ROOT = Path(__file__).resolve().parents[3]
M = ROOT / 'media/celestialrithm'
W, H, FPS = 1280, 720, 60
FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'


def fit(img, bg=(3, 5, 12)):
    im = Image.fromarray(img) if isinstance(img, np.ndarray) else img
    s = min(W / im.width, (H - 70) / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    out = Image.new('RGB', (W, H), bg); out.paste(im, ((W - im.width) // 2, 60 + (H - 60 - im.height) // 2))
    return out


def label(img, title, sub):
    d = ImageDraw.Draw(img)
    d.text((24, 14), title, font=ImageFont.truetype(FONT, 24), fill=(235, 242, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((24, 44), sub, font=ImageFont.truetype(FONT, 14), fill=(150, 175, 220))
    return np.asarray(img)


def gif_frames(path):
    im = Image.open(path); fr = []
    for i in range(im.n_frames):
        im.seek(i); fr.append((im.convert('RGB'), im.info.get('duration', 100) / 1000))
    return fr


def mp4_frames(path, start, dur):
    pr = probe(path)['streams'][0]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(start), '-t', str(dur), '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, pr['height'], pr['width'], 3)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out)
    segs = []

    def gif_segment(path, seconds, title, sub):
        fr = gif_frames(path); t = 0.0; k = 0; acc = fr[0][1]; n = int(seconds * FPS)
        lab = [label(fit(f), title, sub) for f, _ in fr]
        for i in range(n):
            t = i / FPS
            while t >= acc:
                k = (k + 1) % len(fr); acc += fr[k][1]
            yield lab[k]
        segs.append({'title': title, 'source': str(Path(path).relative_to(ROOT)), 'seconds': seconds, 'unique_frames_per_s': round(len(fr) / sum(d for _, d in fr), 1)})

    def still_segment(path, seconds, title, sub):
        f = label(fit(Image.open(path).convert('RGB')), title, sub)
        for _ in range(int(seconds * FPS)):
            yield f
        segs.append({'title': title, 'source': str(Path(path).relative_to(ROOT)), 'seconds': seconds, 'unique_frames_per_s': 0})

    def mp4_segment(path, start, seconds, title, sub):
        for f in mp4_frames(path, start, seconds):
            yield label(fit(f), title, sub)
        segs.append({'title': title, 'source': str(Path(path).relative_to(ROOT)), 'seconds': seconds, 'unique_frames_per_s': 60})

    def gen():
        yield from gif_segment(M / 'approved-material-visual-target.gif', 4, '1  Approved visual floor', 'reference GIF · 16 frames at ~9 fps, upscaled 3x · the minimum target')
        yield from gif_segment(M / 'engineering-v1-preview.gif', 3, '2  Previous implementation (engineering v1)', 'sine-sum fields · source GIF 30 frames at 15 fps · below the floor')
        yield from still_segment(M / 'frontier/lineage/round0-first-pass.jpg', 2, '3  Foundry, first pass (still)', 'real field methods, before QA: gloss wash, weak solar / holo / crystal')
        yield from mp4_segment(M / 'frontier/board-core12.mp4', 1.4, 6, '4  Foundry after 6 QA rounds', '60 fps offline render · stationary keys · press timeline per key')
        yield from mp4_segment(M / 'frontier/breakdown-hydroglass.mp4', 2.6, 4, '5  Layer breakdown: Hydroglass', 'height -> normals -> refraction caustics -> grade -> face -> shell')
    n = encode(gen(), out.with_suffix('.mp4'), W, H, FPS)
    make_gif(out.with_suffix('.mp4'), out.with_suffix('.gif'), width=480, fps=12, start=0, dur=19)
    st = probe(out.with_suffix('.mp4'))['streams'][0]
    out.with_suffix('.json').write_text(json.dumps({'frames': n, 'mp4': st, 'segments': segs}, indent=1))
    print(n, st['avg_frame_rate'])


if __name__ == '__main__':
    main()
