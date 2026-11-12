--!strict
-- Shared helpers for the geometry QA scripts (lune). Output goes through lib/frontier/qa/Out (@@CHECK / @@TIME /
-- @@DONE house protocol), reused rather than duplicated.
local Out = require("../../../frontier/qa/Out")
local GreedyMesher = require("../GreedyMesher")

local Check = {}
Check.Out = Out

local function key3(x: number, y: number, z: number): string
	return string.format("%d,%d,%d", math.floor(x * 1000 + 0.5), math.floor(y * 1000 + 0.5), math.floor(z * 1000 + 0.5))
end
Check.key3 = key3

local function vtx(m: GreedyMesher.Mesh, v: number): (number, number, number)
	return buffer.readf32(m.pos, v * 12), buffer.readf32(m.pos, v * 12 + 4), buffer.readf32(m.pos, v * 12 + 8)
end
Check.vtx = vtx

-- Directed edge counts over welded positions. Returns map "a|b" -> count.
function Check.directedEdges(m: GreedyMesher.Mesh): { [string]: number }
	local e: { [string]: number } = {}
	for t = 0, m.tcount - 1 do
		local k = {}
		for c = 0, 2 do
			local v = buffer.readu32(m.idx, t * 12 + c * 4)
			k[c + 1] = key3(vtx(m, v))
		end
		for c = 1, 3 do
			local a, b = k[c], k[c % 3 + 1]
			local id = a .. "|" .. b
			e[id] = (e[id] or 0) + 1
		end
	end
	return e
end

-- Every triangle side split into unit lattice segments (for meshes with T-junctions). Diagonals are kept whole:
-- they are interior to a quad and shared by its two triangles. Returns directed segment counts.
function Check.unitSegments(m: GreedyMesher.Mesh, unit: number): { [string]: number }
	local e: { [string]: number } = {}
	for t = 0, m.tcount - 1 do
		local p = {}
		for c = 0, 2 do
			local v = buffer.readu32(m.idx, t * 12 + c * 4)
			local x, y, z = vtx(m, v)
			p[c + 1] = { x, y, z }
		end
		for c = 1, 3 do
			local a, b = p[c], p[c % 3 + 1]
			local dx, dy, dz = b[1] - a[1], b[2] - a[2], b[3] - a[3]
			local axisAligned = (math.abs(dx) > 1e-6 and 1 or 0) + (math.abs(dy) > 1e-6 and 1 or 0) + (math.abs(dz) > 1e-6 and 1 or 0) == 1
			local n = if axisAligned then math.floor((math.abs(dx) + math.abs(dy) + math.abs(dz)) / unit + 0.5) else 1
			for s = 0, n - 1 do
				local f0, f1 = s / n, (s + 1) / n
				local id = key3(a[1] + dx * f0, a[2] + dy * f0, a[3] + dz * f0) .. "|" .. key3(a[1] + dx * f1, a[2] + dy * f1, a[3] + dz * f1)
				e[id] = (e[id] or 0) + 1
			end
		end
	end
	return e
end

-- Closed, consistently oriented surface: every directed edge is matched by its reverse the same number of times.
-- Returns (unmatched count, total directed edges, max undirected multiplicity).
function Check.balance(e: { [string]: number }): (number, number, number)
	local bad, total, maxMul = 0, 0, 0
	for id, n in e do
		total += n
		local a, b = id:match("^(.-)|(.*)$")
		local rev = e[(b :: string) .. "|" .. (a :: string)] or 0
		if rev ~= n then
			bad += 1
		end
		maxMul = math.max(maxMul, n + rev)
	end
	return bad, total, maxMul
end

-- Fingerprint of a mesh's vertex data (positions + colours + uvs + indices).
function Check.meshKey(m: GreedyMesher.Mesh): string
	return buffer.readstring(m.pos, 0, m.vcount * 12) .. buffer.readstring(m.col, 0, m.vcount * 4) .. buffer.readstring(m.uv, 0, m.vcount * 8) .. buffer.readstring(m.idx, 0, m.tcount * 12)
end

return Check
