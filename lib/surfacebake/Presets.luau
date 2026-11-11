--!strict
--# selene: allow(mixed_table) -- recipe mask terms are { kind, key = value } by design
-- Presets: ready recipes. Copy one, change numbers only. Scales are per stud of object space
-- (scale 4 = features about a quarter stud apart) and edge distances are in studs; these are
-- tuned for props about 2 studs across, so scale them with the asset.

local Presets = {}

--- Painted metal with chipped, polished edges and grime in the creases.
Presets.paintedMetal = {
	base = { color = { 0.16, 0.36, 0.62 }, rough = 0.45, metal = 0, vary = { scale = 3, amount = 0.06 } },
	detail = { { "noise", scale = 14, octaves = 3, amp = 0.004 } },
	layers = {
		{ name = "chips", color = { 0.62, 0.63, 0.66 }, rough = 0.25, metal = 1, height = -0.04,
			mask = { { "edge", lo = 0.09, hi = 0.02 }, { "noise", scale = 9, octaves = 4, lo = -0.25, hi = 0.15 } } },
		{ name = "grime", color = { 0.12, 0.1, 0.08 }, rough = 0.9, opacity = 0.85,
			mask = { { "ao", lo = 0.8, hi = 0.45 }, { "noise", scale = 6, octaves = 3, lo = -0.4, hi = 0.3 } } },
		{ name = "dust", color = { 0.55, 0.5, 0.42 }, rough = 0.95, opacity = 0.5,
			mask = { { "up", lo = 0.55, hi = 0.9 }, { "noise", scale = 5, octaves = 4, lo = -0.2, hi = 0.4 } } },
	},
	normalStrength = 1,
}

--- Rusted iron: warped rust patches with pitted height, bare metal on worn edges.
Presets.rustedIron = {
	base = { color = { 0.36, 0.36, 0.38 }, rough = 0.35, metal = 1, vary = { scale = 5, amount = 0.08 } },
	detail = { { "noise", scale = 30, octaves = 3, amp = 0.01 } },
	layers = {
		{ name = "rust", color = { 0.45, 0.2, 0.08 }, rough = 0.92, metal = 0, height = 0.05,
			vary = { scale = 14, amount = 0.25 },
			mask = { { "noise", scale = 2.5, octaves = 5, warp = 1.2, lo = -0.05, hi = 0.2 } } },
		{ name = "pitting", color = { 0.28, 0.1, 0.04 }, rough = 1, height = -0.03,
			mask = { { "noise", scale = 2.5, octaves = 5, warp = 1.2, lo = 0.2, hi = 0.35 }, { "voronoi", scale = 22, lo = 0.12, hi = 0 } } },
		{ name = "worn edge", color = { 0.62, 0.62, 0.64 }, rough = 0.2, metal = 1,
			mask = { { "edge", lo = 0.05, hi = 0.01 }, { "noise", scale = 12, octaves = 3, lo = -0.3, hi = 0.2 } } },
	},
	normalStrength = 1.2,
}

--- Cobbled stone: Voronoi cells with mortar cracks, moss on top faces and in crevices.
Presets.mossyStone = {
	base = { color = { 0.48, 0.47, 0.44 }, rough = 0.85, metal = 0, vary = { scale = 2, amount = 0.12 } },
	detail = {
		{ "voronoi", scale = 3, lo = 0.0, hi = 0.18, amp = 0.12 },   -- stones bulge, mortar sinks
		{ "noise", scale = 12, octaves = 4, amp = 0.025 },
	},
	layers = {
		{ name = "stone tint", color = { 0.4, 0.38, 0.36 }, opacity = 0.6,
			mask = { { "voronoi", scale = 3, field = "id", lo = 0.4, hi = 0.8 } } },
		{ name = "mortar", color = { 0.25, 0.24, 0.22 }, rough = 1,
			mask = { { "voronoi", scale = 3, lo = 0.08, hi = 0.0 } } },
		{ name = "moss", color = { 0.22, 0.38, 0.12 }, rough = 0.95, height = 0.02,
			vary = { scale = 16, amount = 0.3 },
			mask = { { "up", lo = 0.2, hi = 0.75 }, { "noise", scale = 3, octaves = 5, lo = -0.1, hi = 0.25 } } },
		{ name = "crevice moss", color = { 0.16, 0.3, 0.1 }, rough = 0.95, opacity = 0.8,
			mask = { { "ao", lo = 0.85, hi = 0.55 } } },
	},
	normalStrength = 1.5,
}

--- Glowing lava rock: dark ridged crust with hot cracks (bake the cracks as an emissive mask too).
Presets.lavaRock = {
	base = { color = { 0.09, 0.08, 0.08 }, rough = 0.9, metal = 0, vary = { scale = 4, amount = 0.2 } },
	detail = { { "ridged", scale = 3, octaves = 4, amp = 0.08 } },
	layers = {
		{ name = "hot cracks", color = { 1.0, 0.42, 0.08 }, rough = 0.6, height = -0.06,
			mask = { { "voronoi", scale = 4, lo = 0.09, hi = 0.0 }, { "noise", scale = 2, octaves = 3, lo = -0.3, hi = 0.1 } } },
		{ name = "embers", color = { 1.0, 0.75, 0.3 },
			mask = { { "voronoi", scale = 4, lo = 0.03, hi = 0.0 }, { "noise", scale = 2, octaves = 3, lo = 0.0, hi = 0.3 } } },
	},
	normalStrength = 1.3,
}

--- Ice: pale, glossy, with frosted cracks and a blue tint in the hollows.
Presets.ice = {
	base = { color = { 0.78, 0.9, 0.97 }, rough = 0.12, metal = 0, vary = { scale = 3, amount = 0.05 } },
	detail = { { "ridged", scale = 5, octaves = 3, amp = 0.02 } },
	layers = {
		{ name = "deep blue", color = { 0.35, 0.6, 0.85 }, opacity = 0.7, mask = { { "ao", lo = 0.9, hi = 0.5 } } },
		{ name = "frost cracks", color = { 0.95, 0.98, 1.0 }, rough = 0.6, height = 0.01,
			mask = { { "voronoi", scale = 6, lo = 0.05, hi = 0.0 } } },
	},
	normalStrength = 0.8,
}

return Presets
