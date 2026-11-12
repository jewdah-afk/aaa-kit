#!/usr/bin/env python3
"""Propose bounded variant parameterizations from *measured* approved candidate results.
This does not auto-edit code, auto-approve visuals or alter shipped presets.
"""
import argparse, json, pathlib, random, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('report',help='evolve.py report JSON with measured winners');p.add_argument('--per-parent',type=int,default=8);p.add_argument('--seed',type=int,default=111126);p.add_argument('--out',default=str(ROOT/'qa/next_generation.jsonl'));args=p.parse_args()
assert 1<=args.per_parent<=40
report=json.loads(pathlib.Path(args.report).read_text());winners=[r for r in report.get('winners',[]) if r.get('passes')]
if not winners:raise SystemExit('No passing measured candidates. Run measured QA first. No mutations created.')
# Bounded, legible parameters. Art direction and protected region are NON-MUTABLE constraints.
params={'compliance':(.02,.30),'damping':(.2,.98),'caustic_gain':(.05,.6),'rim_energy':(.03,.32),'lip_depth':(3,15),'afterglow_ms':(80,200),'mesh_update_hz':(15,60),'field_update_hz':(15,60)}
def clamp(k,v):
 a,b=params[k];return max(a,min(b,int(round(v)) if k in ('lip_depth','afterglow_ms','mesh_update_hz','field_update_hz') else round(v,4)))
def init():return {'compliance':.11,'damping':.67,'caustic_gain':.24,'rim_energy':.13,'lip_depth':9,'afterglow_ms':145,'mesh_update_hz':30,'field_update_hz':30}
rng=random.Random(args.seed);offspring=[]
for parent in winners[:12]:
 for n in range(args.per_parent):
  cfg=init();changes=rng.sample(list(cfg),2)
  for k in changes:
   lo,hi=params[k];cfg[k]=clamp(k,cfg[k]+(rng.random()*2-1)*(hi-lo)*.18)
  if cfg['afterglow_ms']>200:cfg['afterglow_ms']=200
  raw=parent['id']+'|'+json.dumps(cfg,sort_keys=True)
  offspring.append({'id':'V-'+hashlib.blake2s(raw.encode(),digest_size=7).hexdigest(),'parent_id':parent['id'],'params':cfg,'mutated_keys':changes,'status':'NOT_RENDERED_NOT_APPROVED','source_measurement_score':parent['score'],'immutable_style_contract':{'squared_outline':True,'text_protected':True,'icon_protected':True,'whole_key_press':True,'calm_idle':True},'required_gates':['harness','hierarchy','APCA','flash','CVD','reduced-motion','Studio-ms','human-approval']})
out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w') as f:
 for row in offspring:f.write(json.dumps(row)+'\n')
print(f'{len(offspring)} proposals saved to {out}; ALL untested and unapproved')
