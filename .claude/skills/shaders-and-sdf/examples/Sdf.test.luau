--!strict
local Sdf = require("./Sdf")
local t = require("../../../../tools/lib/t")

t.near("circle centre", Sdf.circle(0, 0, 5), -5)
t.near("circle edge", Sdf.circle(5, 0, 5), 0)
t.near("box face", Sdf.roundBox(10, 0, 10, 5, 0), 0)
t.near("box corner rounding", Sdf.roundBox(10, 5, 10, 5, 2), 2 * math.sqrt(2) - 2, 1e-9)
t.near("ring", Sdf.ring(8, 0, 8, 2), -1)
t.ok("smooth union is below min", Sdf.smoothUnion(1, 1, 2) < 1)
t.near("smooth union far apart = min", Sdf.smoothUnion(0, 10, 2), 0)
t.near("coverage inside", Sdf.coverage(-3), 1)
t.near("coverage edge", Sdf.coverage(0), 0.5)
t.near("glow fades", Sdf.glow(4, 4), 0)

local img = Sdf.rasterize(16, 16, function(x, y)
	return Sdf.circle(x - 8, y - 8, 5)
end)
t.eq("raster inside", buffer.readu8(img, 8 * 16 + 8), 255)
t.eq("raster outside", buffer.readu8(img, 0), 0)
local edge = buffer.readu8(img, 8 * 16 + 12)
t.ok("raster AA edge", edge > 0 and edge < 255)

t.done()
