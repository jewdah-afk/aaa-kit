#!/usr/bin/env python3
"""Human-in-the-loop ranking from measured experiments, not autonomous aesthetic claims.
Input evaluation CSV: id,focus_lift,contrast_lc,frame_ms,flash_pass,human_rating,style_pass
Rows with missing measurements are not eligible. Produces ranked recommendations and rejected reasons.
"""
import argparse,csv,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]; BASE=ROOT/'docs/algorithm-vault'
p=argparse.ArgumentParser();p.add_argument('measurements');p.add_argument('--out',default=str(ROOT/'qa/evolution_report.json'));p.add_argument('--max-ms',type=float,default=2.0);args=p.parse_args()
recipes={x['id']:x for line in (BASE/'recipes.jsonl').open() if (x:=json.loads(line))};records=[]
with open(args.measurements,newline='') as f:
 for r in csv.DictReader(f):
  if r.get('id') not in recipes:continue
  try:
   lift=float(r['focus_lift']); lc=float(r['contrast_lc']); ms=float(r['frame_ms']);rating=float(r['human_rating'])
  except (ValueError,KeyError):continue
  reasons=[]
  if r.get('flash_pass','').strip().lower() not in ('1','true','yes','pass'):reasons.append('flash safety')
  if r.get('style_pass','').strip().lower() not in ('1','true','yes','pass'):reasons.append('style drift')
  if lift<1.5:reasons.append('focus lift')
  if lc<60:reasons.append('label APCA')
  if ms>args.max_ms:reasons.append('runtime budget')
  if rating<3:reasons.append('human quality')
  score=round(min(3,lift)*30+min(100,lc)*.25+rating*10-max(0,ms)*12,2)
  records.append({'id':r['id'],'score':score,'passes':not reasons,'failures':reasons,'recipe':recipes[r['id']]['description'],'frame_ms':ms})
records.sort(key=lambda x:(x['passes'],x['score']),reverse=True)
out={'measured_candidates':len(records),'passed':sum(x['passes'] for x in records),'rejected':sum(not x['passes'] for x in records),'winners':records[:25],'note':'Only user-supplied measured records are scored; no generated recipe is pre-approved.'}
pathlib.Path(args.out).parent.mkdir(parents=True,exist_ok=True);pathlib.Path(args.out).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('winners',)},indent=2));print('Top IDs:',[x['id'] for x in records[:5]])
