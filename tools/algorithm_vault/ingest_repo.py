#!/usr/bin/env python3
"""Index *actual files* from a checked-out aaa-kit source tree.
Does not copy code/docs; records path and line, names/headers only. No invented content.
Usage: python tools/algorithm_vault/ingest_repo.py /path/to/aaa-kit
"""
import pathlib,re,json,sys,hashlib
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
out=pathlib.Path(__file__).resolve().parents[2]/'docs/algorithm-vault/repo_discovery.jsonl'
entries=[]
def add(kind,path,line,title):
 if not title or len(title)>180:return
 rel=path.relative_to(root).as_posix()
 eid='R-'+hashlib.blake2s(f'{rel}:{line}:{title}'.encode(),digest_size=6).hexdigest()
 entries.append({'id':eid,'kind':kind,'repo_path':rel,'line':line,'title':title,'provenance':'local-source-code-or-document','verification':'path indexed, not performance tested'})
for path in root.rglob('*'):
 if not path.is_file() or any(x in path.parts for x in ('.git','node_modules','__pycache__','vendor','dist')):continue
 if path.suffix=='.luau':
  add('luau-module',path,1,path.stem)
  text=path.read_text(encoding='utf-8',errors='ignore')
  for i,line in enumerate(text.splitlines(),1):
   if i>1500:break
   m=re.match(r'\s*(?:function\s+\w+[.:]|local\s+function\s+)([\w_]+)',line)
   if m:add('luau-function',path,i,m.group(1))
 elif path.suffix=='.md' and ('research' in path.parts or 'ideas' in path.parts or path.name in ['LEXICON.md','HIERARCHY.md']):
  text=path.read_text(encoding='utf-8',errors='ignore')
  for i,line in enumerate(text.splitlines(),1):
   if len(entries)>80000:break
   m=re.match(r'^#{1,4}\s+(.+)$',line)
   if m:add('research-heading',path,i,m.group(1).strip())
   m=re.match(r'^\s*\d+\.\s+\*\*(.+?)\*\*\s*:',line)
   if m:add('algorithm-idea',path,i,m.group(1).strip())
 elif path.name=='lexicon.json':
  try:
   data=json.loads(path.read_text())
   def walk(v):
    if isinstance(v,dict):
     for k,x in v.items():
      if k in ('term','name','label') and isinstance(x,str):add('lexicon-term',path,0,x)
      walk(x)
    elif isinstance(v,list):
     for x in v:walk(x)
   walk(data)
  except Exception as e: print('lexicon parse failed:',e,file=sys.stderr)
seen=set();unique=[]
for x in entries:
 if x['id'] not in seen:seen.add(x['id']);unique.append(x)
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w') as f:
 for x in unique:f.write(json.dumps(x,ensure_ascii=False)+'\n')
print(json.dumps({'repo':str(root),'records':len(unique),'path':str(out)}))
