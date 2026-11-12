"""Deterministic offline pixel-compositor demo of flat Stud UI, using actual screenshot crops.
No AI textures; real source pixels unchanged at rest. 240 computed frames, 60 FPS container.
This uses no Roblox APIs and does not prove EditableMesh runtime performance.
"""
from pathlib import Path
import numpy as np, cv2, math, subprocess, json, time
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
ORIG=Path('/mnt/data/cachedMedia(1).jpeg')
assert ORIG.exists(),f'please place original screenshot at {ORIG}'
img=np.asarray(Image.open(ORIG).convert('RGB'))
# x, y, w, h; carefully aligned with real screenshot
buttons={'SHOP':(16,242,113,111),'UPGRADES':(139,242,114,111),'INDEX':(16,365,113,113),'ANIMALS':(139,365,114,113)}
regions={k:img[y:y+h,x:x+w].copy() for k,(x,y,w,h) in buttons.items()}
W,H=1152,752
canvas=np.zeros((H,W,3),dtype=np.uint8)
canvas[:]=[11,19,36]
cv2.putText(canvas,'ACTUAL STUD UI  /  T12+ COUPLED MATERIAL STUDY',(38,47),cv2.FONT_HERSHEY_SIMPLEX,0.76,(220,230,245),2,cv2.LINE_AA)
cv2.putText(canvas,'ORIGINAL PAINTED ART REMAINS THE VISIBLE FACE',(38,74),cv2.FONT_HERSHEY_SIMPLEX,0.44,(137,164,198),1,cv2.LINE_AA)
roles=['SHOP','UPGRADES','INDEX','ANIMALS']
colors={'SHOP':(255,57,110),'UPGRADES':(183,94,255),'INDEX':(50,208,255),'ANIMALS':(255,180,39)}
# 2x2 stage, each with a 2.5x upscale of the exact original image. Big enough for phones.
coords={'SHOP':(56,116),'UPGRADES':(602,116),'INDEX':(56,406),'ANIMALS':(602,406)}
size=(275,275)
xx,yy=np.meshgrid(np.arange(size[0]),np.arange(size[1])); u=xx/(size[0]-1); v=yy/(size[1]-1)
frame_samples=[]
def event(t,j):
  # 4 distinct hero events: impacts staggered; each returns to baseline
  tt=t-(0.4+j*0.72)
  if tt<0 or tt>1.12:return 0,0
  pressure=max(0,1-abs(tt-.16)/.16) if tt<.32 else max(0,math.exp(-(tt-.32)*7)*math.sin((tt-.32)*27))
  return min(1,max(0,math.exp(-tt*2.5))),pressure

def frame(k):
  t=k/60; out=canvas.copy()
  for j,key in enumerate(roles):
    x0,y0=coords[key]
    src=regions[key]
    arr=cv2.resize(src,size,interpolation=cv2.INTER_NEAREST).astype(np.float32)
    env,press=event(t,j)
    # No icon/text repaint, only change background color where naturally high-saturation bright face exists.
    mx=arr.max(2);mn=arr.min(2);sat=(mx-mn)/(mx+1e-5)
    # Restrict optic signal to upper-right/right-side border strips to protect central icon and lower label.
    rim=((u>0.80)&(u<0.94)&(v>0.10)&(v<0.76)) | ((v<0.18)&(v>0.07)&(u>0.08)&(u<0.92))
    background=((u>.07)&(u<.94)&(v>.08)&(v<.70)&(sat>.18)&(mx>70))
    iconzone=((u>.2)&(u<.79)&(v>.20)&(v<.71))
    permitted=(background & ~iconzone)|rim
    phi=22*u+12*v + 1.7*np.sin(10*v-3*t)
    waves=np.sin(phi+9*t)+.5*np.cos(31*v-13*u-7*t)
    caustic=np.clip(np.maximum(waves,0)**3 * (20+env*54),0,78)
    weight=(permitted.astype(float)*env).astype(np.float32)
    color=np.asarray(colors[key],dtype=np.float32)
    arr=np.clip(arr + (color[None,None,:]/255)*caustic[:,:,None]*weight[:,:,None],0,255).astype(np.uint8)
    # Existing art is translated as a single object, with extrusion visible UNDER it.
    offset=int(round(6*press))
    lip=14-offset
    px=x0+150
    py=y0+4+offset
    # Square under-body and lip, no giant frame or replacement artwork.
    cv2.rectangle(out,(px-8,py+lip-2),(px+size[0]+8,py+size[1]+lip+8),(4,6,13),-1)
    dark=np.clip(color*.38,0,255).astype(np.uint8)
    cv2.rectangle(out,(px,py+lip-1),(px+size[0],py+size[1]+lip),tuple(int(a) for a in dark),-1)
    cv2.rectangle(out,(px,py+lip),(px+size[0],py+size[1]+lip),(6,9,20),3)
    out[py:py+size[1],px:px+size[0]]=arr
    # One localized SDF halo reserved for the currently pressed button.
    if env>0.01:
      halo=np.zeros_like(out)
      c=tuple(int(vv) for vv in color)
      cv2.rectangle(halo,(px-4,py-4),(px+size[0]+4,py+size[1]+5),c,2)
      blurred=cv2.GaussianBlur(halo,(0,0),5)
      out=np.clip(out.astype(np.float32)+blurred.astype(np.float32)*env*.5,0,255).astype(np.uint8)
  cv2.putText(out,'T12: MEMBRANE PRESSURE / OPTICAL FIELD / UNDER-FACE DEPTH / PROTECTED ICONS',(40,730),cv2.FONT_HERSHEY_SIMPLEX,.44,(149,175,214),1,cv2.LINE_AA)
  return out

def main():
  ROOT.joinpath('renders').mkdir(exist_ok=True)
  outpath=ROOT/'renders/FlatStudReactor_60fps.mp4'
  cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','60','-i','-','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',str(outpath)]
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  for k in range(240):
    fr=frame(k)
    if k in [0,40,83,127,173,220]:Image.fromarray(fr).save(ROOT/f'renders/frame_{k:03d}.png')
    p.stdin.write(fr.tobytes())
  p.stdin.close(); assert p.wait()==0
  print('wrote',outpath, outpath.stat().st_size)
if __name__=='__main__':main()
