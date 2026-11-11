--!strict
-- @title EconomyService
-- Service template: one table, explicit lifecycle (init/start/playerAdded/playerRemoving),
-- per-player state cleared on leave, every remote argument validated on the server.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Kit = require(Shared.Kit)
local Upgrades = require(Shared.Content.Upgrades)
local Economy = require(Shared.Systems.Economy)
local Unlocks = require(Shared.Systems.Unlocks)
local Automations = require(Shared.Systems.Automations)

local EconomyService = { name = "EconomyService" }

local DataService: any -- looked up in init
local BuyRemote: RemoteFunction
local TapRemote: RemoteEvent
local tapLimit = Kit.Guard.rate(0.08) -- 12.5 taps per second, matches a fast human
local buyLimit = Kit.Guard.rate(0.2)
local automations: { [Player]: any } = {}

local MAX_BUY = 1000

local function onTap(player: Player)
	if not tapLimit(player) then
		return
	end
	local save = DataService.get(player)
	if not save then
		return
	end
	local tap = Economy.rates(save)
	save.coins += tap
	save.stats.coinsEarned += tap
	for _, id in Unlocks.refresh(save) do
		DataService.changed:fire(player, "unlocked", id)
	end
	DataService.changed:fire(player, "coins", save.coins)
end

local function onBuy(player: Player, id: unknown, n: unknown): any
	-- 1. shape: whitelist the key, bound the count, reject NaN/inf
	if not Kit.Guard.oneOf(id, Upgrades) or not Kit.Guard.count(n, MAX_BUY) then
		return { ok = false, reason = "bad request" }
	end
	-- 2. rate
	if not buyLimit(player) then
		return { ok = false, reason = "slow down" }
	end
	-- 3. state: the server's copy is the only truth
	local save = DataService.get(player)
	if not save then
		return { ok = false, reason = "not loaded" }
	end
	local result = Economy.buy(save, id :: string, n :: number, function(u)
		return Unlocks.isUnlocked(save, u)
	end)
	if result.ok then
		DataService.changed:fire(player, "upgrades", id)
	end
	return result
end

function EconomyService.init(registry: any)
	DataService = registry:get("DataService")
	local remotes = ReplicatedStorage:WaitForChild("Remotes")
	BuyRemote = remotes:WaitForChild("Buy") :: RemoteFunction
	TapRemote = remotes:WaitForChild("Tap") :: RemoteEvent
end

function EconomyService.start(_registry: any)
	BuyRemote.OnServerInvoke = onBuy
	TapRemote.OnServerEvent:Connect(onTap)
end

function EconomyService.playerAdded(player: Player)
	local auto = Automations.new()
	auto:add({
		id = "passive_income",
		interval = 1,
		maxCatchUp = 5,
		run = function(save, elapsed)
			local _, perSecond = Economy.rates(save)
			local gain = perSecond * elapsed
			save.coins += gain
			save.stats.coinsEarned += gain
			save.stats.playSeconds += elapsed
		end,
	})
	automations[player] = auto
end

function EconomyService.playerRemoving(player: Player)
	automations[player] = nil
end

-- Called by the single server heartbeat in init.server.luau.
function EconomyService.step(dt: number)
	for player, auto in automations do
		local save = DataService.get(player)
		if save then
			auto:tick(save, dt)
		end
	end
end

return EconomyService
