--!strict
-- Compile-checks every .luau / .lua file under the given folders (default: the repo).
-- Also compiles Luau code blocks inside Markdown (```lua / ```luau) so skill examples
-- can't rot. A block that starts with `-- snippet` is skipped (partial code on purpose).
-- Usage: lune run tools/check_luau.luau [dir ...]

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local process = require("@lune/process")

local roots = if #process.args > 0 then process.args else { "." }
local checked, failed = 0, 0
local SKIP = { [".git"] = true, ["node_modules"] = true, ["Packages"] = true }

local function compile(label: string, source: string)
	checked += 1
	local ok, err = pcall(luau.compile, source)
	if not ok then
		failed += 1
		print("FAIL", label, err)
	end
end

local function scanMarkdown(path: string, text: string)
	local line = 0
	local inBlock, lang, buf, start = false, "", {}, 0
	for raw in (text .. "\n"):gmatch("([^\n]*)\n") do
		line += 1
		if not inBlock then
			local l = raw:match("^%s*```%s*(%a+)%s*$")
			if l then
				inBlock, lang, buf, start = true, l:lower(), {}, line
			end
		elseif raw:match("^%s*```%s*$") then
			inBlock = false
			if (lang == "lua" or lang == "luau") and not (buf[1] or ""):match("^%s*%-%-%s*snippet") then
				compile(`{path}:{start}`, table.concat(buf, "\n"))
			end
		else
			table.insert(buf, raw)
		end
	end
end

local function walk(dir: string)
	for _, name in fs.readDir(dir) do
		local path = dir .. "/" .. name
		if fs.isDir(path) then
			if not SKIP[name] then
				walk(path)
			end
		elseif name:match("%.luau?$") then
			compile(path, fs.readFile(path))
		elseif name:match("%.md$") then
			scanMarkdown(path, fs.readFile(path))
		end
	end
end

for _, root in roots do
	if fs.isFile(root) then
		if root:match("%.md$") then
			scanMarkdown(root, fs.readFile(root))
		else
			compile(root, fs.readFile(root))
		end
	else
		walk(root)
	end
end

print(`{checked} checked, {failed} failed`)
process.exit(failed == 0 and 0 or 1)
