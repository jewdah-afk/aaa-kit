# Trace and match: lining a concept up with its brick model

Chapter [91](91-readable-voxel-surfaces.md) scores a model's surface on its own. This chapter
compares the model with its **concept drawing**: outline both, lay one over the other, measure
the gap, and trace the concept's plates straight into the model. The war rhino is the
benchmark.

Researched **2026-11-13**. Sources were read through search summaries. Nothing here was run
in Studio or on a phone.

## Short version

- **The shipped rhino's plate lines are in the wrong place, and that is measurable.** Its
  folds run diagonally; the concept's plates lie in horizontal rows. Mean distance from a
  concept plate line to the nearest model line: 1.78 bricks.
- **Tracing fixes placement directly.** The concept's plates are its lit top faces. Segment
  them, fit the drawing to the model's side view, and let each brick look up its plate. The
  traced rhino scores 0.73 bricks on the same measure.
- **The fit is a stretch, not a camera solve.** The concept is drawn in perspective and in a
  walking pose, so silhouette overlap tops out near 0.79 and legs, head and tail do not line up.

## 1. What the search added

| Idea | Use here | Source |
|---|---|---|
| Chamfer matching: score a template's edges against the distance map of the image's edges; search coarse to fine | the line and outline distances below | [Thayananthan et al. 2003](https://mi.eng.cam.ac.uk/reports/abstracts/vision/thayananthan_cvpr03.html), [directional chamfer, MERL](https://shadow.merl.com/publications/docs/TR2010-045.pdf) |
| Silhouette intersection, then colour projection, from front and side drawings; misses hollows | a starting grid for new creatures (not built yet) | [TU Delft thesis](https://repository.tudelft.nl/record/uuid:c617a480-53fe-4e27-bfda-008cc718cee1), [sprite carving write-up](https://0fps.net/2012/09/18/turning-8-bit-sprites-into-printable-3d-models/) |
| Merge unit bricks into larger ones layer by layer | turning traced regions into fewer, larger plates (not built yet) | [Image2Lego](https://arxiv.org/pdf/2108.08477), [Legolization](https://history.siggraph.org/?p=210389) |

## 2. The method (`scripts/trace_match.py`)

| Step | What happens |
|---|---|
| Outline | concept silhouette = everything that is not the flat grey background, holes filled |
| Plates | lit top faces: pixels brighter than their surroundings (blur radius 6), connected regions of 40 px or more, grown until they touch. The joins are the plate lines |
| Fit | stretch and slide the concept until its silhouette overlaps the model's flat side view best (coarse-to-fine search on IoU) |
| Measure | silhouette IoU; chamfer distance in bricks for the outline and for the plate lines, both directions |
| Picture | fitted concept, model view, and an overlay (concept orange, model blue) |
| Trace | plates resampled to one cell per brick; each plate gets one of four height levels so that touching plates never share a level, lighter plates higher |

The model file reads the traced map and gives each hide brick the plate at its (z, y), so the
same rows appear on both flanks and wrap over the back. Plate tops stay flat, so studs stay
whole; every plate edge is a real step of one to three bricks.

## 3. Results on the war rhino

| Model | Silhouette IoU | Concept line → model (bricks) | Model line → concept (bricks) | Structure | Relief | Backed |
|---|---|---|---|---|---|---|
| Shipped (diagonal folds) | 0.76 | 1.78 | 1.49 | 83 | 15 % | 60 % |
| First rebuild (hand-laid rings) | 0.78 | 1.16 | 1.50 | 95 | 29 % | 80 % |
| Traced rebuild | 0.79 | 0.73 | 1.14 | 91 | 29 % | 79 % |

## 4. Decisions

| Decision | Options considered | Pick | Reason |
|---|---|---|---|
| How to find plates in the drawing | dark lines between plates; lit top faces; colour clustering | lit top faces | the dark lines do not close into regions at this image size; the lit faces do |
| How to place plates | hand-laid rings; traced map | traced map | placement comes from the concept and is measured |
| Plate tops | tilted; flat | flat | a tilt turns into ripples on a brick grid and breaks the studs |
| Fit | bounding box; IoU search; camera solve | IoU search | cheap and good enough for the torso; a camera solve is the next step |

## Not tested

- Only the side view is traced. Front and back views are not used yet.
- The line distances depend on the fit; they are comparable between versions of one model, not between models.
- The plate segmentation thresholds were set on one concept sheet (541 × 406 px).
- No measure here is validated against people. Nothing ran in Studio or on a phone.

## Sources

- [Shape context and chamfer matching in cluttered scenes](https://mi.eng.cam.ac.uk/reports/abstracts/vision/thayananthan_cvpr03.html)
- [Fast directional chamfer matching (MERL TR2010-045)](https://shadow.merl.com/publications/docs/TR2010-045.pdf)
- [How can we convert 2D pixel art into a 3D voxel representation (TU Delft)](https://repository.tudelft.nl/record/uuid:c617a480-53fe-4e27-bfda-008cc718cee1)
- [Turning 8-bit sprites into printable 3D models](https://0fps.net/2012/09/18/turning-8-bit-sprites-into-printable-3d-models/)
- [Image2Lego](https://arxiv.org/pdf/2108.08477)
- [Legolization: optimizing LEGO designs](https://history.siggraph.org/?p=210389)
