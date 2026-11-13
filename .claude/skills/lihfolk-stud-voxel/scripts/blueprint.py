# Blueprint extractor: turns a brick-pipeline model into a fixed, mirrored 3D point set.
# No Blender needed (numpy only). It runs the model script's own shape maths, then derives:
#   anchors  rig joints (named vertices) + the bones between them
#   rings    outline points: surface bricks on evenly spaced Z and Y planes + the centre profile
#   slots    one coarse voxel per `cell` bricks on the shell, with colour and baked light
#   views    the exact cameras of the pipeline's rest_front / rest_34 renders (to draw over a render)
# Everything is in brick coords (x right, y up, z back, front = -z); 1 brick = 2.5 studs.
# With --mirror (default when the model is symmetric) the -x half is the +x half reflected, so
# every point has an exact twin.
#
# Run: python3 scripts/blueprint.py examples/brick/ember_dragon_brick.py --out out_bp
#        [--cell 4] [--ring 8] [--no-mirror] [--html page.html] [--luau Module.luau]
import argparse, base64, json, math, os, re, sys, types
import numpy as np


class _Stub:
    """Stands in for bpy / mathutils: any attribute, call or item gives another stub."""
    def __getattr__(self, k): return _Stub()
    def __call__(self, *a, **k): return _Stub()
    def __getitem__(self, k): return _Stub()
    def __iter__(self): return iter(())
    def __mul__(self, o): return self


def run_model(path):
    """Execute the shape + palette part and the rig declaration of a brick script, skipping Blender."""
    src = open(path, encoding='utf8').read()
    m_mesh = re.search(r'^# -+ mesh', src, re.M)
    m_rig = re.search(r'^# -+ rig \(always\)', src, re.M)
    if not m_mesh:
        raise SystemExit('no "# ---- mesh" marker in ' + path)
    captured = {}
    rig_mod = types.ModuleType('brick_rig')
    rig_mod.limb = lambda *a, **k: []
    def _export(ID, OUT, lo, kind, col, RIG, OVR=None, **kw):
        captured['RIG'] = RIG; captured['pose'] = kw.get('pose')
    rig_mod.export = _export
    saved = {k: sys.modules.get(k) for k in ('bpy', 'mathutils', 'brick_rig')}
    sys.modules['bpy'] = _Stub(); sys.modules['brick_rig'] = rig_mod
    mu = types.ModuleType('mathutils'); mu.Vector = _Stub; sys.modules['mathutils'] = mu
    mk = os.makedirs; os.makedirs = lambda *a, **k: None          # the script would create its out_ folder
    ns = {'__file__': os.path.abspath(path), '__name__': 'brick_model'}
    try:
        exec(compile(src[:m_mesh.start()], path, 'exec'), ns)
        if m_rig:
            ns.setdefault('argv', []); ns.setdefault('ONLY', [])
            ns.setdefault('solid', ns['kind'] > 0)
            try:
                exec(compile(src[m_rig.start():], path, 'exec'), ns)
            except Exception as e:                                 # rig is optional for the blueprint
                print('RIG_SKIPPED', type(e).__name__, e)
    finally:
        os.makedirs = mk
        for k, v in saved.items():
            if v is None: sys.modules.pop(k, None)
            else: sys.modules[k] = v
    return ns, captured


def fit_view(P, az, el, lens=50.0):
    """Same framing as render_all().fit() in the brick scripts. P = points in brick coords."""
    a, e = math.radians(az), math.radians(el)
    dv = np.array((math.cos(e) * math.sin(a), math.sin(e), -math.cos(e) * math.cos(a)))   # brick coords (y up)
    up = np.array((0, 1.0, 0))
    r = np.cross(dv, up); r /= np.linalg.norm(r); u = np.cross(r, dv)                    # camera right / up
    pr, pu, pf = P @ r, P @ u, P @ dv
    c = r * (pr.max() + pr.min()) / 2 + u * (pu.max() + pu.min()) / 2 + dv * (pf.max() + pf.min()) / 2
    q = P - c; qr, qu, qf = np.abs(q @ r), np.abs(q @ u), q @ dv
    th = 18.0 / lens
    dist = 1.04 * max((qr / th + qf).max(), (qu / th + qf).max())
    return dict(az=az, el=el, c=c.round(3).tolist(), dv=dv.round(6).tolist(), r=r.round(6).tolist(),
                u=u.round(6).tolist(), dist=round(float(dist), 3), th=th)


def project(view, P):
    """Brick coords -> normalised screen (-1..1, y up) for a view from fit_view."""
    q = np.asarray(P, float) - np.array(view['c'])
    d = view['dist'] - q @ np.array(view['dv'])
    return np.stack([(q @ np.array(view['r'])) / d / view['th'], (q @ np.array(view['u'])) / d / view['th']], -1)


def load_model(path, cache=None):
    """run_model, or its saved grid when --cache points at an existing .npz (big models take minutes)."""
    if cache and os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        glow = {int(k): v for k, v in zip(z['glow_k'], z['glow_v'])}
        return dict(kind=z['kind'], col=z['col'], lo=z['lo'], ID=str(z['ID']), GLOW=glow), dict(RIG=z['RIG'].tolist())
    ns, cap = run_model(path)
    if cache:
        np.savez_compressed(cache, kind=ns['kind'], col=ns['col'].astype(np.float32), lo=np.array(ns['lo'], float),
                            ID=ns.get('ID', ''), RIG=np.array(cap.get('RIG', []), dtype=object),
                            glow_k=np.array(list(ns.get('GLOW', {}).keys()), int), glow_v=np.array(list(ns.get('GLOW', {}).values()), float).reshape(-1, 3))
    return ns, cap


def extract(path, cell=4, ring=8, mirror=None, cache=None):
    ns, cap = load_model(path, cache)
    kind, col, lo = ns['kind'], np.clip(ns['col'], 0, 1).copy(), np.array(ns['lo'], float)
    n = np.array(kind.shape); solid = kind > 0
    for k, c in ns.get('GLOW', {}).items(): col[kind == k] = c                    # glow bricks: their flat colour, not the height shading
    xc = lo[0] + .5 + np.arange(n[0])
    sym_grid = abs(xc[0] + xc[-1]) < 1e-6
    iou = float((solid & solid[::-1]).sum() / max(1, (solid | solid[::-1]).sum())) if sym_grid else 0.0
    if mirror is None: mirror = iou > .9
    if mirror and not sym_grid: raise SystemExit('grid is not centred on x = 0, cannot mirror')

    inner = solid.copy()
    for ax in range(3):
        for s in (1, -1):
            nb = np.roll(solid, s, axis=ax); sl = [slice(None)] * 3; sl[ax] = 0 if s > 0 else -1; nb[tuple(sl)] = False
            inner &= nb
    surf = solid & ~inner
    half = (xc > 0)[:, None, None] if mirror else np.ones((n[0], 1, 1), bool)

    # ---- palette: the colours the surface really uses (glow bricks keep their own entries)
    I = np.argwhere(surf & half)
    c8 = np.round(col[tuple(I.T)] * 255).astype(np.int64)
    key = (c8[:, 0] << 16) | (c8[:, 1] << 8) | c8[:, 2]
    isglow = kind[tuple(I.T)] >= 2
    key = key | (isglow.astype(np.int64) << 24)
    keys, pal_i = np.unique(key, return_inverse=True)
    if len(keys) > 255: raise SystemExit('more than 255 surface colours; snap the model to its palette first')
    palette = ['#%06x' % (k & 0xffffff) for k in keys]; glow = [bool(k >> 24) for k in keys]

    # ---- rings: surface bricks on every `ring`-th Z and Y plane, plus the centre profile
    iz, iy, ix = I[:, 2], I[:, 1], I[:, 0]
    x0i = int(np.argmax(xc > 0))
    on = (iz % ring == ring // 2) | (iy % ring == ring // 2) | (ix == x0i)
    R = I[on]
    rings = lo + .5 + R
    if mirror: rings = np.concatenate([rings, rings * np.array((-1, 1, 1))])

    # ---- slots: coarse shell voxels, x cells mirrored about 0
    hx = cell * math.ceil(max(abs(xc[0]) + .5, abs(xc[-1]) + .5) / cell)
    org = np.array((-hx, lo[1], lo[2])); cn = np.array((2 * hx // cell, math.ceil(n[1] / cell), math.ceil(n[2] / cell)), int)
    def cid(idx):
        p = lo + .5 + idx
        return np.floor((p - org) / cell).astype(int)
    S = np.argwhere(solid); cs = cid(S)
    flat = lambda c: (c[:, 0] * cn[1] + c[:, 1]) * cn[2] + c[:, 2]
    cnt = np.bincount(flat(cs), minlength=cn.prod()).reshape(cn)
    filled = cnt >= .15 * cell ** 3
    if mirror: filled |= filled[::-1]
    pad = np.pad(filled, 1)
    cin = filled.copy()
    for ax in range(3):
        for s in (0, 2):
            sl = [slice(1, -1)] * 3; sl[ax] = slice(s, s + cn[ax]); cin &= pad[tuple(sl)]
    shell = filled & ~cin
    votes = np.zeros((cn.prod(), len(keys)), np.int32)
    np.add.at(votes, (flat(cid(I)), pal_i), 1)
    votes = votes.reshape(*cn, len(keys))
    if mirror: votes = votes + votes[::-1]
    f = pad.astype(np.float32)                                                   # light: normal from the blurred fill
    for ax in range(3): f = (np.roll(f, 1, ax) + f + np.roll(f, -1, ax)) / 3
    g = np.stack([np.roll(f, 1, ax) - np.roll(f, -1, ax) for ax in range(3)], -1)[1:-1, 1:-1, 1:-1]
    g /= np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-6)
    L = np.array((.3, .8, -.52)); L /= np.linalg.norm(L)
    light = np.clip(.62 + .38 * (g @ L), 0, 1)
    J = np.argwhere(shell)
    has = votes[tuple(J.T)].sum(-1) > 0
    pal_s = votes[tuple(J.T)].argmax(-1)
    if (~has).any():                                                             # shell cell with no surface brick: copy the nearest that has one
        good = J[has]
        for k in np.where(~has)[0]:
            pal_s[k] = pal_s[has][np.argmin(((good - J[k]) ** 2).sum(-1))]
    order = np.lexsort((J[:, 0], J[:, 2], J[:, 1]))                              # build order: bottom-up, front to back
    J = J[order]; pal_s = pal_s[order]
    lt = np.round(light[tuple(J.T)] * 255).astype(np.uint8)
    slots = np.concatenate([J.astype(np.uint8), pal_s[:, None].astype(np.uint8), lt[:, None]], 1)
    if cn.max() > 255: raise SystemExit('coarse grid over 255 cells; raise --cell')

    # ---- anchors: rig joints
    anchors, bones, seen = [], [], {}
    def anchor(p, name):
        k = tuple(np.round(p, 2))
        if k not in seen: seen[k] = len(anchors); anchors.append(dict(name=name, p=[float(v) for v in k]))
        return seen[k]
    for bone, parent, h, t in cap.get('RIG', []):
        if bone == 'root': continue
        bones.append([anchor(h, bone), anchor(t, bone + '_end'), bone])

    P = lo + .5 + np.argwhere(surf)[::5]
    return dict(
        name=ns.get('ID', os.path.basename(path)), unit='brick', studsPerBrick=2.5,
        lo=lo.tolist(), size=n.tolist(), symmetry=dict(iou=round(iou, 4), mirrored=bool(mirror)),
        anchors=anchors, bones=bones, palette=palette, glow=glow,
        cell=cell, slotOrigin=org.tolist(), slotGrid=cn.tolist(), slotCount=len(slots), slots=slots,
        ringStep=ring, ringCount=len(rings), rings=rings,
        views=dict(front=fit_view(P, 0, 8), threeQuarter=fit_view(P, 35, 14)))


def to_json(bp):
    o = dict(bp)
    o['slots'] = base64.b64encode(bp['slots'].tobytes()).decode()                 # u8 x5: ix iy iz palette light
    o['rings'] = base64.b64encode(np.round(bp['rings'] * 2).astype('<i2').tobytes()).decode()   # i16 x3, half-bricks
    return json.dumps(o, separators=(',', ':'))


def to_luau(bp):
    a = ',\n'.join('\t\t{ name = "%s", p = { %g, %g, %g } }' % (x['name'], *x['p']) for x in bp['anchors'])
    b = ',\n'.join('\t\t{ %d, %d, "%s" }' % (i + 1, j + 1, nm) for i, j, nm in bp['bones'])
    p = ', '.join('0x%s' % h[1:] for h in bp['palette'])
    g = ', '.join('true' if v else 'false' for v in bp['glow'])
    hexs = bp['slots'].tobytes().hex()
    rows = '\n'.join('\t\t.. "%s"' % hexs[i:i + 120] for i in range(0, len(hexs), 120))
    return ('--!strict\n-- %s blueprint. Generated by lihfolk-stud-voxel/scripts/blueprint.py; do not edit by hand.\n'
            '-- Brick coords: x right, y up, z back (front = -z). 1 brick = %g studs. Decode with Blueprint.decode().\n'
            '-- bones = { anchor index, anchor index, bone name }.\n'
            'return {\n\tname = "%s",\n\tstudsPerBrick = %g,\n\tmirrored = %s,\n\tcell = %d,\n'
            '\tslotOrigin = { %g, %g, %g },\n\tslotCount = %d,\n'
            '\tpalette = { %s },\n\tglow = { %s },\n\tanchors = {\n%s,\n\t},\n\tbones = {\n%s,\n\t},\n'
            '\t-- 5 bytes per slot as hex: ix, iy, iz, palette index (0-based), light (0-255); sorted bottom-up\n'
            '\tslots = ""\n%s,\n}\n') % (
        bp['name'], bp['studsPerBrick'], bp['name'], bp['studsPerBrick'], 'true' if bp['symmetry']['mirrored'] else 'false',
        bp['cell'], *bp['slotOrigin'], bp['slotCount'], p, g, a, b, rows)


def main():
    ap = argparse.ArgumentParser(description='Extract a hologram blueprint from a brick model script.')
    ap.add_argument('model'); ap.add_argument('--out', default=None)
    ap.add_argument('--cell', type=int, default=4, help='bricks per slot voxel')
    ap.add_argument('--ring', type=int, default=8, help='bricks between outline planes')
    ap.add_argument('--no-mirror', action='store_true')
    ap.add_argument('--cache', help='.npz to save / reuse the model grid')
    ap.add_argument('--html', help='page with a <script id="blueprint" type="application/json"> block to refresh')
    ap.add_argument('--luau', help='write the Luau data module here')
    a = ap.parse_args()
    bp = extract(a.model, a.cell, a.ring, False if a.no_mirror else None, a.cache)
    js = to_json(bp)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, bp['name'] + '_blueprint.json'), 'w', encoding='utf8').write(js)
    if a.luau: open(a.luau, 'w', encoding='utf8').write(to_luau(bp))
    if a.html:
        page = open(a.html, encoding='utf8').read()
        new, k = re.subn(r'(<script id="blueprint" type="application/json">).*?(</script>)', lambda m: m.group(1) + js + m.group(2), page, flags=re.S)
        if k != 1: raise SystemExit('no blueprint script block in ' + a.html)
        open(a.html, 'w', encoding='utf8').write(new)
    print('BLUEPRINT_OK %s: %d anchors, %d bones, %d ring points, %d slots (cell %d), %d colours, symmetry %.3f, mirrored %s' % (
        bp['name'], len(bp['anchors']), len(bp['bones']), bp['ringCount'], bp['slotCount'], bp['cell'], len(bp['palette']),
        bp['symmetry']['iou'], bp['symmetry']['mirrored']))
    return bp


if __name__ == '__main__':
    main()
