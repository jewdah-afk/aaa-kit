# Roblox Mastery Corpus

Total command of building things inside Roblox `EditableImage` and
`EditableMesh`, and of Roblox game development generally — written as a
knowledge base for porting a large incremental game to the platform.

**37,000+ lines across 20 chapters.** Every chapter was written by a dedicated
research agent against primary sources, with unverifiable claims marked
`[UNVERIFIED]` rather than guessed.

## Part I — The editable-asset core

| # | Chapter | Answers |
|---|---------|---------|
| 20 | [EditableImage API](20-roblox-editableimage-api.md) | Complete verified API, buffer layout, every display sink, the three failure gates |
| 21 | [EditableMesh API](21-roblox-editablemesh-api.md) | All 94 methods with thread-safety, the id-based model, does mutation live-update |
| 40 | [EditableImage cookbook](40-editableimage-technique-cookbook.md) | Painting, canvases, minimaps, filters, software rendering, texture synthesis |
| 41 | [EditableMesh cookbook](41-editablemesh-technique-cookbook.md) | Deformation, destruction, voxels, slicing, procedural objects, debug draw |

## Part II — Engine mastery

| # | Chapter | Answers |
|---|---------|---------|
| 22 | [Luau performance](22-luau-performance-engineering.md) | buffers, native codegen, what is actually parallel-safe, profiling |
| 23 | [Rendering & materials](23-roblox-rendering-lighting-materials.md) | Art direction without shaders, runtime PBR, lighting recipes |
| 43 | [3D math toolkit](43-roblox-3d-math-toolkit.md) | CFrame algebra, quaternions, splines, springs, geometry queries |
| 49 | [AI & NPC behavior](49-roblox-ai-and-npc-behavior.md) | Pathfinding, behavior trees, utility AI, crowds at scale |

## Part III — Craft

| # | Chapter | Answers |
|---|---------|---------|
| 42 | Genre atlas (kept in the research-calculator repo: it surveys other games by name) | What each genre demands; where the white space is |
| 46 | [Code architecture](46-roblox-code-architecture-and-frameworks.md) | Framework comparison, project structure, testing |
| 47 | [Security & anti-exploit](47-roblox-security-and-anti-exploit.md) | Threat model, server authority, information leakage |
| 48 | [Procedural generation](48-procedural-generation-toolkit.md) | Dungeons, WFC, erosion, L-systems, loot, solvability |
| 51 | [Live ops & growth](51-roblox-liveops-analytics-and-growth.md) | Discovery, funnel metrics, monetization, the honest picture |
| 31 | [Prior art & benchmarks](31-roblox-prior-art-and-benchmarks.md) | What exists already, reusable libraries, measured numbers |

## Part IV — The incremental-game port

| # | Chapter | Answers |
|---|---------|---------|
| 60 | [Big numbers & AlyaNum](60-luau-bignum-and-alyanum.md) | The magnitude ladder, library comparison, serialization, formatting |
| 61 | [Incremental architecture](61-incremental-game-architecture-roblox.md) | The tick loop, closed-form offline progress, multiplier stacking, persistence |
| 62 | [JS → Luau port method](62-js-to-luau-port-methodology.md) | Semantic gotchas, DOM→GUI mapping, equivalence testing |
| 63 | [Incremental UI](63-incremental-game-ui-roblox.md) | Number formatting, virtualized lists, the screens, mobile |
| 64 | [QA & verification](64-qa-and-verification-methodology.md) | Golden-master testing, property tests, CI, the review rubric |
| 65 | [Adversarial QA loops](65-adversarial-qa-loops.md) | Critic agents, staged gauntlets, what the evidence supports |

## Part V — Hierarchy science

Why HIERARCHY.md works, with the perception, timing and audio research behind each rule, and the numbers to measure it. Tool: [`tools/hierarchy`](../../tools/hierarchy/README.md). Skill: [`hierarchy-audit`](../../.claude/skills/hierarchy-audit/SKILL.md).

| # | Chapter | Answers |
|---|---------|---------|
| 70 | [HUD hierarchy survey](70-game-hud-hierarchy.md) | How strategy HUDs and Roblox lobbies rank information; touch and thumb zones |
| 80 | [Attention and salience](80-attention-and-salience.md) | Pre-attentive features, salience maps, onsets and looming, inhibition of return, the attentional blink, crowding, inattentional and change blindness |
| 81 | [Contrast, colour, colour blindness](81-contrast-colour-and-colour-blindness.md) | APCA Lc floors, OKLab, the Machado CVD model, the WCAG flash limit |
| 82 | [Time, motion and cue timing](82-time-motion-and-cue-timing.md) | The response chain, the telegraph budget, spacing cues, motion per tier |
| 83 | [Audio hierarchy](83-audio-hierarchy.md) | Priority, ducking (AudioCompressor sidechain), masking, loudness targets, tiers as buses |
| 84 | [Grouping, density and choice](84-grouping-density-and-choice.md) | Common region, about four chunks, Hick and Fitts, touch targets, clutter |
| 85 | [Measuring hierarchy](85-measuring-hierarchy.md) | The auditor's checks and thresholds, how the model fails, validating with people |

## Part VI — Asset packs

| # | Chapter | Answers |
|---|---------|---------|
| 90 | [Stud Voxel in Studio](90-stud-voxel-in-studio.md) | Three routes from a brick grid into Studio, the lune-tested Parts route, measured box counts, and the ranked upgrade plan |
| 91 | [Readable voxel surfaces](91-readable-voxel-surfaces.md) | How overlap, lip shadow and value bands make armour, scales and fur read; headless surface measures; the surface types in the 17 models |

## Method

`create.roblox.com`, `devforum.roblox.com` and `luau.org` are unreachable from
this environment. Claims were verified against the authoritative upstreams
instead, which are reachable and higher-fidelity than the rendered pages:

- **`Roblox/creator-docs`** — the generated reference YAML the Creator Hub is
  built from. Carries full signatures, defaults and thread-safety metadata.
- **`MaximumADHD/Roblox-Client-Tracker`** — the live engine reflection dump,
  used to confirm security levels and catch undocumented members.
- **`luau-lang/luau`** — VM source and RFCs.

DevForum was reachable only through search summaries; every such figure is
flagged `[COMMUNITY, SECOND-HAND]`. Treat community performance numbers as
unmeasured until reproduced in-engine.
