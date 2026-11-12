#!/usr/bin/env python3
"""Deterministic squared stud-world generator + OBJ exporter for visual QA.
No claim that this replaces the real Roblox map or runs in Studio.
"""
import argparse, math, json
from pathlib import Path
from PIL import Image, ImageDraw

def rnd(x,z,s):
    v=math.sin(x*127.1+z*311.7+s*74.7)*43758.5453
    return v-math.floor(v)

def height(x,z,seed,road_width=5):
    v=math.sin(x*.075+seed*.31)*.5+math.cos(z*.071-seed*.19)*.34+(rnd(math.floor(x/8),math.floor(z/8),seed)-.5)*.19
    h=math.floor((8+v*7)/2)*2
    return 4 if abs(x)<road_width else h

def generate(side=32,seed=143,tile=4):
    return [[height((x-side//2)*tile,(z-side//2)*tile,seed) for x in range(side)] for z in range(side)]

def export_obj(data,dest,tile=4):
    # Geometry is explicit voxel columns. Internal side faces are culled at shared edges.
    n=len(data);vertices=[];faces=[];colors=[]
    def face(pts):
        i=len(vertices)+1;vertices.extend(pts);faces.extend([(i,i+1,i+2),(i,i+2,i+3)])
    for z in range(n):
        for x in range(n):
            h=data[z][x];X=(x-n/2)*tile;Z=(z-n/2)*tile
            face([(X,h,Z),(X+tile,h,Z),(X+tile,h,Z+tile),(X,h,Z+tile)])
            for dx,dz,pts in [(1,0,[(X+tile,0,Z),(X+tile,0,Z+tile),(X+tile,h,Z+tile),(X+tile,h,Z)]),(-1,0,[(X,0,Z+tile),(X,0,Z),(X,h,Z),(X,h,Z+tile)]),(0,1,[(X+tile,0,Z+tile),(X,0,Z+tile),(X,h,Z+tile),(X+tile,h,Z+tile)]),(0,-1,[(X,0,Z),(X+tile,0,Z),(X+tile,h,Z),(X,h,Z)])]:
                ix,iz=x+dx,z+dz;neighbor=data[iz][ix] if 0<=ix<n and 0<=iz<n else 0
                if neighbor<h:
                    pts=[(a,neighbor if y==0 else y,b) for a,y,b in pts]
                    face(pts)
    with open(dest,'w') as f:
        f.write('# Celestialrithm studded terrain preview; derived from deterministic heightfield\n')
        for a,b,c in vertices:f.write(f'v {a:.4f} {b:.4f} {c:.4f}\n')
        for a,b,c in faces:f.write(f'f {a} {b} {c}\n')
    return {'vertices':len(vertices),'triangles':len(faces),'cells':n*n}

def render(data,dest):
    n=len(data);scale=14
    im=Image.new('RGB',(n*scale,n*scale),(15,23,45)); d=ImageDraw.Draw(im)
    palette={4:('#acdfe9','#7db9cd'),6:('#a4d1df','#7fb1c4'),8:('#80bacb','#589db1'),10:('#b8e5ef','#8ac8d9'),12:('#d9f2f5','#a4d2dd'),14:('#e6f9fa','#b4e1e8')}
    for z,row in enumerate(data):
        for x,h in enumerate(row):
            c=palette.get(h,('#eefbff','#bddfeb'))[0]
            d.rectangle((x*scale,z*scale,(x+1)*scale-2,(z+1)*scale-2),fill=c)
            d.line((x*scale,z*scale,(x+1)*scale-2,z*scale),fill='#ffffff',width=2)
            # tiny square stud motif, deterministic and stylized
            d.rectangle((x*scale+5,z*scale+5,x*scale+8,z*scale+8),fill='#ffffff')
    im.save(dest)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=143);ap.add_argument('--side',type=int,default=32);ap.add_argument('--out',default='.')
    a=ap.parse_args();o=Path(a.out);o.mkdir(parents=True,exist_ok=True)
    data=generate(a.side,a.seed);metrics=export_obj(data,o/'stud_chunk.obj');render(data,o/'stud_chunk.png')
    (o/'stud_chunk.json').write_text(json.dumps({'seed':a.seed,**metrics,'source':'generated extension; existing map unchanged'},indent=2))
    print(metrics)
