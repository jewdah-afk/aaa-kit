# tier-sim

A headless lune simulation of an escalation game prototype: seeded level grammar, obstacle certification, a 120 Hz controller, escalation tiers, a sensory-load budget, and death/rebirth. Each tier's visual load is checked against luminance bands (see `tiers.json`), so it doubles as an example of testing the [intensity ladder](../../HIERARCHY.md#4-the-intensity-ladder) and the [figure-ground gate](../../HIERARCHY.md#11-figure-ground-gate) in code.

```sh
lune run examples/tier-sim/sim.luau     # runs the sim; results go to out.json
```

`index.html` and `level.html` render the last run (open them in a browser). The `*.tpl.html` files are the templates they're built from.
