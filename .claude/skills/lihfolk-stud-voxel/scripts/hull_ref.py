# Reference picture -> voxel model -> blueprint. numpy + Pillow only.
# Takes two pictures of the same symmetric model (a front view and a 3/4 view on a plain background) and:
#   1. cuts each silhouette out of the background
#   2. finds the 3/4 camera by silhouette consistency (the carved shape must fill both silhouettes)
#   3. carves a voxel grid: a voxel stays only if it AND its mirror twin land inside every silhouette
#      (mirroring makes two pictures work like four views)
#   4. colours each surface voxel from the picture that sees it best, then snaps to a small palette
#   5. traces the front silhouette into outline vertices, mirrors them and lifts them onto the shape
# and writes the same blueprint as blueprint.py (anchors, rings, slots, views).
# What no picture shows (the back, the underside, anything hidden) is filled in by the carve, not known.
#
# Run: python3 scripts/hull_ref.py front.png threequarter.png --name EmberDragonRef --out out_ref
#        [--az 35 --el 14 --front-el 8] [--free-angles] [--cell 2] [--ring 6] [--html page.html --block blueprint-ref] [--luau M.luau]
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blueprint as BP

TH = 0.36                                                    # half field of view (tan) of the pipeline's 50 mm camera


# ------------------------------------------------------------------ silhouettes
def _erode(m, r):
    o = m.copy()
    for ax in (0, 1):
        t = o.copy()
        for k in range(1, r + 1):
            a = [slice(None)] * 2; b = [slice(None)] * 2
            a[ax] = slice(k, None); b[ax] = slice(None, -k)
            t[tuple(a)] &= o[tuple(b)]; t[tuple(b)] &= o[tuple(a)]
            e = [slice(None)] * 2; e[ax] = slice(0, k); t[tuple(e)] = False
            e[ax] = slice(-k, None); t[tuple(e)] = False
        o = t
    return o


def silhouette(rgb):
    """Model mask of a render on a plain two-tone background (grey sky, green ground)."""
    a = rgb.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sky = a[2, 2]
    is_sky = (np.abs(a - sky).max(-1) <= 6) & (a.max(-1) - a.min(-1) <= 3)
    is_ground = (g - np.maximum(r, b)) > 12
    m = ~(is_sky | is_ground)
    m = _erode(m, 1)                                          # cut hair-thin bridges to specks
    H, W = m.shape
    blur = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W // 16, H // 16), Image.BOX).resize((W, H), Image.BILINEAR)).astype(int)
    sy, sx = np.unravel_index(np.argmax(np.where(m, blur, -1)), m.shape)
    im = Image.fromarray((m * 255).astype(np.uint8)).copy(); ImageDraw.floodfill(im, (int(sx), int(sy)), 128)
    m = np.asarray(im) == 128                                 # the connected piece around the densest spot
    grow = np.pad(m, 1); grow = (grow[1:-1, 1:-1] | grow[:-2, 1:-1] | grow[2:, 1:-1] | grow[1:-1, :-2] | grow[1:-1, 2:])   # give the eroded pixel back
    m = grow & ~(is_sky | is_ground)
    return m | _erode(~_erode(~np.pad(m, 4), 3), 3)[4:-4, 4:-4]   # close pinholes (model pixels that happen to match the background)


def fill_edge(rgb, sil, r=4):
    """Replace the dark outline band just inside the silhouette with the colours next to it."""
    out = rgb.astype(np.float32).copy(); known = _erode(sil, r)
    for _ in range(3 * r):
        todo = sil & ~known
        if not todo.any(): break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src_k = np.roll(known, (dy, dx), (0, 1)); take = todo & src_k & ~known
            out[take] = np.roll(out, (dy, dx), (0, 1))[take]; known = known | take
    return out


# ------------------------------------------------------------------ cameras
def camera(az, el, c, dist):
    a, e = math.radians(az), math.radians(el)
    dv = np.array((math.cos(e) * math.sin(a), math.sin(e), -math.cos(e) * math.cos(a)))
    r = np.cross(dv, (0, 1.0, 0)); r /= np.linalg.norm(r); u = np.cross(r, dv)
    return dict(az=float(az), el=float(el), c=np.asarray(c, float), dv=dv, r=r, u=u, dist=float(dist), th=TH)


def pixels(cam, P, size):
    q = P - cam['c']; d = cam['dist'] - q @ cam['dv']
    px = ((q @ cam['r']) / d / TH + 1) * size / 2; py = (1 - (q @ cam['u']) / d / TH) * size / 2
    return px, py, d


def _view(cam, P, S):
    """Voxel centres -> pixel index in a picture reduced to about one voxel per pixel, and depth."""
    R = max(16, int(2 * TH * cam['dist'] * .8)); px, py, d = pixels(cam, P, R)
    return R, np.clip(px.astype(int), 0, R - 1) + R * np.clip(py.astype(int), 0, R - 1), d


def inside(cam, P, sil):
    S = sil.shape[0]; px, py, d = pixels(cam, P, S)
    xi = np.floor(px).astype(int); yi = np.floor(py).astype(int)
    ok = (xi >= 0) & (yi >= 0) & (xi < S) & (yi < S) & (d > 1)
    out = np.zeros(len(P), bool); out[ok] = sil[yi[ok], xi[ok]]
    return out


def carve(cams, sils, P, shape):
    keep = np.ones(shape, bool)
    for cam, sil in zip(cams, sils):
        m = inside(cam, P, sil).reshape(shape)
        keep &= m & m[::-1]                                   # the voxel and its mirror twin
    return keep


def coverage(cams, sils, P, keep):
    """How much of each silhouette the carved shape fills (1 = all of it), measured at about one voxel per pixel."""
    tot = []
    for cam, sil in zip(cams, sils):
        R, pi, _ = _view(cam, P[keep.ravel()], 0)
        small = np.asarray(Image.fromarray((sil * 255).astype(np.uint8)).resize((R, R), Image.BOX)).ravel() > 127
        hit = np.zeros(R * R, bool); hit[pi] = True
        tot.append((hit & small).sum() / max(1, small.sum()))
    return tot


def calibrate(sil_f, sil_q, grid, az, el, front_el, dist_f, dist_q, free_angles=False, log=print):
    """Pattern search for the 3/4 camera position. Two pictures do not pin the angles down (several angle sets
    fill the silhouettes equally well), so they stay at the given values unless free_angles is set."""
    P, shape = grid
    small = [np.asarray(Image.fromarray(s).resize((150, 150), Image.BOX)) for s in (sil_f, sil_q)]
    def cams(x): return [camera(0, x[5], (0, 0, 0), dist_f), camera(x[0], x[1], x[2:5], dist_q)]
    def score(x):
        c = cams(x); return float(np.mean(coverage(c, small, P, carve(c, small, P, shape))))
    best = None
    for az0 in ((az - 10, az, az + 10) if free_angles else (az,)):
        x = np.array([az0, el, 0, 0, 0, front_el], float); step = np.array([4, 3, 8, 8, 12, 2], float); s = score(x)
        while step[0] > .2:
            moved = False
            for i in (range(len(x)) if free_angles else (2, 3, 4)):
                for sg in (1, -1):
                    y = x.copy(); y[i] += sg * step[i]; t = score(y)
                    if t > s + 1e-5: x, s, moved = y, t, True; break
            if not moved: step /= 2
        log('  start az %g -> az %.1f el %.1f front el %.1f, fill %.3f' % (az0, x[0], x[1], x[5], s))
        if best is None or s > best[0]: best = (s, x)
    return cams(best[1]), best[0]


def _shell(solid):
    pad = np.pad(solid, 1); inner = solid.copy(); n = solid.shape
    for ax in range(3):
        for s in (0, 2):
            sl = [slice(1, -1)] * 3; sl[ax] = slice(s, s + n[ax]); inner &= pad[tuple(sl)]
    return solid & ~inner


def photo_carve(solid, lo, cams, pics, tol=60.0, rounds=150, log=print):
    """Space carving: peel surface voxels whose colour in the front picture disagrees with their colour (or their
    mirror twin's colour) in the 3/4 picture. A voxel that is the last cover of a silhouette pixel is never removed."""
    solid = solid.copy(); S = pics[0].shape[0]; n0 = solid.shape[0]
    small = []
    for cam, pic in zip(cams, pics):
        R = max(16, int(2 * TH * cam['dist'] * .8))
        small.append(np.asarray(Image.fromarray(pic).resize((R, R), Image.BOX)).reshape(-1, 3).astype(np.float32))
    for rnd in range(rounds):
        A = np.argwhere(solid); PA = lo + .5 + A
        I = np.argwhere(_shell(solid)); P = lo + .5 + I
        idg = np.full(solid.shape, -1, np.int32); idg[tuple(I.T)] = np.arange(len(I)); twin = idg[n0 - 1 - I[:, 0], I[:, 1], I[:, 2]]
        col, vis, prot = [], [], np.zeros(len(I), bool)
        for cam, sm in zip(cams, small):
            R, pa, _ = _view(cam, PA, S); cnt = np.bincount(pa, minlength=R * R)
            _, pi, d = _view(cam, P, S); zb = np.full(R * R, np.inf); np.minimum.at(zb, pi, d)
            vis.append(d <= zb[pi] + 1.2); col.append(sm[pi]); prot |= cnt[pi] <= 2
        def differ(ca, va, cb, vb): return va & vb & (np.sqrt(((ca - cb) ** 2).sum(1)) > tol)
        bad = differ(col[0], vis[0], col[1], vis[1]) | differ(col[0], vis[0], col[1][twin], vis[1][twin])
        bad |= bad[twin]; bad &= ~prot & ~prot[twin]
        if bad.sum() < max(20, .001 * len(I)): break
        solid[tuple(I[bad].T)] = False
    log('colour carve: %d rounds, %d voxels left' % (rnd + 1, solid.sum()))
    return solid


def depth_limit(solid, lo, cams, depth):
    """No picture shows the back, and the silhouette carve leaves everything behind the model solid. Keep only what
    lies within `depth` voxels behind a surface some picture sees (the mirrored 3/4 view counts as a picture)."""
    A = np.argwhere(solid); PA = lo + .5 + A; keep = np.zeros(solid.shape, bool)
    for k, cam in enumerate(cams):
        R, pa, d = _view(cam, PA, 0); zb = np.full(R * R, np.inf); np.minimum.at(zb, pa, d)
        m = np.zeros(solid.shape, bool); m[tuple(A.T)] = d - zb[pa] <= depth
        keep |= m | m[::-1]
    return solid & keep


# ------------------------------------------------------------------ outline vertices
def trace(mask):
    """Moore boundary of the mask's outer edge, clockwise, as (x, y) pixels."""
    m = np.pad(mask, 1); ys, xs = np.nonzero(m); s = (int(ys[0]), int(xs[0]))
    nb = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]; where = {d: i for i, d in enumerate(nb)}
    pts = [s]; cur = s; back = 0
    for _ in range(4 * m.size):
        for k in range(1, 9):
            i = (back + k) % 8; y, x = cur[0] + nb[i][0], cur[1] + nb[i][1]
            if m[y, x]:
                j = (i - 1) % 8; back = where[(nb[j][0] - nb[i][0], nb[j][1] - nb[i][1])]; cur = (y, x); break
        else: break
        if cur == s: break
        pts.append(cur)
    return np.array([(x - 1, y - 1) for y, x in pts], float)


def simplify(pts, eps):
    """Douglas-Peucker on a closed loop."""
    n = len(pts); far = int(np.argmax(((pts - pts[0]) ** 2).sum(1))); keep = np.zeros(n, bool); keep[[0, far]] = True
    stack = [(0, far), (far, n)]
    while stack:
        a, b = stack.pop(); pa, pb = pts[a], pts[b % n]
        if b - a < 2: continue
        seg = pb - pa; L = np.linalg.norm(seg) + 1e-9; q = pts[a + 1:b] - pa
        d = np.abs(q[:, 0] * seg[1] - q[:, 1] * seg[0]) / L; k = int(np.argmax(d))
        if d[k] > eps: keep[a + 1 + k] = True; stack += [(a, a + 1 + k), (a + 1 + k, b)]
    return pts[keep]


def finish_colour(surf, I, rgb, seen, colours=20, spread=6):
    """Seen surface colours -> full colour grid: spread a few voxels, dark tone for the never-seen, snap to a palette, mirror."""
    shape = surf.shape
    colg = np.zeros((*shape, 3), np.float32); known = np.zeros(shape, bool)
    colg[tuple(I[seen].T)] = rgb[seen]; known[tuple(I[seen].T)] = True
    want = surf & (np.arange(shape[0]) >= shape[0] // 2)[:, None, None]
    for _ in range(spread):                                   # spread seen colours a few voxels over the unseen surface
        todo = want & ~known
        if not todo.any(): break
        got = False
        for ax in range(3):
            for s in (1, -1):
                take = todo & np.roll(known, s, ax) & ~known
                if take.any(): colg[take] = np.roll(colg, s, ax)[take]; known |= take; got = True
        if not got: break
    todo = want & ~known                                      # never shown in a picture: the model's most common dark colour
    if todo.any():
        dark = rgb[seen][rgb[seen].sum(1) < np.median(rgb[seen].sum(1))]
        colg[todo] = np.median(dark, 0); known |= todo
    hc = colg[want]
    pim = Image.fromarray(np.clip(hc, 0, 255).astype(np.uint8).reshape(-1, 1, 3)).quantize(colours, method=Image.Quantize.MEDIANCUT, kmeans=3)
    pal = np.array(pim.getpalette()[:colours * 3], np.float32).reshape(-1, 3); colg[want] = pal[np.asarray(pim).ravel()]
    colg[:shape[0] // 2] = colg[::-1][:shape[0] // 2]          # the -x half is the +x half reflected
    return colg


# ------------------------------------------------------------------ main build
def build(front_img, quarter_img, name='Model', az=35, el=14, front_el=8, cell=2, ring=6, colours=20, eps=7.0, free_angles=False, photo=True, spread=6, depth=12, log=print):
    rgb_f = np.asarray(Image.open(front_img).convert('RGB')); rgb_q = np.asarray(Image.open(quarter_img).convert('RGB'))
    S = rgb_f.shape[0]; assert rgb_f.shape[:2] == (S, S) and rgb_q.shape[:2] == (S, S), 'pictures must be square and the same size'
    sil_f = silhouette(rgb_f); sil_f = sil_f & sil_f[:, ::-1]                    # a symmetric model has a symmetric front view
    sil_q = silhouette(rgb_q)
    log('silhouettes: front %d px, 3/4 %d px' % (sil_f.sum(), sil_q.sum()))

    # world: 1 unit = 1 voxel; the front camera looks at the origin; x = 0 is the mirror plane
    xs = np.nonzero(sil_f.any(0))[0]; ys = np.nonzero(sil_f.any(1))[0]
    dist_f = 176.0; dist_q = 280.0
    hx = math.ceil((xs[-1] - S / 2) / (S / 2) * TH * dist_f * 1.3); hx += hx % 2
    y0 = math.floor((1 - 2 * ys[-1] / S) * TH * dist_f * 1.9); y1 = math.ceil((1 - 2 * ys[0] / S) * TH * dist_f * 1.5)
    hz = int(hx * 1.9)
    lo = np.array((-hx, y0, -hz), float); n = np.array((2 * hx, y1 - y0, 2 * hz))
    def centres(step):
        ax = [lo[i] + step / 2 + np.arange(0, n[i], step) for i in range(3)]
        G = np.stack(np.meshgrid(*ax, indexing='ij'), -1).astype(np.float32)
        return G.reshape(-1, 3), G.shape[:3]
    log('calibrating the 3/4 camera ...')
    cams, fill = calibrate(sil_f, sil_q, centres(3), az, el, front_el, dist_f, dist_q, free_angles, log)
    P, shape = centres(1)
    solid = carve(cams, [sil_f, sil_q], P, shape)
    hull_n = int(solid.sum())
    if photo: solid = photo_carve(solid, lo, cams, (rgb_f, rgb_q), log=log)
    if depth: solid = depth_limit(solid, lo, cams, depth); log('depth limit %g: %d voxels left' % (depth, solid.sum()))
    cov = coverage(cams, [sil_f, sil_q], P, solid)
    log('carved %d voxels in a %s grid; silhouette fill front %.3f, 3/4 %.3f' % (solid.sum(), 'x'.join(map(str, shape)), *cov))

    # ---- colour: each surface voxel from the picture that sees it most face-on
    pad = np.pad(solid, 1); inner = solid.copy()
    for ax in range(3):
        for s in (0, 2):
            sl = [slice(1, -1)] * 3; sl[ax] = slice(s, s + n[ax]); inner &= pad[tuple(sl)]
    surf = solid & ~inner
    f = pad.astype(np.float32)
    for _ in range(2):
        for ax in range(3): f = (np.roll(f, 1, ax) + f + np.roll(f, -1, ax)) / 3
    nrm = np.stack([np.roll(f, 1, ax) - np.roll(f, -1, ax) for ax in range(3)], -1)[1:-1, 1:-1, 1:-1]
    I = np.argwhere(surf); Ps = lo + .5 + I; Ns = nrm[tuple(I.T)]; Ns /= np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-6)
    half = Ps[:, 0] > 0
    best = np.full(len(Ps), .08); rgb = np.zeros((len(Ps), 3), np.float32); seen = np.zeros(len(Ps), bool)
    for cam, pic, sil in zip(cams, (rgb_f, rgb_q), (sil_f, sil_q)):
        clean = fill_edge(pic, sil)
        R, pi, d = _view(cam, Ps, S); zb = np.full(R * R, np.inf); np.minimum.at(zb, pi, d)
        vis = d <= zb[pi] + 1.5
        for mir in (False, True):                             # the twin's view of the camera counts too
            j = np.arange(len(Ps))
            if mir:                                           # look up each voxel's mirror twin
                key = {tuple(v): k for k, v in enumerate(I)}; j = np.array([key.get((shape[0] - 1 - a, b, c), -1) for a, b, c in I])
            ok = (j >= 0) & half; jj = j[ok]
            nn = Ns[jj] * (np.array((-1, 1, 1)) if mir else 1)
            sc = np.where(vis[jj], (Ns[jj] @ cam['dv']), -1)
            fx, fy, _ = pixels(cam, Ps[jj], S)
            col = clean[np.clip(fy.astype(int), 0, S - 1), np.clip(fx.astype(int), 0, S - 1)]
            idx = np.nonzero(ok)[0]; better = sc > best[idx]
            best[idx[better]] = sc[better]; rgb[idx[better]] = col[better]; seen[idx[better]] = True
    log('coloured from the pictures: %.0f%% of the surface; the rest takes its nearest seen colour' % (100 * seen[half].mean()))
    colg = finish_colour(surf, I, rgb, seen, colours, spread)
    kind = solid.astype(np.int8)

    # ---- outline vertices: front silhouette -> simplified loop -> mirrored -> lifted onto the surface
    loop = simplify(trace(sil_f), eps); cx = (S - 1) / 2
    loop[np.abs(loop[:, 0] - cx) <= 3, 0] = cx
    fx, fy, _ = pixels(cams[0], Ps[half | (Ps[:, 0] > -1)], S); Ph = Ps[half | (Ps[:, 0] > -1)]
    def lift(p):
        d2 = (fx - p[0]) ** 2 + (fy - p[1]) ** 2; near = np.nonzero(d2 <= d2.min() + 9)[0]
        k = near[np.argmin(Ph[near, 2])]                       # the candidate nearest the front camera
        return (0.0 if p[0] == cx else float(Ph[k, 0]), float(Ph[k, 1]), float(Ph[k, 2]))
    rig = []; m = len(loop)
    for i in range(m):
        a, b = loop[i], loop[(i + 1) % m]
        if a[0] < cx or b[0] < cx: continue                   # keep the +x side of the loop, mirror it below
        A, B = lift(a), lift(b)
        rig.append(('outlineL_%02d' % len(rig), None, A, B))
    rig += [(nm.replace('L_', 'R_'), None, (-A[0], A[1], A[2]), (-B[0], B[1], B[2])) for nm, _, A, B in list(rig)]

    bp = BP.extract_grid(dict(kind=kind, col=colg / 255.0, lo=lo, ID=name), dict(RIG=rig), cell, ring, True, flat_light=235)
    bp['unit'] = 'voxel'; bp['studsPerBrick'] = 5.0
    for key, cam in zip(('front', 'threeQuarter'), cams):
        bp['views'][key] = dict(az=cam['az'], el=cam['el'], c=np.round(cam['c'], 3).tolist(), dv=np.round(cam['dv'], 6).tolist(),
                                r=np.round(cam['r'], 6).tolist(), u=np.round(cam['u'], 6).tolist(), dist=cam['dist'], th=TH)
    bp['source'] = dict(kind='pictures', fill=dict(front=round(float(cov[0]), 4), threeQuarter=round(float(cov[1]), 4)), seen=round(float(seen[half].mean()), 4))
    return bp, dict(sil_f=sil_f, sil_q=sil_q, cams=cams, solid=solid, lo=lo, col=colg)


def main():
    ap = argparse.ArgumentParser(description='Build a voxel blueprint from a front and a 3/4 picture of a symmetric model.')
    ap.add_argument('front'); ap.add_argument('quarter'); ap.add_argument('--name', default='Model'); ap.add_argument('--out')
    ap.add_argument('--az', type=float, default=35); ap.add_argument('--el', type=float, default=14); ap.add_argument('--front-el', type=float, default=8)
    ap.add_argument('--cell', type=int, default=2); ap.add_argument('--ring', type=int, default=6); ap.add_argument('--colours', type=int, default=20)
    ap.add_argument('--depth', type=float, default=12, help='voxels kept behind a seen surface (0 = keep the whole carve)')
    ap.add_argument('--no-colour-carve', action='store_true', help='keep the plain silhouette hull')
    ap.add_argument('--free-angles', action='store_true', help='also search the camera angles (needs a third picture to be reliable)')
    ap.add_argument('--html'); ap.add_argument('--block', default='blueprint-ref'); ap.add_argument('--luau')
    ap.add_argument('--photos', nargs=2, metavar=('FRONT', 'QUARTER'), help='file names the page should show under the points')
    a = ap.parse_args()
    bp, dbg = build(a.front, a.quarter, a.name, a.az, a.el, a.front_el, a.cell, a.ring, a.colours, free_angles=a.free_angles, photo=not a.no_colour_carve, depth=a.depth)
    if a.photos: bp['photos'] = dict(front=a.photos[0], threeQuarter=a.photos[1])
    js = BP.to_json(bp)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, a.name + '_blueprint.json'), 'w', encoding='utf8').write(js)
        np.savez_compressed(os.path.join(a.out, a.name + '_grid.npz'), solid=np.packbits(dbg['solid']), shape=np.array(dbg['solid'].shape), lo=dbg['lo'])
    if a.luau: open(a.luau, 'w', encoding='utf8').write(BP.to_luau(bp))
    if a.html: BP.write_html(a.html, js, a.block)
    print('HULL_OK %s: %d anchors, %d outline edges, %d ring points, %d slots, %d colours, fill front %.3f / 3/4 %.3f' % (
        a.name, len(bp['anchors']), len(bp['bones']), bp['ringCount'], bp['slotCount'], len(bp['palette']),
        bp['source']['fill']['front'], bp['source']['fill']['threeQuarter']))


if __name__ == '__main__':
    main()
