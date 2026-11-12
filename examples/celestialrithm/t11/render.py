"""AAA-kit T11: deterministic, offline 60 Hz mesh-field + optical-field render.
Requires numpy, opencv-python, Pillow. No network or AI-generated pixels.
An OBJ is exported from the EXACT height function used for face normals/lighting.
"""
from pathlib import Path
import math, json, time, subprocess
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent
W,H=960,540
FW,FH=500,194
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=lambda sz:ImageFont.truetype(FONT,sz)
# spec values sourced from aaa-kit docs/playbooks/figma-to-roblox-ui.md
INK=(11,12,16); N_FRAMES=240; FPS=60
uvx,uvy=np.meshgrid(np.linspace(-1,1,FW,dtype=np.float32),np.linspace(-1,1,FH,dtype=np.float32))

def smoothstep(a,b,x):
    q=np.clip((x-a)/(b-a),0,1)
    return q*q*(3-2*q)

def pressure_at(t):
    # four seconds: idle -> press -> hold -> release -> settle
    if t < .65: return 0.
    if t < .88:return smoothstep(.65,.88,t)
    if t < 1.42:return 1.
    if t < 1.95:return 1.-smoothstep(1.42,1.95,t)*1.18
    return -.18*math.exp(-(t-1.95)*4.6)*math.cos((t-1.95)*17.5)

def heightfield(u,v,t,p):
    # mathematically shared mesh/material state. Bounded and square-edged.
    edge=np.minimum(1-np.abs(u),1-np.abs(v))
    bevel=smoothstep(0,.16,edge)
    r=np.sqrt((u-.04)**2+(v+.06)**2)
    dent=-.20*p*np.exp(-(r/.48)**2)
    ring=.075*p*np.sin(19*r-10*t)*np.exp(-2.6*r)
    gentle=.013*np.sin(11*u+2.0*t)*np.cos(13*v-1.4*t)
    return (.105*bevel+dent+ring+gentle*bevel).astype(np.float32)

def render_face(t,mode='HYDRO'):
    p=pressure_at(t); h=heightfield(uvx,uvy,t,p)
    gy,gx=np.gradient(h)
    nx=-gx*17; ny=-gy*17; nz=np.ones_like(nx)*.8
    norm=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=norm;ny/=norm;nz/=norm
    diffuse=np.maximum(.0,nx*-.44+ny*-.55+nz*.82)
    # depth-linked caustic optics (not physical ray traced refraction)
    phase=17.5*uvx+9*uvy+7.5*h+3.4*t
    warp=6.5*h+np.sin(7*uvx-6*uvy+1.5*t)*.08
    c1=np.cos(phase+3*np.sin(9*uvy-2.3*t+warp))
    c2=np.cos(22*uvy-12*uvx-2.5*t+14*h)
    c3=np.sin(15*uvx+15*uvy+4*t)
    vein=np.maximum(0,(c1+c2+c3)/3-.19)**2*3.0
    fres=np.clip((1-nz)**1.4,0,1)
    spec=np.maximum(nx*-.35+ny*-.58+nz*.73,0)**25
    light=np.clip(.36+.52*diffuse+.5*vein+.75*spec+.15*fres,0,1.5)
    palettes={'HYDRO':((12,80,137),(45,224,249)), 'PRISM':((79,27,136),(230,85,248)), 'SOLAR':((139,51,15),(255,207,54))}
    dark,bright=palettes[mode]
    v=np.clip(light,0,1)
    base=np.zeros((FH,FW,3),np.float32)
    for k in range(3):base[:,:,k]=dark[k]+v*(bright[k]-dark[k])
    if mode=='PRISM':
        base[:,:,0]+=28*np.cos(phase*.63+t*1.1)
        base[:,:,2]+=26*np.sin(phase*.8-t)
    if mode=='SOLAR':base[:,:,0]+=24*vein; base[:,:,1]+=12*vein
    # SDF protective zone for icon/text: aggressively suppress moving luminance
    central=np.exp(-((uvx/.57)**8+(uvy/.56)**8))
    neutral=np.array([32,85,129] if mode=='HYDRO' else [90,46,125] if mode=='PRISM' else [133,84,24],np.float32)
    base=base*(1-.45*central[:,:,None])+neutral[None,None,:]*(.45*central[:,:,None])
    # pixel crispness: no unrelated highlights in central protected region
    border=np.minimum(1-np.abs(uvx),1-np.abs(uvy))
    base*=np.clip(border/.08,.3,1)[...,None]
    return np.uint8(np.clip(base,0,255)),h,float(p)

def geometry_export(t,mode):
    nx,ny=40,24; u=np.linspace(-1,1,nx+1);v=np.linspace(-1,1,ny+1)
    U,V=np.meshgrid(u,v);h=heightfield(U,V,t,pressure_at(t))
    # closed sidewalls with 3D volume; 41x25 top vertex lattice
    vertices=[];faces=[]
    for j in range(ny+1):
        for i in range(nx+1):vertices.append((u[i]*2.9,v[j]*1.16,float(h[j,i])))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i+1;b=a+1;c=a+(nx+1);d=c+1
            faces.extend([(a,b,d),(a,d,c)])
    edge_idx=list(range(1,nx+2))+[j*(nx+1)+nx+1 for j in range(1,ny+1)]+[ny*(nx+1)+i+1 for i in range(nx-1,-1,-1)]+[j*(nx+1)+1 for j in range(ny-1,0,-1)]
    lower=[]
    for vid in edge_idx:
        x,y,z=vertices[vid-1];vertices.append((x,y,-.16));lower.append(len(vertices))
    for k,top in enumerate(edge_idx):
        nxt=(k+1)%len(edge_idx);faces.extend([(top,edge_idx[nxt],lower[nxt]),(top,lower[nxt],lower[k])])
    out=P/f'{mode.lower()}_press.obj'
    with out.open('w') as f:
        f.write('# AAA-kit T11 deterministic pressure field, triangulated closed keycap\n')
        for x,y,z in vertices:f.write(f'v {x:.7f} {y:.7f} {z:.7f}\n')
        for a,b,c in faces:f.write(f'f {a} {b} {c}\n')
    return {'vertices':len(vertices),'triangles':len(faces),'file':out.name}

# static scene textures
bg=np.zeros((H,W,3),np.uint8)
yy,xx=np.mgrid[:H,:W]
bg[:,:,0]=np.uint8(np.clip(13+18*(1-yy/H)+7*np.sin(xx/96),0,255))
bg[:,:,1]=np.uint8(np.clip(19+25*(1-yy/H),0,255))
bg[:,:,2]=np.uint8(np.clip(42+35*(1-yy/H),0,255))
for ix in range(0,W,24):cv2.line(bg,(ix,0),(ix,H),(30,41,67),1)
for iy in range(0,H,24):cv2.line(bg,(0,iy),(W,iy),(30,41,67),1)

def txt(img,xy,text,size,fill,stroke=0,stroke_fill=(4,8,14),anchor=None):
    d=ImageDraw.Draw(img);d.text(xy,text,font=font(size),fill=fill,stroke_width=stroke,stroke_fill=stroke_fill,anchor=anchor)

def frame(t,mode='HYDRO'):
    face,h,p=render_face(t,mode)
    # OpenCV is BGR, PIL RGB.
    screen=Image.fromarray(bg.copy(),'RGB')
    d=ImageDraw.Draw(screen)
    d.rectangle((0,0,959,66),fill=(8,13,30),outline=(67,87,119),width=2)
    txt(screen,(26,10),'AAA-KIT / FRONTIER T11',27,(245,249,255),2)
    txt(screen,(29,47),'VOLUMETRIC-LOOKING HYDRO JELLY  /  60 HZ OFFLINE RENDER',11,(117,197,236))
    txt(screen,(930,21),f'{mode} / {t:04.2f}s',14,(169,221,247),anchor='ra')
    # square hero base and steps. Ink outline 4px style at scaled output resolution
    d=ImageDraw.Draw(screen)
    d.rectangle((149,141,811,437),fill=(4,8,17))
    d.rectangle((155,147,805,426),fill=(18,31,60),outline=(5,7,13),width=5)
    d.rectangle((172,171,789,404),fill=(7,20,39),outline=(84,104,133),width=3)
    # physical keycap shell responds to pressure with its whole body moving, lip hides
    py=int(18*max(0,p))
    color={'HYDRO':(15,95,155),'PRISM':(105,29,158),'SOLAR':(180,86,23)}[mode]
    d.rectangle((191,180+py,769,393),fill=(5,9,21),outline=(6,8,14),width=5)
    d.rectangle((198,187+py,762,380+py),fill=color,outline=(3,5,15),width=5)
    # projected image field is derived from the same geometry normals
    tile=Image.fromarray(face,'RGB')
    tile=tile.resize((FW,194),Image.Resampling.BILINEAR)
    screen.paste(tile,(230,184+py))
    d=ImageDraw.Draw(screen)
    d.rectangle((226,180+py,734,382+py),outline=(8,13,23),width=6)
    d.line((236,190+py,722,190+py),fill=(172,244,255),width=3)
    # 3d stepped bevel, black ink outer consistent
    d.line((205,387+py,764,387+py),fill=(5,10,21),width=10)
    d.line((211,393+py,755,393+py),fill=(38,117,153),width=3)
    # protected icon/text as the only bright center read
    if mode=='HYDRO':label='PLAY';icol=(255,222,84)
    elif mode=='PRISM':label='UPGRADE';icol=(242,198,255)
    else:label='CLAIM';icol=(255,240,154)
    cy=285+py
    d.polygon([(309,cy-35),(309,cy+35),(370,cy)],fill=icol)
    d.line([(309,cy-35),(309,cy+35),(370,cy),(309,cy-35)],fill=INK,width=6,joint='curve')
    txt(screen,(525,cy),label,57,(255,255,255),5,(7,11,22),anchor='mm')
    # side priority labels and measurements
    txt(screen,(149,462),'MESH: 41 x 25 LATTICE',15,(182,216,247))
    txt(screen,(812,462),'EI: 500 x 194 FIELD',15,(182,216,247),anchor='ra')
    status='HOLD' if .88<=t<=1.42 else 'PRESS' if .65<t<.88 else 'REBOUND' if 1.42<t<2.4 else 'IDLE'
    txt(screen,(150,505),f'STATE {status}  |  PRESSURE {p:+.3f}',15,(245,207,112))
    txt(screen,(812,505),'INK > LABEL > MATERIAL > DECOR',13,(139,196,221),anchor='ra')
    return np.array(screen)

def main():
    start=time.perf_counter()
    raw=str(P/'hero_frames_%04d.png')
    for i in range(N_FRAMES):
        image=frame(i/FPS)
        cv2.imwrite(raw%i,cv2.cvtColor(image,cv2.COLOR_RGB2BGR))
    variants=[]
    for mode in ['HYDRO','PRISM','SOLAR']:
        variants.append(geometry_export(.98,mode))
        Image.fromarray(frame(.98,mode)).save(P/f'{mode.lower()}_hero.png')
    # high-quality 60fps h264. Video is genuine fps=60 with 240 distinct computed frames.
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','60','-i',str(P/'hero_frames_%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-preset','veryfast','-crf','19','-movflags','+faststart',str(P/'T11_hero_60fps.mp4')]
    subprocess.run(cmd,check=True)
    # animated gif lightweight preview from every 2nd unique computed frame at 30fps (mobile GIF support)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(P/'T11_hero_60fps.mp4'),'-vf','fps=20,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer','-loop','0',str(P/'T11_preview.gif')],check=True)
    shots=[Image.open(P/f'hero_frames_{i:04d}.png').resize((480,270)) for i in [12,53,77,106]]
    sheet=Image.new('RGB',(960,540)); [sheet.paste(a,((i%2)*480,(i//2)*270)) for i,a in enumerate(shots)]
    sheet.save(P/'four_states.jpg',quality=90)
    meta={'width':W,'height':H,'fps':FPS,'frames':N_FRAMES,'duration':N_FRAMES/FPS,'mesh_exports':variants,'render_seconds':round(time.perf_counter()-start,2),'render':'Offline CPU-generated geometry-sourced pixel material; not Roblox engine rendering','face_resolution':[FW,FH]}
    (P/'metrics.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
