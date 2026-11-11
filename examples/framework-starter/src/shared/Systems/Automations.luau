--!strict
-- Central system: every per-second effect in the game is one entry here, ticked by one
-- loop. Never start a new `while true` loop for passive income, regen or timers.

export type Entry = {
	id: string,
	interval: number, -- seconds between runs
	run: (save: any, elapsed: number) -> (), -- elapsed = interval * runs this tick (catch-up)
	maxCatchUp: number?, -- cap on runs per tick (protects against huge offline gaps)
}

local Automations = {}
Automations.__index = Automations

export type Automations = typeof(setmetatable({} :: { _entries: { Entry }, _acc: { [string]: number } }, Automations))

function Automations.new(): Automations
	return setmetatable({ _entries = {}, _acc = {} }, Automations)
end

function Automations.add(self: Automations, e: Entry)
	for _, x in self._entries do
		assert(x.id ~= e.id, `duplicate automation {e.id}`)
	end
	table.insert(self._entries, e)
	self._acc[e.id] = 0
end

-- Advance every entry by dt seconds for one save.
function Automations.tick(self: Automations, save: any, dt: number)
	for _, e in self._entries do
		local acc = self._acc[e.id] + dt
		local runs = math.floor(acc / e.interval)
		if runs > 0 then
			local capped = math.min(runs, e.maxCatchUp or 60)
			e.run(save, capped * e.interval)
			acc -= runs * e.interval
		end
		self._acc[e.id] = acc
	end
end

return Automations
