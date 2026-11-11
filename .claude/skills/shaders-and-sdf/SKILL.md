---
name: shaders-and-sdf
description: Use for shader-style maths - signed distance fields (2D and 3D), raymarching, smooth unions, noise (value, gradient, fBm, domain warping), thin-film and iridescence, Fresnel, lensing and refraction, dithering, and how to get the same looks in Roblox where there are no custom shaders (EditableImage, UIGradient, layered images, baked textures). Triggers on "shader", "SDF", "signed distance", "raymarch", "GLSL", "noise", "fbm", "thin film", "iridescent", "refraction", "dither".
---

# shaders-and-sdf

Roblox has no custom shaders. This skill gives you the maths, then the three ways to get that maths on screen in Roblox: compute it into an EditableImage, fake it with stacked UI primitives, or bake it into a texture.

## When to use

- Procedural shapes with soft edges, glows and outlines (UI panels, rings, blobs)
- Noise-driven looks (clouds, fire, dissolves, terrain)
- Web labs and prototypes in GLSL

**Not for:** which material to use per rarity (`materials`) or when an effect should play (`vfx`).

## Method

1. **Write the look as a distance function first.** Shapes are `d(p)`: negative inside, positive outside. Combine with `min` (union), `max(a, -b)` (subtract) and `smin` (smooth union).
2. **Get everything else from `d`.** Fill = `clamp(0.5 - d, 0, 1)` (1 px AA). Outline = `abs(d) - w/2`. Glow = `(1 - d/r)^2` outside. Shadow = sample `d` offset by the light direction.
3. **Add noise only where needed.** fBm with 4–6 octaves; domain warp (`p + k * noise(p)`) for organic motion. Hash-based noise keeps it seedable.
4. **Pick the Roblox path:**

| Need | Roblox path |
|---|---|
| Animated, per-pixel, ≤ 256² area | Compute into an EditableImage (CPU, `buffer` writes) |
| Static shape, any size | Bake once to an EditableImage or upload a texture |
| Gradients, rings, sweeps on UI | `UIGradient` + `UIStroke` + `UICorner` (no pixels) |
| 3D surfaces | `SurfaceAppearance` + baked maps; `Beam` textures for energy |

5. **Budget CPU pixels.** At ~0.1 µs per simple pixel in the interpreter, a 128² SDF panel costs ~1.6 ms. Update it at 30 Hz or only when it changes.
6. **Web.** One full-screen triangle and a fragment shader. Clamp loop counts and early-out on distance.
7. Run the self-check.

### GLSL ↔ Luau cheat sheet

| GLSL | Luau |
|---|---|
| `length(p) - r` | `math.sqrt(x*x + y*y) - r` |
| `clamp(x, a, b)` | `math.clamp(x, a, b)` |
| `mix(a, b, t)` | `a + (b - a) * t` |
| `smoothstep(a, b, x)` | `local t = math.clamp((x-a)/(b-a), 0, 1); t*t*(3-2*t)` |
| `fract(x)` | `x - math.floor(x)` |
| `pow(1. - dot(n, v), 5.)` (Fresnel) | `(1 - dot) ^ 5` |

## Hierarchy rules it obeys

- §2: a shader is a tool, so its tier is the tier of whatever it draws.
- §6: animated fields idle slowly or not at all at the calm rung.
- §11: SDF outlines are the cheapest way to pass the figure-ground gate (a 1–2 px darker ring).

## Engine notes

- **Roblox:** `math.noise` is Perlin in [-1, 1] (approx.); remap with `* 0.5 + 0.5`. Native codegen (`--!native`) helps inner loops in Studio, but live clients may run interpreted, so measure both.
- **Thin-film / iridescence:** hue = `fract(k * thickness * cosθ)` run through a spectral palette. In Roblox UI, approximate it with a rainbow `UIGradient` whose `Offset` follows the tilt.
- **Dithering:** an ordered Bayer 8×8 threshold keeps hard pixels for pixel art, and interleaved gradient noise works for smooth gradients.

## Example

`examples/Sdf.luau` provides circle, rounded box, ring, union, subtract, smooth union, AA coverage, glow and a rasteriser into an 8-bit alpha buffer (tested in `examples/Sdf.test.luau`). The WebGL raymarcher (smooth-union blobs, soft shadows, AO) is the SDF tile in [effects-gallery.html](../../../examples/web/effects-gallery.html).

```lua
local Sdf = require("./examples/Sdf")
-- a 96x32 pill button with a 2 px ring, rasterised once (bake it, don't redraw per frame)
local alpha = Sdf.rasterize(96, 32, function(x, y)
	local d = Sdf.roundBox(x - 48, y - 16, 46, 14, 14)
	return Sdf.union(d, Sdf.ring(x - 48, y - 16, 10, 2))
end)
```

## Make it insane

1. **Metaball HUD:** health orbs that merge with `smin` as they fill and split with a stretch when you take damage, rendered in a 128² EditableImage at 30 Hz.
2. **Lensing portal:** a Mythic reveal backdrop that bends the scene behind it (sample offset = `normalize(p) * k / d`), with a thin-film rim.
3. **SDF fonts:** baked distance-field glyphs give crisp outlines, glows and drop shadows at any scale from one small texture.

## Self-check

- [ ] Every shape is a distance function; fills, outlines and glows derive from it.
- [ ] CPU pixel cost measured; animated fields capped at 30 Hz or on-change.
- [ ] Static results are baked, not recomputed.
- [ ] Loops are bounded (raymarch steps, octaves).
- [ ] The Roblox fallback is chosen and noted for every web-only technique.
