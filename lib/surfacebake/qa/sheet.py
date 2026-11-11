#!/usr/bin/env python3
"""Runs test_surfacebake.luau --images and writes a contact sheet of every baked map (needs Pillow)."""
import subprocess, sys, pathlib
from PIL import Image, ImageDraw
here = pathlib.Path(__file__).parent
subprocess.run(["lune", "run", "test_surfacebake.luau", "--images"], cwd=here, capture_output=True, check=True)
imgs = []
for f in sorted((here / "out").glob("*.rgba")):
    stem = f.stem
    name, size = stem[3:].rsplit("_", 1)
    w, h = (int(v) for v in size.split("x"))
    imgs.append((name, Image.frombytes("RGBA", (w, h), f.read_bytes())))
cell = 256
sheet = Image.new("RGB", (cell * 6, (cell + 18) * 2), (24, 24, 30))
d = ImageDraw.Draw(sheet)
for idx, (name, im) in enumerate(imgs):
    col, row = idx // 2, idx % 2  # columns: map kind; rows: sphere, box
    bg = Image.new("RGBA", im.size, (40, 40, 48, 255))
    bg.alpha_composite(im)
    sheet.paste(bg.convert("RGB").resize((cell, cell), Image.NEAREST), (col * cell, row * (cell + 18) + 18))
    d.text((col * cell + 4, row * (cell + 18) + 3), name, fill=(220, 220, 230))
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else here / "out" / "sheet.png")
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print(out, len(imgs), "maps")
