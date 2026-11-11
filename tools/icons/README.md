# tools/icons

The icon pipeline: glossy painted icons with one uniform ink outline, cut from generated sheets, QA'd on dark and light, and (optionally) modelled in Blender for 3D. The method and style rules are in the [icon playbook](../../docs/playbooks/icon-pipeline.md).

| Script | What it does |
|---|---|
| `cut_grid.py` | Cut an N×M generated sheet (black background) into `final/<name>.png`, 256 px, with the same ink ring on every icon. `python3 cut_grid.py sheet.png 4 4 name1 name2 …` (`-` skips a cell; `name!` keeps the drawn size, for size tiers) |
| `clean_ring.py` | Re-ring icons with a crisp, uniform outline (fixes soft halos); keeps originals in `final_pre_ring/` |
| `dehalo.py` | Remove baked dark auras and redraw the standard ring; writes `final_clean/` for review, `--apply` to replace |
| `bolden.py` | Thicken outlines to match an existing set |
| `qa.py` | Contact sheet on dark and light backgrounds: `python3 qa.py out.png name1 name2 …` |
| `sheet.py` | Contact sheet of Blender renders for review |
| `lib.py` | Blender (`bpy`) helpers: emission-only 3-band cel material, rim from Layer Weight, outline hull (solidify + ink material), primitives |

Needs Python 3 with Pillow, NumPy and SciPy; `lib.py` needs Blender's `bpy` (`pip install bpy`, no UI needed).
