# AAA-KIT T11 — 60 FPS Hero Button, reproducible research package

## What is actually delivered
- 3 distinct **60 FPS H.264 MP4s** (Hydroglass, Prism Gel, Solar Plasma); each 4 s / 240 frames at 960×540.
- 1 small preview GIF (20 FPS derivative of the real 60 FPS video; GIF is not itself 60 FPS).
- 3 OBJ meshes, each **1,153 vertices / 2,176 faces**. A fixed 41×25 top grid, plus closed side wall, press-deformed by the same function driving the optical field.
- `render.py` (offline Python + NumPy + OpenCV + Pillow, deterministic), `render_variants.py`, `qa.py` and `QA_RESULTS.json`.
- `T11_Studio_Harness.client.luau`: experimental Roblox mesh/UV/image implementation, GUI input overlay and script-side timings.

## Research grounding — actual aaa-kit paths
- `HIERARCHY.md`: single dominant primary, pixel ownership, meaningful color jobs, calm frames, protected label regions.
- `docs/playbooks/figma-to-roblox-ui.md`: squared ink body (radius ~4), faces/lips ~2.5, `#0B0C10`, whole keycap moves as one object on press.
- `.claude/skills/editable-mesh/SKILL.md`: fixed topology, deform only touched vertices; cheap collision proxy.
- `.claude/skills/shaders-and-sdf/SKILL.md`: signed-distance-field masks and optical field math.
- `lib/frontier/README.md`: uploader and atlas lessons, dirty tiles and shared per-frame budgets.
- `lib/pixelfx/README.md`: wave rings, jump flooding and hierarchy-aware effects.
- `docs/playbooks/icon-pipeline.md`: actual 256×256 painted icons with consistent 6 px ink outline. **This pack uses a procedural triangle icon, not a new generated painted PNG.**

## Coupled field model

```
pressure(t) = press envelope + damped rebound
h(u,v,t,p) = bevel(u,v) + gaussian_dent(u,v,p) + ring_impulse(u,v,t,p) + micro_wave(u,v,t)
mesh_vertex_z = h(u,v,t,p)
normal ≈ normalize(-∂h/∂u, -∂h/∂v, 1)
caustic = directional interference(phase + k*h)
material_color = diffuse(normal) + specular(normal) + caustic
material_color = mix(material_color, stable_center, protected_glyph_mask)
```

In the **offline renderer**, the same displacement field is sampled on the exported mesh and the shaded image. For real-time rendering, the image is computed as an approximation of the mesh optics, not a ray-traced physically correct refraction.

## QA results — measured here
- 19/19 offline tests PASS after correcting the overly broad glyph-area contrast measurement.
- 960×540, 60/1 average video frame rate, 240 frames, 4.000 seconds by ffprobe; 240 decodable frames by OpenCV.
- Sequential rendered frames differ; this is an actual time-varying computation, not a 4-image slideshow.
- Contrast proxy: label 85th-percentile pixel = 255, background median = 149. This **is not APCA**, and not proof of real player scanpath.
- The 3 exports were counted individually; each has 1,153 vertices and 2,176 triangular faces.

## Important limitations
- **Render throughput is not Roblox FPS**. Encoding at 60 Hz does not mean the image or mesh is computed in under 16.67 ms during Roblox gameplay.
- The offline specimen is a 2.5D optical study with a closed surface geometry export; its shown face is software composited, not a full 3D rasterization of the OBJ mesh inside Roblox.
- The Roblox script is experimental and was not executed in Studio. `SetFaceUVs`, `SetPosition`, `CreateMeshPartAsync`, and `TextureContent=Content.fromObject` are documented API paths, but the actual permissions, UV orientation, memory, GPU refresh, and correct renderer must be checked in an enabled Studio session.
- UI text remains plain 2D for a stable protected silhouette. For shipping, use the owner's actual painted PNG icons and GUI layout rules.

## Studio validation gates
1. Confirm permissions: EditableMesh and EditableImage creation must succeed. Save first Output error if not.
2. Confirm checkerboard-free UV texture on the mesh. Check front/back winding and UV Y direction.
3. Verify pressed-state vertex motion is visible; test 100 simultaneous presses with 1 and 4 instances.
4. Capture MicroProfiler (mesh transcoding and GPU upload), not only script timers.
5. Measure p50/p95/p99 frame time for PC + phone 60 Hz. Adjust vertex grid, EI resolution and update rate to meet 16.67 ms whole-frame cap.
6. Capture actual in-game screenshot: squint/blur and run `tools/hierarchy/hierarchy.py audit` with a focus rectangle around the CTA, check label contrast and placement within safe areas.
7. Run on low-end phone; if degradation is required, keep press motion and outline while lowering EI update rate to 15–30 Hz.

## How to reproduce offline
`python render.py`, `python render_variants.py`, `python qa.py`.

## Design verdict
Promising **experimental T11**, not certified production AAA UI. The material movement is coherent, but the visual renderer still needs thicker depth, actual painted icon art, and Studio-grade lighting/texture inspection before replacing a shipped Stud UI button.
