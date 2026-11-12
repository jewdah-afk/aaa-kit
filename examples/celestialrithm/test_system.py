import json,sys,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from render_lab import PALETTES,field,render,patch
class Test(unittest.TestCase):
 def test_palette_count(self):self.assertGreaterEqual(len(PALETTES),8)
 def test_color_channels(self):
  for p in PALETTES.values():
   for k in ('base','light','shadow'):self.assertRegex(p[k],r'^#[0-9a-fA-F]{6}$')
 def test_fields_finite(self):
  import numpy as np
  for p in PALETTES: self.assertTrue(np.isfinite(field(p,1.2)).all())
 def test_motion(self):
  for k,p in PALETTES.items():self.assertNotEqual(patch(p,k,0).tobytes(),patch(p,k,0.4).tobytes())
 def test_frame(self):self.assertEqual(render(0).size,(960,540))
 def test_determinism(self):self.assertEqual(render(0).tobytes(),render(0).tobytes())
 def test_static_title(self):
  import numpy as np
  a=np.array(render(0));b=np.array(render(.4));self.assertTrue(np.array_equal(a[0:50,0:340],b[0:50,0:340]))
 def test_changed_material(self):
  import numpy as np
  a=np.array(render(0));b=np.array(render(.4));self.assertGreater(np.abs(a[130:200,38:310].astype('i2')-b[130:200,38:310].astype('i2')).sum(),10000)
if __name__=='__main__':unittest.main()
