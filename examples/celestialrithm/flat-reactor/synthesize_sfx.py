"""Create original layered per-button UI sounds: click contact + soft body + release sparkle.
One shared event envelope (visual and audio), 48 kHz stereo, deterministic synthesis.
No third-party sound assets; Roblox upload/asset IDs are not included.
"""
from pathlib import Path
import numpy as np, wave
root=Path(__file__).resolve().parents[1]
sr=48000; seconds=4.0; n=int(seconds*sr)
t=np.arange(n)/sr
out=np.zeros((n,),dtype=np.float64)
rng=np.random.default_rng(178)
events=[(.4,360), (1.12,520), (1.84,680), (2.56,440)]
for start,pitch in events:
 onset=int(start*sr);dur=int(.24*sr)
 tt=np.arange(dur)/sr
 transient=(rng.normal(0,1,dur)*np.exp(-tt*140)*.05)
 body=(np.sin(2*np.pi*(pitch*tt+90*tt**2))*np.exp(-tt*27)*.09)
 shimmer=(np.sin(2*np.pi*4*pitch*tt)*np.exp(-tt*34)*.022)
 release=np.sin(2*np.pi*(1.8*pitch)*tt)*np.exp(-((tt-.09)/.055)**2)*.022
 out[onset:onset+dur]+=transient+body+shimmer+release
out=np.tanh(out*1.1)
stereo=np.stack([out,out],axis=1)
p=root/'renders/FlatStudReactor_original_SFX.wav'
with wave.open(str(p),'wb') as f:
 f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((stereo*32767).astype('<i2').tobytes())
print('original SFX',p)
