"""Tests for meshgen + texbake. python3 test_meshvfx.py"""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import meshgen, texbake

def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name); return cond

ok = True
for nm, m in [('crescent', meshgen.crescent()), ('shell', meshgen.shell(meshgen.crescent())), ('vortex', meshgen.vortex()), ('debris', meshgen.debris(3))]:
    U = np.array(m.uv)
    ok &= check(f'{nm} tris in 60..1500 ({m.tris()})', 60 <= m.tris() <= 1500)
    ok &= check(f'{nm} uv inset', U.min() >= 0.029 and U.max() <= 0.971)
    ok &= check(f'{nm} faces valid', all(max(f) < len(m.v) for f in m.f))
sw = meshgen.shockwave(); ok &= check('shockwave v inset', np.array(sw.uv)[:, 1].min() >= 0.029)
c = meshgen.crescent(); V = np.array(c.v)
ok &= check('crescent tapers to points', np.linalg.norm(V[0] - V[c.v.index(c.v[4])]) < 0.1)
for kind in ('flame', 'streaks'):
    a = getattr(texbake, kind)(128).astype(float)
    inner = abs(np.diff(a, axis=1)).mean() + abs(np.diff(a, axis=0)).mean()
    seam = abs(a[:, 0] - a[:, -1]).mean() + abs(a[0] - a[-1]).mean()
    ok &= check(f'{kind} tiles (seam {seam:.1f} <= 1.5x interior {inner:.1f})', seam <= 1.5 * inner + 1)
    ok &= check(f'{kind} has contrast', a.std() > 40)
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, 'x.obj'); s = c.write_obj(p, 'x'); ok &= check('obj written', os.path.getsize(p) > 1000 and s['tris'] == c.tris())
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
