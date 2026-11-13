--!strict
-- Hologram blueprint maths: a model as a fixed set of voxel slots, and a 1:1 transform of any
-- voxel pile into those slots. Pure Luau (no Roblox types), so it runs headless under lune.
--
-- Data comes from lihfolk-stud-voxel/scripts/blueprint.py (see EmberDragonBlueprint.luau).
-- Positions are flat arrays { x1, y1, z1, x2, ... } in brick coords: x right, y up, z back.

local Blueprint = {}

export type Data = {
	name: string,
	studsPerBrick: number,
	mirrored: boolean,
	cell: number,
	slotOrigin: { number },
	slotCount: number,
	palette: { number },
	glow: { boolean },
	anchors: { { name: string, p: { number } } },
	bones: { { any } },
	slots: string,
}

export type Decoded = {
	count: number,
	cell: number,
	pos: { number }, -- 3 per slot: the slot centre, in bricks
	color: { number }, -- 0xRRGGBB per slot
	light: { number }, -- 0..1 baked top light per slot
	glow: { boolean }, -- emissive slots (eyes, cores)
}

-- Unpack the slot string: 5 hex bytes per slot (ix, iy, iz, palette index, light).
function Blueprint.decode(data: Data): Decoded
	local n = data.slotCount
	assert(#data.slots == n * 10, "slot string length does not match slotCount")
	local pos = table.create(n * 3)
	local color = table.create(n)
	local light = table.create(n)
	local glow = table.create(n)
	local ox, oy, oz = data.slotOrigin[1], data.slotOrigin[2], data.slotOrigin[3]
	local c = data.cell
	local s = data.slots
	for i = 1, n do
		local at = (i - 1) * 10
		local v = tonumber(string.sub(s, at + 1, at + 8), 16) :: number
		local ix, iy, iz, p = v // 16777216, (v // 65536) % 256, (v // 256) % 256, v % 256
		pos[i * 3 - 2] = ox + (ix + 0.5) * c
		pos[i * 3 - 1] = oy + (iy + 0.5) * c
		pos[i * 3] = oz + (iz + 0.5) * c
		color[i] = data.palette[p + 1]
		glow[i] = data.glow[p + 1]
		light[i] = (tonumber(string.sub(s, at + 9, at + 10), 16) :: number) / 255
	end
	return { count = n, cell = c, pos = pos, color = color, light = light, glow = glow }
end

-- Largest distance between a point and its mirror twin across x = 0 (0 = exactly symmetric).
function Blueprint.mirrorError(pos: { number }): number
	local seen: { [string]: boolean } = {}
	local n = #pos // 3
	for i = 1, n do
		seen[string.format("%.3f|%.3f|%.3f", pos[i * 3 - 2], pos[i * 3 - 1], pos[i * 3])] = true
	end
	local worst = 0
	for i = 1, n do
		if not seen[string.format("%.3f|%.3f|%.3f", -pos[i * 3 - 2], pos[i * 3 - 1], pos[i * 3])] then
			worst = math.max(worst, 2 * math.abs(pos[i * 3 - 2]))
		end
	end
	return worst
end

local function spread(v: number): number -- 10 bits -> every third bit
	v = bit32.band(v, 0x3ff)
	v = bit32.band(bit32.bor(v, bit32.lshift(v, 16)), 0x30000ff)
	v = bit32.band(bit32.bor(v, bit32.lshift(v, 8)), 0x300f00f)
	v = bit32.band(bit32.bor(v, bit32.lshift(v, 4)), 0x30c30c3)
	return bit32.band(bit32.bor(v, bit32.lshift(v, 2)), 0x9249249)
end

-- Indices of the points sorted along a Morton (Z-order) curve through their own bounding box.
function Blueprint.mortonOrder(pos: { number }): { number }
	local n = #pos // 3
	local lo = { math.huge, math.huge, math.huge }
	local hi = { -math.huge, -math.huge, -math.huge }
	for i = 1, n do
		for a = 1, 3 do
			local v = pos[(i - 1) * 3 + a]
			lo[a] = math.min(lo[a], v)
			hi[a] = math.max(hi[a], v)
		end
	end
	local keys = table.create(n)
	local order = table.create(n)
	for i = 1, n do
		local k = 0
		for a = 1, 3 do
			local span = hi[a] - lo[a]
			local q = if span > 0 then math.floor((pos[(i - 1) * 3 + a] - lo[a]) / span * 1023 + 0.5) else 0
			k += spread(q) * 2 ^ (a - 1)
		end
		keys[i] = k
		order[i] = i
	end
	table.sort(order, function(p, q)
		if keys[p] ~= keys[q] then
			return keys[p] < keys[q]
		end
		return p < q
	end)
	return order
end

-- 1:1 pairing of a source pile to the slots: the k-th source along its Morton curve goes to the
-- k-th slot along the slots' Morton curve, so neighbours stay neighbours and no slot is shared.
-- Returns perm where perm[slot] = source index. Both sets must have the same count.
function Blueprint.assign(src: { number }, dst: { number }): { number }
	assert(#src == #dst, "source and slot counts differ")
	local so, dorder = Blueprint.mortonOrder(src), Blueprint.mortonOrder(dst)
	local perm = table.create(#dorder)
	for k = 1, #dorder do
		perm[dorder[k]] = so[k]
	end
	return perm
end

-- A source pile: n voxels stacked as a solid block on the ground under the model.
function Blueprint.pile(n: number, cell: number, cx: number, y0: number, cz: number): { number }
	local side = math.ceil((n / 0.5) ^ (1 / 3)) -- about twice as wide as it is tall
	local pos = table.create(n * 3)
	local half = (side - 1) / 2
	for i = 0, n - 1 do
		local ix, iz, iy = i % side, (i // side) % side, i // (side * side)
		pos[i * 3 + 1] = cx + (ix - half) * cell
		pos[i * 3 + 2] = y0 + (iy + 0.5) * cell
		pos[i * 3 + 3] = cz + (iz - half) * cell
	end
	return pos
end

-- A source shell: n voxels on a Fibonacci sphere (an egg when ry > r).
function Blueprint.shell(n: number, cx: number, cy: number, cz: number, r: number, ry: number?): { number }
	local pos = table.create(n * 3)
	local golden = math.pi * (3 - math.sqrt(5))
	for i = 0, n - 1 do
		local y = 1 - 2 * (i + 0.5) / n
		local rad = math.sqrt(1 - y * y)
		pos[i * 3 + 1] = cx + math.cos(golden * i) * rad * r
		pos[i * 3 + 2] = cy + y * (ry or r)
		pos[i * 3 + 3] = cz + math.sin(golden * i) * rad * r
	end
	return pos
end

-- Progress of one slot at global time t (0..1). Slots start in build order (bottom-up), each takes
-- (1 - stagger) of the timeline, eased. Exactly 0 at t = 0 and exactly 1 at t = 1 for every slot.
function Blueprint.progress(t: number, slot: number, count: number, stagger: number): number
	local start = if count > 1 then stagger * (slot - 1) / (count - 1) else 0
	local u = math.clamp((t - start) / (1 - stagger), 0, 1)
	return u * u * (3 - 2 * u)
end

export type PoseOptions = { stagger: number?, arc: number? }

-- Write every voxel's position at time t into `out` (flat, same layout). At t = 1 each voxel sits
-- exactly on its slot. `arc` lifts the flight path (bricks) so voxels don't tunnel through the model.
function Blueprint.pose(out: { number }, src: { number }, dst: { number }, perm: { number }, t: number, opts: PoseOptions?): { number }
	local n = #dst // 3
	local stagger = if opts and opts.stagger then opts.stagger else 0.6
	local arc = if opts and opts.arc then opts.arc else 0
	for i = 1, n do
		local e = Blueprint.progress(t, i, n, stagger)
		local s = (perm[i] - 1) * 3
		local d = (i - 1) * 3
		out[d + 1] = dst[d + 1] * e + src[s + 1] * (1 - e)
		out[d + 2] = dst[d + 2] * e + src[s + 2] * (1 - e) + arc * 4 * e * (1 - e)
		out[d + 3] = dst[d + 3] * e + src[s + 3] * (1 - e)
	end
	return out
end

return Blueprint
