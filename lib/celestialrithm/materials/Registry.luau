--!strict
-- Registry of the runtime materials, in canonical-id order. Every entry has
-- `.new(width, height, seed, quality)` and `:Render(t, press, outBuffer)` writing RGBA8 for
-- EditableImage:WritePixelsBuffer, plus `:Bytes()` (memory held by the face).

local Registry = {
	order = { "hydroglass", "solar_plasma", "crystal_ice", "molten_core" },
	byId = {
		hydroglass = require("./Hydroglass"),
		solar_plasma = require("./SolarPlasma"),
		crystal_ice = require("./CrystalIce"),
		molten_core = require("./MoltenCore"),
	},
	tiers = { "high", "mid", "low" },
}

return Registry
