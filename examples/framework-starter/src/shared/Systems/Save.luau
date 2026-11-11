--!strict
-- Central system: the save template and reconcile.
-- A new field goes in TEMPLATE only; `reconcile` fills it into every old save on load.
-- Pure: no DataStore calls here (the DataService owns storage, session locks and retries).

local Save = {}

Save.VERSION = 1

Save.TEMPLATE = table.freeze({
	version = Save.VERSION,
	coins = 0,
	gems = 0,
	upgrades = {} :: { [string]: number },
	unlocked = {} :: { [string]: boolean },
	stats = { coinsEarned = 0, coinsSpent = 0, resets = 0, playSeconds = 0 },
	settings = { music = 0.8, sfx = 1, reducedMotion = false },
})

local function deepCopy(v: any): any
	if type(v) ~= "table" then
		return v
	end
	local out = {}
	for k, x in v do
		out[k] = deepCopy(x)
	end
	return out
end

Save.copy = deepCopy

-- Returns a fresh save.
function Save.new(): any
	return deepCopy(Save.TEMPLATE)
end

-- Fills missing keys from the template (recursively) and drops values whose type
-- changed. Never removes unknown keys: a newer server may have written them.
function Save.reconcile(data: any, template: any?): any
	local t = template or Save.TEMPLATE
	if type(data) ~= "table" then
		return deepCopy(t)
	end
	for k, def in t do
		local cur = data[k]
		if cur == nil or type(cur) ~= type(def) then
			data[k] = deepCopy(def)
		elseif type(def) == "table" and next(def) ~= nil then
			Save.reconcile(cur, def)
		end
	end
	data.version = Save.VERSION
	return data
end

return Save
