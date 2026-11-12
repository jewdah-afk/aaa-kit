--!strict
-- SampleModels: two generic stud-voxel models written as sculpt recipes (pure data, no code).
-- Units are recipe units; VoxelGrid.sculpt(recipe, res) fits `res` voxels along the longest bounds axis.
-- Axes: +Y up, front = -Z (Roblox LookVector of an unrotated part), left/right = +-X.
-- Both share one bounds box and a 15-colour combined palette, so they can be morphed into each other
-- (VoxelMorph) without re-quantising.
--
-- Look rules applied (from studying stud-voxel creature work; see docs/celestialrithm/frontier/editablemesh-voxel.md):
-- one hue in light / main / dark tone jobs (light top, dark underside), small saturated accents, flush eyes made
-- of a dark block plus a flat white shine (eyes and shines are `flat`: never studded), blush, an oversized
-- signature trait (the sprout), and everything blended from a few big ellipsoids with smooth-min.

local SampleModels = {}

local BOUNDS = { min = { -11.5, 0, -10.5 }, max = { 11.5, 20.5, 10.5 } }

local PALETTE = {
	-- slime: mint-teal tone jobs + accents
	main = 0x3FBF9B,
	light = 0x86E6C6,
	dark = 0x24806B,
	belly = 0xCDF5E6,
	spot = 0x2AA184,
	eye = 0x1E1B2E,
	shine = 0xFFFFFF,
	blush = 0xFF8FA3,
	stem = 0x4E8B2E,
	leaf = 0x8CCB45,
	-- chest: wood + gold
	wood = 0x9A5B2E,
	woodDark = 0x6B3A1E,
	woodLight = 0xC07A3F,
	gold = 0xF2C230,
	goldDark = 0xB8861B,
}

local FLAT = { eye = true, shine = true }

SampleModels.StudSlime = {
	name = "StudSlime",
	bounds = BOUNDS,
	palette = PALETTE,
	flat = FLAT,
	ops = {
		-- body: a dome, a wider puddle base and a top dollop, smooth-blended
		{ op = "union", shape = "ellipsoid", c = { 0, 7, 0 }, r = { 9.5, 7.2, 8.6 }, color = "main" },
		{ op = "union", shape = "ellipsoid", c = { 0, 2.6, 0 }, r = { 11, 3.2, 10 }, color = "main", k = 3 },
		{ op = "union", shape = "sphere", c = { 0, 13.4, 0.6 }, r = 3.4, color = "main", k = 3.5 },
		-- flat bottom so it sits on the ground
		{ op = "subtract", shape = "box", c = { 0, -5, 0 }, h = { 20, 5.6, 20 } },
		-- sprout: stem + two leaves (rigid piece "sprout" so it can be animated separately)
		{ op = "union", shape = "capsule", a = { 0, 15.6, 0.6 }, b = { 0.4, 18.6, 0.6 }, r = 0.75, color = "stem", piece = "sprout" },
		{ op = "union", shape = "ellipsoid", c = { 2.7, 18.9, 0.6 }, r = { 2.6, 0.9, 1.5 }, color = "leaf", piece = "sprout" },
		{ op = "union", shape = "ellipsoid", c = { -2.0, 18.4, 0.6 }, r = { 2.0, 0.8, 1.2 }, color = "leaf", piece = "sprout" },
		-- tone jobs: light top, dark underside band
		{ op = "paint", shape = "ellipsoid", c = { -1.5, 13.5, -1.0 }, r = { 7.5, 4.6, 7.5 }, color = "light" },
		{ op = "paint", shape = "box", c = { 0, 0.5, 0 }, h = { 20, 1.2, 20 }, color = "dark" },
		-- belly patch on the front
		{ op = "paint", shape = "ellipsoid", c = { 0, 4.6, -9.6 }, r = { 6.2, 3.6, 3.2 }, color = "belly" },
		-- eyes: dark flush blocks with one flat shine each, then blush and a small mouth
		{ op = "paint", shape = "ellipsoid", c = { -3.7, 8.6, -9.4 }, r = { 1.55, 2.25, 2.6 }, color = "eye" },
		{ op = "paint", shape = "ellipsoid", c = { 3.7, 8.6, -9.4 }, r = { 1.55, 2.25, 2.6 }, color = "eye" },
		{ op = "paint", shape = "sphere", c = { -4.1, 9.7, -8.2 }, r = 1.0, color = "shine" },
		{ op = "paint", shape = "sphere", c = { 3.3, 9.7, -8.2 }, r = 1.0, color = "shine" },
		{ op = "paint", shape = "ellipsoid", c = { -6.6, 6.6, -8.4 }, r = { 1.7, 1.0, 2.4 }, color = "blush" },
		{ op = "paint", shape = "ellipsoid", c = { 6.6, 6.6, -8.4 }, r = { 1.7, 1.0, 2.4 }, color = "blush" },
		{ op = "paint", shape = "box", c = { 0, 6.7, -9.6 }, h = { 0.9, 0.45, 2.0 }, color = "eye" },
	},
	-- seeded darker spots on the back and sides: change the seed, change the pattern
	scatter = {
		{ count = 6, around = { c = { 0, 7, 0 }, r = { 9.5, 7.2, 8.6 } }, radius = { 1.0, 1.7 }, color = "spot", minY = 3.5, minZ = -4 },
	},
}

SampleModels.RewardChest = {
	name = "RewardChest",
	bounds = BOUNDS,
	palette = PALETTE,
	flat = FLAT,
	ops = {
		-- base box and a rounded lid (rigid piece "lid": hinge it at the back edge to open)
		{ op = "union", shape = "box", c = { 0, 4.6, 0 }, h = { 9.6, 4.6, 7.0 }, round = 0.6, color = "wood" },
		{ op = "union", shape = "box", c = { 0, 10.6, 0 }, h = { 10.0, 1.6, 7.4 }, round = 0.6, color = "wood", piece = "lid" },
		{ op = "union", shape = "ellipsoid", c = { 0, 11.6, 0 }, r = { 10.0, 4.2, 7.4 }, color = "woodLight", piece = "lid", k = 1.2 },
		{ op = "subtract", shape = "box", c = { 0, -5, 0 }, h = { 20, 5, 20 } },
		-- plank lines and the lid seam
		{ op = "paint", shape = "box", c = { 0, 3.0, 0 }, h = { 20, 0.35, 20 }, color = "woodDark" },
		{ op = "paint", shape = "box", c = { 0, 6.2, 0 }, h = { 20, 0.35, 20 }, color = "woodDark" },
		{ op = "paint", shape = "box", c = { 0, 9.2, 0 }, h = { 20, 0.5, 20 }, color = "woodDark" },
		-- gold straps over body and lid, then the lock plate with a keyhole
		{ op = "paint", shape = "box", c = { -6.2, 8, 0 }, h = { 1.0, 12, 20 }, color = "gold" },
		{ op = "paint", shape = "box", c = { 6.2, 8, 0 }, h = { 1.0, 12, 20 }, color = "gold" },
		{ op = "paint", shape = "box", c = { 0, 0.6, 0 }, h = { 20, 0.7, 20 }, color = "goldDark" },
		{ op = "union", shape = "box", c = { 0, 8.6, -7.2 }, h = { 1.8, 2.2, 0.9 }, color = "gold", piece = "lid" },
		{ op = "paint", shape = "box", c = { 0, 8.2, -8.2 }, h = { 0.45, 0.9, 0.6 }, color = "eye" },
		{ op = "paint", shape = "box", c = { 0, 15.4, 0 }, h = { 20, 0.6, 20 }, color = "goldDark" },
	},
}

-- The morph pair used by the transformation moment (slime -> chest "mimic" reveal).
SampleModels.MorphPair = { SampleModels.StudSlime, SampleModels.RewardChest }

return SampleModels
