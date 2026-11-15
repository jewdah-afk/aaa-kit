--!strict
-- Crescent slash: body + dark core + shockwave ring, timed by beats. Tier 2 (Hero full, Phone drops shell, Crowd ring only).
-- Templates: a Folder with MeshParts "Body", "Core", "Shell", "Ring" (meshgen OBJs), pivot at the swing centre.
local TweenService = game:GetService("TweenService")

local Beats = { Anticipate = 0.15, Impact = 0.07, Expand = 0.63, Fade = 0.35 }

local function tween(Part: Instance, Time: number, Goal: { [string]: any }, Style: Enum.EasingStyle?)
	local T = TweenService:Create(Part, TweenInfo.new(Time, Style or Enum.EasingStyle.Quint, Enum.EasingDirection.Out), Goal)
	T:Play()
	return T
end

local Slash = {}

function Slash.play(Template: Folder, Origin: CFrame, Rung: string)
	local Fx = Template:Clone()
	local Parts: { [string]: MeshPart } = {}
	for _, v in Fx:GetChildren() do
		if v:IsA("MeshPart") then
			v.Anchored, v.CanCollide, v.CanQuery, v.CanTouch, v.CastShadow = true, false, false, false, false
			v.CFrame = Origin
			v.Transparency = 1
			Parts[v.Name] = v
		end
	end
	if Rung ~= "Hero" and Parts.Shell then Parts.Shell:Destroy(); Parts.Shell = nil end
	if Rung == "Crowd" then
		for k, v in Parts do if k ~= "Ring" then v:Destroy(); Parts[k] = nil end end
	end
	Fx.Parent = workspace

	local Body, Core, Shell, Ring = Parts.Body, Parts.Core, Parts.Shell, Parts.Ring
	-- anticipation: thin sliver swings in
	if Body then
		local Full = Body.Size
		Body.Size = Full * Vector3.new(0.3, 1, 0.3)
		Body.CFrame = Origin * CFrame.Angles(0, math.rad(-40), 0)
		tween(Body, Beats.Anticipate, { Transparency = 0.4, CFrame = Origin }, Enum.EasingStyle.Quad)
		task.delay(Beats.Anticipate, function()
			-- impact frame: only beat at full brightness
			Body.Transparency = 0
			if Core then Core.Transparency = 0 end
			tween(Body, Beats.Impact + Beats.Expand, { Size = Full * 1.35 })
			task.delay(Beats.Impact, function()
				tween(Body, Beats.Expand, { Transparency = 1 })
				if Core then tween(Core, Beats.Expand * 0.5, { Transparency = 1 }) end
			end)
		end)
	end
	if Shell then
		task.delay(Beats.Anticipate, function()
			Shell.Transparency = 0.7
			tween(Shell, Beats.Expand, { Size = Shell.Size * 1.6, Transparency = 1 })
		end)
	end
	if Ring then
		task.delay(Beats.Anticipate + Beats.Impact, function()
			Ring.Transparency = 0.2
			tween(Ring, Beats.Expand, { Size = Ring.Size * 3, Transparency = 1 }, Enum.EasingStyle.Expo)
		end)
	end
	task.delay(Beats.Anticipate + Beats.Impact + Beats.Expand + Beats.Fade, function()
		Fx:Destroy()
	end)
end

return Slash
