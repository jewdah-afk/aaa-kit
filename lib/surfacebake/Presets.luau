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

--- Varnished wood: rings around the Y axis bent by noise, darker latewood, knots, worn edges.
Presets.wood = {
	base = { color = { 0.56, 0.36, 0.2 }, rough = 0.55, vary = { scale = 1.5, amount = 0.1 } },
	detail = { { "wave", dir = { 0, 1, 0 }, scale = 18, warp = 0.6, warpScale = 2, amp = 0.004 } },
	layers = {
		{ name = "latewood", color = { 0.36, 0.21, 0.11 }, height = -0.01,
			mask = { { "rings", scale = 7, warp = 1.4, warpScale = 1.2, lo = 0.55, hi = 0.85 } } },
		{ name = "knots", color = { 0.25, 0.14, 0.07 }, rough = 0.7,
			mask = { { "voronoi", scale = 1.5, field = "f1", lo = 0.18, hi = 0.08 }, { "noise", scale = 3, octaves = 2, lo = 0.1, hi = 0.3 } } },
		{ name = "worn varnish", color = { 0.68, 0.48, 0.3 }, rough = 0.8,
			mask = { { "edge", lo = 0.07, hi = 0.015 }, { "noise", scale = 10, octaves = 3, lo = -0.3, hi = 0.2 } } },
	},
	normalStrength = 1,
}

--- Polished gold with tarnish in the hollows and faint fingerprints.
Presets.gold = {
	base = { color = { 1.0, 0.77, 0.34 }, rough = 0.18, metal = 1, vary = { scale = 3, amount = 0.04 } },
	layers = {
		{ name = "tarnish", color = { 0.45, 0.33, 0.14 }, rough = 0.6, opacity = 0.9,
			mask = { { "ao", lo = 0.9, hi = 0.55 }, { "noise", scale = 5, octaves = 3, lo = -0.4, hi = 0.2 } } },
		{ name = "smudges", rough = 0.35, opacity = 0.6,
			mask = { { "noise", scale = 7, octaves = 4, warp = 1.5, lo = 0.25, hi = 0.45 } } },
		{ name = "bright edge", color = { 1.0, 0.87, 0.55 }, rough = 0.08,
			mask = { { "edge", lo = 0.04, hi = 0.0 } } },
	},
	normalStrength = 0.5,
}

--- Veined marble: warped sine veins, a few darker cracks, a high polish.
Presets.marble = {
	base = { color = { 0.92, 0.91, 0.88 }, rough = 0.12, vary = { scale = 2, amount = 0.05 } },
	layers = {
		{ name = "veins", color = { 0.42, 0.42, 0.46 }, rough = 0.2,
			mask = { { "wave", dir = { 0.6, 0.8, 0.2 }, scale = 1.6, warp = 3.2, warpScale = 1.4, octaves = 5, lo = 0.86, hi = 0.97 } } },
		{ name = "gold veins", color = { 0.78, 0.6, 0.3 }, rough = 0.15, metal = 0.6,
			mask = { { "wave", dir = { -0.3, 0.9, 0.4 }, scale = 0.9, warp = 4, warpScale = 1, octaves = 5, lo = 0.95, hi = 0.99 } } },
	},
	normalStrength = 0.3,
}

--- Sci-fi hull panels: panel seams, a lit strip, grime in the seams, scuffed edges.
Presets.sciFiPanel = {
	base = { color = { 0.68, 0.7, 0.74 }, rough = 0.4, metal = 0.8, vary = { scale = 2, amount = 0.04 } },
	layers = {
		{ name = "panel tint", color = { 0.58, 0.6, 0.64 }, opacity = 0.7,
			mask = { { "voronoi", scale = 2, field = "id", lo = 0.5, hi = 0.8 } } },
		{ name = "seams", color = { 0.12, 0.13, 0.15 }, rough = 0.8, height = -0.03,
			mask = { { "grid", scale = 2, lo = 0.03, hi = 0.0 } } },
		{ name = "light strip", color = { 0.3, 0.9, 1.0 }, rough = 0.3, metal = 0,
			mask = { { "grid", scale = 0.5, lo = 0.02, hi = 0.0 }, { "up", lo = 0.5, hi = -0.5 } } },
		{ name = "scuffs", color = { 0.85, 0.86, 0.88 }, rough = 0.25,
			mask = { { "edge", lo = 0.05, hi = 0.0 }, { "noise", scale = 14, octaves = 3, lo = -0.2, hi = 0.3 } } },
	},
	normalStrength = 1,
}

--- Woodland camouflage: three stacked noise thresholds, matte.
Presets.camo = {
	base = { color = { 0.42, 0.45, 0.3 }, rough = 0.85 },
	layers = {
		{ name = "brown", color = { 0.36, 0.27, 0.17 }, mask = { { "noise", scale = 1.6, octaves = 3, warp = 0.8, lo = 0.05, hi = 0.09 } } },
		{ name = "dark", color = { 0.16, 0.18, 0.13 }, mask = { { "noise", scale = 2.2, octaves = 3, warp = 0.8, seed = 3, lo = 0.15, hi = 0.19 } } },
		{ name = "tan", color = { 0.66, 0.6, 0.44 }, mask = { { "noise", scale = 2.6, octaves = 3, warp = 0.8, seed = 7, lo = 0.3, hi = 0.34 } } },
	},
	normalStrength = 0.2,
}

--- Snow-capped rock: ridged granite, snow on top faces with a soft edge.
Presets.snowRock = {
	base = { color = { 0.4, 0.39, 0.38 }, rough = 0.85, vary = { scale = 3, amount = 0.15 } },
	detail = { { "ridged", scale = 2.5, octaves = 5, amp = 0.1 } },
	layers = {
		{ name = "lichen", color = { 0.52, 0.5, 0.32 }, opacity = 0.6,
			mask = { { "noise", scale = 5, octaves = 4, lo = 0.25, hi = 0.4 } } },
		{ name = "snow", color = { 0.93, 0.95, 0.98 }, rough = 0.5, height = 0.04,
			mask = { { "up", lo = 0.35, hi = 0.6 }, { "noise", scale = 2, octaves = 4, lo = -0.4, hi = -0.1 } } },
	},
	normalStrength = 1.4,
}

--- Glossy slime: warped green with bright highlights and darker pockets.
Presets.slime = {
	base = { color = { 0.32, 0.78, 0.24 }, rough = 0.08, vary = { scale = 2, amount = 0.2 } },
	detail = { { "noise", scale = 3, octaves = 3, warp = 2, amp = 0.05 } },
	layers = {
		{ name = "pockets", color = { 0.12, 0.42, 0.1 }, mask = { { "noise", scale = 3, octaves = 3, warp = 2, lo = 0.1, hi = 0.4 } } },
		{ name = "bubbles", color = { 0.7, 1.0, 0.55 }, height = 0.03,
			mask = { { "voronoi", scale = 6, field = "f1", lo = 0.22, hi = 0.12 }, { "noise", scale = 4, octaves = 2, lo = 0.0, hi = 0.3 } } },
	},
	normalStrength = 1.2,
}

--- Rune-carved stone: dark blocks, carved channels glowing cyan (animate with Animate "pulse").
Presets.runeStone = {
	base = { color = { 0.3, 0.3, 0.33 }, rough = 0.9, vary = { scale = 2, amount = 0.15 } },
	detail = { { "voronoi", scale = 2, lo = 0.0, hi = 0.12, amp = 0.06 }, { "noise", scale = 10, octaves = 3, amp = 0.015 } },
	layers = {
		{ name = "block seams", color = { 0.15, 0.15, 0.17 }, mask = { { "voronoi", scale = 2, lo = 0.05, hi = 0.0 } } },
		{ name = "runes", color = { 0.35, 0.95, 1.0 }, rough = 0.4, height = -0.025,
			mask = { { "wave", dir = { 1, 0.3, 0.7 }, scale = 3, warp = 0.8, warpScale = 4, lo = 0.93, hi = 0.99 }, { "voronoi", scale = 2, lo = 0.12, hi = 0.2 } } },
	},
	normalStrength = 1.3,
}

--- Carbon fibre: two crossed waves make the weave; glossy clear coat.
Presets.carbonFiber = {
	base = { color = { 0.1, 0.1, 0.11 }, rough = 0.15 },
	detail = { { "wave", dir = { 1, 1, 0 }, scale = 30, amp = 0.002 }, { "wave", dir = { 1, -1, 0 }, scale = 30, amp = 0.002 } },
	layers = {
		{ name = "weave A", color = { 0.34, 0.34, 0.37 }, mask = { { "wave", dir = { 1, 1, 0.3 }, scale = 14, lo = 0.2, hi = 0.9 } } },
		{ name = "weave B", color = { 0.2, 0.2, 0.23 }, mask = { { "wave", dir = { 1, -1, -0.3 }, scale = 14, lo = 0.2, hi = 0.9 } } },
	},
	normalStrength = 0.6,
}

--- Aged copper: verdigris patina in the hollows and on top, bright copper on the edges.
Presets.copperPatina = {
	base = { color = { 0.72, 0.42, 0.26 }, rough = 0.35, metal = 1, vary = { scale = 4, amount = 0.1 } },
	layers = {
		{ name = "verdigris", color = { 0.32, 0.66, 0.56 }, rough = 0.9, metal = 0, height = 0.015,
			vary = { scale = 12, amount = 0.2 },
			mask = { { "ao", lo = 0.95, hi = 0.6 }, { "noise", scale = 4, octaves = 4, warp = 1, lo = -0.3, hi = 0.1 } } },
		{ name = "rain streaks", color = { 0.38, 0.62, 0.52 }, rough = 0.85, metal = 0,
			mask = { { "wave", dir = { 1, 0, 0.3 }, scale = 9, warp = 0.6, warpScale = 3, lo = 0.6, hi = 0.95 }, { "noise", scale = 1.5, octaves = 3, lo = 0.0, hi = 0.3 } } },
		{ name = "polished edge", color = { 0.9, 0.58, 0.4 }, rough = 0.2, metal = 1,
			mask = { { "edge", lo = 0.05, hi = 0.0 } } },
	},
	normalStrength = 0.8,
}

return Presets
