"""One command: build a model, score it, line it up with its concept and write a match report.

    python3 scripts/concept_match.py <model.py> <concept.jpg> x0 y0 x1 y1 <out dir> [--trace plates.npz]

x0..y1 is the crop of the concept's SIDE view. Needs Blender's bpy (to build the grid), numpy and Pillow.
Writes into <out dir>:
    report.png     fitted concept | model flat side view | outline overlay, then the front and back flat views
    report.json    scorecard measures + trace measures + the checklist below
    plates.png     (with --trace) the traced plate map; the .npz goes where --trace says
Prints a parity checklist. The thresholds are working marks from the war rhino benchmark (research ch. 92), not
validated limits: a WARN means "look here first", never "fail the build".
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import scorecard as sc

MARKS = (('silhouette overlap (IoU)', 'iou', '>=', .75), ('concept plate line to model, bricks', 'lines_c2m', '<=', 1.0),
         ('relief (share of surface on a real step)', 'relief', '>=', .20), ('edges backed by geometry', 'backed', '>=', .70),
         ('featureless area', 'flat', '<=', .10), ('value bands', 'bands', '>=', 6), ('survives at 48 px', 'small', '>=', .60))


def main():
    a = sys.argv[1:]; trace = None
    if '--trace' in a: i = a.index('--trace'); trace = os.path.abspath(a[i + 1]); del a[i:i + 2]
    model, concept, box, out = os.path.abspath(a[0]), os.path.abspath(a[1]), a[2:6], os.path.abspath(a[6])
    os.makedirs(out, exist_ok=True); key = 'file_' + os.path.splitext(os.path.basename(model))[0]
    if not sc.dump_file(model, key): sys.exit(1)
    s = sc.score(key, concept, save_views=os.path.join(sc.CACHE, 'views'))
    cmd = [sys.executable, os.path.join(HERE, 'trace_match.py'), key, concept, *box, os.path.join(out, 'trace')] + ([trace] if trace else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if 'TRACE_OK' not in r.stdout: print(r.stdout[-400:], r.stderr[-400:]); sys.exit(1)
    t = json.load(open(os.path.join(out, 'trace.json')))
    from PIL import Image
    top = Image.open(os.path.join(out, 'trace_side_by_side.png')).convert('RGB')
    fb = [Image.open(os.path.join(sc.CACHE, 'views', '%s_%s.png' % (key, v))).convert('RGB') for v in ('front', 'back')]
    h = max(i.height for i in fb); rep = Image.new('RGB', (max(top.width, sum(i.width for i in fb) + 20), top.height + h + 10), (24, 26, 32))
    rep.paste(top, (0, 0)); x = 0
    for i in fb: rep.paste(i, (x, top.height + 10)); x += i.width + 20
    rep.save(os.path.join(out, 'report.png'))
    if trace and os.path.exists(os.path.join(out, 'trace_plates.png')): os.replace(os.path.join(out, 'trace_plates.png'), os.path.join(out, 'plates.png'))
    vals = dict(s, **{k: t[k] for k in ('iou', 'outline_c2m', 'outline_m2c', 'lines_c2m', 'lines_m2c')})
    check = []
    for name, k, op, mark in MARKS:
        v = vals[k]; ok = v >= mark if op == '>=' else v <= mark
        check.append(dict(name=name, value=round(float(v), 3), mark='%s %s' % (op, mark), ok=bool(ok)))
        print('%-4s %-44s %7.2f   (%s %s)' % ('ok' if ok else 'WARN', name, v, op, mark))
    for rule in s['rules']: print('FAIL rule:', rule)
    print('     largest piece %s triangles (limit 20,000), %d colours (limit 16)' % (s.get('max_tris'), s['colours']))
    json.dump(dict(model=os.path.basename(model), scorecard={k: v for k, v in s.items()}, trace=t, checklist=check), open(os.path.join(out, 'report.json'), 'w'), indent=1)
    print('MATCH_OK', os.path.join(out, 'report.png'))


if __name__ == '__main__':
    main()
