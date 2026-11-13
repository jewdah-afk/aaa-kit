# hologram

A model as a **blueprint**: a fixed, mirrored set of 3D points taken from the same maths that builds the model, plus the transform that moves any pile of voxels into it, one voxel per slot.

| File | What it is |
|---|---|
| `Blueprint.luau` | Pure Luau: decode the slots, Morton-curve 1:1 assignment, source piles, per-slot progress and pose |
| `EmberDragonBlueprint.luau` | Generated data for the Ember Dragon: rig joints, bones, palette and the voxel slots |
| `qa/test_hologram.luau` | Headless checks (lune) |

See it running: [examples/web/dragon-hologram.html](../../examples/web/dragon-hologram.html) (hologram, points drawn over two renders of the model, build scrubber).

## What is in a blueprint

- **Anchors**: the rig's bone ends as named vertices, and the bones between them. Left and right joints are exact mirrors.
- **Slots**: one voxel per `cell` bricks on the model's shell, each with a palette colour and a baked top light. The -x half is the +x half reflected, so every slot has a twin. Slots are stored bottom-up, which is the build order.
- **Outline rings** (web page only): surface bricks on evenly spaced Z and Y planes plus the centre profile.
- **Views** (JSON only): the cameras of the pipeline's `rest_front` and `rest_34` renders, so the points can be drawn over those pictures.

Coordinates are bricks: x right, y up, z back (front = -z). Multiply by `studsPerBrick` (2.5) for studs.

## Make one

```sh
cd .claude/skills/lihfolk-stud-voxel
python3 scripts/blueprint.py examples/brick/ember_dragon_brick.py \
  --luau ../../../lib/hologram/EmberDragonBlueprint.luau \
  --html ../../../examples/web/dragon-hologram.html
```

It needs numpy only (no Blender): it runs the brick script's shape code and rig table and skips the renderer. The dragon's grid is 20 million bricks, so this takes about four minutes (add `--ring 12` for the outline spacing the page uses); `--cache grid.npz` saves the grid for later runs. `--cell` sets bricks per slot (4), `--ring` the spacing of the outline planes.

## The transform

1. Make a source pile with the same count as the slots (`Blueprint.pile`, `Blueprint.shell`, or your own positions).
2. `Blueprint.assign(src, slots)` sorts both along a Morton curve and pairs them in that order. Each slot gets exactly one voxel and neighbours stay neighbours, so the flight paths don't cross much.
3. `Blueprint.pose(out, src, slots, perm, t)` gives every voxel's position at time `t`. Slots start bottom-up; at `t = 1` every voxel is exactly on its slot (the tests check equality, not closeness).

## In Roblox

The module has no Roblox types. This adapter builds the hologram as ghost parts and then flies bricks into it:

```lua
local Blueprint = require(script.Parent.Blueprint)
local Data = require(script.Parent.EmberDragonBlueprint)

local bp = Blueprint.decode(Data)
local S = Data.studsPerBrick
local origin = CFrame.new(0, 0, 0) * CFrame.Angles(0, math.pi, 0) -- front = -z in brick coords

local function color(i: number): Color3
	local c, l = bp.color[i], if bp.glow[i] then 1 else 0.45 + 0.6 * bp.light[i]
	return Color3.fromRGB(math.min(255, (c // 65536) * l), math.min(255, (c // 256 % 256) * l), math.min(255, (c % 256) * l))
end

local src = Blueprint.pile(bp.count, bp.cell, 0, 0, 0)
local perm = Blueprint.assign(src, bp.pos)
local out = table.create(bp.count * 3, 0)
local parts = table.create(bp.count)
local cframes = table.create(bp.count)
for i = 1, bp.count do
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CastShadow = true, false, false
	p.Size = Vector3.one * bp.cell * S
	p.Color = color(i)
	p.Material = if bp.glow[i] then Enum.Material.Neon else Enum.Material.Plastic
	p.Parent = workspace
	parts[i] = p
end

local function step(t: number)
	Blueprint.pose(out, src, bp.pos, perm, t, { arc = 40 })
	for i = 1, bp.count do
		cframes[i] = origin * CFrame.new(out[i * 3 - 2] * S, out[i * 3 - 1] * S, out[i * 3] * S)
	end
	workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
end
step(0)
```

Drive `step(t)` from `RunService.Heartbeat` on the client. For the hologram look before the build, show the same parts at `t = 1` with `Material = ForceField` or `Neon`, one colour, high transparency. For a phone, raise `--cell` to 6 or 8 (fewer, bigger voxels) or build only the slots near the camera; several thousand moving parts is a desktop budget.

When the build finishes, swap the voxels for the real model (the skinned `.glb` from the brick pipeline) placed at the same origin: both come from the same grid, so they line up.

## Tests

```sh
cd lib/hologram/qa && lune run test_hologram.luau | grep -a '^@@'
```

Not tested here: the Roblox adapter above (it compiles; it has not been run in Studio) and frame time on a real phone.
