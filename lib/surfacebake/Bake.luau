--!strict
-- Bake: mesh + recipe -> RGBA8 maps ready for EditableImage:WritePixelsBuffer.
--   albedo     sRGB colour, alpha 255 on the model (and its gutter), 0 elsewhere
--   normal     tangent-space, OpenGL convention (+Y up, green not inverted), as Roblox expects
--   roughness  grey
--   metalness  grey
--   curvature, ao, edge   grey debug/reuse maps (edge: white on sharp edges, fading out by edgeMax)
-- Normals come from the recipe's height evaluated at +-epsilon along the texel's tangent and
-- bitangent in 3D, so the bump is continuous across UV seams.
--
-- Pure Luau; runs in lune and Roblox. Use opts.yield (e.g. task.wait) to spread a big bake
-- over frames in game; Apply.luau wires the result to a MeshPart.

local Mesh = require("./Mesh")
local Raster = require("./Raster")
local Surface = require("./Surface")
local Recipe = require("./Recipe")
type Mesh = Mesh.Mesh

export type Maps = {
	W: number,
	H: number,
	albedo: buffer,
	normal: buffer,
	roughness: buffer,
	metalness: buffer,
	curvature: buffer,
	ao: buffer,
	edge: buffer,
	G: Raster.GBuffer,
	ms: { [string]: number },
}

export type Options = {
	size: number?, -- square texture size (default 256; Roblox max 1024)
	padding: number?, -- gutter texels (default 4)
	curvatureGain: number?,
	aoRadius: number?, -- studs; default 25% of the mesh's bounding radius
	aoRays: number?,
	edgeMax: number?, -- studs; edge-distance field is capped here (default 10% of bounding radius)
	edgeAngle: number?, -- degrees; dihedral angle that counts as a sharp edge (default 30)
	flipGreen: boolean?, -- DirectX-style green channel (Roblox wants OpenGL, so leave false)
	yield: (() -> ())?, -- called every few rows so a big bake doesn't freeze a frame
	rowsPerYield: number?,
}

local Bake = {}

local function clock(): number
	return os.clock()
end

local function boundsRadius(m: Mesh): number
	local P = m.P
	local cx, cy, cz, n = 0, 0, 0, #P // 3
	for v = 1, n do
		cx += P[v * 3 - 2]
		cy += P[v * 3 - 1]
		cz += P[v * 3]
	end
	cx, cy, cz = cx / n, cy / n, cz / n
	local r = 0
	for v = 1, n do
		r = math.max(r, math.sqrt((P[v * 3 - 2] - cx) ^ 2 + (P[v * 3 - 1] - cy) ^ 2 + (P[v * 3] - cz) ^ 2))
	end
	return r
end

-- Object-space size of one texel: sqrt(surface area / covered texels).
local function texelSize(m: Mesh, G: Raster.GBuffer): number
	local P, tris = m.P, m.tris
	local area = 0
	for t = 1, #tris // 3 do
		local a, b, c = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
		local e1x, e1y, e1z = P[b * 3 - 2] - P[a * 3 - 2], P[b * 3 - 1] - P[a * 3 - 1], P[b * 3] - P[a * 3]
		local e2x, e2y, e2z = P[c * 3 - 2] - P[a * 3 - 2], P[c * 3 - 1] - P[a * 3 - 1], P[c * 3] - P[a * 3]
		local x, y, z = e1y * e2z - e1z * e2y, e1z * e2x - e1x * e2z, e1x * e2y - e1y * e2x
		area += math.sqrt(x * x + y * y + z * z) / 2
	end
	return math.sqrt(area / math.max(1, G.covered))
end

local function u8(v: number): number
	return math.clamp(math.floor(v * 255 + 0.5), 0, 255)
end

function Bake.run(m: Mesh, recipe: any, opts: Options?): Maps
	local o = opts or {}
	local S = o.size or 256
	local ms = {}
	local t0 = clock()
	local G = Raster.bake(m, S, S)
	Raster.dilate(G, o.padding or 4)
	ms.raster = (clock() - t0) * 1000

	t0 = clock()
	local curvV = Surface.vertexCurvature(m, o.curvatureGain)
	local aoV = Surface.vertexAO(m, o.aoRadius or boundsRadius(m) * 0.25, o.aoRays)
	local curvT = Surface.toTexels(G, m, curvV)
	local aoT = Surface.toTexels(G, m, aoV)
	local edgeMax = o.edgeMax or boundsRadius(m) * 0.1
	local edgeT = Surface.edgeDistance(G, m, edgeMax, o.edgeAngle)
	ms.surface = (clock() - t0) * 1000

	t0 = clock()
	local n = S * S
	local albedo, normal = buffer.create(n * 4), buffer.create(n * 4)
	local rough, metal = buffer.create(n * 4), buffer.create(n * 4)
	local curvOut, aoOut, edgeOut = buffer.create(n * 4), buffer.create(n * 4), buffer.create(n * 4)
	local eps = texelSize(m, G)
	local strength = recipe.normalStrength or 1
	local c = { px = 0, py = 0, pz = 0, nx = 0, ny = 1, nz = 0, curv = 0.5, ao = 1, edge = 0 }
	local rowsPerYield = o.rowsPerYield or 16
	for y = 0, S - 1 do
		for x = 0, S - 1 do
			local i = y * S + x
			local q = i * 4
			if buffer.readu8(G.cover, i) ~= 0 then
				local px, py, pz = Raster.readVec(G.pos, i)
				local nx, ny, nz = Raster.readVec(G.nrm, i)
				local tx, ty, tz = Raster.readVec(G.tan, i)
				c.px, c.py, c.pz, c.nx, c.ny, c.nz = px, py, pz, nx, ny, nz
				c.curv = buffer.readf32(curvT, q)
				c.ao = buffer.readf32(aoT, q)
				c.edge = buffer.readf32(edgeT, q)
				local r, g, b, ro, me, h0 = Recipe.shade(recipe, c :: any)
				-- OpenGL normal maps: red = slope along +u, green = slope along image-up (= -v,
				-- because rows grow with v). opts.flipGreen gives DirectX-style maps if needed.
				local vx, vy, vz = Raster.readVec(G.bit, i)
				local ht = Recipe.height(recipe, c :: any, px + tx * eps, py + ty * eps, pz + tz * eps)
				local hu = Recipe.height(recipe, c :: any, px - vx * eps, py - vy * eps, pz - vz * eps)
				local du, dv = (ht - h0) / eps * strength, (hu - h0) / eps * strength
				if o.flipGreen then
					dv = -dv
				end
				local l = math.sqrt(du * du + dv * dv + 1)
				buffer.writeu32(albedo, q, u8(r) + u8(g) * 256 + u8(b) * 65536 + 255 * 16777216)
				buffer.writeu32(normal, q, u8(-du / l * 0.5 + 0.5) + u8(-dv / l * 0.5 + 0.5) * 256 + u8(1 / l * 0.5 + 0.5) * 65536 + 255 * 16777216)
				local rv, mv = u8(ro), u8(me)
				buffer.writeu32(rough, q, rv * 65793 + 255 * 16777216)
				buffer.writeu32(metal, q, mv * 65793 + 255 * 16777216)
				local cv, av = u8(c.curv), u8(c.ao)
				buffer.writeu32(curvOut, q, cv * 65793 + 255 * 16777216)
				buffer.writeu32(aoOut, q, av * 65793 + 255 * 16777216)
				local ev = u8(1 - c.edge / edgeMax)
				buffer.writeu32(edgeOut, q, ev * 65793 + 255 * 16777216)
			else
				-- outside the model: flat normal, mid roughness, transparent albedo
				buffer.writeu32(normal, q, 128 + 128 * 256 + 255 * 65536 + 255 * 16777216)
				buffer.writeu32(rough, q, 128 * 65793 + 255 * 16777216)
			end
		end
		if o.yield and (y + 1) % rowsPerYield == 0 then
			o.yield()
		end
	end
	ms.shade = (clock() - t0) * 1000
	return {
		W = S,
		H = S,
		albedo = albedo,
		normal = normal,
		roughness = rough,
		metalness = metal,
		curvature = curvOut,
		ao = aoOut,
		edge = edgeOut,
		G = G,
		ms = ms,
	}
end

return Bake
