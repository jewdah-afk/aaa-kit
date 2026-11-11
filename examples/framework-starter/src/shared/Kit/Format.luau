--!strict
-- Format: number formatting for the HUD.
-- short(1234) -> "1.23K", short(1.5e9) -> "1.50B". Three significant digits, stable width.

local Format = {}

Format.SUFFIXES = table.freeze({ "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" })

local function trim(n: number): string
	if n >= 100 then
		return string.format("%d", math.floor(n))
	elseif n >= 10 then
		return string.format("%.1f", math.floor(n * 10) / 10)
	end
	return string.format("%.2f", math.floor(n * 100) / 100)
end

-- Short form with suffix. Floors instead of rounding, so the HUD never shows more than you have.
function Format.short(n: number): string
	if n ~= n then
		return "NaN"
	end
	if n < 0 then
		return "-" .. Format.short(-n)
	end
	if n < 1000 then
		return tostring(math.floor(n))
	end
	local i = 1
	while n >= 1000 and i < #Format.SUFFIXES do
		n /= 1000
		i += 1
	end
	if n >= 1000 then -- past the last suffix: scientific
		return string.format("%.2e", n * 1000 ^ (i - 1))
	end
	return trim(n) .. Format.SUFFIXES[i]
end

-- Full form with thousands separators: 1234567 -> "1,234,567".
function Format.commas(n: number): string
	local s = tostring(math.floor(math.abs(n)))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	if out:sub(1, 1) == "," then
		out = out:sub(2)
	end
	return (n < 0 and "-" or "") .. out
end

-- Seconds to "1h 02m", "3m 05s" or "12s".
function Format.duration(seconds: number): string
	local s = math.max(0, math.floor(seconds))
	local h, m = s // 3600, (s % 3600) // 60
	if h > 0 then
		return string.format("%dh %02dm", h, m)
	elseif m > 0 then
		return string.format("%dm %02ds", m, s % 60)
	end
	return `{s}s`
end

return Format
