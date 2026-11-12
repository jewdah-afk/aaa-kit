"""Contact sheet of the brick pipeline's *_fx.png renders (3 per row, 450 px tiles, preferred views first).
py brick_sheet.py <render_dir> <out.png>"""
import sys, glob, os
from PIL import Image
d, out = sys.argv[1], sys.argv[2]
ORDER = ('rest_34', 'ref34', 'rest_side', 'side', 'rest_front', 'front', 'rest_back', 'back34', 'head34', 'nose', 'face', 'headside',
         'wheels', 'footfront', 'footside', 'feet', 'ortho_front', 'ortho_side', 'ortho_back', 'ortho_top')
fs = sorted(glob.glob(os.path.join(d, '*_fx.png')))
def key(p):
    v = os.path.basename(p)[:-7].split('_', 1)[-1]
    return (ORDER.index(v) if v in ORDER else 99, v)
fs.sort(key=key)
T = 450; cols = 3; rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * T, rows * T), 'white')
for i, p in enumerate(fs):
    sheet.paste(Image.open(p).convert('RGB').resize((T, T)), ((i % cols) * T, (i // cols) * T))
sheet.save(out); print('SHEET_OK', len(fs), 'views ->', out)
