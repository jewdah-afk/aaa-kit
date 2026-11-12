"""Render a stationary material board to MP4 (H.264, 60 fps) + GIF + PNG contact sheet.

    python3 -m tools.celestialrithm.foundry.board --set core12 --seconds 12 --out media/celestialrithm/frontier/board-core12

Keys never move. Each key runs the interaction timeline
Idle -> Anticipation -> Activation -> Peak -> Recovery -> Settle on a stagger,
and a single light sweep visits one key at a time (one attention owner).
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

from . import keycap as kc
from . import materials as M
from .fields import F32, blur, smoothstep
from .optics import hex_rgb, linear_to_srgb

SETS = {
    'core12': M.ORDER_12,
    'extra4': M.ORDER_EXTRA,
    'all16': M.ORDER_12 + M.ORDER_EXTRA,
}


# ----------------------------------------------------------------- timeline
PHASES = [('idle', 0.0), ('anticipation', .18), ('activation', .10), ('peak', .30), ('recovery', .45), ('settle', .9)]


def press_curve(local):
    """Activation envelope for a key whose press starts at local = 0 (seconds).

    Anticipation dips slightly negative (the material inhales), activation is a
    fast ease-out rise, peak holds, recovery eases down, settle is a damped
    spring (critically-underdamped, 2 visible wobbles) back to rest.
    """
    if local < 0:
        return 0.0, 'idle'
    t = local
    a, act, pk, rec, st = .18, .10, .30, .45, .9
    if t < a:
        return -.12 * math.sin(math.pi * t / a), 'anticipation'
    t -= a
    if t < act:
        u = t / act
        return 1 - (1 - u) ** 3, 'activation'
    t -= act
    if t < pk:
        return 1.0, 'peak'
    t -= pk
    if t < rec:
        u = t / rec
        return 1 - u * u * (3 - 2 * u) * .92, 'recovery'
    t -= rec
    if t < st:
        return .08 * math.exp(-t * 4.5) * math.cos(t * 14), 'settle'
    return 0.0, 'idle'


def schedule(n, seconds, first=1.6, gap=.62):
    """Press start times: one sweep of presses after an idle opening, a second pass if time allows."""
    starts = []
    for k in range(n):
        s = first + k * gap
        starts.append([s] + ([s + n * gap + 1.2] if s + n * gap + 1.2 + 2 < seconds else []))
    return starts


# ----------------------------------------------------------------- background
def background(W, Hh, panel):
    yy, xx = np.mgrid[0:Hh, 0:W].astype(F32)
    v = yy / Hh; u = xx / W
    bg = (hex_rgb('#03050c') * (1 - v[..., None]) + hex_rgb('#070d1f') * v[..., None])
    vign = 1 - .45 * (((u - .5) * 1.6) ** 2 + ((v - .5) * 1.8) ** 2)
    bg = bg * vign[..., None]
    # faint square-stud grid: nod to the Stud UI language, sub-threshold contrast
    gs = 24
    gx = np.abs(((xx + gs / 2) % gs) - gs / 2); gy = np.abs(((yy + gs / 2) % gs) - gs / 2)
    stud = (np.maximum(gx, gy) < 7) & (np.maximum(gx, gy) > 5.5)
    bg = bg + stud[..., None] * hex_rgb('#0d1630') * .25
    x0, y0, x1, y1 = panel
    pw, ph = (x1 - x0) / 2, (y1 - y0) / 2
    d = kc.sd_round_rect(xx - (x0 + x1) / 2, yy - (y0 + y1) / 2, pw, ph, 26)
    inside = kc.cover(d)
    plate = hex_rgb('#0a1226') * (1 - .35 * ((yy - y0) / (y1 - y0)))[..., None]
    bg = bg * (1 - inside[..., None]) + plate * inside[..., None]
    # panel bevel: lit top edge, dark bottom, black ink
    rim = kc.cover(d + 3) * (1 - kc.cover(d + 10))
    toplit = np.clip((y0 + 40 - yy) / 40, 0, 1)
    bg = bg + rim[..., None] * (hex_rgb('#1d2b52') * (.5 + toplit[..., None]))
    ink = kc.cover(d) * (1 - kc.cover(d + 3))
    bg = bg * (1 - ink[..., None]) + hex_rgb('#010204') * ink[..., None]
    # accent trims: short cyan bars top/bottom centre and corner brackets (static)
    acc = hex_rgb('#4fb4ff')
    for cy in (y0 + 6, y1 - 7):
        bar = (np.abs(xx - (x0 + x1) / 2) < 110) & (np.abs(yy - cy) < 1.6)
        bg = bg + blur(bar.astype(F32), 3)[..., None] * acc * 1.2 + bar[..., None] * acc * .8
    for (cx, cy, sx, sy) in ((x0 + 26, y0 + 18, 1, 1), (x1 - 26, y0 + 18, -1, 1), (x0 + 26, y1 - 18, 1, -1), (x1 - 26, y1 - 18, -1, -1)):
        br = (((np.abs(yy - cy) < 1.2) & ((xx - cx) * sx > 0) & ((xx - cx) * sx < 46))
              | ((np.abs(xx - cx) < 1.2) & ((yy - cy) * sy > 0) & ((yy - cy) * sy < 22)))
        bg = bg + br[..., None] * acc * .55
    return bg.astype(F32)


# ----------------------------------------------------------------- board
class Board:
    def __init__(self, ids, cols, W=1280, Hh=720, seed=7, quality='high', shell=None, reduced_motion=False):
        self.ids, self.cols = ids, cols
        self.rows = math.ceil(len(ids) / cols)
        self.W, self.H = W, Hh
        self.shell = shell or kc.Shell()
        gapx, gapy = 30, 34
        bw = cols * self.shell.w + (cols - 1) * gapx
        bh = self.rows * self.shell.h + (self.rows - 1) * gapy
        self.ox = (W - bw) // 2 + self.shell.w // 2
        self.oy = (Hh - bh) // 2 + self.shell.h // 2 - 6
        self.centres = [(self.ox + (i % cols) * (self.shell.w + gapx), self.oy + (i // cols) * (self.shell.h + gapy)) for i in range(len(ids))]
        pad = 46
        self.panel = ((W - bw) // 2 - pad, (Hh - bh) // 2 - pad + 4, (W + bw) // 2 + pad, (Hh + bh) // 2 + pad - 4)
        self.bg = background(W, Hh, self.panel)
        fw, fh = self.shell.face_w, self.shell.face_h
        self.mats = [M.REGISTRY[m](fw, fh, seed=seed + i, quality=quality) for i, m in enumerate(ids)]
        self.tints = [M.REGISTRY[m].tint() for m in ids]
        self.timing = {m: [] for m in ids}
        self.reduced = reduced_motion

    def render(self, t, starts, sweep_period=4.8):
        canvas = self.bg.copy()
        phases = []
        n = len(self.ids)
        tt = t * (.2 if self.reduced else 1.0)
        for i, (mat, tint, (cx, cy)) in enumerate(zip(self.mats, self.tints, self.centres)):
            p, ph = 0.0, 'idle'
            for s in starts[i]:
                q, qph = press_curve(t - s)
                if qph != 'idle':
                    p, ph = q, qph
            t0 = time.perf_counter()
            face, glow = mat.frame(tt, max(p, 0.0) if not self.reduced else 0.0)
            self.timing[self.ids[i]].append((time.perf_counter() - t0) * 1000)
            # one sweep owner at a time, cycling through keys
            k = int(t / sweep_period * n * .5) % n if not self.reduced else -1
            local = (t / sweep_period * n * .5) % 1
            sweep = local * 1.3 - .15 if (k == i and local < .7) else -1
            exposure = 1 + .1 * min(p, 0)                     # anticipation dims slightly
            kc.compose(canvas, cx, cy, self.shell, face * exposure, glow, tint, tt, sweep=sweep, press=max(p, 0))
            phases.append(ph)
        return np.clip(linear_to_srgb(canvas) * 255 + .5, 0, 255).astype(np.uint8), phases


def encode(frames_iter, out_mp4, W, Hh, fps):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{Hh}', '-r', str(fps), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
           '-movflags', '+faststart', '-r', str(fps), str(out_mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for f in frames_iter:
        p.stdin.write(f.tobytes()); n += 1
    p.stdin.close(); p.wait()
    if p.returncode:
        raise SystemExit('ffmpeg failed')
    return n


def make_gif(mp4, gif, width=560, fps=15, start=0, dur=6):
    span = ['-ss', str(start)] + (['-t', str(dur)] if dur else [])
    vf = f'fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=255:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *span, '-i', str(mp4), '-vf', vf, '-loop', '0', str(gif)], check=True)


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                          'stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_frames',
                          '-show_entries', 'format=duration', '-of', 'json', str(path)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', default='core12', choices=list(SETS))
    ap.add_argument('--ids', default='', help='comma list overrides --set')
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--seconds', type=float, default=12)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--out', required=True, help='output path stem (no extension)')
    ap.add_argument('--still', type=float, default=None, help='render one frame at this time to <out>.png and exit')
    ap.add_argument('--reduced-motion', action='store_true')
    ap.add_argument('--gif-width', type=int, default=560)
    a = ap.parse_args()
    ids = [s for s in a.ids.split(',') if s] or SETS[a.set]
    W, Hh = map(int, a.size.split('x'))
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    board = Board(ids, a.cols, W, Hh, seed=a.seed, reduced_motion=a.reduced_motion)
    starts = schedule(len(ids), a.seconds)
    if a.still is not None:
        n = int(a.still * 60)
        img = None
        for i in range(n + 1):
            img, _ = board.render(i / 60, starts)
        Image.fromarray(img).save(out.with_suffix('.png'))
        print('still', out.with_suffix('.png'))
        return
    total = int(round(a.seconds * a.fps))
    keep = {int(total * f) for f in (.08, .3, .5, .72)}
    stills = {}
    phase_log = []
    t_start = time.perf_counter()

    def gen():
        for i in range(total):
            img, ph = board.render(i / a.fps, starts)
            phase_log.append(ph)
            if i in keep:
                stills[i] = img
            yield img
    n = encode(gen(), out.with_suffix('.mp4'), W, Hh, a.fps)
    wall = time.perf_counter() - t_start
    make_gif(out.with_suffix('.mp4'), out.with_suffix('.gif'), width=a.gif_width)
    ks = sorted(stills)
    sheet = Image.new('RGB', (W, Hh * len(ks)))
    for j, k in enumerate(ks):
        sheet.paste(Image.fromarray(stills[k]), (0, Hh * j))
    sheet.save(out.with_name(out.name + '-sheet.png'), optimize=True)
    pr = probe(out.with_suffix('.mp4'))
    st = pr['streams'][0]
    timing = {m: {'mean_ms': round(float(np.mean(v)), 2), 'p95_ms': round(float(np.percentile(v, 95)), 2)} for m, v in board.timing.items()}
    meta = {'ids': ids, 'cols': a.cols, 'size': [W, Hh], 'seed': a.seed, 'seconds': a.seconds, 'fps_requested': a.fps,
            'frames_rendered': n, 'mp4': {k: st.get(k) for k in ('codec_name', 'profile', 'pix_fmt', 'width', 'height', 'r_frame_rate', 'avg_frame_rate', 'nb_read_frames')},
            'duration_s': float(pr['format']['duration']), 'reduced_motion': a.reduced_motion,
            'offline_ms_per_face_python': timing, 'wall_s': round(wall, 1),
            'note': '60 fps here is the encoded output cadence of an offline NumPy render. It says nothing about Roblox runtime frame time.',
            'press_starts_s': starts}
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ('frames_rendered', 'mp4', 'duration_s', 'wall_s')}))


if __name__ == '__main__':
    main()
