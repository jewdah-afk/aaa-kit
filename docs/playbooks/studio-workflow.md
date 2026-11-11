# Studio workflow

How we worked with Roblox Studio from files, including with Claude driving it.

## Rules

- **The repo is the source.** A change made only in Studio is lost on the next `rojo build`.
- **Our own test place, one Studio window per project.** Never test in the owner's live place or another project's place. Name the dev place clearly (`<Game>_dev.rbxl`) and rebuild it from the repo.
- **Build and deliver:** `rojo build -o <Game>.rbxl` (or `rojo serve` + the Studio plugin). Copy the fresh build to the Desktop for the owner.
- **Play test with zero errors** in both the server and client output before calling anything done. Then replay remotes with bad arguments and confirm the server refuses them.

## Fast sync without a rebuild

When a full rebuild is too slow, push edited files straight into the open place:

1. Serve a copy of `src/` locally: `python -m http.server 8765 --bind 127.0.0.1`.
2. In the Edit DataModel, set `HttpService.HttpEnabled = true`, `GetAsync` each file into its script's `.Source`, then set `HttpEnabled` back.
3. Keep the sync snippet in `tools/sync.luau` so every session runs the same thing.

## Claude + Studio (Studio MCP)

- The owner enables the Studio MCP in the right Studio window. `list_roblox_studios` shows which places are connected; if only another project's place appears, stop and ask.
- **Uploads go one image at a time:**
  - Serve the folder: `python -m http.server --directory art/out`.
  - `upload_image` each file, inspecting it first.
  - Roblox downscales anything over 1024 px.
  - Kid-safe content only; a bad upload can get the account warned.
- Screenshot every visual change before and after.

## Dev tooling that paid for itself

| Tool | What it did |
|---|---|
| **Dev saves** | REGULAR (the real save), MAXED (everything unlocked and maxed), NEXT AREA (works on a copy and steps forward one unlock). Sandbox states never save. Only Studio, the owner or listed dev user ids can use them. |
| **Debug commands** | One invoke endpoint (`PlayerGui.<Game>.Debug:Invoke(cmd, arg)`) with `max`, `offer`, `stress N`, `pause`, `perf`, `profile`, `overlay`, `die`, `tp`, `zoom`. |
| **Debug attributes** | State exposed as PlayerGui attributes (`<Game>Open = "shop:UPGRADES"`, `<Game>Prompt`, `<Game>Moment`) so a script or Claude can read and set UI state. |
| **QA globals** | `_G.__uiKeys()` lists every live key with its press-in and sound; `_G.__vfx(name, rarity)` plays an effect. |
| **Overlays** | F3 = perf overlay, F4 = a scripted late-game profile (owner/Studio only). |
| **Dev sound board** | Audition and pick sounds in game (see [UI motion and sound](ui-motion-and-sound.md)). |

## Checks before a Studio session

- `rojo build` succeeds.
- `lune run tools/check_luau.luau src` → 0 failed.
- `luau-lsp analyze` is clean on what changed.
- The headless suites pass (`tests/all.sh`).
- Studio is the last check, not the first.
