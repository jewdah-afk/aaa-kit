"""Algorithm fills for HUD v4 Stud Plates (galaxy, aurora, frost, ember).

Each fill is a 512x256 PNG for a plate face; the plate itself (rim, lip, studs,
sill) is drawn in Figma / Roblox on top. Run: python3 tools/lookdev/stud_fills.py OUTDIR
"""
import sys, os
import numpy as np
from PIL import Image

W, H = 512, 256
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)

def noise(scale, seed):
    """Smooth value noise: random grid upsampled with bicubic, tileable enough for a plate."""
    r = np.random.default_rng(seed)
    g = r.random((max(2, int(H / scale)) + 3, max(2, int(W / scale)) + 3)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((W + int(3 * scale), H + int(3 * scale)), Image.BICUBIC)
    return np.asarray(im, np.float32)[:H, :W] / 255.0

def fbm(scale, seed, oct=5):
    v, a, t = 0, 0.5, 0
    for i in range(oct):
        v = v + noise(scale / 2 ** i, seed + i) * a; t += a; a *= 0.5
    return v / t

def ramp(t, stops):
    t = np.clip(t, 0, 1)[..., None]
    out = np.zeros((H, W, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        k = np.clip((t - p0) / (p1 - p0), 0, 1)
        seg = (t >= p0) & (t <= p1)
        out = np.where(seg, np.array(c0) * (1 - k) + np.array(c1) * k, out)
    return out

def galaxy():
    n = fbm(160, 11); w = fbm(90, 21)
    neb = np.clip((n - 0.38) * 2.4, 0, 1)
    col = ramp(0.25 * Y / H + 0.75 * w, [(0, (40, 10, 90)), (0.45, (150, 40, 200)), (0.7, (250, 90, 190)), (1, (255, 190, 150))])
    base = np.array((22, 10, 60), np.float32)
    img = base * (1 - neb[..., None]) + col * neb[..., None]
    r = np.random.default_rng(5)
    stars = (r.random((H, W)) > 0.993) * (140 + r.random((H, W)) * 115)
    big = (r.random((H, W)) > 0.9993)
    stars = np.maximum(stars, np.asarray(Image.fromarray((big * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(1.6)), np.float32) * 3)
    return np.clip(img + stars[..., None], 0, 255)

def aurora():
    sky = ramp(Y / H, [(0, (6, 22, 48)), (1, (8, 40, 70))])
    out = sky.copy()
    for k, (c, amp, y0, sd) in enumerate([((60, 255, 200), 0.18, 0.45, 3), ((80, 170, 255), 0.14, 0.62, 7), ((190, 120, 255), 0.10, 0.32, 9)]):
        path = y0 + (fbm(220, sd, 3)[H // 2] - 0.5) * amp * 2.6
        d = (Y / H) - path[None, :]
        band = np.where(d >= 0, np.exp(-(d / 0.035) ** 2), np.exp(d / 0.18))  # sharp lower hem, long upward fade
        rays = 0.55 + 0.45 * noise(6, sd + 50)[0][None, :].repeat(H, 0)
        out += np.array(c) * (band * rays)[..., None] * 0.75
    r = np.random.default_rng(2)
    out += ((r.random((H, W)) > 0.996) * 180)[..., None] * (Y < H * 0.6)[..., None]
    return np.clip(out, 0, 255)

def voronoi_edges(cells, seed):
    r = np.random.default_rng(seed)
    pts = r.random((cells, 2)) * (W, H)
    d = np.sqrt((X[..., None] - pts[:, 0]) ** 2 + (Y[..., None] - pts[:, 1]) ** 2)
    s = np.sort(d, axis=2)
    return s[..., 1] - s[..., 0], s[..., 0]

def frost():
    e, d0 = voronoi_edges(34, 4)
    base = ramp(Y / H * 0.7 + fbm(120, 3) * 0.3, [(0, (232, 248, 255)), (0.6, (170, 220, 250)), (1, (120, 190, 240))])
    crack = np.exp(-(e / 1.6) ** 2)
    glint = np.exp(-(e / 7) ** 2) * 0.25
    img = base + (np.array((255, 255, 255)) - base) * (crack * 0.85 + glint)[..., None]
    img -= (np.array((40, 30, 10)) * (crack * 0.15)[..., None])
    return np.clip(img, 0, 255)

def ember():
    e, d0 = voronoi_edges(26, 8)
    base = ramp(fbm(80, 4), [(0, (60, 14, 8)), (1, (120, 30, 10))])
    glow = np.exp(-(e / 2.2) ** 2)
    halo = np.exp(-(e / 10) ** 2) * 0.5
    hot = ramp(glow, [(0, (255, 90, 20)), (1, (255, 230, 140))])
    return np.clip(base * (1 - glow[..., None]) + hot * np.clip(glow + halo, 0, 1)[..., None], 0, 255)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, f in [('galaxy', galaxy), ('aurora', aurora), ('frost', frost), ('ember', ember)]:
        Image.fromarray(f().astype(np.uint8)).save(os.path.join(out, f'fill_{name}.png'))
        print('wrote', name)
