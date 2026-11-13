"""Shared core of the brick pipeline: grid, sculpt helpers, clean-up, mesh, render, sheet and rig export in one module.

The older examples each carry ~200 lines of the same grid/mesh/render code. A model written on this core is only its
sculpt. No shipped example uses this core yet.

    from brick_core import Model, hx
    M = Model('MyMob', __file__, lo=(-40, 0, -30), hi=(40, 80, 30))     # brick coords: x right, y up, front = -z
    X, Y, Z = M.X, M.Y, M.Z
    M.put(M.ell((0, 20, 0), (18, 18, 18)) < 0, hx('f2f2f0'), p=M.part())       # mask, colour, part id (seams between parts)
    M.finish(rig=[('root', None, (0, 0, 0), (0, 6, 0)), ...], overrides=[...], lights=[((x, y, z), colour, energy)])

Run (Linux/macOS, Blender 4.2+ or the `bpy` pip module):  bash scripts/run_brick.sh <file.py> [views] [res=600] [norig]
finish() prints CONN_OK, PALETTE, VOX_OK, LINT_OK / LINT_FAIL, then RIG_OK from brick_rig.
"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import brick_rig

STUD_PNG = os.path.join(HERE, '..', 'assets', 'roblox_square_studs.png')
MAX_COLOURS = 16


def hx(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def lin(c):
    return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)


def smin(a, b, k):
    """smooth union of two distance fields (k = blend width in bricks)"""
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Model:
    def __init__(self, ID, file, lo, hi):
        self.ID = ID
        self.dir = os.path.dirname(os.path.abspath(file))
        self.OUT = os.path.join(self.dir, 'out_' + os.path.splitext(os.path.basename(file))[0])
        self.REN = os.path.join(self.OUT, 'render'); os.makedirs(self.REN, exist_ok=True)
        self.lo = np.array(lo, float)                                           # lo[1] is the ground plane; brick centres sit at lo + .5 + i
        self.n = n = (np.array(hi, float) - self.lo).astype(int)
        c = [self.lo[i] + .5 + np.arange(n[i]) for i in range(3)]
        self.X, self.Y, self.Z = np.meshgrid(*c, indexing='ij')
        self.col = np.zeros((*n, 3)); self.kind = np.zeros(n, np.int8)          # kind 0 empty, 1 solid, 2+ glow
        self.pid = np.zeros(n, np.int32); self.lvl = np.zeros(n); self.keep = np.zeros(n, bool)
        self.used = {}; self._next = 10
        a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
        self.render = 'render' in a; self.norig = 'norig' in a
        self.res = next((int(v[4:]) for v in a if v.startswith('res=')), 900)
        self.only = [v for v in a if v not in ('render', 'norig') and not v.startswith('res=')]

    # ------------------------------------------------------------ sculpt
    def part(self):
        """new part id: neighbouring parts get a dark seam where they meet"""
        self._next += 1; return self._next

    def put(self, m, rgb, k=1, p=0, l=0.0, keep=False):
        """paint mask m. k: 1 solid, 2+ glow kind. p: part id. l: height level (the lower part takes the seam).
        keep=True: no seam darkening and no vertical shading on these bricks (eyes, teeth, markings)."""
        rgb = np.asarray(rgb, float)
        self.col[m] = rgb; self.kind[m] = k; self.pid[m] = p; self.lvl[m] = l; self.keep[m] = keep
        if k == 1: self.used[tuple(np.round(rgb, 4))] = 1

    def cut(self, m):
        self.kind[m] = 0

    def ell(self, c, r):
        """signed distance to an ellipsoid (centre c, radii r); < 0 inside"""
        px, py, pz = (self.X - c[0]) / r[0], (self.Y - c[1]) / r[1], (self.Z - c[2]) / r[2]
        k0 = np.sqrt(px * px + py * py + pz * pz)
        k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
        return k0 * (k0 - 1) / k1

    def cap(self, a, b, ra, rb=None, flat=False):
        """tapered capsule a -> b (radius ra -> rb); flat=True cuts the round ends off"""
        rb = ra if rb is None else rb
        a = np.array(a, float); b = np.array(b, float); ab = b - a
        t0 = ((self.X - a[0]) * ab[0] + (self.Y - a[1]) * ab[1] + (self.Z - a[2]) * ab[2]) / ab.dot(ab); t = np.clip(t0, 0, 1)
        d = np.sqrt((self.X - a[0] - ab[0] * t) ** 2 + (self.Y - a[1] - ab[1] * t) ** 2 + (self.Z - a[2] - ab[2] * t) ** 2)
        m = d <= ra + (rb - ra) * t
        return m & (t0 >= 0) & (t0 <= 1) if flat else m

    def box(self, x0, x1, y0, y1, z0, z1):
        X, Y, Z = self.X, self.Y, self.Z
        return (X > x0) & (X < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)

    def step(self, v, s):
        """quantise a coordinate field to steps of s bricks: use inside a shape test for chunkier, stepped forms"""
        return np.floor(v / s) * s + s / 2

    def surface(self, m=None):
        """solid bricks with at least one empty 6-neighbour"""
        s = self.kind > 0; inner = s.copy()
        for ax in range(3):
            for d in (1, -1): inner &= np.roll(s, d, axis=ax)
        out = s & ~inner
        return out if m is None else out & m

    # ------------------------------------------------------------ clean-up
    def _connect(self, ground):
        s = self.kind > 0
        if not s.any(): raise SystemExit('LINT_FAIL empty model')
        ix = np.argwhere(s); cen = ix.mean(0)
        seed = ix[np.argmin(((ix - cen) ** 2).sum(1))]
        reach = np.zeros_like(s); reach[tuple(seed)] = True
        if ground: reach[:, 0, :] |= s[:, 0, :]
        prev = -1
        while True:
            o = reach
            for ax in range(3):
                a_ = [slice(None)] * 3; b_ = [slice(None)] * 3; a_[ax] = slice(1, None); b_[ax] = slice(None, -1)
                t = o.copy(); t[tuple(a_)] |= o[tuple(b_)]; t[tuple(b_)] |= o[tuple(a_)]; o = t
            reach = o & s; c = int(reach.sum())
            if c == prev: break
            prev = c
        drop = s & ~reach
        self.kind[drop] = 0
        self.dropped = int(drop.sum())
        print('CONN_OK kept', prev, 'dropped floating', self.dropped)

    def _seams_shade_palette(self, palette, shade):
        n, pid, lvl, kind, col = self.n, self.pid, self.lvl, self.kind, self.col
        dark = np.zeros(n, bool)
        for ax in range(3):
            for s in (1, -1):
                np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
                dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
        col[dark & (kind == 1) & ~self.keep & self.surface()] *= .72
        ys = self.Y[kind > 0]; t = (self.Y - ys.min()) / max(1.0, ys.max() - ys.min())
        col *= np.where(self.keep, 1.0, shade[0] + (shade[1] - shade[0]) * t)[..., None]
        np.clip(col, 0, 1, out=col)
        pal = np.array([hx(h) for h in palette]) if palette else np.array(list(self.used))
        sol = kind == 1
        cs = col[sol]; idx = np.empty(len(cs), np.int64)
        for i in range(0, len(cs), 200000):
            idx[i:i + 200000] = np.argmin(((cs[i:i + 200000, None, :] - pal[None]) ** 2).sum(-1), 1)
        col[sol] = pal[idx]
        self.colours = len(np.unique(idx))
        print('PALETTE', len(pal), 'colours in use:', self.colours)

    # ------------------------------------------------------------ mesh
    def _exposed(self, mask, ax, s):
        nb = np.roll(self.kind > 0, -s, axis=ax)
        sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
        return mask & ~nb

    def _build(self, name, mask):
        verts = []; faces = []; cols = []; uvs = []; nv = 0
        for ax in range(3):
            u, w = [k for k in range(3) if k != ax]
            for s in (1, -1):
                e = np.argwhere(self._exposed(mask, ax, s))
                if not len(e): continue
                base = self.lo + e; off = np.zeros(3); off[ax] = 1 if s > 0 else 0
                q = []; t = []
                for du, dw in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    dd = off.copy(); dd[u] = du; dd[w] = dw; q.append(base + dd)
                    t.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w] + dw) / 16.0], 1))     # one stud per 2x2 bricks
                q = np.stack(q, 1); t = np.stack(t, 1); k = len(e)
                if not ((s > 0) != (ax == 1)): t = t[:, ::-1]; q = q[:, ::-1]
                verts.append(q.reshape(-1, 3)); faces.append(nv + np.arange(4 * k).reshape(k, 4)); nv += 4 * k
                uvs.append(t.reshape(-1, 2)); cols.append(np.repeat(self.col[e[:, 0], e[:, 1], e[:, 2]], 4, axis=0))
        Vt = np.concatenate(verts); Cv = np.concatenate(cols); UV = np.concatenate(uvs)
        me = bpy.data.meshes.new(name)
        me.from_pydata(np.stack([Vt[:, 0], Vt[:, 2], Vt[:, 1]], 1).tolist(), [], np.concatenate(faces).tolist())
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', np.concatenate([lin(np.clip(Cv, 0, 1)), np.ones((len(Cv), 1))], 1).ravel())
        ul = me.uv_layers.new(name='UVMap')
        li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
        ul.data.foreach_set('uv', UV[li].ravel())
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

    def _scene(self, glow):
        for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
        body = self._build(self.ID, self.kind == 1)
        m = bpy.data.materials.new('Brick'); m.use_nodes = True
        nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
        bs.inputs['Roughness'].default_value = .6
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
        tx.image.colorspace_settings.name = 'Non-Color'
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 1
        nt.links.new(at.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7])
        nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
        body.data.materials.append(m)
        for k, c in glow.items():
            if not (self.kind == k).any(): continue
            o = self._build('Glow%d' % k, self.kind == k)
            gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
            cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
            b2.inputs['Emission Strength'].default_value = 5.0; gm.diffuse_color = cl
            o.data.materials.append(gm); o.color = cl
        self.faces = len(body.data.polygons)
        print('VOX_OK', int((self.kind > 0).sum()), 'bricks', self.faces, 'faces')
        return body

    # ------------------------------------------------------------ render
    def _render(self, body, lights, face, extra):
        sc = bpy.context.scene; B = lambda x, y, z: Vector((x, z, y))
        ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
        for i, (p, c, e) in enumerate(lights):
            L = bpy.data.objects.new('Pt%d' % i, bpy.data.lights.new('Pt%d' % i, 'POINT')); sc.collection.objects.link(L)
            L.data.energy = e; L.data.color = tuple(c); L.data.shadow_soft_size = 1.0; L.location = B(*p)
        for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
            L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
            L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
        sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
        sc.render.resolution_x = sc.render.resolution_y = self.res
        sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.78, .78, .8)
        for attr in ('use_gtao', 'use_raytracing'):
            try: setattr(sc.eevee, attr, True)
            except Exception: pass
        me = bpy.data.meshes.new('G'); s = 3000; gy = self.lo[1]
        me.from_pydata([(-s, -s, gy), (s, -s, gy), (s, s, gy), (-s, s, gy)], [], [(0, 1, 2, 3)])
        g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
        gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True
        gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.5, .5, .52, 1); me.materials.append(gm)
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 5000

        def view(name, tgt, dist, az, el, lens=50, ortho=None):
            t = B(*tgt)
            dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
            cam.location = t + dv * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
            cam.data.type = 'ORTHO' if ortho else 'PERSP'
            if ortho: cam.data.ortho_scale = ortho
            p = os.path.join(self.REN, '%s_%s.png' % (self.ID, name))
            sc.render.engine = ENG; sc.render.film_transparent = False; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_shadows = False; sh.show_cavity = False
            g.hide_render = True; sc.render.film_transparent = True; sc.render.filepath = p[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
            sc.render.film_transparent = False; keep = tuple(sc.world.color); sc.world.color = (0, 0, 0); sh.background_type = 'WORLD'
            kc = tuple(body.color); body.color = (0, 0, 0, 1)
            sc.render.filepath = p[:-4] + '_glow.png'; bpy.ops.render.render(write_still=True)
            body.color = kc; sc.world.color = keep; g.hide_render = False

        ix = np.argwhere(self.kind > 0); a = self.lo + ix.min(0); b = self.lo + ix.max(0) + 1
        cen = tuple((a + b) / 2); size = float(max(b - a)); D = size * 2.2
        views = [(nm, (cen, 4 * size, az, el), dict(ortho=size * 1.2))
                 for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9))]
        views += [(nm, (cen, D, az, el), {}) for nm, az, el in (('rest_34', -35, 14), ('rest_side', 90, 6), ('rest_front', 0, 6),
                                                                ('rest_back', 180, 8), ('back34', 145, 14))]
        if face: views.append(('face', (tuple(face[0]), face[1], face[2] if len(face) > 2 else -20, 6), {}))
        views += [(nm, a_, {}) for nm, a_ in extra]
        for nm, a_, kw in views:
            if self.only and nm not in self.only: continue
            view(nm, *a_, **kw)

    def _post(self, strong):
        try:
            import post_glow, subprocess
        except Exception as e:
            print('POST_SKIP (no Pillow in this Python; the runner script does the post)', e); return
        import glob
        if strong: os.environ['GLOW_STRONG'] = '1'
        else: os.environ.pop('GLOW_STRONG', None)
        for p in sorted(glob.glob(os.path.join(self.REN, '*.png'))):
            if p.endswith(('_mask.png', '_glow.png', '_fx.png', '_ol.png', '_tex.png', '_rigrest.png', '_posed.png')) or not os.path.exists(p[:-4] + '_mask.png'): continue
            post_glow.fx(p).save(p[:-4] + '_fx.png')
        subprocess.run([sys.executable, os.path.join(HERE, 'brick_sheet.py'), self.REN, os.path.join(self.OUT, 'sheet.png')])

    # ------------------------------------------------------------ finish
    def finish(self, rig=None, overrides=(), pose=None, glow=None, palette=None, lights=(), face=None, views=(),
               shade=(.86, 1.1), ground=True, glow_strong=False):
        """clean up, mesh, render (when run with `-- render`), lint, rig export. Call once, last.
        rig: [(bone, parent, head_xyz, tail_xyz)], root first. overrides: [(mask, bone)], last wins.
        lights: [((x, y, z), colour, energy)] point lights (one per glowing eye / core).
        face: ((x, y, z), distance[, azimuth]) for a face close-up. views: extra [(name, (target, dist, az, el))].
        shade: (bottom, top) brightness ramp before the palette snap. ground=True keeps bricks resting on y 0."""
        glow = glow or {}
        self._connect(ground)
        self._seams_shade_palette(palette, shade)
        body = self._scene(glow)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(self.OUT, self.ID + '.blend'))
        if self.render:
            self._render(body, lights, face, views); self._post(glow_strong)
        ix = np.argwhere(self.kind > 0); ext = (ix.max(0) - ix.min(0) + 1)
        lint = dict(id=self.ID, bricks=int((self.kind > 0).sum()), faces=self.faces, colours=self.colours, dropped=self.dropped,
                    size_bricks=[int(v) for v in ext], size_studs=[round(float(v) * 2.5, 1) for v in ext],
                    glow_bricks=int((self.kind > 1).sum()), glow_share=round(float((self.kind > 1).sum() / (self.kind > 0).sum()), 4))
        bad = []
        if self.colours > MAX_COLOURS: bad.append('more than %d colours (%d)' % (MAX_COLOURS, self.colours))
        if lint['glow_share'] > .04 and not glow_strong: bad.append('glow share %.1f%% is over the 4%% budget' % (lint['glow_share'] * 100))
        if ix[:, 1].min() > 0: bad.append('model does not touch the ground (lowest layer %d)' % ix[:, 1].min())
        lint['fail'] = bad
        json.dump(lint, open(os.path.join(self.OUT, self.ID + '_lint.json'), 'w'), indent=1)
        print('LINT_FAIL ' + '; '.join(bad) if bad else 'LINT_OK', json.dumps({k: lint[k] for k in ('bricks', 'colours', 'size_studs', 'glow_share')}))
        if rig and not self.norig:
            brick_rig.export(self.ID, self.OUT, self.lo, self.kind, self.col, rig, list(overrides), glow=glow, pose=pose or {}, render=self.render)
        print('BL_OK', self.ID)
