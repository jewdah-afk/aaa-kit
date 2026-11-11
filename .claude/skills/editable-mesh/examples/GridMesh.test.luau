--!strict
local GridMesh = require("./GridMesh")
local t = require("../../../../tools/lib/t")

local flat = GridMesh.build(10, 4, function()
	return 0
end)
t.eq("vertex count", #flat.positions, 25)
t.eq("triangle count", #flat.tris, 32)
t.near("flat normal is up", flat.normals[13][2], 1)

-- winding: cross product of a flat triangle points +Y
local tri = flat.tris[1]
local a, b, c = flat.positions[tri[1]], flat.positions[tri[2]], flat.positions[tri[3]]
local ux, uz = b[1] - a[1], b[3] - a[3]
local vx, vz = c[1] - a[1], c[3] - a[3]
t.ok("counter-clockwise from +Y", (uz * vx - ux * vz) > 0)

local hill = GridMesh.build(10, 8, function(x, z)
	return 3 * math.exp(-(x * x + z * z) / 8)
end)
local maxY = 0
for _, p in hill.positions do
	maxY = math.max(maxY, p[2])
end
t.near("peak height", maxY, 3, 1e-9)
t.ok("slope normal tilts", hill.normals[1 + 9 * 4 + 6][1] > 0)

t.eq("LOD near", GridMesh.cellsForDistance(32, 10, 50), 32)
t.eq("LOD mid", GridMesh.cellsForDistance(32, 100, 50), 16)
t.eq("LOD far", GridMesh.cellsForDistance(32, 400, 50), 8)

t.done()
