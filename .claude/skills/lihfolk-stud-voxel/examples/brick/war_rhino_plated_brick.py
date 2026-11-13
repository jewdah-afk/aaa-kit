# SKILL EXAMPLE (plated rebuild, not yet owner-approved): reference = previews/WarRhino_concept.jpg; Roblox square-stud overlay at 2x2, strong eye glow
# GLOW: strong   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# War Rhino, plated rebuild (the shipped war_rhino_brick.py stays 1:1 for comparison): smooth anatomy field -> separate
# armour plates traced from the concept, at different heights (every plate edge is a real brick step) -> grid-exact face + hooves -> brick faces + studs -> EEVEE.
# Run: blender -b --factory-startup --python rhino_fable.py -- render
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'FBRhinoPlated'

lo = np.array((-28.0, -0.5, -62.0)); hi = np.array((28.0, 62.5, 54.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)                                      # plate id / plate height level

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
PLATE = hx('56709e'); HEADC = hx('5c77a6'); HIDE = hx('1f2a40'); HOOF = hx('3a3e47'); HOOFL = hx('5e636d')
BLACK = hx('0c0e12'); IVORY = hx('f6e0b0'); COLLAR = hx('3c4456'); TUFT = hx('252b38')
GLOW = {2: hx('ff7a18')}                                       # eyes: ONE flat glow colour (no hot centre / rim / glint)

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):                                    # ellipsoid signed distance (iq's estimate)
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def box(x0, x1, y0, y1, z0, z1):                    # symmetric in x (uses |x|)
    return (AX > x0) & (AX < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cap(a, b, ra, rb):                               # capsule a->b
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    return d <= ra + (rb - ra) * t
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
def col4(x, z, hx_, hz_):                            # rounded-square column section at (|x|, z)
    return ((AX - x) / hx_) ** 4 + ((Z - z) / hz_) ** 4 < 1

rng = np.random.RandomState(5)
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

# ---------------------------------------------------------------- body: real rhino anatomy (Indian-rhino armoured hide)
# barrel body with a sagging belly, neck hump over the shoulders, dip behind it, rounded rump, thick neck into the head,
# shoulder / thigh muscle masses where the legs join. Front = -z.
d = sd_ell((0, 25.5, 4), (16.0, 13.5, 29.0))                        # barrel
d = smin(d, sd_ell((0, 31.0, -14), (15.5, 13.5, 11.0)), 6)          # neck / shoulder hump (highest point)
d = smin(d, sd_ell((0, 28.5, 25), (16.5, 13.0, 12.5)), 6)           # rump
d = smin(d, sd_ell((0, 19.0, 5), (14.0, 9.5, 21.0)), 6)             # belly sag (lowest at mid body)
d = smin(d, sd_ell((0, 25.0, -26), (11.5, 11.5, 9.0)), 5)           # thick neck into the head
for sx in (1, -1):
    d = smin(d, sd_ell((11.5 * sx, 21.0, -13), (6.0, 10.0, 7.0)), 3)  # shoulder / upper front leg
    d = smin(d, sd_ell((11.5 * sx, 23.0, 25), (6.5, 11.5, 9.0)), 3)   # thigh
put(d < 0, HIDE, st=False)
# TRACED PLATE ARMOUR (research ch. 91, 92): the plates are traced from the concept's side view by scripts/trace_match.py
# (refs/WarRhino_plates.npz: one cell per brick of the side view = a plate number, and a height level per plate chosen so
# touching plates never share a level). Each brick of the hide looks up its plate by (z, y), so the plates lie in the
# concept's horizontal rows on both flanks and wrap over the back. Tops are flat (studs stay whole); every plate edge is a
# real step of 1-3 bricks.
TR = np.load(os.path.join(HERE, 'refs', 'WarRhino_plates.npz'))
pmap, plev = TR['plate'], TR['level']
ci = np.clip(np.round(Z - float(TR['z0'])).astype(int), 0, pmap.shape[1] - 1)
ri = np.clip(np.round(float(TR['ytop']) - Y).astype(int), 0, pmap.shape[0] - 1)
plate = pmap[ri, ci]; L_ = plev[plate].astype(float)
BELLY_Y = 13.5                                                         # below this the soft belly hide shows: no plates
shell = (d < L_ - .5) & (d > -2.5) & (Y > BELLY_Y)
TONE = (1.0, .94, 1.06)
put(shell, PLATE, p=0, l=0)
col[shell] = (PLATE[None] * (np.array(TONE)[plate[shell] % 3] * (.80 + .09 * L_[shell]))[:, None])   # proud plates lighter
pid[shell] = 2000 + plate[shell]; lvl[shell] = L_[shell]
put((d < .6) & (d > -2.5) & (Y > 9.5) & (Y <= BELLY_Y), HIDE * 1.4, st=False)                     # belly hide, darker
# bone spikes along the hump: base on the top surface, raked back
BONE = hx('8a7350')
for zs, L in ((-20, 4.5), (-13, 6.0), (-6, 6.5), (1, 5.5), (8, 4.0)):
    zi = int(round(zs - lo[2] - .5)); xi = int(round(0 - lo[0] - .5))
    col_ = np.where(kind[xi, :, zi] > 0)[0]
    if not len(col_): continue
    yt = lo[1] + .5 + col_.max()
    put(chain([(0, yt - 1.5, zs), (0, yt + L * .55, zs + 1.2), (0, yt + L, zs + 2.4)], [2.0, 1.2, .45]), BONE, st=False, p=newid(), l=6)
# ---------------------------------------------------------------- legs: plated pillars (thigh plate, knee band, cuff) + 3-toed hooves
for (lx, lz, yt) in ((12.5, -13, 22), (12.5, 25, 23)):
    put(col4(lx, lz, 6.6, 7.0) & (Y > 4) & (Y < yt), PLATE * .72, p=newid(), l=0)                      # leg core shows dark in the gaps
    put(col4(lx, lz, 8.6, 9.0) & (Y > 15.5) & (Y < yt + 2) & (AX > lx - 3), PLATE * 1.04, p=newid(), l=3)   # thigh shield, 2 bricks proud, outer side
    put(col4(lx, lz, 7.8, 8.2) & (Y > 9.5) & (Y < 13.5), PLATE * .98, p=newid(), l=2)                  # knee cap, 1 brick proud
    put(col4(lx, lz, 8.6, 9.0) & (Y > 3.5) & (Y < 7.5), PLATE * .86, p=newid(), l=3)                   # ankle cuff, 2 bricks proud
    x0 = lx - 7; zf = lz
    put(box(x0 + .5, x0 + 13.5, -1, 3.5, zf - 6, zf + 4), BLACK, st=False)                             # pad (shows in the toe gaps)
    put(box(x0 + 1, x0 + 13, -1, 3.5, zf + 4, zf + 6), HOOF * .9, st=False)                            # heel
    for t in range(3):
        a = x0 + 5 * t; f = 2 if t == 1 else 0
        put(box(a, a + 4, -1, 4.5, zf - 7 - f, zf + 4), HOOF, st=False)                                # toe body
        put(box(a + 1, a + 3, 4.4, 5.5, zf - 5 - f, zf + 3), HOOFL, st=False)                          # arched top
        put(box(a, a + 4, -1, 3.5, zf - 9 - f, zf - 7 - f), HOOF, st=False)                            # front step
        put(box(a + 1, a + 3, 3.4, 4.5, zf - 9 - f, zf - 7 - f), HOOFL, st=False)
        put(box(a + 1, a + 3, -1, 2.5, zf - 10 - f, zf - 9 - f), HOOF * 1.05, st=False)                # rounded tip
    put(box(x0 + 13, x0 + 14, -1, 4.5, zf - 2, zf - 1) | box(x0, x0 + 1, -1, 4.5, zf - 2, zf - 1), BLACK, st=False)   # side split: reads as 2 toes from the side

# ---------------------------------------------------------------- head: sloped profile (z, bottom, top, half width), rounded section
PROF = np.array([(-49, 12.0, 20.5, 7.0), (-46, 11.0, 21.5, 8.0), (-43, 10.5, 21.5, 8.5), (-42, 10.5, 21.5, 9.0), (-41, 10.5, 26.5, 10.0),
                 (-39, 10.5, 28.5, 10.5), (-36, 11.5, 30.0, 10.5), (-33, 13.0, 31.5, 10.5), (-30, 14.5, 32.5, 10.0), (-26, 16.5, 32.5, 9.5)])
hb = np.interp(Z, PROF[:, 0], PROF[:, 1]); ht = np.interp(Z, PROF[:, 0], PROF[:, 2]); hw = np.interp(Z, PROF[:, 0], PROF[:, 3])
hm = (hb + ht) / 2; hh = (ht - hb) / 2
head = ((AX / hw) ** 5 + (np.abs(Y - hm) / hh) ** 5 < 1) & (Z > -49) & (Z < -26)
HID = newid()
put(head, HEADC, p=HID, l=3)
put(head & (Y < 13.5), HEADC * .84, p=HID, l=3)                                    # jaw, a shade darker
put(head & (Y > 12.5) & (Y < 13.5) & (Z < -36), BLACK, st=False)                   # mouth line
put(box(0, 6.5, 13.5, 20.5, -50, -48.9) | box(0, 5.5, 20.4, 21.5, -50, -48.9), HEADC * 1.03, p=newid(), l=4)   # muzzle front plate
put(box(3, 5, 17.5, 19.5, -50, -48), BLACK, st=False)                              # nostrils (front)
put(box(10, 12.6, 14.5, 21.5, -40, -30), HEADC * .96, p=newid(), l=4)              # cheek plates, 2 bricks proud
put(box(0, 7, 32.4, 34.6, -37, -28), HEADC * 1.04, p=newid(), l=4)                 # crown plate, 2 bricks proud
put(box(7, 9, 16.5, 18.5, -48, -46) & head, BLACK, st=False)                       # nostrils (side)
# eyes: recessed almond under the brow. Dark socket ring, one flat orange glow.
put(box(4.5, 10.0, 22.5, 26.5, -41.4, -39.5), BLACK, st=False)                                   # socket (stays inside the head's side)
for (xa, xb, y) in ((5.5, 9.5, 23), (6.5, 10.5, 24), (8.5, 10.5, 25)):         # almond: outer corner high
    put(box(xa, xb, y - .5, y + .5, -42, -40), GLOW[2], k=2, st=False)
BR = newid()                                                                       # brow wedges stepping down to the horn
put(box(8.5, 12.0, 25.5, 28.5, -45, -35), HEADC * 1.1, p=BR, l=5)
put(box(6.5, 8.5, 24.5, 27.5, -45, -36), HEADC * 1.1, p=BR, l=5)
put(box(3, 6.5, 23.5, 26.5, -45, -38), HEADC * 1.1, p=BR, l=5)
put(box(4, 11, 25.5, 26.5, -45.2, -44), HIDE, st=False)                          # dark brow underside shadow
# ears: stepped triangles, dark inner on the front face
for y in range(31, 44):
    w = 4.2 * (1 - (y - 31) / 13.5) + .6; xc = 8.6 + (y - 31) * .22
    put((np.abs(AX - xc) < w) & (np.abs(Y - y) < .5) & (Z > -31) & (Z < -28), HEADC, p=newid(), l=3)
    if 33 <= y <= 39: put((np.abs(AX - xc) < w - 1.2) & (np.abs(Y - y) < .5) & (Z > -31) & (Z < -30), HIDE, st=False)
# horns: dark collars, cream capsule chains (no studs), main horn leans forward
put(((X ** 2 + (Z + 45.2) ** 2) < 5.6 ** 2) & (Y > 21) & (Y < 25), COLLAR, st=False)
put(chain([(0, 25.5, -45.8), (0, 30.5, -50.0), (0, 36.0, -53.6), (0, 41.5, -56.0), (0, 47.0, -57.0)], [5.2, 4.4, 3.3, 2.1, .7]), IVORY, st=False)
put(((X ** 2 + (Z + 37.3) ** 2) < 3.5 ** 2) & (Y > 28) & (Y < 30.6), COLLAR, st=False)
put(chain([(0, 30.0, -37.4), (0, 33.2, -39.4), (0, 36.6, -41.2)], [3.0, 2.0, .7]), IVORY, st=False)
# tail
put(chain([(0, 34, 35), (0, 31, 39), (0, 26, 40.5), (0, 21.5, 40.5)], [2.2, 1.9, 1.6, 1.5]), PLATE * .8, p=newid(), l=1)
put(sd_ell((0, 19.5, 40.5), (2.6, 3.4, 2.6)) < 0, TUFT, st=False)

# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .5
rim = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        rim |= (pid >= 2000) & (np_ >= 2000) & (np_ != pid) & (nl < lvl)
col[rim & ~dark & (kind == 1)] *= 1.22                                             # hard light edge on the proud plate
col *= np.clip(.62 + .55 * (Y / 50.0), .62, 1.18)[..., None]                      # lit tops, dark underside
col = np.clip(col, 0, 1)
# voxel-style: VOXEL SIZE = 1 unit (= 2.5 studs in game). PALETTE <= 16: snap every solid brick to its nearest entry.
PAL = np.array([hx(h) for h in ('7d97c8', '5f79a8', '4a6090', '384a72', '27344f',      # armour: light / main / side / dark / shadow
                                 '1a2236', '121828',                                  # seam / deep crease
                                 '6c88ba',                                            # head highlight
                                 '3a3e47', '5e636d', '0b0d11',                        # hoof / hoof light / black
                                 'f2d8a2', 'c9a86e', '8a7350', '2e3546')])            # ivory / ivory shade / bone spike / horn collar
sol = kind == 1
cs = col[sol]; dd = ((cs[:, None, :] - PAL[None]) ** 2).sum(-1)
col[sol] = PAL[np.argmin(dd, 1)]
print('PALETTE', len(PAL), 'colours in use:', len(np.unique(np.argmin(dd, 1))))

# ---------------------------------------------------------------- mesh: exposed faces (vertex colours) + studs on 2x2 flat tops
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb

STUD_PNG = os.path.join(HERE, '..', '..', 'assets', 'roblox_square_studs.png')
def build(name, mask, with_studs):
    """exposed brick faces as flat quads; UVs = brick coords / 4 so the 4x4 stud tile puts ONE stud on every brick face"""
    verts = []; faces = []; cols = []; uvs = []; nv = 0
    for ax in range(3):
        u, w = [k for k in range(3) if k != ax]
        for s in (1, -1):
            e = np.argwhere(exposed(mask, ax, s))
            if not len(e): continue
            base = lo + e; off = np.zeros(3); off[ax] = 1 if s > 0 else 0
            q = []; t = []
            for du, dw in ((0, 0), (1, 0), (1, 1), (0, 1)):
                dd = off.copy(); dd[u] = du; dd[w] = dw; q.append(base + dd)
                t.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w] + dw) / 16.0], 1))   # Roblox square-stud tile (8x8 studs): one stud per 2x2 bricks
            q = np.stack(q, 1); t = np.stack(t, 1); k = len(e)
            idx = nv + np.arange(4 * k).reshape(k, 4)
            if not ((s > 0) != (ax == 1)): idx = idx[:, ::-1]; t = t[:, ::-1]; q = q[:, ::-1]; idx = nv + np.arange(4 * k).reshape(k, 4)
            verts.append(q.reshape(-1, 3)); faces.append(idx); nv += 4 * k; uvs.append(t.reshape(-1, 2))
            cols.append(np.repeat(col[e[:, 0], e[:, 1], e[:, 2]], 4, axis=0))
    Vt = np.concatenate(verts); Cv = np.concatenate(cols); UV = np.concatenate(uvs)
    Vb = np.stack([Vt[:, 0], Vt[:, 2], Vt[:, 1]], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(Vb.tolist(), [], np.concatenate(faces).tolist())
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.concatenate([lin(np.clip(Cv, 0, 1)), np.ones((len(Cv), 1))], 1).ravel())
    ul = me.uv_layers.new(name='UVMap')
    li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
    ul.data.foreach_set('uv', UV[li].ravel())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
body = build('Rhino', kind == 1, True)
m = bpy.data.materials.new('Brick'); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
bs.inputs['Roughness'].default_value = .6
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
tx.image.colorspace_settings.name = 'Non-Color'                     # overlay values: .5 = unchanged, lighter = highlight, darker = shadow
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 1
nt.links.new(at.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
body.data.materials.append(m); body['glow'] = False
GL = []
for k, c in GLOW.items():
    if not (kind == k).any(): continue
    o = build('Glow%d' % k, kind == k, False)
    gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
    cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
    b2.inputs['Emission Strength'].default_value = 5.0; gm.diffuse_color = cl
    o.data.materials.append(gm); o.color = cl; GL.append(o)
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for sx in (1, -1):                                                         # eye lights: the glow spills onto brow + snout
        L = bpy.data.objects.new('EyeLight%d' % sx, bpy.data.lights.new('EyeLight%d' % sx, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = 2500; L.data.color = (1.0, .32, .06); L.data.shadow_soft_size = 1.0
        L.location = B(8.0 * sx, 24.0, -44.5)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.75, .8, .9)
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.26, .4, .2, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 5000
    def view(name, tgt, dist, az, el, lens=50, ortho=None):
        t = B(*tgt)
        dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
        cam.location = t + dv * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        cam.data.type = 'ORTHO' if ortho else 'PERSP'
        if ortho: cam.data.ortho_scale = ortho
        p = os.path.join(REN, '%s_%s.png' % (ID, name))
        sc.render.engine = ENG; sc.render.film_transparent = False; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_shadows = False; sh.show_cavity = False
        g.hide_render = True; sc.render.film_transparent = True; sc.render.filepath = p[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
        sc.render.film_transparent = False; keep = tuple(sc.world.color); sc.world.color = (0, 0, 0); sh.background_type = 'WORLD'
        body.color = (0, 0, 0, 1)
        sc.render.filepath = p[:-4] + '_glow.png'; bpy.ops.render.render(write_still=True)
        sc.world.color = keep; g.hide_render = False
    cen = (0, 24, -3); D = 172
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 24, -4), 300, az, el, ortho=125)
    for nm, a in (('rest_34', (cen, D, -35, 14)), ('rest_side', (cen, D, 90, 8)), ('rest_front', (cen, D, 0, 8)), ('rest_back', (cen, D, 150, 18)),
                  ('face', ((0, 22, -42), 56, 0, 4)), ('headside', ((0, 24, -38), 66, 90, 4)), ('head34', ((0, 24, -40), 70, -38, 10)),
                  ('footfront', ((-14, 5, -16), 36, 0, 6)), ('footside', ((-14, 5, -16), 40, -90, 4)), ('feet', ((0, 9, 8), 150, 90, 2))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()

# ---------------------------------------------------------------- rig (always): bones in brick coords, L = +x
RIG = [('root', None, (0, 0, 4), (0, 6, 4)), ('hips', 'root', (0, 26, 24), (0, 27, 8)), ('spine', 'hips', (0, 27, 8), (0, 29, -12)),
       ('neck', 'spine', (0, 28, -12), (0, 26, -27)), ('head', 'neck', (0, 25, -27), (0, 22, -48)), ('jaw', 'head', (0, 13, -34), (0, 12, -49)),
       ('tail', 'hips', (0, 34, 36), (0, 20, 41))]
OVR = [((Z > 28) & ~((AX < 3.5) & (Z > 37.5)), 'hips'), ((AX < 3.5) & (Z > 37.5), 'tail'),
       ((Z < -27) & (Y > 13), 'head'), ((Z < -34) & (Y < 13), 'jaw')]
for sx, sd in ((1, 'L'), (-1, 'R')):
    for lz, fb in ((-13, 'F'), (25, 'B')):
        up, lw = 'leg%s%s_up' % (fb, sd), 'leg%s%s_low' % (fb, sd)
        RIG += [(up, 'spine' if fb == 'F' else 'hips', (12.5 * sx, 21, lz), (12.5 * sx, 11, lz)), (lw, up, (12.5 * sx, 11, lz), (12.5 * sx, 1, lz - 2))]
        leg = (((X * sx - 12.5) / 7.6) ** 4 + ((Z - lz) / 8.5) ** 4 < 1) | ((X * sx > 4.5) & (X * sx < 20.5) & (Z > lz - 13) & (Z < lz + 7) & (Y < 6))
        OVR += [(leg & (Y < 20) & (Y >= 11), up), (leg & (Y < 11), lw)]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (25, 0, 0), 'jaw': (25, 0, 0), 'legFL_up': (30, 0, 0), 'legBR_up': (-25, 0, 0), 'tail': (0, 0, 20)},
                 render='render' in argv)
print('BL_OK')
