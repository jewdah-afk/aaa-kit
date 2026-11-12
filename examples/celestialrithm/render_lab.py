"""Deterministic 60-fps reference renderer. Offline material simulations; NOT Roblox FPS evidence.
Requires numpy, Pillow. Run: python src/render_lab.py --out renders --frames 120
"""
import argparse, json, math, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[2]
PALETTES=json.loads((ROOT/'docs/celestialrithm/palettes-v1.json').read_text())
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=lambda s: ImageFont.truetype(FONT,s)

W,H=960,540
X,Y=np.meshgrid(np.linspace(-1,1,186,dtype=np.float32),np.linspace(-1,1,96,dtype=np.float32))
def rgb(hexcode): return tuple(int(hexcode[i:i+2],16) for i in (1,3,5))
def field(name,t,phase=0):
    a=np.sqrt((X-.2*np.cos(t*1.5+phase))**2+(Y-.2*np.sin(t*1.3+phase))**2)
    wave=np.sin(17*a-8*t+phase)*np.exp(-2.0*a)
    caustics=np.cos(11*X+4*np.sin(3*Y+1.8*t+phase))*np.cos(10*Y-5*np.sin(2*X+1.2*t))
    if name=='hydro': f=.58*caustics+.42*wave
    elif name=='prism': f=np.sin(10*X+5*Y+2*t)+.6*np.cos(12*Y-3*t)+.35*wave
    elif name=='solar': f=.6*np.sin(16*X-9*t)+.75*wave+.3*caustics
    elif name=='bio': f=np.sin(12*(X+Y)+3*np.sin(8*Y-t))*np.cos(8*X-4*t)
    elif name=='frost': f=np.cos(16*np.maximum(np.abs(X),np.abs(Y))-2*t)+.35*wave
    elif name=='void': f=np.sin(11*X+8*t)*np.cos(12*Y-3*t)+.8*wave
    elif name=='holo': f=np.sin(7*X+8*Y+3*t)+np.cos(14*(X-Y)-t)
    else: f=np.sin(12*X+5*t)*np.sin(8*Y-3*t)
    return f.astype(np.float32)
def patch(palette,material,t,phase=0):
    base=np.asarray(rgb(palette['base']),np.float32)
    lit=np.asarray(rgb(palette['light']),np.float32)
    deep=np.asarray(rgb(palette['shadow']),np.float32)
    f=field(material,t,phase)
    # soft curvature with high-impact luminous veins, protected center icon by layout geometry
    shine=np.maximum(0,f-.45)**3
    top=np.maximum(0,Y+.15)*.15
    blend=np.clip(.64+.14*f-top,0,1)[...,None]
    pix=deep[None,None,:]*(1-blend)+base[None,None,:]*blend
    pix=np.broadcast_to(pix,(96,186,3)).copy()
    pix=pix*(1-np.minimum(.52,shine)[...,None]) + lit[None,None,:]*np.minimum(.52,shine)[...,None]
    band=np.exp(-((X+0.7-0.37*(t%5))/.16)**2)*.20
    pix=pix*(1-band[...,None])+lit*band[...,None]
    pix=np.clip(pix,0,255).astype(np.uint8)
    return Image.fromarray(pix,'RGB')

def keycap(img,xy,size,label,kind,material,t,focus=False):
    x,y=xy; w,h=size; pal=PALETTES[kind]; d=ImageDraw.Draw(img)
    # physical black ink chassis and pressed-state entire-key translation (not just face)
    press=.5+.5*math.sin(t*2.2+(x%3)); press=press**15 if focus else 0
    dy=int(4*press)
    ink='#080d1c'; depth=int(h*.12)
    d.rounded_rectangle((x+1,y+depth+dy,x+w+1,y+h+depth+dy),radius=5,fill=ink)
    d.rounded_rectangle((x+4,y+depth-1+dy,x+w-4,y+h+depth-4+dy),radius=3,fill=pal['shadow'])
    d.rounded_rectangle((x,y+dy,x+w,y+h+dy),radius=5,fill=ink)
    d.rounded_rectangle((x+4,y+4+dy,x+w-4,y+h-4+dy),radius=3,fill=pal['base'])
    surface=patch(pal,material,t,(x+y)/53).resize((w-14,h-17),Image.Resampling.BILINEAR)
    mask=Image.new('L',surface.size); md=ImageDraw.Draw(mask); md.rounded_rectangle((0,0,surface.width-1,surface.height-1),radius=2,fill=255)
    img.paste(surface,(x+7,y+7+dy),mask)
    d=ImageDraw.Draw(img)
    d.line([(x+8,y+9+dy),(x+w-9,y+9+dy)],fill=pal['light'],width=2)
    d.line([(x+8,y+h-8+dy),(x+w-8,y+h-8+dy)],fill=pal['shadow'],width=3)
    if focus:
        d.rounded_rectangle((x-3,y-3,x+w+3,y+h+depth+3),radius=7,outline='#e6f9ff',width=2)
    # label is conventional GUI analogue, never written into dynamic material buffer
    f=font(13 if w>120 else 11)
    bb=d.textbbox((0,0),label,font=f,stroke_width=2)
    tx=x+(w-(bb[2]-bb[0]))//2;ty=y+(h-(bb[3]-bb[1]))//2-2+dy
    d.text((tx,ty),label,font=f,fill='#ffffff',stroke_width=3,stroke_fill='#0b0c10')

def container(img,box,title):
    d=ImageDraw.Draw(img);x,y,w,h=box
    d.rounded_rectangle((x,y,x+w,y+h),radius=8,fill='#09172a',outline='#405779',width=2)
    d.rectangle((x+2,y+2,x+w-2,y+37),fill='#152c4a')
    d.line((x+4,y+39,x+w-4,y+39),fill='#060b18',width=3)
    d.text((x+13,y+10),title,fill='#e9f3ff',font=font(16))

def render(t):
    img=Image.new('RGB',(W,H),'#081125');d=ImageDraw.Draw(img)
    # low-frequency background, calm, bounded underneath HUD
    for i in range(0,960,32):d.line((i,0,i,540),fill='#10213a',width=1)
    for j in range(0,540,32):d.line((0,j,960,j),fill='#10213a',width=1)
    d.rectangle((0,0,960,53),fill='#101f38');d.line((0,52,960,52),fill='#253e65',width=2)
    d.text((17,15),'CELESTIALRITHM',fill='#f1f7ff',font=font(19))
    d.text((237,20),'SHOP   /   INVENTORY   /   TASKBAR',fill='#89bcf2',font=font(13))
    d.text((801,20),'FRAME 60',fill='#a1bce1',font=font(12))
    container(img,(16,67,326,452),'SHOP / MATERIAL ECONOMY')
    container(img,(352,67,346,452),'INVENTORY / RARITY')
    container(img,(708,67,236,452),'TASKBAR / HUD')
    d=ImageDraw.Draw(img)
    # Shop featured card and buy controls
    keycap(img,(32,124),(294,94),'FEATURED  /  HYDRO','hydro','hydro',t,True)
    for x,k,m,l in [(32,'solar','solar','BUY  499'),(184,'prism','prism','EQUIP')]:
        keycap(img,(x,239),(142,51),l,k,m,t)
    for i,(k,m,l) in enumerate([('bio','bio','SLIME'),('frost','frost','ICE'),('void','void','VOID'),('holo','holo','HOLO')]):
        x=32+(i%2)*152;y=319+(i//2)*86
        keycap(img,(x,y),(142,62),l,k,m,t)
    # Inventory grid 4 x 3; one selected, one rarity motion owner
    keys=['hydro','prism','solar','bio','frost','void','holo','azure','solar','frost','prism','bio']
    for i,k in enumerate(keys):
        x=368+(i%4)*80;y=126+(i//4)*96
        keycap(img,(x,y),(70,72),'★' if i==5 else str(i+1),k,k,t, i==5)
    d=ImageDraw.Draw(img);d.text((368,445),'SELECTED   VOID / EPIC',font=font(13),fill='#f3c9ff')
    d.text((368,472),'Inspect • Compare • Equip',font=font(11),fill='#93a7c8')
    # HUD vertical taskbar and counters
    buttons=[('hydro','SHOP'),('prism','UPGRADE'),('solar','PETS'),('bio','REWARDS'),('azure','INDEX')]
    for i,(k,l) in enumerate(buttons):keycap(img,(723,119+i*65),(205,50),l,k,k,t,i==1)
    d=ImageDraw.Draw(img);d.text((727,463),'GOLD',font=font(12),fill='#c6defc');d.text((788,463),'2.66B',font=font(18),fill='#ffd24a')
    d.text((727,492),'60 FPS TARGET • OFFLINE',font=font(10),fill='#90accd')
    return img

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--frames',type=int,default=120);ap.add_argument('--out',default=str(ROOT/'renders'));args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    st=time.perf_counter()
    for i in range(args.frames):
        image=render(i/60)
        image.save(out/f'frame_{i:04}.png',compress_level=1)
    print(json.dumps({'frames':args.frames,'resolution':[W,H],'offline_seconds':round(time.perf_counter()-st,2)}))
