# Venom Widow (stud-voxel spider boss, brick pipeline). Reference = concept_sheet.jpg (this folder).
# GLOW: subtle   (tight halo only on the 2 big eyes; small eyes + hourglass + drips are solid lime bricks)
# Built from the War Rhino brick example: blended anatomy field -> plates with stepped seams -> brick faces + square-stud overlay -> EEVEE.
# Run: powershell -File <skill>\scripts\run_brick.ps1 venom_widow_brick.py [views]
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit (= 2.5 studs in game).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'VenomWidow'

lo = np.array((-80.0, -0.5, -74.0)); hi = np.array((80.0, 74.5, 66.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)      # kind 0 empty, 1 solid, 2+ glow
pid = np.zeros(n, np.int32); lvl = np.zeros(n)                                      # plate id / plate height level

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
BLACK = hx('120c18'); DARK = hx('241830'); DEEP = hx('35214c'); PURP = hx('4f2e70'); PURPL = hx('6b3e96')
LIME = hx('a6f21a'); VIO = hx('a83cf0'); VIOL = hx('c672ff'); FANG = hx('5a5664'); FANGL = hx('86818f'); FANGD = hx('2e2a36')
GLOW = {2: hx('a6f21a'),   # EYEFIX: big eyes = LIME, same as the small eyes
        3: hx('c2ff3c'), 4: hx('f0ffd0')}   # toxic green edge / hot centre / glint

def put(m, rgb, k=1, st=True, p=0, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = p; lvl[m] = l

def sd_ell(c, r):                                    # ellipsoid signed distance (iq's estimate)
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2) + 1e-9
    return k0 * (k0 - 1) / k1
def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def cap(a, b, ra, rb, flat=False):                   # capsule a->b (flat = cylinder with flat ends)
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t0 = ((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab); t = np.clip(t0, 0, 1)
    d = np.sqrt((X - a[0] - ab[0] * t) ** 2 + (Y - a[1] - ab[1] * t) ** 2 + (Z - a[2] - ab[2] * t) ** 2)
    m = d <= ra + (rb - ra) * t
    return m & (t0 >= 0) & (t0 <= 1) if flat else m
def chain(pts, radii):
    m = np.zeros(n, bool)
    for i in range(len(pts) - 1): m |= cap(pts[i], pts[i + 1], radii[i], radii[i + 1])
    return m
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]
rng = np.random.default_rng(7)
SPK = np.zeros(n, bool); KEEP = np.zeros(n, bool)                                                   # bricks the height shading must not darken (fangs)

# ---------------------------------------------------------------- abdomen: huge stepped sphere, latitude bands, hourglass x2
AC = np.array((0.0, 45.0, 33.0)); AR = np.array((27.0, 25.0, 29.0))
sdA = sd_ell(AC, AR)
abd = sdA < 0
lat = np.degrees(np.arcsin(np.clip((Y - AC[1]) / AR[1], -1, 1)))
band = np.floor((lat + 90) / 15).astype(int)
lon = np.degrees(np.arctan2(X - AC[0], -(Z - AC[2]))) + 180                # 0..360 around the vertical axis
abd2 = abd | ((sd_ell(AC, AR + .9) < 0) & (band % 2 == 1))                 # odd rings stand 1 brick proud
plate = np.zeros(n, int)                                                   # staggered plates of uneven length along each ring
for b_ in range(12):
    cuts = np.cumsum(rng.uniform(20, 42, 20)) + rng.uniform(0, 30)
    plate[band == b_] = np.searchsorted(cuts, lon[band == b_])
for b_ in np.unique(band[abd2]):
    for q_ in np.unique(plate[abd2 & (band == b_)]):
        m_ = abd2 & (band == b_) & (plate == q_)
        put(m_, (DEEP if b_ % 2 else DARK) * (1.08 if (q_ + b_) % 2 else 1.0), p=2000 + b_ * 20 + q_, l=1 + (b_ % 2) * .8)
put(abd2 & (lat > 66), DEEP, p=2999, l=1.6)                                 # one cap plate over the top pole (no bullseye)
abd = abd2; sdA = np.minimum(sdA, sd_ell(AC, AR + .9))
surf = abd & (sdA > -1.6)
groove = surf & (band != np.roll(band, 1, axis=1)) & (np.abs(Y - AC[1]) < AR[1] * .93)
put(groove, BLACK, st=False)                                               # black groove between rings
put(surf & (rng.random(n) < .05), PURP, p=2100, l=1.2)                      # scattered lighter bricks
put(surf & (rng.random(n) < .02), PURPL, p=2101, l=1.2)
put(abd & (Y < AC[1] - 12), BLACK, st=False)                               # dark belly
D = np.stack([(X - AC[0]) / AR[0], (Y - AC[1]) / AR[1], (Z - AC[2]) / AR[2]], -1)
D /= np.linalg.norm(D, axis=-1, keepdims=True) + 1e-9
def hourglass(elev, back, V=.62, k=1.0, umax=1.0):                          # flat studded lime bricks (no glow), black rim
    m_ = np.array((0, math.sin(math.radians(elev)), (1 if back else -1) * math.cos(math.radians(elev))))
    e2 = np.cross(np.array((1.0, 0, 0)), m_)                               # meridian direction
    v = np.arctan2(D @ e2, D @ m_); u = D[..., 0]; fw = (D @ m_) > 0
    w = np.minimum((.07 + .42 * np.abs(v) / V) * k, umax)
    sh2 = abd & (sdA > -2.8) & fw                                           # deep shell: also covers the ring step faces
    shape = sh2 & (np.abs(v) < V) & (np.abs(u) < w)
    rim = sh2 & (np.abs(v) < V + .07) & (np.abs(u) < w + .07) & ~shape
    put(rim, BLACK, st=False)
    put(shape, LIME, p=9000, l=9); KEEP[shape] = True
hourglass(40, False, .46, 1.25, .5)
hourglass(24, True)
put(sd_ell((0, 32, 59), (3, 2.5, 2.5)) < 0, BLACK, st=False)                   # spinnerets
put(chain([(0, 28, 0), (0, 31, 9)], [6, 7]), BLACK, st=False)              # pedicel

# ---------------------------------------------------------------- cephalothorax + head (1.5x, pushed forward): blended, armoured top plates
HY = 5.0; Y0 = Y; Y = Y0 - HY                                               # head group modelled HY lower, lands HY higher
TC = (0.0, 24.0, -16.0); TR = (20.0, 11.0, 18.0); HC = (0.0, 25.0, -39.0); HR = (18.5, 13.5, 13.5)
sdT = sd_ell(TC, TR); sdH = sd_ell(HC, HR); sdC = smin(sdT, sdH, 4.5)
ceph = sdC < 0
put(ceph, DEEP, p=newid(), l=2)
PZ = [-54, -35, -20, -8, 3]
for k_ in range(4):
    z0, z1 = PZ[k_], PZ[k_ + 1]
    t = np.clip((Z - z0) / (z1 - z0), 0, 1)
    sh = (sdC < .6 + 1.0 * t) & (Z > z0) & (Z < z1) & (Y > 28 - 2.2 * (AX / 18) ** 2)
    put(sh, PURP if k_ % 2 == 0 else DEEP, p=3000 + k_, l=3 + (k_ % 2) * .5)
for z in PZ[1:-1]:
    put((np.abs(Z - z) < .8) & (kind == 1) & (pid >= 3000) & (pid < 3100), DARK, st=False)
put((kind == 1) & ceph & (Y < 18), BLACK, st=False)                        # dark underside (sternum)
put(ceph & (AX < 1.6) & (Y > 32) & (Z > -30) & (Z < 0), VIO, p=newid(), l=5)  # violet dorsal ridge

# ---------------------------------------------------------------- eyes: 2 big round + 6 small crossed eyes, flush, dark sockets
def zsurf(x, y):
    q = 1 - ((x - HC[0]) / HR[0]) ** 2 - ((y - HC[1]) / HR[1]) ** 2
    return HC[2] - HR[2] * math.sqrt(max(q, 0))
def eye(x, y, r, big=False):                         # x, y on voxel centres so discs are symmetric (r 1.4 = crossed box, 1.5 would fill the 3x3)
    for s in (1, -1):
        zs = zsurf(x * s, y)
        disc = (X - x * s) ** 2 + (Y - y) ** 2; dz = 3 if big else 1.6          # shallow small eyes: no smear over the curved head
        put((disc < (r + 1.0) ** 2) & (Z > zs - 1.5) & (Z < zs + dz) & (kind > 0), BLACK, st=False)
        e_ = (disc < r * r) & (Z > zs - 1.5) & (Z < zs + dz)
        if not big:                                                         # small eye: solid round lime bricks, no glow
            put(e_, LIME, st=False); KEEP[e_] = True
        else:
            put(e_, GLOW[2], k=2, st=False)
        if big:                                                             # EYEFIX: no hot centre / glint
            kind[e_ & (Z < zs + .5)] = 0                                    # recessed 1 brick
put(ceph & (Y > 36.0) & (Z < -42) & (kind == 1), PURPL, p=newid(), l=6)        # brow plate over the eye cluster
eye(5.5, 23.5, 4.0, True)                                                  # 2 big eyes, front-centre
eye(3.5, 32.5, 2.2); eye(10.5, 30.5, 2.2); eye(12.5, 21.5, 2.2)          # 6 small eyes in a cluster round them

# ---------------------------------------------------------------- fangs (2x horn hooks curving in) + venom drops + pedipalps
for s in (1, -1):
    put(sd_ell((5.5 * s, 14.5, -48.0), (4.4, 5.0, 4.4)) < 0, DEEP, p=newid(), l=4)
    P = [(5.5 * s, 13.0, -51.0), (8.5 * s, 9.5, -55.0), (9.6 * s, 5.5, -57.0), (8.6 * s, 2.0, -57.0), (6.2 * s, .4, -55.8)]
    f = chain(P, [1.6, 1.5, 1.2, .85, .3]); KEEP[f] = True               # slim tusk, 2-3 bricks thick, tapering, hooking inward
    put(f, FANGL, p=newid(), l=5)
    put(f & (np.floor(Y) % 3 == 0), FANG, p=newid(), l=5)
    put(f & (Y > 14.5), FANG, st=False)
    put(f & (AX < 7) & (Y < 6), FANG, st=False)
    for (x_, y_, z_), L_ in (((6.2 * s, 0.0, -55.8), 4.4), ((9.4 * s, 4.0, -57.4), 3.6)):   # goo hanging straight down, tapering
        dr = cap((x_, y_ + .6, z_), (x_, y_ - L_, z_), 1.2, .4)
        put(dr & ~f, LIME, st=False); KEEP[dr] = True
        
    put(cap((11 * s, 15, -46), (14.5 * s, 12.5, -53), 1.6, 1.4), PURP, p=newid(), l=4)          # slim pedipalps
    put(cap((14.5 * s, 12.5, -53), (14.3 * s, 7, -56), 1.3, 1.0), PURPL, p=newid(), l=4.5)
    put(cap((14.3 * s, 7, -56), (13.6 * s, 4.5, -56.5), .9, .3), BLACK, st=False)
    put(cap((14.5 * s, 13.4, -52.2), (14.5 * s, 11.6, -53.8), 1.9, 1.9, flat=True), VIO, p=newid(), l=6)

Y = Y0
# ---------------------------------------------------------------- legs: 4 pairs, femur up to a high knee, tibia down, black claw tip
def unit(v): v = np.array(v, float); return v / np.linalg.norm(v)
def spikes(a, b, r, out, ts):                        # one regular row of distinct black spikes along the top-outer edge
    a = np.array(a, float); b = np.array(b, float); d = unit(b - a)
    up = np.array((0, 1.0, 0)) + .6 * out; up -= d * up.dot(d); up = unit(up)
    for t in ts:
        p_ = a + (b - a) * t
        m_ = cap(p_ + up * (r - .5), p_ + up * (r + 4.6) + d * 1.6, 1.5, .15); put(m_, BLACK, st=False); SPK[m_] = True
def band(p_, d, r):
    p_ = np.array(p_, float); m_ = cap(p_ - d * 1.4, p_ + d * 1.4, r + .6, r + .6, flat=True)
    put(m_, VIO, p=newid(), l=6); put(m_ & (Y > p_[1] + r * .3), VIOL, p=newid(), l=6.5)
NEXT[0] = 5000                                                             # leg plate ids start here
LEGS = [(-20, -50, 66, 22, 46, 62, -5, 48), (-13, -4, 64, 26, 52, 64, -4, 35), (-6, 20, 64, 26, 52, 62, 20, 35), (1, 46, 60, 23, 48, 58, 46, 31)]
for (z0, ang, ky, kr, mr, tr, kang, my) in LEGS:
    for s in (1, -1):
        o = np.array((math.cos(math.radians(ang)) * s, 0, math.sin(math.radians(ang))))
        def at(r_, y_): return (14 * s + o[0] * r_, y_, z0 + o[2] * r_)
        ok = np.array((math.cos(math.radians(kang)) * s, 0, math.sin(math.radians(kang))))
        A = at(0, 27); C_ = at(5, 32); K = (14 * s + ok[0] * kr, ky, z0 + ok[2] * kr); M = at(mr, my); T = at(tr, .6)
        Tm = tuple(np.array(M) * .45 + np.array(T) * .55 + np.array((0, 3, 0)))
        put(cap(A, C_, 4.0, 3.8), DARK, p=newid(), l=2)                               # coxa
        put(cap(C_, K, 3.9, 3.4), DEEP, p=newid(), l=3)                               # femur
        put(cap(K, M, 3.3, 2.5), DEEP, p=newid(), l=3.5)                              # tibia
        put(cap(M, Tm, 2.4, 1.6), DARK, p=newid(), l=3)                               # metatarsus
        put(cap(Tm, T, 1.6, .3), BLACK, st=False)                                     # claw
        band(C_, unit(np.array(K) - C_), 3.7); band(K, unit(np.array(M) - K), 3.2); band(M, unit(np.array(Tm) - M), 2.4)
        spikes(C_, K, 3.6, o, (.2, .4, .6, .8)); spikes(K, M, 2.9, o, (.2, .4, .6, .8)); spikes(M, Tm, 2.0, o, (.35, .7))

topx = (kind == 1) & ~np.roll(kind > 0, -1, axis=1) & (pid >= 5000) & (col[..., 0] < .3) & (Y > 8)
col[topx] = PURP                                                           # lighter purple tops on the leg segments
col[SPK & (kind == 1) & ~np.roll(kind > 0, -1, axis=1)] = FANG             # spikes: lighter grey top face
# ---------------------------------------------------------------- seams: the lower plate darkens where it meets a higher neighbour
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & ((nl > lvl) | ((nl == lvl) & (np_ > pid)))
col[dark & (kind == 1)] *= .62
col *= np.where(KEEP, 1.0, np.clip(.7 + .5 * (Y / 50.0), .7, 1.2))[..., None]                       # lit tops, dark underside
col = np.clip(col, 0, 1)
PAL = np.array([hx(h) for h in ('0c0810', '18101f', '241830', '2e1f40', '3a2652', '4a2e68', '5c3880', '7044a0',   # black .. purple ladder
                                 '9638dc', 'b45af8', 'd090ff',                                                     # violet bands
                                 '5a5664', '86818f', 'a8a3b0', 'a6f21a', '86cc12')])                                          # fang greys
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
body = build('VenomWidow', kind == 1, True)
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
    for nm, p, e in (('EyeL', (5.5, 28.5, -58), 1200), ('EyeR', (-5.5, 28.5, -58), 1200)):   # green eye/hourglass lights
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); sc.collection.objects.link(L)
        L.data.energy = e * .35; L.data.color = (.381, .888, .010)   # = LIME a6f21a (linear); L.data.shadow_soft_size = 1.0
        L.location = B(*p)
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -12), 22), ('FillL', 1.5, (62, 0, -80), 40), ('FillR', 1.7, (62, 0, 80), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.78, .78, .8)
    for attr in ('use_gtao', 'use_raytracing'):
        try: setattr(sc.eevee, attr, True)
        except Exception: pass
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -.5), (s, -s, -.5), (s, s, -.5), (-s, s, -.5)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.5, .5, .52, 1)
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
    cen = (0, 28, -8); D = 235
    for nm, az, el in (('ortho_front', 0, 0), ('ortho_side', 90, 0), ('ortho_back', 180, 0), ('ortho_top', 0, 89.9)):
        if not ONLY or nm in ONLY: view(nm, (0, 33, -4), 400, az, el, ortho=162)
    for nm, a in (('rest_34', (cen, D, -35, 14)), ('rest_side', (cen, D, 90, 6)), ('rest_front', (cen, D, 0, 6)), ('rest_back', (cen, D, 180, 8)),
                  ('face', ((0, 24, -52), 90, 0, 4)), ('headside', ((0, 24, -38), 130, 90, 10)), ('head34', ((0, 24, -44), 100, -35, 10)),
                  ('footfront', ((-40, 30, -40), 70, -40, 12)), ('feet', ((0, 20, -6), 270, 0, 30))):
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): thorax + head + abdomen, 8 legs x 3, fangs + pedipalps on the head; L = +x
RIG = [('root', None, (0, 0, 0), (0, 6, 0)), ('thorax', 'root', (0, 29, 2), (0, 30, -30)), ('head', 'thorax', (0, 30, -30), (0, 31, -54)),
       ('abdomen', 'thorax', (0, 30, 3), (0, 45, 62))]
OVR = [((Z > 3) & (kind > 0), 'abdomen'), ((Z <= 3) & (kind > 0), 'thorax'), ((Z < -33) & (kind > 0), 'head')]
LEGM = []; LEGC = []
for s, sd in ((1, 'L'), (-1, 'R')):
    fang = (s * X > 0) & (kind > 0) & ((sd_ell((5.5 * s, 19.5, -48.0), (4.6, 5.2, 4.6)) < 0) |
            chain([(5.5 * s, 18.0, -51.0), (8.5 * s, 14.5, -55.0), (9.6 * s, 10.5, -57.0), (8.6 * s, 7.0, -57.0), (6.2 * s, 5.4, -55.8)], [2.6, 2.5, 2.2, 1.9, 1.4]) |
            ((AX > 4) & (AX < 11.5) & (Y < 6) & (Z < -53) & (Z > -60)))
    palp = (s * X > 0) & (kind > 0) & chain([(11 * s, 20, -46), (14.5 * s, 17.5, -53), (14.3 * s, 12, -56), (13.6 * s, 9.5, -56.5)], [2.6, 2.9, 2.0, 1.4])
    RIG += [('fang' + sd, 'head', (5.5 * s, 20, -48), (8 * s, 4, -57)), ('palp' + sd, 'head', (11 * s, 20, -46), (14 * s, 9, -56))]
    OVR += [(fang, 'fang' + sd), (palp & ~fang, 'palp' + sd)]
    for i, (z0, ang, ky, kr, mr, tr, kang, my) in enumerate(LEGS):
        o = np.array((math.cos(math.radians(ang)) * s, 0, math.sin(math.radians(ang))))
        ok = np.array((math.cos(math.radians(kang)) * s, 0, math.sin(math.radians(kang))))
        A = (14 * s, 27, z0); K = (14 * s + ok[0] * kr, ky, z0 + ok[2] * kr); M = (14 * s + o[0] * mr, my, z0 + o[2] * mr); T = (14 * s + o[0] * tr, .6, z0 + o[2] * tr)
        nm = 'leg%d%s' % (i + 1, sd)
        LEGC.append([(nm + '_1', 'thorax', A, K), (nm + '_2', nm + '_1', K, M), (nm + '_3', nm + '_2', M, T)])
        LEGM.append(chain([A, K, M, T], [9.5, 9, 8, 6]))
for c in LEGC: RIG += c
cand = np.zeros(n, bool)
for m_ in LEGM: cand |= m_
cand &= (kind > 0) & ~(ceph & (AX < 19)) & ~abd
ci = np.argwhere(cand); P = lo + .5 + ci                                           # each candidate brick -> nearest leg polyline
dl = np.full((len(ci), len(LEGC)), 1e9)
for j, c in enumerate(LEGC):
    for _, _, a, b in c:
        a = np.array(a); b = np.array(b); ab = b - a; t = np.clip(((P - a) @ ab) / ab.dot(ab), 0, 1)
        dl[:, j] = np.minimum(dl[:, j], np.linalg.norm(P - a - t[:, None] * ab, axis=1))
own = np.argmin(dl, 1)
for j, c in enumerate(LEGC):
    m_ = np.zeros(n, bool); sel = ci[own == j]; m_[sel[:, 0], sel[:, 1], sel[:, 2]] = True
    OVR += brick_rig.limb(X, Y, Z, m_, c)
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'head': (0, 15, 0), 'fangL': (30, 0, 0), 'palpR': (-35, 0, 0), 'leg1L_1': (0, 0, 25), 'leg1L_2': (0, 0, -30),
                       'leg3R_1': (0, 25, 0), 'abdomen': (-15, 0, 0)},
                 render='render' in argv)
print('BL_OK')
