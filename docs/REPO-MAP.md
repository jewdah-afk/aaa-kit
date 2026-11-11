# Repo map

Which repo does what, and where new work goes.

```
                aaa-kit  (hub: hierarchy, framework, lexicon, skills, examples, tools)
               /    |     \            \
  cursed-survivors  ObsidianVault  research-calculator  WNGU
       (game)         (lab)            (lab)            (lab)
```

| Repo | Tier | What it is | Language / engine | Go here for |
|---|---|---|---|---|
| [aaa-kit](https://github.com/jewdah-afk/aaa-kit) | Hub | Shared knowledge and the single source of truth | Markdown, Luau, JS | Rules, skills, vocabulary, the framework starter, checkers |
| [cursed-survivors](https://github.com/jewdah-afk/cursed-survivors) | Game | 2D survivors-genre game drawn into one EditableImage per frame (480×270 hard pixels) | Luau / Roblox (Rojo, Lune, Selene) | The reference EditableImage renderer, owner buffer, intensity ladder, render goldens, a large before/after look archive |
| [ObsidianVault](https://github.com/jewdah-afk/ObsidianVault) | Lab | Research notes, a 57-chapter algorithm compendium, 1,361 idea cards, 60+ offline HTML labs | Markdown, HTML/JS/WebGL | Deep research before building; the original labs behind the skills |
| [research-calculator](https://github.com/jewdah-afk/research-calculator) | Lab | Prototype bench: 30+ branches of incremental, tower, map, icon-pipeline and EditableImage/EditableMesh experiments | HTML/JS, Luau, Python + Blender | Old prototypes. Its calculator and big-number library moved here ([tools/research-calculator](../tools/research-calculator/index.html), [examples/bignum](../examples/bignum/README.md)) |
| [WNGU](https://github.com/jewdah-afk/WNGU) | Lab | "Genesis": web game-system experiments (factory sim, genome raster, falling-sand racer) on branch `claude/project-genesis-…` | HTML/JS (canvas) | Web prototypes of simulation systems |

## Where new work goes

| You are making | Put it in |
|---|---|
| A rule, term or procedure every game should follow | aaa-kit (`HIERARCHY.md`, `lexicon.json`, a skill) |
| A small runnable demo of a technique | aaa-kit `examples/` |
| A new game | Its own repo, started from `examples/framework-starter`, with a `CLAUDE.md` that links here |
| Research or an idea not ready to build | ObsidianVault (`Library/Ideas`, a research series) |
| A throwaway prototype | A branch in research-calculator, or a new lab repo |

## Every repo links back

Each repo's README ends with a link to this hub, and its `CLAUDE.md` starts with the amplifier block from the hub's `CLAUDE.md`.
