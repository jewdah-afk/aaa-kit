# Style

## Writing (every `.md`)

- **Plain and specific.** Write "the HUD shows coins at top-left in 28 px bold", not "the HUD is clean and readable".
- **Skimmable.** Headings, short paragraphs, tables for anything with two or more attributes, numbered steps for procedures.
- **No filler.** Avoid "it's worth noting", "simply", "robust", "seamless", "leverage", "powerful" and "comprehensive".
- **Numbers over adjectives.** "2-frame hit-stop, 6 px shake decaying over 120 ms" beats "punchy".
- **Mark what's unverified.** Write "start value, tune in play", "not measured on a phone" or "UNKNOWN — ask owner".
- **Generic names in public files.** Never name another studio's items, characters, stages or games in public material.

### Repo doc set (same headings, same order, in every repo)

`README.md`:

1. Title + one-sentence pitch
2. Screenshot or GIF
3. Quick start
4. Structure
5. Status
6. Links (hub, related repos)

`CLAUDE.md`:

1. The amplifier block (copied from the hub)
2. What this repo is (two lines)
3. Where things go
4. Rules (repo-specific; slip-ups turned into rules)
5. Checks before done

## Naming

| Thing | Style | Example |
|---|---|---|
| Repo, folder, skill | lowercase-hyphenated | `framework-starter`, `reward-moments` |
| Luau module file | PascalCase | `EconomyService.luau` |
| Luau locals and functions | camelCase | `maxAffordable`, `tapLimit` |
| Luau types | PascalCase | `export type Upgrade` |
| Constants | UPPER_SNAKE | `MAX_BUY`, `FALL_HOLD` |
| Content row ids | snake_case | `click_power`, `first_reset` |
| Tags (CollectionService) | PascalCase | `CoinCounter` |
| Remotes | Verb or noun, PascalCase | `Buy`, `Tap`, `State` |
| Lexicon terms | lowercase words | `hit-stop`, `figure-ground gate` |

## Code

**Luau**

- `--!strict` at the top of every file.
- Tabs for indentation. Format with StyLua (column width 120) if it's installed.
- Type every function's parameters and returns.
- String requires (`require("./X")`, `require("@self/X")`) for shared modules, so lune can run them.
- Pure logic lives in modules with no `game:GetService`, so it's testable headlessly.
- No `print` in hot paths. `warn` once per real failure.
- Every module ends with `return X`.

**JavaScript / HTML labs**

- Single-file pages with no build step. Use `const` by default.
- `requestAnimationFrame` with a clamped `dt` (cap at 1/20 s).
- Respect `prefers-reduced-motion`.
- Zero console errors on load (checked in headless Chromium).

## Commits

- One topic per commit. The message says what changed: `skills: add reward-moments`.
- Work on a branch and open a PR. Never force-push a shared branch.
