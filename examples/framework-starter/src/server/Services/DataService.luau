--!strict
-- @title DataService
-- Owns saves: load with retries, session lock, reconcile against the template, autosave,
-- save on leave and on shutdown. Read-only if a load fails, so a bad load never overwrites
-- a good save. Swap the DataStore calls for ProfileStore if you prefer; keep the rules.

local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Kit = require(Shared.Kit)
local Save = require(Shared.Systems.Save)

local DataService = { name = "DataService" }
DataService.changed = Kit.Signal.new() :: any -- (player, key, value)

local STORE_NAME = "Saves_v1"
local LOCK_SECONDS = 1800
local AUTOSAVE = 120
local RETRIES = 4

local store: DataStore = DataStoreService:GetDataStore(STORE_NAME)
local saves: { [Player]: any } = {}
local readOnly: { [Player]: boolean } = {}

local function key(player: Player): string
	return `u_{player.UserId}`
end

local function withRetry<T>(fn: () -> T): (boolean, T | string)
	local lastErr: any
	for attempt = 1, RETRIES do
		local ok, res = pcall(fn)
		if ok then
			return true, res
		end
		lastErr = res
		task.wait(2 ^ attempt)
	end
	return false, tostring(lastErr)
end

local function load(player: Player)
	local jobId = game.JobId
	local ok, res = withRetry(function()
		return store:UpdateAsync(key(player), function(old: any)
			local data = Save.reconcile(old)
			local lock = data._lock
			if lock and lock.job ~= jobId and os.time() - lock.at < LOCK_SECONDS then
				return nil -- another server holds it; don't write
			end
			data._lock = { job = jobId, at = os.time() }
			return data
		end)
	end)
	if not ok or res == nil then
		warn(`[DataService] load failed for {player.UserId}; session is read-only`)
		readOnly[player] = true
		saves[player] = Save.new()
		return
	end
	saves[player] = res
end

local function write(player: Player, release: boolean)
	local data = saves[player]
	if not data or readOnly[player] then
		return
	end
	data._lock = if release then nil else { job = game.JobId, at = os.time() }
	withRetry(function()
		return store:UpdateAsync(key(player), function()
			return data
		end)
	end)
end

function DataService.get(player: Player): any
	return saves[player]
end

function DataService.start(_registry: any)
	-- forward server-side changes to the owning client only
	local state = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("State") :: RemoteEvent
	DataService.changed:connect(function(player: Player, k: string, value: any)
		state:FireClient(player, k, value)
	end)
	task.spawn(function()
		while true do
			task.wait(AUTOSAVE)
			for player in saves do
				task.spawn(write, player, false)
			end
		end
	end)
	game:BindToClose(function()
		if RunService:IsStudio() then
			return
		end
		for player in saves do
			task.spawn(write, player, true)
		end
		task.wait(3)
	end)
end

function DataService.playerAdded(player: Player)
	load(player)
end

function DataService.playerRemoving(player: Player)
	write(player, true)
	saves[player] = nil
	readOnly[player] = nil
end

return DataService
