"""Overlay a render's silhouette on a concept view to check proportions 1:1.
py compare.py <concept_img> <render_view.png> <out.png> [--flip] [--crop x0,y0,x1,y1]
concept pixels = coloured / dark (not the flat grey background); render = its _mask.png alpha.
Both are cropped to their bounding boxes and scaled to the same HEIGHT (feet to top), so the overlay shows proportion
errors directly: red = concept only (model missing), blue = model only (model too big), grey = match.
"""
import sys
import numpy as np
from PIL import Image


def concept_mask(path, crop):
    im = np.asarray(Image.open(path).convert('RGB').crop(crop) if crop else Image.open(path).convert('RGB')).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    sat = im.max(-1) - im.min(-1); lum = im.mean(-1)
    m = (sat > 28) | (lum < 95)
    return m, im


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def main():
    a = sys.argv[1:]
    flip = '--flip' in a
    crop = None
    if '--crop' in a: crop = tuple(int(v) for v in a[a.index('--crop') + 1].split(','))
    cm, cim = concept_mask(a[0], crop)
    rm = np.asarray(Image.open(a[1][:-4] + '_mask.png').getchannel('A')) > 128
    rim = np.asarray(Image.open(a[1]).convert('RGB')).astype(int)
    if flip: rm, rim = rm[:, ::-1], rim[:, ::-1]
    H = 320
    out = []
    for m, im in ((cm, cim), (rm, rim)):
        x0, y0, x1, y1 = bbox(m)
        k = H / (y1 - y0); W = max(1, round((x1 - x0) * k))
        out.append((np.asarray(Image.fromarray((m[y0:y1, x0:x1] * 255).astype('uint8')).resize((W, H))) > 127,
                    Image.fromarray(im[y0:y1, x0:x1].astype('uint8')).resize((W, H))))
    W = max(out[0][0].shape[1], out[1][0].shape[1])
    pad = lambda m: np.pad(m, ((0, 0), (0, W - m.shape[1])))
    c, r = pad(out[0][0]), pad(out[1][0])
    ov = np.full((H, W, 3), 255, 'uint8')
    ov[c & r] = (150, 150, 150); ov[c & ~r] = (230, 40, 40); ov[~c & r] = (40, 90, 230)
    iou = (c & r).sum() / max(1, (c | r).sum())
    sheet = Image.new('RGB', (W * 3, H), 'white')
    sheet.paste(out[0][1], (0, 0)); sheet.paste(out[1][1], (W, 0)); sheet.paste(Image.fromarray(ov), (2 * W, 0))
    sheet.save(a[2])
    print('IOU %.3f  concept aspect %.2f  model aspect %.2f' % (iou, out[0][0].shape[1] / H, out[1][0].shape[1] / H))


if __name__ == '__main__':
    main()
