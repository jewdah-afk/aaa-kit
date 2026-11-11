# tools/hierarchy

Measures visual hierarchy: where the eye goes, whether text is readable, whether colour codes survive colour blindness, and whether effects are flash-safe. It needs only Python 3, numpy and Pillow. The science and the thresholds are in [research Part V](../../docs/research/85-measuring-hierarchy.md); the workflow is in the [hierarchy-audit skill](../../.claude/skills/hierarchy-audit/SKILL.md).

```bash
# where does the eye go? (exit 1 on FAIL)
python3 tools/hierarchy/hierarchy.py audit shot.png --focus 860,620,240,72 --out pass-03
#   pass-03.png   grey screenshot + salience heat + focus box + numbered fixations (green in focus, red outside)
#   pass-03.json  fixations, lift, competitor, squint gap, deutan/protan re-check, clutter, verdict, reasons

python3 tools/hierarchy/hierarchy.py apca '#9aa4b2' '#1a1a2e'          # APCA Lc + WCAG ratio
python3 tools/hierarchy/hierarchy.py flash media/gifs/tier6-boids.gif  # WCAG 2.3.1 general + red flashes
python3 tools/hierarchy/hierarchy.py flash capture.gif --fine          # strict per-pixel mode
python3 tools/hierarchy/hierarchy.py cvd shot.png --type deutan --out shot-deutan.png
python3 tools/hierarchy/test_hierarchy.py                              # 13 tests
```

| Output | Pass (house thresholds) |
|---|---|
| fixation 1 | inside a `--focus` rect |
| `lift` | ≥ 1.5: the focus holds more than its share of salience (FAIL < 1.0) |
| `competitor.ratio` | < 0.9 of the focus peak |
| `squint_gap` | ≥ 0.08 OKLab L between the focus and the ring around it, after a 1%-of-diagonal blur |
| `cvd.deutan` / `cvd.protan` | first fixation still in the focus |
| `clutter.edge_density` | compare against the same screen's calm frame; combat ≤ about 2× |

Models: the spectral residual (Hou & Zhang 2007) plus an OKLab centre-surround with Itti-style few-peaks weighting (Itti, Koch & Niebur 1998); winner-take-all with inhibition of return for the scanpath; Machado 2009 CVD matrices on linear RGB; APCA 0.0.98G-4g; WCAG 2.2 flash definitions. Limits: bottom-up only (meaning, faces and goals aren't modelled), and a single frame (no onsets). See [ch. 85 §2](../../docs/research/85-measuring-hierarchy.md#2-how-the-salience-model-works-and-how-it-fails).

`tools/check_all.sh` runs the tests and flash-checks every GIF in `media/gifs`.
