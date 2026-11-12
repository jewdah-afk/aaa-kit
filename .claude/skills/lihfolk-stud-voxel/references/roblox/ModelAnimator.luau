-- ModelAnimator: plays the Blender clips (<Name>Clips) on a model built by ModelBuild. Client side: call :Step(dt) every frame.
-- Clip key = { frame, {qx,qy,qz,qw per bone..., rootX, rootY, rootZ}, {sx,sy,sz per bone}? }
-- The third table (scale) is optional: Shark "Inflate" and every Kraken clip use it. Scale is inherited down the bone
-- chain (like Blender / three.js): Motor6D.C0 offsets, Weld offsets and Part sizes are multiplied by the accumulated scale.
local Animator = {}
Animator.__index = Animator

function Animator.new(model: Model, data, clips)
	local self = setmetatable({}, Animator)
	self.Fps = data.Fps or 30
	self.Motors, self.Parent, self.Welds = {}, {}, {}
	for _, m in model:WaitForChild("Joints"):GetChildren() do
		self.Motors[m.Name] = m
		local par = m:GetAttribute("Parent")
		self.Parent[m.Name] = (par ~= "" and par) or nil
	end
	-- welds per bone (to scale parts)
	for _, p in model:GetChildren() do
		local w = p:IsA("BasePart") and p:FindFirstChildOfClass("Weld")
		if w and w.Part0 then
			local bone = string.sub(w.Part0.Name, 3)
			self.Welds[bone] = self.Welds[bone] or {}
			table.insert(self.Welds[bone], w)
		end
	end
	self.Order = clips.Bones -- parents before children
	local n = #self.Order
	self.Clips = {}
	for name, clip in clips.Clips do
		local keys = {}
		for i, k in clip.Keys do
			local v, sc, pose, scale = k[2], k[3], {}, nil
			for b, bone in self.Order do
				local o = (b - 1) * 4
				pose[bone] = CFrame.new(0, 0, 0, v[o + 1], v[o + 2], v[o + 3], v[o + 4])
			end
			local r = n * 4
			pose[self.Order[1]] = CFrame.new(v[r + 1], v[r + 2], v[r + 3]) * pose[self.Order[1]] -- root carries translation
			if sc then
				scale = {}
				for b, bone in self.Order do
					local o = (b - 1) * 3
					scale[bone] = Vector3.new(sc[o + 1], sc[o + 2], sc[o + 3])
				end
			end
			keys[i] = { k[1], pose, scale }
		end
		self.Clips[name] = { Length = clip.Length, Keys = keys }
	end
	self.Time, self.Speed = 0, 1
	self.Scale = {} -- current local scale per bone
	self.Applied = {} -- last accumulated scale written to parts
	return self
end

local function sample(keys, frame)
	for i = 1, #keys - 1 do
		local a, b = keys[i], keys[i + 1]
		if frame <= b[1] then
			return a, b, math.clamp((frame - a[1]) / (b[1] - a[1]), 0, 1)
		end
	end
	local last = keys[#keys]
	return last, last, 0
end

-- returns the clip duration in seconds
function Animator:Play(name: string, loop: boolean, fade: number?)
	local snap, snapS = {}, {}
	for bone, m in self.Motors do
		snap[bone] = m.Transform
		snapS[bone] = self.Scale[bone] or Vector3.one
	end
	self.From, self.FromS, self.Fade, self.FadeT = snap, snapS, fade or 0.2, 0
	self.Name, self.Clip, self.Loop, self.Time = name, self.Clips[name], loop, 0
	return self.Clip.Length / self.Fps
end

function Animator:Frame()
	return self.Time * self.Fps
end

function Animator:_applyScale()
	local acc = {}
	for _, bone in self.Order do
		local par = self.Parent[bone]
		local pacc = par and acc[par] or Vector3.one
		acc[bone] = pacc * (self.Scale[bone] or Vector3.one)
		local last = self.Applied[bone]
		if not last or (last - acc[bone]).Magnitude > 1e-3 then
			self.Applied[bone] = acc[bone]
			local m = self.Motors[bone]
			m.C0 = CFrame.new(m:GetAttribute("BaseC0") * pacc)
			for _, w in self.Welds[bone] or {} do
				local p = w.Part1
				w.C0 = CFrame.new(w:GetAttribute("BaseOffset") * acc[bone]) * w.C0.Rotation
				p.Size = p:GetAttribute("BaseSize") * acc[bone] -- exact for uniform scale (all clips use uniform or axis-aligned)
			end
		end
	end
end

function Animator:Step(dt: number)
	local clip = self.Clip
	if not clip then
		return
	end
	self.Time += dt * self.Speed
	local frame = self.Time * self.Fps
	if frame >= clip.Length then
		if self.Loop then
			frame %= clip.Length
			self.Time = frame / self.Fps
		else
			frame = clip.Length
		end
	end
	local a, b, u = sample(clip.Keys, frame)
	self.FadeT += dt
	local f = if self.Fade > 0 then math.min(self.FadeT / self.Fade, 1) else 1
	local scaled = false
	for bone, m in self.Motors do
		local cf = a[2][bone]:Lerp(b[2][bone], u)
		m.Transform = if f < 1 then self.From[bone]:Lerp(cf, f) else cf
		local s = Vector3.one
		if a[3] and b[3] then
			s = a[3][bone]:Lerp(b[3][bone], u)
		end
		if f < 1 then
			s = self.FromS[bone]:Lerp(s, f)
		end
		if (s - (self.Scale[bone] or Vector3.one)).Magnitude > 1e-4 then
			scaled = true
		end
		self.Scale[bone] = s
	end
	if scaled then
		self:_applyScale()
	end
end

return Animator
