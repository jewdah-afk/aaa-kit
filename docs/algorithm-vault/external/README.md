# External methods registry

A catalogue of published rendering and simulation methods that the Celestialrithm UI/material renderer (and other kit code) could use. Each entry records the original source, the core maths in two or three sentences, cost, how it maps onto Roblox (EditableImage, EditableMesh, UIGradient, baked textures), and whether the kit already implements it.

Data: [methods.json](methods.json) (76 entries). Check: [test_external.py](test_external.py).

Families: A geometry/deformation · B fluids · C optics · D procedural materials · E SDF/vector · F motion · G particles/VFX · H perceptual · I infrastructure · J worlds · X-other.

## How entries are verified

| Field | Rule |
|---|---|
| `source` | Title, authors, year and URL were seen in a web search result or fetched page. Nothing is filled from memory. |
| `verification` | `source-verified` when that holds; otherwise `unverified-source` with `url: null`. |
| `license` | Papers are `paper (no code license)`. Repos carry the licence read from their LICENSE file, or `unknown`. |
| `implemented_in_kit` | `no`, or a repo-relative path found by grepping `lib/`, `.claude/skills/` and `tools/`. `kit_note` explains partial matches. |
| Costs and fits | Relative estimates (low/med/high), not benchmarks. Measure before relying on them. |

Current state: 75 source-verified, 1 unverified. No third-party code is copied here.

## Licence flags

- **APCA**: the `apca-w3` LICENSE limits use to WCAG web content. The kit's `Perceptual.luau` uses APCA constants, so review before shipping it in a game.
- **WaveFunctionCollapse**: code is MIT; sample images may carry separate terms.
- **VoxelSpace**: code is MIT; the Comanche maps are excluded.

## Entries

| id | name | family | verification | implemented_in_kit |
|---|---|---|---|---|
| `xpbd` | XPBD (extended position-based dynamics) | A | source-verified | — |
| `pbd` | Position Based Dynamics | A | source-verified | — |
| `shape-matching` | Meshless shape matching | A | source-verified | — |
| `mean-value-cage` | Mean value coordinates (cage deformation) | A | source-verified | — |
| `dual-quaternion-skinning` | Dual quaternion skinning | A | source-verified | — |
| `meshlets` | Meshlets (clustered geometry for mesh shaders) | A | source-verified | — |
| `level-set-method` | Level set method | A | source-verified | — |
| `stable-fluids` | Stable Fluids | B | source-verified | — |
| `maccormack-advection` | Unconditionally stable MacCormack advection | B | source-verified | — |
| `vorticity-confinement` | Vorticity confinement | B | source-verified | — |
| `heightfield-shallow-water` | Height-field shallow water waves | B | source-verified | [`lib/pixelfx/fx/WaveRing.luau`](../../../lib/pixelfx/fx/WaveRing.luau) |
| `sph-fluids` | SPH particle fluids | B | source-verified | — |
| `position-based-fluids` | Position Based Fluids | B | source-verified | — |
| `flip-pic` | FLIP/PIC hybrid | B | source-verified | — |
| `metaballs` | Metaballs (blobby surfaces) | B | source-verified | — |
| `realtime-caustics` | Real-time caustics by area change | C | source-verified | — |
| `screen-space-refraction` | Image-space refraction (two interfaces) | C | source-verified | — |
| `parallax-occlusion-mapping` | Parallax occlusion mapping | C | source-verified | [`lib/surfacebake/Parallax.luau`](../../../lib/surfacebake/Parallax.luau) |
| `interior-mapping` | Interior mapping | C | source-verified | [`lib/surfacebake/Parallax.luau`](../../../lib/surfacebake/Parallax.luau) |
| `thin-film-iridescence` | Thin-film iridescence (Airy, pre-integrated) | C | source-verified | — |
| `schlick-fresnel` | Schlick Fresnel approximation | C | source-verified | — |
| `disney-principled-brdf` | Disney principled BRDF (clearcoat, anisotropy, sheen) | C | source-verified | — |
| `ggx-microfacet` | GGX microfacet distribution | C | source-verified | — |
| `sh-irradiance` | Spherical harmonic irradiance (9 coefficients) | C | source-verified | — |
| `gray-scott` | Gray-Scott reaction-diffusion | D | source-verified | — |
| `physarum` | Physarum transport networks (agent-based) | D | source-verified | [`lib/pixelfx/fx/Physarum.luau`](../../../lib/pixelfx/fx/Physarum.luau) |
| `worley-noise` | Worley / cellular (Voronoi) noise | D | source-verified | [`lib/surfacebake/Noise.luau`](../../../lib/surfacebake/Noise.luau) |
| `domain-warping` | Domain warping | D | source-verified | [`lib/surfacebake/Noise.luau`](../../../lib/surfacebake/Noise.luau) |
| `curl-noise` | Curl noise | D | source-verified | — |
| `gabor-noise` | Sparse Gabor convolution noise | D | source-verified | — |
| `flow-maps` | Flow maps | D | source-verified | — |
| `wavelet-noise` | Wavelet noise | D | source-verified | — |
| `improved-perlin-noise` | Improved Perlin noise | D | source-verified | — |
| `msdf` | Multi-channel signed distance fields (MSDF) | E | source-verified | — |
| `jump-flooding` | Jump flooding algorithm (JFA) | E | source-verified | [`lib/pixelfx/fx/JumpFloodOutline.luau`](../../../lib/pixelfx/fx/JumpFloodOutline.luau) |
| `valve-sdf-text` | Alpha-tested distance-field magnification (Valve) | E | source-verified | — |
| `smooth-min` | Smooth minimum (smooth union) | E | source-verified | [`.claude/skills/shaders-and-sdf/examples/Sdf.luau`](../../../.claude/skills/shaders-and-sdf/examples/Sdf.luau) |
| `felzenszwalb-edt` | Exact Euclidean distance transform (Felzenszwalb-Huttenlocher) | E | source-verified | [`lib/frontier/fx/RadianceCascades.luau`](../../../lib/frontier/fx/RadianceCascades.luau) |
| `critically-damped-spring` | Critically damped spring (damper) | F | source-verified | — |
| `framerate-independent-damping` | Frame-rate independent damping (exponential lerp) | F | source-verified | — |
| `minimum-jerk` | Minimum-jerk trajectory | F | source-verified | — |
| `ruckig-jerk-limited` | Jerk-limited time-optimal trajectories (Ruckig) | F | source-verified | — |
| `taa` | Temporal anti-aliasing / supersampling | F | source-verified | — |
| `fabrik` | FABRIK inverse kinematics | F | source-verified | [`lib/pixelfx/fx/FabrikChain.luau`](../../../lib/pixelfx/fx/FabrikChain.luau) |
| `dla` | Diffusion-limited aggregation | G | source-verified | [`lib/pixelfx/fx/FrostDLA.luau`](../../../lib/pixelfx/fx/FrostDLA.luau) |
| `dielectric-breakdown` | Dielectric breakdown model (Lichtenberg figures) | G | source-verified | [`lib/pixelfx/fx/Lichtenberg.luau`](../../../lib/pixelfx/fx/Lichtenberg.luau) |
| `kim-lin-lightning` | Fast lightning on adaptive grids | G | source-verified | — |
| `ribbon-trails` | Ribbon / trail strips | G | source-verified | — |
| `boids` | Boids flocking | G | source-verified | — |
| `oklab` | OKLab perceptual colour space | H | source-verified | [`.claude/skills/hierarchy-audit/examples/Perceptual.luau`](../../../.claude/skills/hierarchy-audit/examples/Perceptual.luau) |
| `apca` | APCA contrast (Accessible Perceptual Contrast Algorithm) | H | source-verified | [`.claude/skills/hierarchy-audit/examples/Perceptual.luau`](../../../.claude/skills/hierarchy-audit/examples/Perceptual.luau) |
| `ciede2000` | CIEDE2000 colour difference | H | source-verified | — |
| `itti-koch-saliency` | Itti-Koch-Niebur saliency map | H | source-verified | [`tools/hierarchy/hierarchy.py`](../../../tools/hierarchy/hierarchy.py) |
| `machado-cvd` | Machado colour vision deficiency simulation | H | source-verified | [`.claude/skills/hierarchy-audit/examples/Perceptual.luau`](../../../.claude/skills/hierarchy-audit/examples/Perceptual.luau) |
| `wcag-flash` | WCAG 2.3.1 flash thresholds | H | source-verified | [`tools/hierarchy/hierarchy.py`](../../../tools/hierarchy/hierarchy.py) |
| `dirty-rectangles` | Dirty rectangles / cached cell rendering | I | source-verified | [`lib/frontier/IndexedFrame.luau`](../../../lib/frontier/IndexedFrame.luau) |
| `rect-bin-packing` | Rectangle bin packing for texture atlases | I | source-verified | [`lib/frontier/Atlas.luau`](../../../lib/frontier/Atlas.luau) |
| `dynamic-resolution` | Dynamic resolution rendering | I | source-verified | — |
| `spatial-hashing` | Spatial hashing for neighbour queries | I | source-verified | [`lib/pixelfx/fx/Crowd.luau`](../../../lib/pixelfx/fx/Crowd.luau) |
| `wave-function-collapse` | Wave function collapse | J | source-verified | — |
| `poisson-disk-bridson` | Fast Poisson disk sampling (Bridson) | J | source-verified | [`.claude/skills/procedural-world/examples/Poisson.luau`](../../../.claude/skills/procedural-world/examples/Poisson.luau) |
| `greedy-meshing` | Greedy meshing for voxels | J | source-verified | — |
| `marching-cubes` | Marching cubes / marching squares | J | source-verified | [`lib/frontier/mesh/ContourMesh.luau`](../../../lib/frontier/mesh/ContourMesh.luau) |
| `dual-contouring` | Dual contouring of Hermite data | J | source-verified | — |
| `surface-nets` | Naive surface nets | J | source-verified | — |
| `cellular-automata-caves` | Cellular-automata cave generation | J | source-verified | [`lib/pixelfx/fx/CaveCA.luau`](../../../lib/pixelfx/fx/CaveCA.luau) |
| `blackbody-color` | Blackbody colour temperature to RGB (fitted) | X-other | source-verified | — |
| `diffraction-shader` | Diffraction shaders (gratings, CD sheen) | X-other | source-verified | — |
| `opal-play-of-colour` | Opal play-of-colour (stratified structural colour) | X-other | source-verified | — |
| `gravitational-lensing` | Gravitational lensing (ray-bundle renderer) | X-other | source-verified | — |
| `rosensweig-instability` | Rosensweig (normal-field) ferrofluid instability | X-other | source-verified | — |
| `radiance-cascades` | Radiance cascades (2D global illumination) | X-other | source-verified | [`lib/frontier/fx/RadianceCascades.luau`](../../../lib/frontier/fx/RadianceCascades.luau) |
| `voxel-space` | Voxel Space heightmap terrain | X-other | source-verified | [`lib/frontier/fx/VoxelSpace.luau`](../../../lib/frontier/fx/VoxelSpace.luau) |
| `void-and-cluster` | Void-and-cluster blue-noise dither arrays | X-other | source-verified | [`lib/pixelfx/fx/BlueNoiseDissolve.luau`](../../../lib/pixelfx/fx/BlueNoiseDissolve.luau) |
| `bayer-dither` | Bayer ordered dithering | X-other | unverified-source | [`lib/pixelfx/fx/PaletteDither.luau`](../../../lib/pixelfx/fx/PaletteDither.luau) |
| `phyllotaxis-vogel` | Vogel phyllotaxis spiral | X-other | source-verified | [`lib/pixelfx/fx/Phyllotaxis.luau`](../../../lib/pixelfx/fx/Phyllotaxis.luau) |

## How to add an entry

1. Search for the original source and confirm title, authors, year and a URL you actually saw. If you can't, set `verification` to `unverified-source` and `url` to `null`.
2. Add an object to `methods.json` with every key used above. Give it a stable kebab-case `id`; never rename an existing id.
3. Write `principle` as the actual maths, `roblox_fit` honestly (say "bake offline" when per-frame Luau is too heavy), and list `combos` by id.
4. Grep `lib/`, `.claude/skills/` and `tools/` for the method. Record the path in `implemented_in_kit` or leave `no`.
5. Add a row to the table above, then run `python3 docs/algorithm-vault/external/test_external.py` until it prints `0 errors`.
