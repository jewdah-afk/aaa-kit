import json,sqlite3, pathlib,subprocess,sys,tempfile,csv
ROOT=pathlib.Path(__file__).resolve().parents[2];base=ROOT/'docs/algorithm-vault'
checks={}
m=json.loads((base/'manifest.json').read_text());checks['primitive_count']=m['primitives']==156;checks['recipe_count']=m['generated_recipes']==12000
p=json.loads((base/'primitives.json').read_text());checks['unique_method_ids']=len({x['id'] for x in p})==len(p)
sources=json.loads((base/'sources.json').read_text()); checks['source_links']=all(x['url'] for x in sources)
r=[json.loads(x) for x in (base/'recipes.jsonl').read_text().splitlines()];checks['unique_recipes']=len({x['id'] for x in r})==len(r)
checks['all_restricted']=all(x['production_status']=='UNTESTED_RECIPE' and x['measured_ms'] is None for x in r)
checks['has_hierarchy']=all(x['hierarchy'] for x in r)
checks['style_contract']=all('flat squared face' in x['style_contract'] for x in r)
db=sqlite3.connect(base/'vault.sqlite');checks['sqlite_recipes']=db.execute('select count(*) from recipes').fetchone()[0]==12000;checks['sqlite_primitive']=db.execute('select count(*) from primitives').fetchone()[0]==156;db.close()
q=subprocess.run([sys.executable,str(ROOT/'tools/algorithm_vault/query.py'),'caustic','--limit','2'],capture_output=True,text=True);checks['cli_query']=q.returncode==0 and 'id' in q.stdout
with tempfile.TemporaryDirectory() as d:
 tmp=pathlib.Path(d);(tmp/'docs/research/ideas').mkdir(parents=True);(tmp/'lib/frontier').mkdir(parents=True)
 (tmp/'docs/research/ideas/TEST.md').write_text('## Real Method\n1. **New tessellation**: example\n')
 (tmp/'lib/frontier/Sample.luau').write_text('local function ping()\nend\n')
 v=subprocess.run([sys.executable,str(ROOT/'tools/algorithm_vault/ingest_repo.py'),str(tmp)],capture_output=True,text=True)
 records=[json.loads(x) for x in (base/'repo_discovery.jsonl').read_text().splitlines()]
 checks['ingest_fixture']=v.returncode==0 and len(records)==4
 with (tmp/'eval.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['id','focus_lift','contrast_lc','frame_ms','flash_pass','human_rating','style_pass']);w.writerow([r[0]['id'],2.0,80,1.2,'pass',4,'pass']);w.writerow([r[1]['id'],.9,20,6,'fail',1,'fail'])
 evo=subprocess.run([sys.executable,str(ROOT/'tools/algorithm_vault/evolve.py'),str(tmp/'eval.csv'),'--out',str(tmp/'report.json')],capture_output=True,text=True)
 report=json.loads((tmp/'report.json').read_text());checks['evolution_rejects_failures']=evo.returncode==0 and report['passed']==1 and report['rejected']==1
 mutation=subprocess.run([sys.executable,str(ROOT/'tools/algorithm_vault/mutate.py'),str(tmp/'report.json'),'--out',str(tmp/'mutations.jsonl')],capture_output=True,text=True)
 descendants=[json.loads(x) for x in (tmp/'mutations.jsonl').read_text().splitlines()]
 checks['mutation_approval_gated']=mutation.returncode==0 and len(descendants)==8 and all(x['status']=='NOT_RENDERED_NOT_APPROVED' and x['immutable_style_contract']['whole_key_press'] for x in descendants)
# Remove fixture-specific discovery file so user won't mistake tests for actual repo index
(base/'repo_discovery.jsonl').unlink(missing_ok=True)
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
assert all(checks.values()),checks
print(f'{len(checks)}/{len(checks)} passed')
