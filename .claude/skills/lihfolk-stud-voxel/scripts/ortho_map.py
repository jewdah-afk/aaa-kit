# Vertex mapping from straight-on views. numpy + Pillow only.
# Takes orthographic pictures of one symmetric model (front, side, top, optional back; the brick pipeline renders
# them as ortho_front / ortho_side / ortho_top / ortho_back) and builds:
#   cells      a voxel grid: a cell is solid where the front, side and top silhouettes all cover it
#   vertices   every corner of every exposed cell face, numbered, with its exact pixel in each view:
#                front  u = L + a*x        v = T + a*(Y - y)
#                side   u = L + a*z        v = T + a*(Y - y)
#                top    u = L + a*x        v = T + a*(Z - z)
#              (a, L, T per view are in the output; x right, y up, z back)
#   reveal     a build order from a curved threshold F swept through the grid
#   colours    each surface cell from the view that faces it
# Straight-on views make the mapping exact: one cell is always the same number of pixels.
# Hollows that no silhouette shows (a cave in the chest, the inside of a mouth) stay filled.
#
# Run: python3 scripts/ortho_map.py front.png side.png top.png [--back back.png] --name EmberDragonOrtho --out out_map
#        [--angled view34.png 35 14 --angled back.png 150 18] [--px 6] [--html page.html --block blueprint-ortho] [--photos front.png side.png]
import argparse, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blueprint as BP
import hull_ref as H


def bbox(m):
    ys = np.nonzero(m.any(1))[0]; xs = np.nonzero(m.any(0))[0]
    return int(xs[0]), int(xs[-1]) + 1, int(ys[0]), int(ys[-1]) + 1


def sample(img, x0, y0, step, nu, nv, flip_u=False, flip_v=True):
    """Average a picture over an nu x nv grid of step-sized boxes starting at (x0, y0). Returns [u, v, ...]."""
    w, h = int(round(nu * step)), int(round(nv * step))
    crop = Image.fromarray(img).crop((x0, y0, x0 + w, y0 + h)).resize((nu, nv), Image.BOX)
    a = np.asarray(crop).astype(np.float32)
    if flip_v: a = a[::-1]
    if flip_u: a = a[:, ::-1]
    return np.swapaxes(a, 0, 1)


def build(front, side, top, back=None, name='Model', px=6.0, colours=20, extra=(), log=print):
    pics = {k: np.asarray(Image.open(p).convert('RGB')) for k, p in dict(front=front, side=side, top=top, back=back).items() if p}
    sil = {k: H.silhouette(v) for k, v in pics.items()}
    clean = {k: H.fill_edge(pics[k], sil[k]) for k in pics}
    bb = {k: bbox(v) for k, v in sil.items()}
    wf, hf = bb['front'][1] - bb['front'][0], bb['front'][3] - bb['front'][2]
    # each view was framed on its own, so chain the scales through shared axes: front -> top by width (x),
    # top -> side by length (z). Height is not used: glow halos under a tail or feet inflate it.
    step = dict(front=px, top=px * (bb['top'][1] - bb['top'][0]) / wf)
    nz_top = (bb['top'][3] - bb['top'][2]) / step['top']
    step['side'] = (bb['side'][1] - bb['side'][0]) / nz_top
    if back: step['back'] = px * (bb['back'][1] - bb['back'][0]) / wf
    nx = int(np.ceil(wf / px)); nx += nx % 2
    ny = int(np.ceil(hf / px)); nz = int(np.ceil(nz_top))
    log('grid %d x %d x %d cells at %g px; height from front %.1f cells, from side %.1f cells' % (nx, ny, nz, px, hf / px, (bb['side'][3] - bb['side'][2]) / step['side']))
    # origin of each view's cell grid in its own picture (x = 0 is the mirror line; the side view hangs from its top edge)
    org = dict(front=((bb['front'][0] + bb['front'][1]) / 2 - nx * px / 2, bb['front'][3] - ny * px),
               side=(bb['side'][0], bb['side'][2] + (hf / px - ny) * step['side']),
               top=((bb['top'][0] + bb['top'][1]) / 2 - nx * step['top'] / 2, bb['top'][3] - nz * step['top']))
    if back: org['back'] = ((bb['back'][0] + bb['back'][1]) / 2 - nx * step['back'] / 2, bb['back'][3] - ny * step['back'])
    dims = dict(front=(nx, ny), side=(nz, ny), top=(nx, nz), back=(nx, ny))
    def grid(k, img): return sample(img, *[int(round(v)) for v in org[k]], step[k], *dims[k], flip_u=(k == 'back'))
    cov = {k: grid(k, (sil[k] * 255).astype(np.uint8)) > 90 for k in pics}          # [u, v] cell masks
    cov['front'] &= cov['front'][::-1]; cov['top'] &= cov['top'][::-1]             # symmetric model, symmetric views
    solid = cov['front'][:, :, None] & cov['side'].T[None, :, :] & cov['top'][:, None, :]
    lo = np.array((-nx / 2, 0.0, -nz / 2))
    log('%d cells occupied after the three flat views' % solid.sum())

    # ---- angled views cut what flat views cannot: the box corners left where two extrusions cross
    G = np.stack(np.meshgrid(*[lo[i] + .5 + np.arange(n_) for i, n_ in enumerate((nx, ny, nz))], indexing='ij'), -1).reshape(-1, 3)
    for path, az, el in extra:
        es = H.silhouette(np.asarray(Image.open(path).convert('RGB')))
        es = ~H._erode(~es, 2)                                                     # 2 px of slack so thin parts survive
        v = BP.fit_view(lo + .5 + np.argwhere(solid), az, el)                      # the pipeline frames a view from the model's own bounds
        x = np.array([*v['c'], v['dist']], float); stepv = np.array([4, 4, 4, 8], float)
        def cut(x):
            m = H.inside(H.camera(az, el, x[:3], x[3]), G, es).reshape(solid.shape); return solid & m & m[::-1]
        def score(x): return H.coverage([H.camera(az, el, x[:3], x[3])], [es], G, cut(x))[0]
        sc = score(x)
        while stepv[0] > .2:                                                       # nudge the camera until the cut model fills the silhouette
            moved = False
            for i in range(4):
                for sg in (1, -1):
                    y = x.copy(); y[i] += sg * stepv[i]; t = score(y)
                    if t > sc + 1e-5: x, sc, moved = y, t, True; break
            if not moved: stepv /= 2
        if sc < .93: log('  %s: fill only %.3f, view skipped' % (os.path.basename(path), sc)); continue
        before = solid.sum(); solid = cut(x)
        log('  %s (az %g, el %g): fill %.3f, cut %d cells' % (os.path.basename(path), az, el, sc, before - solid.sum()))
    log('%d cells occupied' % solid.sum())

    # ---- how well the grid reproduces each silhouette
    match = {}
    for k, proj in (('front', solid.any(2)), ('side', solid.any(0).T), ('top', solid.any(1))):
        match[k] = float((proj & cov[k]).sum() / max(1, (proj | cov[k]).sum()))

    # ---- vertices: unique corners of exposed faces
    pad = np.pad(solid, 1); corners = []
    for ax in range(3):
        for sgn in (0, 1):
            sl = [slice(1, -1)] * 3; sl[ax] = slice(2, None) if sgn else slice(0, -2)
            F = np.argwhere(solid & ~pad[tuple(sl)])
            u, w = [a for a in range(3) if a != ax]
            for du in (0, 1):
                for dw in (0, 1):
                    c = F.copy(); c[:, ax] += sgn; c[:, u] += du; c[:, w] += dw; corners.append(c)
    V = np.unique(np.concatenate(corners), axis=0)                                  # sorted by x, then y, then z: the vertex IDs

    # ---- colour: each surface cell from the straight-on view that faces it and sees it first
    surf = H._shell(solid)
    f = pad.astype(np.float32)
    for ax in range(3): f = (np.roll(f, 1, ax) + f + np.roll(f, -1, ax)) / 3
    nrm = np.stack([np.roll(f, 1, ax) - np.roll(f, -1, ax) for ax in range(3)], -1)[1:-1, 1:-1, 1:-1]
    I = np.argwhere(surf); N = nrm[tuple(I.T)]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    cg = {k: grid(k, np.clip(clean[k], 0, 255).astype(np.uint8)) for k in pics}
    first = dict(front=(I[:, 2] == solid.argmax(2)[I[:, 0], I[:, 1]], -N[:, 2], lambda: cg['front'][I[:, 0], I[:, 1]]),
                 side=(I[:, 0] == nx - 1 - solid[::-1].argmax(0)[I[:, 1], I[:, 2]], N[:, 0], lambda: cg['side'][I[:, 2], I[:, 1]]),
                 top=(I[:, 1] == ny - 1 - solid[:, ::-1].argmax(1)[I[:, 0], I[:, 2]], N[:, 1], lambda: cg['top'][I[:, 0], I[:, 2]]))
    if back: first['back'] = (I[:, 2] == nz - 1 - solid[:, :, ::-1].argmax(2)[I[:, 0], I[:, 1]], N[:, 2], lambda: cg['back'][I[:, 0], I[:, 1]])
    best = np.full(len(I), .05); rgb = np.zeros((len(I), 3), np.float32); seen = np.zeros(len(I), bool)
    for k, (vis, score, get) in first.items():
        better = vis & (score > best); best[better] = score[better]; rgb[better] = get()[better]; seen |= better
    half = I[:, 0] >= nx // 2
    log('coloured from the views: %.0f%% of the surface' % (100 * seen[half].mean()))
    colg = H.finish_colour(surf, I, rgb, seen, colours, spread=4)

    bp = BP.extract_grid(dict(kind=solid.astype(np.int8), col=colg / 255.0, lo=lo, ID=name), dict(RIG=[]), 1, 4, True, flat_light=235)
    bp['unit'] = 'cell'; bp['studsPerBrick'] = 5.0
    bp['rings'] = lo + V; bp['ringCount'] = len(V)                                  # the page's outline = the mapped vertices
    # reveal order: a curved threshold swept through doubled cell-centre coordinates
    s = bp['slots']; X2, Y2, Z2 = 2 * s[:, 0].astype(int) + 1, 2 * s[:, 1].astype(int) + 1, 2 * s[:, 2].astype(int) + 1
    Fv = 80 * Y2 + 16 * Z2 + (X2 - bp['slotGrid'][0]) ** 2
    bp['slots'] = s[np.argsort(Fv, kind='stable')]
    bp['reveal'] = 'F = 80*Y2 + 16*Z2 + (X2 - gridWidth)^2 on doubled cell centres; slots are stored in rising F'
    # the page draws pictures through a camera; a very distant one with a tiny lens is a straight-on view
    D = 1e5
    def ortho_cam(k, dv, r, u, centre):
        S = pics[k].shape[0]
        return dict(az=0, el=0, c=[float(v) for v in centre], dv=dv, r=r, u=u, dist=D, th=(S / 2) / (D * step[k]))
    Sf = pics['front'].shape[0]; Ss = pics['side'].shape[0]
    bp['views'] = dict(
        front=ortho_cam('front', [0, 0, -1], [1, 0, 0], [0, 1, 0], ((Sf / 2 - org['front'][0]) / px + lo[0], (org['front'][1] + ny * px - Sf / 2) / px, 0)),
        threeQuarter=ortho_cam('side', [1, 0, 0], [0, 0, 1], [0, 1, 0], (0, (org['side'][1] + ny * step['side'] - Ss / 2) / step['side'], (Ss / 2 - org['side'][0]) / step['side'] + lo[2])))
    bp['viewLabels'] = dict(front='Front view', threeQuarter='Side view')
    bp['source'] = dict(kind='ortho', match={k: round(v, 4) for k, v in match.items()}, seen=round(float(seen[half].mean()), 4), occupied=int(solid.sum()))
    vmap = dict(name=name, cells=[int(nx), int(ny), int(nz)], occupied=int(solid.sum()), vertexCount=int(len(V)),
                axes='x right, y up, z back; vertex (x, y, z) are cell-corner indices, zero-based',
                views={k: dict(a=round(step[k], 4), L=round(org[k][0], 2), T=round(org[k][1], 2), picture=os.path.basename(p))
                       for k, p in dict(front=front, side=side, top=top).items()},
                formulas=dict(front='u = L + a*x, v = T + a*(Y - y)', side='u = L + a*z, v = T + a*(Y - y)', top='u = L + a*x, v = T + a*(Z - z)'),
                Y=int(ny), Z=int(nz), reveal=bp['reveal'], silhouetteMatch=bp['source']['match'], verticesXYZ=V.tolist())
    return bp, vmap


def main():
    ap = argparse.ArgumentParser(description='Voxel grid + numbered vertex-to-pixel map from front, side and top views.')
    ap.add_argument('front'); ap.add_argument('side'); ap.add_argument('top'); ap.add_argument('--back')
    ap.add_argument('--name', default='Model'); ap.add_argument('--out'); ap.add_argument('--px', type=float, default=6, help='picture pixels per cell (front view)')
    ap.add_argument('--colours', type=int, default=20); ap.add_argument('--html'); ap.add_argument('--block', default='blueprint-ortho'); ap.add_argument('--luau')
    ap.add_argument('--angled', nargs=3, action='append', default=[], metavar=('PNG', 'AZ', 'EL'), help='extra perspective view to carve with (repeatable)')
    ap.add_argument('--photos', nargs=2, metavar=('FRONT', 'SIDE'), help='file names the page should show under the points')
    a = ap.parse_args()
    bp, vmap = build(a.front, a.side, a.top, a.back, a.name, a.px, a.colours, [(p_, float(az), float(el)) for p_, az, el in a.angled])
    if a.photos: bp['photos'] = dict(front=a.photos[0], threeQuarter=a.photos[1])
    js = BP.to_json(bp)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, a.name + '_blueprint.json'), 'w', encoding='utf8').write(js)
        open(os.path.join(a.out, a.name + '_vertexmap.json'), 'w', encoding='utf8').write(json.dumps(vmap, separators=(',', ':')))
    if a.luau: open(a.luau, 'w', encoding='utf8').write(BP.to_luau(bp))
    if a.html: BP.write_html(a.html, js, a.block)
    m = bp['source']['match']
    print('MAP_OK %s: %s cells, %d occupied, %d vertices, %d slots, silhouette match front %.3f side %.3f top %.3f' % (
        a.name, 'x'.join(map(str, vmap['cells'])), vmap['occupied'], vmap['vertexCount'], bp['slotCount'], m['front'], m['side'], m['top']))


if __name__ == '__main__':
    main()
