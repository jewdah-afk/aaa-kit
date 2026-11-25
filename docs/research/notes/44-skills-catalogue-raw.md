# G. Third-party skills catalogue: what is new for the kit

Scope: 28 skills downloaded from a public skills catalogue (folder `scratchpad/skdl/`). All files were read as text; no script was run. Compared against our kit: skills `vfx`, `editable-image`, `editable-mesh`, `shaders-and-sdf`, `reward-moments`, `ui-hud`, `algorithms`, `materials`; research ch. 23, 40, 41, 45, 63, 82, 83; playbooks `vfx-craft`, `ui-motion-and-sound`.

Short version: about a third are junk or duplicates. Six are genuinely strong: **game-sfx** (a procedural SFX synthesis and measurement pipeline, which our kit does not have at all), **game-feel-polish** (a full set of tuned juice numbers), **lihfolk-vfx** (a shipped Roblox combat-VFX kit with budgets and a replication pattern), the **PixelWao trio** (orchestration, QA trace auditor, impact animation), **roblox-animation / roblox-animation-vfx** (AnimationTrack and tween gotchas) and **juice-scan** (Roblox haptics, an automated juice audit).

---

## 1. All 28 at a glance

Quality: 1 = junk, 5 = senior-grade. Licence is the repository licence from `LICENCJA-REPOZYTORIUM.txt`.

| # | Skill (folder) | Source repo | Licence | Q | Verdict |
|---|---|---|---|---|---|
| 1 | 4k-vfx | Pika-Labs/Pika-Plugins | Apache-2.0 | 2 | **Junk** for us. It re-renders real video through a paid AI video model. Only the frame-indexed contact-sheet ffmpeg trick is reusable (see QA). |
| 2 | audio-sound-effects | voyager67/Agentic-Skill-Garage | Apache-2.0 | 1 | **Junk.** A generic post-production checklist with no numbers. |
| 3 | better-sfx | devhims/better-sfx | MIT code; sounds under a separate "Better SFX License" | 3 | **Useful as a source.** A free UI-SFX catalogue with exact durations and matched "sets" (glass/wood/soft/retro/mechanical). The sound licence bans standalone redistribution. |
| 4 | design-procedural-gen | fcsouza/agent-skills | **GPL-3.0** | 2 | **Duplicate** of `algorithms` / `procedural-world`. Don't copy: GPL. |
| 5 | editable-image | jewdah-afk/aaa-kit (ours) | MIT | – | **Ours.** It's byte-identical to our skill, which means the kit is already public in the catalogue. |
| 6 | editable-mesh | jewdah-afk/aaa-kit (ours) | MIT | – | **Ours**, identical. |
| 7 | game-2d-art-animation-and-vfx-pipeline | peterbamuhigire/chwezi-dev-engine | MIT | 1 | **Junk.** Generic asset-provenance checklist. |
| 8 | game-feel-and-juice (6b3f01) | Srijan69/ue-indie-superpowers | MIT | 2 | **Duplicate.** Unreal-flavoured summary of what ch. 45 already says. |
| 9 | game-feel-and-juice (cea3b9) | rondorkerin/gamestack | MIT | 4 | **Useful.** Kao 2020 inverted-U (N=3,018), a per-event feedback ceiling, latency thresholds by genre, and "eyes-closed / mute-all / sound-only" tests. |
| 10 | game-feel-debugging-qa | PixelWao/codex-gamedev-skills | MIT (upstream Apache-2.0 attribution kept) | 4 | **Useful.** JSONL feel-trace schema plus a deterministic auditor with 12 named violation codes. |
| 11 | game-feel-event-orchestration | PixelWao/codex-gamedev-skills | MIT (+Apache-2.0 upstream) | 4 | **Useful.** HitStopManager / FeedbackDirector, with overlapping-stop policy, dedupe and 100 ms budgets. |
| 12 | game-feel-polish | furkantokkan/agent-foundry (adapts Miisan's Liquid UI Kit, MIT) | MIT | 5 | **Useful, best numbers.** An `impact(strength)` composite, damage numbers, counter roll, lag bar, toasts, refusal shake, sound banks. |
| 13 | game-sfx | GhazaGG/Game-Sound-Effect-for-Claude | MIT | 5 | **Useful, biggest gap filled.** JSON-patch synth (PolyBLEP, SVF, FM, partials), loudness doctor with spectrogram, CC0 sample slicer, foley pattern and recipes. |
| 14 | game-sounds | akillness/jeo-skills | MIT | 1 | **Junk.** It plays sounds on Claude Code hooks, not game audio. |
| 15 | game-vfx (463c8c) | Ddrubok/bettermakegame | MIT | 3 | **Partly useful.** An evidence ladder (what each kind of proof can and can't show) and pending vs confirmed event semantics. |
| 16 | game-vfx (bfdf23) | akillness/jeo-skills (from lev-os/agents) | MIT | 2 | **Mostly duplicate.** Apple-derived budgets. The idea of a machine-checkable VFX spec plus validator is the only new part. |
| 17 | game-vfx-workflow | C4rI0s/game-3d-skills | MIT | 3 | **Partly useful.** A lifecycle case table (cancelled wind-up, teleport, pooled reuse, owner death). |
| 18 | gamedev-2d-art-vfx-2d | claude-dev-suite/claude-dev-suite | MIT | 3 | **Partly useful.** A table of canonical frame counts and fps per effect type. Some claims are dubious (see §3). |
| 19 | glsl-shaders | PIXARTSeu/Synapse | **AGPL-3.0** | 2 | **Duplicate / irrelevant** (Three.js). Don't copy: AGPL. |
| 20 | impact-animation-vfx | PixelWao/codex-gamedev-skills | MIT (+Apache-2.0 upstream) | 3 | **Partly useful.** Tween ownership per (target, property) with baseline restore, and an absolute-time easing rule. |
| 21 | juice-apply | m4bwav/game-juice | MIT | 3 | **Partly useful.** Accessibility defaults table (flash area/rate, hit-stop toggle, haptics) and a `juice-changes.md` revert log. |
| 22 | juice-scan | m4bwav/game-juice | MIT | 4 | **Useful.** Roblox engine reference (`HapticEffect`, AnimationTrack hit-stop, UIScale pop, coyote time) and a static juice scanner with risk patterns. |
| 23 | lihfolk-vfx | lihfolk-cy/v2-vault | **CC-BY-4.0** for code/notes; textures/meshes are a separate pack (use in games OK, no redistribution) | 5 | **Useful.** A production Roblox combat-VFX kit with blind-review lessons, per-preset budgets, culling tiers, a replication protocol, and hit-stop/shake code. |
| 24 | particles-vfx (8d28d2) | zenobi-us/dotfiles | MIT | 2 | **Duplicate**, Godot-only. |
| 25 | particles-vfx (e983e2) | jame581/godotprompter | MIT | 2 | **Duplicate of #24** (near-identical text, newer Godot notes). |
| 26 | roblox-animation | nonlooped/roblox-suite | MIT | 4 | **Useful.** Animator, markers, priorities, IKControl and constraints, AnimationClipProvider, and the "End" keyframe rule. |
| 27 | roblox-animation-vfx | tabooharmony/roblox-brain | MIT | 4 | **Useful.** Ended vs Stopped, WeightCurrent convergence, the tween `DelayTime` ownership trap, `Completed` firing on cancel, and Server Authority rules for predicted effects. |
| 28 | roblox-lighting | tabooharmony/roblox-brain | MIT | 2 | **Mostly duplicate** of ch. 23 and 45. Mood presets only. One claim conflicts with ch. 23 (see §3). |

---

## 2. New to us, by area

Format for each item: the idea → numbers → **from** → **goes to**. Items marked **[licence]** are big enough that copying text or code would trigger attribution or licence terms.

### 2.1 VFX

1. **Flash placement rule.** The impact flash is small (about **0.6× body size**), lasts **1–2 frames**, and starts **1 frame after contact** at the blade or crescent head, ahead of the body, never centred on the character. Our skill says only "onset is the brightest frame". **From** lihfolk-vfx. **To** `vfx` Method step 3 and the `vfx-craft` playbook.
2. **"Grandeur = escalate a few layers, cut others."** In a blind-reviewed case, adding vortex, rune circle, smoke and rings to a spin attack *dropped* the median score from 8.1 to 7.7, with only about 150 particles live. The limit was screen clutter, not particle caps. Their rules: at most **one growing element** per effect (vortex *or* sigil); each repeat bigger, brighter, faster *and different*; later layers shorter; ground rings expand while fading; re-check the character silhouette at game distance after every added layer. **From** lihfolk-vfx. **To** `vfx` "Make it insane" guardrail plus the `vfx-craft` playbook.
3. **Three tones in every frame.** Every frame has a white rim/glint, an element-colour body and dark ink (blue-black thinning to blue, never grey, or it reads muddy). Dark only reads over something bright. White on a pale floor gets a thin dark outline. Void elements invert this: a near-black body with the rim only at the silhouette (shell scale about 1.02, transparency about 0.45). **From** lihfolk-vfx. **To** `vfx` §Colour, `materials`.
4. **Frontal-slash clamp.** Slash arcs stay within ±100° of LookVector (120–200° long) and drift at most 10° further. No 360° rings unless it's an explicit spin move. No weapon `Trail` on sweeps over about 120° or on stabs, because it draws a wedge behind the back. **From** lihfolk-vfx. **To** `vfx` Engine notes (Roblox).
5. **Beams under bloom.** Hairline beams need *low* Brightness, because bloom fattens them. Ribbons read thicker with a lower body brightness and a thin white core. Light shafts only as additive textures tapered both along and across. **From** lihfolk-vfx. **To** ch. 45 §2.6 gotchas.
6. **Canonical frame counts per effect** (flipbook authoring): smoke puff 6–8 frames at 8–12 fps (600–700 ms); fire loop 4–6 at 8–10; splash 5–7 (200–400 ms); electricity 2–3 frames at 24–30 fps (60–100 ms, never mirrored); sparks 3–5; sword trail 3–4 at 24+ (100–150 ms); damage flash 2–3 (60–120 ms); explosion 8–12 at 8–15 (0.5–1 s); pickup 8–10 at 12–15. All of these fit inside Roblox's 30 fps flipbook cap. **From** gamedev-2d-art-vfx-2d. **To** ch. 45 §1.6 and the `vfx-craft` toon-flipbook lever.
7. **Water impact as four behaviours, not one emitter:** surface ring, heavy upward splashes, fine droplets, lingering mist, each with its own lifetime, speed, scale and transparency. The same decomposition applies to any natural effect. **From** roblox-animation-vfx. **To** `vfx-craft` recipes.
8. **One combined screen pass, hidden at zero.** All screen effects (flash, aberration, vignette, warp, grain) go through one pass, and the quad is hidden when every parameter is 0. On Roblox that means one overlay `ImageLabel`/EditableImage plus one `ColorCorrectionEffect` tweened, never several stacked. CRT look presets (OFF/SUBTLE/ARCADE/HANDHELD/BROKEN) cross-fade over 0.45 s. "BROKEN" works as a failure sting: snap in about 0.08 s, hold about 0.5 s, fade back over 0.5 s. **From** game-feel-polish. **To** `editable-image` screen-overlay section and ch. 40 §9.

### 2.2 Optimisation and budgets

1. **Per-preset budget table, real shipped numbers** (quality 1, per cast). Slash sweep: 51 particles, 9 SpecialMesh parts, 4 beams, 1 light. Hit spark: 33 particles, 0 meshes. Charge-up: 69 particles. Level-up: 76 particles. Projectile: 9 muzzle + about 19 wake + 25 impact. Exactly **one light per effect, no shadows**. **From** lihfolk-vfx **[licence: CC-BY-4.0, credit "LihFolk Vault V2"]**. **To** ch. 45 §9.2, which is marked `[UNVERIFIED]` today; these give a second data point.
2. **Live caps and degradation ladder.** Live particle cap **900 on PC, 360 on touch**; touch starts at quality 0.6. Above **75 % of the cap or beyond 160 studs**: halve counts and drop decoration (glints, mist, ink cards, small spikes, ghosts). Beyond **220 studs**: play nothing. At most **8 concurrent effects**, and `important` casts bypass the limit. Several modules share one cap (`externalLive`). Culled calls return a no-op handle, so callers never nil-check. Compare our ch. 45 (800 desktop / 250 mobile, 5 Hz culling): close agreement, and theirs adds the 75 % rule and the no-op handle. **From** lihfolk-vfx. **To** ch. 45 §9.4–9.5 and `vfx` step 6.
3. **One Heartbeat for every effect**, disconnected when idle. Each effect is a Model destroyed at end of life, with `Debris` as a safety net. An error inside a step cleans up the effect. Every part is Anchored with CanCollide/CanQuery/CanTouch/CastShadow off. **From** lihfolk-vfx. **To** `vfx` Engine notes.
4. **Feedback budgets per 100 ms window**: default **32 accepted events and 120 particles per 100 ms**. Events arrive with a stable ID and are deduped for a TTL (default 10 s). Dense contacts (debris) are aggregated *before* dispatch and sorted by tier, then ID, when priority matters. Our ch. 45 §9.6 coalesces by time window; the ID-dedupe and hard particle-per-window cap are new. **From** game-feel-event-orchestration. **To** ch. 45 §9.6 and a Luau `FeedbackDirector` in `vfx/examples`.
5. **Pool every reusable thing with reset discipline.** Before reuse, reset parent/enabled, attachments, all sequences, active tweens and connections, and the expiry timestamp. Callbacks captured before reuse must carry an owner *generation* so they can't finish the new instance. **From** roblox-animation-vfx and game-vfx (Ddrubok). **To** ch. 45 §9.3.
6. **Sound voice pools.** **24 players per kind** (positional and flat); steal the oldest. Drop a second trigger of the same bank inside **25 ms**: two identical samples on one frame double the amplitude and clip. Ours rate-limits at 50–80 ms per bus (ch. 83), which is compatible; the 25 ms *same-bank* dedupe and the clipping reason are new. **From** game-feel-polish. **To** ch. 83 rule 5 and the sound manager in ch. 45 §8.5.
7. **Particle preprocess (pre-warm).** Godot sets `preprocess` to 1–2× lifetime so ambient emitters don't pop in. Roblox `ParticleEmitter` has no pre-warm, so ambient emitters visibly fill in after a streaming-in or enable. Workarounds: enable ambient emitters a lifetime before the camera arrives, or burst-`Emit` at enable. Also: tick ambient simulation at a fixed **30 Hz**, not per frame. This idea is ported (Godot `fixed_fps = 30`); it isn't a Roblox fact. **From** particles-vfx. **To** ch. 45 §1.7 and §9.7 (the gotcha is ours to verify).
8. **Half-resolution heavy effects** look identical to most players. This applies to EditableImage overlays: render blur/glow at half the size and let `ResampleMode` upscale. **From** glsl-shaders (idea only, AGPL text not copied). **To** ch. 40 "Resolution tiers" (already partly there).

### 2.3 Animation and game feel

1. **`impact(position, strength)` composite with thresholds.** Strength is 0–1:
   - shake = lerp(0.18, 0.75), with distance falloff (1 − d/r)², r = 600 px
   - hit-stop = lerp(35, 130) ms
   - white screen flash only above **0.25** (alpha lerp 0–0.4, 100 ms)
   - chromatic aberration and zoom punch only above **0.45** (zoom up to 5 %)
   - sound bank `hit_heavy` above 0.5

   Rule: screen-wide effects open only above a threshold, so routine hits don't wash out big ones, and you raise contrast by *lowering* routine feedback, not by raising the top tier. **From** game-feel-polish (Liquid UI Kit values, MIT). **To** `vfx` step 4 and `examples/Impact.luau`.
2. **Tier table:** UI click trauma 0.10–0.15 / hit-stop 30 ms or none; light hit 0.30 / 30 ms; solid 0.45 / 90 ms; crit 0.75 / 120 ms; kill or explosion 0.85 / 130 ms; over 200 ms "the game froze". **From** game-feel-polish. **To** ch. 45 §4.2. It agrees with our 60–90 / 100–130 ms; the trauma column is new.
3. **Overlapping hit-stop policy.**
   - effective scale = **external base scale × min(active multipliers)**
   - each request has its own ID and deadline: A over 0–80 ms plus B over 30–150 ms stops until 150 ms; cancelling A doesn't cancel B
   - a longer stop extends, a shorter one never cuts
   - `baseScale()` must return the *external* policy (pause, slow-mo), never the feedback-modified value, or tempo recurses
   - dispose restores the *live* baseline, never a hard-coded 1.0
   - hit-stop beats slow-mo
   - **cap cumulative hit-stop per second**
   - **shorten hit-stop on fast repeated hits**

   Our `Impact.luau` does max-extend only. **From** game-feel-event-orchestration, game-feel-polish, gamestack, juice-scan. **To** `vfx/examples/Impact.luau` v2.
4. **Roblox AnimationTrack hit-stop done right.** `AdjustSpeed(0)` per track, then restore *the speed each track had before the first overlapping stop* (keyed by a token, so overlapping stops extend rather than restore early). The optional **catch-up** plays at speed × (2 − slow) for the same duration so the clip lands back on schedule and markers keep their gameplay timing. Capped at **0.2 s**, usual range 50–90 ms. Accepts an Animator (`GetPlayingAnimationTracks()`). **From** lihfolk-vfx **[licence: CC-BY-4.0]**. **To** ch. 45 §4.2 (which only names `AdjustSpeed`) and `vfx` Engine notes.
5. **Camera shake with source distance falloff.** Smoothstep from full strength at **30 studs** to zero at **150 studs** from the camera. Noise at **16 Hz**. Peak pitch/yaw **1.6°**, roll **0.9°**. Bind to RenderStep only while a shake is live, unbind when empty. Starting intensities: **0.12 medium hit, 0.35 finisher, 0.6 ultimate**, over **0.15–0.4 s**. **From** lihfolk-vfx. **To** ch. 45 §4.1 (ours lacks distance falloff; see §3 on peak angle).
6. **Shake keeps moving during hit-stop.** Decay shake by real time (and clamp dt to 0.1 s) so the frozen frame still vibrates. A shake timed with scaled dt freezes with the world. **From** game-feel-polish. **To** `vfx` step 4. This conflicts with our playbook wording, see §3.
7. **Asymmetric impact tweens, exact split.** Punch scale: 22 % out (quad ease-out) to ×1.25, then 78 % back (elastic ease-out), 0.32 s total. Squash/stretch: 20/80 over 0.36 s, with 1/(1+a) across the axis. Punch rotation: 8° over 0.4 s. Pop-in: 0.4 s back-out. Pop-out: 0.25 s back-in. Hit flash: 90 ms, hold 34 %, fade 66 % quad-out, mixed toward the colour, never touching alpha. Ours gives 40–70 ms in / 120–200 ms out, which is consistent; this adds the ratio and elastic settle. **From** game-feel-polish. **To** ch. 45 §4.3.
8. **Rest-state ownership for tweens.** One tween owns each (target, property). Record the node's rest value the first time it's touched, kill the previous tween on that channel, and always return to rest. Always ease from absolute progress `u = (now − start)/duration`, never by repeated lerp from last frame. A 20-press spam test must leave nothing at the wrong scale. **From** game-feel-polish and impact-animation-vfx. **To** `ui-hud` Self-check and `lib/figma-ui/Motion.luau`.
9. **Damage numbers spec.**
   - pool **64**
   - font 22 (crit 32), black outline at 0.85 alpha
   - start scale 0.6 (crit 0.4), pop to 1.1 (crit 1.35) over 16 % of life with back-out, then to 1.0 over 20 %
   - motion `y = −rise·t + ½·420·t²`, x drift ±34 px, rise 130 px/s (crit ×1.3)
   - **hold opaque 30 % of life, then fade over 34 %**, because fading from the start makes the number unreadable while it matters
   - life 0.9 s (crit ×1.25)

   **From** game-feel-polish. **To** `ui-hud` damage numbers.
10. **Counter roll and lag bar.**
    - Counter roll time = 0.55 s × clamp(|Δ| / max(|prev|, 1), 0.15, 2.0), clamped to 0.12–1.1 s. Punch ×1.22 elastic over 0.4 s; tint returns faster (0.3 s) than scale.
    - Bar: fill 0.16 s quad-out; ghost holds **0.25 s**, then drains 0.45 s.
    - Loss rattle strength = clamp(Δ×3, 0.2, 1) over 0.4 s, two sines at 96 Hz and 77 Hz, 5 px.
    - Gain pulse 0.35 s.

    **From** game-feel-polish. **To** `ui-hud` bars and counters, and ch. 63.
11. **Refusal shake for a disabled button:** amount 1 → 0 over 0.45 s elastic, sum of two sines **74 Hz × 9 px + 131 Hz × 4 px**, plus an error sound at −6 dB. State doesn't change. Sound levels: hover −10 dB, press −4 dB, refused −6 dB. **From** game-feel-polish. **To** `ui-motion-and-sound` playbook (the `cant_afford` / `denied` events).
12. **Toast stack:** in 0.24 s back-out (slides 90 px, grows 0.86 → 1.0), hold 1.4 s, out 0.26 s back-in, max **5 visible**, oldest retired first, reflow 0.28 s cubic-out, entry rattle 6 px at 88 Hz and 71 Hz. Menu stagger: **60 ms** per step; the outro uses 60 % of the intro delay. **From** game-feel-polish. **To** `ui-hud`.
13. **Kao 2020 inverted-U.** N=3,018: *Extreme* juice hurt experience, motivation **and raw performance** as much as *None*; Medium–High won. Kao CHI 2024 (N=1,699): over-amplification impairs the sense of agency. Proposed per-event ceiling:
    - 3–5 simultaneous emitters
    - peak shake 2 px minor, 8 px major, 20 px climactic
    - hit-stop 0–10 frames
    - 3 SFX layers max
    - screen clear within 0.5–1.5 s
    - top tier of any primitive at most about once per session

    This is evidence for our HIERARCHY "calm by default" rule, which we don't cite today. **From** gamestack game-feel-and-juice (secondary citation; verify the papers). **To** ch. 82 or `HIERARCHY.md` §4 and the `vfx` budget.
14. **Latency thresholds by interaction:** expert FPS about 15 ms; platformer degrades from about 50 ms; action annoys at about 100 ms; RTS orders tolerate 500–1000 ms; UI transitions 100–200 ms ideal, over 400 ms sluggish. Coyote time **5 frames / 83 ms** (Celeste); input buffer 100–200 ms (over about 500 ms fires "ghost actions"); enemy anticipation at least 150–200 ms; player attack startup 4–8 frames; follow-through 2–5 frames. **From** gamestack. **To** ch. 82 §1.
15. **Animation marker discipline (Roblox).**
    - Use `GetMarkerReachedSignal(name)` with a free-form param string (for example `"left,heavy"`), not `KeyframeReached` or polling `TimePosition`.
    - Keep marker handlers tiny and push side-effects through `task.defer` so the animation evaluator isn't stalled.
    - Retime wind-ups so a charge effect's release lands on the `Hit` marker: speed = authored lead / clip lead.
    - Start sounds skipped forward by their measured peak offset, so the crack lands *on* the marker.
    - Markers are hints, never proof of a hit: validate on the server.

    **From** roblox-animation and lihfolk-vfx. **To** a new "Animation" section in ch. 45 (we have none) and `vfx` Engine notes.
16. **IKControl plus constraint limits.** Set Type, EndEffector, Target, ChainRoot. `SmoothTime` damps; higher `P` is snappier but overshoots. Add Hinge or BallSocket constraints at the Motor6D pivot (wrist `UpperAngle` about 80°) so joints don't hyper-extend. Use markers to enable or disable a given IKControl (for example a reach). **From** roblox-animation. **To** a new animation section (not covered anywhere in the kit).

### 2.4 SFX and audio

1. **Procedural SFX pipeline (the biggest gap).** A sound is a JSON patch that renders to WAV deterministically. It is the editable source and lives in the repo, like our baked textures.
   - Layers: `sine/triangle/square(duty)/saw/noise/sample`; breakpoint `freq` and `cutoff` curves (exponential sweeps, same-`t` points for arpeggio steps); env attack/hold/release with a `curve` exponent (2–3 for percussive).
   - Filters: SVF low/high/band-pass, `q` 0.7 gentle, 4–8 resonant.
   - Tone shaping: `detune_cents` 5–15 for thickness, tanh `drive` 0.5–2 for warm thumps, FM (integer ratio = bell, 1.4 or 3.5 = metallic; falling index = "bling").
   - `partials` presets: wood `[1,0],[2.76,−8],[5.4,−16]`, bell `[1,0],[2.4,−4],[5.95,−10]`.
   - `vibrato`: 5–7 Hz sings; 12–20 Hz with decaying depth gives a spring "boing".
   - `at` lists for rolls and footfalls, and `jitter` per hit (layers at the same time share a draw).
   - Master: high-pass, LUFS target, peak ceiling, small reverb.
   - `vary` gives `--variants N`, round-robin with no immediate repeat.
   - **PolyBLEP** oscillators so square and saw don't alias.
   - The renderer rejects unknown keys, so a typo fails loudly.

   **From** game-sfx **[licence: MIT; worth porting the design, and possibly the stdlib Python, with the copyright notice]**. **To** a new `tools/sfx/` plus a new **`sfx` skill** (we have no SFX-authoring skill at all; ch. 45 §8 and ch. 83 cover playback and mixing only).
2. **Per-asset loudness ladder** (master LUFS of each file): hero impacts and explosions **−12 to −14**, pickups and jumps **−16**, footsteps and loops **−18 to −20**, UI **−20 to −24**, peak never above **−1 dBFS**. Sharp clicks *measure* 2–4 dB quieter in LUFS than they sound, so match those by ear. This pairs with our mix-level target in ch. 83 (−18 ±2 LUFS integrated). Ours is the bus; this is the file. **From** game-sfx. **To** ch. 83 §2 (new "asset loudness" column).
3. **"Doctor" measurements that replace hearing.** An agent can't hear, so it checks numbers:
   - crest factor under 6 dB = droning (no transient); over 20 dB = spike with no body
   - spectral centroid targets: UI 1–4 kHz, pickups 1.5–5 kHz, impacts 150–1500 Hz, explosions under 800 Hz, footsteps 200–1500 Hz
   - energy: 2–5 kHz over 50 % = harsh; over 16 kHz above 5 % = aliasing or hiss
   - leading silence = reads as input lag; also checks tail silence, DC offset, non-zero start/end (click risk) and clipped runs
   - a PNG spectrogram (log frequency, 100 ms ticks) so the model can *see* sweeps, noise smears and harmonics

   **From** game-sfx. **To** `tools/sfx/doctor` and a new QA check in `check_all.sh` for any WAV in a repo.
4. **Layering rule with frequency lanes.**
   - transient 0–30 ms (noise or click, high-passed above 1–2 kHz)
   - body 30–200 ms (tonal, 100–1000 Hz)
   - tail (filtered noise or decaying tone)
   - optional sweetener
   - pitch *moves*: down for hits, lasers and hurt; up for jumps, power-ups and confirms; stepped for coins; static only for UI ticks
   - durations: UI 15–80 ms, pickups 150–400 ms, impacts 100–300 ms
   - high-pass UI and pickups at 150–300 Hz; keep 40–80 Hz sub for impacts only; low-pass bright layers at 8–12 kHz

   Ours (ch. 45 §8.4) has transient/body/tail timing; the pitch-direction rule, durations and filter lanes are new. **From** game-sfx. **To** ch. 45 §8.4.
5. **Category recipes with numbers.** Some highlights:
   - retro coin: square 50 %, 988 → 1319 Hz (a 4th up), 60 ms + 200 ms decay
   - cartoon coin: FM bell, ratio 3, index 2.5 → 0.3, B5 → F#6
   - UI click: noise tick high-passed at 3 kHz for 6 ms + triangle 2000 → 1700 Hz over 25 ms, −20 LUFS
   - hover: 2–3 kHz for 20–40 ms, 6 dB under the click
   - confirm: rising major 3rd or 5th, 60 + 120 ms
   - error: two falling notes, or a 150–250 Hz buzz
   - laser: 1500 → 300 Hz saw + 5 ms click
   - explosion: noise with low-pass sweeping 3 kHz → 200 Hz over 0.8–1.5 s + sub 60 → 35 Hz + 30 ms crack, −12 LUFS
   - level-up: C-E-G-C, 90 ms per note, last note held 400 ms
   - whoosh: band-pass centre 300 → 2000 → 500 Hz, q 1.5–3, peaking at 40–60 %
   - magic sparkle: 15–40 sine blips at 2–8 kHz scattered over 0.6 s

   **From** game-sfx. **To** the new `sfx` skill (recipes table); it also feeds our sound board (`ui-motion-and-sound` playbook) as candidates.
6. **Foley pattern, validated by ear:** one *shared* impact layer for every surface (so it's the same creature everywhere), plus a recorded surface texture, plus a small room (reverb mix 0.04–0.06, decay 0.3), with four paired variants. Muffle the impact per surface: low-pass about 3.5 kHz on dirt, 2.5 kHz on water/snow, 1.8 kHz on grass/mud, bright on stone. All-synth realistic foley was rejected as "toy-like", so use samples for grounded styles and the synth for UI, magic and cartoon. **From** game-sfx. **To** the `sfx` skill.
7. **Sample slicer scoring** (for cutting single hits from CC0 recordings): each hit gets `peak` relative to the loudest, `clean` (dB above what precedes it: over 25 dB isolated, under 10 dB overlapping) and `decay` (dB fall before the next hit). Four different real hits beat four pitch-shifted copies of one. CC0-only Freesound search keeps the licence clean. **From** game-sfx. **To** the `sfx` skill. Note the Freesound API key must go through a secret, never chat.
8. **`SOUND_STYLE.md` sound bible per game:** style (retro/cartoon/grounded), source palette, world materials, music key and tempo (jingles use the key's triad), reverb space, loudness ladder, sound list mapped to code events, and a one-line-per-change Decisions log. Verbal fixes translate to parameters: "shrill" → lower notes or FM index, low-pass at 6–8 kHz; "weak" → driven sub or longer body; "cheap" → more layers, room, moving pitch. **From** game-sfx. **To** the `sfx` skill template, alongside `docs/look/`.
9. **Matched UI sound sets.** Pick one "voice" (glass/wood/soft/retro/mechanical) for every UI cue in a game. A durations reference: click 10–45 ms, hover 20–65 ms, tab switch 85 ms, modal open/close 135 ms, drawer 225 ms, riser 615 ms. **From** better-sfx. **To** the `ui-motion-and-sound` playbook as a candidate source. **Licence:** sounds are free for commercial use with no credit, but standalone redistribution is banned and Content ID registration is banned. On Roblox, upload them as **private** assets only, never "Distribute" on the Creator Store.
10. **Audio test procedures:**
    - **mute-all**: the game is still playable
    - **sound-only**: every event is identifiable by ear
    - **eyes-closed menu**: you can tell highlight, confirm and back apart by sound
    - fire one action **20×**: it stays non-fatiguing
    - audio–visual sync within about **50 ms**

    **From** gamestack. **To** ch. 83 §3 Measuring.

### 2.5 Roblox API specifics and gotchas

1. **`HapticEffect` replaces `HapticService`.** The creator docs mark `HapticService` superseded, though the API dump doesn't tag it deprecated. Create the effect once on the client: `Type = Enum.HapticEffectType.GameplayCollision` (also `UIClick`, `UIHover`, `UINotification`, `GameplayExplosion`, `Custom`). It has `Looped`, `Position`, `Radius`, `SetWaveformKeys`, `Play`, `Stop`. Gate it behind a haptics setting. We have no haptics coverage at all. **From** juice-scan (verified there 2026-10-26; re-verify). **To** ch. 45 (new §), `vfx` and `ui-hud` Engine notes.
2. **`Animator:LoadAnimation`, not `Humanoid:LoadAnimation`.** Preload `Animation` instances with `ContentProvider:PreloadAsync` (tracks are not valid there). Replacement default animations need the final keyframe named exactly **"End"**. Client-played animations on the player's own character replicate only if the asset is owned by the player or the experience. Priority order: Core < Idle < Movement < Action < Action2 < Action3 < Action4; don't compare enum numbers, because Core has a special value. Same-priority tracks blend by weight. **From** roblox-animation and roblox-animation-vfx. **To** a new animation section.
3. **Track events.**
   - `Stopped` fires on natural end *and* on explicit `Stop()`; `Ended` fires only after the fade has fully released the pose. Hook cleanup to `Ended` and chaining to `Stopped`.
   - `DidLoop` counts loops.
   - `Length` is 0 until loaded; duration = Length/Speed, and Speed 0 means paused.
   - `WeightCurrent` converges to `WeightTarget` over the fade, so poll |Δ| < 0.01 when the state machine needs a settled blend. There's no writable `.Weight`.

   **From** roblox-animation-vfx. **To** the new animation section.
4. **Tween ownership traps.** `TweenInfo.DelayTime` does **not** queue ownership: a delayed tween on the same property can cancel the earlier one. Start phase N+1 from phase N's real `Completed`. `Completed` also fires with `Enum.PlaybackState.Cancelled`, so check the state before destroying a pooled or shared target. **From** roblox-animation-vfx. **To** ch. 45 §4.5 and `lib/figma-ui/Motion.luau` review.
5. **Server Authority (beta) and effects.**
   - Synchronized animation logic runs in `RunService:BindToSimulation()` (needs `Workspace.UseFixedSimulation`).
   - Don't cache `AnimationTrack` handles across rollback; re-query `Animator:GetPlayingAnimationTracks()`.
   - Predicted effects must be **reversible** (cancel or hide on rollback) and never grant outcomes.
   - Use `RunService:IsResimulating()` to suppress duplicate one-shots during replay.
   - `BindToAnimation()` runs at fixed frequency, ordered relative to Animator updates only when fixed simulation is on.

   **From** roblox-animation-vfx and roblox-animation. **To** ch. 47 (server-authority section) and ch. 45. Ch. 47 mentions server authority, but not effect reversibility or `IsResimulating`.
6. **Disable vs destroy for legacy emitters.** `Sparkles`/`Fire`/`Smoke` (and `ParticleEmitter`): `Enabled = false` lets live particles finish; Destroy or `Parent = nil` kills them instantly. To stop cleanly, disable, then `Debris:AddItem` after the max lifetime. **From** roblox-animation-vfx. **To** ch. 45 §1.7.
7. **Fresh texture uploads can fail `PreloadAsync` for 20–60 s.** Never guess an asset id. Empty id means skip the layer with one warning. **From** lihfolk-vfx. **To** ch. 45 §8.9 / the Studio playbook.
8. **`SpecialMesh` centres a FileMesh on its bounding box,** so an arc mesh whose bbox isn't centred on the arc's circle sits off the swing centre. Fix with a yaw or position offset, checked once per mesh. Also verify that a SpecialMesh `TextureId` shows on Neon. **From** lihfolk-vfx. **To** `vfx-craft` "Limits we hit".
9. **Ghost and afterimage cloning** skips parts with `Archivable = false`; check accessories and layered clothing. **From** lihfolk-vfx. **To** `vfx-craft`.
10. **One Highlight per object.** An aura or shield `Highlight` rim fights an existing character Highlight. The emulator note "Roblox Color3 is sRGB, linearise for previews" matters for our Blender/PIL look-dev previews. **From** lihfolk-vfx. **To** ch. 45 §7.5 and the `look-dev-loop` playbook.
11. **VFX replication protocol** (server validates, clients render):
    - The caster predicts locally (`important = true`) and fires `AbilityCast(presetId, aim)`, sending no colour, size or CFrame for the server to trust.
    - The server checks: type, preset whitelist, finite aim, alive, range clamp, per-preset cooldown, and a **token bucket (6 burst, 3/s)**.
    - It then sends **one** compact payload `(caster, presetId, cf, elementIndex, seed, aux)` to players within **250 studs**, skipping the caster.
    - Persistent states (aura on, shield up) go as **attributes**; each client starts or stops its own effect from `GetAttributeChangedSignal`.

    This fits our FRAMEWORK "server validates everything" rule exactly. **From** lihfolk-vfx **[licence: CC-BY-4.0]**. **To** ch. 46/47 and `vfx` Engine notes.
12. **Coyote time on a Humanoid:** record `os.clock()` on `Running`/`Landed` state; on `JumpRequest` while `FloorMaterial == Air` and within 0.12 s, call `ChangeState(Jumping)`. **From** juice-scan. **To** ch. 45 (new "forgiveness" §) if a game needs platforming.

### 2.6 QA and tooling

1. **Feel-trace schema plus auditor.** Record JSONL with monotonic **unscaled** ms: `hitstop_start/extended/end`, `feedback_accepted` (eventId, channels, particles, reducedMotion and allowFlashes *snapshots*), `feedback_rejected`, `vfx_batch` (active/capacity), `camera_delta` (x, y, roll). The auditor flags:
   - errors: `duplicate_accepted`, `hitstop_not_released`, `hitstop_orphan_end`, `hitstop_double_start`, `out_of_order`, `reduced_motion_violation`, `flashes_disabled_violation`, `camera_nonfinite`, `vfx_capacity_exceeded`
   - warnings: `hitstop_excessive` (over 250 ms), `event_budget_exceeded` / `particle_budget_exceeded` (32 events or 120 particles per 100 ms)

   Our `Impact.luau` sim could emit this trace from lune so the checks run headlessly. **From** game-feel-debugging-qa (MIT, about 120 lines of stdlib Python). **To** `tools/` plus ch. 64, wired into `check_all.sh` for games that log traces.
2. **Regression matrix for feel:**
   - overlapping hit-stops, and a scene unload mid-freeze
   - external slow-mo restored correctly
   - same visual value at the same timestamp at **30/60/144 fps**
   - duplicate contact IDs, and 1000+ debris contacts
   - tab resume, reduced motion, flashes off
   - camera delta finite
   - cancelled animation restores baseline

   Plus an explicit list of what logs can't prove (comfort, GPU cost, photosensitivity). **From** game-feel-debugging-qa. **To** ch. 64 and the `vfx` Self-check.
3. **Evidence ladder for VFX claims.** Source text proves intent only. A generated-but-unopened file proves creation only. A still or contact sheet proves shape and colour, not motion. An ordered frame sequence proves continuity, not real-time feel. Viewed playback proves readability in the observed conditions only. Target-device profiling proves cost. Report status in five columns: **created / visually inspected / motion checked / export checked / integrated-tested**. **From** game-vfx (Ddrubok). **To** CLAUDE.md working rule 7 (report honestly) and the `vfx` Self-check.
4. **Lifecycle case table for every effect:**
   - wind-up cancelled → no projectile or hit burst
   - release then target moves → visual follows the gameplay projectile
   - hit confirmed → exactly one impact at the real contact
   - status refresh → updates, no stacking
   - owner dies → emission stops, resources released
   - teleport or pooled reuse → old trail doesn't bridge
   - surface emitter changes site → new lifetime

   Plus **pending vs confirmed**: a predicted cue may acknowledge but never signal success or reward; an older confirmation must not revive a rejected state. **From** game-vfx-workflow and game-vfx (Ddrubok). **To** the `vfx` Self-check and `reward-moments` (purchase pending vs confirmed).
5. **Static juice scanner.** It walks a Rojo repo, finds "moments" (`.Touched`, `Humanoid:TakeDamage`, `Died`, `StateChanged`, `JumpRequest`, `GuiButton.Activated`, leaderstats changes) and lists missing feedback channels and risk patterns:
   - `timeScale = 0` never restored
   - effects instantiated in per-frame functions
   - shake triggered per frame
   - full-screen flash without a toggle

   Lessons from its own field tests: name matching floods on tests, editor tools and `Has/Is/Get/Can` predicates, and misses genre core verbs (cards, turns), so add those. **From** juice-scan (MIT). **To** `tools/doctor.py` repo audit (a "juice" section), alongside the kit doctor.
6. **A/B kill switch and spam test.** One hub owns `enabled` plus an intensity multiplier from 0 to 2. Turning it off resets everything it owns (time requests, camera offsets, screen pulses, voices) while preserving pause and other owners' state. Verify by A/B on the same screen; any effect that makes no visible difference gets deleted. Spam test: 20 rapid presses leave no stuck scale or time scale and no clipping. **From** game-feel-polish. **To** `vfx` and `ui-hud` Self-check; it maps onto our `Intensity.budget` and the `_G.__vfx` dev hooks.
7. **Frame-indexed contact sheets:** `ffmpeg -i in.mp4 -vf "scale=480:-1,drawtext=text='%{n}':x=4:y=4:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.5,tile=5x5" sheet_%03d.png` stamps the frame number on each of 25 tiles. It lets an agent check "flash on frame contact+1" or "recovery within 12 frames" on a Studio capture. **From** 4k-vfx (idea only). **To** the `look-dev-loop` playbook.
8. **Machine-checkable VFX spec.** A JSON effect packet (event, phases, layers, blend, space, particle/draw/overdraw budgets, reduced-motion fallback) validated by a script before building. **From** game-vfx (jeo). **To** a possible later addition to the `vfx` skill; low priority.
9. **Accessibility defaults table:**
   - shake slider 0–100 %, where 0 really means off
   - reduce motion: shake and kick 0; *their* suggestion halves tween durations (ours swaps motion for fades, see §3)
   - flashes covering about **20 % or more of the screen at ≤3 per second**, **no saturated red flash** (WCAG 2.3.1, XAG 118)
   - a **hit-stop toggle**, because some players find freezes disorienting
   - a haptics intensity slider
   - hold all of this in one settings module

   **From** juice-apply. **To** ch. 81/82 and `hierarchy-audit` (flash checks). Ours covers ReducedMotionEnabled and WCAG flash rate already; the 20 %-area threshold, red-flash rule and hit-stop toggle are new.

---

## 3. Claims that look wrong or contradict our research

| Claim | Where | Why it's suspect / what we say |
|---|---|---|
| "`Animator:LoadAnimation` caches tracks when called with the same Animation on the same Animator" | roblox-animation (3d-animations.md) | Likely **wrong**. Repeated `LoadAnimation` calls create new tracks, which is what triggers the well-known per-Animator track-limit warning. Cache the returned track yourself. Verify against the AnimationTrack/Animator docs before writing it into the kit. |
| `Animator:GetTrackByAnimationId()` | roblox-animation-vfx | Not in our research; treat as **unverified**. `GetPlayingAnimationTracks()` is the known API. |
| Hit-stop sketch: `AdjustSpeed(0)` then `AdjustSpeed(1)` after a delay | juice-scan roblox.md | **Buggy.** It restores speed 1 even for tracks running at another speed, and an earlier overlapping stop's timer un-freezes a later one. Use lihfolk's token-and-restore-prior-speed pattern (§2.3 item 4). |
| "Don't actually `Time.timeScale = 0`, it breaks animation timing on resume" | gamedev-2d-art-vfx-2d | **Dubious.** The other skills freeze at scale 0 safely by timing the stop on the wall clock. The real bug is timing the stop with scaled dt. Our ch. 45 avoids engine timescale on Roblox anyway. |
| Shake peak rotation 1.6° (lihfolk), 2.5° (juice-scan), roll 0.06 rad (polish, 2D) | several | Our ch. 45 §4.1 uses **6°** peak at trauma 1 plus 0.9 studs of translation. That is 2.5–4× theirs. Ours is squared-trauma gated, so typical hits see much less, but on a phone 6° at a heavy hit may be too much. Calibrate in the look-dev loop and consider 2–3° peak plus distance falloff. The gamestack note "3D shake = rotation, not translation (translation clips through walls)" also argues for cutting our 0.9-stud translation. |
| Shake keeps moving during hit-stop (real-time decay) | game-feel-polish | Conflicts in spirit with our `vfx-craft` "Hit-stop freezes everything except the hero flash". Not wrong, a design choice. Decide one rule and write it down; the polish argument (a frozen frame that still vibrates reads as impact) is persuasive. |
| Reduced motion = "tween durations halved" | juice-apply accessibility.md | Contradicts the Roblox guidance in our ch. 63 (animation time 0, or swap movement for fades). Keep ours. |
| `Lighting.ShadowSoftness = 0.2` as a tuning knob; "sharp shadows = scarier" | roblox-lighting | Our ch. 23 says `ShadowSoftness` has **no effect** except under specific Technology modes. The day/night sample increments `ClockTime` in a `task.wait()` loop (on the server it replicates every frame); do it on the client or step coarsely. |
| "Limit to 4–6 shadow-casting lights" / "pick 2–3 post effects max" | roblox-lighting | Unsourced, same `[UNVERIFIED]` status as our own light budget. Fine as craft, not as fact. |
| Mobile active particles 500–2,000; under 10 overlay draw calls | game-vfx (jeo) | Apple/Metal-derived, not Roblox. Our ch. 45 (≤250 mobile) and lihfolk (360 touch) are the relevant numbers. Ignore. |
| Hit-stop up to 250 ms on crits (gamedev-2d) vs "over 200 ms feels frozen" (polish) | 2D vs polish | Consistent with our ch. 45 ("over about 250 ms reads as a hitch"; prestige 150–220 ms). No change; note that 200–250 ms is reserved for the rarest moment. |
| Kao 2020 / CHI 2024 figures | gamestack | Quoted second-hand; verify the papers before citing in HIERARCHY. |
| better-sfx: "free, no credit" | better-sfx | True for use in a game, but the licence bans standalone redistribution. A public Roblox audio asset (Creator Store "Distribute") could count. Keep uploads private. |

---

## 4. Top 10 ranked additions

1. **A procedural SFX skill and toolchain** (`tools/sfx`: patch → render → doctor with LUFS/crest/centroid/harsh-band checks and a spectrogram PNG; foley pattern; per-asset LUFS ladder; category recipes; `SOUND_STYLE.md`). This is our biggest hole: we can mix and play sound but can't author or measure it. Source: game-sfx (MIT).
2. **Overlap-safe hit-stop and FeedbackDirector in Luau.** Per-ID deadlines, min multiplier over the external base scale, extend-never-cut, a cumulative cap per second, shorter stops on rapid repeats. Event-ID dedupe and per-100 ms event/particle budgets. Tier presets. Upgrades `vfx/examples/Impact.luau`. Sources: PixelWao orchestration, game-feel-polish (MIT).
3. **Roblox AnimationTrack hit-stop and marker sync:** token-based restore of each track's prior speed, catch-up mode, 0.2 s cap, charge retimed to land on `Hit`, sounds pre-rolled to their peak. Sources: lihfolk-vfx (CC-BY), roblox-animation (MIT).
4. **`impact(strength)` composite with thresholds** (flash over 0.25, aberration and zoom over 0.45), plus the tier table and the rule "raise contrast by lowering routine feedback". Source: game-feel-polish (MIT).
5. **Feel-trace auditor in lune**, with 12 violation codes and the 30/60/144 fps regression matrix, wired into `check_all.sh`. Source: game-feel-debugging-qa (MIT).
6. **New "Animation" section in ch. 45:** Animator-only loading, priorities, `Ended` vs `Stopped`, `WeightCurrent` settling, IKControl plus constraint limits, the "End" keyframe, ownership for replication, the `DelayTime` and `Completed`-on-cancel traps. Sources: roblox-animation, roblox-animation-vfx (MIT). Verify the LoadAnimation caching claim first.
7. **LihFolk production rules for combat VFX:** flash at 0.6× body, 1 frame after contact; three tones; frontal clamp; "escalate few layers"; budgets per preset; 900/360 live caps with the 75 % halving rule, 160/220-stud tiers, max 8 effects and a no-op handle; one light per effect. Source: lihfolk-vfx (CC-BY-4.0, credit required if text is reused).
8. **Server-validated VFX replication protocol and Server Authority effect rules:** token bucket 6/3 per s; one compact seeded payload within 250 studs; persistent states as attributes; predicted effects reversible; `IsResimulating` suppression. Sources: lihfolk-vfx, roblox-animation-vfx.
9. **UI juice spec sheet:** damage numbers (hold 30 % opaque, gravity arc, pool 64), counter roll formula, lag-bar ghost 0.25 s + 0.45 s, refusal two-sine shake 74/131 Hz, toast stack of 5, 60 ms menu stagger, 25 ms same-bank SFX dedupe with 24 voices stealing the oldest. Source: game-feel-polish (MIT).
10. **Evidence and accessibility upgrades:** the five-column VFX status (created / inspected / motion / export / integrated), the lifecycle case table with pending vs confirmed, `HapticEffect` with a haptics toggle, flash rules (≥20 % area at ≤3/s, no saturated red), a hit-stop toggle, the Kao inverted-U as the citation for "calm by default", and frame-indexed contact sheets for capture review. Sources: game-vfx (Ddrubok), game-vfx-workflow, juice-scan/apply, gamestack, 4k-vfx (idea).

Not worth taking: 4k-vfx (beyond the ffmpeg line), audio-sound-effects, game-sounds, game-2d-art pipeline, both Godot particle skills, the UE juice skill, glsl-shaders (AGPL), design-procedural-gen (GPL), roblox-lighting mood presets. Two of the 28 (editable-image, editable-mesh) are our own skills republished verbatim from the public aaa-kit repo.
