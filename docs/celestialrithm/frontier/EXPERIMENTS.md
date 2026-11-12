# Experiment lineage: material foundry, iteration 1

Every round of the improvement loop: hypothesis, change, evidence, verdict. Evidence images are in [media/celestialrithm/frontier/lineage/](../../../media/celestialrithm/frontier/lineage/). Nothing here was promoted to production; the human gate is still open.

## Starting point

| What | Finding |
|---|---|
| Approved visual floor | `media/celestialrithm/approved-material-visual-target.gif`: 414×219, 16 frames at 110 ms (~9 fps), 12 squared keys |
| Existing engine code | `lib/celestialrithm/MaterialField.luau` and `examples/celestialrithm/t11/render.py`: sums of 2–3 sines per material. Below the floor. |
| Decision | Build a new reference renderer on real field methods (`tools/celestialrithm/foundry/`), then port winners to Luau |

## Rounds

| Round | Hypothesis | Change | Evidence | Verdict |
|---|---|---|---|---|
| 0 | Real methods (caustics, thin film, Planck, Worley, metaballs, Gray-Scott, Stam fluids, lightning, lensing, gratings) beat sine sums | 12 materials + SDF keycap shell | [round0-first-pass.jpg](../../../media/celestialrithm/frontier/lineage/round0-first-pass.jpg) | **Mixed.** Molten, void, nebula, slime readable. Fails: a full-width gloss band washed every face; bezels grey and heavy; solar read as brown marble; crystal, holo, opal read as stained glass; electric bolts sub-pixel; 1.2 s/frame |
| 1 | The wash is the gloss band; speed is noise cost | Gloss → thin clearcoat strip; inner glass rim in material colour; cached shell geometry (35 → 12 ms/key); half-res smooth fields, x-only fields on one row (nebula 310 → 83 ms) | [round1-gloss-and-speed-fix.jpg](../../../media/celestialrithm/frontier/lineage/round1-gloss-and-speed-fix.jpg) | **Better.** Coral labyrinth, crystal good. Still failing: clearcoat additive light reads grey on dark faces (linear-space addition is strong on near-black); solar beige |
| 2 | Physical Planck colours are too desaturated for the stylized palette; arcs need width in pixels, not face units | Solar: Planck sets hue order, a graded ramp sets the palette; electric: core width ×2.3, standing arcs (1.1 s life) + flickers; slime: tamed SSS | [round2 strips](../../../media/celestialrithm/frontier/lineage/round2-strips-solar-electric-slime.jpg) | **Pass** for solar, electric, slime: at or above the floor's equivalents |
| 3 | Caustics need sharper splat + larger focal depth; holo needs smooth, not per-cell, colour | Caustics sigma .45, depth 40; holo → high-order thin film on brushed silver + grating sparkle; opal → angle-selective domains | [round3 strips](../../../media/celestialrithm/frontier/lineage/round3-strips-caustics-holo-opal.jpg) | **Pass** for hydroglass (true caustic network) and holo. Opal acceptable |
| 4 | Prism film adds green mud; chrome needs high-contrast env; aurora rays must hang upward | Film only at Fresnel rims; studio-strip environment for chrome; aurora curtains flipped with altitude colour | [round4 strips](../../../media/celestialrithm/frontier/lineage/round4-strips-prism-chrome-aurora-ferro.jpg) | **Pass** prism, aurora; chrome needed one more pass (cow-print → soft horizon); ferrofluid acceptable, weakest of the 16 |
| 5 (QA) | Tests catch physics bugs that look plausible | `test_foundry.py` (113 checks) | see below | **3 real bugs found and fixed** |
| 6 | The press must read after the physics fix | Wave drop amplitude 2 → 5, wave share of height ×2 | breakdown reel | Press now reads as a refracted caustic ring |

## Batch B/E: Shop + Inventory hierarchy loop

Measured with `tools/hierarchy/hierarchy.py audit` on the t = 1.5 s frame, focus = the Legendary card and its BUY button (`--focus 304,151,232,373`). Reports and heat maps: [media/celestialrithm/frontier/hierarchy/](../../../media/celestialrithm/frontier/hierarchy/).

| Round | Change | First fixation | Lift (≥ 1.5) | Top competitor (< 0.9) | Squint gap (≥ 0.08) | Deutan / protan lift | Verdict |
|---|---|---|---|---|---|---|---|
| Control (`--no-hierarchy`) | Every card and BUY button loud | Mythic card | 1.37 | 1.99 | 0.003 | 1.20 / 1.06 | FAIL |
| H1 | Non-owner cards at 0.3× time, 80% → 62% exposure | Mythic potion icon | 1.31 | 1.48 | 0.027 | — | FAIL |
| H2 | Legendary halo behind the item + outer glow (rarity-ladder step); non-owner faces 42%, icons desaturated; inventory icons at 80% | HUD coin | 2.19 | 1.40 | 0.11 | — | FAIL |
| H3 | HUD coin calmer (36 px, 70% saturation, 85% value) | **Legendary BUY button** | **2.25** | **0.74** | **0.11** | **2.04 / 1.78** | **PASS** |

Lesson: saturated **icons** out-pulled every animated material. The dark molten owner lost on value until it got the halo the rarity ladder already prescribes for Legendary. This is a bottom-up model only (no meaning or goals); an owner review is still required.

## Bugs the tests caught (all fixed)

| Bug | Why it looked fine | Fix |
|---|---|---|
| Caustic displacement had the wrong sign: light diverged under convex water | Random water produces a caustic net either way | Small-angle Snell: displacement is `+depth·(1−1/n)·∇h`; a lens test checks focusing |
| `WaveSim.drop` gave every drop an upward initial velocity | Ripples still appeared | Drops add to both current and previous height (displacement only) |
| Stable-fluid projection left divergence (0.80 → 0.51 only) | Smoke still swirled | Poisson solve uses the stencil that matches central-difference div/grad (checkerboard mode) |
| Gray-Scott died on small grids, so coral ignored press | Board-size faces were fine | Denser nucleation + automatic re-seed when the pattern dies |
| Press barely changed prism gel and crystal at peak hold | Visible only during the ramp | Inner gel light on press; lit fracture net at peak |
| Python `hash()` seeded noise: different every process | Each render looked fine alone | `zlib.crc32` of the material id |

## Not yet tried (next iteration)

See the frontier [README](README.md#next-iteration).
