--!strict
-- EffectBudget: how many effects may run at once (HIERARCHY.md sections 9 and 10).
-- Friendly effects are capped by slots and by live particles; an extra one is skipped, never queued.
-- A hostile effect always plays and evicts the oldest friendly effects if the particle cap is exceeded.
-- Pure Luau: no Instance and no clock, the caller passes `now`. Tested in lune.

local EffectBudget = {}

EffectBudget.SLOTS = 6 -- start value, tune in play (HIERARCHY.md section 9)
EffectBudget.PARTICLE_CAP = 400 -- start value, not measured on a phone

export type Entry = { particles: number, hostile: boolean, startedAt: number }
export type State = { slots: number, particleCap: number, entries: { [number]: Entry } }
export type Stats = { friendly: number, hostile: number, particles: number }

function EffectBudget.new(slots: number?, particleCap: number?): State
	return {
		slots = slots or EffectBudget.SLOTS,
		particleCap = particleCap or EffectBudget.PARTICLE_CAP,
		entries = {},
	}
end

function EffectBudget.stats(state: State): Stats
	local friendly, hostile, particles = 0, 0, 0
	for _, entry in state.entries do
		if entry.hostile then
			hostile += 1
		else
			friendly += 1
		end
		particles += entry.particles
	end
	return { friendly = friendly, hostile = hostile, particles = particles }
end

-- Returns whether the effect may start, and the ids of friendly effects the caller must stop.
function EffectBudget.request(
	state: State,
	id: number,
	particles: number,
	hostile: boolean,
	now: number
): (boolean, { number })
	assert(particles >= 0, "particles must be zero or more")
	if state.entries[id] then
		return true, {}
	end
	local current = EffectBudget.stats(state)
	if not hostile and not (current.friendly < state.slots and particles + current.particles <= state.particleCap) then
		return false, {}
	end

	local evicted: { number } = {}
	state.entries[id] = { particles = particles, hostile = hostile, startedAt = now }
	if hostile then
		local total = current.particles + particles
		while total > state.particleCap do
			local oldestId: number? = nil
			local oldest: Entry? = nil
			for otherId, entry in state.entries do
				if not entry.hostile then
					if
						oldest == nil
						or entry.startedAt < oldest.startedAt
						or (entry.startedAt == oldest.startedAt and otherId < (oldestId :: number))
					then
						oldestId, oldest = otherId, entry
					end
				end
			end
			if oldestId == nil or oldest == nil then
				break
			end
			total -= oldest.particles
			state.entries[oldestId] = nil
			table.insert(evicted, oldestId)
		end
	end
	return true, evicted
end

function EffectBudget.release(state: State, id: number)
	state.entries[id] = nil
end

return EffectBudget
