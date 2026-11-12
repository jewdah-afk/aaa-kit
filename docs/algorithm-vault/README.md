# AAA-KIT — Algorithm Vault (review package, v1)

**Purpose:** Make repo-owned algorithms, outside research, and new T12–T14+ experiments *findable and testable* by Claude, without losing the Stud UI art direction.

## What exists here

| Artifact | What it actually contains | Status |
| --- | --- | --- |
| `primitives.json` | **156 manually curated technique/method-family entries**, with names, roles and source links | Research index. Some are close relatives; not 156 novel discoveries |
| `sources.json` | 11 source families including repo, uploaded voxel pack, and external research | Bibliography, not copied third-party code |
| `recipes.jsonl` | **12,000 generated algorithm combinations** with deterministic IDs, stages, style constraints, target hardware and QA guard | **UNTESTED** design candidates, not 12,000 implementations |
| `vault.sqlite` | Searchable SQLite recipe and primitive tables + FTS index | Generated and local-tested |
| `repo_manifest.json` | 24 verified `aaa-kit` source paths for integration | Partial index, not a clone |
| `tools/algorithm_vault/ingest_repo.py` | Discovers Luau modules/functions, research headings, algorithm ideas, and lexicon terms in a real checkout | Fixture-tested; run in repo to ingest its current material |
| `examples/algorithm-vault/hydro_hero.py` | Standalone computed membrane/caustic Stud keycap render | Locally rendered MP4 + GIF; no Roblox execution claim |
| `tools/algorithm_vault/evolve.py` | Ranks candidates from **actual measurement CSVs** and rejects unqualified ones | Fixture-tested; requires measurements |

**Don't confuse research-method families, catalog entries, generated combinations and shipped algorithms.** They're four different inventory categories.

## Claude / agent instructions

1. Read `CLAUDE.md`, `README.md`, `HIERARCHY.md`, `docs/playbooks/figma-to-roblox-ui.md`, the EditableImage/Mesh skills, and the existing `lib/frontier` code before choosing a technique.
2. Search the method index before creating a new algorithm. If it exists, reuse or extend the actual implementation, not an untested recipe.
3. Query `vault.sqlite` via `python tools/algorithm_vault/query.py caustic --limit 10` or `--method` to search method names. Generated recipes should always be labeled **candidate**.
4. For every candidate, specify data dependencies, visual style contract, performance class, and literal source paths. Don't copy external source until its license is checked.
5. Implement one candidate as a pure Luau module (or a source-backed CPU/Web offline reference) with engine adapter isolated.
6. Run headless tests, material closeup, calm/press/rebound, full HUD view, screenshot hierarchy auditor, CVD/contrast/flash checks, mobile quality ladder and **Studio performance**.
7. Write a measurement record. Only eligible measured candidates enter `evolve.py` and only human-approved passes become presets. **No AI auto-merge or auto-rewrite of shipped styles.**
8. Successful candidates go in `lib/frontier/ui` or a relevant specialized library, with a `.test.luau`, Studio probe, source citation and new `docs/algorithm-vault/presets/<name>.json`.

## Locked Stud UI contract

- Keep the **T11 Hydroglass / Prism Gel / Solar Plasma keycap quality and construction direction** as the *lower bound*, not the old unmodified Shop icon artwork.
- Exterior squared; the optical and soft-body sophistication is below/in the face, not a rounded app pill.
- 4 px near-black ink body; 2.5 px face/lip radii; 1.5 px top highlight; intact illustrated icon and legible text.
- Whole key moves down by its depth under press. No face-only sink under a stationary outline.
- One visual owner per HUD panel; one real primary CTA; don't apply glow to all buttons at rest.
- Existing color jobs, rarity ladder, pixel-owner and intensity rules win over any recipe.
- At rest: quiet. Hover: owned. Press: one coherent physical response. Resolve and settle to quiet.
- Audio is subordinate to critical gameplay cues; use voice priorities, ducking and reduced-motion alternatives.

## Working commands

```bash
# Run once when installed into a real checked-out aaa-kit repository
python3 tools/algorithm_vault/ingest_repo.py .
# Rebuild the reproducible candidate library and FTS index
python3 tools/algorithm_vault/build_vault.py
# Find a method (actual indexed method family)
python3 tools/algorithm_vault/query.py caustic --method
# Search generated candidate recipes for a stage/term
python3 tools/algorithm_vault/query.py hydroglass --style hydroglass --target phone-mid
# Produce a standalone offline reference without Roblox
python3 examples/algorithm-vault/hydro_hero.py
# Evaluate with REAL human/automated measurements; never guess scores
python3 tools/algorithm_vault/evolve.py measurements.csv --max-ms 2.0
# Mutate only measured winners, track every descendant and approval gate
python3 tools/algorithm_vault/mutate.py qa/evolution_report.json --per-parent 8
# Structural tests
python3 tools/algorithm_vault/test_vault.py
# Repo's existing full standard checks (inside the real repo)
bash tools/check_all.sh
```

### Measurement CSV format

`id,focus_lift,contrast_lc,frame_ms,flash_pass,human_rating,style_pass`

Use `frame_ms` only from device/Studio benchmark captures for production classification. `focus_lift`, APCA and flash checks come from the repo's `tools/hierarchy/hierarchy.py`; human_rating is from a reviewer (1–5). A fallback render is not a production pass.

## T12 → T14+ experimental evolution

**T12 Physical Coupling** — XPBD-ish deformation and shared optical field. Pressure input updates a fixed-topology membrane, normal field, caustics, moving under-face depth, SFX envelopes and stencil. Output: clean, recognizable, pressed keycap.

**T13 Material Memory** — Advection, Gray–Scott / Physarum patterns or hysteresis retain a *short-lived* interaction history, influencing subsequent flashes and shadows. Never deform UI labels. Automatically drains to an exact calm baseline.

**T14 Hierarchy-Guided Synthesis** — Generate multiple candidate material parameterizations, render each at true HUD scale, compute scanpath/contrast/flash metrics, measure runtime, and solicit human ranking. Optimize under constraints rather than maximize bloom. Use A/B lineage and rollback.

**T15+ (proposals, not shipped features)** — Perceptual temporal scheduling; material subgraph compilation; multi-resolution runtime texture budgets; vector-aware icon extrusion; learned quality-cost surrogate fit **only from real measured training data**. These are design hypotheses, not official tier definitions or Roblox APIs.

## Runtime feasibility

Roblox EditableImage display-side refresh is limited to one EditableImage per frame: reuse the existing `lib/frontier/Atlas.luau` and `Uploader.luau`, instead of creating an image per button. Fixed-size mesh edits should use `SetPosition`, dirty normals, and collision proxies. Editable-image and mesh creation can return nil. Always implement static image fallback, reduced-motion fallback and GPU/memory-safe downgrade.

Full library figures, rendering estimates and generated recipe `heuristic_ms` must NOT be called device measurements.

## Content and licensing

This vault links to external sources and paraphrases algorithm families; it does not vendor external code. The uploaded LihFolk pack had no explicit license identified in the previous inspection; keep it local-reference-only until permission is established. Repo `.md` content has CC BY-ND notice; this package references rather than modifies those docs. Keep the vault's novel implementation files separate.

## Repo write status

Built as a ready-to-merge folder. The GitHub connector refused branch creation with HTTP 403 (`Resource not accessible by integration`); **nothing has been pushed or merged**. Do not claim this directory exists in `main` until a successful commit is verified.
