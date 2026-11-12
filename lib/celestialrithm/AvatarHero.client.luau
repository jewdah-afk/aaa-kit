-- Experimental cosmetic-only avatar source and aura sockets. Studio playtest required.
-- Preserve exact existing appearance by operating on a Character clone, not guessing a new mesh.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local player = Players.LocalPlayer
local function attachHero(character)
    local root = character:FindFirstChild("HumanoidRootPart")
    if not root then return end
    local old = root:FindFirstChild("CelestialrithmAura")
    if old then old:Destroy() end
    local att = Instance.new("Attachment")
    att.Name = "CelestialrithmAura"
    att.Position = Vector3.new(0, -1.7, 0)
    att.Parent = root
    local emit = Instance.new("ParticleEmitter")
    emit.Name = "HydroOrbital"
    emit.Rate = 0 -- at rest no particle spam
    emit.Lifetime = NumberRange.new(0.25, 0.5)
    emit.Speed = NumberRange.new(0.3, 0.8)
    emit.Size = NumberSequence.new(0.15)
    emit.Color = ColorSequence.new(Color3.fromRGB(55, 215, 255))
    emit.LightEmission = 0.35
    emit.Parent = att
    -- Call :Emit(...) on an authorized cosmetic event, rate-limited and reduced-motion aware.
    -- Never replace the avatar character's real mesh to achieve a cosmetic effect.
    return emit
end
local function onCharacter(character)
    character:WaitForChild("HumanoidRootPart", 10)
    attachHero(character)
end
player.CharacterAdded:Connect(onCharacter)
if player.Character then onCharacter(player.Character) end
