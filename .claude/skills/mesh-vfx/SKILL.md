---
name: mesh-vfx
description: Use when an effect needs authored geometry instead of (or under) particles - anime sword slashes, crescent arcs, shockwave rings and cones, tornado/vortex columns, energy shells, debris chunks, scrolling-texture meshes, Blender-to-Roblox VFX pipelines, flipbooks and baked noise textures. Triggers on "mesh vfx", "slash effect", "sword slash", "crescent", "shockwave mesh", "vortex mesh", "blender vfx", "uv scroll", "flipbook", "bake a texture for vfx".
---

# mesh-vfx

Authored meshes give an effect a silhouette particles can't: a crisp crescent, a ring that expands with perspective, a twisting column. Mesh VFX are tier 2 (HIERARCHY.md §2) on hits and casts, tier 1 only for a reveal or ultimate. Every mesh effect names its rungs: full on Hero, mesh plus 1 emitter on phone, a single decal or nothing on Crowd/Far.

## When to use

- A shape must read in one frame (slash arc, impact ring, pillar) and particles would look like soup.
- An effect needs perspective and depth that flat sprites fake badly.
- You are turning a Blender or "AAA VFX pipeline" spec into Roblox. Run its claims through the reality checks below first.

## Method

1. **Timeline first.** Write beats in seconds before modelling: anticipation (0–0.15), impact frame (0.15–0.22, hold 2–4 frames), expansion (0.22–0.85), dissipation (0.85–1.2). The impact frame gets the brightest value; everything else is dimmer.
2. **Layer stack (outside in).** Shell (soft, wide, low alpha) → body (the crescent / ring) → core (thin, white-hot, or black for a dark tear) → secondary (sparks, debris) → light (one PointLight pulse). At most 3 mesh layers and 2 emitters per effect.
3. **Generate the meshes.** `python3 scripts/meshgen.py crescent|shell|shockwave|vortex|debris out.obj`. Straight grid UVs (u along the length, v across), 3% inset, per-vertex mask colour. Budget: 80–800 tris per mesh. In Blender, `scripts/blender_gen.py` builds the crescent with modifiers and exports FBX. No Blender install needed: `python3.13 -m venv bpyenv && bpyenv/bin/pip install bpy`, then `bpyenv/bin/python scripts/blender_gen.py -- out.fbx` (Cycles CPU renders also work; needs libegl1).
3b. **Whole pipeline in Blender:** `bpyenv/bin/python scripts/blender_pipeline.py -- OUT 45 480` builds every shape, exports an FBX per shape, bakes the flame with Blender nodes and renders the slash in Cycles (with Fog Glow bloom). About 1 minute for 45 frames on CPU. See `examples/slash_cycles.gif`.
4. **Bake textures.** `python3 scripts/texbake.py flame|streaks|flipbook out.png` makes white RGB + alpha, tileable, so Color tints them in Studio. One 512² per family; flipbooks are 4×4 at 1024².
5. **Animate in Roblox.** Use TweenService on Size, CFrame and Transparency (examples/slash_controller.luau). Scrolling is done with a Beam (`TextureSpeed`) laid along the mesh, or by swapping flipbook frames on a SurfaceAppearance-free Texture/Decal offset (`OffsetStudsU/V` on a `Texture`).
6. **Glow.** Material Neon with Bloom does the work for bright layers. Dark layers are ForceField or SmoothPlastic, never black Neon.
7. **Pool and clean up.** Clone from a template folder, reuse it, and `Debris`/pool it back after the last tween ends.

### Reality checks (common wrong claims in generated pipelines)

| Claim | Truth in Roblox |
|---|---|
| "MeshPart.LightEmission" | Doesn't exist. LightEmission is on Beam/ParticleEmitter/Trail. Meshes glow via Neon + Bloom. |
| "LightEmission = -1 for black voids" | Only valid on beams/particles and still can't make true black glow. Use an opaque dark ForceField layer in front. |
| "Scroll the UVs of a MeshPart" | No UV offset on MeshPart. Use a Beam's TextureSpeed, a `Texture` instance's OffsetStudsU/V, or EditableImage frames. |
| "InvertColor screen effect" | Doesn't exist. ColorCorrectionEffect (Saturation -1, Contrast high, TintColor) or a full-screen Frame for 1–2 frames. |
| "Export FBX at 0.01 scale" | Check it: the importer reads the file's units. Model at 1 unit = 1 stud and confirm the size after import. |
| "Vertex colours drive the alpha" | Treat vertex-colour import as unverified. Bake the gradient into the texture alpha instead. |
| "Noise scale 6.5, detail 8, Voronoi 8" on a 0–1 UV | Renders as TV static at game sizes. Start at noise 2.5 / detail 4 / Voronoi 3 and look at the result. |
| "Transparent meshes sort fine" | They don't always. Use DoubleSided only where needed, and an inverted inner shell 0.005 inward. |

## Hierarchy rules

- The impact frame is the only moment at full brightness; shell and secondaries stay ≥ 30% dimmer.
- One mesh effect owns its pixels at a time; overlapping slashes cap at 2 live copies per player.
- Calm by default: no mesh loops at rest except a selected item's slow idle.
- Phone rung: drop the shell and debris first, keep the body silhouette.

## Engine notes

- MeshPart: `CanCollide/CanQuery/CanTouch = false`, `CastShadow = false`, `Anchored = true`, and no physics welds for VFX.
- Size tweens rescale the mesh along its local axes, so put the swing pivot at the origin (meshgen does).
- Transparency on MeshParts animates cheaply; Color3 tweens are fine; CFrame tweens of 3 parts per effect are trivial.
- Tri budget per live effect: 2,000 on desktop, 800 on phone.
- Textures uploaded as images need a moderation pass; keep them abstract.

## Example

`examples/slash_controller.luau`: crescent body + inverted core + shockwave ring, beat by beat, with the phone rung dropping the shell. Generate the assets with:

```sh
python3 scripts/meshgen.py crescent slash_body.obj --bend 210 --mask core
python3 scripts/meshgen.py shell slash_shell.obj
python3 scripts/meshgen.py shockwave ring.obj
python3 scripts/texbake.py flame flame.png
python3 scripts/test_meshvfx.py
```

## Make it insane

- **Void Singularity** (`scripts/blender_singularity.py`, `examples/void_singularity_cycles.gif`): real gravitational lensing in Cycles (Refraction BSDF IOR 0.72 sphere around a black horizon bends the starfield), an accretion disc tilted only ~14° so it reads edge-on (face-on reads as a target), polar jets, debris stretched along its fall. Roblox has no refraction: fake the lens with a dark ForceField shell.

- **Eclipse Vortex ultimate** (`scripts/blender_vortex.py`, `examples/eclipse_vortex_cycles.gif`): twisted flame column + counter-spinning core + thin helix ribbons + black eclipse disc with burning corona, sparks that gather inward then ride the column, rising debris. Lesson from the first render: bright helix ribbons blow out to white and read as a spring. Keep accents thin and dimmer than the flame body.

- **Dark-core tear:** a black ForceField crescent inside a Neon rim, for 2 frames only, reads as reality ripping.
- **Echo slashes:** 2 delayed copies at 60% and 30% alpha, scaled 1.05 and 1.1 (cheap motion blur).
- **Vortex column:** a twisted cylinder with a Beam spiral riding it, plus the TextureSpeed flame.
- **Debris with real facets:** a flat-shaded icosphere chunk, 3–6 pieces, on a projectile arc with spin.
- **Camera beat:** 2-frame FOV punch (-4) on the impact frame only.

## Self-check

- [ ] Timeline written with an impact frame, and only that frame is at full brightness
- [ ] Every mesh under its tri budget (meshgen stats JSON) with UVs inset (test passes)
- [ ] No claim from the reality-check table used wrong (no MeshPart LightEmission, no UV scroll on MeshPart)
- [ ] Rungs named: Hero / phone / Crowd behaviour
- [ ] Pooled or cleaned up; nothing collides or casts shadows
- [ ] Not tested in Studio unless you say so
