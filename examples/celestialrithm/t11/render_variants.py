from pathlib import Path
import subprocess, cv2, importlib.util, json, time
P=Path(__file__).parent
spec=importlib.util.spec_from_file_location('render',P/'render.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for name in ['PRISM','SOLAR']:
 for i in range(m.N_FRAMES):
  a=m.frame(i/m.FPS,name)
  cv2.imwrite(str(P/f'{name.lower()}_frame_{i:04}.png'),cv2.cvtColor(a,cv2.COLOR_RGB2BGR))
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','60','-i',str(P/f'{name.lower()}_frame_%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-preset','veryfast','-crf','19','-movflags','+faststart',str(P/f'T11_{name.lower()}_60fps.mp4')],check=True)
 for f in P.glob(f'{name.lower()}_frame_*.png'):f.unlink()
 print(name,'done')
