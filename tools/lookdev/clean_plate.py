"""Paint the old HUD out of a game capture so a new HUD can be mocked over it.

The winter corridor is near-symmetric about its centre (x = 836 in the 1672 px capture),
so holes on the left are filled with the mirrored right side (real fences, walls and snow);
the remaining holes (top centre, top right, bottom centre) get a coarse inpaint plus
grain. Rects are in capture pixels. Run: python3 tools/lookdev/clean_plate.py CAPTURE OUTDIR
Needs opencv-python-headless and numpy.
"""
import os, sys
import cv2, numpy as np
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
src = cv2.imread(sys.argv[1])
H, W = src.shape[:2]
def mask(R):
    m = np.zeros((H, W), np.uint8)
    for x0,y0,x1,y1 in R: m[y0:y1, x0:x1] = 255
    return m
# corridor centre is x≈836, so mirror about it: x -> 2*836 - x
cx = 836
mx = np.clip(2*cx - np.arange(W), 0, W-1)
mirror = src[:, mx]
mL = mask([(0,70,400,680),(0,742,490,941)])
mI = mask([(455,0,1215,172),(1185,0,1672,84),(526,768,1160,941)])
out = src.copy()
# mirrored fill for the left side, nudged to the local colour so seams don't show
out[mL>0] = mirror[mL>0]
s = 4
small = cv2.resize(out, (W//s, H//s), interpolation=cv2.INTER_AREA)
ms = cv2.resize(mI, (W//s, H//s), interpolation=cv2.INTER_NEAREST)
fs = cv2.inpaint(small, ms, 6, cv2.INPAINT_TELEA)
coarse = cv2.resize(fs, (W, H), interpolation=cv2.INTER_CUBIC)
out[mI>0] = coarse[mI>0]
rng = np.random.default_rng(3)
o = out.astype(np.float32); o[mI>0] += rng.normal(0, 3.0, (H, W, 1)).astype(np.float32)[mI>0]
out = np.clip(o,0,255).astype(np.uint8)
m = np.maximum(mL, mI)
feather = cv2.GaussianBlur(m, (0,0), 4).astype(np.float32)[...,None]/255
out = (src*(1-feather) + out*feather).astype(np.uint8)
cv2.imwrite(os.path.join(OUT, 'backdrop_clean.png'), cv2.resize(out, (1920, 1080), interpolation=cv2.INTER_CUBIC))

