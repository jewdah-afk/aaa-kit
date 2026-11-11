--!strict
-- Client boot: a local "changed" signal fed by the server, components bound by tag.
-- Replication here is a placeholder: replace with your state-sync library of choice.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Kit = require(ReplicatedStorage:WaitForChild("Shared").Kit)
local CoinCounter = require(script.Components.CoinCounter)

local changed = Kit.Signal.new()
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local stateEvent = remotes:WaitForChild("State") :: RemoteEvent
stateEvent.OnClientEvent:Connect(function(key: string, value: any)
	changed:fire(key, value)
end)

CoinCounter.bind(changed)
