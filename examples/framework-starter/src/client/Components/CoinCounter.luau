--!strict
-- Component template: bound to a CollectionService tag, construct/start/stop lifecycle,
-- one Maid in `self._maid`. This one rolls a TextLabel toward the coin total
-- (odometer-style count-up, HIERARCHY.md tier 3: still until the number changes).

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Kit = require(ReplicatedStorage:WaitForChild("Shared").Kit)

local TAG = "CoinCounter"
local SETTLE = 0.35 -- seconds to close ~95% of the gap

export type CoinCounter = {
	label: TextLabel,
	shown: number,
	target: number,
	_maid: any,
}

local CoinCounter = {}
CoinCounter.__index = CoinCounter

function CoinCounter.construct(label: TextLabel): CoinCounter
	local self = setmetatable({}, CoinCounter) :: any
	self.label = label
	self.shown = 0
	self.target = 0
	self._maid = Kit.Maid.new()
	return self
end

function CoinCounter.start(self: CoinCounter, changed: any)
	self._maid:give(changed:connect(function(key: string, value: any)
		if key == "coins" then
			self.target = value
		end
	end))
	self._maid:give(RunService.RenderStepped:Connect(function(dt)
		if self.shown == self.target then
			return -- calm: no work when nothing changes
		end
		local k = 1 - math.exp(-dt * 3 / SETTLE)
		self.shown += (self.target - self.shown) * k
		if math.abs(self.target - self.shown) < 1 then
			self.shown = self.target
		end
		self.label.Text = Kit.Format.short(self.shown)
	end))
end

function CoinCounter.stop(self: CoinCounter)
	self._maid:clean()
end

-- Binder: one instance per tagged label, cleaned when the tag or label goes away.
local live: { [Instance]: CoinCounter } = {}

local function bind(changed: any)
	local function add(inst: Instance)
		if inst:IsA("TextLabel") and not live[inst] then
			local c = CoinCounter.construct(inst)
			live[inst] = c
			c:start(changed)
		end
	end
	local function remove(inst: Instance)
		local c = live[inst]
		if c then
			c:stop()
			live[inst] = nil
		end
	end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(add)
	CollectionService:GetInstanceRemovedSignal(TAG):Connect(remove)
	for _, inst in CollectionService:GetTagged(TAG) do
		add(inst)
	end
end

CoinCounter.bind = bind
return CoinCounter
