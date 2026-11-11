# Time, motion and cue timing

Part V, Hierarchy science. Hierarchy over time: how long a cue must last, how far apart cues must be, and how fast a player can answer one. Builds on [chapter 80](80-attention-and-salience.md) (onsets, IOR, attentional blink) and the [UI motion playbook](../playbooks/ui-motion-and-sound.md).

## Takeaway

A player needs about **200 ms to move their eyes** to a cue, about **250 ms to react to an expected one**, and **500 ms or more to choose between options**. Then add input and network delay. Every telegraph, reward beat and warning is sized from that chain. Motion is the strongest cue in the periphery, so it is budgeted like brightness.

## 1. The human response chain

**Findings**
- **Saccade latency** (target onset to eye movement) is "typically around 200 ms". One example spans about 146–270 ms, and visual step targets average about 250–260 ms. "Express" saccades form a separate earlier peak near 100 ms. ([Radboud perception and action notes, ch. 17](https://perception-and-action-37169a.pages.science.ru.nl/content/17_reaction_times.html))
- **Simple visual reaction time** (one known signal, one response) is about **250–310 ms** in adults across the studies we surveyed, with trained athletes near 250 ms. **Choice reaction time** is roughly **500–550 ms** in large adult samples and rises slowly with age. We gathered both ranges from search summaries of sports-science and ageing studies, not from the papers' own text: **[UNVERIFIED] against the primary papers**, but consistent with the standard textbook picture that choice RT is well above simple RT.
- **Hick–Hyman law:** choice time grows with the information in the choice, T = a + b·log2(n + 1) for n equally likely options. Some sources drop the +1. ([Hick's law](https://en.wikipedia.org/wiki/Hick%27s_law)) Going from 2 to 8 options doubles the bits: log2 3 ≈ 1.58 versus log2 9 ≈ 3.17.

**The telegraph budget (derived; the numbers are house defaults)**

```
telegraph ≥ notice + decide + act + latency
notice  ≈ 200 ms   (saccade; 0 if the cue is already where the player looks)
decide  ≈ 250 ms   (one known answer: "dodge")   …   500+ ms (pick between options)
act     ≈ 100–200 ms (move the character out of the zone; depends on speed and zone size)
latency ≈ 50–150 ms (input + Roblox network round trip for server-timed hits)
```

| Attack type | Minimum wind-up | Why |
|---|---|---|
| Familiar, one answer, on screen centre | 600 ms | 0 + 250 + 200 + 150 |
| Familiar, peripheral | 800 ms | + 200 saccade |
| New or with a choice (which way to dodge) | 1000–1200 ms | choice RT ≈ 500 |
| Boss super, first sight | 1500 ms+ | learning; shorten after the player has seen it |

Faster wind-ups are a difficulty dial, not a readability fix. Keep the **shape and timing of each telegraph family** consistent so it becomes the "familiar" row ([telegraph design](https://gamedeveloper.com/design/enemy-attacks-and-telegraphing); [readability in ARPGs](https://www.gamedeveloper.com/game-platforms/designing-for-difficulty-readability-in-arpgs)).

## 2. Spacing cues in time

| Rule | Number | Source |
|---|---|---|
| Two separate messages | ≥ 500 ms apart, or merged within ≤ 100 ms | Attentional blink 200–500 ms; lag-1 sparing ([ch. 80 §4](80-attention-and-salience.md#4-after-capture-inhibition-of-return-and-the-attentional-blink)) |
| Repeat of a cue at the same place | change place, size or modality | Inhibition of return from ~300 ms |
| State change during a transition | wait until the transition ends | Change blindness ([ch. 80 §6](80-attention-and-salience.md#6-blindness-to-the-unattended)) |
| Large flashes | ≤ 3 per second over 2.78% of the screen | WCAG 2.3.1 ([ch. 81 §4](81-contrast-colour-and-colour-blindness.md#4-flashing-the-hard-safety-limit)) |
| How long a reading-required message stays | ≥ 1 s + 250 ms per word (house) | Reading-time numbers come from text research; for games this is UNKNOWN — tune in playtests |

## 3. Motion as a loudness channel

**Findings**
- Motion is one of the pre-attentive attributes on every list. Moving and looming items capture attention, and peripheral sensitivity to temporal change is about as good as foveal ([ch. 80 §3, §5](80-attention-and-salience.md#3-what-captures-attention-involuntarily-onsets-and-looming)).

**Rules for us**
1. **Budget motion per tier the way HIERARCHY §2 budgets brightness:**

| Tier | Allowed motion at rest | On event |
|---|---|---|
| 1 Moments | none until triggered | full screen, camera, looming |
| 2 Combat | idle loops ≤ 1 Hz | hit-stop, shake, approach |
| 3 HUD | **still** | one punch (scale 1.0 → 1.12 → 1.0 in ≤ 250 ms), count-up |
| 4 World | slow ambient (≥ 2 s cycles) | none |
| 5 Materials | slow sheen (≥ 3 s cycles) | none |
| 6 Engines | continuous but low contrast | none |

2. **Only one thing moves fast at a time.** A second fast motion splits attention, the same as a second loud element (HIERARCHY §13).
3. **Ambient motion stays slow, especially at the edges,** because the periphery is most sensitive there. Ambient cycles faster than about 1 Hz near the edges read as alerts. (That number is a house value.)
4. **Easing tells the player what kind of event it is.** Ease-out (fast start) is arrival and urgency. Ease-in (slow start) is departure and "done". Spring overshoot is reward. Linear is mechanical: progress bars, timers.
5. **Respect `ReducedMotionEnabled`.** Swap motion for value or colour changes. Keep the information, drop the movement.

## 4. Frame-level timing

- **Hit-stop** (freezing both actors for a few frames) makes an impact land by giving the eye a still frame to read. The house range is 2–6 frames at 60 fps, scaled by hit weight. See the [vfx skill](../../.claude/skills/vfx/SKILL.md).
- **Onset frames carry the message.** A tier-2 effect is brightest on frame 1 and back to baseline within about 12 frames (HIERARCHY §2). That gives one strong onset (which captures attention) and a quick return (which frees attention for the next cue).
- **Count-ups:** a number that counts for longer than about 1 s hides its final value. Count over 0.3–0.8 s, then punch the final value. These are house values; they match the odometer example in [ui-hud](../../.claude/skills/ui-hud/SKILL.md).

## 5. Gaps

- The reaction-time studies are of adults. Our audience skews young, and child RTs are longer (**UNKNOWN by how much for our ages — check before tuning wind-ups for kids**).
- Network latency on Roblox varies by region and server. Measure it with the perf overlay ([studio playbook](../playbooks/studio-workflow.md)) instead of trusting 150 ms.
- The easing semantics in §3 are a widely used animation convention, not a measured perception result.
