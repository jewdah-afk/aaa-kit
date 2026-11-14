--!strict
-- Spring: a critically damped follower for cameras and anything that chases a target.
-- Exact for any frame length (30 and 60 fps trace the same path), never overshoots from rest,
-- and takes a starting speed, so a hand-off between two shots has no corner.

local Spring = {}

-- One axis. `targetSpeed * lead` is matched outright, so the follower trails a fast target by a
-- steady 2 * (1 - lead) * targetSpeed / stiffness instead of falling further behind.
function Spring.step(position: number, speed: number, target: number, targetSpeed: number, stiffness: number, dt: number, lead: number?): (number, number)
	dt = math.clamp(if dt ~= dt then 0 else dt, 0, 1 / 20) -- a hitch takes one capped step
	local carry = (if targetSpeed ~= targetSpeed then 0 else targetSpeed) * (lead or 0)
	local offset = position - target
	local relative = speed - carry
	local temp = (relative + stiffness * offset) * dt
	local decay = math.exp(-stiffness * dt)
	return target + (offset + temp) * decay + carry * dt, (relative - stiffness * temp) * decay + carry
end

-- Stiffness that starts loose and tightens: the camera eases into a chase instead of lurching.
function Spring.tighten(age: number, from: number, to: number, time: number): number
	local u = math.clamp(age / time, 0, 1)
	return from + (to - from) * (u * u * u * (u * (u * 6 - 15) + 10))
end

-- A short bump that opens fast and closes slowly: field of view kicks, squash on a landing.
function Spring.kick(age: number, rise: number, fall: number): number
	if age <= 0 or age >= rise + fall then
		return 0
	end
	local u = if age < rise then age / rise else 1 - (age - rise) / fall
	return u * u * u * (u * (u * 6 - 15) + 10)
end

-- Biggest change in speed per second over a list of positions sampled every `dt`. Use it to
-- compare two hand-offs: a cut or a plain lerp shows up as a spike.
function Spring.maxAccel(path: { number }, dt: number): number
	local worst = 0
	for i = 3, #path do
		worst = math.max(worst, math.abs(path[i] - 2 * path[i - 1] + path[i - 2]) / (dt * dt))
	end
	return worst
end

return Spring
