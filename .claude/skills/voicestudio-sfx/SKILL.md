---
name: voicestudio-sfx
description: Use when a game needs original sound effects or voice lines made locally with VoiceStudio (the open-source, on-device ElevenLabs alternative) - text-to-SFX for clicks, coins, whooshes, hits, chest opens, level-ups, ambience and loops, NPC or announcer voice lines, batch renders with seeds and variants, loudness by hierarchy tier, OGG for Roblox upload. Triggers on "sound effect", "sfx", "generate a sound", "voice line", "voicestudio", "elevenlabs alternative", "make audio for".
---

# voicestudio-sfx

Original audio, made on your own machine, mixed by the same hierarchy as the picture. [VoiceStudio](https://github.com/debpalash/voicestudio) does the generating; this skill decides what to ask for, how loud it may be and how it gets into the game.

## When to use

- Sound effects for UI, pickups, combat, rewards, ambience and loops
- Voice lines for NPCs, announcers and tutorials
- Re-rendering a whole sound list reproducibly (same prompt + seed = same take)

**Not for:** wiring sounds into Roblox `SoundGroup`s and the event system (see the [UI motion and sound playbook](../../../docs/playbooks/ui-motion-and-sound.md)), or music.

## Method

1. **Install once.** VoiceStudio desktop from its releases page. Sound effects are opt-in: **Tools → Sound effects → Install** (MOSS-SoundEffect v2.0, Apache-2.0 weights, ~11 GB download, ~22 GB disk). **NVIDIA GPU only, about 11 GB of VRAM**; the page says why when a host can't run it. Voice lines use the default engine and run on far less.
2. **Write the list, not one-offs.** Copy `examples/sounds.json`: one entry per sound with `id`, `tier` (loudness tier from HIERARCHY.md), `duration` (1–30 s), `seed` and `variants`.
3. **Prompt like a sound designer:** the source, the action, the size, the space, and what to leave out. "a bright metallic coin pickup chime, one short sparkle, dry, no music". Always add "no music", "no voice" or "dry" when you don't want them; the model fills silence otherwise. English (or Chinese), 500 characters at most.
4. **Render:** `python examples/vs_client.py batch examples/sounds.json out/ --ogg`. It checks every entry first, refuses durations outside 1–30 s and prompts over 500 characters, then writes `out/<id>.wav`, a tier-normalised `out/<id>.ogg` and `out/manifest.json` (prompt, seed, timings).
5. **Variants:** use 3+ takes for anything that repeats (clicks, hits, footsteps). `variants: 3` renders seeds `seed`, `seed+1`, `seed+2`.
6. **Listen, keep, re-roll.** A bad take gets a new seed or a sharper prompt; the manifest keeps the winning seed, so the sound can be remade exactly.
7. **Voice lines:** connect VoiceStudio's MCP server (`http://127.0.0.1:3900/mcp/`, exported for Claude Code under the app's **Integrations**) and use `design_voice` + `generate_speech`. Set `OMNIVOICE_MCP_OUTPUT_MODE=files` so audio goes to disk, not into the conversation.
8. **Upload** the `.ogg` files to Roblox (Creator Hub or Asset Manager), then wire them into the sound buses.

## Hierarchy rules it obeys

- [Audio hierarchy](../../../docs/research/83-audio-hierarchy.md): the loudness tiers map onto the mix. The client normalises each asset by its tier: 1 Moments −14 LUFS, 2 Combat −16, 3 HUD −20, 4–5 World −24, 6 Engines −26, true peak −1 dBTP. These are house values under the −18 LUFS mix target from that chapter.
- One hero sound per moment. Ceremony sounds (tier 1) are full-band and rare; everything else ducks under them.
- Repetition is loudness: 3+ variants and ±3–5% pitch for anything that repeats.
- Threat cues live in 2–5 kHz and outrank loot (ch. 83 §2).

## Engine notes

**VoiceStudio.**

- The backend listens on `http://127.0.0.1:3900`, loopback-only with no key by default. Sound effects: `GET /api/sfx/status`, `POST /api/sfx/generate` `{prompt, duration, seed?}` → `{id, audio_url, duration_s, gen_time_s, seed, engine}`. `409` = not installed or unsupported host, `422` = duration out of range, `503` = GPU busy (retry).
- Output is mono 48 kHz WAV. Takes carry VoiceStudio's AI-generated audio mark when its watermark setting is on.
- VoiceStudio is AGPL-3.0. The kit only calls its local API and copies none of its code, so nothing here becomes AGPL.

**Roblox.**

- Upload `.ogg` or `.mp3`. Each upload is moderated, and you must own the rights: these are your own generations; never clone a real person's voice without their consent.
- Play through `SoundGroup`s per bus (or the new audio API's `AudioCompressor` sidechain to duck), as in [ch. 45 §8](../../../docs/research/45-roblox-vfx-audio-and-game-feel.md).

## Example

`examples/vs_client.py` is the client (Python standard library, ffmpeg only for `--ogg`). `examples/sounds.json` is a starter list: UI click, coin pickup, sword whoosh, hit, chest open, level-up, forest ambience, waterfall loop. `examples/test_vs_client.py` runs the client against a mock backend with the real routes and status codes (17 checks: limits, seeds, variants, manifest, missing engine, unreachable app).

```sh
python examples/vs_client.py status
python examples/vs_client.py one "a fast sword swing whoosh through the air, close, no impact" 1.5 out/whoosh.wav --seed 31
python examples/vs_client.py batch examples/sounds.json out/ --ogg
```

## Make it insane

1. **Sound from the picture:** every VFX recipe carries a one-line sound prompt next to its timing, so a new effect gets its matching sound rendered in the same batch, in the same tier.
2. **Material-aware impacts:** one prompt template × the surface materials in the map (wood, stone, metal, grass) renders a full impact matrix, so hits sound like what they hit.
3. **Seed ladders for rarity:** the same reveal prompt rendered with a rising "bigger, brighter, more sparkle" ladder gives each rarity its own sting, all from one family.

## Self-check

- [ ] Every sound has a tier, a seed and, if it repeats, 3+ variants.
- [ ] Prompts say what to leave out (music, voice, reverb).
- [ ] OGGs are loudness-normalised by tier; one hero sound per moment.
- [ ] The manifest is kept with the files, so any take can be remade.
- [ ] No cloned real voices without consent; uploads are your own generations.
