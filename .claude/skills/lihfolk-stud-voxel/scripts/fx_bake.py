"""Bake effects onto a render in 3D: effects are computed per BRICK from a position pass, not per screen pixel.

    python3 scripts/fx_bake.py <out.mp4> --grid nx,ny,nz --mouth x,y,z [--hue 0.78] <view_fx.png> [more views ...]

Each <view_fx.png> needs its position pass next to it (<view>_pos.png, written by a model file's pos_pass: 16-bit,
RGB = the brick coordinates of the face under the pixel, scaled 0..1 over the grid). --grid is the grid size in
bricks and --mouth the brick-grid position (0..1) the pulse starts from. Needs numpy, Pillow and ffmpeg.

Because every pixel knows its brick, the effects follow the model's shape and step brick by brick:
  wing wave    colour bands travel outward along the wing span (distance from the body's centre plane)
  body wave    a second band runs head to tail through lava and belly
  twinkle      about one warm brick in eight flares briefly, each on its own clock (hash of its brick position)
  mouth pulse  a shell expands from the mouth through the whole body every 2 s and lights the bricks it crosses
Only warm, saturated pixels change (wings, belly, lava, glow). Plays the base colours first, then the --hue variant.
A look study: in game the same waves need a per-brick band number exported with the mesh (not built yet).
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image

a = sys.argv[1:]; out = a[0]; opt = {}; views = []
i = 1
while i < len(a):
    if a[i].startswith('--'): opt[a[i][2:]] = a[i + 1]; i += 2
    else: views.append(a[i]); i += 1
GRID = np.array([float(v) for v in opt['grid'].split(',')]); MOUTH = np.array([float(v) for v in opt['mouth'].split(',')]) * GRID
HUE2 = float(opt.get('hue', .78)); FPS = 20; SECS = 4


def read16(p):
    w, h = Image.open(p).size
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', p, '-pix_fmt', 'rgba64le', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint16).reshape(h, w, 4).astype(np.float32) / 65535


def to_hsv(x):
    mx = x.max(-1); mn = x.min(-1); d = mx - mn; r, g, b = x[..., 0], x[..., 1], x[..., 2]; m = d > 1e-6; dd = np.where(m, d, 1)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6
    return np.where(m, h % 1, 0), np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0), mx


def to_rgb(h, s, v):
    i_ = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    return np.stack([np.choose(i_, [v, q, p, p, t, v]), np.choose(i_, [t, v, v, q, p, p]), np.choose(i_, [p, p, t, v, v, q])], -1)


imgs, poss = [], []
for v in views:
    imgs.append(np.asarray(Image.open(v).convert('RGB')).astype(np.float32) / 255)
    poss.append(read16(v.replace('_fx.png', '_pos.png')))
img = np.concatenate(imgs, 1); pos = np.concatenate(poss, 1)
on = pos[..., 3] > .5; B = pos[..., :3] * GRID                             # brick coordinates per pixel
h, s, v = to_hsv(img)
warm = ((h < .17) | (h > .95)) * np.clip((s - .45) / .15, 0, 1) * np.clip((v - .12) / .1, 0, 1) * on
hot = np.clip((v - .7) / .25, 0, 1) * warm
span = np.abs(B[..., 0] - GRID[0] / 2)                                     # distance from the centre plane = along the wing
along = B[..., 2]                                                          # head to tail
key = np.round(B * 2).astype(np.int64); hsh = ((key[..., 0] * 73856093) ^ (key[..., 1] * 19349663) ^ (key[..., 2] * 83492791)) & 0xFFFF
ph = hsh / 65535.0; sparkler = ph < .125; ph2 = ((hsh * 2654435761) & 0xFFFF) / 65535.0
rm = np.sqrt(((B - MOUTH) ** 2).sum(-1))
tmp = tempfile.mkdtemp(); k = 0
for part, base in enumerate((0.0, HUE2)):
    for f in range(SECS * FPS):
        t = f / FPS
        wing = np.sin(2 * np.pi * (t * .8 - span / 70)); body = np.sin(2 * np.pi * (t * .6 - along / 120))
        hue = base + .045 * wing + .03 * body
        tw = np.where(sparkler, np.maximum(0, np.sin(2 * np.pi * (t * 1.1 + ph2))) ** 10, 0)
        shell = np.exp(-((rm - (t % 2.0) / 2.0 * 520) / 22) ** 2)         # expanding pulse, 22 bricks thick
        gain = 1 + .30 * np.maximum(wing, 0) * (.3 + hot) + .9 * tw + .7 * shell
        hh = (h + hue) % 1; ss = np.clip(s * (1 - .5 * tw - .35 * shell * hot), 0, 1); vv = np.clip(v * gain, 0, 1)
        rgb = to_rgb(hh, ss, vv); o = img * (1 - warm[..., None]) + rgb * warm[..., None]
        Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).save(os.path.join(tmp, 'f%04d.png' % k)); k += 1
pat = os.path.join(tmp, 'f%04d.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', pat, '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', out], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', pat, '-vf', 'scale=640:-2,split[a][b];[a]palettegen[p];[b][p]paletteuse', os.path.splitext(out)[0] + '.gif'], check=True)
for i_, n in ((14, 'a'), (SECS * FPS + 9, 'b'), (SECS * FPS + 47, 'c')): Image.open(os.path.join(tmp, 'f%04d.png' % i_)).save(os.path.splitext(out)[0] + '_%s.png' % n)
print('FX_BAKE_OK', k, 'frames ->', out)
