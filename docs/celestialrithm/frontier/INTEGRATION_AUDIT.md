# Integration audit (2026-11-12)

What came in, what overlapped, what conflicted, what's outdated, and what's missing. Read this before trusting any file under `docs/celestialrithm/`, `docs/algorithm-vault/` or `lib/celestialrithm/`.

## Inputs

| Input | What it is | Result |
|---|---|---|
| `AAA_KIT_CELESTIALRITHM_UNIVERSAL_UI_WORLD_PATCH_VERIFIED.zip` | 78 files: algorithm vault, Celestialrithm docs, Luau prototypes, offline renderers, the approved visual target GIF | Installed (75 files). The package's root `README.md` would have overwritten the kit's, so it lives at [PATCH_README.md](../PATCH_README.md). `MANIFEST.json` and `install_into_aaa_kit.py` were not committed: the manifest's hashes describe the zip, not the repo. |
| `AAA_Algorithm_Vault_CORE_mobile.zip` | 17 files | **Exact duplicate**: all 13 shared files are byte-identical (SHA-256) to the patch's copies, and its `CLAUDE_VAULT_ADDENDUM.md` equals `docs/celestialrithm/CLAUDE_VAULT_ADDENDUM.md`. Nothing extra to install; its `qa/LOCAL_QA.md` is summarised below. |
| `LihFolk-Stud-Voxel-SOURCE-LITE.zip` | 71 files: skill docs, Blender build scripts, Luau builder/animator, example scripts, rig JSON | Installed as a Claude skill at `~/.claude/skills/lihfolk-stud-voxel/`. **Not committed to this repo** (see Licences). |
| ObsidianVault | Private knowledge vault | Checked: no Celestialrithm, LihFolk or Algorithm Vault notes exist there. Related sources: `Cursed Survivors/Research/Render Deep Dive`, `UI FX Stack`, `Algorithm Compendium`. |

## Duplicates and conflicts

| Item | Finding | Decision |
|---|---|---|
| Vault CORE zip vs patch | 13/13 files identical | Install once |
| Patch `README.md` vs kit `README.md` | Path conflict; the installer refuses | Moved to `docs/celestialrithm/PATCH_README.md` |
| `recipes.jsonl` (7.5 MB), `vault.sqlite` (6–9 MB), `ui_recipe_catalog.jsonl` (10.6 MB) | Generated, and rebuilt byte-identical by their builders (checked by hash) | Git-ignored; `tools/check_all.sh` rebuilds them before testing |
| `lib/celestialrithm/MaterialField.luau` | A sum of 2–3 sine waves per material: the "single-frequency sine" look the brief rules out | Kept as legacy. Superseded by `tools/celestialrithm/foundry/` (reference) and the Luau ports in `lib/celestialrithm/materials/` |
| `examples/celestialrithm/t11/`, `flat-reactor/` | Earlier engineering experiments; the patch marks flat-reactor historical | Kept as history; not the visual bar |
| `CLAUDE_VAULT_ADDENDUM.md` | Mentions `repo_discovery.jsonl`, which doesn't exist until `tools/algorithm_vault/ingest_repo.py .` runs | Not pasted into `CLAUDE.md`; routing is in the frontier README instead |
| Patch status lines ("NOT PUSHED", "GitHub 403") | True when packaged, stale now | Left in place as history; this branch is the push |

## Dependencies

| Need | Status here | How |
|---|---|---|
| Blender | **Installed**: Blender 5.3 as the `bpy` Python module (PyPI) plus Mesa software EGL for headless EEVEE | `pip install bpy`; `apt-get install libegl1 libegl-mesa0 libgl1-mesa-dri` |
| Python, NumPy, Pillow | Installed (3.13, 2.5, 12.3) | — |
| lune 0.10.5, selene 0.31.0 | Installed from the projects' GitHub releases (versions from `rokit.toml`) | `rokit install` on a dev PC |
| selene Roblox std | Not downloaded (needs network once) | `check_all.sh` skips with a message, as before |
| OpenCV (`cv2`) | **Missing**: `examples/celestialrithm/t11/render.py` and `qa.py` import it | `pip install opencv-python` if those legacy scripts are needed; the foundry doesn't use it |
| FFmpeg / ffprobe | Installed | — |
| Roblox Studio | **Not available** in this environment | Studio rungs (C–E of the proof ladder) are not run |

## LihFolk Source-Lite: what's missing

The full pack's description promises 45+ examples with concept sheets, previews and full build files. The Source-Lite archive has the scripts but not the reference material.

| Missing | Effect (tested) |
|---|---|
| `examples/concepts/`, `concepts/style_refs/` | `scripts/compare.py` has nothing to compare against; builds still run |
| `examples/previews/` (the "approved looks") | No visual bar for the pack's own models |
| `examples/brick/refs/*.npz` | Traced weapons fail: `props_brick.py -- Pistol` raises `FileNotFoundError: refs/Pistol.npz` |
| `out_*/` GLBs and renders (only `*_rig.json` present) | Must be rebuilt locally |

Verified working: the INSTALL test (`props_brick.py -- render Oak` prints `RIG_OK`, writes `Oak_tex.png`) and a boss build (`war_rhino_brick.py`: `RIG_OK`, 15 bones, 27,026 tris). The `.ps1` runners are Windows-only; on Linux run the example with `python3 <file>.py -- render` (bpy) or `blender -b --factory-startup --python <file> -- render`.

## Licences

| Material | Licence found | Use here |
|---|---|---|
| LihFolk Stud Voxel Pack | **None** (no LICENSE file in the archive) | Studied and run locally only. Its techniques (SDF sculpting, greedy meshing, world-aligned stud UVs, flood-fill cleanup, per-bone splitting) are reimplemented from first principles in `tools/celestialrithm/geometry/` and `lib/celestialrithm/geometry/`. No LihFolk code, textures or renders are committed. Ask the author before copying anything. |
| APCA (used by `hierarchy-audit`) | The `apca-w3` licence limits it to WCAG web content | Flagged by the research registry; review before shipping APCA inside a game |
| External methods | Recorded per entry | [external/README.md](../../algorithm-vault/external/README.md) |
