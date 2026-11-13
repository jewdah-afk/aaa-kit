--!strict
-- StudMotion: the HUD v4 motion table as data, played with TweenService. It replaces
-- FrameWisp's animation layer: every row on the Figma spec board ("5 · Motion spec") is
-- one entry in MOTION, so tuning means editing numbers here, not re-importing frames.
-- Event-driven only; nothing runs per frame and nothing loops at rest except the
-- Daily badge and the selected slot (HIERARCHY.md §6).

local TweenService = game:GetService("TweenService")
local Spec = require("./StudPlateSpec")
local LuckMeter = require("./LuckMeter")
local StudPlate = require("./StudPlate")

local StudMotion = {}

local E, D = Enum.EasingStyle, Enum.EasingDirection

StudMotion.MOTION = {
	pressDown = { time = 0.04, style = E.Quad, dir = D.Out },
	pressUp = { time = 0.09, style = E.Quad, dir = D.Out },
	hover = { time = 0.12, style = E.Quad, dir = D.Out, veil = 0.06, lift = 2, glow = 0.7 },
	pressGlow = 0.3,
	windowGrow = { time = 0.2, style = E.Back, dir = D.Out, from = 0.86, peak = 1.04 },
	windowSettle = { time = 0.12, style = E.Sine, dir = D.Out },
	rowCascade = 0.04,
	currencyPop = { time = 0.12, style = E.Back, dir = D.Out, scale = 1.08 },
	badgeBob = { time = 1.2, style = E.Sine, dir = D.InOut, px = 3 },
	selectBreathe = { time = 2.8, style = E.Sine, dir = D.InOut, low = 0.6, high = 0.9 },
}

local function tween(obj: Instance, row: { time: number, style: Enum.EasingStyle, dir: Enum.EasingDirection }, props: { [string]: any }, repeats: number?, reverses: boolean?): Tween
	local t = TweenService:Create(obj, TweenInfo.new(row.time, row.style, row.dir, repeats or 0, reverses or false), props)
	t:Play()
	return t
end

-- Rows 1-2: one function wires press and hover on a plate. Keys press in and never bounce.
function StudMotion.wire(p: StudPlate.Plate, onActivate: (() -> ())?): RBXScriptConnection
	local M = StudMotion.MOTION
	local drop = math.floor(p.layout.pressDrop * p.scale + 0.5)
	local movers: { GuiObject } = { p.face }
	if p.icon then
		table.insert(movers, p.icon)
	end
	if p.label then
		table.insert(movers, p.label)
	end
	local home: { [GuiObject]: UDim2 } = {}
	for _, g in movers do
		home[g] = g.Position
	end
	local restGlow = 1 - Spec.GLOW_ALPHA

	local button = Instance.new("TextButton")
	button.Name = "Hit"
	button.Text = ""
	button.BackgroundTransparency = 1
	button.Size = UDim2.fromScale(1, 1)
	button.ZIndex = 20
	button.Parent = p.root

	local function sink(down: boolean)
		local row = if down then M.pressDown else M.pressUp
		for _, g in movers do
			tween(g, row, { Position = home[g] + UDim2.fromOffset(0, if down then drop else 0) })
		end
		tween(p.sill, row, { BackgroundTransparency = if down then 1 else 0 })
		tween(p.glow, row, { ImageTransparency = if down then 1 - M.pressGlow else restGlow })
	end

	button.MouseEnter:Connect(function()
		tween(p.veil, M.hover, { BackgroundTransparency = 1 - M.hover.veil })
		tween(p.glow, M.hover, { ImageTransparency = 1 - M.hover.glow })
	end)
	button.MouseLeave:Connect(function()
		tween(p.veil, M.hover, { BackgroundTransparency = 1 })
		tween(p.glow, M.hover, { ImageTransparency = restGlow })
		sink(false)
	end)
	button.MouseButton1Down:Connect(function()
		sink(true)
	end)
	return button.MouseButton1Up:Connect(function()
		sink(false)
		if onActivate then
			onActivate()
		end
	end)
end

-- Row 3: a window grows out of the tile that opened it. Uses a UIScale so layout is untouched.
function StudMotion.openWindow(window: GuiObject, rows: { GuiObject }?)
	local M = StudMotion.MOTION
	local sc = window:FindFirstChildOfClass("UIScale") or Instance.new("UIScale")
	sc.Scale = M.windowGrow.from
	sc.Parent = window
	window.Visible = true
	local grow = tween(sc, M.windowGrow, { Scale = M.windowGrow.peak })
	grow.Completed:Once(function()
		tween(sc, M.windowSettle, { Scale = 1 })
	end)
	for i, r in rows or {} do
		r.Visible = false
		task.delay(i * M.rowCascade, function()
			r.Visible = true
		end)
	end
end

-- Row 7: a balance pop. The odometer (ui-hud/examples/Odometer.luau) rolls the digits.
function StudMotion.currencyPop(label: GuiObject)
	local M = StudMotion.MOTION
	local sc = label:FindFirstChildOfClass("UIScale") or Instance.new("UIScale")
	sc.Parent = label
	sc.Scale = M.currencyPop.scale
	tween(sc, M.currencyPop, { Scale = 1 })
end

-- Row 8: the Daily badge, the one idle loop on the left. Returns the tween so the caller
-- can :Cancel() it when the reward is claimed.
function StudMotion.badgeBob(badge: GuiObject): Tween
	local M = StudMotion.MOTION
	return tween(badge, M.badgeBob, { Position = badge.Position - UDim2.fromOffset(0, M.badgeBob.px) }, -1, true)
end

-- Row 9: selected hotbar slot, glow breathes.
function StudMotion.selectBreathe(p: StudPlate.Plate): Tween
	local M = StudMotion.MOTION
	p.glow.ImageTransparency = 1 - M.selectBreathe.low
	return tween(p.glow, M.selectBreathe, { ImageTransparency = 1 - M.selectBreathe.high }, -1, true)
end

-- Rows 4-6: the luck counter. `ui` holds the TextLabel number (with a UIGradient), the
-- clover ImageLabel, a UIScale on the group and the rung pill's TextLabel.
export type LuckUI = {
	number: TextLabel,
	gradient: UIGradient,
	clover: ImageLabel,
	scale: UIScale,
	pill: TextLabel,
	group: CanvasGroup?,
}

local function sequence(stops: { { number | string } }): ColorSequence
	local keys = {}
	for _, st in stops do
		local r, g, b = Spec.hex(st[2] :: string)
		table.insert(keys, ColorSequenceKeypoint.new(st[1] :: number, Color3.fromRGB(r, g, b)))
	end
	return ColorSequence.new(keys)
end

function StudMotion.luck(ui: LuckUI)
	local shown, target, rung = 1, 1, 1
	local tick: thread? = nil
	local self = {}

	local function applyRung(i: number)
		local r = LuckMeter.RUNGS[i]
		ui.gradient.Color = sequence(r.stops)
		ui.pill.Text = r.name
	end
	applyRung(1)
	ui.scale.Scale = LuckMeter.RUNGS[1].scale

	local function punch(newRung: number)
		local r = LuckMeter.RUNGS[newRung]
		applyRung(newRung)
		local up = TweenService:Create(ui.scale, TweenInfo.new(LuckMeter.PUNCH_UP, E.Quad, D.Out), { Scale = r.scale * LuckMeter.PUNCH_PEAK })
		up.Completed:Once(function()
			TweenService:Create(ui.scale, TweenInfo.new(LuckMeter.PUNCH_SETTLE, E.Back, D.Out), { Scale = r.scale }):Play()
			TweenService:Create(ui.clover, TweenInfo.new(LuckMeter.PUNCH_SETTLE, E.Back, D.Out), { Rotation = 0 }):Play()
		end)
		ui.clover.Rotation = -12
		up:Play()
	end

	-- Call whenever the server-sent luck changes during a throw.
	function self.set(luck: number)
		local from = shown
		target = luck
		local crossed = LuckMeter.crossed(from, luck)
		if crossed then
			rung = crossed
			punch(crossed)
		end
		if tick then
			task.cancel(tick)
		end
		tick = task.spawn(function()
			local t0 = os.clock()
			while true do
				local t = (os.clock() - t0) / LuckMeter.TICK_TIME
				shown = LuckMeter.countUp(from, target, t)
				ui.number.Text = LuckMeter.format(shown)
				if t >= 1 then
					break
				end
				task.wait()
			end
			tick = nil
		end)
	end

	-- Ball landed: hold, then ease back to CALM size and dim (row 6).
	function self.rest()
		task.delay(LuckMeter.REST_HOLD, function()
			local info = TweenInfo.new(LuckMeter.REST_TIME, E.Quint, D.InOut)
			TweenService:Create(ui.scale, info, { Scale = LuckMeter.RUNGS[1].scale }):Play()
			if ui.group then
				TweenService:Create(ui.group, info, { GroupTransparency = 1 - LuckMeter.REST_OPACITY }):Play()
			end
		end)
	end

	-- New throw: back to ×1.00, full opacity.
	function self.reset()
		shown, target, rung = 1, 1, 1
		applyRung(1)
		ui.number.Text = LuckMeter.format(1)
		ui.scale.Scale = LuckMeter.RUNGS[1].scale
		if ui.group then
			ui.group.GroupTransparency = 0
		end
	end

	function self.rung(): number
		return rung
	end

	return self
end

return StudMotion
