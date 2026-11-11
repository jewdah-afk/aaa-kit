--!strict
-- Central system: applies a reset layer from Content/ResetLayers.
-- Wipes go back to the save template's value; keeps win over wipes.

local Layers = require("../Content/ResetLayers")
local Save = require("./Save")

local Reset = {}

function Reset.payout(save: any, layerId: string): number
	local layer = Layers[layerId]
	assert(layer, `unknown reset layer {layerId}`)
	local p = layer.payout
	local from = save.stats[p.from] or 0
	return math.floor(p.base * from ^ p.exponent)
end

function Reset.canReset(save: any, layerId: string): boolean
	local layer = Layers[layerId]
	return layer ~= nil and (save.stats[layer.requires.stat] or 0) >= layer.requires.atLeast
end

-- Applies the layer and every lower layer's wipes. Returns the payout, or nil if not allowed.
function Reset.apply(save: any, layerId: string): number?
	if not Reset.canReset(save, layerId) then
		return nil
	end
	local layer = Layers[layerId]
	local gain = Reset.payout(save, layerId)

	local keep: { [string]: boolean } = {}
	for _, k in layer.keeps do
		keep[k] = true
	end
	for _, other in Layers do
		if other.order <= layer.order then
			for _, k in other.wipes do
				if not keep[k] then
					save[k] = Save.copy(Save.TEMPLATE[k])
				end
			end
		end
	end

	save[layer.payout.currency] += gain
	save.stats.resets += 1
	save.stats.coinsEarned = 0 -- the stat the payout reads starts over each layer
	return gain
end

return Reset
