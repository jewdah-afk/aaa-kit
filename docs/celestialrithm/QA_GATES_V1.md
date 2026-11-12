# QA Gates and known failures — v1

## Local verification completed

- 8 Python unit checks pass: palette syntax, deterministic frames, finite numerical fields, time changes, target image dimensions, static top bar, significant material changes.
- Output video verified with ffprobe: 960×540, 120 decoded frames, 60/1 frames per second. This **does not** demonstrate real-time rendering speed or Roblox client 60 FPS.
- One representative frame inspected visually: squared dark ink, distinct colored keycaps, coherent labels and grouped Shop/Inventory/Taskbar layout. No algorithm-induced cursor magnetism.

## Not yet verified

- True EditableImage and EditableMesh runtime; the source renderer is Python/Pillow, not Studio output.
- Roblox GUI anchoring under cutouts/mobile safe areas, hitboxes and all text clipping.
- `lune`, `selene`, `rojo`, `Studio` and GPU shader bake; not installed in this execution container.
- Full repo `tools/hierarchy/hierarchy.py` audit; source was reviewed but no checkout/execution was available.
- Real audio mixing/ducking (this preview has no sound) and avatar-appearance permissions.
- No writes to GitHub: connector branch creation previously returned HTTP 403 `Resource not accessible by integration`.

## Acceptance thresholds for in-game upgrade

- Readability: all labels ≥60 APCA Lc on worst material frame; play-critical numeric text ≥75. Never assume a white font is safe just because it has a stroke.
- Salience: first fixation on intended CTA, lift ≥1.5, strongest competitor <90% of focus, squint OKLab-L difference ≥0.08. Apply the repo's existing auditor to gameplay and menu screenshots.
- Motion: idle mostly still; background can be slow, selected key only quiet. Respect `GuiService.ReducedMotionEnabled`; flash testing for every final GIF.
- Performance: instrument per-stage milliseconds in Studio. At 60 Hz, complete frame target 16.67 ms; subsystem cost caps are design hypotheses and require device-specific testing. Keep fixed topology and one displayed EI update per frame.
- Pixel ownership: original icons and text own the foreground; material can only write into face material region. No uncontrolled frame glow; no fractured text.
- Reproducibility: record seed, source version, device, frame count, render resolution, candidate ID, author approval.

## Measurable next experiment

**Candidate V1-A: Hydroglass press.** Hold all typography/icons constant. Increase optical displacement until first mobile-size viewers notice motion, then keep the minimum effective intensity. Measure 10 representative frames with APCA, squint, CVD and flash checks. Next compare with physically coupled EditableMesh; reject extra geometry if the readability/performance gain is imperceptible.
