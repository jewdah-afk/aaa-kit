--!strict
-- Server boot: register services in dependency order, boot, wire players, one heartbeat.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Kit = require(ReplicatedStorage:WaitForChild("Shared").Kit)

local registry = Kit.Registry.new()
registry:add(require(script.Services.DataService))
local Economy = registry:add(require(script.Services.EconomyService)) :: any
registry:boot()

Players.PlayerAdded:Connect(function(p)
	registry:playerAdded(p)
end)
Players.PlayerRemoving:Connect(function(p)
	registry:playerRemoving(p)
end)
for _, p in Players:GetPlayers() do
	task.spawn(registry.playerAdded, registry, p)
end

RunService.Heartbeat:Connect(function(dt)
	Economy.step(dt)
end)
