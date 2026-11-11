# Framework starter

A tiny tap-to-earn loop built on the kit's five-layer framework. Copy this folder to start a new Roblox game. Read [docs/FRAMEWORK.md](../../docs/FRAMEWORK.md) for the rules behind it.

## Quick start

```sh
rojo build examples/framework-starter -o Starter.rbxl   # or `rojo serve` from this folder
lune run examples/framework-starter/tests/run.luau      # 48 headless checks
lune run tools/check_luau.luau examples/framework-starter # compile check
```

## Structure

```
src/
├── shared/                 → ReplicatedStorage.Shared
│   ├── Kit/                hub: Maid, Signal, Guard, Format, Registry
│   ├── Content/            data: Upgrades, Unlocks, ResetLayers
│   └── Systems/            pure: Save, Economy, Automations, Unlocks, Reset, Intensity
├── server/                 → ServerScriptService.Server
│   ├── init.server.luau    boot: registry, players, one Heartbeat
│   └── Services/           DataService (session-locked saves), EconomyService (validated remotes)
└── client/                 → StarterPlayerScripts.Client
    ├── init.client.luau    boot: state signal, bind components
    └── Components/         CoinCounter (tag "CoinCounter", odometer count-up)
tests/run.luau              lune tests for every pure module
```

Modules use string requires (`require("./Save")`, `require("@self/Maid")`), so the same file runs in Roblox and in lune.

## Make it yours

1. Add rows to `Content/Upgrades.luau`. That's the whole balance pass.
2. Add a save field to `Systems/Save.TEMPLATE`. Old saves pick it up automatically.
3. Add a per-second effect with `Automations:add`, not a new loop.
4. Tag a TextLabel `CoinCounter` in Studio to see the counter roll.

## Status

The pure modules are tested headlessly. The services and components compile-check but haven't been play-tested in Studio from this repo.
