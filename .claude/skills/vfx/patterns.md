# VFX patterns: ❌ DO NOT vs ✅ DO

Open this file only when you are writing Instance code for an effect. The blueprint rules are in [SKILL.md](SKILL.md); the facts below come from the [VFX craft playbook](../../../docs/playbooks/vfx-craft.md) and, for the API detail, [research ch. 45](../../../docs/research/45-roblox-vfx-audio-and-game-feel.md) and [ch. 20](../../../docs/research/20-roblox-editableimage-api.md). Rules marked ⚙ are machine-checked by `Blueprint.validate` (`examples/Blueprint.luau`).

None of this has been play-tested in Studio from the authoring environment. Treat every number as a start value and tune in play.

## 1. Beam and Trail attachments

### 1.1 A Beam needs two parented attachments, an orientation, and to be parented last

❌ DO NOT:

```lua
local beam = Instance.new("Beam")
beam.Parent = workspace          -- live before it is configured: a frame of nothing, then a default ribbon
beam.Attachment0 = a0            -- Attachment1 never set: a Beam with one attachment draws nothing
beam.CurveSize0 = 4              -- the curve leaves along a default +X: it bulges "somewhere"
```

✅ DO:

```lua
local function arch(parent: BasePart, from: Vector3, to: Vector3, bulge: number): Beam
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = from, to
	a0.Axis = Vector3.yAxis -- the curve leaves A0 along its +X ...
	a1.Axis = -Vector3.yAxis -- ... and arrives along A1's -X: both point up, so the arc arches over
	a0.Parent, a1.Parent = parent, parent -- attachments first, and two different objects
	local beam = Instance.new("Beam")
	beam.Attachment0, beam.Attachment1 = a0, a1
	beam.CurveSize0, beam.CurveSize1 = bulge, bulge
	beam.Segments = 12
	beam.FaceCamera = true -- set it; a flat beam disappears edge-on
	beam.LightEmission, beam.LightInfluence = 1, 0
	beam.Parent = parent -- last: nothing renders half configured
	return beam
end
```

⚙ A Beam sets `Width0`, `Width1`, `FaceCamera`, `LightEmission` and `LightInfluence` explicitly.

### 1.2 Animate a Beam by its numbers, not by rebuilding it

❌ DO NOT destroy and recreate the beam each frame, or drag the attachments to fake motion.

✅ DO tween `CurveSize0/1` and `Width0/1`. It is cheaper and smoother, and the timeline starts the tween (section 4):

```lua
local TweenService = game:GetService("TweenService")
local function collapse(beam: Beam, frames: number)
	local info = TweenInfo.new(frames / 60, Enum.EasingStyle.Quart, Enum.EasingDirection.Out)
	TweenService:Create(beam, info, { CurveSize0 = 0, CurveSize1 = 0, Width0 = 0, Width1 = 0 }):Play()
end
```

### 1.3 A Trail is the gap between two attachments on the SAME moving part

❌ DO NOT:

```lua
local trail = Instance.new("Trail")
trail.Attachment0 = a0           -- one attachment: nothing renders
trail.Attachment1 = a0           -- or the same spot twice: a zero-width ribbon
-- Lifetime stays 2 s, MinLength 0, MaxLength 0: a crumpled knot when idle, an endless ribbon when fast
```

✅ DO:

```lua
local function addTrail(part: BasePart, width: number): Trail
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = Vector3.new(0, width / 2, 0), Vector3.new(0, -width / 2, 0) -- width = the gap
	a0.Parent, a1.Parent = part, part
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Lifetime = 0.3 -- snappy; the default 2 s smears
	trail.MinLength = 0.2 -- no new segments while idle or jittering
	trail.MaxLength = 12 -- the geometry budget, whatever the speed
	trail.FaceCamera = true
	trail.LightEmission, trail.LightInfluence = 1, 0
	trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0) })
	trail.Enabled = false -- on only after the part is placed (1.4)
	trail.Parent = part
	return trail
end
```

⚙ A Trail sets `Lifetime`, `MinLength`, `MaxLength`, `LightEmission` and `LightInfluence`.

### 1.4 Never move an enabled trail across the map

❌ DO NOT:

```lua
part.CFrame = spawnCFrame        -- the trail is on: it draws a streak from the old position to the new one
```

✅ DO:

```lua
local function relocate(part: BasePart, trail: Trail, cf: CFrame)
	trail.Enabled = false
	part.CFrame = cf
	trail:Clear() -- drop the old segments
	trail.Enabled = true
end
```

## 2. ParticleEmitter

### 2.1 Set the three dials every time

`LightEmission` is the blend mode (0 alpha, 1 additive). `LightInfluence` is whether world light shades the particle. `ZOffset` is the sort order in studs toward the camera. `LightInfluence` defaults to 1 for an emitter inserted in Studio and 0 for `Instance.new`, so an effect looks different depending on how it was made.

❌ DO NOT:

```lua
local e = Instance.new("ParticleEmitter")
e.Texture = id                   -- everything else is a default that differs by how the emitter was created
```

✅ DO (the ladder from the craft playbook, front to back):

```lua
local FIRE = { LightEmission = 1, LightInfluence = 0, Brightness = 3 }
local SMOKE = { LightEmission = 0, LightInfluence = 1, Brightness = 1 }
local Z = { core = 0.6, support = 0.2, spark = 0.1, smoke = -0.5 }

local function style(e: ParticleEmitter, look: { [string]: number }, z: number)
	for k, v in look do
		(e :: any)[k] = v
	end
	e.ZOffset = z -- set per emitter, never left at 0 for all of them
end
```

⚙ An Emitter sets `LightEmission`, `LightInfluence` and `ZOffset`. The Core emitter has the highest `ZOffset`; Dissipation smoke has the lowest.

### 2.2 Dark colours vanish under additive blending

❌ DO NOT: black or deep-violet smoke with `LightEmission = 1`. Additive black adds nothing, so the smoke is invisible.

✅ DO: smoke, dust and debris use `LightEmission = 0` (and `LightInfluence` near 1). Additive is for fire, sparks and magic, and those colours stay bright.

⚙ A layer with `LightEmission >= 0.5` needs a colour with luma >= 0.25. Dissipation includes smoke with `LightEmission = 0`.

### 2.3 Bursts: Rate 0 and Emit, then clean up after the last particle

❌ DO NOT:

```lua
e.Enabled = true; e.Rate = 50
task.wait(0.1)                   -- the burst size depends on the frame rate and the scheduler
e.Enabled = false
host:Destroy()                   -- kills every live particle mid-flight
```

✅ DO:

```lua
local Debris = game:GetService("Debris")
local function burst(e: ParticleEmitter, host: BasePart, count: number, maxLifetime: number)
	e.Rate = 0 -- stays enabled; only :Emit makes particles
	e:Emit(count) -- an exact count, on this frame
	Debris:AddItem(host, maxLifetime + 0.5) -- after the last particle has faded
end
```

When an effect is reused, call `e:Clear()` before moving it so old particles don't smear across the world.

### 2.4 Budget by overdraw, and scale by the rung

❌ DO NOT hard-code counts, or stack large additive sprites. Cost is covered area times layers, not particle count.

✅ DO plan counts from the rung's budget and cap the total:

```lua
local plan = Blueprint.plan(blueprint, Intensity.BUDGET[level]) -- drops gated layers, scales counts, keeps hostile telegraphs whole
assert(plan.particles <= blueprint.maxParticles)
```

### 2.5 Cosmetic effects are built on the client

❌ DO NOT create particles on the server for every player. ✅ DO send one remote with the effect name, origin and rung; each client builds it from the same blueprint. The server owns the hit, never the sparkle ([FRAMEWORK.md](../../../docs/FRAMEWORK.md)).

## 3. EditableImage procedural flipbooks

### 3.1 A particle cannot show an EditableImage

The research table ([ch. 20 §5.5](../../../docs/research/20-roblox-editableimage-api.md)) separates two questions: a property may be *writable* by a script, and it may *accept* an EditableImage. `ImageLabel.ImageContent`, `ImageButton.ImageContent`, `Decal.TextureContent`, `Texture.*` and `MeshPart.TextureContent` are documented to accept one. `ParticleEmitter.TextureContent`, `Beam.TextureContent` and `Trail.TextureContent` are not: a script can assign a `Content` there, but only a URI is known to render.

❌ DO NOT:

```lua
emitter.TextureContent = Content.fromObject(editableImage) -- accepted by the property, renders nothing useful
```

✅ DO choose by where the frames show:

| You need | Do this |
|---|---|
| Frames on a ParticleEmitter | Bake the sheet offline (Blender or the `Flipbook` generator, then save a PNG), upload it, set `FlipbookLayout`, `FlipbookMode` and `Texture` |
| A runtime-generated animation (a ground sigil, a ring, a screen element) | One EditableImage sheet shown on an `ImageLabel` or `Decal`, stepped by `ImageRectOffset` |
| A look that changes per player or per seed | The runtime route; keep the sheet small (64 px cells, 16 frames) |

### 3.2 Bake the sheet once, upload once, step by rect

❌ DO NOT:

```lua
RunService.PreRender:Connect(function()
	local img = AssetService:CreateEditableImage({ Size = Vector2.new(256, 256) }) -- a new image every frame
	img:WritePixelsBuffer(Vector2.zero, Vector2.new(256, 256), renderOneFrame()) -- and a whole redraw
	label.ImageContent = Content.fromObject(img)
end)
```

✅ DO (`examples/Flipbook.luau` is pure and tested; the Roblox half below is compile-checked only):

```lua
local Flipbook = require("./examples/Flipbook")
local AssetService = game:GetService("AssetService")

local sheet = Flipbook.bake(64, 4, 16, Flipbook.ring) -- once, at load, off the hot path
local img = AssetService:CreateEditableImage({ Size = Vector2.new(sheet.size, sheet.size) })
if img == nil then
	return -- creation fails on low memory: fall back to a baked PNG or skip the effect
end
img:WritePixelsBuffer(Vector2.zero, Vector2.new(sheet.size, sheet.size), sheet.buf) -- one write, ever
label.ImageContent = Content.fromObject(img)
label.ImageRectSize = Vector2.new(sheet.cell, sheet.cell)

local function show(elapsed: number) -- each frame: move the window, touch no pixels
	local frame = Flipbook.frameAt(elapsed, 24, sheet.frames, "OneShot")
	local x, y = Flipbook.rect(frame, sheet.cell, sheet.grid)
	label.ImageRectOffset = Vector2.new(x, y)
end
```

Pool and reuse the EditableImage across plays (`lib/frontier` `ImagePool`); each one counts against a per-device memory budget.

### 3.3 Sheet rules (tested in `examples/Flipbook.test.luau`)

- The sheet is `grid x grid` cells (`Grid2x2` 4 frames, `Grid4x4` 16, `Grid8x8` 64), so its size is an exact multiple of the layout.
- Every cell keeps a 1 px transparent margin, so a filtered sheet doesn't bleed neighbouring frames.
- Alpha under 3/255 is zeroed. Under alpha blending it shows as a faint box.
- Frame 0 must read on its own: low-memory phones turn flipbooks off and show only frame 0.
- At most 30 frames per second. A one-shot ends empty, so it leaves nothing behind.
- Put shape change in the frames and leave rotation to `RotSpeed`.
- One emitter can show N shapes: `FlipbookStartRandom = true` with `FlipbookFramerate = NumberRange.new(0, 0)` gives each particle one random static frame (the shard emitters in the templates).

## 4. Frame-accurate scheduling

### 4.1 One clock per effect, counted in 60 fps frames

❌ DO NOT:

```lua
task.wait(0.3); spawnRing()
task.wait(0.1); spawnArcs()      -- each wait resumes at least one frame late, and the error adds up along the chain
tween.Completed:Wait(); nextStep() -- another hop, another frame of drift; two cues in one frame have no defined order
```

✅ DO (`examples/Timeline.luau`, tested: catch-up, ordering, hit-stop):

```lua
local RunService = game:GetService("RunService")
local Timeline = require("./examples/Timeline")

local timeline = Timeline.new(plan.layers, blueprint.hitFrame, blueprint.duration)
local connection
connection = RunService.PreRender:Connect(function(dt: number)
	for _, cue in timeline:step(dt) do -- every cue that came due, in order; a hitch fires them all in one step
		if cue.kind == "start" then
			runners[cue.layer].start()
		elseif cue.kind == "done" then
			connection:Disconnect() -- one connection per effect, always disconnected
		end
	end
end)
```

⚙ Layer frames are whole numbers inside `0..duration`; the hit frame is 3..90; the Core starts on the hit frame.

### 4.2 Tweens start from cues, with explicit lengths

❌ DO NOT chain tweens through `Completed`. ✅ DO start every tween from its layer's `start` cue with `Timeline.toSeconds(layer.stop - layer.start + 1)` as the length, so the tween and the cue agree on when the layer ends.

### 4.3 Smoothing and springs depend on dt, never on the frame

❌ DO NOT: `value = value:Lerp(target, 0.1)` per frame. It converges twice as fast at 120 fps as at 60.

✅ DO:

```lua
local function smooth(current: number, target: number, k: number, dt: number): number
	return current + (target - current) * (1 - math.exp(-k * dt))
end
```

### 4.4 Hit-stop scales your own clocks

❌ DO NOT change the physics timestep or `task.wait` to "freeze" a hit. Roblox physics can't be paused.

✅ DO set `timeline.timeScale = 0` for the hit-stop frames (the hero flash keeps real time) and feed gameplay the stepped dt from `examples/Impact.luau`. At rung 0 and 1 there is no hit-stop (`Intensity.budget(level).impact` is false).

### 4.5 Beat-locked cues use the audio clock

For a cue that must land on a sound or a beat, `SoundService:GetMixerTime()` is the sample-accurate clock. `os.clock()` and frame time drift against the mixer ([research ch. 45](../../../docs/research/45-roblox-vfx-audio-and-game-feel.md)).
