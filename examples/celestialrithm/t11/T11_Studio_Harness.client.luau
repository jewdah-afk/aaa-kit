--!strict
-- AAA-KIT / FRONTIER T11 / EXPERIMENTAL ROBLOX STUDIO HARNESS
-- Place as a LocalScript under StarterPlayerScripts.
-- Engine-facing EditableMesh + EditableImage with shared pressure state.
-- Requires creation permissions and may fail on unsupported clients.
-- No claim of 60 FPS Roblox execution until validated with the MicroProfiler.
-- Design source: aaa-kit HIERARCHY.md and docs/playbooks/figma-to-roblox-ui.md.

local Players = game:GetService("Players")
local AssetService = game:GetService("AssetService")
local RunService = game:GetService("RunService")
local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")

local INK = Color3.fromRGB(11, 12, 16)
local NX, NY = 40, 24
local IW, IH = 128, 64
local PIXEL_COUNT = IW * IH
local EI_RATE = 1 / 30 -- test 30 Hz image and 60 Hz geometry separately; user can change
local PRESS_STIFFNESS = 105
local PRESS_DAMPING = 13
local meshtime, imagetime = 0, 0
local meshsamples, imagesamples = 0, 0
local t, pressure, velocity, target, age = 0, 0, 0, 0, 0
local active = true
local material = "HYDRO"

local styles = {
    HYDRO = { low = Vector3.new(12, 80, 137), high = Vector3.new(45, 224, 249) },
    PRISM = { low = Vector3.new(79, 27, 136), high = Vector3.new(230, 85, 248) },
    SOLAR = { low = Vector3.new(139, 51, 15), high = Vector3.new(255, 207, 54) },
}

local function clamp(x: number, lo: number, hi: number): number
    return math.max(lo, math.min(hi, x))
end
local function smooth(a: number, b: number, v: number): number
    local x = clamp((v - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)
end
local function field(u: number, v: number, tick: number, p: number): number
    local edge = math.min(1 - math.abs(u), 1 - math.abs(v))
    local bevel = smooth(0, .16, edge)
    local r = math.sqrt((u - .04)^2 + (v + .06)^2)
    local dent = -.20 * p * math.exp(-(r / .48)^2)
    local ring = .075 * p * math.sin(19*r - 10*tick) * math.exp(-2.6*r)
    local gentle = .013 * math.sin(11*u + 2*tick) * math.cos(13*v - 1.4*tick)
    return .105 * bevel + dent + ring + gentle * bevel
end

local gui = Instance.new("ScreenGui")
gui.Name = "T11_HeroButton_Probe"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.Parent = playerGui
local frame = Instance.new("Frame")
frame.Name = "SquarePanel"
frame.AnchorPoint = Vector2.new(.5, .5)
frame.Position = UDim2.fromScale(.5, .5)
frame.Size = UDim2.fromOffset(600, 350)
frame.BackgroundColor3 = Color3.fromRGB(17, 28, 50)
frame.BorderColor3 = INK
frame.BorderSizePixel = 4
frame.Parent = gui
local viewport = Instance.new("ViewportFrame")
viewport.BackgroundTransparency = 1
viewport.Name = "MeshViewport"
viewport.Position = UDim2.fromOffset(12, 12)
viewport.Size = UDim2.new(1, -24, 0, 222)
viewport.Ambient = Color3.fromRGB(145, 165, 195)
viewport.LightColor = Color3.fromRGB(255, 255, 255)
viewport.LightDirection = Vector3.new(-.35, -.6, -1)
viewport.Parent = frame
local world = Instance.new("WorldModel")
world.Parent = viewport
local cam = Instance.new("Camera")
cam.CFrame = CFrame.lookAt(Vector3.new(0, 0, 6.2), Vector3.zero)
cam.Parent = viewport
viewport.CurrentCamera = cam
local status = Instance.new("TextLabel")
status.Position = UDim2.fromOffset(12, 244)
status.Size = UDim2.new(1,-24,0,36)
status.BackgroundTransparency = 1
status.TextColor3 = Color3.fromRGB(215,233,252)
status.TextXAlignment = Enum.TextXAlignment.Left
status.Font = Enum.Font.Code
status.TextSize = 14
status.Text = "Preparing EditableMesh / EditableImage..."
status.Parent = frame
local button = Instance.new("TextButton")
button.Name = "InputAndLabel"
button.Position = viewport.Position
button.Size = viewport.Size
button.BackgroundTransparency = 1
button.Text = "▶ PLAY"
button.TextColor3 = Color3.fromRGB(255,255,255)
button.TextStrokeColor3 = INK
button.TextStrokeTransparency = 0
button.Font = Enum.Font.GothamBlack
button.TextSize = 48
button.ZIndex = 5
button.Parent = frame
button.MouseButton1Down:Connect(function() target = 1 end)
button.MouseButton1Up:Connect(function() target = 0 end)
button.MouseLeave:Connect(function() target = 0 end)

local function addSelect(name: string, index: number)
    local b=Instance.new("TextButton")
    b.Name="Material_"..name
    b.Position=UDim2.fromOffset(12+(index-1)*194,292)
    b.Size=UDim2.fromOffset(181,42)
    b.BackgroundColor3=Color3.fromRGB(35,58,88)
    b.BorderColor3=INK
    b.BorderSizePixel=3
    b.Text=name
    b.TextColor3=Color3.new(1,1,1)
    b.TextSize=20
    b.Font=Enum.Font.GothamBold
    b.Parent=frame
    b.Activated:Connect(function() material=name end)
end
addSelect("HYDRO",1)
addSelect("PRISM",2)
addSelect("SOLAR",3)

-- Actual runtime engine objects; recover to functional GUI if permissions deny allocation.
local ok, created = pcall(function() return AssetService:CreateEditableMesh() end)
if not ok or not created then
    status.Text = "EditableMesh unavailable. GUI remains operable; enable Mesh/Image APIs."
    return
end
local mesh = created :: EditableMesh
local ids: {number} = {}
local uvIds: {number} = {}
local rest: {Vector3} = {}
local function index(i: number, j: number): number
    return j*(NX+1)+i+1
end
for j=0,NY do
    for i=0,NX do
        local u=i/NX*2-1
        local v=j/NY*2-1
        ids[#ids+1]=mesh:AddVertex(Vector3.new(u*2.9,v*1.16,0))
        uvIds[#uvIds+1]=mesh:AddUV(Vector2.new(i/NX, 1-j/NY))
        rest[#rest+1]=Vector3.new(u,v,0)
    end
end
for j=0,NY-1 do
    for i=0,NX-1 do
        local a,b,c,d=index(i,j),index(i+1,j),index(i,j+1),index(i+1,j+1)
        local f1=mesh:AddTriangle(ids[a],ids[b],ids[d])
        local f2=mesh:AddTriangle(ids[a],ids[d],ids[c])
        mesh:SetFaceUVs(f1,{uvIds[a],uvIds[b],uvIds[d]})
        mesh:SetFaceUVs(f2,{uvIds[a],uvIds[d],uvIds[c]})
    end
end
local displayOK, result = pcall(function()
    return AssetService:CreateMeshPartAsync(Content.fromObject(mesh))
end)
if not displayOK or not result then
    status.Text = "MeshPart creation failed; inspect Studio Output."
    mesh:Destroy()
    return
end
local part = result :: MeshPart
part.Name = "LiveDeformedMembrane"
part.Anchored = true
part.CanCollide = false
part.Color = Color3.fromRGB(44,183,237)
part.Parent = world

local image: EditableImage? = nil
local imageOK, imageResult=pcall(function()
    return AssetService:CreateEditableImage({Size=Vector2.new(IW,IH)})
end)
if imageOK and imageResult then
    image=imageResult :: EditableImage
    -- Actual procedural EditableImage mapped onto actual UV-mapped EditableMesh.
    part.TextureContent=Content.fromObject(image)
else
    status.Text = "Mesh only fallback: EditableImage allocation unavailable."
end
local pixelBuffer=buffer.create(PIXEL_COUNT*4)
local function imageFrame(dt: number)
    if not image then return end
    local style=styles[material]
    for y=0,IH-1 do
        local v=y/(IH-1)*2-1
        for x=0,IW-1 do
            local u=x/(IW-1)*2-1
            local z=field(u,v,age,pressure)
            local caust=math.cos(17.5*u+9*v+7.5*z+3.4*age+3*math.sin(9*v-2.3*age+6.5*z))
            local caust2=math.cos(22*v-12*u-2.5*age+14*z)
            local diffuse=clamp(.51+.23*caust+.20*caust2,0,1)
            -- Protect the glyph region from optical clutter using a rounded power mask.
            local protected=math.exp(-((u/.57)^8+(v/.56)^8))
            local intensity=diffuse*(1-.45*protected)+.30*protected
            local lo,hi=style.low,style.high
            local r=math.floor(clamp(lo.X+(hi.X-lo.X)*intensity,0,255))
            local g=math.floor(clamp(lo.Y+(hi.Y-lo.Y)*intensity,0,255))
            local b=math.floor(clamp(lo.Z+(hi.Z-lo.Z)*intensity,0,255))
            local offset=(y*IW+x)*4
            buffer.writeu8(pixelBuffer,offset,r)
            buffer.writeu8(pixelBuffer,offset+1,g)
            buffer.writeu8(pixelBuffer,offset+2,b)
            buffer.writeu8(pixelBuffer,offset+3,255)
        end
    end
    image:WritePixelsBuffer(Vector2.zero,Vector2.new(IW,IH),pixelBuffer)
end

local acc = 0
local n=0
local connection
connection=RunService.RenderStepped:Connect(function(dt: number)
    if not active then return end
    dt=math.min(dt,1/20)
    velocity=(velocity+(target-pressure)*PRESS_STIFFNESS*dt)*math.exp(-PRESS_DAMPING*dt)
    pressure+=velocity*dt
    age+=dt
    local a=os.clock()
    -- no topology rebuild; only visual vertex positions change.
    for k,id in ipairs(ids) do
        local pos=rest[k]
        mesh:SetPosition(id,Vector3.new(pos.X*2.9,pos.Y*1.16,field(pos.X,pos.Y,age,pressure)))
    end
    meshtime+= (os.clock()-a)*1000
    meshsamples+=1
    acc+=dt
    if acc>=EI_RATE then
        acc-=EI_RATE
        a=os.clock()
        imageFrame(dt)
        imagetime+=(os.clock()-a)*1000
        imagesamples+=1
    end
    n+=1
    if n%60==0 then
        status.Text=string.format("STUDIO PROBE  |  FPS %.1f  |  mesh %.2f ms  |  EI %.2f ms  |  %s  |  pressure %.2f",1/math.max(dt,.0001),meshtime/math.max(meshsamples,1),imagetime/math.max(imagesamples,1),material,pressure)
        meshtime=0; imagetime=0;meshsamples=0;imagesamples=0
    end
end)
-- NOTE: Script-side timings exclude GPU uploads, draw calls and presentation delay.
-- Capture MicroProfiler with a physical phone and verify visual output independently.
