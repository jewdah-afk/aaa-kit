# Contrast, colour and colour blindness: the numbers

Part V, Hierarchy science. Readable text, colour that keeps its job for every player, and value that holds the hierarchy when hue is gone. All of it is computed by `tools/hierarchy/hierarchy.py` (Python) and `Perceptual.luau` (in game) in the [hierarchy-audit skill](../../.claude/skills/hierarchy-audit/SKILL.md).

## Takeaway

Measure lightness contrast with **APCA** (polarity-aware, tuned to text size) and colour differences in **OKLab**. Check every colour code under a **deuteranopia simulation**, because about 1 in 12 boys sees red and green as close. Hierarchy has to survive in grey first. Hue is a second channel, never the only one.

## 1. Text and icon contrast: APCA Lc

**Findings**
- APCA ("Advanced Perceptual Contrast Algorithm") gives a lightness contrast **Lc** of about −108 to +106. It is signed: positive means dark text on a light background, negative means light on dark. The two polarities aren't symmetric: black on white is Lc 106.0, while white on black is −107.9. Our implementation follows the reference `apca-w3` 0.0.98G-4g constants (TRC 2.4; exponents 0.56/0.57 normal, 0.62/0.65 reverse; scale 1.14; offset 0.027; black soft clamp at 0.022 with exponent 1.414). ([apca-w3 source](https://github.com/Myndex/apca-w3); [APCA introduction](https://github.com/Myndex/apca-introduction))
- The simple conformance ladder (ARC "Bronze", still in beta) uses these levels:

| abs(Lc) | Use |
|---|---|
| 90 | Preferred for body text |
| 75 | Minimum for body text |
| 60 | Other content text (about 16 px and up, or 24 px normal weight) |
| 45 | Large headlines (about 36 px), large non-text such as icons |
| 30 | Minimum for any text that isn't meant to be read fluently (placeholders, disabled), and for spot non-text elements |
| 15 | Below this, some people can't see the element at all; use only for dividers that don't matter |

  ([ARC Bronze simple mode](https://a11yreadtech.github.io/ARC/tests/bronze-simple-mode); [ARC readability tests](https://a11yreadtech.github.io/ARC/tests/visual-readability-contrast)). The pixel-size bands differ between secondary sources. Treat the size column as approximate. **UNKNOWN — check the ARC repo for final bands.**
- **WCAG 2.x ratio** for reference: 4.5:1 for normal text, 3:1 for large text and non-text UI. It's symmetric, and it is known to rate dark-mode pairs poorly. Mid-grey `#888` on white is APCA Lc 63.1 but WCAG 3.54:1. Both are reported by `hierarchy.py apca`.

**Rules for us**
1. **Numbers the player reads during play** (currency, HP, timers, damage) need abs(Lc) ≥ 75 against the *worst* background they can appear on. Damage numbers over bright VFX need an outline or shadow that guarantees it.
2. **Labels and secondary text** need abs(Lc) ≥ 60. Disabled or locked text needs abs(Lc) ≥ 30. Disabled means quieter, not invisible.
3. **Contrast is a hierarchy tool.** Give tier 3 HUD text the highest Lc on screen. Ambient tier 4–6 world text stays below the HUD's Lc so it never competes.
4. **Dark UI:** design dark-mode pairs in Lc directly. The 4.5:1 ratio over-rates light-on-dark mid-greys.

## 2. Perceptual colour: OKLab

**Findings**
- OKLab (Ottosson, December 2020) is a perceptually uniform space with CIELAB's layout: L from 0 (black) to 1 (white), plus opponent axes a (green–red) and b (blue–yellow). It goes linear sRGB → LMS (M1) → cube root → Lab (M2). It predicts lightness and hue better than CIELAB, and its cylindrical form OKLCH is in CSS Color 4. ([Ottosson, "A perceptual color space for image processing"](https://bottosson.github.io/posts/oklab/); [Oklab, Wikipedia](https://en.wikipedia.org/wiki/Oklab_color_space))
- Euclidean distance in OKLab works as a ΔE: about 0.02 is a just-visible difference for neighbouring patches. This is an estimate used in colour tooling, not a published threshold. **[UNVERIFIED]**

**Rules for us**
1. **The figure-ground gate (HIERARCHY §11)** is measured in OKLab L. Threats and rewards must sit outside the background's L band. The auditor's squint value gap must be ≥ 0.08 OKLab L. That's a house threshold, set so the gap survives a 1%-of-diagonal blur.
2. **The rarity ladder (HIERARCHY §7)** must climb in L and chroma as well as hue. Each step needs ΔL ≥ 0.05 or Δchroma ≥ 0.04 from its neighbours (house thresholds), so rarities stay ordered in grey and under colour blindness.
3. **Interpolate gradients and tweens in OKLab or OKLCH.** sRGB tweens between complementary colours pass through mud. `Perceptual.luau` exposes `oklab` and `mixOklab`.

## 3. Colour blindness

**Findings**
- About **8% of men and 0.5% of women** have a colour vision deficiency. Commonly cited ranges run 5–8% of men and under 1% of women. The red-green types dominate, and **deuteranomaly is the most common** (about 5% of men). ([All About Vision](https://www.allaboutvision.com/conditions/color-blindness/color-deficiency/); [News-Medical](https://www.news-medical.net/health/Color-Blindness-Prevalence.aspx))
- Machado, Oliveira & Fernandes (2009) model normal vision, anomalous trichromacy and dichromacy with one physiologically based method. It is a single 3×3 matrix per type and severity, with pre-computed matrices at severity steps of 0.1. ([IEEE TVCG 15(6)](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html)) Current implementations, such as R `colorspace` ≥ 2.0-3, apply the matrices to **linear** RGB. ([colorspace::simulate_cvd](https://rdrr.io/cran/colorspace/man/simulate_cvd.html))

**Rules for us**
1. **Never encode with hue alone.** Every colour code (team, rarity, damage type, affordable vs not) is paired with value, shape, icon or position. "Green = can buy, red = can't" also needs a lock icon or a dimmed card.
2. **Run the deutan and protan check on every main screen.** The auditor re-runs the first fixation under both and warns when the focus loses.
3. **Pairs that collapse:** red/green and orange/lime under deutan and protan, blue/purple under protan, yellow/white under tritan (rare). Separate them in OKLab L.
4. Roblox has no system colour-blind filter. **Offer a setting** that swaps the rarity and team palettes for a CVD-safe set (`Perceptual.luau` can check a palette pair by pair).

## 4. Flashing: the hard safety limit

**Findings (WCAG 2.2 SC 2.3.1, "Three Flashes or Below Threshold")**
- A **flash** is a pair of opposing changes in relative luminance. A **general flash** is a pair of opposing changes of ≥ 10% of maximum relative luminance where the darker state is below 0.80. A **red flash** is a pair of opposing transitions to or from a **saturated red**: R/(R+G+B) ≥ 0.8, with a chromaticity change of more than 0.2 in CIE 1976 u′v′.
- Content passes if there are **no more than three general and three red flashes in any one-second period**, or if the flashing area is small: no more than 25% of any 10° visual field. That's a 341 × 256 px rectangle on a 1024 × 768 screen (87,296 px), and 25% of it is about 21,824 px, or **2.78% of the screen**. ([W3C Understanding 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html); [Technique G176](https://www.w3.org/WAI/WCAG21/Techniques/general/G176.html))

**Rules for us**
1. **This is the one hierarchy rule that is a safety rule.** Tier 1–2 impact frames, lightning and screen flashes are throttled to ≤ 3 per second whenever they cover more than 2.78% of the screen, whatever the intensity rung. HIERARCHY §9 already rate-limits; this sets the ceiling.
2. **Red is special.** Full-screen red damage vignettes that pulse are red flashes. Pulse them with value (darker and back) under 3 Hz, or keep them under the area limit.
3. **Check every captured effect:** `hierarchy.py flash effect.gif`. All 15 of our tier 5–6 GIFs pass. The per-pixel `--fine` mode flags `tier6-boids`, whose average frame luminance only moves 0.022–0.023: small moving particles, not a flash. That's why the default mode averages over blocks about 0.5° wide.
4. Respect `GuiService.ReducedMotionEnabled` ([chapter 63](63-incremental-game-ui-roblox.md)). When it's on, impact flashes become a value dip and shake drops to zero.

## 5. Gaps

- The APCA size bands are still beta, and the ARC and APCA documents may change. Pin to the version in `hierarchy.py`.
- No source gives a ΔE threshold for game-speed glances. Ours are house values, to be tuned with playtests.
- Flash analysis on game captures depends on the capture's frame rate. A 30 fps GIF can't show 20 Hz flicker. Capture at 60 fps for impact effects.
