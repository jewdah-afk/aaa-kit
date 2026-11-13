"""Scorecard for the brick creatures: the same measures for every model, from the brick grid itself.

    python3 scripts/scorecard.py dump [name ...]      needs Blender's bpy; runs each example once, caches its grid
    python3 scripts/scorecard.py score [name ...]     numpy + Pillow only; writes examples/SCORECARD.md + views
    python3 scripts/scorecard.py baseline             freeze today's scores as examples/BASELINE.json
    python3 scripts/scorecard.py check                fail if any model scores below its baseline
    python3 scripts/scorecard.py file <model.py> <concept.jpg>     score one new model file (dump + score), no baseline

Why not score the Blender renders: they take minutes and change with the Blender version. The grid is exact. Each
model is projected to flat front / side / back views at one pixel per brick with a fixed "measuring light"
(surface colour x form shading x cavity shading from local depth), and every measure is taken on that image.
It is a measuring instrument, not the beauty render: the eye still judges the Blender sheet.

Measures (per model; view measures are the mean of front, side and back):
  match      best silhouette overlap (IoU, 0-1) between the model's side / front view and any view on its concept sheet
  bands      how many of the 8 OKLab lightness bands hold at least 3 % of the visible surface   (HIERARCHY.md s11 bands)
  edges      share of surface pixels on a lightness step of one band or more (Rosenholtz edge density); 8-25 % reads as texture, more is clutter
  flat       share of the surface with no edge within 3 bricks: featureless area
  contrast   mean lightness step across those edges, in bands
  relief     share of the interior surface sitting 0.75 brick or more proud of, or recessed from, its surroundings: real layering
  backed     share of the lightness edges that sit on a real depth step (geometry) and not on paint
  small      share of the surface detail that survives shrinking the model to 48 px tall (phone far view)
  at100      the same at the size the model has on a 844x390 phone from 100 studs away
  structure  0-100 summary of bands, edges, flat, relief and backed (formula in structure())
Rules and cost: solid colours (<= 16), glow share (<= 4 % unless GLOW: strong), triangles of the largest piece (<= 20,000).
"""
import os, sys, json, glob, shutil, subprocess, tempfile, time
import numpy as np

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get('SV_CACHE', os.path.join(tempfile.gettempdir(), 'sv_cache'))
EX = os.path.join(SKILL, 'examples')
SKIP = {'props', 'terrain', 'shop', 'tower', 'gate', 'arcane_train'}
ANCHORS = ('swamp_croc', 'war_rhino', 'kraken')                # looks the owner approved by eye
SMALL = 48                                                     # px tall: a boss far off or in a crowd on a phone
EDGE = 1.0                                                     # a lightness edge = a step of one full band or more
TOL = dict(match=.02, structure=1.0, small=.03)               # check: a model may not drop by more than this

INNER = r'''
import sys, json, runpy, numpy as np
f, out, scripts = sys.argv[1], sys.argv[2], sys.argv[3]; sys.argv = [f]
sys.path.insert(0, scripts); import brick_rig
real = brick_rig.export
def wrapped(ID, OUT, lo, kind, col, RIG, overrides=(), glow=None, **kw):
    g = {int(k): [float(c) for c in v] for k, v in (glow or {}).items()}
    np.savez_compressed(out + '.npz', kind=kind.astype(np.int8), col=np.round(np.clip(col, 0, 1) * 255).astype(np.uint8), lo=np.asarray(lo, float))
    json.dump(dict(id=ID, bones=len(RIG), glow=g), open(out + '.json', 'w'))
    kw['render'] = False
    return real(ID, OUT, lo, kind, col, RIG, overrides, glow=glow, **kw)
brick_rig.export = wrapped
runpy.run_path(f, run_name='__main__')
'''


def names(want):
    all_ = sorted(f[:-len('_brick.py')] for f in os.listdir(os.path.join(EX, 'brick')) if f.endswith('_brick.py'))
    return [n for n in all_ if n not in SKIP and (not want or n in want)]


def dump_file(path, key):
    """run one model file in a temp copy of the skill; cache its grid, bone count and triangle counts under `key`"""
    os.makedirs(CACHE, exist_ok=True)
    tmp = tempfile.mkdtemp(); sk = os.path.join(tmp, 'sk'); shutil.copytree(SKILL, sk, ignore=shutil.ignore_patterns('out_*', 'previews'))
    bd = os.path.join(sk, 'examples', 'brick'); dst = os.path.join(bd, os.path.basename(path))
    if not os.path.exists(dst): shutil.copy(path, dst)
    open(os.path.join(tmp, 'inner.py'), 'w').write(INNER)
    t = time.time(); out = os.path.join(CACHE, key)
    r = subprocess.run([sys.executable, os.path.join(tmp, 'inner.py'), dst, out, os.path.join(sk, 'scripts')], cwd=bd, capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if not os.path.exists(out + '.json'):
        print(key, 'DUMP_FAIL', (r.stdout + r.stderr)[-400:]); return False
    j = json.load(open(out + '.json')); j['build_s'] = round(time.time() - t)
    for l in r.stdout.splitlines():
        if l.startswith('RIG_EXPORT'): j['pieces'] = int(l.split(' pieces')[0].split()[-1]); j['max_tris'] = int(l.split('max tris ')[1].split()[0])
        if l.startswith('RIG_OK'): j['tris'] = int(l.split(' tris ')[1].split()[0])
    j['strong'] = '# GLOW: strong' in open(path, encoding='utf8').read()
    json.dump(j, open(out + '.json', 'w')); print(key, 'DUMP_OK', j); return True


# ---------------------------------------------------------------- measuring views
def oklab_L(rgb):
    c = rgb / 255.0; c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    l = .4122214708 * c[..., 0] + .5363325363 * c[..., 1] + .0514459929 * c[..., 2]
    m = .2119034982 * c[..., 0] + .6806995451 * c[..., 1] + .1073969566 * c[..., 2]
    s = .0883024619 * c[..., 0] + .2817188376 * c[..., 1] + .6299787005 * c[..., 2]
    return .2104542553 * np.cbrt(l) + .7936177850 * np.cbrt(m) - .0040720468 * np.cbrt(s)


def blur(a, r, w=None):
    """box blur of radius r; with weights w it is a masked mean (ignores pixels outside the silhouette)"""
    w = np.ones_like(a, float) if w is None else w.astype(float)
    def box(v):
        for ax in (0, 1):
            p = np.cumsum(np.pad(v, [(r + 1, r) if k == ax else (0, 0) for k in (0, 1)]), axis=ax)
            v = np.take(p, np.arange(2 * r + 1, p.shape[ax]), axis=ax) - np.take(p, np.arange(0, p.shape[ax] - 2 * r - 1), axis=ax)
        return v
    return box(a * w) / np.maximum(box(w), 1e-9)


def project(kind, col, axis, rev):
    """first solid brick along `axis` (from the far end when rev). Returns colour (H, W, 3), depth, mask, glow; row 0 = top"""
    k, c = kind, col
    if rev: k = np.flip(k, axis); c = np.flip(c, axis)
    s = k > 0; first = np.argmax(s, axis=axis); mask = s.any(axis=axis)
    idx = np.expand_dims(first, axis)
    colour = np.take_along_axis(c, np.expand_dims(idx, -1), axis=axis).squeeze(axis)
    knd = np.take_along_axis(k, idx, axis=axis).squeeze(axis)
    # remaining axes: axis 2 (z) -> (x, y); axis 0 (x) -> (y, z). Make rows = y descending.
    if axis == 2: colour, depth, mask, knd = (np.swapaxes(a, 0, 1)[::-1] for a in (colour, first, mask, knd))
    else: colour, depth, mask, knd = (a[::-1] for a in (colour, first, mask, knd))
    if (axis == 2) == bool(rev): colour, depth, mask, knd = (a[:, ::-1] for a in (colour, depth, mask, knd))    # as the viewer sees it
    return colour.astype(float), depth.astype(float), mask, knd > 1


def shade(colour, depth, mask, glow):
    """the measuring light: form shading from the smoothed depth slope + cavity shading from local relief"""
    d = np.where(mask, depth, 0.0)
    sm = blur(d, 3, mask)
    gy = np.zeros_like(sm); gy[1:-1] = (sm[2:] - sm[:-2]) / 2          # > 0: surface recedes downward = faces up
    form = 1 + .16 * np.clip(-gy, -1, 1)                                # row 0 is the top, so facing up = depth grows upward
    cav = 1 + np.clip(.12 * (sm - d), -.2, .1)                         # proud of its surroundings -> lighter, recessed -> darker
    under = np.zeros_like(d); under[1:] = np.clip(d[1:] - d[:-1], 0, 3) * mask[:-1]   # a lip just above casts a shadow
    lip = 1 - .12 * np.minimum(under, 2)
    f = np.where(glow, 1.0, form * cav * lip)
    img = np.clip(colour * f[..., None], 0, 255)
    return np.where(mask[..., None], img, 255.0), np.where(mask, sm - d, 0.0), d


def crop(m, *arrs):
    ys, xs = np.nonzero(m); sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    return [a[sl] for a in (m,) + arrs]


def view_measures(img, mask, rel, d):
    L = oklab_L(img) * 8                                                # lightness in bands (0..8)
    inside = mask.sum()
    band = np.clip(np.floor(L), 0, 7).astype(int)[mask]
    bands = int((np.bincount(band, minlength=8) / inside >= .03).sum())
    eh = np.zeros_like(mask); ev = np.zeros_like(mask); step = []
    dh = np.abs(L[:, 1:] - L[:, :-1]); okh = mask[:, 1:] & mask[:, :-1]
    dv = np.abs(L[1:] - L[:-1]); okv = mask[1:] & mask[:-1]
    eh[:, 1:] = okh & (dh >= EDGE); ev[1:] = okv & (dv >= EDGE)
    step = np.concatenate([dh[okh & (dh >= EDGE)], dv[okv & (dv >= EDGE)]])
    edge = eh | ev
    sh = np.zeros_like(mask); sv = np.zeros_like(mask)                    # the same pixel pairs with a depth step of a brick or more
    sh[:, 1:] = np.abs(d[:, 1:] - d[:, :-1]) >= 1; sv[1:] = np.abs(d[1:] - d[:-1]) >= 1
    backed = ((eh & sh) | (ev & sv)).sum() / max(1, edge.sum())
    near = blur(edge.astype(float), 3) > 0
    # relief is judged on the interior only: 3 bricks in from the silhouette and away from big depth jumps (leg in front of body),
    # so a smooth round body scores ~0 and only plates, folds and layers 2 bricks or more deep count
    jump = np.zeros_like(mask); jump[:, 1:] |= np.abs(d[:, 1:] - d[:, :-1]) >= 4; jump[1:] |= np.abs(d[1:] - d[:-1]) >= 4
    core = (blur(mask.astype(float), 3) > .999) & ~(blur(jump.astype(float), 3) > 0)
    relief = float((np.abs(rel)[core] >= .75).sum() / max(1, core.sum()))
    hp = np.where(mask, L - blur(L, 4, mask), 0)
    return dict(bands=bands, edges=float(edge.sum() / inside), flat=float((mask & ~near).sum() / inside),
                contrast=float(step.mean()) if len(step) else 0.0, relief=relief,
                backed=float(backed)), L, hp


def resize(a, h, w):
    from PIL import Image
    return np.asarray(Image.fromarray(a.astype(np.float32), mode='F').resize((w, h), Image.BOX if h < a.shape[0] else Image.BILINEAR))


def retained(L, hp, mask, target_h):
    """share of the surface detail (high-pass lightness) left after shrinking the view to target_h pixels and back"""
    H, W = L.shape
    if target_h >= H: return 1.0
    w2 = max(1, round(W * target_h / H))
    Lm = np.where(mask, L, blur(L, 4, mask))
    small = resize(resize(Lm, target_h, w2), H, W)
    hp2 = np.where(mask, small - blur(small, 4, mask), 0)
    a = float(np.sqrt((hp[mask] ** 2).mean())); b = float(np.sqrt((hp2[mask] ** 2).mean()))
    return min(1.0, b / a) if a > 1e-6 else 1.0


def structure(m):
    """0-100. A layered, readable surface has several value bands, an edge share between 8 and 25 %, little
    featureless area, real relief (20 % or more of the surface proud or recessed) and edges backed by geometry."""
    e = m['edges']; es = min(e / .08, 1.0) if e <= .25 else max(0.0, 1 - (e - .25) / .25)
    return 100 * (.2 * (min(m['bands'], 6) - 1) / 5 + .2 * es + .2 * (1 - m['flat']) + .25 * min(m['relief'] / .2, 1) + .15 * m['backed'])


# ---------------------------------------------------------------- match to the concept sheet
def concept_blobs(path):
    from PIL import Image
    im = Image.open(path).convert('RGB'); im.thumbnail((360, 360))
    a = np.asarray(im).astype(int); m = ((a.max(-1) - a.min(-1)) > 28) | (a.mean(-1) < 95)
    lab = np.zeros(m.shape, int); blobs = []; H, W = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]: continue
        st = [(y0, x0)]; lab[y0, x0] = len(blobs) + 1; pts = []
        while st:
            y, x = st.pop(); pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = lab[y0, x0]; st.append((yy, xx))
        if len(pts) >= .012 * H * W:
            p = np.array(pts); b = np.zeros((p[:, 0].max() - p[:, 0].min() + 1, p[:, 1].max() - p[:, 1].min() + 1), bool)
            b[p[:, 0] - p[:, 0].min(), p[:, 1] - p[:, 1].min()] = True
            b = fill_holes(b); blobs.append(b)
    return blobs


def fill_holes(b):
    out = np.pad(~b, 1, constant_values=True); seen = np.zeros_like(out); st = [(0, 0)]; seen[0, 0] = True
    H, W = out.shape
    while st:
        y, x = st.pop()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < H and 0 <= xx < W and out[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; st.append((yy, xx))
    return ~seen[1:-1, 1:-1]


def iou(a, b, h=96):
    def norm(m):
        w = max(1, round(m.shape[1] * h / m.shape[0])); return resize(m.astype(float), h, w) > .5
    a, b = norm(a), norm(b); W = max(a.shape[1], b.shape[1])
    pad = lambda m: np.pad(m, ((0, 0), ((W - m.shape[1]) // 2, W - m.shape[1] - (W - m.shape[1]) // 2)))
    a, b = pad(a), pad(b); return float((a & b).sum() / max(1, (a | b).sum()))


def best_match(mask, blobs):
    return max([max(iou(mask, b), iou(mask[:, ::-1], b)) for b in blobs] or [0.0])


# ---------------------------------------------------------------- one model
def score(key, concept=None, save_views=None):
    z = np.load(os.path.join(CACHE, key + '.npz')); j = json.load(open(os.path.join(CACHE, key + '.json')))
    kind, col = z['kind'], z['col'].copy()
    for k, c in j.get('glow', {}).items(): col[kind == int(k)] = np.round(np.array(c) * 255)
    solid = kind == 1; ix = np.argwhere(kind > 0); ext = ix.max(0) - ix.min(0) + 1
    out = dict(id=j['id'], bones=j['bones'], bricks=int((kind > 0).sum()), studs=[round(float(v) * 2.5) for v in ext],
               colours=int(len(np.unique(col[solid].reshape(-1, 3), axis=0))), glow_share=float((kind > 1).sum() / (kind > 0).sum()),
               max_tris=j.get('max_tris'), tris=j.get('tris'), pieces=j.get('pieces'), build_s=j.get('build_s'), strong=j.get('strong', False))
    h100 = out['studs'][1] / (2 * 100 * np.tan(np.radians(35))) * 390           # px tall on a 844x390 phone at 100 studs, FOV 70
    out['px_at_100'] = round(float(h100))
    acc = {k: [] for k in ('bands', 'edges', 'flat', 'contrast', 'relief', 'backed', 'small', 'at100')}; masks = {}; imgs = {}
    for nm, axis, rev in (('front', 2, False), ('side', 0, True), ('back', 2, True)):
        c, d, m, g = project(kind, col, axis, rev)
        m, c, d, g = crop(m, c, d, g)
        img, rel, dd = shade(c, d, m, g); vm, L, hp = view_measures(img, m, rel, dd)
        for k in ('bands', 'edges', 'flat', 'contrast', 'relief', 'backed'): acc[k].append(vm[k])
        acc['small'].append(retained(L, hp, m, SMALL)); acc['at100'].append(retained(L, hp, m, int(min(h100, 390))))
        masks[nm] = m; imgs[nm] = img
    for k, v in acc.items(): out[k] = float(np.mean(v))
    out['structure'] = structure(out)
    if concept and os.path.exists(concept):
        blobs = concept_blobs(concept)
        out['match_side'] = best_match(masks['side'], blobs); out['match_front'] = best_match(masks['front'], blobs)
        out['match'] = (out['match_side'] + out['match_front']) / 2
    bad = []
    if out['colours'] > 16: bad.append('colours')
    if out['glow_share'] > .04 and not out['strong']: bad.append('glow')
    if out['max_tris'] and out['max_tris'] > 20000: bad.append('triangles')
    out['rules'] = bad
    if save_views:
        from PIL import Image
        os.makedirs(save_views, exist_ok=True)
        for nm, img in imgs.items():
            s = max(1, 440 // max(img.shape[:2]))
            Image.fromarray(img.astype('uint8')).resize((img.shape[1] * s, img.shape[0] * s), Image.NEAREST).save(os.path.join(save_views, '%s_%s.png' % (key, nm)))
    return out


def concept_of(name, ID):
    for c in (ID, ''.join(p.title() for p in name.split('_'))):
        p = os.path.join(EX, 'concepts', c + '_concept.jpg')
        if os.path.exists(p): return p
    return None


COLS = ('match', 'structure', 'bands', 'edges', 'flat', 'contrast', 'relief', 'backed', 'small', 'at100')


def fmt(o, k):
    v = o.get(k)
    if v is None: return 'n/a'
    return {'match': '%.2f', 'structure': '%.0f', 'bands': '%.1f', 'edges': '%.0f %%', 'flat': '%.0f %%', 'contrast': '%.2f', 'relief': '%.0f %%', 'backed': '%.0f %%', 'small': '%.2f', 'at100': '%.2f'}[k] % (v * 100 if k in ('edges', 'flat', 'relief', 'backed') else v)


def table(rows):
    md = ['| Model | Match | Structure | Bands | Edges | Flat | Contrast | Relief | Backed | Small (48 px) | At 100 studs | Colours | Glow | Largest piece (tris) | Rules |', '|' + '---|' * 15]
    for n, o in rows:
        md.append('| %s%s | %s | %d | %.1f %% | %s | %s |' % (n, ' (anchor)' if n in ANCHORS else '', ' | '.join(fmt(o, k) for k in COLS), o['colours'],
                  o['glow_share'] * 100, format(o['max_tris'], ',') if o.get('max_tris') else 'n/a', 'ok' if not o['rules'] else 'FAIL: ' + ', '.join(o['rules'])))
    return md


def main():
    a = sys.argv[1:]; cmd = a[0] if a else 'score'
    if cmd == 'dump':
        for n in names(a[1:]): dump_file(os.path.join(EX, 'brick', n + '_brick.py'), n)
    elif cmd == 'file':
        key = 'file_' + os.path.splitext(os.path.basename(a[1]))[0]
        if dump_file(os.path.abspath(a[1]), key):
            o = score(key, a[2] if len(a) > 2 else None, save_views=os.path.join(CACHE, 'views'))
            print('\n'.join(table([(key[5:], o)]))); json.dump(o, open(os.path.join(CACHE, key + '_score.json'), 'w'), indent=1)
    elif cmd in ('score', 'baseline', 'check'):
        rows = []
        for n in names(a[1:]):
            if not os.path.exists(os.path.join(CACHE, n + '.npz')): print(n, 'not dumped: run `scorecard.py dump` first'); continue
            ID = json.load(open(os.path.join(CACHE, n + '.json')))['id']
            rows.append((n, score(n, concept_of(n, ID), save_views=os.path.join(CACHE, 'views'))))
        md = table(rows); print('\n'.join(md))
        bp = os.path.join(EX, 'BASELINE.json')
        if cmd == 'baseline':
            json.dump({n: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in o.items()} for n, o in rows}, open(bp, 'w'), indent=1)
            open(os.path.join(EX, 'SCORECARD.md'), 'w').write('# Scorecard of the shipped brick creatures\n\nWritten by `scripts/scorecard.py baseline`. '
                 'Measures are defined at the top of that script; they are taken on flat measuring views of the brick grid, not on the Blender renders. '
                 'Frozen in `BASELINE.json`; `scorecard.py check` fails when a model drops below it.\n\n' + '\n'.join(md) + '\n')
            print('BASELINE_OK', len(rows), 'models')
        if cmd == 'check':
            base = json.load(open(bp)); bad = []
            for n, o in rows:
                for k, t in TOL.items():
                    if k in base.get(n, {}) and o.get(k) is not None and o[k] < base[n][k] - t: bad.append('%s %s %.3f < %.3f' % (n, k, o[k], base[n][k]))
                if o['rules'] and not base.get(n, {}).get('rules'): bad.append('%s rules %s' % (n, o['rules']))
            print('SCORE_FAIL ' + '; '.join(bad) if bad else 'SCORE_OK %d models at or above baseline' % len(rows))
            if bad: sys.exit(1)


if __name__ == '__main__':
    main()
