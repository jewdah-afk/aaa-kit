--!native
--!optimize 2
-- Store: one immutable MeshData per creature, loaded once and shared by every instance.
-- MeshData holds rest positions (f32 xyz), triangles (u32), the segment of each vertex (u16), a per-vertex
-- secondary-motion weight (f32, 0 = rigid, 1 = full jiggle) and the segment tree (name, parent, pivot).
-- Segments are stored parents-first, so one forward pass solves the whole hierarchy.
-- Pure Luau. Coordinates are Roblox studs, Y up.

local Store = {}

export type Segment = { name: string, parent: number?, pivot: { number } }
export type MeshData = {
	name: string,
	n: number, -- vertices
	triCount: number,
	rest: buffer, -- n * 3 f32
	tris: buffer, -- triCount * 3 u32 (0-based vertex index)
	seg: buffer, -- n u16 (1-based segment index)
	weight: buffer, -- n f32
	segments: { Segment },
	segIndex: { [string]: number },
	bounds: { min: { number }, max: { number } },
}

-- Engine limits for one EditableMesh (docs/research/41-editablemesh-technique-cookbook.md).
Store.MAX_VERTS = 60000
Store.MAX_TRIS = 20000

-- Blueprint (what tools/export_blend.py writes):
--   { name, verts = {x,y,z, ...}, tris = {a,b,c, ...} (0-based), vseg = {segName per vertex},
--     weights = {w per vertex}?, segments = { {name, parent?, pivot = {x,y,z}} ... } }
function Store.fromBlueprint(bp: any): MeshData
	local n = #bp.verts // 3
	local triCount = #bp.tris // 3
	assert(n > 0 and #bp.verts == n * 3, "verts must be a flat xyz list")
	assert(#bp.tris == triCount * 3, "tris must be a flat abc list")
	assert(n <= Store.MAX_VERTS, `{bp.name}: {n} verts over the {Store.MAX_VERTS} limit`)
	assert(triCount <= Store.MAX_TRIS, `{bp.name}: {triCount} tris over the {Store.MAX_TRIS} limit`)
	assert(#bp.vseg == n, "vseg needs one segment name per vertex")

	-- Order segments parents-first (stable), and reject cycles or unknown parents.
	local byName = {}
	for _, s in bp.segments do
		assert(byName[s.name] == nil, `duplicate segment {s.name}`)
		byName[s.name] = s
	end
	local ordered, placed, visiting = {}, {}, {}
	local function place(s)
		if placed[s.name] then
			return
		end
		assert(not visiting[s.name], `segment cycle at {s.name}`)
		visiting[s.name] = true
		if s.parent then
			local p = byName[s.parent]
			assert(p, `{s.name}: unknown parent {s.parent}`)
			place(p)
		end
		visiting[s.name] = nil
		placed[s.name] = true
		table.insert(ordered, s)
	end
	for _, s in bp.segments do
		place(s)
	end
	local segIndex = {}
	for i, s in ordered do
		segIndex[s.name] = i
	end
	local segments = {}
	for i, s in ordered do
		local pv = s.pivot or { 0, 0, 0 }
		segments[i] = { name = s.name, parent = s.parent and segIndex[s.parent], pivot = { pv[1], pv[2], pv[3] } }
	end
	assert(#segments <= 65535, "too many segments")

	local rest = buffer.create(n * 12)
	local mn, mx = { math.huge, math.huge, math.huge }, { -math.huge, -math.huge, -math.huge }
	for i = 0, n - 1 do
		for k = 1, 3 do
			local v = bp.verts[i * 3 + k]
			buffer.writef32(rest, (i * 3 + k - 1) * 4, v)
			mn[k] = math.min(mn[k], v)
			mx[k] = math.max(mx[k], v)
		end
	end
	local tris = buffer.create(triCount * 12)
	for i = 1, triCount * 3 do
		local v = bp.tris[i]
		assert(v >= 0 and v < n, `triangle index {v} out of range`)
		buffer.writeu32(tris, (i - 1) * 4, v)
	end
	local seg, weight = buffer.create(n * 2), buffer.create(n * 4)
	for i = 0, n - 1 do
		local si = segIndex[bp.vseg[i + 1]]
		assert(si, `vertex {i}: unknown segment {bp.vseg[i + 1]}`)
		buffer.writeu16(seg, i * 2, si)
		buffer.writef32(weight, i * 4, if bp.weights then bp.weights[i + 1] else 0)
	end

	return table.freeze({
		name = bp.name or "Mesh",
		n = n,
		triCount = triCount,
		rest = rest,
		tris = tris,
		seg = seg,
		weight = weight,
		segments = segments,
		segIndex = segIndex,
		bounds = { min = mn, max = mx },
	})
end

-- Shared cache: one MeshData per name, reference counted so the last release frees it.
local cache: { [string]: { data: MeshData, refs: number } } = {}

function Store.acquire(name: string, load: () -> any): MeshData
	local e = cache[name]
	if not e then
		e = { data = Store.fromBlueprint(load()), refs = 0 }
		cache[name] = e
	end
	e.refs += 1
	return e.data
end

function Store.release(name: string)
	local e = cache[name]
	if not e then
		return
	end
	e.refs -= 1
	if e.refs <= 0 then
		cache[name] = nil
	end
end

function Store.refs(name: string): number
	local e = cache[name]
	return if e then e.refs else 0
end

return Store
