import unittest
from build_ui_catalog import recipes,BUDGETS,GENRES,COMPONENTS,MATERIALS,DEVICES
class TestCatalog(unittest.TestCase):
 def test_count_unique(self):
  r=list(recipes());self.assertEqual(len(r),len(GENRES)*len(COMPONENTS)*len(MATERIALS)*len(DEVICES));self.assertEqual(len(set(x['id'] for x in r)),len(r))
 def test_cost_rungs(self):
  self.assertLess(BUDGETS['low-mobile']['fx_ms'],BUDGETS['mid-mobile']['fx_ms']);self.assertLess(BUDGETS['mid-mobile']['fx_ms'],BUDGETS['desktop']['fx_ms'])
 def test_always_protect_icon(self):self.assertTrue(all('protect_text_and_icon' in x['visual_contract'] for x in recipes()))
 def test_every_entry_unimplemented(self):self.assertTrue(all(x['status']=='generated_candidate_not_implemented' for x in recipes()))
 def test_no_magnetic_cursor(self):self.assertTrue(all('no_cursor_magnetism' in x['visual_contract'] for x in recipes()))
if __name__=='__main__':unittest.main()
