# bignum

`EternityNum.luau` stores numbers past 1e308 as `{sign, layer, mag}` (up to towers like 1e1e1e500), with break_eternity.js maths, closed-form buy-all helpers, HUD suffixes, lossless save strings and an order-preserving leaderboard encoder. It came over from the research-calculator repo.

## Quick start

```sh
lune run examples/bignum/test.luau   # 13 checks
```

```lua
local EN = require("./EternityNum")
local coins = EN.add("1e400", EN.mul(5, "1e399"))   -- 1.5e400
print(EN.short(coins))                               -- HUD string
local n = EN.geomAfford(coins, 10, 1.15, 0)          -- how many levels you can buy, O(1)
local save = EN.toString(coins)                      -- store as a string, read back with EN.fromSave
```

## Rules

- Store big numbers as strings (`EN.toString`) in saves. Never compare strings with `>`.
- Use plain numbers below 9e15. The module's fast paths do this automatically.
- Use `EN.lbencode` for OrderedDataStore leaderboards (it preserves order).

See the [game-economy skill](../../.claude/skills/game-economy/SKILL.md).

## Credits

The algorithms port [break_eternity.js](https://github.com/Patashu/break_eternity.js) (MIT, Patashu).
