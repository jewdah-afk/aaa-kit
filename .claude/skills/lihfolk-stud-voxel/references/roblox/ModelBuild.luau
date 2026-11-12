-- ModelBuild: builds a boss from its <Name>Data module (exported from Blender). Run once in Edit (or at runtime on the server).
-- One Part per box (studs on all 6 faces, Neon for glow colors), welded with a Weld to an invisible "bone part".
-- Bone parts are chained with Motor6D (folder Joints); ModelAnimator writes Motor6D.Transform (+ optional scale).
-- Usage: local build = require(ModelBuild); local model = build(require(SharkData), CFrame.new(0, 0, 0), "Shark"); model.Parent = workspace
local STUD_FACES = { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" }
local DEFAULT_GLOW = { EY = true, IC = true, GL = true, GO = true, GP = true }
local DEFAULT_NOSTUD = { EY = true, IR = true, WH = true, SH = true, PU = true } -- eyes are never studded

return function(data, place: CFrame, name: string?, glow: { [string]: boolean }?)
	glow = glow or data.Glow or DEFAULT_GLOW -- studlib exports data.Glow
	local model = Instance.new("Model")
	model.Name = name or "Boss"

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

	local bones, heads = {}, {}
	for _, b in data.Bones do -- parents always come before their children
		local boneName, parentName, pos = b[1], b[2], b[3]
		heads[boneName] = pos
		local p = Instance.new("Part")
		p.Name = "B_" .. boneName
		p.Size = Vector3.one * 0.4
		p.Transparency = 1
		p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
		p.Massless = true
		p.CFrame = place * CFrame.new(pos)
		p.Parent = model
		bones[boneName] = p

		local m = Instance.new("Motor6D")
		m.Name = boneName
		m.Part0 = parentName and bones[parentName] or root
		m.Part1 = p
		m.C0 = CFrame.new(pos - (parentName and heads[parentName] or Vector3.zero))
		m:SetAttribute("Parent", parentName or "")
		m:SetAttribute("BaseC0", m.C0.Position)
		m.Parent = joints
	end

	for _, bx in data.Boxes do
		local bone, k, size, pos, xv, yv, zv = table.unpack(bx)
		local cf = CFrame.fromMatrix(pos, xv, yv, zv)
		local shape = bx[8] -- nil = box, "Wedge" = WedgePart, "Cyl" = cylinder (axis = local X)
		local p = Instance.new(shape == "Wedge" and "WedgePart" or "Part")
		if shape == "Cyl" then
			p.Shape = Enum.PartType.Cylinder
		end
		p.Name = k
		p.Size = size
		p.CFrame = place * cf
		p.Color = Color3.fromHex(data.Colors[k])
		if glow[k] then
			p.Material = Enum.Material.Neon
		elseif (data.NoStud or DEFAULT_NOSTUD)[k] then
			p.Material = Enum.Material.SmoothPlastic
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
		w.Part0 = bones[bone]
		w.Part1 = p
		w.C0 = CFrame.new(heads[bone]):Inverse() * cf -- bone parts are world-aligned at rest
		w:SetAttribute("BaseOffset", w.C0.Position)
		w.Parent = p
		p.Parent = model
	end
	return model
end
