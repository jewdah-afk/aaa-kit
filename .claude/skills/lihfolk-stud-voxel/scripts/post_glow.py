"""Preview post: single black silhouette outline + Neon-style glow bloom.
py post_glow.py <render_dir> [prefix]   -> writes <name>_fx.png for every <name>.png that has _mask.png (+ optional _glow.png)
_glow.png = glow parts in their colour, everything else black (depth-correct), rendered by the build's glow pass.
"""
import sys, glob, os
import numpy as np
from PIL import Image, ImageFilter, ImageChops


def fx(p, ring=4):
    im = Image.open(p).convert('RGB')
    a = Image.open(p[:-4] + '_mask.png').getchannel('A').point(lambda v: 255 if v > 128 else 0)
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(ring * 2 + 1)), a)
    im.paste((0, 0, 0), mask=edge)
    gp = p[:-4] + '_glow.png'
    if os.path.exists(gp):
        g = Image.open(gp).convert('RGB')
        base = np.asarray(im).astype(np.float32)
        gl = np.asarray(g).astype(np.float32)
        # anti-aliased glow edges are dim, not 'on', and showed as a dark ring: fill a 1 px border with the neighbouring full glow colour
        strong = Image.fromarray(np.where(gl.max(-1, keepdims=True) > 100, gl, 0).astype('uint8'))
        gmx = np.asarray(strong.filter(ImageFilter.MaxFilter(3))).astype(np.float32)          # brightest full-glow neighbour
        inside = (np.asarray(a) > 0)[..., None]
        on = (gl.max(-1, keepdims=True) > 20) & inside
        dim = gl.max(-1, keepdims=True) < 0.85 * gmx.max(-1, keepdims=True)
        gl = np.where(dim, gmx, gl)                                                               # dim AA edge pixel -> neighbour colour
        # GLOW_STRONG=1: eyes throw a wide coloured halo. Default stays subtle.
        if os.environ.get('GLOW_STRONG') == '1':                                   # small eyes: grow the source first, then blur wide
            gs = g.filter(ImageFilter.MaxFilter(9)); lay = ((6, 1.0), (16, .75), (34, .5))
        else:
            gs = g; lay = ((3, 0.35), (8, 0.18))
        bloom = sum(np.asarray(gs.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) * k for r, k in lay)
        if os.environ.get('GLOW_STRONG') == '1':                                   # tint the surface toward the glow colour
            hue = bloom / (bloom.max(-1, keepdims=True) + 1e-3) * 255
            a_ = np.clip(bloom.max(-1, keepdims=True) / 255 * 1.5, 0, .85)
            base = np.where(on, gl, base * (1 - a_) + hue * a_)
        else:
            base = np.where(on, gl, base + bloom)                                      # glow keeps its exact hue; halo only outside
        im = Image.fromarray(np.clip(base, 0, 255).astype('uint8'))
    return im


if __name__ == '__main__':
    d = sys.argv[1]; pre = sys.argv[2] if len(sys.argv) > 2 else ''
    n = 0
    for p in sorted(glob.glob(os.path.join(d, pre + '*.png'))):
        if p.endswith(('_mask.png', '_glow.png', '_fx.png', '_ol.png')) or not os.path.exists(p[:-4] + '_mask.png'): continue
        fx(p).save(p[:-4] + '_fx.png'); n += 1
    print('FX_OK', n)
