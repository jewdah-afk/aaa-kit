"""Animate the warm (red / orange / yellow) bricks of a finished render: a full hue cycle, then a "crazy" void mode.

    python3 scripts/hue_anim.py <out.mp4> <render.png> [render2.png ...]      (numpy, Pillow, ffmpeg)

Works on rendered stills, so it takes seconds instead of a render per frame. Only pixels that are warm AND saturated
move (wings, belly, lava, glow); charcoal, horns, claws, ground and outline stay put, so the hierarchy is unchanged.
Part 1 (3 s): every warm brick turns through the whole hue wheel together.
Part 2 (5 s): void. Hue rides two crossing waves between violet and magenta, a slow pulse runs outward from the head,
and the hottest bricks spark toward cyan-white at the crest. Pulses are spatial waves at 1.5 Hz or less, not
whole-picture flashes.
This is a look study. In game the same effect needs the warm bricks exported as their own pieces so their colour can
be tweened; that export is not built yet.
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image

out, srcs = sys.argv[1], sys.argv[2:]
ims = [np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255 for p in srcs]
h0 = min(i.shape[0] for i in ims); img = np.concatenate([i[:h0] for i in ims], 1)
H, W = img.shape[:2]


def to_hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.zeros_like(mx); m = d > 1e-6
    hr = ((g - b) / np.where(m, d, 1)) % 6; hg = (b - r) / np.where(m, d, 1) + 2; hb = (r - g) / np.where(m, d, 1) + 4
    h = np.where(mx == r, hr, np.where(mx == g, hg, hb)) / 6; h = np.where(m, h % 1, 0)
    return h, np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0), mx


def to_rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v]); g = np.choose(i, [t, v, v, q, p, p]); b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


h, s, v = to_hsv(img)
warm = ((h < .17) | (h > .95)).astype(np.float32) * np.clip((s - .45) / .15, 0, 1) * np.clip((v - .12) / .1, 0, 1)   # soft mask
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
hot = np.clip((v - .7) / .25, 0, 1) * warm                                # lava, glow, wing edge
tmp = tempfile.mkdtemp(); FPS = 20; k = 0
def save(rgb):
    global k
    o = img * (1 - warm[..., None]) + rgb * warm[..., None]
    Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).save(os.path.join(tmp, 'f%04d.png' % k)); k += 1
for f in range(3 * FPS):                                                  # part 1: the whole wheel
    save(to_rgb((h + f / (3 * FPS)) % 1, s, v))
panel = W / len(ims)
cx_ = (xx % panel) - panel * .3; cy_ = yy - H * .45; rad = np.sqrt(cx_ ** 2 + cy_ ** 2)
for f in range(5 * FPS):                                                  # part 2: void, crazy
    t = f / FPS
    hue = .80 + .07 * np.sin(2 * np.pi * (t * .9 + xx / 210)) + .05 * np.sin(2 * np.pi * (t * 1.3 - yy / 150))
    pulse = np.maximum(0, np.sin(2 * np.pi * (t * 1.5 - rad / 260))) ** 5
    hh = (h + hue) % 1; ss = np.clip(s * (1.05 - .55 * pulse * hot), 0, 1); vv = np.clip(v * (1 + .35 * pulse * (.4 + hot)), 0, 1)
    hh = np.where(pulse * hot > .5, (hh * (1 - pulse) + .52 * pulse) % 1, hh)                 # crest: hottest bricks spark cyan-white
    save(to_rgb(hh, ss, vv))
pat = os.path.join(tmp, 'f%04d.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', pat, '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', out], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', pat, '-vf', 'scale=640:-2,split[a][b];[a]palettegen[p];[b][p]paletteuse', os.path.splitext(out)[0] + '.gif'], check=True)
for i, n in ((10, 'cycle'), (3 * FPS + 28, 'void_a'), (3 * FPS + 63, 'void_b')): Image.open(os.path.join(tmp, 'f%04d.png' % i)).save(os.path.splitext(out)[0] + '_%s.png' % n)
print('HUE_OK', k, 'frames ->', out)
