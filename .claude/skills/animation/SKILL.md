---
name: animation
description: Use when animating a character, object or camera and when two shots must join smoothly - keyframe clips kept as data, easing and timing, anticipation, squash and overshoot, follow-through and settle, secondary motion, motion driven by charge or power, camera hand-offs with no cut or jerk, spring followers, field of view kicks, and proving smoothness with a test or an offline Blender animatic. Triggers on "animate", "animation clip", "keyframes", "easing", "anticipation", "follow-through", "camera transition", "smooth transition", "camera hand-off", "feels stiff", "feels jerky", "animatic", "storyboard".
---

# animation

Motion is a loudness lever (HIERARCHY.md §1): whatever moves most owns the eye. So an animation is designed as a hierarchy first (who moves, who waits, who hands over) and as curves second. Curves live in data, are sampled by pure functions, and are proven smooth by a number before anyone watches them.

## When to use

- A character or object action: throw, swing, jump, open, hatch, hit, idle
- A camera move, or the join between two camera shots
- Motion that scales with an input: charge, power, rarity, size
- Anything described as stiff, floaty, jerky, snappy or "it pops"

**Not for:** particles and screen effects (`vfx`), the order of a reward's beats (`reward-moments`), UI tweens on buttons (`ui-hud`), building the model or rig (`lihfolk-stud-voxel`).

## Method

1. **Write the motion hierarchy before any curve.** For each beat, name one **lead** (the thing the player must watch), its **support** (secondary motion that lags the lead: a tail, a bow, a back foot) and what stays **still**. Two leads in one beat is a bug. The camera is a mover too: when it moves, the subject holds; when the subject acts, the camera holds or follows.
2. **Find the keys from a reference, then throw the reference away.** Step a clip at 12 fps, note the poses and their times (contact, extreme, release, settle). Keep the timings and the order of body parts. The poses you build are your own.
3. **Six beats for any action:** ready → anticipation (move the opposite way first) → action → contact or release → follow-through (overshoot past the pose) → settle. Anticipation and settle are where the weight is; never cut them to save time, shorten the action instead.
4. **Sequence the body, don't move it at once.** Big parts lead, small parts lag: hips, then torso, then arm, then hand. Give each a key 2–4 frames after its parent.
5. **Ease by intent.** Into a hit or release: accelerate ("In"). Out of it: decelerate ("Out"). Everything else: smooth both ends. Blends that start or stop a camera use the smoother curve (no acceleration at the ends).
6. **Clips are data; samplers are pure.** Keys go in a content table (time, one number per channel, ease). One function turns time into a pose using plain numbers: no instances, no clock. The game, the tests and the render all call it (`examples/Clip.luau`).
7. **Drive it with the input.** While the player charges, the pose follows the meter (a coil that tightens). On release, scale reach and twist channels by a 0–1 drive from the real power. A weak and a strong action must read differently in a still frame.
8. **Leave from where you are.** A clip never starts from its first key; it blends from the pose being held over ~0.1 s. Test that frame 0 equals the held pose exactly.
9. **Join shots without a corner.** At a hand-off, carry the camera's **speed** across, not just its position. Use a critically damped spring that starts loose and tightens, match a share of the target's speed so the camera trails by a steady distance, slide the look target with the smoother curve, and add a short field of view kick for the launch (`examples/Spring.luau`). A lerp-to-target restarts from zero speed every hand-off; that is the jerk.
10. **Information may ride on motion, decided by the server.** Size, colour and count can tell the player something true before the reveal (a bigger box for a bigger prize) because the result already exists. Give each channel one meaning: size says size, colour says rarity. Never animate a tell the result doesn't back.
11. **Prove it with numbers.** Assert: keys are hit exactly; the largest per-millisecond step of every channel is small ("nothing snaps"); the same path at 30 and 60 fps; the peak acceleration at a hand-off, new against old.
12. **Then watch it offline.** Dump frames from the real sampler and render them: a quick box rasteriser for poses, or a Blender animatic for camera work (`examples/animatic.py`, Cycles on the CPU, about 3 s a frame at 640×360). Step the storyboard, fix the pose that reads wrong, and only then spend a Studio session on it.
13. Run the self-check.

## Hierarchy rules it obeys

- §1: motion is a loudness channel; the lead of each beat is the only fast mover.
- §2: an action's loudness tier sets its amplitude. Tier 1 (reward) may overshoot and shake; tier 4–6 motion stays slow (cycles ≥ 2 s).
- §6: back to rest within 200 ms of resolving; nothing loops at rest except selection and slow ambient motion.
- §7: rarer results get more motion (count, amplitude, duration), never a different rule set. Commons stay short.
- §9: wind-ups are honest telegraphs: ≥ 600 ms for a familiar action, ≥ 1 s for a new one, and critical cues never wait for an animation to finish.
- §13: one lead per beat is "one loud element per panel" in time.
- §14: beats start when the last one settles; a skip jumps to the final pose with everything restored.

## Engine notes

**Roblox.** Sample on `RunService.PreSimulation` for joints (`Motor6D.Transform` blended from the pose at entry) and `RenderStepped` for the camera. Disable the `Animate` script and stop playing tracks while a procedural clip owns the body, and restore both on exit. Hands and feet reach targets with `IKControl`; check that a planted foot is within leg length or the leg will stretch. Scale a model with `ScaleTo` and keep it on the floor by scaling its height offset too; don't resize parts of a model you are also scaling. Use the camera's own `FieldOfView` for a kick and put it back on every exit path. Springs take `dt` from the frame and cap it, so a hitch doesn't fling the camera.

**Offline.** `pip install bpy` gives Blender as a Python module. In a container only Cycles on the CPU works; EEVEE and Workbench need a display and crash. Convert Roblox axes with (x, y, z) → (x, −z, y). Render every second simulated frame, join with `ffmpeg`, and keep a before/after pair when you change a hand-off.

**Web.** The same sampler in JS; `requestAnimationFrame` gives `dt` for the spring.

## Example

`examples/Clip.luau` samples a keyed clip with per-key easing, scales channels by a drive, blends in from a held pose, and measures the largest step. `examples/Spring.luau` is the exact critically damped follower with speed carry and target lead, a tightening stiffness, a kick curve, and a peak-acceleration measure. Both are tested in `examples/Motion.test.luau`, including a hand-off that must be at least 5× gentler than a lerp. `examples/animatic.py` renders a frames file in headless Blender.

```lua
local Clip = require("./examples/Clip")
local Spring = require("./examples/Spring")

-- every frame of the action
local pose = Clip.from(HeldPose, Clip.sample(ThrowClip, Time, Pose, { [TWIST] = 1 + 0.44 * Drive }), Time, 0.1)

-- every frame of the chase, per axis; CamSpeed starts as the speed the last shot ended on
local stiffness = Spring.tighten(Age, 3.2, 6, 0.6)
CamX, CamSpeedX = Spring.step(CamX, CamSpeedX, WantX, WantSpeedX, stiffness, dt, 0.5)
Camera.FieldOfView = BaseFov + 9 * Spring.kick(Age, 0.14, 0.75)
```

## Make it insane

1. **Hold frame:** on a perfect input, freeze the lead for 3 frames at the extreme pose while the camera keeps drifting, then release at double speed.
2. **Smear:** for the 2 fastest frames, stretch the lead part along its velocity and squash it across; restore on the contact frame.
3. **Camera as a character:** give the camera its own anticipation (a 2° counter-tilt before a launch) and settle (a damped 1-cycle wobble on landing), always quieter than the lead.

## Self-check

- [ ] Every beat names one lead, its support and what stays still; the camera and the subject never both act.
- [ ] Anticipation, action, contact, follow-through and settle are all present; the action is the shortest.
- [ ] Parts move in sequence (parent first), not all on the same key.
- [ ] Keys are in a content table and the sampler uses only numbers.
- [ ] The clip starts from the held pose and scales with the real input.
- [ ] Tests pass: keys hit exactly, nothing snaps, same path at 30 and 60 fps, hand-off acceleration measured against the old one.
- [ ] Each tell (size, colour, count) has one meaning and matches a result that already exists.
- [ ] Watched offline as a storyboard or animatic before the Studio session; what was not tested in the engine is said plainly.
- [ ] Skip restores the body, the camera and the field of view.
