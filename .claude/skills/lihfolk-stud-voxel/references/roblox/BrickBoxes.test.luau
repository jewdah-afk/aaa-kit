-- lune run BrickBoxes.test.luau
local BrickBoxes = require("./BrickBoxes")

local passed = 0
local function check(name: string, cond: boolean)
	if not cond then
		error("FAIL: " .. name, 2)
	end
	passed += 1
end

-- every exposed cell is covered exactly once, by a box of its own colour and bone; no box holds an empty cell
local function verify(g, boxes): boolean
	local cover = {}
	for _, b in boxes do
		for y = b.y0, b.y1 do
			for z = b.z0, b.z1 do
				for x = b.x0, b.x1 do
					local c = g:get(x, y, z)
					if c == 0 then
						return false
					end
					local i = x + g.nx * (z + g.nz * y)
					if buffer.readu8(g.bone, i) ~= b.bone then
						return false
					end
					local open = false
					for _, d in { { 1, 0, 0 }, { -1, 0, 0 }, { 0, 1, 0 }, { 0, -1, 0 }, { 0, 0, 1 }, { 0, 0, -1 } } do
						if g:get(x + d[1], y + d[2], z + d[3]) == 0 then
							open = true
						end
					end
					if open then
						if c ~= b.colour or cover[i] then
							return false
						end
						cover[i] = true
					end
				end
			end
		end
	end
	local n = 0
	for _ in cover do
		n += 1
	end
	return n == g:lint().exposed
end

-- 1. a solid block is one box
local g = BrickBoxes.new(8, 6, 4)
g:fill(0, 0, 0, 7, 5, 3, 1)
local b = g:boxes()
check("solid block merges to one box", #b == 1 and b[1].x1 == 7 and b[1].y1 == 5 and b[1].z1 == 3)
check("solid block verifies", verify(g, b))

-- 2. a stepped ball: far fewer boxes than exposed bricks, all rules hold
g = BrickBoxes.new(40, 40, 40)
g:ellipsoid(20, 20, 20, 18, 18, 18, 1)
b = g:boxes()
local l = g:lint()
check("ball verifies", verify(g, b))
check("ball: at least 4x fewer boxes than exposed bricks", #b * 4 < l.exposed)
check("ball: nothing floats, one colour", l.floating == 0 and l.colours == 1)

-- 3. painted detail keeps its colour: eyes on the front of a head
g = BrickBoxes.new(24, 24, 24)
g:ellipsoid(12, 12, 12, 10, 10, 10, 1)
local eyes = 0
for _, ex in { 8, 15 } do
	for z = 0, 23 do
		if g:get(ex, 14, z) ~= 0 then
			g:set(ex, 14, z, 2) -- first solid cell from the front
			eyes += 1
			break
		end
	end
end
b = g:boxes()
local eyeBoxes = 0
for _, bx in b do
	if bx.colour == 2 then
		eyeBoxes += 1
	end
end
check("eyes painted", eyes == 2)
check("eyes verify and keep their own boxes", verify(g, b) and eyeBoxes == 2)

-- 4. boxes never cross a bone boundary
g = BrickBoxes.new(10, 20, 6)
g:fill(0, 0, 0, 9, 9, 5, 1, 1)
g:fill(0, 10, 0, 9, 19, 5, 1, 2)
b = g:boxes()
check("two bones give two boxes", #b == 2 and b[1].bone ~= b[2].bone and verify(g, b))

-- 5. lint finds floating bricks; ground-resting pieces can be allowed
g = BrickBoxes.new(20, 20, 20)
g:fill(0, 0, 0, 9, 9, 9, 1)
g:set(15, 15, 15, 3)
g:set(18, 0, 18, 3)
check("lint counts floating bricks", g:lint().floating == 2)
check("groundOk keeps the brick on the floor", g:lint(true).floating == 1)
check("lint counts colours", g:lint().colours == 2)

-- 6. diagonal contact counts as connected (26-neighbourhood), like the Python pipeline
g = BrickBoxes.new(4, 4, 4)
g:set(0, 0, 0, 1)
g:set(1, 1, 1, 1)
check("diagonal neighbours are connected", g:lint().floating == 0)

-- 7. deterministic
g = BrickBoxes.new(30, 30, 30)
g:ellipsoid(15, 15, 15, 13, 11, 9, 1)
local b1, b2 = g:boxes(), g:boxes()
local same = #b1 == #b2
for i, bx in b1 do
	same = same and bx.x0 == b2[i].x0 and bx.y1 == b2[i].y1 and bx.z1 == b2[i].z1
end
check("same grid gives the same boxes", same)

print(`BrickBoxes: {passed} checks passed`)
