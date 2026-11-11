# Audio hierarchy

Part V, Hierarchy science. Sound has the same job as the picture: one thing owns the moment, everything else steps back. This chapter maps the loudness tiers onto a mix. The Roblox mixer code is in [chapter 45 §8](45-roblox-vfx-audio-and-game-feel.md#81-soundservice-and-soundgroups--build-the-mixer-first) and the event system in the [UI motion and sound playbook](../playbooks/ui-motion-and-sound.md).

## Takeaway

**Priority, then ducking, then frequency.** Decide what must always be heard. Duck everything below it a few dB while it plays. Keep each class in its own frequency band so nothing masks it. Hold the whole mix to a loudness target, so "loud" means something.

## 1. Findings

- **Priority lists and voice stealing.** Common practice is to write down what must always be heard (dialogue first, then gameplay-critical cues, then ambience and music) and to let **voice stealing** stop lower-priority sounds when the voice limit is reached. ([audio clarity guide, MCV/Audiokinetic](https://mcvuk.com/development-news/audio-guide-side-chaining-in-wwise/); [Wwise HDR](https://www.audiokinetic.com/en/blog/wwise-hdr-overview-and-best-practices-for-game-mixing))
- **Ducking / side-chaining.** A compressor on the music bus, keyed by the dialogue bus, dips music and ambience **a few dB with a quick attack and gentle release** while the key plays. ([MCV/Audiokinetic](https://mcvuk.com/?p=121596))
- **Roblox supports this natively** in the new audio API. `AudioCompressor` has **Input** and **Sidechain** pins (wired with `Wire.TargetName`). When the Sidechain pin is wired, the Threshold "analyzes those streams instead of the Input streams", which "can be used to duck the volume of one stream in response to another". Ranges: Attack 0.0001–0.5 s, Release 0.01–5 s, Ratio 1–50, Threshold −60–0 dB, MakeupGain ±30 dB. ([AudioCompressor.yaml](https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/AudioCompressor.yaml)) The classic `SoundGroup` tree ducks by tweening `Volume` ([ch. 45 §8](45-roblox-vfx-audio-and-game-feel.md#81-soundservice-and-soundgroups--build-the-mixer-first)).
- **Masking.** Two sounds within about one **critical band** of each other mask each other. The bands widen with frequency (about 24 across hearing), and low frequencies mask high ones more easily than the reverse. ([Siemens, auditory masking](https://community.sw.siemens.com/articles/en_US/Knowledge/masking); [FabFilter, frequency and loudness](https://www.fabfilter.com/learn/science-of-sound/perception-of-frequency-and-loudness)) The ear is most sensitive at about **2–5 kHz** (the equal-loudness contours, ISO 226), so cues there cut through at lower levels.
- **Loudness targets.** Sony's ASWG-R001 (2013, quoted by secondary sources) sets **−24 LKFS ±2 for home console and −18 LKFS ±2 for portable**, true peak −1 dBTP. An ITU-R report cites the same working-document values. GANG's reference puts mobile at −16 LUFS. Wwise normalises to −23 LUFS by default, the EBU R128 broadcast target. ([ITU-R BS.2434](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BS.2434-2018-PDF-E.pdf); [GANG IESD mix reference](https://www.audiogang.org/wp-content/uploads/2015/04/IESD-Mix-Ref-Levels-v03.02.pdf)) Roblox publishes no loudness target. **UNKNOWN; we use the portable value, since most players are on phones.**

## 2. The loudness tiers as a mix

| Tier | Bus | Priority | Ducks | Band it owns (house) | Voice limit (house) |
|---|---|---|---|---|---|
| 1 Moments | `Ceremony` | 1 | everything else −8 dB, music −10 dB | full band, one hero sound | 2 |
| 2 Combat | `Threat` (incoming), `Impact` (outgoing) | 2 / 3 | ambience −4 dB on boss rung | threat 2–5 kHz transient; impact 80–250 Hz body + 2–4 kHz click | 8 / 12 |
| 3 HUD | `UI` | 4 | nothing | 1–4 kHz short ticks; never sub-bass | 4 |
| 4 World | `Ambience` | 6 | — | low-passed above ~6 kHz, no transients | 6 |
| 5 Materials | `Foley` (pickups, sheen) | 5 | — | 3–8 kHz sparkle, short | 6 |
| 6 Engines | `Bed` | 7 | — | pad, filtered | 2 |
| — | `Music` | 8 | by Ceremony, Threat on surge | below 2 kHz when combat is on | — |

Rules:
1. **Incoming threats outrank outgoing impacts.** A hit you're about to take matters more than one you dealt. This is HIERARCHY §8 ("urgency beats rarity") in sound.
2. **The intensity ladder drives the mix.** Calm: music full, ambience full. Surge: music low-passed and −3 dB, ambience off. Boss: Threat bus +2 dB. Ceremony: everything ducks under the reveal. One `Intensity.budget(level)` read sets all the bus targets.
3. **One hero sound per moment.** Layer it from 2–3 parts (transient, body, tail; see the [motion and sound playbook](../playbooks/ui-motion-and-sound.md)) but play one event.
4. **Carve, don't boost.** If a cue is buried, cut the masker's band (subtractive EQ, or `AudioEqualizer` on its bus) before raising the cue.
5. **Repetition fatigue counts as loudness.** Vary pitch ±3–5% and pick between 3+ variants. Rate-limit identical cues to one per 50–80 ms per bus (house).
6. **Never use sound alone for critical information.** Many players play muted. Every audio cue has a visual twin, and every critical visual cue gains a sound in the surge rung.

## 3. Measuring

- `Sound.PlaybackLoudness` gives a live level per sound. The perf overlay can log the maximum per bus per second.
- Before release, record 60 s of calm, surge and ceremony gameplay and measure integrated loudness and true peak with any EBU R128 meter. Targets: integrated −18 ±2 LUFS, true peak ≤ −1 dBTP, and **ceremony at least 4 LU above calm**, so the moment is louder than the baseline (house).

## 4. Gaps

- No research on audio hierarchy specific to Roblox or to kids was found.
- The band assignments and duck amounts are house starting points from mixing practice, not measured optima.
- We haven't verified the ASWG-R001 text itself; the figures above rest on two secondary sources that agree.
