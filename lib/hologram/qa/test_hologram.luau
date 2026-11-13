-- Headless checks for the hologram blueprint. Run: cd lib/hologram/qa && lune run test_hologram.luau | grep -a '^@@'
local Out = require("../../frontier/qa/Out")
local Blueprint = require("../Blueprint")
type Data = typeof(require("../EmberDragonBlueprint"))
local n = 0
for _, case in { { "maths.", require("../EmberDragonBlueprint") }, { "picture.", require("../EmberDragonRefBlueprint") } } do
	local tag: string, Data: Data = case[1], case[2]

	local bp = Blueprint.decode(Data)
	n = bp.count

	Out.check(tag .. "decode.count_matches", n == Data.slotCount and #bp.pos == n * 3 and #bp.color == n, tostring(n))
	Out.check(tag .. "decode.enough_slots_for_a_boss", n > 2000 and n < 20000, tostring(n))

	local inPalette = true
	for i = 1, n do
		if table.find(Data.palette, bp.color[i]) == nil or bp.light[i] < 0 or bp.light[i] > 1 then
			inPalette = false
		end
	end
	Out.check(tag .. "decode.colours_from_palette", inPalette)

	-- every slot has an exact twin across x = 0
	Out.check(tag .. "mirror.slots_exact", Blueprint.mirrorError(bp.pos) == 0, tostring(Blueprint.mirrorError(bp.pos)))

	-- slots are unique and on the cell lattice
	local seen: { [string]: boolean } = {}
	local unique, onGrid = true, true
	for i = 1, n do
		local x, y, z = bp.pos[i * 3 - 2], bp.pos[i * 3 - 1], bp.pos[i * 3]
		local k = x .. "," .. y .. "," .. z
		if seen[k] then
			unique = false
		end
		seen[k] = true
		if ((x - Data.slotOrigin[1]) / Data.cell) % 1 ~= 0.5 then
			onGrid = false
		end
	end
	Out.check(tag .. "slots.unique", unique)
	Out.check(tag .. "slots.on_cell_lattice", onGrid)

	-- build order is bottom-up
	local rising = true
	for i = 2, n do
		if bp.pos[i * 3 - 1] < bp.pos[(i - 1) * 3 - 1] then
			rising = false
		end
	end
	Out.check(tag .. "slots.sorted_bottom_up", rising)

	-- anchors: left and right joints mirror each other; bones index real anchors
	local byName: { [string]: { number } } = {}
	for _, a in Data.anchors do
		byName[a.name] = a.p
	end
	local pairsOk, pairsN = true, 0
	for name, p in byName do
		local twin = byName[(string.gsub(name, "L_", "R_", 1))]
		if string.find(name, "L_", 1, true) and twin then
			pairsN += 1
			if math.abs(p[1] + twin[1]) > 0.01 or math.abs(p[2] - twin[2]) > 0.01 or math.abs(p[3] - twin[3]) > 0.01 then
				pairsOk = false
			end
		end
	end
	Out.check(tag .. "anchors.left_right_mirror", pairsOk and pairsN >= 6, tostring(pairsN))
	local bonesOk = #Data.bones > 0
	for _, b in Data.bones do
		if Data.anchors[b[1]] == nil or Data.anchors[b[2]] == nil then
			bonesOk = false
		end
	end
	Out.check(tag .. "bones.index_anchors", bonesOk, tostring(#Data.bones))

	-- assignment is a permutation (1:1), for both source shapes
	for _, src_case in { { "pile", Blueprint.pile(n, bp.cell, 0, 0, 0) }, { "shell", Blueprint.shell(n, 0, 60, 0, 40, 55) } } do
		local name, src = src_case[1], src_case[2]
		local perm = Blueprint.assign(src, bp.pos)
		local used: { [number]: boolean } = {}
		local ok = #perm == n
		for i = 1, n do
			if perm[i] == nil or used[perm[i]] or perm[i] < 1 or perm[i] > n then
				ok = false
			end
			used[perm[i]] = true
		end
		Out.check(tag .. "assign." .. name .. "_is_one_to_one", ok)

		-- t = 0 is the source pile, t = 1 is exactly the blueprint
		local out = table.create(n * 3, 0)
		Blueprint.pose(out, src, bp.pos, perm, 0, { arc = 30 })
		local atSrc = true
		for i = 1, n do
			for a = 1, 3 do
				if out[(i - 1) * 3 + a] ~= src[(perm[i] - 1) * 3 + a] then
					atSrc = false
				end
			end
		end
		Out.check(tag .. "pose." .. name .. "_t0_is_source", atSrc)
		Blueprint.pose(out, src, bp.pos, perm, 1, { arc = 30 })
		local exact = true
		for i = 1, n * 3 do
			if out[i] ~= bp.pos[i] then
				exact = false
			end
		end
		Out.check(tag .. "pose." .. name .. "_t1_exact", exact)

		-- Morton pairing keeps travel short compared with pairing in storage order
		local function travel(p: { number }): number
			local sum = 0
			for i = 1, n do
				local s, d = (p[i] - 1) * 3, (i - 1) * 3
				sum += math.sqrt((src[s + 1] - bp.pos[d + 1]) ^ 2 + (src[s + 2] - bp.pos[d + 2]) ^ 2 + (src[s + 3] - bp.pos[d + 3]) ^ 2)
			end
			return sum / n
		end
		local identity = table.create(n)
		for i = 1, n do
			identity[i] = (i * 7919) % n + 1 -- a fixed shuffle (7919 is prime, so this is a permutation when n is not a multiple)
		end
		Out.check(tag .. "assign." .. name .. "_shorter_than_shuffled", travel(perm) < travel(identity), string.format("%.1f vs %.1f bricks", travel(perm), travel(identity)))
	end

end

-- progress: monotonic per slot, bottom slots start first
local mono = true
for _, slot in { 1, n // 2, n } do
	local last = -1
	for step = 0, 50 do
		local e = Blueprint.progress(step / 50, slot, n, 0.6)
		if e < last then
			mono = false
		end
		last = e
	end
end
Out.check("progress.monotonic", mono)
Out.check("progress.bottom_first", Blueprint.progress(0.3, 1, n, 0.6) > Blueprint.progress(0.3, n, n, 0.6))
Out.check("progress.ends_exact", Blueprint.progress(1, 1, n, 0.6) == 1 and Blueprint.progress(1, n, n, 0.6) == 1 and Blueprint.progress(0, 1, n, 0.6) == 0)

Out.done()
