--!strict
-- Poisson: Bridson's Poisson-disk sampling. Points no closer than `r`, packed evenly with
-- no grid look. The default for placing props, trees, rocks, spawn points and decals.
-- O(n): a background grid with cell size r/√2 holds at most one point per cell.

local Poisson = {}

export type Point = { x: number, y: number }

-- w, h: area; r: minimum spacing; k: attempts per active point (30 is standard);
-- rand: () -> [0,1); keep(x, y) optional mask (return false to forbid, e.g. paths or water).
function Poisson.sample(w: number, h: number, r: number, rand: () -> number, k: number?, keep: ((number, number) -> boolean)?): { Point }
	local tries = k or 30
	local cell = r / math.sqrt(2)
	local gw, gh = math.ceil(w / cell), math.ceil(h / cell)
	local grid: { [number]: number } = {}
	local points: { Point } = {}
	local active: { number } = {}

	local function fits(x: number, y: number): boolean
		if x < 0 or y < 0 or x >= w or y >= h then
			return false
		end
		if keep and not keep(x, y) then
			return false
		end
		local gx, gy = math.floor(x / cell), math.floor(y / cell)
		for yy = math.max(0, gy - 2), math.min(gh - 1, gy + 2) do
			for xx = math.max(0, gx - 2), math.min(gw - 1, gx + 2) do
				local idx = grid[yy * gw + xx]
				if idx then
					local p = points[idx]
					local dx, dy = p.x - x, p.y - y
					if dx * dx + dy * dy < r * r then
						return false
					end
				end
			end
		end
		return true
	end

	local function add(x: number, y: number)
		table.insert(points, { x = x, y = y })
		grid[math.floor(y / cell) * gw + math.floor(x / cell)] = #points
		table.insert(active, #points)
	end

	-- first point: try a few random spots (the mask may reject some)
	for _ = 1, 100 do
		local x, y = rand() * w, rand() * h
		if fits(x, y) then
			add(x, y)
			break
		end
	end

	while #active > 0 do
		local ai = math.floor(rand() * #active) + 1
		local p = points[active[ai]]
		local placed = false
		for _ = 1, tries do
			local ang = rand() * math.pi * 2
			local dist = r * (1 + rand())
			local x, y = p.x + math.cos(ang) * dist, p.y + math.sin(ang) * dist
			if fits(x, y) then
				add(x, y)
				placed = true
				break
			end
		end
		if not placed then
			active[ai] = active[#active]
			active[#active] = nil
		end
	end
	return points
end

return Poisson
