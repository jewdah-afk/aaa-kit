from pathlib import Path
import cv2,numpy as np,json,subprocess,re
p=Path(__file__).parent
r=json.loads((p/'metrics.json').read_text())
checks={}
for path in ['T11_hero_60fps.mp4','T11_preview.gif','four_states.jpg','hydro_press.obj','prism_press.obj','solar_press.obj','hydro_hero.png','prism_hero.png','solar_hero.png']:
 checks['exists_'+path]= (p/path).is_file() and (p/path).stat().st_size>100
obj_counts=[]
for mode in ['hydro','prism','solar']:
 lines=(p/f'{mode}_press.obj').read_text().splitlines(); v=sum(l.startswith('v ') for l in lines); f=sum(l.startswith('f ') for l in lines)
 checks[mode+'_geometry_counts']=(v==1153 and f==2176)
 obj_counts.append((mode,v,f))
video=p/'T11_hero_60fps.mp4'
result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames,width,height,duration','-of','json',str(video)],capture_output=True,text=True,check=True)
stream=json.loads(result.stdout)['streams'][0]
checks['60fps_exact']=stream['avg_frame_rate']=='60/1'
checks['240_encoded_frames']=int(stream['nb_frames'])==240
checks['size_960x540']=(stream['width']==960 and stream['height']==540)
# video frames not repeated: significant sequential pixel differences
cap=cv2.VideoCapture(str(video));prev=None;deltas=[];n=0
while True:
 ok,frame=cap.read()
 if not ok:break
 if prev is not None:deltas.append(float(np.mean(np.abs(frame.astype(np.int16)-prev.astype(np.int16)))))
 prev=frame;n+=1
cap.release()
checks['decoded_240_frames']=n==240
checks['frames_change']=sum(x>.015 for x in deltas)>=235
# compare icon-region vs outer material to check contrast; proxy not proper APCA
img=cv2.imread(str(p/'hydro_hero.png'))
gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
# bright white CTA area and background samples
label=float(np.percentile(gray[275:325,445:610],85));surround=float(np.median(gray[212:250,430:600])); contrast=abs(label-surround)
checks['label_region_contrast_proxy']=contrast>=35
checks['no_missing_frame_files']=len(list(p.glob('hero_frames_*.png')))==240
result={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'ffprobe':stream,'sequential_frame_mean_differences':{'min':min(deltas),'median':float(np.median(deltas)),'max':max(deltas)},'grayscale_label_85th_percentile':label,'grayscale_surround_median':surround,'caveats':['Frame differences include video compression','Grayscale pixel contrast is not APCA, saliency or eye tracking','Only offline performance tested. No Studio execution or hardware benchmark']}
(p/'QA_RESULTS.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
assert all(checks.values()),'Some QA checks failed'
