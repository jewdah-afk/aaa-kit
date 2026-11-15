"""Audit every shipped brick creature against the skill's own rules, without rendering.
    python3 scripts/audit.py [name ...]        (needs Blender's bpy; `lune` on PATH adds the Parts count)
Runs each examples/brick/*_brick.py creature in a temp copy with the rig export intercepted, then reports per model:
bricks, solid colours (rule: 16 or fewer), glow kinds, glow share, bones, floating bricks, and how many Parts the
BrickBoxes route would need. Writes examples/AUDIT.md. Changes nothing in the skill folder except that file.
"""
import os, sys, json, shutil, subprocess, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {'props', 'terrain', 'shop', 'tower', 'gate', 'arcane_train'}        # bld.Grid models: covered by regress.sh
INNER = r'''
import sys, json, runpy, numpy as np
f, outdir = sys.argv[1], sys.argv[2]; sys.argv = [f]
sys.path.insert(0, sys.argv[0].rsplit('/', 3)[0] + '/scripts'); import brick_rig
def fake(ID, OUT, lo, kind, col, RIG, overrides=(), glow=None, **kw):
    n = kind.shape; lo = np.asarray(lo, float)
    c = [lo[k] + .5 + np.arange(n[k]) for k in range(3)]
    X, Y, Z = np.meshgrid(*c, indexing='ij'); solid = kind > 0
    lab = brick_rig.assign(X, Y, Z, solid, RIG, overrides)
    rgb = np.round(np.clip(col, 0, 1) * 255).astype(np.int64)
    code = np.where(kind == 1, (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2], -kind.astype(np.int64))   # glow kind = one colour
    u, cid = np.unique(code[solid], return_inverse=True)
    g = np.zeros(n, np.uint8); g[solid] = cid + 1
    b = np.zeros(n, np.uint8); b[solid] = lab[solid] + 1
    open(outdir + '/grid.bin', 'wb').write(np.ascontiguousarray(g.transpose(1, 2, 0)).tobytes() + np.ascontiguousarray(b.transpose(1, 2, 0)).tobytes())
    ix = np.argwhere(solid); ext = ix.max(0) - ix.min(0) + 1
    json.dump(dict(id=ID, n=[int(v) for v in n], bones=len(RIG), bricks=int(solid.sum()), solid_colours=int((u >= 0).sum()),
                   glow_kinds=int((u < 0).sum()), glow_share=float((kind > 1).sum() / solid.sum()),
                   studs=[round(float(v) * 2.5) for v in ext]), open(outdir + '/grid.json', 'w'))
brick_rig.export = fake
runpy.run_path(f, run_name='__main__')
'''
LUNE = r'''
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local process = require("@lune/process")
local B = require("./BrickBoxes")
local dir = process.args[1]
local j = serde.decode("json", fs.readFile(dir .. "/grid.json"))
local nx, ny, nz = j.n[1], j.n[2], j.n[3]
local g = B.new(nx, ny, nz)
local raw = buffer.fromstring(fs.readFile(dir .. "/grid.bin"))
buffer.copy(g.colour, 0, raw, 0, nx * ny * nz)
buffer.copy(g.bone, 0, raw, nx * ny * nz, nx * ny * nz)
local l = g:lint(true)
print(serde.encode("json", { boxes = #g:boxes(), floating = l.floating, exposed = l.exposed }))
'''


def main():
    want = sys.argv[1:]
    tmp = tempfile.mkdtemp(); sk = os.path.join(tmp, 'sk'); shutil.copytree(SKILL, sk)
    bd = os.path.join(sk, 'examples', 'brick'); rb = os.path.join(sk, 'references', 'roblox')
    open(os.path.join(tmp, 'inner.py'), 'w').write(INNER); open(os.path.join(rb, '_audit.luau'), 'w').write(LUNE)
    lune = shutil.which('lune'); rows = []
    for f in sorted(os.listdir(bd)):
        name = f[:-len('_brick.py')]
        if not f.endswith('_brick.py') or name in SKIP or (want and name not in want): continue
        od = os.path.join(tmp, name); os.makedirs(od)
        subprocess.run([sys.executable, os.path.join(tmp, 'inner.py'), os.path.join(bd, f), od], cwd=bd, capture_output=True)
        if not os.path.exists(od + '/grid.json'): rows.append((name, None)); print(name, 'FAILED'); continue
        j = json.load(open(od + '/grid.json'))
        if lune:
            r = subprocess.run([lune, 'run', '_audit.luau', od], cwd=rb, capture_output=True, text=True)
            try: j.update(json.loads(r.stdout.strip().splitlines()[-1]))
            except Exception: pass
        rows.append((name, j)); print(name, j)
    md = ['# Audit of the shipped brick creatures', '',
          'Written by `scripts/audit.py`. No rendering: each model is run with the rig export intercepted.',
          'Rules checked: 16 solid colours or fewer, glow share at or under 4 % unless the model is `# GLOW: strong`, no floating bricks.',
          'Parts = boxes the BrickBoxes route would need (boxes never cross a bone or a colour).', '',
          '| Model | Size (studs, x y z) | Bricks | Bones | Solid colours | Glow kinds | Glow share | Floating | Parts | Rules |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for name, j in rows:
        if not j: md.append('| %s | build failed | | | | | | | | FAIL |' % name); continue
        strong = '# GLOW: strong' in open(os.path.join(bd, name + '_brick.py'), encoding='utf8').read()
        bad = []
        if j['solid_colours'] > 16: bad.append('colours')
        if j['glow_share'] > .04 and not strong: bad.append('glow')
        if j.get('floating', 0): bad.append('floating')
        md.append('| %s | %s | %s | %d | %d | %d | %.1f %% | %s | %s | %s |' % (
            name, ' x '.join(str(v) for v in j['studs']), format(j['bricks'], ','), j['bones'], j['solid_colours'], j['glow_kinds'],
            j['glow_share'] * 100, j.get('floating', 'n/a'), format(j['boxes'], ',') if 'boxes' in j else 'n/a', 'ok' if not bad else 'FAIL: ' + ', '.join(bad)))
    if not want: open(os.path.join(SKILL, 'examples', 'AUDIT.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md)); shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
