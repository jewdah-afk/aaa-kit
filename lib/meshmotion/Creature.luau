--!native
--!optimize 2
-- Creature: one animated instance = Rig + current clip + deformer stack + per-frame hooks.
-- Hooks are the surface link: register surfacebake/frontier animators (rainbow coat, glow pulse) with
-- `onFrame` so texture and geometry advance on the same tick and freeze together when the LOD scheduler
-- skips this creature. `present` is where the adapter push goes (editable or parts mode).
-- Pure Luau.

local Rig = require("./Rig")
local Animator = require("./Animator")

local Creature = {}
Creature.__index = Creature

function Creature.new(data, o: { clip: any?, deformers: { any }?, present: ((any) -> ())? }?)
	local self = setmetatable({
		rig = Rig.new(data),
		clip = o and o.clip,
		deformers = (o and o.deformers) or {},
		hooks = {} :: { (number, number) -> () },
		present = o and o.present,
		speed = 1,
		clock = 0,
	}, Creature)
	return self
end

function Creature.play(self, clip, restart: boolean?)
	self.clip = clip
	if restart ~= false then
		self.clock = 0
	end
	self.rig:resetPose()
end

function Creature.onFrame(self, fn: (number, number) -> ())
	table.insert(self.hooks, fn)
end

-- Advance by dt (seconds since this creature last updated; the scheduler can make it several frames).
function Creature.step(self, dt: number)
	self.clock += dt * self.speed
	local t = self.clock
	if self.clip then
		Animator.sample(self.clip, self.rig, t)
	end
	self.rig:update(t, dt, self.deformers)
	for _, h in self.hooks do
		h(t, dt)
	end
	if self.present then
		self.present(self.rig)
	end
end

return Creature
