--!strict
-- RewardSequence: hands attention along in order (HIERARCHY.md §14):
-- container → item → identity → delta → continue. Each beat starts when the previous
-- one settles. Skip always works and jumps to the final state. Beat lengths scale
-- with rarity so a Common drop is quick and a Mythic gets the full ceremony.

local RewardSequence = {}
RewardSequence.__index = RewardSequence

export type Beat = "container" | "item" | "identity" | "delta" | "continue" | "done"
local ORDER: { Beat } = { "container", "item", "identity", "delta", "continue", "done" }

-- seconds per beat at each rarity tier (1 Common .. 7 Secret)
local BASE = { container = 0.35, item = 0.30, identity = 0.40, delta = 0.45, continue = 0 }
local SCALE = { 0.5, 0.6, 0.8, 1.0, 1.3, 1.7, 2.0 }

export type Sequence = typeof(setmetatable({} :: {
	tier: number,
	index: number,
	t: number,
	skipped: boolean,
	onBeat: ((Beat) -> ())?,
}, RewardSequence))

function RewardSequence.new(tier: number, onBeat: ((Beat) -> ())?): Sequence
	local self = setmetatable({ tier = math.clamp(tier, 1, 7), index = 1, t = 0, skipped = false, onBeat = onBeat }, RewardSequence)
	if onBeat then
		onBeat("container")
	end
	return self
end

function RewardSequence.beat(self: Sequence): Beat
	return ORDER[self.index]
end

function RewardSequence.length(self: Sequence, beat: Beat): number
	if beat == "continue" or beat == "done" then
		return math.huge -- waits for input
	end
	return (BASE :: any)[beat] * SCALE[self.tier]
end

-- Progress 0..1 inside the current beat (for easing that beat's animation).
function RewardSequence.progress(self: Sequence): number
	local len = self:length(self:beat())
	return if len == math.huge then 1 else math.clamp(self.t / len, 0, 1)
end

function RewardSequence.step(self: Sequence, dt: number)
	if self:beat() == "done" then
		return
	end
	self.t += dt
	while self.t >= self:length(self:beat()) do
		self.t -= self:length(self:beat())
		self.index += 1
		if self.onBeat then
			self.onBeat(self:beat())
		end
	end
end

-- Input: during the sequence it skips to "continue"; on "continue" it finishes.
function RewardSequence.press(self: Sequence)
	local b = self:beat()
	if b == "continue" then
		self.index = #ORDER
	elseif b ~= "done" then
		self.skipped = true
		self.index = table.find(ORDER, "continue") :: number
	else
		return
	end
	self.t = 0
	if self.onBeat then
		self.onBeat(self:beat())
	end
end

return RewardSequence
