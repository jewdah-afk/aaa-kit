"""Celestialrithm integration smoke checks. Run from anywhere: python tools/celestialrithm/verify_integration.py"""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
TESTS=[
 'tools/algorithm_vault/test_vault.py',
 'tools/celestialrithm/test_ui_catalog.py',
 'tools/celestialrithm/test_world.py',
 'examples/celestialrithm/test_system.py',
]
results=[]
for name in TESTS:
    path=ROOT/name
    proc=subprocess.run([sys.executable,str(path)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    results.append({'test':name,'passed':proc.returncode==0,'output_tail':proc.stdout[-1200:]})
for name in ('approved-material-visual-target.gif','engineering-v1-preview.gif'):
    path=ROOT/'media/celestialrithm'/name
    results.append({'test':'media/'+name,'passed':path.exists() and path.stat().st_size>0,'bytes':path.stat().st_size if path.exists() else 0})
output={'status':'PASS' if all(x['passed'] for x in results) else 'FAIL','checks':results,'scope':'local integration smoke check; not Lune, Selene, Studio, or device FPS'}
(ROOT/'tools/celestialrithm/INTEGRATION_QA.json').write_text(json.dumps(output,indent=2)+'\n')
print(output['status'],sum(x['passed'] for x in results),'/',len(results))
for r in results: print('PASS' if r['passed'] else 'FAIL',r['test'])
sys.exit(0 if output['status']=='PASS' else 1)
