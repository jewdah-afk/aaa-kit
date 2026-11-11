--!strict
-- RarityStyle: the rarity ladder (HIERARCHY.md §7) as data, plus an applier for Roblox UI.
-- Each tier adds exactly one behaviour on top of the one below, so the ladder reads.
-- The applier uses UIStroke + UIGradient (cheap, no images) and a rotation tween for motion.

local RarityStyle = {}

export type Style = {
	name: string,
	color: { number }, -- 8-bit RGB
	stroke: number, -- px
	sweep: boolean, -- a shine band passes every few seconds (Rare+)
	spin: boolean, -- rotating conic edge (Epic+)
	sparks: boolean, -- sparks run along the edge (Legendary+)
	rainbow: boolean, -- full-spectrum edge (Mythic+)
	glitch: boolean, -- glitch slices + hidden tier until reveal (Secret)
	material: string,
	adds: string, -- the one new behaviour this tier introduces
}

RarityStyle.TIERS = table.freeze({
	{ name = "Common", color = { 154, 164, 178 }, stroke = 2, sweep = false, spin = false, sparks = false, rainbow = false, glitch = false, material = "flat", adds = "static border" },
	{ name = "Uncommon", color = { 79, 209, 122 }, stroke = 2, sweep = false, spin = false, sparks = false, rainbow = false, glitch = false, material = "satin", adds = "inner highlight" },
	{ name = "Rare", color = { 90, 180, 255 }, stroke = 3, sweep = true, spin = false, sparks = false, rainbow = false, glitch = false, material = "brushed", adds = "shine sweep" },
	{ name = "Epic", color = { 178, 92, 255 }, stroke = 3, sweep = true, spin = true, sparks = false, rainbow = false, glitch = false, material = "glass", adds = "rotating edge" },
	{ name = "Legendary", color = { 255, 176, 46 }, stroke = 3, sweep = true, spin = true, sparks = true, rainbow = false, glitch = false, material = "chrome", adds = "edge sparks + glow" },
	{ name = "Mythic", color = { 255, 61, 127 }, stroke = 4, sweep = true, spin = true, sparks = true, rainbow = true, glitch = false, material = "holo", adds = "rainbow edge" },
	{ name = "Secret", color = { 255, 255, 255 }, stroke = 2, sweep = true, spin = true, sparks = true, rainbow = true, glitch = true, material = "void", adds = "glitch + hidden reveal" },
} :: { Style })

local FLAGS = { "sweep", "spin", "sparks", "rainbow", "glitch" }

-- Number of motion behaviours a tier uses (for the "each tier adds one" check).
function RarityStyle.behaviours(s: Style): number
	local n = 0
	for _, f in FLAGS do
		if (s :: any)[f] then
			n += 1
		end
	end
	return n
end

function RarityStyle.get(tier: number): Style
	return RarityStyle.TIERS[math.clamp(tier, 1, #RarityStyle.TIERS)]
end

-- Roblox: style a Frame as a rarity slot. Returns a cleanup function.
-- (Not run in lune; compile-checked only.)
function RarityStyle.apply(frame: GuiObject, tier: number): () -> ()
	local TweenService = (game :: any):GetService("TweenService")
	local s = RarityStyle.get(tier)
	local c = Color3.fromRGB(s.color[1], s.color[2], s.color[3])
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = s.stroke
	stroke.Color = c
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Parent = frame
	local tweens = {}
	if s.sweep or s.spin or s.rainbow then
		local g = Instance.new("UIGradient")
		if s.rainbow then
			g.Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 61, 127)),
				ColorSequenceKeypoint.new(0.25, Color3.fromRGB(255, 176, 46)),
				ColorSequenceKeypoint.new(0.5, Color3.fromRGB(79, 209, 122)),
				ColorSequenceKeypoint.new(0.75, Color3.fromRGB(90, 180, 255)),
				ColorSequenceKeypoint.new(1, Color3.fromRGB(178, 92, 255)),
			})
		else
			g.Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, c),
				ColorSequenceKeypoint.new(0.5, Color3.new(1, 1, 1)),
				ColorSequenceKeypoint.new(1, c),
			})
		end
		g.Parent = stroke
		if s.spin then
			local tw = TweenService:Create(g, TweenInfo.new(if s.rainbow then 2 else 4, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, -1), { Rotation = 360 })
			tw:Play()
			table.insert(tweens, tw)
		else -- sweep only: slide the gradient across every 2.5 s
			g.Offset = Vector2.new(-1, 0)
			local tw = TweenService:Create(g, TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, false, 1.7), { Offset = Vector2.new(1, 0) })
			tw:Play()
			table.insert(tweens, tw)
		end
	end
	return function()
		for _, tw in tweens do
			tw:Cancel()
		end
		stroke:Destroy()
	end
end

return RarityStyle
