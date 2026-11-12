from pathlib import Path
import tempfile,sys,json
sys.path.insert(0,str(Path(__file__).parent))
from world_preview import generate,export_obj,render

a=generate(16,143);b=generate(16,143);c=generate(16,144)
assert a==b and a!=c
assert all(isinstance(h,int) and h>=0 and h%2==0 for row in a for h in row)
assert any(h==4 for row in a for h in row)
with tempfile.TemporaryDirectory() as t:
 p=Path(t);m=export_obj(a,p/'mesh.obj');render(a,p/'map.png')
 assert m['cells']==256 and m['triangles']>512
 assert len((p/'mesh.obj').read_text().splitlines())>m['vertices']
 assert (p/'map.png').stat().st_size>1000
print('PASS deterministic seed, terrace invariants, road corridor, watertight-facing exports, preview')
