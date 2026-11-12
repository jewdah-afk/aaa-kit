# T12–T14+ implementation-oriented examples

Every example below is a **candidate architecture**, not an already benchmarked feature. It gives the mathematical composition, the screen action, how it maps to `aaa-kit` and how to falsify the result.

## 1. Hydrogel pressure lens
**Ingredients:** XPBD distance constraints + damped wave equation + slope specular + jump-flood SDF + key drop + protected region.

At each substep, predict membrane points `p_i* = p_i + dt*v_i + dt²*g`. For each edge constraint `C = |p_i-p_j|-L`, compute compliant XPBD correction `Δλ = (-C - α~ λ) / (Σ w_i |∇C_i|² + α~)`, where `α~ = α / dt²`. Keep face boundary anchored and correct pressure into its interior. Compute `n ∝ (-∂h/∂x, 1, -∂h/∂y)` for the caustic/clearcoat field, clipped away from icon/text. Entire key face/body descend together.

**Build:** pure Luau solver → fixed topology `EditableMesh:SetPosition` → one atlas region rendered from gradient field → GUI icon/text above it. **Test:** stress 20 quick taps; no tearing, no duplicate glyph edges, stable contour, CPU frame budget.

## 2. Prism memory
**Ingredients:** spring network + reaction diffusion field + thin-film approximation + MSDF corners + one edge charge + voice-priority chime.

Integrate Gray-Scott state using `∂u/∂t = D_u ∇²u - uv² + F(1-u)`, `∂v/∂t = D_v ∇²v + uv² -(F+k)v`. Press deposits small reagent pulse. Use `v` to vary *under-face* hue and facet-light direction. Limit activity to an interaction window; decay to baseline before idle. **Test:** static frame identity, icon contrast, clear rarity color and 30/60 FPS fallback.

## 3. Stylized water caustics without screen-space refraction
**Ingredients:** 2D wave solver + surface gradient + approximate caustic Jacobian + OKLab palette snapping.

Let `q(x,y)=(x,y)+κ∇h(x,y)` be refractive UV mapping. Brightness approximately varies with `1 / max(ε, |det(∂q/∂(x,y))|)` but clamp, smooth, limit spatial extent and temporally damp. Reproject into one atlas region. This is a stylized approximation, not ray-traced water. **Test:** no pathological white flashing, clear glyph contrast and energy budget.

## 4. Flat-but-deep square key
**Ingredients:** image-to-voxel tracing (licensed or reimplemented) + greedy voxel meshing + morph target / spring underlip + SDF precise ink.

Trace the **silhouette only** to generate a shallow underlayer with discrete tessellated bevel. Keep the painted icon as stable foreground. Use signed distance for outer edges and a black 4px stroke. **Test:** 32px icon readability, no extra black line when the whole key drops; verify no face-only sinking.

## 5. Self-improving render tournament
**Ingredients:** candidate recipe generation + deterministic seed + screenshot hierarchy auditor + APCA + flash safety + measured performance + human pick.

For one existing button create 16 candidates varying membrane compliance, wave damping, refractive strength and border coverage. Save previews and `metrics.csv`. Reject all that fail shape fidelity, icon contrast, flashing rules, frame cost. Rank remaining with reviewer scores. Continue mutations from the top *three diverse candidates*, not only the highest bloom score. Require versioned approval and a golden-frame regression before adopting.

## 6. Multi-scale synthesis and downgrade
**Ingredients:** Atlas + Uploader + IndexedFrame + limited mesh updates + clean fallback.

Use one 512² shared atlas containing 64–128px regions for keycaps, 16×16 dirty cells and a single upload scheduler. A phone-low rung can use static baked caustics + GUI press + 15Hz animated field, while phone-mid can update fields at 30Hz and desktop at 60Hz if measured budgets permit. The render remains 60 FPS even when field simulation updates less often. These are *targets* and must be profiled.

## 7. Rarity morph without color chaos
**Ingredients:** material presets + progressive constraints + rarity ladder + one motion new per rung.

Common is quiet, Rare gains one bright sweep, Epic gains a moving facet response, Legendary adds a finite spark event, Mythic grants a ceremony. Keep color jobs consistent and never animate every rarity card just because the algorithm can.

## 8. Audio-matched elastic surface
**Ingredients:** damped oscillator + force envelope + multi-component synthesized cue + mix priority.

From `x'' + 2ζωx' + ω²x = F(t)`, map first downward acceleration to a short contact transient, displacement peak to a body note and rebound velocity to a short release chirp. Gate one sound event by the UI bus; duck/steal lower-priority voices. Reduced-motion uses a soft value dip without excessive sound.

## 9. Faceted-to-gel phase material
**Ingredients:** voxel shell + deformation heightfield + smooth union + normal quantization + palette interpolation.

Instead of morphing button outline, interpolate *internal* facet normal scale from hard glass to gel while the squared rim is rigid. `n(t)=normalize(mix(n_faceted,n_smooth,smoothstep(t)))`. A tiny particle event marks phase change. **Test:** ink shape stable, press and rebound still visible, no static-layout jump.

## 10. Pressure-guided particle relief
**Ingredients:** pressure map + SDF boundary + phyllotaxis emission + short damping + ownership stencil.

Spawn a bounded ring of 12–24 microflecks at release with angular position `θ_i = i*2.399963...` and initial velocity weighted by the pressure normal. Kill within 200–350 ms and never draw over the icon. **Test:** clutter and flash checks.

## 11. Adaptive hierarchy gate
**Ingredients:** salience maps + prior design tokens + focus lock + temporal reservation.

Give every panel one `attentionOwner`. Assign accent budget only if `owner == hovered/selected/primary`. During a reward, lower neighboring effects; after 200 ms, restore calm. *Don't predict eye movements from unvalidated proxies.* Compare predicted scanpaths to human first-click tests before learning weights.

## 12. Reproducible algorithm search
**Ingredients:** source provenance + formula + bound parameters + compatibility + tests + review status.

`query.py` finds source-backed methods; `ingest_repo.py` discovers new current repo modules and numbered ideas; generated recipes are proposals until `evolve.py` receives measured evidence. Never silently elevate a candidate to shipped or use a generated estimate as a benchmark.
