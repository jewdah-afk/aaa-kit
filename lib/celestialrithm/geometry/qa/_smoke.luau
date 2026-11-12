local VG = require("../VoxelGrid")
local GM = require("../GreedyMesher")
local S = require("../SampleModels")
for _, res in {32, 64} do
	local t0 = os.clock()
	local g, f = VG.sculpt(S.StudSlime, res, {seed = 1})
	local t1 = os.clock()
	local m = GM.mesh(g, {})
	local t2 = os.clock()
	print(res, g.nx, g.ny, g.nz, VG.count(g), VG.colorsUsed(g), "sculpt ms", (t1-t0)*1000, "mesh ms", (t2-t1)*1000, "quads", m.quads, "naive", GM.exposedFaces(g), "area", GM.area(m))
	local g2 = VG.sculpt(S.RewardChest, res, {seed = 1})
	print("chest", VG.count(g2), VG.colorsUsed(g2), GM.mesh(g2).quads, g2.pieces ~= nil)
end
