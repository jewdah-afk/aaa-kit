# SKILL EXAMPLE (approved look 2026-11): reference = user screenshot of a blue voxel steam train; Roblox square-stud overlay at 2x2
# GLOW: normal   (read by scripts/run_brick.ps1: strong = GLOW_STRONG=1 eye halo)
# Arcane Express - voxel steam locomotive (stud-voxel, all in Blender) after the user's reference: deep-blue studded body,
# glowing cyan rune disc on the smokebox, glowing domes / lanterns, cab with windows, 3 big driving wheels with rods,
# striped cowcatcher, rails with wooden ties. Run: blender -b --factory-startup --python train_fable.py -- render
# Design coords: x right, y up, z back (front = -z). 1 voxel = 1 unit.
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, next(p for p in (os.path.join(HERE, '..', '..', 'scripts'), os.path.expanduser('~/.claude/skills/stud-voxel-creatures/scripts')) if os.path.exists(os.path.join(p, 'brick_rig.py'))))
import brick_rig
OUT = os.path.join(HERE, 'out_' + os.path.splitext(os.path.basename(__file__))[0]); REN = os.path.join(OUT, 'render'); os.makedirs(REN, exist_ok=True)
ID = 'Train'

lo = np.array((-15.0, -3.0, -110.0)); hi = np.array((15.0, 50.0, 110.0))
n = (hi - lo).astype(int)
cx = lo[0] + .5 + np.arange(n[0]); cy = lo[1] + .5 + np.arange(n[1]); cz = lo[2] + .5 + np.arange(n[2])
X, Y, Z = np.meshgrid(cx, cy, cz, indexing='ij'); AX = np.abs(X)
col = np.zeros((*n, 3)); kind = np.zeros(n, np.int8); stud = np.zeros(n, bool)
pid = np.zeros(n, np.int32); lvl = np.zeros(n)

def hx(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
BLUE = hx('2452d4'); BLUE2 = hx('1b3fae'); NAVY = hx('122466'); DEEP = hx('0b1440'); TRIM = hx('9fb4ff')
STEEL = hx('9aa6b8'); STEELD = hx('5a6476'); BLACK = hx('0c0f18'); WHITE = hx('e8ecf4'); WOOD = hx('b0784a'); WOODD = hx('7a4e2c')
RAIL = hx('c8ccd4'); GLASS = hx('a8b4cc'); GOLD = hx('d8b45a')
GLOW = {2: hx('3ee8ff'), 3: hx('0b5fa8'), 4: hx('e8fdff')}
NEXT = [10]
def newid(): NEXT[0] += 1; return NEXT[0]

def put(m, rgb, k=1, st=True, p=None, l=0.0):
    col[m] = rgb; kind[m] = k; stud[m] = st; pid[m] = newid() if p is None else p; lvl[m] = l
def box(x0, x1, y0, y1, z0, z1, sym=True):
    xx = AX if sym else X
    return (xx > x0) & (xx < x1) & (Y > y0) & (Y < y1) & (Z > z0) & (Z < z1)
def cylz(yc, r, z0, z1, xc=0.0):               # cylinder along z
    return ((X - xc) ** 2 + (Y - yc) ** 2 < r * r) & (Z > z0) & (Z < z1)
def cyly(xc, zc, r, y0, y1):                   # cylinder along y
    return ((X - xc) ** 2 + (Z - zc) ** 2 < r * r) & (Y > y0) & (Y < y1)
def disc_x(yc, zc, r, x0, x1):                 # wheel disc (axis x), symmetric
    return ((Y - yc) ** 2 + (Z - zc) ** 2 < r * r) & (AX > x0) & (AX < x1)
def dome(xc, yc, zc, r):                       # hemisphere on top
    return ((X - xc) ** 2 + (Y - yc) ** 2 + (Z - zc) ** 2 < r * r) & (Y >= yc)

# ---------------------------------------------------------------- track: rails + wooden ties (static scenery, part of the model file)
for zt in range(-106, 108, 7):
    put(box(0, 13, -3, -1, zt - 1.6, zt + 1.6), WOOD if (zt // 7) % 2 else WOODD, st=False)
put(box(6, 8, -1, 0.6, -110, 110), RAIL, st=False)
put(box(5.5, 8.5, -1, -0.4, -110, 110), STEELD, st=False)

# ---------------------------------------------------------------- chassis: frame, running board (light trim edge), buffer beam
put(box(0, 9, 3, 9, -36, 36), DEEP, st=False)                                         # deep frame between the wheels
put(box(0, 12.5, 10, 12, -38, 38), NAVY)                                              # running board
put(box(11.5, 12.5, 10, 12.4, -38, 38), TRIM, st=False)                               # light edge strip
put(box(0, 12.5, 6, 10, -40, -36), NAVY)                                              # buffer beam
for bx in (-8, 8):
    put(cylz(8, 1.4, -43, -40, bx), STEELD, st=False)                                 # buffers
    put(cylz(8, 2.0, -43.5, -42.5, bx), STEEL, st=False)

# ---------------------------------------------------------------- boiler: studded blue cylinder with navy bands, smokebox, cyan rune disc
put(cylz(21, 9.0, -30, 14), BLUE)
for zb in (-22, -12, -2, 8):
    put(cylz(21, 9.4, zb - .8, zb + .8), NAVY, st=False)                              # boiler bands
put(cylz(21, 9.8, -36, -30), BLUE2)                                                    # smokebox (a step wider)
put(cylz(21, 10.4, -37, -35.5), NAVY, st=False)                                        # smokebox ring
put(cylz(21, 8.6, -38.5, -36.5), DEEP, st=False)                                       # recess behind the disc
disc = cylz(21, 8.2, -40, -37)
put(disc, GLOW[2], k=2, st=False)                                                      # glowing rune disc
rr = np.sqrt(X ** 2 + (Y - 21) ** 2); th = np.arctan2(Y - 21, X)
sa = np.mod(th + np.pi / 2, 2 * np.pi / 5) - np.pi / 5                                 # 5-point star outline
star = np.abs(rr * np.cos(sa) - (2.2 + 3.6 * (1 - np.abs(sa) / (np.pi / 5)))) < .55
put(disc & ((np.abs(rr - 6.8) < .6) | (star & (rr < 6.3)) | (np.abs(rr - 2.0) < .5)) & (Z < -39), GLOW[3], k=3, st=False)
for a in range(0, 360, 45):                                                          # spokes of light between ring and star
    ca, sa2 = math.cos(math.radians(a)), math.sin(math.radians(a))
    put(disc & (np.abs(X * sa2 - (Y - 21) * ca) < .45) & (rr > 6.0) & (rr < 7.6) & (Z < -39), GLOW[3], k=3, st=False)
put(cylz(21, 1.4, -40.5, -39), GLOW[4], k=4, st=False)                                 # hot centre
for a in range(0, 360, 30):                                                            # rivets round the ring
    xr, yr = 9.6 * math.cos(math.radians(a)), 21 + 9.6 * math.sin(math.radians(a))
    put(cylz(yr, .8, -38, -36.6, xr), STEEL, st=False)

# ---------------------------------------------------------------- chimney (glowing crown), domes, lanterns
put(cyly(0, -30, 3.2, 28, 38), NAVY)
put(cyly(0, -30, 4.4, 38, 41), DEEP, st=False)                                         # flared crown
put(cyly(0, -30, 4.6, 41, 42.5) & ~cyly(0, -30, 3.2, 41, 42.5), GLOW[2], k=2, st=False)
put(cyly(0, -30, 3.0, 40, 41.6), BLACK, st=False)
for (zc, r, gl) in ((-16, 4.2, True), (-4, 3.4, False), (6, 3.8, True)):
    put(cyly(0, zc, r, 28, 31), NAVY, st=False)
    put(dome(0, 31, zc, r), GLOW[2] if gl else BLUE, k=2 if gl else 1, st=not gl)
put(dome(0, 34.6, -16, 1.6), GLOW[4], k=4, st=False)
for zl in (-24, -10, 2):                                                               # side lanterns on the boiler shoulder
    for s in (-1, 1):
        put(box(5.5, 8.5, 27, 30, zl - 1.5, zl + 1.5) & (np.sign(X) == s), DEEP, st=False)
        put(box(6, 8, 27.5, 29.5, zl - 1, zl + 1) & (np.sign(X) == s), GLOW[2], k=2, st=False)
put(box(0, 2, 30, 32, -27, -18), GOLD, st=False)                                       # whistle pipe
for s in (-1, 1):                                                                      # handrails
    put(box(9.6, 10.4, 24.6, 25.4, -34, 13) & (np.sign(X) == s), STEEL, st=False)

# ---------------------------------------------------------------- cylinders + headlamp
for s in (-1, 1):
    put(cylz(10.5, 3.6, -34, -23, 11 * s), BLUE2)
    put(cylz(10.5, 3.9, -34.6, -33.4, 11 * s) | cylz(10.5, 3.9, -23.6, -22.4, 11 * s), STEEL, st=False)
put(box(0, 3, 32, 36, -38, -34), NAVY, st=False)
put(box(0, 2, 32.6, 35.4, -38.8, -37.8), GLOW[4], k=4, st=False)

# ---------------------------------------------------------------- cab: walls, windows with frames, roof overhang, side panels
cab = box(0, 11.5, 12, 37, 14, 36)
put(cab, BLUE)
put(box(0, 10, 13, 36, 16, 35), DEEP, st=False)                                        # hollow inside
put(box(0, 11.5, 12, 14, 14, 36), NAVY, st=False)                                      # floor band
for (z0, z1) in ((17, 23), (26, 32)):                                                  # side windows
    put(box(10.5, 11.6, 24, 33, z0, z1), TRIM, st=False)
    put(box(10.8, 11.8, 25, 32, z0 + 1, z1 - 1), GLASS * .55, st=False)
    put(box(10.8, 11.8, 28, 29, z0 + 1, z1 - 1), TRIM, st=False)
for xw in (3.5, 8.0):                                                                  # front windows (onto the boiler)
    put(box(xw - 2, xw + 2, 27, 33, 13.5, 15), TRIM, st=False)
    put(box(xw - 1.2, xw + 1.2, 28, 32, 13, 14.5), GLASS * .55, st=False)
put(box(0, 13, 37, 39, 12, 38), NAVY)                                                  # roof
put(box(0, 9, 39, 40, 15, 35), BLUE2)                                                  # roof crown
put(box(12.6, 13.2, 36.2, 37.2, 12, 38), TRIM, st=False)                               # roof drip edge
for s in (-1, 1):                                                                      # cab lamp
    put(box(11.4, 12.6, 30, 33, 34, 36) & (np.sign(X) == s), GLOW[2], k=2, st=False)

# ---------------------------------------------------------------- wheels: 3 big drivers + 2 pony wheels each side, rods, cowcatcher
DRV = (-12, 1, 14)
for zc in DRV:
    put(disc_x(7, zc, 6.6, 9.2, 11.2), DEEP, st=False)                                 # tyre
    put(disc_x(7, zc, 5.6, 9.0, 11.4) & ~disc_x(7, zc, 4.6, 0, 99), STEELD, st=False)  # rim
    put(disc_x(7, zc, 4.6, 9.2, 10.8), NAVY, st=False)                                 # wheel centre
    for a in range(0, 180, 30):                                                        # spokes
        dy, dz = math.sin(math.radians(a)), math.cos(math.radians(a))
        sp = (np.abs((Y - 7) * dz - (Z - zc) * dy) < .6) & disc_x(7, zc, 4.6, 10.6, 11.6)
        put(sp, STEEL, st=False)
    put(disc_x(7, zc, 1.3, 10.6, 12.2), GOLD, st=False)                                # hub
for zc in (-30,):
    put(disc_x(4, zc, 4.0, 8.0, 10.0), DEEP, st=False)
    put(disc_x(4, zc, 3.2, 7.8, 10.2) & ~disc_x(4, zc, 2.2, 0, 99), STEELD, st=False)
put(box(11.8, 13.0, 6.2, 7.8, -12.5, 14.5), STEEL, st=False)                           # coupling rod
put(box(11.8, 12.8, 9.0, 10.4, -30, -2), STEELD, st=False)                             # main rod to the cylinder
put(box(0, 13, 1, 3, 30, 40), NAVY, st=False)                                          # rear drawbar block
# cowcatcher: stepped wedge with black / white diagonal stripes
for k in range(7):
    z0 = -41 - k * 1.5; ytop = 9 - k * 1.2
    put(box(0, 11.5 - k * .6, 0.4, ytop, z0 - 1.5, z0), BLACK, st=False)
cc = (Z < -41) & (Z > -52) & (kind == 1) & (col[..., 0] < .1)
stripe = (np.floor((X + Y * .9 + 50) / 3.0).astype(int) % 2) == 0
put(cc & stripe, WHITE, st=False)

stud[:] = False and kind == 1                                                                     # voxel stud look: every solid brick is studded (glow/glass stay smooth)
stud[(np.abs(col - GLASS * .55).sum(-1) < .05)] = False
# ---------------------------------------------------------------- seams + light grading
solid = kind > 0
dark = np.zeros(n, bool)
for ax in range(3):
    for s in (1, -1):
        np_ = np.roll(pid, s, axis=ax); nl = np.roll(lvl, s, axis=ax)
        dark |= (pid > 0) & (np_ > 0) & (np_ != pid) & (np_ > pid) & (kind == 1) & (np.roll(kind, s, axis=ax) == 1)
col[dark] *= .8
col *= np.clip(.88 + .2 * (Y / 40.0), .85, 1.1)[..., None]
col[kind == 1] *= (.94 + .12 * np.random.RandomState(3).rand(int((kind == 1).sum())))[:, None]   # per-brick tone jitter
col = np.clip(col, 0, 1)

# ---------------------------------------------------------------- mesh (exposed faces + studs on brick tops)
def lin(c): return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
def exposed(mask, ax, s):
    nb = np.roll(solid, -s, axis=ax)
    sl = [slice(None)] * 3; sl[ax] = -1 if s > 0 else 0; nb[tuple(sl)] = False
    return mask & ~nb
BEV = .12
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
                t.append(np.stack([(e[:, u] + du) / 16.0, (e[:, w] + dw) / 16.0], 1))   # Roblox square-stud tile: one stud per 2x2 bricks
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
body = build('Train', kind == 1, True)
m = bpy.data.materials.new('Brick'); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes['Principled BSDF']; at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'
bs.inputs['Roughness'].default_value = .5
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(STUD_PNG); tx.interpolation = 'Linear'
tx.image.colorspace_settings.name = 'Non-Color'                     # overlay: .5 grey = unchanged
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 1
nt.links.new(at.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
body.data.materials.append(m)
GL = []
for k, c in GLOW.items():
    if not (kind == k).any(): continue
    o = build('Glow%d' % k, kind == k, False)
    gm = bpy.data.materials.new('Glow%d' % k); gm.use_nodes = True; b2 = gm.node_tree.nodes['Principled BSDF']
    cl = (*lin(c), 1); b2.inputs['Base Color'].default_value = cl; b2.inputs['Emission Color'].default_value = cl
    b2.inputs['Emission Strength'].default_value = 6.0; gm.diffuse_color = cl
    o.data.materials.append(gm); o.color = cl; GL.append(o)
print('VOX_OK', int((kind > 0).sum()), 'bricks', len(body.data.polygons), 'faces')

def B(x, y, z): return Vector((x, z, y))
def render_all():
    sc = bpy.context.scene
    ENG = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
    for nm, e, rot, an in (('Sun', 2.8, (52, 0, -20), 22), ('FillL', 1.4, (62, 0, -85), 40), ('FillR', 1.6, (62, 0, 85), 40), ('Back', .9, (60, 0, 170), 40)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.angle = math.radians(an); L.rotation_euler = tuple(math.radians(v) for v in rot)
    sh = sc.display.shading; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.color = (.55, .7, .88)
    me = bpy.data.meshes.new('G'); s = 3000
    me.from_pydata([(-s, -s, -3), (s, -s, -3), (s, s, -3), (-s, s, -3)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new('Gnd'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.32, .27, .3, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 5000
    def view(name, tgt, dist, az, el, lens=50):
        t = B(*tgt)
        dv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
        cam.location = t + dv * dist; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        p = os.path.join(REN, '%s_%s.png' % (ID, name))
        sc.render.engine = ENG; sc.render.film_transparent = False; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        sc.render.engine = 'BLENDER_WORKBENCH'; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_shadows = False; sh.show_cavity = False
        g.hide_render = True; sc.render.film_transparent = True; sc.render.filepath = p[:-4] + '_mask.png'; bpy.ops.render.render(write_still=True)
        sc.render.film_transparent = False; keep = tuple(sc.world.color); sc.world.color = (0, 0, 0); sh.background_type = 'WORLD'
        body.color = (0, 0, 0, 1)
        sc.render.filepath = p[:-4] + '_glow.png'; bpy.ops.render.render(write_still=True)
        sc.world.color = keep; g.hide_render = False
    VIEWS = (('ref34', ((0, 18, -5), 150, -32, 12)), ('side', ((0, 18, 0), 170, 90, 6)), ('front', ((0, 18, -10), 120, 0, 6)),
             ('back34', ((0, 18, 0), 160, 145, 18)), ('nose', ((0, 20, -38), 60, -25, 8)), ('wheels', ((10, 8, 2), 70, 90, 4)))
    for nm, a in VIEWS:
        if ONLY and nm not in ONLY: continue
        view(nm, *a)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = [a for a in argv if a != 'render']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, ID + '.blend'))
if 'render' in argv: render_all()
# ---------------------------------------------------------------- rig (always): body on root, every axle its own bone (spins about its length), rods, rune disc
SOL = kind > 0
RIG = [('root', None, (0, -3, 0), (0, 3, 0)), ('body', 'root', (0, 10, 40), (0, 10, -40)),
       ('rune', 'body', (0, 21, -36.5), (0, 21, -41))]
OVR = [(SOL, 'body'), (SOL & (Y < 0.6), 'root'),                        # rails + ties stay on root
       (SOL & ((X ** 2 + (Y - 21) ** 2) < 8.3 ** 2) & (Z < -36.9), 'rune')]
def wheel(zc, yc):                                                     # the exact wheel primitives (not the running board they cut into)
    if yc == 4: return disc_x(4, zc, 4.0, 8.0, 10.0) | disc_x(4, zc, 3.2, 7.8, 10.2)
    m = disc_x(7, zc, 6.6, 9.2, 11.2) | disc_x(7, zc, 5.6, 9.0, 11.4) | disc_x(7, zc, 1.3, 10.6, 12.2)
    for a in range(0, 180, 30):
        dy, dz = math.sin(math.radians(a)), math.cos(math.radians(a))
        m |= (np.abs((Y - 7) * dz - (Z - zc) * dy) < .6) & disc_x(7, zc, 4.6, 10.6, 11.6)
    return m
for i, (zc, yc) in enumerate([(-30, 4)] + [(z, 7) for z in DRV]):
    RIG += [('axle%d' % i, 'body', (-12, yc, zc), (12, yc, zc))]
    OVR += [(SOL & wheel(zc, yc), 'axle%d' % i)]
for s, sd in ((1, 'L'), (-1, 'R')):
    RIG += [('rod' + sd, 'body', (12.5 * s, 7, -12.5), (12.5 * s, 7, 14.5))]
    OVR += [(SOL & box(11.8, 13.0, 6.2, 7.8, -12.5, 14.5) & (np.sign(X) == s), 'rod' + sd)]
brick_rig.export(ID, OUT, lo, kind, col, RIG, OVR, glow=GLOW,
                 pose={'axle1': (0, 60, 0), 'axle2': (0, 60, 0), 'axle3': (0, 60, 0), 'axle0': (0, 60, 0), 'rune': (0, 36, 0)},
                 render='render' in argv)
print('BL_OK')
