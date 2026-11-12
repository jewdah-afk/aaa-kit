#!/usr/bin/env python3
"""Deterministic experimental 60 FPS *offline* Stud UI surface render.
Simulation: damped/oscillatory pressure, two-frequency caustic interference,
normal-based lighting, pressure-responsive depth lip, label protection.
CPU sampling at 60fps is not a Roblox 60fps performance benchmark.
"""
import math, pathlib, subprocess, time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=pathlib.Path(__file__).resolve().parent/'renders';OUT.mkdir(exist_ok=True)
W,H=640,360;FPS=60;FRAMES=180
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',63)
except:font=ImageFont.load_default()
Y,X=np.mgrid[0:150,0:440].astype('float32')
x=X/439; y=Y/149
base=np.zeros((150,440,3),dtype='float32');base[:,:,0]=250-50*y;base[:,:,1]=160-55*y;base[:,:,2]=17+15*y

def pulse(t):
 # 0.0-0.7s calm, 0.7-1.1 compress, 1.1-1.6 hold, release spring and settle
 if t<.7:return 0.0
 if t<1.1:return (t-.7)/.4
 if t<1.6:return 1.0
 u=t-1.6
 return math.exp(-4.2*u)*(math.cos(15*u)+.22*math.sin(15*u))

def draw(t,frame):
 p=pulse(t)
 phase=t*2.3
 # Heightfield z from shared pressure state plus moving waves.
 rr=np.sqrt(((x-.5)*1.2)**2+((y-.55)*1.5)**2)
 h=-.18*p*np.exp(-(rr/.36)**2)+.023*np.sin(34*rr-phase*3)*np.exp(-rr*3)*(max(p,0)+.08)
 dx=np.gradient(h,axis=1);dy=np.gradient(h,axis=0)
 # Computed normal and caustics (stylized, not raytraced refractive transport).
 light=np.clip(.65-dx*13-dy*9,.25,1.3)
 warp=2*np.sin(19*x+5*np.sin(9*y+phase)) + 2*np.cos(23*y-8*x+phase*1.4)
 caustic=(np.cos(9*x+4*y+warp+phase)*np.cos(9*y-3*x+warp*.8-phase*.7))**10
 water=np.clip(.23 + .65*caustic + .2*np.sin(10*x-12*y+phase)*np.sin(9*y+phase),0,1)
 material=base.copy()
 material[:,:,0]+=19*caustic-6*water
 material[:,:,1]+=40*water+16*caustic
 material[:,:,2]+=70*water+12*caustic
 material*=light[:,:,None]
 # A light band at top, and dark bottom, shaded from gradient.
 material+=np.clip(1-(y/.18),0,1)[:,:,None]*27
 material-=np.clip((y-.78)/.22,0,1)[:,:,None]*24
 # Crisp side trims not rounded pills.
 arr=np.clip(material,0,255).astype('uint8')
 canvas=Image.new('RGB',(W,H),(7,14,29));d=ImageDraw.Draw(canvas)
 # Sprite entirely floats, no extraneous outer showcase plate.
 left=90;top=87+round(8*max(p,0));depth=16-round(12*max(p,0))
 d.rectangle((left+9,top+depth+3,left+440+9,top+150+depth+7),fill=(3,5,10))
 d.rectangle((left+7,top+depth,left+445,top+150+depth),fill=(23,11,45),outline=(1,3,8),width=6)
 d.rectangle((left+4,top+depth-1,left+438,top+147+depth),fill=(164,55,4),outline=(6,5,12),width=5)
 im=Image.fromarray(arr).resize((440,150),Image.Resampling.NEAREST);canvas.paste(im,(left,top))
 d=ImageDraw.Draw(canvas)
 d.rectangle((left-4,top-4,left+443,top+153),outline=(5,6,17),width=8)
 d.line((left+11,top+10,left+429,top+10),fill=(255,249,172),width=5)
 d.line((left+11,top+12,left+11,top+43),fill=(255,235,140),width=4)
 d.line((left+12,top+143,left+429,top+143),fill=(99,38,8),width=6)
 # Protected foreground icon/text (never displaced or caustic-overpainted).
 iconx=left+61; icony=top+77
 d.polygon([(iconx-21,icony-36),(iconx-21,icony+36),(iconx+44,icony)],fill=(9,9,17))
 d.polygon([(iconx-13,icony-26),(iconx-13,icony+26),(iconx+31,icony)],fill=(249,247,251))
 tx=left+153;ty=top+34
 d.text((tx+3,ty+4),'PLAY',font=font,fill=(4,7,16),stroke_width=6,stroke_fill=(4,7,16))
 d.text((tx,ty),'PLAY',font=font,fill=(255,255,255),stroke_width=3,stroke_fill=(4,7,16))
 return canvas

def main():
 saveframes=[0,48,75,98,132,175]
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-movflags','+faststart',str(OUT/'stud_hydro_60fps.mp4')]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 start=time.perf_counter()
 for n in range(FRAMES):
  im=draw(n/FPS,n)
  if n in saveframes:im.save(OUT/f'frame_{n:03d}.png')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();ret=proc.wait()
 assert ret==0
 print('Rendered',FRAMES,'frames in',round(time.perf_counter()-start,2),'s')
 frames=[Image.open(OUT/f'frame_{n:03d}.png') for n in saveframes]
 sheet=Image.new('RGB',(W*3,H*2));
 for i,im in enumerate(frames):sheet.paste(im,((i%3)*W,(i//3)*H))
 sheet.save(OUT/'six_states.jpg',quality=93)
 # 30fps GIF direct frames from video - compact and iPhone-friendly
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(OUT/'stud_hydro_60fps.mp4'),'-vf','fps=20,scale=480:-1:flags=lanczos',str(OUT/'stud_hydro_mobile.gif')],check=True)
if __name__=='__main__':main()
