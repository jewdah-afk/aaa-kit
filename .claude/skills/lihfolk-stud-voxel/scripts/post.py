"""Post-process renders from studlib.py: black SILHOUETTE outline (like a Roblox Highlight), contact sheet, loop GIF.
py post.py <out/Name>      (needs Pillow; run with normal Python, not Blender)
"""
import sys, glob, os, shutil, subprocess
from PIL import Image, ImageFilter, ImageChops


def outline(p, px):
    im = Image.open(p).convert('RGB')
    a = Image.open(p[:-4] + '_mask.png').getchannel('A').point(lambda v: 255 if v > 128 else 0)
    ring = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(px * 2 + 1)), a)   # outer ring only, no inner lines
    im.paste((0, 0, 0), mask=ring)
    return im


def main(out):
    R = os.path.join(out, 'render')
    done = []
    for p in sorted(glob.glob(os.path.join(R, '**', '*.png'), recursive=True)):
        if p.endswith('_mask.png') or p.endswith('_ol.png') or not os.path.exists(p[:-4] + '_mask.png'):
            continue
        q = p[:-4] + '_ol.png'
        outline(p, 4 if Image.open(p).width > 700 else 3).save(q); done.append(q)
    views = [os.path.join(R, f'view_{v}_ol.png') for v in ('front', 'q34', 'side', 'back')]
    poses = sorted(glob.glob(os.path.join(R, 'pose_*_ol.png')))
    tiles = [Image.open(v).convert('RGB').resize((450, 450)) for v in views + poses if os.path.exists(v)]
    cols = 3 if len(tiles) % 4 and not len(tiles) % 3 else 4; rows = max(1, (len(tiles) + cols - 1) // cols)
    sheet = Image.new('RGB', (cols * 450, rows * 450), (40, 40, 40))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * 450, (i // cols) * 450))
    if tiles: sheet.save(os.path.join(out, 'sheet.png'))
    fr = [Image.open(p).convert('RGB') for p in sorted(glob.glob(os.path.join(R, 'loop', 'f*_ol.png')))]
    if fr:
        fr[0].save(os.path.join(out, 'loop.gif'), save_all=True, append_images=fr[1:], duration=67, loop=0)
    vids = []
    for d in sorted(glob.glob(os.path.join(R, 'clips', '*'))):      # video mode: one mp4 per clip, looped 3x
        fs = sorted(glob.glob(os.path.join(d, 'f*_ol.png')))
        if not fs: continue
        name = os.path.basename(d); lst = os.path.join(d, 'list.txt')
        with open(lst, 'w') as fh:
            for _ in range(3):
                for f in fs: fh.write("file '%s'\nduration 0.0666667\n" % f.replace('\\', '/'))
        mp4 = os.path.join(out, name + '.mp4')
        subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-vf', 'fps=30,format=yuv420p',
                        '-c:v', 'libx264', '-crf', '18', mp4], check=True)
        vids.append(name + '.mp4')
    print('POST_OK', len(done), 'images; sheet.png', 'loop.gif' if fr else '', ' '.join(vids))


def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe: return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


if __name__ == '__main__':
    main(sys.argv[1])
