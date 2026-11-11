# Grouping, density and choice

Part V, Hierarchy science. This chapter covers layout: what the eye joins together, how much one screen can hold, how many choices it can offer, and how big a target must be. The HUD-specific survey is [chapter 70](70-game-hud-hierarchy.md); phone layout is [chapter 63 §7](63-incremental-game-ui-roblox.md#74-safe-areas-and-the-top-bar).

## Takeaway

Group with **enclosure and connection first, proximity second, similarity last**. Show **about four chunks** at a glance. Every extra option costs decision time, roughly log2(n+1). Keep the background around important elements low in clutter, so they pop without getting louder.

## 1. Grouping (Gestalt, measured)

**Findings**
- **Common region** (Palmer 1992): elements inside one bounded area group together, and this can't be reduced to proximity or closure. **Element connectedness** (Palmer & Rock 1994): elements sharing a border group together. **Uniform connectedness**, a connected region of one colour, texture or motion, is proposed to come *before* the other groupings. ([Palmer, Berkeley](https://palmerlab.berkeley.edu/pdf/Palmer.pdf); [Han, Humphreys & Chen 1999](https://typeset.io/pdf/uniform-connectedness-and-classical-gestalt-principles-of-3m33wfdvud.pdf))
- In one hierarchical-stimulus study, common region **dominated** connectedness. Grouping by **proximity** is reached **faster** than grouping by similarity of luminance or shape (Ben-Av & Sagi 1995; Han 2004). ([Razpurker-Apfeld & Kimchi 2007](https://iipdm.haifa.ac.il/images/publications/Rutie_Kimchi/Razpurker-Apfeld%20and%20Kimchi_2007_P&P.pdf); [Kubovy & van den Berg review](https://researchgate.net/profile/Michael-Kubovy/publication/230587594_A_Century_of_Gestalt_Psychology_in_Visual_Perception_I_Perceptual_Grouping_and_Figure-Ground_Organization/links/00b7d525ff3a85b71f000000/A-Century-of-Gestalt-Psychology-in-Visual-Perception-I-Perceptual-Grouping-and-Figure-Ground-Organization.pdf))

**Rules for us**
1. **Panels (common region) are the strongest grouping tool, so spend them carefully.** One card holds one item's price, icon, name and buy button. Never let a button sit on the border between two cards.
2. **Space within a group must be clearly smaller than space between groups.** The house ratio is 1 : 2 or more (for example 8 px inside a card, 16–24 px between cards). Proximity is the fastest cue, so a broken ratio is the first thing players misread.
3. **Similarity (same colour or shape) means "same kind", not "same group".** Use it to say "all of these are currencies", never to hold a layout together.
4. **A uniform field is one object.** A row of identical locked cards reads as one grey block; that's good for locked content and bad for things the player should compare.

## 2. How much fits in one glance

**Findings**
- Cowan (2001): the central capacity limit averages **about four chunks**, and 3–5 in adults in his later review. Miller's "seven" was a rough estimate. Capacity depends on what counts as a chunk and on whether recoding is possible. ([Cowan 2001, BBS](https://memory.psych.missouri.edu/assets/doc/articles/2001/cowan-bbs-2001.pdf); [Cowan 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2864034); [2024 modelling paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11259112/))

**Rules for us**
1. **Four groups per screen at a glance.** A HUD is about four chunks: currency group, objective, ability bar, alerts. A fifth group must be quieter (tier 4) or hidden until needed.
2. **Four stats per reward card.** If an item has more, show the four that changed and put the rest behind a tap.
3. **Chunk numbers.** "1.25M" is one chunk; "1,254,880" is three or more. Use the big-number formatter ([examples/bignum](../../examples/bignum/README.md)).

## 3. Choices and targets

**Findings**
- **Hick–Hyman law:** decision time ≈ a + b·log2(n + 1) for n equally likely options; unequal probabilities use entropy ([ch. 82 §1](82-time-motion-and-cue-timing.md#1-the-human-response-chain)).
- **Fitts's law (Shannon form):** movement time ≈ a + b·ID, with ID = log2(D/W + 1), where D is the distance to the target and W its width. MacKenzie argued for this form, and ISO 9241 adopted it. Drewes (2023) disputes it. ([MacKenzie 1992](https://www.yorku.ca/mack/CHI92.html); [Fitts's law](https://en.wikipedia.org/wiki/Fitts%27s_law))
- **Touch targets:** Apple's minimum is **44 × 44 pt** and Material's is **48 × 48 dp**. The visible icon can be smaller if invisible padding fills the target. Leave **≥ 8 pt/dp** between targets. WCAG 2.5.5 (AAA) uses 44 × 44 CSS px. ([TetraLogical, target size](https://tetralogical.com/blog/2022/12/20/foundations-target-size/); [Shopify](https://shopify.dev/docs/storefronts/themes/best-practices/performance/increase-tap-target-size))

**Rules for us**
1. **Make the expected choice the default and the biggest target.** Fitts says big and near is fast; Hick says fewer options are fast. The main call to action is the largest button, closest to the thumb, and alone in its row (HIERARCHY §13).
2. **Split choices over 8 into categories.** Eight options cost about 3.2 bits. Two levels of three each cost about 2 bits per level, but the player only reads the level they're on.
3. **Touch:** every tappable element is at least 44 × 44 at the device's point scale, with ≥ 8 between targets. Roblox's GUI pixel-to-point mapping varies by device, so **verify on a real phone** (UNKNOWN: Roblox doesn't document a fixed density). The thumb-zone survey is in [chapter 70 §4](70-game-hud-hierarchy.md#4-mobile-and-touch-thumb-zones-minimum-tap-sizes-safe-areas-density).

## 4. Clutter

**Findings**
- Rosenholtz, Li & Nakano (2007) measure clutter three ways: **Feature Congestion** (how hard it would be to add a new item that grabs attention), **Subband Entropy**, and **Edge Density** (from Mack & Oliva). All three track visual-search performance in complex images. Colour variability, captured only by Feature Congestion, matters for perceived clutter. ([J. Vision 7(2):17](https://pubmed.ncbi.nlm.nih.gov/18217832); [MIT code](https://dspace.mit.edu/handle/1721.1/37593))

**Rules for us**
1. **Clutter is the denominator of salience.** The same button is louder on a calm background. Before raising an element's brightness, lower the clutter behind it: blur, dim or desaturate the world under menus (HIERARCHY §6).
2. **Measure it.** The auditor reports edge density and OKLab chroma spread, a cheap stand-in for Feature Congestion. Compare a screen against its own calm frame. Combat frames are allowed about 2× the calm frame's edge density (house). Above that, crowd LOD should kick in (HIERARCHY §12).
3. **Ornament costs.** Every bevel, gradient and pattern adds edges. Tier 3 panels use flat fills with one rim; ornament is earned by tier 1 moments.

## 5. Gaps

- Grouping-strength rankings come from lab stimuli; how they hold up in dense game UI is untested.
- Cowan's limit is for memory under load. A glanceable-HUD limit has not been measured directly; four is our working number.
- Roblox GUI density per device is undocumented. Measure on hardware.
