-- BrickBuild: builds a brick model in Studio straight from a BrickBoxes grid. No Blender, no 3D Importer.
-- One studded Part per merged box, welded to an invisible bone part; bone parts are chained with Motor6D in a
-- "Joints" folder exactly like ModelBuild, so ModelAnimator plays clips on the result unchanged.
-- NOT YET RUN IN STUDIO: BrickBoxes is tested under lune; this file is compile-checked only.
--
-- Usage (command bar or a server script):
--   local BrickBoxes = require(path.BrickBoxes)
--   local grid = BrickBoxes.new(48, 64, 40)
--   grid:ellipsoid(24, 20, 20, 16, 16, 15, 1, 1)                    -- palette 1, bone 1
--   local model = require(path.BrickBuild)(grid, {
--       Palette = { "e9ebef", "2b2b30" },                           -- hex per palette index
--       Glow = { [2] = true },                                      -- palette indices drawn as Neon, no studs
--       Bones = { { "root", nil, { 24, 0, 20 } }, { "head", "root", { 24, 40, 20 } } },   -- name, parent, pivot in cells
--       StudsPerBrick = 2.5,
--       MaterialVariant = nil,                                      -- name of a MaterialVariant with the square stud tile
--   }, CFrame.new(0, 0, 0), "MyMob")
--   model.Parent = workspace
local STUD_FACES = { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" }

return function(grid, spec, place: CFrame, name: string?)
	local s = spec.StudsPerBrick or 2.5
	local ox, oz = grid.nx / 2, grid.nz / 2 -- model origin: centred on x and z, standing on y = 0
	local function studs(x: number, y: number, z: number): Vector3
		return Vector3.new((x - ox) * s, y * s, (z - oz) * s)
	end

	local model = Instance.new("Model")
	model.Name = name or "BrickModel"
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.one
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide, root.CanQuery, root.CanTouch = false, false, false
	root.CFrame = place
	root.Parent = model
	model.PrimaryPart = root
	local joints = Instance.new("Folder")
	joints.Name = "Joints"
	joints.Parent = model

	local boneParts, heads = {}, {}
	for i, b in spec.Bones do -- parents come before their children
		local boneName, parentName, pivot = b[1], b[2], b[3]
		local pos = studs(pivot[1], pivot[2], pivot[3])
		heads[i], heads[boneName] = pos, pos
		local p = Instance.new("Part")
		p.Name = "B_" .. boneName
		p.Size = Vector3.one * 0.4
		p.Transparency = 1
		p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
		p.Massless = true
		p.CFrame = place * CFrame.new(pos)
		p.Parent = model
		boneParts[i], boneParts[boneName] = p, p
		local m = Instance.new("Motor6D")
		m.Name = boneName
		m.Part0 = parentName and boneParts[parentName] or root
		m.Part1 = p
		m.C0 = CFrame.new(pos - (parentName and heads[parentName] or Vector3.zero))
		m:SetAttribute("Parent", parentName or "")
		m:SetAttribute("BaseC0", m.C0.Position)
		m.Parent = joints
	end

	local glow = spec.Glow or {}
	local boxes = grid:boxes()
	for _, bx in boxes do
		local size = Vector3.new(bx.x1 - bx.x0 + 1, bx.y1 - bx.y0 + 1, bx.z1 - bx.z0 + 1) * s
		local pos = studs((bx.x0 + bx.x1 + 1) / 2, (bx.y0 + bx.y1 + 1) / 2, (bx.z0 + bx.z1 + 1) / 2)
		local p = Instance.new("Part")
		p.Name = "C" .. bx.colour
		p.Size = size
		p.CFrame = place * CFrame.new(pos)
		p.Color = Color3.fromHex(spec.Palette[bx.colour])
		if glow[bx.colour] then
			p.Material = Enum.Material.Neon
		elseif spec.MaterialVariant then
			p.Material = Enum.Material.Plastic
			p.MaterialVariant = spec.MaterialVariant
		else
			p.Material = Enum.Material.Plastic
			for _, f in STUD_FACES do
				p[f] = Enum.SurfaceType.Studs
			end
		end
		p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
		p.Massless = true
		p:SetAttribute("BaseSize", size)
		local w = Instance.new("Weld")
		w.Part0 = boneParts[bx.bone]
		w.Part1 = p
		w.C0 = CFrame.new(pos - heads[bx.bone])
		w:SetAttribute("BaseOffset", w.C0.Position)
		w.Parent = p
		p.Parent = model
	end
	model:SetAttribute("Boxes", #boxes)
	return model
end
