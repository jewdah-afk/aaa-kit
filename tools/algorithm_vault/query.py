#!/usr/bin/env python3
"""Find recipes / methods, print direct paths and fields. Stdlib only."""
import argparse,sqlite3,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]; DB=ROOT/'docs/algorithm-vault/vault.sqlite'
p=argparse.ArgumentParser();p.add_argument('term',nargs='?',default='');p.add_argument('--style');p.add_argument('--target');p.add_argument('--limit',type=int,default=12);p.add_argument('--method',action='store_true');args=p.parse_args()
c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
if args.method:
 rows=c.execute('SELECT * FROM primitives WHERE name LIKE ? OR id LIKE ? LIMIT ?',('%'+args.term+'%','%'+args.term+'%',args.limit)).fetchall()
else:
 where=['1=1'];params=[]
 if args.term:where.append('id IN (SELECT id FROM recipes_fts WHERE description MATCH ?)');params.append('"'+args.term.replace('"','')+'"')
 if args.style:where.append('style=?');params.append(args.style)
 if args.target:where.append('target=?');params.append(args.target)
 rows=c.execute('SELECT * FROM recipes WHERE '+' AND '.join(where)+' ORDER BY heuristic_ms ASC LIMIT ?',(*params,args.limit)).fetchall()
for row in rows:print(json.dumps(dict(row)))
