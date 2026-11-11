# Lexicon

444 design terms from my repos and standard practice. Each has a ready-to-paste prompt phrase. The machine-readable version is [lexicon.json](lexicon.json) (schema: [lexicon.schema.json](lexicon.schema.json)); this page is generated from it by `python3 tools/lexicon/build.py`, so edit `tools/lexicon/src/*.txt`, not this file.

## Starter pack (40 terms)

The highest-leverage terms. Know these and most briefs write themselves.

| Term | Domain | Prompt phrase |
|---|---|---|
| [loudness tier](#loudness-tier) | hierarchy | put this in loudness tier 2: bright on the onset frame, back to baseline within 12 frames |
| [pixel ownership](#pixel-ownership) | hierarchy | stamp the effect at hero rank so it never covers threats, UI or ceremony pixels |
| [intensity ladder](#intensity-ladder) | hierarchy | drive bloom, particle caps and music level from the intensity rung, not per-effect logic |
| [calm frame](#calm-frame) | hierarchy | at rest nothing animates except the selected button's slow pulse |
| [colour job](#colour-job) | hierarchy | use gold only for currency and the main call to action |
| [currency gold](#currency-gold) | hierarchy | colour the price and Buy button currency gold; nothing else on the card is gold |
| [danger red](#danger-red) | hierarchy | keep red for threats only; use bone white for "new" badges |
| [rarity ladder](#rarity-ladder) | hierarchy | each rarity adds exactly one behaviour: static, highlight, sweep, spin, sparks, rainbow, glitch |
| [figure-ground gate](#figure-ground-gate) | hierarchy | gate every enemy colour against the ground: at least 2 OKLab bands apart at the worst pixel |
| [one loud element per panel](#one-loud-element-per-panel) | hierarchy | on each shop card only the Buy button may animate or glow |
| [urgency beats rarity](#urgency-beats-rarity) | hierarchy | even the Mythic aura drops its sparks inside a hostile shot's lane |
| [critical cue](#critical-cue) | hierarchy | treat the hostile shot as a critical cue: it always draws on time, unclipped |
| [decoration slot](#decoration-slot) | hierarchy | cap decorations at 6 world slots; skip the 7th spark instead of queueing it |
| [reward sequencing](#reward-sequencing) | hierarchy | sequence the reveal: crate shakes, item bursts, name stamps, stat delta, continue |
| [skippable reveal](#skippable-reveal) | reward | a tap skips to the final state and restores the world |
| [decide-then-animate](#decide-then-animate) | reward | roll on the server, send the result, then build the reel to land on it |
| [hit-stop](#hit-stop) | vfx | add a 2-frame hit-stop on hits and 6 frames on kills |
| [screen shake](#screen-shake) | vfx | add a 6 px screen shake that decays over 120 ms |
| [impact flash](#impact-flash) | vfx | flash the target white for 1 frame on hit |
| [onset frame](#onset-frame) | hierarchy | make the onset frame the brightest of the effect; everything after is dimmer |
| [recovery window](#recovery-window) | hierarchy | return the screen to baseline within 12 frames (200 ms) after the hit resolves |
| [telegraph](#telegraph) | vfx | draw the attack's real area in red 0.6 s before it lands, filling as it charges |
| [odometer counter](#odometer-counter) | ui | roll only the changed digits over ~140 ms with an ease-out |
| [big-number suffix](#big-number-suffix) | ui | show 3 significant digits plus a suffix: 1.23K, 45.6M |
| [ghost bar](#ghost-bar) | ui | trail HP loss with a pale ghost bar that catches up after 400 ms |
| [rarity frame](#rarity-frame) | ui | style each slot border by rarity: static, sweep, spin, sparks, rainbow, glitch |
| [call to action](#call-to-action) | ui | make Buy the call to action: gold fill, largest, the only animated element |
| [safe area](#safe-area) | ui | inset the HUD by the device safe area and keep 12 px margins |
| [holo foil](#holo-foil) | materials | give Mythic cards holo foil: hue shifts with tilt, sheen follows the pointer |
| [rarity-as-material](#rarity-as-material) | hierarchy | map rarity to material: Rare brushed metal, Epic glass, Legendary chrome, Mythic holo |
| [signed distance field](#signed-distance-field) | shaders | build the shape as a signed distance field and derive fill, outline and glow from it |
| [fBm](#fbm) | shaders | 5-octave fBm, lacunarity 2, gain 0.5 |
| [godrithm](#godrithm) | algorithms | build the look as a godrithm: noise → warp → threshold → distance → bands |
| [Poisson disk](#poisson-disk) | algorithms | scatter trees with Poisson disk at 12 stud spacing |
| [balance in data](#balance-in-data) | economy | move every price and rate into content rows; services hold none |
| [pacing](#pacing) | economy | simulate a player and keep each wait within 2× of the last |
| [server authority](#server-authority) | code | the client requests, the server validates and decides |
| [remote validation](#remote-validation) | code | validate shape (type, whitelist, finite, capped), then rate, then state |
| [frame budget](#frame-budget) | performance | keep this system under 0.8 ms of the 16.6 ms frame budget |
| [brief](#brief) | process | write a brief before building: goal, tier, deliverable, constraints, bar, done |

## Domains

[Hierarchy](#hierarchy) (61) · [UI & HUD](#ui---hud) (56) · [Rewards & Moments](#rewards---moments) (22) · [VFX](#vfx) (42) · [Materials](#materials) (41) · [Shaders & SDF](#shaders---sdf) (28) · [Algorithms](#algorithms) (38) · [World](#world) (29) · [Economy](#economy) (26) · [Code & Framework](#code---framework) (34) · [Performance](#performance) (17) · [Art Direction](#art-direction) (17) · [Audio & Feel](#audio---feel) (8) · [Game Feel](#game-feel) (12) · [Process](#process) (13)

## Hierarchy

### loudness tier

One of six ranks (1 Moments … 6 Engines) that sets how loud an effect may be on screen. **Use when:** Deciding how much an effect may glow, move or cover.

> put this in loudness tier 2: bright on the onset frame, back to baseline within 12 frames

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [pixel ownership](#pixel-ownership), [one loud element per panel](#one-loud-element-per-panel) · Source: aaa-kit/HIERARCHY.md

### pixel ownership

Every pixel has one owner rank (background < ambient < world < reward < threat < hero < UI < ceremony) and writes may only cover lower ranks. **Use when:** Deciding what may draw over what.

> stamp the effect at hero rank so it never covers threats, UI or ceremony pixels

Tier: all · Pairs with: [owner buffer](#owner-buffer), [loudness tier](#loudness-tier), [protected region](#protected-region) · Source: cursed-survivors/docs/decisions.md

### owner buffer

A byte per pixel recording which owner rank drew it this frame. **Use when:** Pixel renderers that need per-pixel draw rules.

> keep a u8 owner buffer cleared each frame and route every write through the owner rule

Tier: T6 engines · Pairs with: [pixel ownership](#pixel-ownership), [EditableImage](#editableimage), [CAN table](#can-table) · Source: cursed-survivors/docs/budgets.md

### CAN table

A lookup of which writer rank may paint over which destination rank. **Use when:** Centralising draw permissions for every FX write.

> route all FX writes through one CAN[writer][dest] table instead of per-effect checks

Tier: T6 engines · Pairs with: [owner buffer](#owner-buffer), [pixel ownership](#pixel-ownership) · Source: cursed-survivors/docs/decisions.md

### intensity ladder

One game-state number from calm (0) to finale (5) that every visual layer reads to size its budget. **Use when:** Scaling spectacle with the situation.

> drive bloom, particle caps and music level from the intensity rung, not per-effect logic

Tier: all · Pairs with: [calm frame](#calm-frame), [hysteresis](#hysteresis), [intensity budget](#intensity-budget) · Source: cursed-survivors/src/shared/Intensity.luau

### intensity budget

The knobs a rung allows: impact frames, ambient, particle scale, bloom, music level. **Use when:** Implementing the intensity ladder in a system.

> read Intensity.budget(level) and skip impact frames when it says impact = false

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [hit-stop](#hit-stop) · Source: cursed-survivors/src/shared/Intensity.luau

### calm rung

Intensity 0: nothing near the player, menus at rest; ambient on, no impact frames. **Use when:** Defining the baseline look.

> at the calm rung keep music muffled and weapon ornament back

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [calm frame](#calm-frame) · Source: cursed-survivors/src/shared/Intensity.luau

### build rung

Intensity 1: the crowd is growing; the celebration rung with full weapon ornament. **Use when:** Rewarding a strong build mid-run.

> let weapon trails run at full ornament on the build rung

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [surge rung](#surge-rung) · Source: cursed-survivors/src/shared/Intensity.luau

### surge rung

Intensity 2: dense crowd near the player, a hostile shot near, or low HP. **Use when:** Danger moments that need clarity.

> on the surge rung turn ambient off and let HUD ornament wait

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [urgency beats rarity](#urgency-beats-rarity) · Source: cursed-survivors/src/shared/Intensity.luau

### ceremony rung

Intensity 3: a level-up, chest or reward screen is open. **Use when:** Reward screens.

> on the ceremony rung drop the world to the lowest band behind the reveal

Tier: T1 moments · Pairs with: [reward sequencing](#reward-sequencing), [world dim](#world-dim) · Source: cursed-survivors/src/shared/Intensity.luau

### boss rung

Intensity 4: a boss is on screen; impact on, ambient off, grade floor raised. **Use when:** Boss fights.

> on the boss rung raise the grade floor and allow impact frames

Tier: T2 combat · Pairs with: [intensity ladder](#intensity-ladder), [telegraph](#telegraph) · Source: cursed-survivors/src/shared/Intensity.luau

### finale rung

Intensity 5: the final fight or countdown; everything allowed. **Use when:** The last minutes of a run.

> save the brightest grade and loudest music for the finale rung only

Tier: T1 moments · Pairs with: [intensity ladder](#intensity-ladder), [impact frame](#impact-frame) · Source: cursed-survivors/src/shared/Intensity.luau

### hysteresis

Separate enter and exit thresholds so a state doesn't flicker at the boundary. **Use when:** Any visual state switched by a live number.

> enter at 12 nearby enemies, exit at 8, held 1 s, so the treatment doesn't flicker

Tier: all · Pairs with: [intensity ladder](#intensity-ladder), [crowd LOD](#crowd-lod) · Source: vault/Notes/15 Attention System

### calm frame

A frame where nothing loops except the selection and slow ambient motion. **Use when:** Setting the baseline so peaks read.

> at rest nothing animates except the selected button's slow pulse

Tier: all · Pairs with: [calm rung](#calm-rung), [recovery window](#recovery-window) · Source: aaa-kit/HIERARCHY.md

### recovery window

The time after an event resolves for the screen to return to baseline (12 frames). **Use when:** Tuning effect tails.

> return the screen to baseline within 12 frames (200 ms) after the hit resolves

Tier: all · Pairs with: [calm frame](#calm-frame), [event timeline](#event-timeline) · Source: vault/Notes/15 Attention System

### event timeline

Baseline → anticipation → onset → active → resolution → recovery for every visible event. **Use when:** Planning an effect's timing.

> write the effect as anticipation 0 frames, onset 2 frames, active 10, recovery 12

Tier: all · Pairs with: [onset frame](#onset-frame), [anticipation](#anticipation), [recovery window](#recovery-window) · Source: vault/Notes/15 Attention System

### onset frame

The first 1–2 frames of an event; the brightest and most informative. **Use when:** Making hits read instantly.

> make the onset frame the brightest of the effect; everything after is dimmer

Tier: T2 combat · Pairs with: [event timeline](#event-timeline), [impact flash](#impact-flash) · Source: aaa-kit/HIERARCHY.md

### critical cue

Information the player must get on time: hits on them, hostile shots, boss attacks, HP changes. **Use when:** Deciding what may never be delayed.

> treat the hostile shot as a critical cue: it always draws on time, unclipped

Tier: all · Pairs with: [decoration slot](#decoration-slot), [urgency beats rarity](#urgency-beats-rarity) · Source: vault/Notes/15 Attention System

### decoration slot

One of a fixed number of places for decorative accents (6 world, 1 UI); losers are skipped, never delayed. **Use when:** Capping sparkle overload.

> cap decorations at 6 world slots; skip the 7th spark instead of queueing it

Tier: all · Pairs with: [critical cue](#critical-cue), [particle budget](#particle-budget) · Source: vault/Notes/15 Attention System

### urgency beats rarity

When situations overlap, danger wins every channel over rarity or celebration. **Use when:** A pretty effect overlaps a threat.

> even the Mythic aura drops its sparks inside a hostile shot's lane

Tier: all · Pairs with: [critical cue](#critical-cue), [protected region](#protected-region) · Source: vault/Notes/15 Attention System

### protected region

A mask (hero, shots, close enemies, pickups, text) inside which decoration reduces itself. **Use when:** Keeping gameplay readable under spectacle.

> inside the hero's 2 px ring, effects drop one band and lose sparks

Tier: T2 combat · Pairs with: [pixel ownership](#pixel-ownership), [urgency beats rarity](#urgency-beats-rarity) · Source: vault/Notes/15 Attention System

### figure-ground gate

A silhouette must be ≥ 2 luminance bands from its 1–2 px ring at the worst pixel. **Use when:** Checking any sprite or icon against its background.

> gate every enemy colour against the ground: at least 2 OKLab bands apart at the worst pixel

Tier: all · Pairs with: [luminance band](#luminance-band), [thin ring](#thin-ring), [squint test](#squint-test) · Source: aaa-kit/HIERARCHY.md

### luminance band

One of 8 perceptual lightness steps (B0–B7) on OKLab L used to assign and check value. **Use when:** Value structure and banded lighting.

> assign the world to bands B1–B3 and pickups to B4–B5

Tier: all · Pairs with: [figure-ground gate](#figure-ground-gate), [OKLab](#oklab) · Source: cursed-survivors/docs/decisions.md

### thin ring

A 1 px ring around the hero that darkens whatever is under it by 2 bands, never black. **Use when:** Keeping the hero findable without a heavy outline.

> give the hero a 1 px 8-neighbour ring that shifts the ground down 2 bands

Tier: T2 combat · Pairs with: [figure-ground gate](#figure-ground-gate), [silhouette](#silhouette) · Source: cursed-survivors/docs/decisions.md

### one loud element per panel

A menu panel has exactly one element that draws the eye. **Use when:** Laying out cards, dialogs and shops.

> on each shop card only the Buy button may animate or glow

Tier: T3 hud · Pairs with: [call to action](#call-to-action), [calm frame](#calm-frame) · Source: aaa-kit/HIERARCHY.md

### colour job

A meaningful hue carries one meaning only (gold currency, blue XP, red danger). **Use when:** Picking colours for anything that means something.

> use gold only for currency and the main call to action

Tier: all · Pairs with: [currency gold](#currency-gold), [danger red](#danger-red), [XP blue](#xp-blue) · Source: aaa-kit/HIERARCHY.md

### currency gold

#ffd24a, reserved for currency and the main call to action. **Use when:** Prices, coin counters, buy buttons.

> colour the price and Buy button currency gold; nothing else on the card is gold

Tier: T3 hud · Pairs with: [colour job](#colour-job), [call to action](#call-to-action) · Source: aaa-kit/HIERARCHY.md

### danger red

Red reserved for threats, damage taken and low HP. **Use when:** Hostile shots, damage numbers on the player, HP warnings.

> keep red for threats only; use bone white for "new" badges

Tier: T2 combat · Pairs with: [colour job](#colour-job), [low-HP vignette](#low-hp-vignette) · Source: aaa-kit/HIERARCHY.md

### XP blue

Blue reserved for experience, XP gems and the XP bar. **Use when:** Progress toward levels.

> XP gems and the XP bar are blue; nothing else is

Tier: T3 hud · Pairs with: [colour job](#colour-job), [XP bar](#xp-bar) · Source: aaa-kit/HIERARCHY.md

### rarity ladder

Common → Uncommon → Rare → Epic → Legendary → Mythic → Secret, each adding one visual behaviour. **Use when:** Designing item tiers.

> each rarity adds exactly one behaviour: static, highlight, sweep, spin, sparks, rainbow, glitch

Tier: T5 materials · Pairs with: [rarity frame](#rarity-frame), [rarity-as-material](#rarity-as-material) · Source: aaa-kit/HIERARCHY.md

### rarity-as-material

Expressing rarity by surface: flat, satin, brushed, glass/gem, chrome/molten, holo, void. **Use when:** Items, icons and frames.

> map rarity to material: Rare brushed metal, Epic glass, Legendary chrome, Mythic holo

Tier: T5 materials · Pairs with: [rarity ladder](#rarity-ladder), [holo foil](#holo-foil) · Source: aaa-kit/HIERARCHY.md

### reward sequencing

A reward hands attention along: container → item → identity → delta → continue. **Use when:** Reveal screens.

> sequence the reveal: crate shakes, item bursts, name stamps, stat delta, continue

Tier: T1 moments · Pairs with: [skippable reveal](#skippable-reveal), [ceremony rung](#ceremony-rung) · Source: aaa-kit/HIERARCHY.md

### crowd LOD

Dense regions switch from sprites to aggregate glyphs before readability fails. **Use when:** Hundreds of enemies on screen.

> collapse cells of 6+ enemies into density glyphs and restore at 3 or fewer

Tier: T6 engines · Pairs with: [glyph density](#glyph-density), [hysteresis](#hysteresis) · Source: cursed-survivors/docs/decisions.md

### glyph density

An ASCII ramp where density means count only: . : * # @. **Use when:** Aggregate crowd display.

> show crowd count with . for 3, : for 4–5, * for 6–7, # for 8–10, @ for 11+

Tier: T6 engines · Pairs with: [crowd LOD](#crowd-lod), [glyph ramp](#glyph-ramp) · Source: cursed-survivors/docs/decisions.md

### attention channel

One of ten levers on attention: meaning, contrast, scale, detail, motion, occlusion, space, time, representation, sound. **Use when:** Diagnosing why something draws the eye.

> check every attention channel, not just brightness, when an element draws too much eye

Tier: all · Pairs with: [figure-ground gate](#figure-ground-gate), [motion budget](#motion-budget) · Source: vault/Notes/15 Attention System

### motion budget

Caps on non-gameplay movers near the hero (≤ 3 per cell) and changed pixels (≤ 15 %). **Use when:** Busy backgrounds and auras.

> near the hero allow at most 3 non-gameplay movers per 16×12 cell

Tier: all · Pairs with: [detail density](#detail-density), [attention channel](#attention-channel) · Source: vault/Notes/15 Attention System

### detail density

How much edge and pattern sits in an area, independent of brightness. **Use when:** Ground textures eating outlines.

> keep edge density under 25 % in the ring around protected silhouettes

Tier: all · Pairs with: [motion budget](#motion-budget), [figure-ground gate](#figure-ground-gate) · Source: vault/Notes/15 Attention System

### squint test

Blur or squint at a frame to see only value and big shapes. **Use when:** Reviewing readability fast.

> squint-test the frame: hero, threats and lanes must survive a 4 px blur

Tier: all · Pairs with: [figure-ground gate](#figure-ground-gate), [silhouette read](#silhouette-read) · Source: industry

### tier view

A debug render that colours each pixel by its owner rank. **Use when:** Auditing ownership and loudness.

> render a tier view where each owner rank has a flat colour to audit coverage

Tier: all · Pairs with: [owner buffer](#owner-buffer), [saliency map](#saliency-map) · Source: cursed-survivors/docs/decisions.md

### saliency map

A computed map of where the eye is likely to go first. **Use when:** Finding elements that draw more attention than their tier allows.

> compare the saliency map with the tier view and fix decor that outranks pickups

Tier: all · Pairs with: [tier view](#tier-view), [squint test](#squint-test) · Source: vault/Notes/16 Hierarchy Codex

### salience map

A per-pixel estimate of how strongly each place differs from its surroundings and so pulls the eye bottom-up. **Use when:** Checking what a screen shouts before anyone reads it.

> run the salience audit and show me where fixation 1 lands

Tier: all · Pairs with: [predicted scanpath](#predicted-scanpath), [focus lift](#focus-lift), [squint test](#squint-test) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### predicted scanpath

The order a salience model visits a screen: take the peak, suppress it (inhibition of return), repeat. **Use when:** Checking that the eye reaches the CTA first and the reward second.

> predict the first five fixations and number them on the overlay

Tier: all · Pairs with: [salience map](#salience-map), [inhibition of return](#inhibition-of-return) · Source: aaa-kit/tools/hierarchy

### focus lift

Share of salience inside the focus element divided by its share of the screen area. **Use when:** Scoring whether the intended focus actually wins.

> the buy button needs a focus lift of at least 1.5

Tier: all · Pairs with: [salience map](#salience-map), [one loud element per panel](#one-loud-element-per-panel) · Source: aaa-kit/docs/research/85-measuring-hierarchy.md

### pre-attentive feature

A basic attribute (colour, size, motion, orientation) that guides attention without item-by-item search. **Use when:** Choosing how a hierarchy level is coded.

> code the urgent state with one pre-attentive feature, not a conjunction

Tier: all · Pairs with: [pop-out](#pop-out), [colour job](#colour-job) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### pop-out

A single item differing in one feature from a uniform field is found instantly regardless of crowd size. **Use when:** Making one element unmissable.

> keep the cards grey so the one gold card pops out

Tier: all · Pairs with: [pre-attentive feature](#pre-attentive-feature), [one loud element per panel](#one-loud-element-per-panel) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### onset capture

A new object appearing abruptly grabs attention involuntarily; gradual reveals do not. **Use when:** Deciding which tiers may pop in.

> let only tier 1-3 elements pop in; fade tier 4-6 content over 300 ms

Tier: T1 moments · Pairs with: [loudness tier](#loudness-tier), [onset frame](#onset-frame) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### looming

Motion toward the viewer, which gets attentional priority as behaviourally urgent. **Use when:** Telegraphs and incoming threats.

> make the boss lunge loom toward camera so it reads as urgent

Tier: T2 combat · Pairs with: [telegraph](#telegraph), [urgency beats rarity](#urgency-beats-rarity) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### inhibition of return

After attention leaves a place, it is slower to come back there (from about 300 ms). **Use when:** Repeating a warning.

> do not re-flash the same spot; move it, grow it or add sound

Tier: all · Pairs with: [predicted scanpath](#predicted-scanpath), [critical cue](#critical-cue) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### attentional blink

A second message 200-500 ms after a first is often missed. **Use when:** Timing reward beats and popups.

> space reward beats at least 500 ms apart or merge them into one beat

Tier: T1 moments · Pairs with: [reward sequencing](#reward-sequencing) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### change blindness

Large changes go unnoticed when a flash, cut or transition masks them. **Use when:** Deciding when to update state.

> change the price after the window transition settles, never during it

Tier: all · Pairs with: [protected region](#protected-region), [calm frame](#calm-frame) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### crowding

Peripheral items can't be identified when neighbours are closer than about half their distance from gaze (Bouma). **Use when:** Placing corner HUD elements.

> peripheral HUD items signal by colour or motion, not detail

Tier: T3 HUD · Pairs with: [touch target](#touch-target), [safe area](#safe-area) · Source: aaa-kit/docs/research/80-attention-and-salience.md

### APCA contrast

Signed lightness contrast (Lc) for text on a background that accounts for polarity and size. **Use when:** Checking any text colour pair.

> keep play-critical numbers at APCA Lc 75 or more on their worst background

Tier: T3 HUD · Pairs with: [OKLab](#oklab), [squint test](#squint-test) · Source: aaa-kit/docs/research/81-contrast-colour-and-colour-blindness.md

### colour-blind check

Re-running a colour code through protan and deutan simulation (Machado 2009) to see if it survives. **Use when:** Any hue-coded state, team or rarity.

> run Perceptual.ladder on the rarity colours under deutan and protan

Tier: all · Pairs with: [colour job](#colour-job), [rarity ladder](#rarity-ladder) · Source: aaa-kit/docs/research/81-contrast-colour-and-colour-blindness.md

### flash limit

No more than 3 general or red flashes per second over more than 25% of a 10-degree field (WCAG 2.3.1). **Use when:** Any impact flash, lightning or strobe.

> throttle impact flashes to 3 per second when they cover more than 2.8% of the screen

Tier: T1 moments · Pairs with: [impact flash](#impact-flash), [hit-stop](#hit-stop) · Source: aaa-kit/docs/research/81-contrast-colour-and-colour-blindness.md

### telegraph budget

Wind-up time sized from notice + decide + act + latency (about 600 ms familiar, 1 s or more new). **Use when:** Tuning enemy wind-ups.

> give the new boss slam a 1.2 s wind-up and shorten it after first sight

Tier: T2 combat · Pairs with: [telegraph](#telegraph), [looming](#looming) · Source: aaa-kit/docs/research/82-time-motion-and-cue-timing.md

### sidechain duck

Lowering one audio bus automatically while another plays, keyed by the louder bus. **Use when:** Making the important sound audible.

> sidechain the music bus to the ceremony bus and duck it 10 dB

Tier: all · Pairs with: [ducking](#ducking), [critical cue](#critical-cue) · Source: aaa-kit/docs/research/83-audio-hierarchy.md

### four chunks

Working memory holds about four chunks at once (Cowan 2001). **Use when:** Deciding how many HUD groups or stats to show.

> keep the HUD to four groups and the reward card to four stats

Tier: T3 HUD · Pairs with: [one loud element per panel](#one-loud-element-per-panel), [call to action](#call-to-action) · Source: aaa-kit/docs/research/84-grouping-density-and-choice.md

### common region

Elements inside one bounded panel are seen as one group, more strongly than proximity. **Use when:** Laying out cards and panels.

> put price, icon and buy button inside one card; never straddle two

Tier: T3 HUD · Pairs with: [four chunks](#four-chunks) · Source: aaa-kit/docs/research/84-grouping-density-and-choice.md

### Hick's law

Decision time grows with log2(n+1) of the number of equal options. **Use when:** Menus, shops, upgrade choices.

> split the 12 upgrades into three tabs of four

Tier: T3 HUD · Pairs with: [Fitts's law](#fitts-s-law), [call to action](#call-to-action) · Source: aaa-kit/docs/research/84-grouping-density-and-choice.md

### Fitts's law

Pointing time grows with log2(distance/width + 1). **Use when:** Sizing and placing buttons.

> make the main CTA the biggest button nearest the thumb

Tier: T3 HUD · Pairs with: [Hick's law](#hick-s-law), [touch target](#touch-target) · Source: aaa-kit/docs/research/84-grouping-density-and-choice.md

### visual clutter

How crowded a scene is in features (edge density, colour variety); the denominator of salience. **Use when:** Backgrounds behind important UI or cues.

> lower the clutter behind the menu before making the button brighter

Tier: all · Pairs with: [calm frame](#calm-frame), [salience map](#salience-map) · Source: aaa-kit/docs/research/84-grouping-density-and-choice.md


## UI & HUD

### HUD

The always-on layer of status and actions over gameplay. **Use when:** Any in-game status display.

> keep the HUD still at rest; animate only what just changed

Tier: T3 hud · Pairs with: [safe area](#safe-area), [one loud element per panel](#one-loud-element-per-panel) · Source: industry

### safe area

Screen region not covered by notches, rounded corners or system bars. **Use when:** Phone layouts.

> inset the HUD by the device safe area and keep 12 px margins

Tier: T3 hud · Pairs with: [thumb zone](#thumb-zone), [HUD](#hud) · Source: industry

### thumb zone

Areas a phone player's thumbs cover (bottom corners) or reach easily. **Use when:** Placing buttons and status.

> put actions in the bottom-right thumb zone and status top-left

Tier: T3 hud · Pairs with: [safe area](#safe-area), [touch target](#touch-target) · Source: industry

### touch target

The tappable area of a control; ≥ 44 px on phones. **Use when:** Buttons and icons on mobile.

> make every touch target at least 44×44 px even if the icon is smaller

Tier: T3 hud · Pairs with: [thumb zone](#thumb-zone) · Source: industry

### tabular figures

Digits of equal width so counters don't wobble when values change. **Use when:** Any changing number.

> use tabular-width digits so the counter doesn't jitter as it rolls

Tier: T3 hud · Pairs with: [odometer counter](#odometer-counter), [big-number suffix](#big-number-suffix) · Source: industry

### big-number suffix

Abbreviating with K, M, B, T, Qa… and three significant digits. **Use when:** Currency and scores.

> show 3 significant digits plus a suffix: 1.23K, 45.6M

Tier: T3 hud · Pairs with: [odometer counter](#odometer-counter), [number floor](#number-floor) · Source: aaa-kit/examples/framework-starter

### number floor

Rounding displayed values down so the HUD never shows more than the player has. **Use when:** Currency displays.

> floor displayed currency so 1,999 shows 1.99K, not 2.00K

Tier: T3 hud · Pairs with: [big-number suffix](#big-number-suffix) · Source: aaa-kit/examples/framework-starter

### odometer counter

A counter whose changed digits roll vertically into place. **Use when:** Coins, scores, big numbers.

> roll only the changed digits over ~140 ms with an ease-out

Tier: T3 hud · Pairs with: [tabular figures](#tabular-figures), [count-up](#count-up) · Source: Living Effects Lab

### count-up

Animating a number from old to new value, often exponentially for big jumps. **Use when:** Payouts and results screens.

> count up exponentially over 1.2 s and burst a ring at each rarity threshold

Tier: T1 moments · Pairs with: [odometer counter](#odometer-counter), [tier threshold burst](#tier-threshold-burst) · Source: Living Effects Lab

### ghost bar

A delayed second fill that trails a bar's losses so damage reads as a chunk. **Use when:** HP, shields, boss bars.

> trail HP loss with a pale ghost bar that catches up after 400 ms

Tier: T3 hud · Pairs with: [eased fill](#eased-fill), [damage number](#damage-number) · Source: industry

### eased fill

A bar that animates to its target with easing and a glowing leading edge. **Use when:** XP and progress bars.

> ease the fill over 250 ms with a soft glow on the leading edge

Tier: T3 hud · Pairs with: [ghost bar](#ghost-bar), [leading-edge glow](#leading-edge-glow) · Source: Living Effects Lab

### leading-edge glow

A bright cap on the moving end of a fill. **Use when:** Progress that should feel alive.

> add a 6 px glow on the bar's leading edge only while it moves

Tier: T3 hud · Pairs with: [eased fill](#eased-fill) · Source: Living Effects Lab

### radial cooldown

A pie-sweep darkening an ability icon until it's ready. **Use when:** Ability bars.

> darken the icon with a clockwise radial sweep and show seconds under 10 s

Tier: T3 hud · Pairs with: [ready flash](#ready-flash) · Source: Living Effects Lab

### ready flash

A one-frame white flash plus ring when a cooldown completes. **Use when:** Telling the player an ability is back.

> when the cooldown ends, flash the icon white for 1 frame and expand a ring

Tier: T3 hud · Pairs with: [radial cooldown](#radial-cooldown) · Source: Living Effects Lab

### combo meter

A streak counter climbing named tiers with a decay bar. **Use when:** Hit streaks and chains.

> climb NICE → GREAT → INSANE → GODLIKE with a decay bar that breaks the streak

Tier: T3 hud · Pairs with: [combo tier](#combo-tier), [decay bar](#decay-bar) · Source: Living Effects Lab

### combo tier

A named threshold of a combo meter with its own look. **Use when:** Escalating streak feedback.

> give each combo tier its own frame colour from the rarity ladder

Tier: T3 hud · Pairs with: [combo meter](#combo-meter), [rarity ladder](#rarity-ladder) · Source: Living Effects Lab

### decay bar

A shrinking bar showing time left before a streak or buff ends. **Use when:** Combos, buffs, timers.

> show a thin decay bar under the combo that refills on every hit

Tier: T3 hud · Pairs with: [combo meter](#combo-meter) · Source: Living Effects Lab

### reward feed

Stacked toasts announcing gains, fading after a few seconds. **Use when:** Loot and kill logs.

> stack at most 4 toasts, fade at 2.5 s, merge repeats into ×N

Tier: T3 hud · Pairs with: [toast merge](#toast-merge) · Source: Living Effects Lab

### toast merge

Combining repeated notifications into one with a count. **Use when:** Spammy feeds.

> merge repeated toasts into one line: "+3 Gems ×4"

Tier: T3 hud · Pairs with: [reward feed](#reward-feed) · Source: industry

### damage number

A number popping from a hit showing damage dealt. **Use when:** Combat feedback.

> pop damage numbers at 1.4× scale to 1×, drift up 20 px, fade by 600 ms

Tier: T2 combat · Pairs with: [crit number](#crit-number), [number cap](#number-cap) · Source: Living Effects Lab

### crit number

A larger, outlined, shaking damage number for critical hits. **Use when:** Making crits read.

> crits pop at 1.8×, add a 2 px outline and a 3-frame shake

Tier: T2 combat · Pairs with: [damage number](#damage-number) · Source: Living Effects Lab

### number cap

A limit on simultaneous damage numbers with merging beyond it. **Use when:** Dense combat.

> cap damage numbers at 12 and merge the rest into running totals

Tier: T2 combat · Pairs with: [damage number](#damage-number), [decoration slot](#decoration-slot) · Source: aaa-kit/.claude/skills/ui-hud

### low-HP vignette

A pulsing red edge and heartbeat when health is low. **Use when:** Danger state.

> below 30 % HP pulse a double-beat red vignette at the screen edge

Tier: T3 hud · Pairs with: [danger red](#danger-red), [surge rung](#surge-rung) · Source: Living Effects Lab

### luck gauge

A segmented boost meter with a spring needle that ignites at max. **Use when:** Boost and luck mechanics.

> spring the gauge needle with overshoot and ignite the dial at max

Tier: T3 hud · Pairs with: [spring animation](#spring-animation) · Source: Living Effects Lab

### rarity frame

An inventory slot border styled by rarity. **Use when:** Inventories and shops.

> style each slot border by rarity: static, sweep, spin, sparks, rainbow, glitch

Tier: T3 hud · Pairs with: [rarity ladder](#rarity-ladder), [UIStroke](#uistroke) · Source: Living Effects Lab

### call to action

The single primary action on a screen, styled loudest. **Use when:** Buttons on shops and dialogs.

> make Buy the call to action: gold fill, largest, the only animated element

Tier: T3 hud · Pairs with: [one loud element per panel](#one-loud-element-per-panel), [currency gold](#currency-gold) · Source: industry

### button press

Feedback when a button is pressed: scale down, then release overshoot. **Use when:** Any button.

> press scales the button to 0.94 in 60 ms and releases with a 1.04 overshoot

Tier: T3 hud · Pairs with: [spring animation](#spring-animation), [hover state](#hover-state) · Source: industry

### hover state

A subtle change on pointer-over (lift, brighten, outline). **Use when:** Desktop UI.

> on hover lift the button 2 px and brighten its outline one band

Tier: T3 hud · Pairs with: [button press](#button-press) · Source: industry

### focus ring

A visible outline on the keyboard- or gamepad-focused element. **Use when:** Controller and keyboard navigation.

> show a 2 px bone-white focus ring on the selected element

Tier: T3 hud · Pairs with: [hover state](#hover-state) · Source: industry

### modal

A screen layer that blocks input to what's behind it until dismissed. **Use when:** Confirmations, reward screens.

> open purchases in a modal and dim the world one band behind it

Tier: T3 hud · Pairs with: [world dim](#world-dim) · Source: industry

### world dim

Darkening the game world behind a UI or ceremony. **Use when:** Focusing attention on a reveal or menu.

> dim the world to the lowest band while the reveal plays

Tier: T1 moments · Pairs with: [modal](#modal), [ceremony rung](#ceremony-rung) · Source: aaa-kit/HIERARCHY.md

### juice

Small, layered feedback (scale, sound, particles, shake) that makes actions feel good. **Use when:** Polishing interactions.

> add juice: 120 ms pop, a click sound and 6 sparks on buy

Tier: T3 hud · Pairs with: [button press](#button-press), [hit-stop](#hit-stop) · Source: industry

### diegetic UI

Interface that exists inside the game world (a lantern for health, a coin pile). **Use when:** Immersive HUDs.

> show health as the hero's lantern brightness, with the number small in the corner

Tier: T3 hud · Pairs with: [HUD](#hud) · Source: industry

### nine-slice

Scaling an image so corners stay fixed and edges stretch. **Use when:** Panels and frames at any size.

> build panels with nine-slice images so corners stay crisp at every size

Tier: T3 hud · Pairs with: [UIStroke](#uistroke) · Source: industry

### tween

An interpolation of a property over time with an easing curve. **Use when:** Any UI motion.

> tween position over 180 ms with an ease-out cubic

Tier: T3 hud · Pairs with: [easing curve](#easing-curve) · Source: industry

### easing curve

A function shaping motion over time (ease-out, back, elastic). **Use when:** Any animation.

> use ease-out cubic for arrivals and ease-in for exits

Tier: all · Pairs with: [tween](#tween), [overshoot](#overshoot) · Source: industry

### overshoot

Going slightly past the target before settling. **Use when:** Snappy, physical-feeling motion.

> land the card with a 6 % overshoot and settle in 120 ms

Tier: all · Pairs with: [easing curve](#easing-curve), [spring animation](#spring-animation) · Source: industry

### spring animation

Motion driven by a damped spring rather than a fixed curve. **Use when:** Interactive, interruptible motion.

> drive the panel with a spring: stiffness 300, damping 25

Tier: all · Pairs with: [overshoot](#overshoot) · Source: industry

### stagger

Starting a list of animations with small delays between items. **Use when:** Lists and grids appearing.

> stagger card entrances by 40 ms each, max 300 ms total

Tier: T3 hud · Pairs with: [tween](#tween) · Source: industry

### screen transition

The animation between two screens (wipe, dissolve, iris). **Use when:** Menu flow.

> transition screens with a 250 ms iris wipe, never a hard cut

Tier: T3 hud · Pairs with: [iris wipe](#iris-wipe) · Source: industry

### iris wipe

A circular reveal or close transition. **Use when:** Scene changes.

> close the old screen with an iris wipe centred on the button pressed

Tier: T3 hud · Pairs with: [screen transition](#screen-transition) · Source: industry

### tooltip

A small panel explaining an element on hover or long-press. **Use when:** Stats and icons.

> show full numbers and stats in a tooltip on long-press

Tier: T3 hud · Pairs with: [long-press](#long-press) · Source: industry

### long-press

Holding a touch to reveal secondary information. **Use when:** Phone detail views.

> long-press a counter to show the exact value with commas

Tier: T3 hud · Pairs with: [tooltip](#tooltip) · Source: industry

### badge

A small marker on an icon (new, count, alert). **Use when:** Notifications.

> mark new items with a bone-white dot, not red

Tier: T3 hud · Pairs with: [colour job](#colour-job) · Source: industry

### progress ring

A circular progress indicator. **Use when:** Timers and charging.

> show charge as a progress ring that fills clockwise

Tier: T3 hud · Pairs with: [radial cooldown](#radial-cooldown) · Source: industry

### inventory grid

A grid of item slots. **Use when:** Inventories and collections.

> sort the inventory grid by rarity, loudest top-left

Tier: T3 hud · Pairs with: [rarity frame](#rarity-frame) · Source: industry

### XP bar

The bar showing progress to the next level. **Use when:** Levelling.

> fill the XP bar in XP blue with an eased leading edge; burst at full

Tier: T3 hud · Pairs with: [XP blue](#xp-blue), [eased fill](#eased-fill), [level-up](#level-up) · Source: Living Effects Lab

### HP bar

The player's or an enemy's health display. **Use when:** Combat status.

> show HP as a bar with a ghost bar trailing losses

Tier: T3 hud · Pairs with: [ghost bar](#ghost-bar), [danger red](#danger-red) · Source: industry

### boss bar

A wide health bar for a boss, with phase markers. **Use when:** Boss fights.

> show the boss bar top-centre with ticks at each phase threshold

Tier: T3 hud · Pairs with: [HP bar](#hp-bar), [boss rung](#boss-rung) · Source: industry

### minimap

A small overview map. **Use when:** Navigation.

> show landmarks and the player arrow on a minimap, nothing else

Tier: T3 hud · Pairs with: [landmark](#landmark) · Source: industry

### fog of war

Hiding unexplored or out-of-sight areas. **Use when:** Exploration and strategy.

> reveal fog of war in a soft-edged radius around the player

Tier: T4 world · Pairs with: [minimap](#minimap) · Source: industry

### off-screen indicator

An arrow at the screen edge pointing to something off screen. **Use when:** Objectives and threats.

> point an edge arrow at the off-screen boss, red only for threats

Tier: T3 hud · Pairs with: [telegraph](#telegraph) · Source: industry

### quest tracker

A compact list of current goals. **Use when:** Guiding players.

> track one active quest at a time with a progress count

Tier: T3 hud · Pairs with: [one loud element per panel](#one-loud-element-per-panel) · Source: industry

### notification dot

A small dot showing something new in a menu. **Use when:** Menu discoverability.

> show a bone-white notification dot on tabs with unseen items

Tier: T3 hud · Pairs with: [badge](#badge) · Source: industry

### settings menu

Options for audio, graphics, controls and accessibility. **Use when:** Every game.

> include reduced motion, music, SFX and render quality in settings

Tier: T3 hud · Pairs with: [reduced motion](#reduced-motion) · Source: industry

### shop card

One purchasable item's tile: icon, name, price and buy button. **Use when:** Shops.

> build the shop card: rarity frame, icon, name, gold price, one Buy button

Tier: T3 hud · Pairs with: [call to action](#call-to-action), [rarity frame](#rarity-frame) · Source: industry


## Rewards & Moments

### reveal

The moment the player learns what they got. **Use when:** Any drop or unlock.

> build anticipation for 0.6 s, then reveal on a hit with a burst

Tier: T1 moments · Pairs with: [reward sequencing](#reward-sequencing), [anticipation](#anticipation) · Source: industry

### anticipation

A wind-up before an event that tells the player something is coming. **Use when:** Reveals, attacks, big hits.

> add 0.4 s of anticipation: charge glow builds, sound rises

Tier: T1 moments · Pairs with: [reveal](#reveal), [telegraph](#telegraph) · Source: industry

### charge-up

A building glow and sound before a reveal or attack. **Use when:** Summons and big attacks.

> charge up for 0.8 s with particles pulled inward

Tier: T1 moments · Pairs with: [anticipation](#anticipation), [tier tell](#tier-tell) · Source: Living Effects Lab

### tier tell

A colour or effect that hints at rarity one beat before the reveal. **Use when:** Gacha and chest reveals.

> tint the charge-up by tier one beat before the item appears

Tier: T1 moments · Pairs with: [charge-up](#charge-up), [rarity ladder](#rarity-ladder) · Source: aaa-kit/.claude/skills/reward-moments

### gacha beam

A beam that climbs through rarity tiers before settling on the result. **Use when:** Summons and pulls.

> climb the beam through tier colours, pausing a beat at each threshold passed

Tier: T1 moments · Pairs with: [tier tell](#tier-tell), [reveal](#reveal) · Source: Living Effects Lab

### RNG reel

A strip of items that decelerates onto the result. **Use when:** Crate and egg opening.

> spin a reel that eases out and lands on the pre-rolled result with a small overshoot

Tier: T1 moments · Pairs with: [near-miss](#near-miss), [decide-then-animate](#decide-then-animate) · Source: Living Effects Lab

### near-miss

Showing the next tier up right beside the landing slot. **Use when:** Building tension honestly.

> show a real higher-tier item one slot past the landing

Tier: T1 moments · Pairs with: [RNG reel](#rng-reel) · Source: aaa-kit/.claude/skills/reward-moments

### decide-then-animate

Roll the result on the server first; the animation only reveals it. **Use when:** Every RNG moment.

> roll on the server, send the result, then build the reel to land on it

Tier: T1 moments · Pairs with: [RNG reel](#rng-reel), [server authority](#server-authority) · Source: aaa-kit/.claude/skills/reward-moments

### skippable reveal

Any input jumps the reveal to its final state. **Use when:** All reward moments.

> a tap skips to the final state and restores the world

Tier: T1 moments · Pairs with: [reward sequencing](#reward-sequencing) · Source: aaa-kit/HIERARCHY.md

### card flip

A card rotating from back to face, often with rays behind it. **Use when:** Card and pet reveals.

> flip the card over 300 ms with rarity rays spinning behind the face

Tier: T1 moments · Pairs with: [light rays](#light-rays), [reveal](#reveal) · Source: Living Effects Lab

### chest burst

A chest lid pops, rays spin out and coins arc under gravity. **Use when:** Chest opening.

> pop the lid, spin rays and arc 20 coins under gravity into the counter

Tier: T1 moments · Pairs with: [coin arc](#coin-arc), [light rays](#light-rays) · Source: Living Effects Lab

### coin arc

Coins thrown in parabolas that magnetise into the counter. **Use when:** Payouts.

> arc coins out, bounce once, then magnetise into the coin counter

Tier: T1 moments · Pairs with: [chest burst](#chest-burst), [magnet pickup](#magnet-pickup) · Source: Living Effects Lab

### light rays

Rotating rays behind a revealed item. **Use when:** Legendary+ reveals.

> spin 12 soft rays behind the item at 20°/s, tinted by rarity

Tier: T1 moments · Pairs with: [card flip](#card-flip), [chest burst](#chest-burst) · Source: Living Effects Lab

### level-up

The moment a level is gained: bar fills, bursts, number stamps. **Use when:** Progression.

> fill the XP bar, burst at full, stamp the new level number

Tier: T1 moments · Pairs with: [eased fill](#eased-fill), [stamp](#stamp) · Source: Living Effects Lab

### stamp

A number or word slamming in at large scale then settling. **Use when:** Level numbers, titles.

> stamp the level number in at 2× scale with a 3-frame hold

Tier: T1 moments · Pairs with: [level-up](#level-up), [hit-stop](#hit-stop) · Source: industry

### rebirth implosion

A runaway number collapses, a shockwave resets the screen and the multiplier climbs. **Use when:** Prestige resets.

> collapse the counter into a point, fire a shockwave, then stamp the new multiplier

Tier: T1 moments · Pairs with: [shockwave](#shockwave), [prestige](#prestige) · Source: Living Effects Lab

### portal backdrop

A swirling vortex behind a top-tier reveal. **Use when:** Mythic reveals.

> open a swirling portal behind Mythic reveals only

Tier: T1 moments · Pairs with: [gravitational lens](#gravitational-lens), [reveal](#reveal) · Source: Living Effects Lab

### particle text morph

Hundreds of particles springing between words. **Use when:** Banners and announcements.

> morph 900 particles from the old word to the new banner

Tier: T1 moments · Pairs with: [stamp](#stamp) · Source: Living Effects Lab

### tier threshold burst

A ring burst each time a count-up crosses a rarity threshold. **Use when:** Count-ups on rewards.

> burst a ring and shift colour each time the count passes a tier

Tier: T1 moments · Pairs with: [count-up](#count-up) · Source: Living Effects Lab

### purchase moment

A short celebration confirming a purchase. **Use when:** Shops.

> after buying, play a 0.8 s moment: item pops into its slot, coins fly out

Tier: T1 moments · Pairs with: [call to action](#call-to-action), [coin arc](#coin-arc) · Source: aaa-kit/.claude/skills/prompt-amplifier

### daily reward

A login reward shown as a sequence of claimable days. **Use when:** Retention screens.

> show 7 day tiles; today's pulses; claiming plays a short reveal

Tier: T1 moments · Pairs with: [reward sequencing](#reward-sequencing) · Source: industry

### pity timer

A guarantee that raises odds or forces a high tier after N misses. **Use when:** Gacha fairness.

> guarantee an Epic within 50 pulls and show the pity counter

Tier: T1 moments · Pairs with: [decide-then-animate](#decide-then-animate) · Source: industry


## VFX

### hit-stop

Freezing gameplay for a few frames on impact. **Use when:** Making hits feel heavy.

> add a 2-frame hit-stop on hits and 6 frames on kills

Tier: T2 combat · Pairs with: [screen shake](#screen-shake), [impact flash](#impact-flash), [intensity budget](#intensity-budget) · Source: industry

### screen shake

Offsetting the camera on impact. **Use when:** Impacts and explosions.

> add a 6 px screen shake that decays over 120 ms

Tier: T2 combat · Pairs with: [trauma](#trauma), [hit-stop](#hit-stop) · Source: industry

### trauma

A 0–1 value driving shake as trauma squared, decaying linearly. **Use when:** Stacking multiple hits into shake.

> add 0.35 trauma per hit; shake = 6 px × trauma², decaying in 450 ms

Tier: T2 combat · Pairs with: [screen shake](#screen-shake) · Source: industry

### impact flash

A 1–2 frame white overlay on the struck target. **Use when:** Confirming a hit.

> flash the target white for 1 frame on hit

Tier: T2 combat · Pairs with: [onset frame](#onset-frame), [hit-stop](#hit-stop) · Source: industry

### impact frame

A held, high-contrast inverted frame on a huge hit, anime-style. **Use when:** Boss hits and finales.

> on the boss's final hit show 2 inverted impact frames before colour returns

Tier: T2 combat · Pairs with: [boss rung](#boss-rung), [hit-stop](#hit-stop) · Source: industry

### impact ring

An expanding ring at the hit point. **Use when:** Showing where a hit landed.

> expand a 2 px ring from the hit point to 24 px over 150 ms

Tier: T2 combat · Pairs with: [shockwave](#shockwave) · Source: industry

### shockwave

An expanding ring that flashes and pushes particles outward. **Use when:** Nukes and screen clears.

> fire a shockwave that shoves every particle outward and flashes the screen 30 %

Tier: T2 combat · Pairs with: [impact ring](#impact-ring), [distortion](#distortion) · Source: Living Effects Lab

### distortion

Bending the image around an effect (heat haze, shockwave refraction). **Use when:** Big explosions and heat.

> distort the background in a ring behind the shockwave

Tier: T2 combat · Pairs with: [shockwave](#shockwave), [refraction](#refraction) · Source: industry

### muzzle flash

A 1–2 frame burst of light at a weapon's barrel. **Use when:** Shooting.

> show a 2-frame muzzle flash and a 1-frame light pop

Tier: T2 combat · Pairs with: [onset frame](#onset-frame) · Source: industry

### trail

A fading ribbon behind a moving object. **Use when:** Swings, projectiles, dashes.

> trail the blade with a ribbon that fades over 120 ms

Tier: T2 combat · Pairs with: [swing smear](#swing-smear), [ribbon](#ribbon) · Source: industry

### swing smear

A stretched arc drawn along a melee swing's path. **Use when:** Melee attacks.

> draw a 3-frame swing smear following the blade arc

Tier: T2 combat · Pairs with: [trail](#trail), [cel VFX](#cel-vfx) · Source: vault/Notes/22 Cel VFX

### cel VFX

Hand-drawn-style effects with flat colour shapes and hard edges. **Use when:** Stylised games.

> use cel VFX: flat colour bursts with 2–3 tones and hard edges

Tier: T2 combat · Pairs with: [swing smear](#swing-smear), [toon ramp](#toon-ramp) · Source: vault/Notes/22 Cel VFX

### branching lightning

Bolts built by midpoint displacement with forks. **Use when:** Chain lightning.

> strike with a midpoint-displaced bolt, two forks and a 1-frame screen flash

Tier: T2 combat · Pairs with: [midpoint displacement](#midpoint-displacement), [glow](#glow) · Source: Living Effects Lab

### chain lightning

Lightning jumping from target to target. **Use when:** Multi-target attacks.

> chain to 4 targets within 120 px, 60 ms per jump

Tier: T2 combat · Pairs with: [branching lightning](#branching-lightning) · Source: industry

### ember dissolve

A noise-threshold burn-away with a glowing edge. **Use when:** Death and despawn.

> dissolve the corpse with noise and a 2 px glowing ember edge over 400 ms

Tier: T2 combat · Pairs with: [dissolve threshold](#dissolve-threshold), [value noise](#value-noise) · Source: Living Effects Lab

### dissolve threshold

A rising cutoff on a noise texture that removes pixels below it. **Use when:** Any dissolve.

> raise the dissolve threshold from 0 to 1 over 0.4 s

Tier: T2 combat · Pairs with: [ember dissolve](#ember-dissolve) · Source: industry

### shatter

Splitting a surface into triangles that fly from the impact. **Use when:** Breaking shields and glass.

> shatter the shield into jittered triangles flying from the hit point

Tier: T2 combat · Pairs with: [Voronoi](#voronoi), [impact ring](#impact-ring) · Source: Living Effects Lab

### aura

A persistent effect around a character showing a passive state. **Use when:** Buffs and passives.

> breathe a cellular-automaton aura ring around the hero, 30 % alpha

Tier: T2 combat · Pairs with: [protected region](#protected-region) · Source: Living Effects Lab

### time freeze

Halting motion with a cold tint and a sweeping clock hand. **Use when:** Stopwatch and freeze powers.

> freeze the world, tint it cold, sweep a clock hand over 1 s

Tier: T2 combat · Pairs with: [hit-stop](#hit-stop) · Source: Living Effects Lab

### magnet vortex

Pickups spiralling into a point with stretched streaks. **Use when:** Collecting and magnets.

> spiral pickups into the player with motion-stretched streaks

Tier: T2 combat · Pairs with: [magnet pickup](#magnet-pickup) · Source: Living Effects Lab

### magnet pickup

Pickups accelerating toward the collector once in range. **Use when:** XP gems and coins.

> accelerate gems toward the player within 80 px, ease-in, arrive in 0.3 s

Tier: T2 combat · Pairs with: [magnet vortex](#magnet-vortex), [coin arc](#coin-arc) · Source: industry

### plasma orb

Crawling noise inside a glass sphere. **Use when:** Charge-ups and energy items.

> fill the orb with crawling plasma noise and a Fresnel glass rim

Tier: T2 combat · Pairs with: [charge-up](#charge-up), [glass](#glass) · Source: Living Effects Lab

### glyph rain

Falling glyph columns with bright heads and fading tails. **Use when:** Digital zones.

> rain glyph columns with bright heads and 12-glyph fading tails

Tier: T2 combat · Pairs with: [glyph ramp](#glyph-ramp) · Source: Living Effects Lab

### telegraph

A warning shape showing where an attack will land. **Use when:** Boss and enemy attacks.

> draw the attack's real area in red 0.6 s before it lands, filling as it charges

Tier: T2 combat · Pairs with: [anticipation](#anticipation), [danger red](#danger-red) · Source: industry

### kill chain

Short arcs linking consecutive kills across a crowd. **Use when:** Crowd clears.

> link each kill to the next within 80 px with a short arc

Tier: T2 combat · Pairs with: [branching lightning](#branching-lightning), [decoration slot](#decoration-slot) · Source: cursed-survivors/docs/look

### bloom

Bright areas bleeding light into their surroundings. **Use when:** True light sources.

> bloom only true emitters: threshold 0.9, intensity from the rung

Tier: all · Pairs with: [glow](#glow), [intensity budget](#intensity-budget) · Source: industry

### glow

A soft halo around a bright shape. **Use when:** Emitters and active states.

> add a soft glow only while the item is active

Tier: all · Pairs with: [bloom](#bloom), [SDF glow](#sdf-glow) · Source: industry

### additive blending

Adding colour values together so overlaps get brighter. **Use when:** Light, fire, sparks.

> draw sparks with additive blending so overlaps brighten

Tier: all · Pairs with: [glow](#glow) · Source: industry

### particle budget

A cap on live particles per system and per screen. **Use when:** Performance and clarity.

> cap the burst at 40 particles, scaled by the rung's particle multiplier

Tier: all · Pairs with: [decoration slot](#decoration-slot), [intensity budget](#intensity-budget) · Source: industry

### burst emit

Emitting a fixed number of particles at once instead of a stream. **Use when:** Impacts and pickups.

> emit 12 particles in one burst instead of a continuous emitter

Tier: all · Pairs with: [particle budget](#particle-budget) · Source: industry

### sub-emitter

A particle that spawns its own particles (sparks from a spark). **Use when:** Fireworks and debris.

> give each firework shell a sub-emitter of 8 sparks on death

Tier: all · Pairs with: [burst emit](#burst-emit) · Source: industry

### motion blur

Stretching a fast object along its motion. **Use when:** Fast projectiles and pickups.

> stretch fast sprites along velocity by up to 3× their length

Tier: all · Pairs with: [trail](#trail) · Source: industry

### afterimage

Fading copies of a sprite along its path. **Use when:** Dashes and teleports.

> leave 4 afterimages 30 ms apart that fade over 150 ms

Tier: T2 combat · Pairs with: [trail](#trail) · Source: industry

### dust puff

Small soft clouds where something lands or turns. **Use when:** Grounding movement.

> puff 3 dust sprites on landing and sharp turns

Tier: T2 combat · Pairs with: [burst emit](#burst-emit) · Source: industry

### debris

Small pieces flying from an impact under gravity. **Use when:** Breakables and explosions.

> throw 6 debris chips with gravity and one bounce

Tier: T2 combat · Pairs with: [sub-emitter](#sub-emitter) · Source: industry

### ribbon

A strip of geometry following a path, textured and faded. **Use when:** Trails, beams, banners.

> build the trail as a ribbon of quads that fade along their length

Tier: T2 combat · Pairs with: [trail](#trail), [Beam](#beam) · Source: industry

### Beam

Roblox's textured strip between two attachments. **Use when:** Lasers and lightning in Roblox.

> draw the laser as a Beam and animate its CurveSize

Tier: T2 combat · Pairs with: [ribbon](#ribbon), [chain lightning](#chain-lightning) · Source: industry

### Highlight

Roblox's outline-and-fill effect on a model. **Use when:** Hit flashes and selection.

> flash the hit enemy with a white Highlight for one frame

Tier: T2 combat · Pairs with: [impact flash](#impact-flash) · Source: industry

### ParticleEmitter

Roblox's particle system component. **Use when:** Sparks, dust, magic.

> call ParticleEmitter:Emit(12) on hit instead of leaving it enabled

Tier: T2 combat · Pairs with: [burst emit](#burst-emit) · Source: industry

### flipbook

An animated texture played from a grid of frames. **Use when:** Explosions and smoke.

> play the explosion as a 4×4 flipbook at 24 fps

Tier: all · Pairs with: [cel VFX](#cel-vfx) · Source: industry

### spark

A tiny bright fast particle. **Use when:** Impacts and metal hits.

> emit 6 sparks with gravity, additive, 150 ms life

Tier: T2 combat · Pairs with: [decoration slot](#decoration-slot), [additive blending](#additive-blending) · Source: industry

### heat haze

Wavy distortion above hot surfaces. **Use when:** Lava and fire.

> add a subtle heat haze above the lava, 2 px amplitude

Tier: T4 world · Pairs with: [distortion](#distortion) · Source: industry


## Materials

### holo foil

A trading-card foil whose rainbow shifts with tilt and a sheen band sweeps. **Use when:** Mythic and shiny variants.

> give Mythic cards holo foil: hue shifts with tilt, sheen follows the pointer

Tier: T5 materials · Pairs with: [Fresnel](#fresnel), [iridescence](#iridescence) · Source: Living Effects Lab

### brushed metal

Streak texture with an anisotropic highlight along the grain. **Use when:** Metal UI panels, Rare items.

> brushed metal: horizontal streaks with a highlight stretched along the grain

Tier: T5 materials · Pairs with: [anisotropic highlight](#anisotropic-highlight) · Source: Living Effects Lab

### anisotropic highlight

A highlight stretched in one direction by surface grain. **Use when:** Brushed metal and hair.

> stretch the highlight 6× along the grain direction

Tier: T5 materials · Pairs with: [brushed metal](#brushed-metal) · Source: industry

### chrome

A mirror metal reflecting its environment with high contrast. **Use when:** Legendary and premium items.

> liquid chrome: dark base, sharp white highlights, reflected sky gradient

Tier: T5 materials · Pairs with: [environment reflection](#environment-reflection), [Fresnel](#fresnel) · Source: Living Effects Lab

### faceted gem

A cut gem whose facets light up as it turns, with star glints. **Use when:** Currency icons and gem items.

> facet the gem into 8 sides that brighten as they face the light

Tier: T5 materials · Pairs with: [star glint](#star-glint) · Source: Living Effects Lab

### star glint

A four-point sparkle on a highlight. **Use when:** Gems and polished metal.

> add at most 3 star glints at once, each 200 ms

Tier: T5 materials · Pairs with: [faceted gem](#faceted-gem) · Source: industry

### glass

A surface showing mostly what's behind it with a bright rim and chromatic edges. **Use when:** Potions and lens UI.

> glass: refract the background, thin bright rim, slight chromatic split at edges

Tier: T5 materials · Pairs with: [refraction](#refraction), [Fresnel](#fresnel) · Source: Living Effects Lab

### crystal

A raymarched or faceted transparent solid with internal colour. **Use when:** Gem items and crystals.

> a crystal with deeper internal colour than its surface and sharp facet edges

Tier: T5 materials · Pairs with: [faceted gem](#faceted-gem), [SDF](#sdf) · Source: Living Effects Lab

### soap film

Thin-film interference colours flowing across a bubble. **Use when:** Bubble pets and shields.

> flow thin-film colours across the bubble with a slow swirl

Tier: T5 materials · Pairs with: [thin-film interference](#thin-film-interference) · Source: Living Effects Lab

### molten

Plasma noise through a black-body heat ramp with a cooling crust. **Use when:** Lava zones and forges.

> molten core: noise through a black-body ramp with dark crust cracks

Tier: T5 materials · Pairs with: [black-body ramp](#black-body-ramp) · Source: Living Effects Lab

### black-body ramp

A colour ramp from black through red, orange and yellow to white by temperature. **Use when:** Heat, fire, lava.

> colour heat with a black-body ramp: black → red → orange → white

Tier: T5 materials · Pairs with: [molten](#molten) · Source: industry

### emissive

A surface that emits its own light. **Use when:** Lights and active states.

> make only active elements emissive; turn emission off when inactive

Tier: T5 materials · Pairs with: [bloom](#bloom) · Source: industry

### satin

A soft sheen between flat and metallic. **Use when:** Uncommon items.

> satin finish: one soft broad highlight, no sparkle

Tier: T5 materials · Pairs with: [rarity-as-material](#rarity-as-material) · Source: aaa-kit/HIERARCHY.md

### void material

A starfield seen through the surface with glitch slices on the rim. **Use when:** Secret rarity.

> void material: parallax starfield inside, glitch slices on the rim

Tier: T5 materials · Pairs with: [glitch slice](#glitch-slice) · Source: aaa-kit/.claude/skills/materials

### glitch slice

Horizontal bands of an image shifted sideways for a frame. **Use when:** Secret items and digital corruption.

> shift 1–2 horizontal slices 4 px sideways for one frame every second

Tier: T5 materials · Pairs with: [void material](#void-material) · Source: Living Effects Lab

### Fresnel

Surfaces reflect more at grazing angles; the rim gets brighter. **Use when:** Glass, water, rims.

> add a Fresnel rim: pow(1 − dot(n, v), 5)

Tier: T5 materials · Pairs with: [rim light](#rim-light) · Source: industry

### rim light

A bright edge on the side away from the main light. **Use when:** Separating a figure from its background.

> add a cool rim light so the hero separates from dark ground

Tier: all · Pairs with: [Fresnel](#fresnel), [figure-ground gate](#figure-ground-gate) · Source: industry

### PBR

Physically based rendering with albedo, normal, metalness and roughness maps. **Use when:** 3D surfaces.

> author PBR maps: albedo, normal, metalness, roughness

Tier: T5 materials · Pairs with: [SurfaceAppearance](#surfaceappearance) · Source: industry

### roughness

How blurry a surface's reflections are. **Use when:** Material tuning.

> roughness 0.15 for polished gold, 0.6 for worn iron

Tier: T5 materials · Pairs with: [PBR](#pbr) · Source: industry

### environment reflection

Reflecting the surrounding sky or scene on a surface. **Use when:** Metals and glass.

> reflect the sky gradient in the chrome so it reads as metal

Tier: T5 materials · Pairs with: [chrome](#chrome) · Source: industry

### toon ramp

Lighting quantised into 2–4 flat steps. **Use when:** Cel shading.

> light with a 3-step toon ramp and a hard terminator

Tier: T5 materials · Pairs with: [luminance band](#luminance-band), [cel VFX](#cel-vfx) · Source: industry

### iridescence

Colour that shifts with viewing angle. **Use when:** Foil, beetle shells, oil.

> iridescent hue = view angle × film thickness

Tier: T5 materials · Pairs with: [thin-film interference](#thin-film-interference), [holo foil](#holo-foil) · Source: industry

### cel shading

Rendering with flat colour bands and hard shadow edges. **Use when:** Stylised 3D or 2D.

> cel-shade with two light bands and a hard terminator

Tier: T5 materials · Pairs with: [toon ramp](#toon-ramp) · Source: industry

### normal map

A texture storing surface direction for lighting detail. **Use when:** Detail without geometry.

> bake a normal map for the bevelled edges

Tier: T5 materials · Pairs with: [PBR](#pbr) · Source: industry

### matcap

Lighting looked up from a sphere image by surface normal. **Use when:** Cheap stylised metal and clay.

> shade the icon with a chrome matcap for a cheap metal look

Tier: T5 materials · Pairs with: [chrome](#chrome) · Source: industry

### UV-space bake

Rasterising a mesh into its own UV layout and computing every texel from the 3D surface point behind it. **Use when:** Putting any algorithm texture on a real model asset.

> bake the recipe onto the mesh's UVs with surfacebake, evaluated in object space so seams vanish

Tier: T5 materials · Pairs with: [triplanar projection](#triplanar-projection), [edge wear](#edge-wear), [gutter padding](#gutter-padding), [normal map](#normal-map) · Source: aaa-kit/lib/surfacebake

### triplanar projection

Sampling a tiling 2D texture three times along X, Y and Z and blending by the surface normal. **Use when:** Wrapping a 2D algorithm render (reaction-diffusion, CA) onto any mesh without UV seams.

> project the reaction-diffusion tile triplanar at scale 0.5 with sharpness 4

Tier: T5 materials · Pairs with: [UV-space bake](#uv-space-bake) · Source: aaa-kit/lib/surfacebake/Noise.luau

### edge wear

Chipped paint, bare metal or polish along sharp edges, keyed on distance to the edge in studs and broken up by noise. **Use when:** Props that should look handled and used.

> chip the paint within 0.09 studs of sharp edges, multiplied by noise so it is irregular

Tier: T5 materials · Pairs with: [UV-space bake](#uv-space-bake), [roughness](#roughness) · Source: aaa-kit/docs/playbooks/procedural-textures.md

### gutter padding

Copying border texels outward around every UV island so mipmaps and filtering never pull in background colour. **Use when:** Every baked texture.

> dilate each island by 4 texels at 512 before uploading

Tier: T5 materials · Pairs with: [UV-space bake](#uv-space-bake) · Source: aaa-kit/lib/surfacebake/Raster.luau

### texel density

Texels per stud on the surface; uneven density makes some faces blurry and others sharp. **Use when:** Choosing texture size and UV layouts.

> keep texel density even: 256 px per 2-stud prop, 1024 only for hero props

Tier: T5 materials · Pairs with: [UV-space bake](#uv-space-bake) · Source: industry

### height-to-normal

Deriving a tangent-space normal map from a height field by finite differences along the tangent frame. **Use when:** Making painted detail catch the light.

> give rust +height and chips -height and derive an OpenGL normal map from it

Tier: T5 materials · Pairs with: [normal map](#normal-map), [UV-space bake](#uv-space-bake) · Source: aaa-kit/lib/surfacebake/Bake.luau

### parallax occlusion mapping

Marching the view ray into a height field per texel so bumps occlude each other on a flat surface. **Use when:** Portals, grates, gem interiors, lava pits without extra geometry.

> render a 128px parallax-occlusion window with 16 steps, updated when the camera angle changes

Tier: T5 materials · Pairs with: [height-to-normal](#height-to-normal), [interior mapping](#interior-mapping) · Source: aaa-kit/lib/surfacebake/Parallax.luau

### interior mapping

One ray-box hit per texel draws a whole room behind each window of a flat facade. **Use when:** City facades and windows at distance.

> fake rooms behind every window with interior mapping instead of modelling interiors

Tier: T4 world · Pairs with: [parallax occlusion mapping](#parallax-occlusion-mapping) · Source: aaa-kit/lib/surfacebake/Parallax.luau

### shell texturing

Stacked copies of a mesh pushed out along normals, each with a sparser alpha mask, giving strands real depth. **Use when:** Fur, grass, moss, velvet on close-up props and pets.

> build 12 fur shells with tapering strand masks and drop to 4 shells at distance

Tier: T5 materials · Pairs with: [UV-space bake](#uv-space-bake) · Source: aaa-kit/lib/surfacebake/Parallax.luau

### infinite zoom

Octaves of a tile at doubling scales blended over log-scale so zooming never loops visibly. **Use when:** Portals, loading screens, falling-into-the-void moments.

> infinite-zoom the reaction-diffusion tile with 6 octaves and a slight spiral

Tier: T1 moments · Pairs with: [octave blend](#octave-blend) · Source: aaa-kit/lib/surfacebake/Parallax.luau

### octave blend

Weighting copies of a pattern at scales 2^k with a window over log-scale so the sum is self-similar. **Use when:** Infinite zooms and scale-free detail.

> weight each octave by sin^2 over its log-scale position so the loop is invisible

Tier: all · Pairs with: [infinite zoom](#infinite-zoom) · Source: aaa-kit/lib/surfacebake/Parallax.luau

### baked-field animation

Precomputing expensive per-texel fields once so each animation frame is only arithmetic over buffers. **Use when:** Realtime moving surfaces on Roblox clients.

> prepare the rune mask and phase once, then pulse it every frame for under a millisecond

Tier: T3 HUD · Pairs with: [amortised update](#amortised-update), [UV-space bake](#uv-space-bake) · Source: aaa-kit/lib/surfacebake/Animate.luau

### amortised update

Spreading a fixed per-frame budget of work over several frames, round-robin. **Use when:** Any per-frame image work that would blow the frame budget.

> refresh 32 rows of the 256px texture per frame so the whole image updates every 8 frames

Tier: all · Pairs with: [frame budget](#frame-budget), [baked-field animation](#baked-field-animation) · Source: aaa-kit/lib/surfacebake/Animate.luau

### dissolve edge

A noise-threshold dissolve with a hot rim where the threshold crosses the surface. **Use when:** Deaths, teleports, reveals.

> dissolve the enemy over 0.8 s with an orange 0.08-wide burning rim

Tier: T2 combat · Pairs with: [baked-field animation](#baked-field-animation) · Source: aaa-kit/lib/surfacebake/Animate.luau

### reactive surface

A texture with per-texel state (heat, frost) that hits, other effects and the object's motion change over time. **Use when:** Impacts that leave marks, elemental fights on a surface, shields that respond.

> make the boss armour a reactive surface: hits heat it, ice spells freeze it, heat melts the ice

Tier: T2 combat · Pairs with: [baked-field animation](#baked-field-animation), [effect coupling](#effect-coupling) · Source: aaa-kit/lib/surfacebake/React.luau

### effect coupling

One effect's state feeding another's (frost suppresses lava flow, flow heat melts frost) so effects interact instead of stacking. **Use when:** Making elemental systems feel physical.

> couple the lava flow to the frost field so ice visibly stops the flow

Tier: all · Pairs with: [reactive surface](#reactive-surface) · Source: aaa-kit/lib/surfacebake/React.luau


## Shaders & SDF

### signed distance field

A function returning distance to a shape's edge, negative inside. **Use when:** Shapes with soft edges, outlines and glows.

> build the shape as a signed distance field and derive fill, outline and glow from it

Tier: T6 engines · Pairs with: [smooth union](#smooth-union), [SDF glow](#sdf-glow) · Source: aaa-kit/.claude/skills/shaders-and-sdf

### SDF

Short for signed distance field. **Use when:** Any procedural shape.

> draw the panel as an SDF rounded box with 1 px anti-aliasing

Tier: T6 engines · Pairs with: [signed distance field](#signed-distance-field) · Source: aaa-kit/.claude/skills/shaders-and-sdf

### smooth union

Blending two SDFs with a smooth minimum so they merge like liquid. **Use when:** Metaballs and organic shapes.

> merge the blobs with a smooth union, k = 0.4

Tier: T6 engines · Pairs with: [signed distance field](#signed-distance-field), [metaball](#metaball) · Source: industry

### metaball

Blobs that merge when close, built from smooth unions. **Use when:** Liquid UI, slimes.

> render health orbs as metaballs that merge as they fill

Tier: T6 engines · Pairs with: [smooth union](#smooth-union) · Source: Living Effects Lab

### SDF glow

A falloff computed from distance outside a shape. **Use when:** Cheap glows.

> glow = (1 − d / 12)² outside the shape

Tier: T6 engines · Pairs with: [signed distance field](#signed-distance-field), [glow](#glow) · Source: aaa-kit/.claude/skills/shaders-and-sdf

### analytic anti-aliasing

Edge smoothing from the distance value (clamp(0.5 − d)). **Use when:** Crisp SDF edges.

> anti-alias with coverage = clamp(0.5 − d, 0, 1)

Tier: T6 engines · Pairs with: [SDF](#sdf) · Source: industry

### raymarching

Rendering by stepping along rays by the SDF distance until hitting a surface. **Use when:** 3D procedural scenes in shaders.

> raymarch the scene with up to 128 steps and an early out at 0.0005

Tier: T6 engines · Pairs with: [sphere tracing](#sphere-tracing), [soft shadow](#soft-shadow) · Source: industry

### sphere tracing

Raymarching where each step is the distance to the nearest surface. **Use when:** SDF scenes.

> sphere-trace the SDF scene and stop at 12 units

Tier: T6 engines · Pairs with: [raymarching](#raymarching) · Source: industry

### soft shadow

Penumbra estimated from the closest SDF approach along the light ray. **Use when:** Raymarched lighting.

> soft shadows: res = min(res, 10·h/t) along the light ray

Tier: T6 engines · Pairs with: [raymarching](#raymarching) · Source: industry

### ambient occlusion

Darkening creases where ambient light can't reach. **Use when:** Grounding objects.

> add 5-tap SDF ambient occlusion in the creases

Tier: all · Pairs with: [soft shadow](#soft-shadow) · Source: industry

### value noise

Smooth noise from interpolated random values on a grid. **Use when:** Cheap organic variation.

> use hashed value noise so results are seedable

Tier: T6 engines · Pairs with: [fBm](#fbm), [hash function](#hash-function) · Source: industry

### gradient noise

Noise from interpolated random gradients (Perlin, simplex). **Use when:** Smoother natural noise.

> use gradient noise for terrain to avoid blocky artefacts

Tier: T6 engines · Pairs with: [value noise](#value-noise), [fBm](#fbm) · Source: industry

### fBm

Fractal Brownian motion: summed octaves of noise at doubling frequency and halving amplitude. **Use when:** Clouds, terrain, fire.

> 5-octave fBm, lacunarity 2, gain 0.5

Tier: T6 engines · Pairs with: [octave](#octave), [domain warping](#domain-warping) · Source: industry

### octave

One layer of fBm at a given frequency. **Use when:** Tuning noise detail.

> add octaves until the detail stops showing at play size

Tier: T6 engines · Pairs with: [fBm](#fbm) · Source: industry

### domain warping

Offsetting noise input by another noise for swirling organic shapes. **Use when:** Marble, smoke, corruption.

> warp the noise domain by a second fBm at strength 4

Tier: T6 engines · Pairs with: [fBm](#fbm) · Source: industry

### hash function

A fast deterministic function turning coordinates into pseudo-random numbers. **Use when:** Seedable randomness in shaders and Luau.

> hash cell coordinates instead of calling the RNG

Tier: T6 engines · Pairs with: [value noise](#value-noise) · Source: industry

### thin-film interference

Colour from light reflecting off two surfaces of a thin layer. **Use when:** Soap, oil, beetles.

> hue = fract(k · thickness · cos θ) through a spectral palette

Tier: T5 materials · Pairs with: [iridescence](#iridescence), [soap film](#soap-film) · Source: industry

### refraction

Light bending through a surface, offsetting what's seen behind. **Use when:** Glass and water.

> offset the background sample by the surface normal × 0.03

Tier: T5 materials · Pairs with: [glass](#glass), [distortion](#distortion) · Source: industry

### gravitational lens

Bending the background around a point mass. **Use when:** Black holes and portals.

> lens the background: offset = normalize(p) · k / distance

Tier: T1 moments · Pairs with: [portal backdrop](#portal-backdrop) · Source: Living Effects Lab

### chromatic aberration

Splitting colour channels slightly at edges. **Use when:** Glass, impact, glitch.

> split RGB by 1 px at the edges of the lens only

Tier: all · Pairs with: [glass](#glass) · Source: industry

### dithering

Using patterned pixels to suggest in-between tones. **Use when:** Pixel-art gradients.

> dither band edges with an 8×8 Bayer pattern

Tier: T6 engines · Pairs with: [Bayer matrix](#bayer-matrix) · Source: industry

### Bayer matrix

A fixed threshold pattern for ordered dithering. **Use when:** Stable dithering in pixel art.

> ordered dither with an 8×8 Bayer matrix so the pattern doesn't crawl

Tier: T6 engines · Pairs with: [dithering](#dithering) · Source: industry

### interleaved gradient noise

A screen-space noise for dithering smooth gradients without banding. **Use when:** Removing banding.

> dither gradients with interleaved gradient noise

Tier: T6 engines · Pairs with: [dithering](#dithering) · Source: industry

### OKLab

A perceptual colour space where equal steps look equal. **Use when:** Palettes, bands and gradients.

> mix colours and measure lightness in OKLab, not sRGB

Tier: all · Pairs with: [luminance band](#luminance-band) · Source: industry

### tone mapping

Compressing high-dynamic-range colour into displayable range. **Use when:** Bright scenes and bloom.

> tone-map with ACES so highlights roll off instead of clipping

Tier: all · Pairs with: [bloom](#bloom) · Source: industry

### gamma correction

Converting between linear light and display sRGB. **Use when:** Any lighting maths.

> light in linear space and convert to sRGB at the end

Tier: all · Pairs with: [OKLab](#oklab) · Source: industry

### full-screen triangle

One oversized triangle covering the screen for a fragment shader pass. **Use when:** Shader post passes.

> draw the pass with a single full-screen triangle

Tier: T6 engines · Pairs with: [raymarching](#raymarching) · Source: industry

### ping-pong buffer

Two textures alternating as input and output across simulation steps. **Use when:** GPU simulations.

> run reaction-diffusion in ping-pong buffers, 8 steps per frame

Tier: T6 engines · Pairs with: [reaction-diffusion](#reaction-diffusion) · Source: industry


## Algorithms

### godrithm

A chain of small typed algorithm passes that together make one look. **Use when:** Building a reusable procedural look.

> build the look as a godrithm: noise → warp → threshold → distance → bands

Tier: T6 engines · Pairs with: [pass chain](#pass-chain), [typed pass](#typed-pass) · Source: vault/Notes/21 Godrithms

### pass chain

An ordered list of passes where each output feeds the next. **Use when:** Composing procedural effects.

> run the passes as a chain and cache every static intermediate

Tier: T6 engines · Pairs with: [godrithm](#godrithm), [typed pass](#typed-pass) · Source: aaa-kit/.claude/skills/algorithms

### typed pass

A pass with a declared input and output type (field, mask, points, palette). **Use when:** Making passes swappable.

> declare each pass as field → field so they can be reordered

Tier: T6 engines · Pairs with: [pass chain](#pass-chain) · Source: aaa-kit/.claude/skills/algorithms

### algorithm factory

A planner that assembles a pass chain backwards from a requested output. **Use when:** Generating looks on demand.

> let a planner pick the cheapest chain that produces a glow mask

Tier: T6 engines · Pairs with: [godrithm](#godrithm) · Source: vault/Artifacts/Godrithms/algorithm-factory

### distance transform

Computing each cell's distance to the nearest feature. **Use when:** Outlines, glows, bevels, fields.

> compute a chamfer distance transform from the mask for a 6 px glow

Tier: T6 engines · Pairs with: [jump flooding](#jump-flooding), [signed distance field](#signed-distance-field) · Source: industry

### jump flooding

A GPU algorithm computing Voronoi and distance fields in log₂(n) passes. **Use when:** Fast distance fields on the GPU.

> build the distance field with jump flooding in 9 passes for 512²

Tier: T6 engines · Pairs with: [distance transform](#distance-transform), [Voronoi](#voronoi) · Source: industry

### Voronoi

Partitioning space into cells around seed points. **Use when:** Stained glass, cracks, biomes.

> partition the map into Voronoi cells for biomes

Tier: T6 engines · Pairs with: [Worley noise](#worley-noise), [jump flooding](#jump-flooding) · Source: industry

### Worley noise

Noise based on distance to the nearest random feature points. **Use when:** Cells, scales, caustics.

> use Worley F2 − F1 for crisp cell edges

Tier: T6 engines · Pairs with: [Voronoi](#voronoi) · Source: industry

### cellular automaton

A grid where each cell updates from local rules. **Use when:** Caves, fire spread, life patterns.

> carve caves with 5 steps of the 4-5 cellular automaton rule

Tier: T6 engines · Pairs with: [Game of Life](#game-of-life) · Source: industry

### Game of Life

Conway's cellular automaton with birth on 3 and survival on 2–3 neighbours. **Use when:** Living patterns.

> seed a Game of Life aura that breathes around the hero

Tier: T6 engines · Pairs with: [cellular automaton](#cellular-automaton) · Source: industry

### reaction-diffusion

Two simulated chemicals (Gray–Scott) forming spots and stripes. **Use when:** Coral, infection, skin patterns.

> grow corruption as Gray–Scott reaction-diffusion with f 0.037, k 0.06

Tier: T6 engines · Pairs with: [Gray–Scott](#gray-scott), [ping-pong buffer](#ping-pong-buffer) · Source: Living Effects Lab

### Gray–Scott

The reaction-diffusion model with feed and kill rates. **Use when:** Tuning reaction-diffusion.

> Gray–Scott with feed 0.055 and kill 0.062 for mitosis spots

Tier: T6 engines · Pairs with: [reaction-diffusion](#reaction-diffusion) · Source: industry

### flow field

A grid of directions that particles or agents follow. **Use when:** Crowds, wind, silk backgrounds.

> steer the crowd with a flow field toward the player, updated at 10 Hz

Tier: T6 engines · Pairs with: [boids](#boids), [Dijkstra map](#dijkstra-map) · Source: Living Effects Lab

### boids

Flocking from separation, alignment and cohesion. **Use when:** Birds, fish, bats.

> flock 200 boids with a spatial hash for neighbours

Tier: T6 engines · Pairs with: [flow field](#flow-field), [spatial hash](#spatial-hash) · Source: Living Effects Lab

### spatial hash

Bucketing objects by grid cell for fast neighbour queries. **Use when:** Collision and separation at scale.

> hash enemies into 32 px cells and only test neighbouring cells

Tier: T6 engines · Pairs with: [boids](#boids) · Source: industry

### quadtree

A tree that splits 2D space into four children as it fills. **Use when:** Uneven densities, culling.

> use a quadtree when entities cluster unevenly

Tier: T6 engines · Pairs with: [spatial hash](#spatial-hash) · Source: industry

### A*

Pathfinding with a heuristic toward the goal. **Use when:** Single-agent paths.

> path single units with A* on the nav grid

Tier: T6 engines · Pairs with: [Dijkstra map](#dijkstra-map) · Source: industry

### Dijkstra map

A distance-to-goal value for every cell, shared by all agents. **Use when:** Many agents chasing one target.

> build one Dijkstra map from the player and let every enemy descend it

Tier: T6 engines · Pairs with: [flow field](#flow-field), [A*](#a) · Source: industry

### L-system

A grammar that rewrites strings into branching structures. **Use when:** Trees, lightning, coral.

> grow trees with an L-system: F → F[+F]F[−F]F, 4 iterations

Tier: T6 engines · Pairs with: [turtle graphics](#turtle-graphics) · Source: Living Effects Lab

### turtle graphics

Drawing by moving and turning a pen from instructions. **Use when:** Rendering L-systems.

> interpret the L-system string with turtle graphics, 25° turns

Tier: T6 engines · Pairs with: [L-system](#l-system) · Source: industry

### midpoint displacement

Recursively offsetting segment midpoints for fractal lines. **Use when:** Lightning, coastlines, cracks.

> displace midpoints 5 times, halving the offset each time

Tier: T6 engines · Pairs with: [branching lightning](#branching-lightning) · Source: industry

### Verlet integration

Physics from current and previous positions; stable for ropes and cloth. **Use when:** Whips, cloth, chains.

> simulate the rope with Verlet integration and 8 constraint passes

Tier: T6 engines · Pairs with: [Verlet cloth](#verlet-cloth) · Source: Living Effects Lab

### Verlet cloth

A pinned grid of Verlet points shaded by its folds. **Use when:** Flags, banners, capes.

> flap the banner as a pinned Verlet cloth in gusting wind

Tier: T4 world · Pairs with: [Verlet integration](#verlet-integration) · Source: Living Effects Lab

### Poisson disk

Random points no closer than a minimum distance. **Use when:** Even, natural-looking scatter.

> scatter trees with Poisson disk at 12 stud spacing

Tier: T6 engines · Pairs with: [Bridson sampling](#bridson-sampling), [scatter mask](#scatter-mask) · Source: aaa-kit/.claude/skills/procedural-world

### Bridson sampling

The O(n) Poisson-disk algorithm using a background grid. **Use when:** Fast Poisson scatter.

> sample with Bridson's algorithm, 30 tries per active point

Tier: T6 engines · Pairs with: [Poisson disk](#poisson-disk) · Source: industry

### marching squares

Turning a scalar field into contour lines. **Use when:** Outlining blobs and terrain.

> extract the island outline with marching squares at 0.5

Tier: T6 engines · Pairs with: [metaball](#metaball) · Source: industry

### wave function collapse

Tile placement by propagating adjacency constraints. **Use when:** Tile-based levels.

> generate rooms with wave function collapse over a 12-tile set

Tier: T6 engines · Pairs with: [tileset](#tileset) · Source: industry

### seeded RNG

A random generator started from a seed so results repeat. **Use when:** Deterministic generation.

> pass a seeded RNG into every generator; never call the global one

Tier: T6 engines · Pairs with: [determinism](#determinism) · Source: industry

### determinism

Same inputs always give the same outputs. **Use when:** Replays, tests, shared worlds.

> make the generator deterministic so one seed rebuilds the world

Tier: all · Pairs with: [seeded RNG](#seeded-rng), [golden frame](#golden-frame) · Source: industry

### glyph ramp

Characters ordered by visual density used to shade with text. **Use when:** ASCII renderers.

> shade with the glyph ramp " .:-=+*#%@" by luminance

Tier: T6 engines · Pairs with: [glyph density](#glyph-density), [ASCII renderer](#ascii-renderer) · Source: Living Effects Lab

### ASCII renderer

Rendering a scene as characters chosen by luminance and edge direction. **Use when:** Retro modes and crowd LOD.

> render the sphere per character cell with edge glyphs slash, pipe, backslash and dash

Tier: T6 engines · Pairs with: [glyph ramp](#glyph-ramp) · Source: Living Effects Lab

### palette quantisation

Snapping colours to a fixed palette. **Use when:** Consistent pixel-art looks.

> quantise to an 8-band OKLab palette with dithered edges

Tier: T6 engines · Pairs with: [luminance band](#luminance-band), [dithering](#dithering) · Source: cursed-survivors/docs/decisions.md

### kuwahara filter

An edge-preserving smoothing filter that looks painterly. **Use when:** Painterly post effects.

> apply an anisotropic Kuwahara filter for a painted look

Tier: T6 engines · Pairs with: [pass chain](#pass-chain) · Source: vault/Artifacts/Godrithms

### spring damper

A damped spring used to smooth or animate values. **Use when:** Camera, UI and needles.

> smooth the needle with a critically damped spring

Tier: all · Pairs with: [spring animation](#spring-animation) · Source: industry

### perlin noise

Ken Perlin's gradient noise. **Use when:** Smooth natural variation.

> use math.noise (Perlin) remapped to 0..1 for terrain

Tier: T6 engines · Pairs with: [gradient noise](#gradient-noise) · Source: industry

### simplex noise

A faster gradient noise with fewer artefacts in higher dimensions. **Use when:** 3D and 4D noise.

> use simplex noise for animated 3D fields

Tier: T6 engines · Pairs with: [gradient noise](#gradient-noise) · Source: industry

### blue noise

Noise with even spacing and no low-frequency clumps. **Use when:** Dithering and sampling.

> sample with blue noise so the pattern has no clumps

Tier: T6 engines · Pairs with: [dithering](#dithering), [Poisson disk](#poisson-disk) · Source: industry

### flood fill

Filling a connected region from a seed. **Use when:** Region detection and paint.

> flood fill from the spawn to find reachable cells

Tier: T6 engines · Pairs with: [cellular automaton](#cellular-automaton) · Source: industry


## World

### landmark

A unique silhouette at a decision point that players navigate by. **Use when:** Map readability.

> place 1–3 landmarks per screen-width at junctions

Tier: T4 world · Pairs with: [lane](#lane), [set piece](#set-piece) · Source: aaa-kit/.claude/skills/procedural-world

### lane

A clear path the player moves along. **Use when:** Arena and level layout.

> keep lanes 3 tiles wide and clear of props

Tier: T4 world · Pairs with: [landmark](#landmark), [choke point](#choke-point) · Source: aaa-kit/.claude/skills/procedural-world

### choke point

A narrow passage that concentrates movement and fights. **Use when:** Level pacing.

> add one choke point between open fields for pacing

Tier: T4 world · Pairs with: [lane](#lane) · Source: industry

### safe pocket

A small protected area for recovery. **Use when:** Survival arenas.

> leave a safe pocket every 40 tiles with no spawns

Tier: T4 world · Pairs with: [lane](#lane) · Source: industry

### biome

A region with its own palette, props and rules. **Use when:** Big maps.

> assign each Voronoi region a biome with one palette ramp

Tier: T4 world · Pairs with: [Voronoi](#voronoi) · Source: industry

### scatter mask

A function that forbids scatter in some areas (lanes, water). **Use when:** Prop placement.

> mask Poisson scatter so nothing spawns on lanes or water

Tier: T4 world · Pairs with: [Poisson disk](#poisson-disk) · Source: aaa-kit/.claude/skills/procedural-world

### prop size class

Grouping props into large, medium and small and placing large first. **Use when:** Natural-looking scatter.

> place large props first, then medium at half spacing, then small

Tier: T4 world · Pairs with: [Poisson disk](#poisson-disk) · Source: industry

### set piece

A handcrafted or scripted moment placed in a generated world. **Use when:** Memorable beats.

> place a collapsing-bridge set piece where the route crosses the river

Tier: T4 world · Pairs with: [landmark](#landmark) · Source: vault/Notes/26 Map Set Pieces

### decal

A flat mark projected on a surface (scorch, footprint, crack). **Use when:** Showing history and direction.

> stamp low-contrast decals that never outshine pickups

Tier: T4 world · Pairs with: [battle history](#battle-history) · Source: industry

### battle history

Persistent marks of what happened (scorch, blood, footprints). **Use when:** Making the world remember.

> write scorch marks into 16×16 history blocks only where fights happened

Tier: T4 world · Pairs with: [decal](#decal) · Source: cursed-survivors/docs/budgets.md

### parallax

Background layers moving slower than the foreground for depth. **Use when:** 2D depth.

> three parallax layers at 0.2, 0.5 and 0.8 of camera speed

Tier: T4 world · Pairs with: [depth fog](#depth-fog) · Source: industry

### depth fog

Fading distant things toward a fog colour. **Use when:** Depth and readability.

> fog distant layers toward the sky colour by 40 %

Tier: T4 world · Pairs with: [parallax](#parallax) · Source: industry

### god rays

Visible light shafts through gaps. **Use when:** Forests and temples.

> march god rays back toward the sun through foliage gaps

Tier: T4 world · Pairs with: [volumetric light](#volumetric-light) · Source: Living Effects Lab

### volumetric light

Light scattering through air, fog or dust. **Use when:** Atmosphere.

> add faint volumetric light in the temple, ≤ 15 % brightness

Tier: T4 world · Pairs with: [god rays](#god-rays) · Source: industry

### aurora

Layered light curtains in a night sky. **Use when:** Night and winter maps.

> layer aurora curtains with slow ray streaks over the mountains

Tier: T4 world · Pairs with: [parallax](#parallax) · Source: Living Effects Lab

### fireflies

Wandering glows blinking on independent clocks. **Use when:** Night ambience.

> 30 fireflies on independent blink clocks, drawn additively

Tier: T4 world · Pairs with: [additive blending](#additive-blending) · Source: Living Effects Lab

### parallax snowfall

Snow in depth layers that piles into drifts. **Use when:** Winter maps.

> three layers of snow that pile into drifts along edges

Tier: T4 world · Pairs with: [parallax](#parallax) · Source: Living Effects Lab

### curl noise

Divergence-free noise for swirling particle motion. **Use when:** Smoke and ink.

> advect particles through curl noise for ink trails

Tier: T4 world · Pairs with: [flow field](#flow-field) · Source: Living Effects Lab

### day-night cycle

Lighting and palette changing over time. **Use when:** Open worlds.

> shift the grade over a 20-minute day-night cycle

Tier: T4 world · Pairs with: [colour grading](#colour-grading) · Source: industry

### colour grading

Adjusting the final image's colours for mood. **Use when:** Setting tone per area.

> grade the cave cooler and darker by one band

Tier: all · Pairs with: [tone mapping](#tone-mapping) · Source: industry

### heightfield

Terrain stored as a height per grid point. **Use when:** Terrain generation.

> build the island as an fBm heightfield with an edge falloff

Tier: T4 world · Pairs with: [fBm](#fbm) · Source: industry

### edge falloff

Lowering height toward the map edge to form islands. **Use when:** Island maps.

> multiply height by a radial falloff so the map becomes an island

Tier: T4 world · Pairs with: [heightfield](#heightfield) · Source: industry

### hydraulic erosion

Simulating water carving terrain. **Use when:** Realistic terrain.

> run 50k droplets of hydraulic erosion for natural valleys

Tier: T4 world · Pairs with: [heightfield](#heightfield) · Source: industry

### tileset

A set of tiles that fit together. **Use when:** Tile-based maps.

> build the dungeon from a 16-tile tileset with matching edges

Tier: T4 world · Pairs with: [wave function collapse](#wave-function-collapse) · Source: industry

### streaming

Loading world parts near the player only. **Use when:** Large Roblox worlds.

> enable StreamingEnabled and keep generated models atomic

Tier: T4 world · Pairs with: [LOD](#lod) · Source: industry

### LOD

Level of detail: simpler versions far away. **Use when:** Performance at distance.

> use three LODs: full under 50 studs, half to 150, quarter beyond

Tier: all · Pairs with: [crowd LOD](#crowd-lod), [mesh LOD](#mesh-lod) · Source: industry

### mesh LOD

Fewer triangles for distant meshes. **Use when:** EditableMesh terrain.

> halve the cells per chunk beyond 50 studs

Tier: T4 world · Pairs with: [LOD](#lod), [skirt](#skirt) · Source: aaa-kit/.claude/skills/editable-mesh

### skirt

A vertical strip under a mesh edge hiding LOD cracks. **Use when:** Chunked terrain.

> add a 2-stud skirt to every chunk edge to hide cracks

Tier: T4 world · Pairs with: [mesh LOD](#mesh-lod) · Source: industry

### chunk

A fixed-size piece of a large surface built and updated on its own. **Use when:** Big terrain and maps.

> split terrain into 32×32 chunks and rebuild only dirty ones

Tier: T4 world · Pairs with: [mesh LOD](#mesh-lod) · Source: industry


## Economy

### faucet

A source of currency (taps, passive income, rewards). **Use when:** Economy design.

> list every faucet and its rate per minute

Tier: economy · Pairs with: [sink](#sink) · Source: industry

### sink

A way currency leaves the economy (upgrades, consumables). **Use when:** Preventing inflation.

> give every faucet a matching sink

Tier: economy · Pairs with: [faucet](#faucet) · Source: industry

### geometric cost curve

Cost = base × growth^level. **Use when:** Upgrade prices.

> cost = 10 × 1.15^level

Tier: economy · Pairs with: [closed-form buy-max](#closed-form-buy-max) · Source: aaa-kit/.claude/skills/game-economy

### polynomial curve

Value = base × (level + 1)^power. **Use when:** XP to next level.

> XP needed = 100 × (level + 1)²

Tier: economy · Pairs with: [geometric cost curve](#geometric-cost-curve) · Source: industry

### soft cap

Linear growth up to a cap, then diminishing returns. **Use when:** Stats that shouldn't explode.

> soft-cap crit chance at 50 % with logarithmic growth beyond

Tier: economy · Pairs with: [diminishing returns](#diminishing-returns) · Source: aaa-kit/.claude/skills/game-economy

### diminishing returns

Each extra unit gives less than the last. **Use when:** Stacking bonuses.

> stack speed bonuses with diminishing returns

Tier: economy · Pairs with: [soft cap](#soft-cap) · Source: industry

### closed-form buy-max

Computing the most levels affordable with a formula, not a loop. **Use when:** Buy-max buttons.

> compute buy-max with the geometric series closed form, then check the boundary

Tier: economy · Pairs with: [geometric cost curve](#geometric-cost-curve) · Source: aaa-kit/examples/framework-starter

### buy-max

A button buying as many levels as affordable. **Use when:** Incremental shops.

> add ×1, ×10 and Max buttons using closed-form maths

Tier: economy · Pairs with: [closed-form buy-max](#closed-form-buy-max) · Source: industry

### prestige

Resetting progress for a permanent multiplier or currency. **Use when:** Long-term incremental loops.

> first prestige at 15–30 min, each run 2–5× faster

Tier: economy · Pairs with: [reset layer](#reset-layer), [prestige payout](#prestige-payout) · Source: industry

### reset layer

A data row describing what a reset wipes, keeps and pays. **Use when:** Implementing prestige.

> define rebirth as a reset layer row: wipes coins and upgrades, pays gems

Tier: economy · Pairs with: [prestige](#prestige) · Source: aaa-kit/examples/framework-starter

### prestige payout

Currency from a reset, usually k × total^0.5. **Use when:** Balancing prestige.

> pay floor(1 × coinsEarned^0.5) gems on rebirth

Tier: economy · Pairs with: [prestige](#prestige) · Source: aaa-kit/.claude/skills/game-economy

### payback time

Seconds of income to recoup an upgrade's cost. **Use when:** Judging upgrade value.

> rank upgrades by payback time = cost / income gained

Tier: economy · Pairs with: [pacing](#pacing) · Source: aaa-kit/.claude/skills/game-economy

### pacing

How the wait between meaningful purchases evolves. **Use when:** Avoiding walls and free rides.

> simulate a player and keep each wait within 2× of the last

Tier: economy · Pairs with: [pacing wall](#pacing-wall), [payback time](#payback-time) · Source: aaa-kit/.claude/skills/game-economy

### pacing wall

A sudden jump in wait time between purchases. **Use when:** Finding grind spikes.

> flag any wait that jumps more than 2× as a pacing wall

Tier: economy · Pairs with: [pacing](#pacing) · Source: aaa-kit/.claude/skills/game-economy

### offline earnings

Income granted for time away, capped and reduced. **Use when:** Idle games.

> grant offline earnings at 50 % rate, capped at 8 hours, shown as a reward

Tier: economy · Pairs with: [reward sequencing](#reward-sequencing) · Source: aaa-kit/.claude/skills/game-economy

### automation

A per-second effect run by one central system. **Use when:** Passive income, regen, timers.

> add passive income as an automation entry, not a new loop

Tier: economy · Pairs with: [central system](#central-system) · Source: aaa-kit/docs/FRAMEWORK.md

### unlock gate

Content hidden until a stat condition is met. **Use when:** Progression gating.

> gate the second zone behind an unlock row: coinsEarned ≥ 1e6

Tier: economy · Pairs with: [central system](#central-system) · Source: aaa-kit/docs/FRAMEWORK.md

### multiplier stack

How several multipliers combine (additive within a group, multiplicative across). **Use when:** Balancing bonuses.

> add bonuses within a group, multiply across groups

Tier: economy · Pairs with: [diminishing returns](#diminishing-returns) · Source: industry

### big number

A value past 1e308 stored as layered exponent. **Use when:** Late incremental games.

> store values past 9e15 as EternityNum strings

Tier: economy · Pairs with: [EternityNum](#eternitynum), [big-number suffix](#big-number-suffix) · Source: aaa-kit/examples/bignum

### EternityNum

A Luau big-number type {sign, layer, mag} with break_eternity maths. **Use when:** Numbers past double range.

> use EternityNum for currency once it can pass 9e15

Tier: economy · Pairs with: [big number](#big-number) · Source: aaa-kit/examples/bignum

### leaderboard encoding

Mapping big numbers to order-preserving integers for OrderedDataStore. **Use when:** Big-number leaderboards.

> encode scores with lbencode before writing to OrderedDataStore

Tier: economy · Pairs with: [EternityNum](#eternitynum) · Source: aaa-kit/examples/bignum

### balance in data

Keeping every tunable number in content tables, never in logic. **Use when:** Any balance work.

> move every price and rate into content rows; services hold none

Tier: economy · Pairs with: [content module](#content-module) · Source: aaa-kit/docs/FRAMEWORK.md

### gacha odds

Published drop rates per tier. **Use when:** Fair RNG.

> show exact odds per tier on the pull screen

Tier: economy · Pairs with: [pity timer](#pity-timer), [decide-then-animate](#decide-then-animate) · Source: industry

### idle game

A game where progress continues with little input. **Use when:** Genre framing.

> design the idle loop: tap early, automate mid, prestige late

Tier: economy · Pairs with: [automation](#automation), [offline earnings](#offline-earnings) · Source: industry

### incremental game

A game about numbers growing through upgrades and resets. **Use when:** Genre framing.

> structure the incremental loop around three reset layers

Tier: economy · Pairs with: [prestige](#prestige), [big number](#big-number) · Source: industry

### conversion rate

The exchange rate between two currencies. **Use when:** Multi-currency economies.

> convert coins to gems at 1000:1 with a daily cap

Tier: economy · Pairs with: [faucet](#faucet), [sink](#sink) · Source: industry


## Code & Framework

### Kit hub

The one shared module every script requires, with no game logic. **Use when:** Structuring a Roblox game.

> require Kit for Format, Guard, Maid and Signal; never put game logic in it

Tier: framework · Pairs with: [service](#service), [component](#component) · Source: aaa-kit/docs/FRAMEWORK.md

### service

A server-authoritative module with init, start and per-player lifecycle. **Use when:** Game rules and data.

> write it as a service with init, start, playerAdded and playerRemoving

Tier: framework · Pairs with: [Kit hub](#kit-hub), [registry](#registry) · Source: aaa-kit/docs/FRAMEWORK.md

### registry

The list that boots services in order: every init, then every start. **Use when:** Service wiring.

> register services in dependency order and boot once

Tier: framework · Pairs with: [service](#service) · Source: aaa-kit/examples/framework-starter

### component

Per-instance behaviour bound to a CollectionService tag with construct/start/stop. **Use when:** Things on screen.

> make it a tagged component with a Maid cleaned in stop

Tier: framework · Pairs with: [Maid](#maid), [CollectionService tag](#collectionservice-tag) · Source: aaa-kit/docs/FRAMEWORK.md

### content module

A module returning one frozen table of data rows. **Use when:** Upgrades, unlocks, loot.

> add the item as a row in the content module, numbers only

Tier: framework · Pairs with: [balance in data](#balance-in-data) · Source: aaa-kit/docs/FRAMEWORK.md

### central system

A pure module owning one cross-cutting job (save, automations, unlocks, resets, intensity). **Use when:** Avoiding ad-hoc loops and wipes.

> route it through the central system instead of a custom loop

Tier: framework · Pairs with: [automation](#automation), [unlock gate](#unlock-gate) · Source: aaa-kit/docs/FRAMEWORK.md

### where things go

A table mapping each kind of change to its one home. **Use when:** Deciding where code lives.

> check the where-things-go table before adding a file

Tier: framework · Pairs with: [Kit hub](#kit-hub) · Source: aaa-kit/docs/FRAMEWORK.md

### slip-ups as rules

Turning each past bug into a written rule with its reason. **Use when:** Team rules docs.

> add the bug to the rules table: what happened, the rule that prevents it

Tier: framework · Pairs with: [where things go](#where-things-go) · Source: aaa-kit/docs/FRAMEWORK.md

### Maid

An object collecting connections and instances to clean in one call. **Use when:** Component and service cleanup.

> give every connection to self._maid and clean it in stop

Tier: framework · Pairs with: [component](#component) · Source: aaa-kit/examples/framework-starter

### Signal

A typed event with connect, once and fire. **Use when:** Decoupled communication.

> expose changes as a Signal and connect through the Maid

Tier: framework · Pairs with: [Maid](#maid) · Source: aaa-kit/examples/framework-starter

### server authority

The server decides every outcome; clients only request. **Use when:** Anything involving value.

> the client requests, the server validates and decides

Tier: framework · Pairs with: [remote validation](#remote-validation) · Source: industry

### remote validation

Checking every remote argument on the server: shape, rate, state. **Use when:** All RemoteEvents and RemoteFunctions.

> validate shape (type, whitelist, finite, capped), then rate, then state

Tier: framework · Pairs with: [server authority](#server-authority), [rate limit](#rate-limit) · Source: aaa-kit/docs/FRAMEWORK.md

### whitelist key

Accepting only string keys that exist in a known table. **Use when:** Any string argument.

> accept the upgrade id only if Upgrades[id] exists

Tier: framework · Pairs with: [remote validation](#remote-validation) · Source: aaa-kit/examples/framework-starter

### NaN guard

Rejecting NaN and infinity in numeric input. **Use when:** Any number from a client.

> reject v ~= v and math.abs(v) == math.huge

Tier: framework · Pairs with: [remote validation](#remote-validation) · Source: aaa-kit/examples/framework-starter

### rate limit

Refusing requests that come faster than a set interval per player. **Use when:** Remotes and actions.

> rate-limit taps to 12.5 per second per player on the server

Tier: framework · Pairs with: [debounce](#debounce) · Source: aaa-kit/examples/framework-starter

### debounce

Ignoring repeat triggers within a short window. **Use when:** Touches, clicks, remotes.

> debounce the touch per player for 0.5 s on the server

Tier: framework · Pairs with: [rate limit](#rate-limit) · Source: industry

### session lock

Marking a save as owned by one server so two can't write it. **Use when:** DataStore saves.

> lock the save with the job id and refuse to write if another server holds it

Tier: framework · Pairs with: [save reconcile](#save-reconcile) · Source: aaa-kit/examples/framework-starter

### save reconcile

Filling missing fields from the template when loading an old save. **Use when:** Adding save fields.

> add the field to the template; reconcile fills old saves on load

Tier: framework · Pairs with: [session lock](#session-lock), [save template](#save-template) · Source: aaa-kit/examples/framework-starter

### save template

The default shape of a new save. **Use when:** Save design.

> add new fields only to the save template

Tier: framework · Pairs with: [save reconcile](#save-reconcile) · Source: aaa-kit/examples/framework-starter

### read-only session

After a failed load, never save, so a bad load can't wipe good data. **Use when:** DataStore errors.

> on load failure mark the session read-only and warn

Tier: framework · Pairs with: [session lock](#session-lock) · Source: aaa-kit/examples/framework-starter

### receipt dedupe

Recording PurchaseIds so a retried receipt isn't granted twice. **Use when:** Developer products.

> store PurchaseId in the save and return PurchaseGranted for duplicates

Tier: framework · Pairs with: [server authority](#server-authority) · Source: aaa-kit/.claude/skills/roblox-luau-standards

### string require

require("./X") paths that work in Roblox and in lune. **Use when:** Testable shared modules.

> use string requires so lune can run the module

Tier: framework · Pairs with: [lune test](#lune-test) · Source: aaa-kit/docs/STYLE.md

### lune test

A headless Luau test run with lune. **Use when:** Pure logic.

> add a lune test for every pure module before shipping

Tier: framework · Pairs with: [determinism](#determinism) · Source: aaa-kit/tools/lib/t.luau

### compile check

Compiling every Luau file to catch syntax errors without running. **Use when:** Before every commit.

> run lune run tools/check_luau.luau and require 0 failed

Tier: framework · Pairs with: [lune test](#lune-test) · Source: aaa-kit/tools/check_luau.luau

### golden frame

A stored reference render that tests compare against. **Use when:** Catching unintended visual changes.

> compare the render against the golden frame checksum

Tier: framework · Pairs with: [determinism](#determinism) · Source: cursed-survivors/docs/budgets.md

### CollectionService tag

A label on instances used to bind components. **Use when:** Attaching behaviour to instances.

> tag the label CoinCounter and let the component bind to it

Tier: framework · Pairs with: [component](#component) · Source: industry

### EditableImage

A Roblox image whose pixels code can write. **Use when:** Pixel renderers and procedural textures.

> draw the frame into an EditableImage and upload once per frame

Tier: T6 engines · Pairs with: [owner buffer](#owner-buffer), [WritePixelsBuffer](#writepixelsbuffer) · Source: aaa-kit/.claude/skills/editable-image

### WritePixelsBuffer

The EditableImage call that uploads an RGBA buffer. **Use when:** Pixel renderers.

> upload the whole frame with one WritePixelsBuffer call

Tier: T6 engines · Pairs with: [EditableImage](#editableimage) · Source: aaa-kit/.claude/skills/editable-image

### EditableMesh

A Roblox mesh whose vertices and triangles code can write. **Use when:** Procedural geometry.

> build terrain chunks as EditableMeshes from a pure builder

Tier: T6 engines · Pairs with: [mesh LOD](#mesh-lod) · Source: aaa-kit/.claude/skills/editable-mesh

### UIStroke

A Roblox outline on UI elements. **Use when:** Frames and text outlines.

> outline the slot with a UIStroke coloured by rarity

Tier: T3 hud · Pairs with: [rarity frame](#rarity-frame) · Source: industry

### UIGradient

A Roblox colour/transparency gradient on UI, rotatable and offsettable. **Use when:** Sweeps and spins on UI.

> tween the UIGradient Offset for a shine sweep every 2.5 s

Tier: T3 hud · Pairs with: [rarity frame](#rarity-frame) · Source: industry

### SurfaceAppearance

Roblox PBR maps on a MeshPart. **Use when:** 3D materials.

> apply a SurfaceAppearance with metalness and roughness maps

Tier: T5 materials · Pairs with: [PBR](#pbr) · Source: industry

### pixel snapping

Drawing only at whole-pixel coordinates. **Use when:** Hard-pixel art.

> snap every sprite to integer pixels; no sub-pixel drawing

Tier: T6 engines · Pairs with: [EditableImage](#editableimage) · Source: aaa-kit/.claude/skills/editable-image

### object pooling

Reusing objects instead of creating and destroying them. **Use when:** Particles, projectiles, UI rows.

> pool projectiles: 200 preallocated, recycled on hit

Tier: all · Pairs with: [particle budget](#particle-budget) · Source: industry


## Performance

### frame budget

The milliseconds available per frame (16.6 ms at 60 fps). **Use when:** Planning any per-frame work.

> keep this system under 0.8 ms of the 16.6 ms frame budget

Tier: all · Pairs with: [phone multiplier](#phone-multiplier) · Source: aaa-kit/CLAUDE.md

### phone multiplier

Assuming a phone runs roughly 4–5× slower than a desktop. **Use when:** Estimating mobile cost.

> budget for a 5× slower phone: 2 ms on desktop means 10 ms on a phone

Tier: all · Pairs with: [frame budget](#frame-budget) · Source: cursed-survivors/docs/budgets.md

### per-layer timing

Measuring each render layer's milliseconds separately. **Use when:** Finding the expensive layer.

> time each layer with os.clock and show a rolling average

Tier: all · Pairs with: [frame budget](#frame-budget) · Source: cursed-survivors/docs/budgets.md

### hot path

Code that runs every frame or per entity. **Use when:** Optimising and logging rules.

> keep the hot path allocation-free and print-free

Tier: framework · Pairs with: [no hot-path prints](#no-hot-path-prints) · Source: aaa-kit/docs/FRAMEWORK.md

### no hot-path prints

Never printing per hit, per frame or per sale. **Use when:** Logging.

> remove prints from the per-hit handler; warn once per real failure

Tier: framework · Pairs with: [hot path](#hot-path) · Source: aaa-kit/docs/FRAMEWORK.md

### allocation-free loop

A per-frame loop that creates no tables or closures. **Use when:** Avoiding GC hitches.

> hoist tables out of the render loop so it allocates nothing per frame

Tier: all · Pairs with: [hot path](#hot-path), [object pooling](#object-pooling) · Source: industry

### native codegen

Luau's --!native compilation for faster inner loops. **Use when:** Heavy maths in Studio.

> mark the inner pixel loop --!native and measure interpreted too

Tier: framework · Pairs with: [interpreter budget](#interpreter-budget) · Source: industry

### interpreter budget

Planning for live clients that may run Luau without native codegen. **Use when:** Client performance.

> measure the renderer interpreted, since live clients may not use native

Tier: framework · Pairs with: [native codegen](#native-codegen) · Source: cursed-survivors/docs/decisions.md

### baking

Precomputing expensive results once (textures, shaded sprites). **Use when:** Static content.

> bake the shaded sprites per palette band at load

Tier: all · Pairs with: [cache](#cache) · Source: cursed-survivors/docs/decisions.md

### cache

Storing a computed result to reuse. **Use when:** Repeated expensive work.

> cache the noise field; recompute only the animated tail

Tier: all · Pairs with: [baking](#baking) · Source: industry

### dirty flag

Marking something as changed so it's rebuilt only then. **Use when:** Avoiding per-frame rebuilds.

> rebuild the chunk only when its dirty flag is set

Tier: all · Pairs with: [cache](#cache) · Source: industry

### frame-sliced work

Splitting heavy work across several frames. **Use when:** Generation and baking.

> generate 100 props per frame with task.wait() between batches

Tier: all · Pairs with: [dirty flag](#dirty-flag) · Source: industry

### half-rate update

Running a system every other frame or at a lower rate. **Use when:** Expensive ambient systems.

> update the light map at 30 Hz and the world pass every other frame on phones

Tier: all · Pairs with: [intensity budget](#intensity-budget) · Source: cursed-survivors/docs/budgets.md

### culling

Skipping work for things off screen or hidden. **Use when:** Many objects.

> cull particles outside the viewport before updating them

Tier: all · Pairs with: [LOD](#lod) · Source: industry

### draw call

One batch of rendering submitted to the GPU. **Use when:** 3D and web performance.

> batch the props to cut draw calls

Tier: all · Pairs with: [batching](#batching) · Source: industry

### batching

Combining many draws into one. **Use when:** Many similar objects.

> batch all coins into one instanced draw

Tier: all · Pairs with: [draw call](#draw-call) · Source: industry

### p95 frame time

The frame time 95 % of frames beat; shows hitches averages hide. **Use when:** Performance reporting.

> report average and p95 frame time for the endgame scene

Tier: all · Pairs with: [frame budget](#frame-budget) · Source: cursed-survivors/docs/budgets.md


## Art Direction

### silhouette

An object's outline shape, readable without detail. **Use when:** Character, enemy and icon design.

> make each enemy family readable from its silhouette alone at 16 px

Tier: all · Pairs with: [silhouette read](#silhouette-read), [figure-ground gate](#figure-ground-gate) · Source: industry

### silhouette read

Testing identification with a solid black fill. **Use when:** Reviewing designs.

> fill every sprite black and check each family is still identifiable

Tier: all · Pairs with: [silhouette](#silhouette) · Source: industry

### value structure

The arrangement of lights and darks in a frame. **Use when:** Composition and readability.

> design value structure in greyscale before colour

Tier: all · Pairs with: [luminance band](#luminance-band) · Source: industry

### greyscale check

Viewing a frame without colour to judge value. **Use when:** Readability reviews.

> review the capture in greyscale; threats must still pop

Tier: all · Pairs with: [value structure](#value-structure) · Source: industry

### focal point

Where the eye goes first. **Use when:** Composition.

> make the reward the focal point: brightest, largest, centred

Tier: all · Pairs with: [saliency map](#saliency-map) · Source: industry

### visual noise

Detail that competes for attention without carrying meaning. **Use when:** Busy screens.

> cut visual noise: remove decor that doesn't help a decision

Tier: all · Pairs with: [detail density](#detail-density) · Source: industry

### lantern light

The hero's own warm light, the only warm source in a cool world. **Use when:** Exploration-driven lighting.

> the hero carries the only warm lantern light; the world stays cool

Tier: T2 combat · Pairs with: [colour job](#colour-job) · Source: vault/Notes/16 Hierarchy Codex

### banded lighting

Lighting quantised to a few luminance bands. **Use when:** Cel and pixel looks.

> quantise lighting to 8 bands with dithered transitions

Tier: all · Pairs with: [luminance band](#luminance-band), [toon ramp](#toon-ramp) · Source: cursed-survivors/docs/decisions.md

### palette ramp

An ordered set of shades for one hue family. **Use when:** Consistent shading.

> give each material a 5-step palette ramp from shadow to highlight

Tier: all · Pairs with: [palette quantisation](#palette-quantisation) · Source: industry

### hue shift

Shifting hue as value changes (cooler shadows, warmer lights). **Use when:** Richer shading.

> shift shadows toward blue and highlights toward yellow

Tier: all · Pairs with: [palette ramp](#palette-ramp) · Source: industry

### saturation hierarchy

Reserving high saturation for what matters. **Use when:** Directing attention with colour.

> keep the world desaturated so threats and pickups own saturation

Tier: all · Pairs with: [colour job](#colour-job) · Source: industry

### phone-first framing

Designing for a phone screen before desktop. **Use when:** Any Roblox UI or camera.

> design at 390×844 first, then scale up

Tier: all · Pairs with: [safe area](#safe-area), [thumb zone](#thumb-zone) · Source: aaa-kit/CLAUDE.md

### outline weight

The thickness of an outline relative to the sprite. **Use when:** Consistent sprite style.

> use 1 px outlines on 16 px sprites and 2 px on 32 px

Tier: all · Pairs with: [thin ring](#thin-ring) · Source: industry

### light direction

One consistent key-light direction across all art. **Use when:** Visual consistency.

> light every sprite from the top-left

Tier: all · Pairs with: [rim light](#rim-light) · Source: industry

### art bible

The written rules of a game's look. **Use when:** Keeping a team consistent.

> write the art bible: palette, light direction, outline rule, colour jobs

Tier: all · Pairs with: [colour job](#colour-job), [palette ramp](#palette-ramp) · Source: industry

### mood board

A collection of references that defines a target look. **Use when:** Starting a new look.

> assemble a mood board of 12 references before drawing

Tier: all · Pairs with: [art bible](#art-bible) · Source: industry

### contrast ratio

The ratio between two luminances; for text ≥ 4.5:1. **Use when:** Text and UI legibility.

> keep UI text at least 4.5:1 against its plate

Tier: all · Pairs with: [figure-ground gate](#figure-ground-gate) · Source: industry


## Audio & Feel

### audio cue

A sound tied to a visual event. **Use when:** Feedback.

> pair the reveal with a rising tone and a hit on the onset frame

Tier: all · Pairs with: [sting](#sting), [layered impact sound](#layered-impact-sound) · Source: vault/Notes/15 Attention System

### sting

A short musical phrase marking a moment. **Use when:** Rewards and level-ups.

> play a tier-specific sting on the reveal

Tier: T1 moments · Pairs with: [audio cue](#audio-cue) · Source: industry

### layered impact sound

An impact built from transient, body and tail layers. **Use when:** Weighty hits.

> layer a sharp transient, a mid body and a short tail for each hit

Tier: T2 combat · Pairs with: [audio cue](#audio-cue) · Source: industry

### pitch variation

Randomising pitch slightly to avoid repetition. **Use when:** Repeated sounds.

> vary pitch ±6 % on every coin pickup

Tier: all · Pairs with: [audio cue](#audio-cue) · Source: industry

### rising pitch chain

Each consecutive pickup plays a slightly higher note. **Use when:** Combos and coin streams.

> raise pickup pitch one semitone per pickup in a streak, reset after 1 s

Tier: T3 hud · Pairs with: [combo meter](#combo-meter) · Source: industry

### ducking

Lowering music under important sounds. **Use when:** Mixing.

> duck music 6 dB under the reveal sting

Tier: all · Pairs with: [audio cue](#audio-cue) · Source: industry

### music intensity

Music level and filter following the intensity rung. **Use when:** Adaptive music.

> open the music's high shelf as the intensity rung climbs

Tier: all · Pairs with: [intensity ladder](#intensity-ladder) · Source: cursed-survivors/src/shared/Intensity.luau

### haptics

Controller or phone vibration on events. **Use when:** Mobile and console feel.

> pulse a 20 ms haptic on hits and a 60 ms one on kills

Tier: all · Pairs with: [hit-stop](#hit-stop) · Source: industry


## Game Feel

### game feel

How responsive and physical control feels. **Use when:** Polishing play.

> tune game feel: input to motion within one frame, clear impacts

Tier: all · Pairs with: [juice](#juice), [hit-stop](#hit-stop) · Source: industry

### input buffer

Remembering an input briefly so it fires when possible. **Use when:** Action timing.

> buffer jump inputs for 100 ms

Tier: all · Pairs with: [coyote time](#coyote-time) · Source: industry

### coyote time

Allowing a jump shortly after leaving a ledge. **Use when:** Platformers.

> allow jumps up to 80 ms after leaving the ledge

Tier: all · Pairs with: [input buffer](#input-buffer) · Source: industry

### squash and stretch

Deforming shapes to show speed and impact. **Use when:** Characters and pickups.

> squash the coin 20 % on landing and stretch it toward the magnet

Tier: all · Pairs with: [overshoot](#overshoot) · Source: industry

### follow-through

Parts continuing to move after the main motion stops. **Use when:** Natural animation.

> let the cape follow through for 150 ms after the stop

Tier: all · Pairs with: [overlap](#overlap) · Source: industry

### overlap

Different parts moving slightly out of sync. **Use when:** Organic motion.

> offset hair and cape motion by 2 frames

Tier: all · Pairs with: [follow-through](#follow-through) · Source: industry

### anticipation pose

A small opposite motion before an action. **Use when:** Attacks and jumps.

> crouch 3 frames before the jump

Tier: all · Pairs with: [anticipation](#anticipation) · Source: industry

### camera lag

The camera trailing its target slightly. **Use when:** Smooth cameras.

> lag the camera 0.1 s behind the player

Tier: all · Pairs with: [camera lead](#camera-lead) · Source: industry

### camera lead

The camera looking ahead in the movement direction. **Use when:** Fast movement.

> lead the camera 20 % of screen width in the move direction

Tier: all · Pairs with: [camera lag](#camera-lag) · Source: industry

### aim assist

Gently helping aim toward valid targets. **Use when:** Mobile shooters.

> snap aim within 12° to the nearest target on touch

Tier: all · Pairs with: [game feel](#game-feel) · Source: cursed-survivors/tests/aim.luau

### readability under spectacle

Keeping gameplay information clear while effects are maxed. **Use when:** Late-game screens.

> at max spectacle every threat must still pass the gate

Tier: all · Pairs with: [protected region](#protected-region), [intensity ladder](#intensity-ladder) · Source: vault/Research/Render Deep Dive/09

### reduced motion

A setting or OS preference to tone down motion. **Use when:** Accessibility.

> honour reduced motion: shake at 25 %, no flashes

Tier: all · Pairs with: [screen shake](#screen-shake) · Source: industry


## Process

### brief

A structured request: goal, tier, deliverable, constraints, quality bar, done-check. **Use when:** Starting any task.

> write a brief before building: goal, tier, deliverable, constraints, bar, done

Tier: process · Pairs with: [prompt amplifier](#prompt-amplifier), [done-check](#done-check) · Source: aaa-kit/.claude/skills/prompt-amplifier

### prompt amplifier

Turning a vague request into a brief with options. **Use when:** Weak prompts.

> amplify the prompt into a brief, then proceed on Solid

Tier: process · Pairs with: [brief](#brief) · Source: aaa-kit/.claude/skills/prompt-amplifier

### solid bold insane

Three escalation levels: ship-ready, signature, memorable. **Use when:** Offering options.

> offer solid, bold and insane versions and start on solid

Tier: process · Pairs with: [prompt amplifier](#prompt-amplifier) · Source: aaa-kit/.claude/skills/prompt-amplifier

### done-check

An observable condition that proves the work is done. **Use when:** Ending any task.

> done when the capture at 390×844 shows the price readable and the test passes

Tier: process · Pairs with: [brief](#brief) · Source: aaa-kit/.claude/skills/prompt-amplifier

### self-check

The checklist a skill runs before saying done. **Use when:** Finishing skill work.

> run the skill's self-check and list any item that fails

Tier: process · Pairs with: [done-check](#done-check) · Source: aaa-kit/.claude/skills

### before/after capture

Screenshots of the same state before and after a change. **Use when:** Visual changes.

> capture before and after at the same seed and size

Tier: process · Pairs with: [done-check](#done-check) · Source: cursed-survivors/docs/look

### parity checklist

A list of features to match against a reference. **Use when:** Ports and remakes.

> track feature parity in a checklist: done, partial, missing

Tier: process · Pairs with: [done-check](#done-check) · Source: cursed-survivors/docs/PARITY_CHECKLIST.md

### handoff note

A written state of work for the next session. **Use when:** Ending a session.

> write a handoff: what's done, what's verified, what's next

Tier: process · Pairs with: [brief](#brief) · Source: cursed-survivors/docs/HANDOFF.md

### skeleton first

Build every system end to end with placeholders, then raise quality module by module. **Use when:** Starting a big game.

> build the full skeleton playable first, then polish one module at a time

Tier: process · Pairs with: [parity checklist](#parity-checklist) · Source: cursed-survivors/docs/decisions.md

### vertical slice

One small part of the game at final quality. **Use when:** Proving the look and feel.

> build a vertical slice: one stage, one weapon, one reward at ship quality

Tier: process · Pairs with: [skeleton first](#skeleton-first) · Source: industry

### playtest

Watching real players use the build. **Use when:** Validating feel and difficulty.

> playtest with 3 players and note where they hesitate

Tier: process · Pairs with: [done-check](#done-check) · Source: industry

### code review

Reading a change for bugs before merging. **Use when:** Every change.

> review the diff for correctness before merging

Tier: process · Pairs with: [done-check](#done-check) · Source: industry

### draft PR

A pull request opened for review before it's ready to merge. **Use when:** Sharing work in progress.

> open a draft PR on a feature branch

Tier: process · Pairs with: [code review](#code-review) · Source: industry
