# lib

Reusable Luau libraries for pixels and procedural geometry in Roblox. Everything here is pure Luau: it runs headless in lune for tests and timings, and only clearly marked adapter functions touch Roblox APIs.

| Library | What it is | Tests |
|---|---|---|
| [frontier](frontier/README.md) | EditableImage and EditableMesh at the engine's limits: an image pool under a byte budget, an atlas and per-frame upload scheduler, a palette-indexed framebuffer, a snapshot codec, falling sand, 2D radiance-cascade GI, Voxel Space terrain, sprite stacking, heightfield and destructible contour meshes, real lightmaps, a sand table and fracture | 12 QA scripts, 158 checks (`qa/test_*.luau`) |
| [pixelfx](pixelfx/README.md) | 15 EditableImage effects writing `WritePixelsBuffer`-ready RGBA8: Lichtenberg lightning, Physarum, wave rings, frost DLA, jump-flood outlines, blue-noise dissolve, bloom, palette dither, phyllotaxis, orbit trails, FABRIK chains, cave CA, slot reel, enemy bake, a 1000-enemy crowd | `qa/run.luau` (timings), `qa/crowd.luau` (stress) |
| [surfacebake](surfacebake/README.md) | Algorithm textures baked onto model assets: UV-space G-buffer, curvature/AO/edge distance, 3D noise, Voronoi and pattern terms, triplanar 2D renders, 15 data recipes → colour, OpenGL normal, roughness, metalness; realtime animated surfaces (pulse, flow, dissolve, scan, spread); reactive surfaces (heat, ripples, frost vs lava, spin shimmer, spring lag); depth without shaders (POM, interior mapping, infinite zoom, layered parallax, shell fur); `Apply` puts them on a MeshPart | `qa/test_surfacebake.luau` (28), `qa/test_motion.luau` (26), `qa/test_react.luau` (11), `qa/bench.luau` → [BENCH.md](surfacebake/BENCH.md) |
| [hologram](hologram/README.md) | A model as a blueprint: mirrored rig joints, outline points and voxel slots taken from the brick pipeline's own maths, plus a 1:1 Morton-curve transform that flies any voxel pile into the slots and lands exactly | `qa/test_hologram.luau` |

The research behind them (the EditableImage and EditableMesh API references and technique cookbooks) is in [docs/research](../docs/research/README.md); the `editable-image` and `editable-mesh` skills say when to use which module.

## Run the tests

```sh
cd lib/frontier/qa && for f in test_*.luau; do lune run $f | grep -a '^@@\(CHECK\|DONE\)'; done
lune run lib/pixelfx/qa/run.luau > /dev/null && echo pixelfx ok
```

`frontier/qa/run.py` runs the same scripts under the standalone `luau` CLI (interpreted and `--codegen`), writes PNG frames to `qa/out/` and a timing table. It needs Pillow and the `luau` binary (`rokit add luau-lang/luau`).

`vs.checkerboard_cheaper` in `test_fx_voxelspace` is a wall-clock comparison; on a busy machine it can fail once and pass on a re-run.

## Status

Imported from the research-calculator repo's EditableImage/EditableMesh branches (2026-11-11). All checks pass headless under lune 0.10.5; Studio timings come from `frontier/studio/Bench.client.luau` and haven't been re-run from this repo.
