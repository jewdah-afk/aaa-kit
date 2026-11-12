"""Post pass for kraken.py (self-contained: copy kraken.py + kraken_post.py together, no other files needed).
Per-colour glow (replaces the GLOW_STRONG pass): eyes (yellow/orange) = tight halo, cyan rune/spots = soft small halo,
one black silhouette outline. Rewrites <out>/render/*_fx.png, then <out>/sheet.png and side_by_side.png (if the concept is found).
Usage (after run_brick.ps1 kraken.py):  py kraken_post.py [out_dir]"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageChops
H = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(H, 'out_kraken*')), key=os.path.getmtime)[-1]
R = os.path.join(OUT, 'render')
LAYERS = {'eye': ((2, .8), (6, .45), (13, .2)), 'cyan': ((2, .5), (6, .22))}       # (blur radius, strength) per glow colour

def fx(p, ring=4):
    im = Image.open(p).convert('RGB')
    a = Image.open(p[:-4] + '_mask.png').getchannel('A').point(lambda v: 255 if v > 128 else 0)
    im.paste((0, 0, 0), mask=ImageChops.subtract(a.filter(ImageFilter.MaxFilter(ring * 2 + 1)), a))
    gl = np.asarray(Image.open(p[:-4] + '_glow.png').convert('RGB')).astype(np.float32)
    base = np.asarray(im).astype(np.float32); on = gl.max(-1) > 20
    cyan = on & (gl[..., 2] > gl[..., 0])
    for key, m in (('cyan', cyan), ('eye', on & ~cyan)):
        src = Image.fromarray((gl * m[..., None]).astype('uint8'))
        bloom = sum(np.asarray(src.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) * k for r, k in LAYERS[key])
        base = base + bloom * (~on)[..., None]
    base[on] = gl[on]
    return Image.fromarray(np.clip(base, 0, 255).astype('uint8'))

fs = []
for p in sorted(glob.glob(os.path.join(R, '*.png'))):
    if p.endswith(('_mask.png', '_glow.png', '_fx.png')) or not os.path.exists(p[:-4] + '_mask.png'): continue
    fx(p).save(p[:-4] + '_fx.png'); fs.append(p[:-4] + '_fx.png')
print('FX_OK', len(fs))

ORDER = ('rest_34', 'rest_side', 'rest_front', 'rest_back', 'head34', 'face', 'headside', 'ortho_front', 'ortho_side', 'ortho_back', 'ortho_top')
def view(p): return os.path.basename(p)[:-7].split('_', 1)[-1]
fs.sort(key=lambda p: (ORDER.index(view(p)) if view(p) in ORDER else 99, view(p)))
T = 450; rows = (len(fs) + 2) // 3
sheet = Image.new('RGB', (3 * T, rows * T), 'white')
for i, p in enumerate(fs): sheet.paste(Image.open(p).convert('RGB').resize((T, T)), ((i % 3) * T, (i // 3) * T))
sheet.save(os.path.join(OUT, 'sheet.png')); print('SHEET_OK', len(fs))

# side_by_side.png: concept crops (top row) vs renders (bottom row)
CON = next((q for q in (os.path.join(H, 'concept_sheet.jpg'), os.path.join(H, '..', 'concepts', 'Kraken_concept.jpg')) if os.path.exists(q)), None)
if CON:
    im = Image.open(CON).convert('RGB'); sx, sy = im.width / 800, im.height / 533          # crop boxes measured on the 800x533 sheet
    C = [(0, 30, 600, 300), (10, 305, 265, 455), (265, 305, 535, 455), (535, 305, 800, 455), (595, 30, 800, 185)]
    Rn = ['rest_34', 'ortho_front', 'ortho_side', 'ortho_back', 'face']
    T = 420; out = Image.new('RGB', (T * 5, T * 2), 'white')
    def fit(a):
        a = a.copy(); a.thumbnail((T, T)); c = Image.new('RGB', (T, T), (200, 200, 205)); c.paste(a, ((T - a.width) // 2, (T - a.height) // 2)); return c
    for i, (b, r) in enumerate(zip(C, Rn)):
        out.paste(fit(im.crop((b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy))), (i * T, 0))
        f = glob.glob(os.path.join(R, '*_%s_fx.png' % r))
        if f: out.paste(fit(Image.open(f[0]).convert('RGB')), (i * T, T))
    out.save(os.path.join(H, 'side_by_side.png')); print('SBS_OK')
