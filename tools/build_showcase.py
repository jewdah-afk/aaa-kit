#!/usr/bin/env python3
"""Builds examples/web/showcase.html from showcase.tpl.html by splicing in the tested engine
(noise, Voronoi, reaction-diffusion, meshes, the UV-space bake, recipes and the flow table) from
examples/web/surface-bake.html, so the showcase and the lab always run the same code.

  python3 tools/build_showcase.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "examples" / "web"
lab = (WEB / "surface-bake.html").read_text(encoding="utf-8")
tpl = (WEB / "showcase.tpl.html").read_text(encoding="utf-8")

start = lab.index("// ---------------------------------------------------------------- noise")
end = lab.index("// ---------------------------------------------------------------- realtime motion")
engine = lab[start:end]
m = re.search(r"^function lut\(\).*\n^const LUT = lut\(\);\n", lab, re.M)
if not m:
    sys.exit("lut() not found in surface-bake.html")
engine += "\n" + m.group(0)
engine = engine.replace('const SIZES = { "128": 128, "256": 256, "512": 512 };\n', "")

if "/*ENGINE*/" not in tpl:
    sys.exit("template has no /*ENGINE*/ marker")
out = tpl.replace("/*ENGINE*/", "// ===== engine spliced from surface-bake.html by tools/build_showcase.py =====\n" + engine)
(WEB / "showcase.html").write_text(out, encoding="utf-8")
print(f"examples/web/showcase.html: {len(out) // 1024} KB (engine {len(engine) // 1024} KB)")
