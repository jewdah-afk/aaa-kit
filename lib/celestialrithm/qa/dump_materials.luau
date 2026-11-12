--!strict
-- Raw RGBA8 dumps for parity.py: renders each material from t = 0 in 1/FPS steps up to T (sim
-- materials need every frame) and writes the final frame to qa/out/<id>_<w>x<h>_<tier>.rgba.
-- Usage: lune run dump_materials.luau [w h frames fps press tier seed]

local fs = require("@lune/fs")
local process = require("@lune/process")
local Registry = require("../materials/Registry")

local a = process.args
local W = tonumber(a[1]) or 240
local H = tonumber(a[2]) or 112
local FRAMES = tonumber(a[3]) or 30
local FPS = tonumber(a[4]) or 30
local PRESS = tonumber(a[5]) or 0
local TIER = a[6] or "high"
local SEED = tonumber(a[7]) or 1

local dir = "out"
if not fs.isDir(dir) then
	fs.writeDir(dir)
end
local out = buffer.create(W * H * 4)
for _, id in Registry.order do
	local M = (Registry.byId :: any)[id]
	local m = M.new(W, H, SEED, TIER)
	for f = 0, FRAMES do
		m:Render(f / FPS, PRESS, out)
	end
	local path = `{dir}/{id}_{W}x{H}_{TIER}.rgba`
	fs.writeFile(path, buffer.tostring(out))
	print(`wrote {path}`)
end
