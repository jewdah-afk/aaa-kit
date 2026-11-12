--!strict
-- Additive Roblox adapter for EXISTING original button art (never replaces Image content).
-- Install in a LocalScript with siblings FlatKeyPhysics and FlatKeyHierarchy ModuleScripts.
-- For each button, place the existing icon/label above a clipped FX overlay. Existing keycap geometry stays in Figma.
-- Explicit opt-in attributes: Set Attribute "FlatFX"=true, "FXRole"="shop"|"upgrades"|"index"|"animals"|"daily".
-- Studio execution still required. This code is an adapter candidate, not claimed as validated on-device.
local Players=game:GetService('Players')
local RunService=game:GetService('RunService')
local AssetService=game:GetService('AssetService')
local Physics=require(script.Parent.FlatKeyPhysics)
local Hierarchy=require(script.Parent.FlatKeyHierarchy)
local screen=Players.LocalPlayer:WaitForChild('PlayerGui')
local sims={}
local effects={}
local owner:string?=nil
local activeCount=0
local atlas=AssetService:CreateEditableImage({Size=Vector2.new(512,512)})
if not atlas then warn('FlatStudReactor: EditableImage budget exhausted; existing UI remains unchanged');return end
-- One texture, one display refresh; each active button uses a reserved 96x96 atlas region.
local slots={{0,0},{104,0},{208,0},{312,0},{416,0}}
local images={}
local stage=buffer.create(96*96*4)
local function pack(r:number,g:number,b:number,a:number):number
 return bit32.bor(r,bit32.lshift(g,8),bit32.lshift(b,16),bit32.lshift(a,24))
end
local function mount(button:GuiButton,role:string,slot:number)
 local overlay=Instance.new('ImageLabel')
 overlay.Name='fx/liquid-under-face';overlay.BackgroundTransparency=1
 overlay.Size=UDim2.fromScale(1,1);overlay.Position=UDim2.fromScale(0,0)
 overlay.ImageContent=Content.fromObject(atlas)
 overlay.ImageRectOffset=Vector2.new(slots[slot][1],slots[slot][2]);overlay.ImageRectSize=Vector2.new(96,96)
 overlay.ImageTransparency=1;overlay.ZIndex=button.ZIndex+1;overlay.Parent=button
 -- Important: the existing icon/text should be ZIndex >= overlay.ZIndex+1; inspect before enabling.
 local sim=Physics.new(17)
 sims[button]=sim
 effects[button]={overlay=overlay,slot=slot,role=role,intensity=0}
 button.Activated:Connect(function()
  owner=button.Name
  Physics.impulse(sim,0.5,0.38,-3,0.22)
  effects[button].intensity=1
 end)
end
for _,obj in screen:GetDescendants() do
 if obj:IsA('GuiButton') and obj:GetAttribute('FlatFX')==true then
  local role=obj:GetAttribute('FXRole')
  if typeof(role)=='string' and #images<#slots then
   table.insert(images,obj);mount(obj,role,#images)
  end
 end
end
local frame=0
local function drawOne(button:GuiButton,entry:any)
 local sim=sims[button];local weight=Hierarchy.weight(button.Name,owner,2,false)
 local c=entry.role=='upgrades' and {155,73,245} or entry.role=='animals' and {246,154,32} or entry.role=='index' and {32,167,248} or entry.role=='daily' and {89,224,42} or {247,61,100}
 for y=0,95 do for x=0,95 do
  local u=x/95;local v=y/95
  local energy=Physics.caustic(sim,u,v)
  local mask=Hierarchy.mask(u,v)
  local amp=math.floor(80*weight*mask*energy)
  local a=math.floor(amp*math.clamp(entry.intensity,0,1))
  buffer.writeu32(stage,(y*96+x)*4,pack(c[1],c[2],c[3],a))
 end end
 atlas:WritePixelsBuffer(Vector2.new(slots[entry.slot][1],slots[entry.slot][2]),Vector2.new(96,96),stage)
 entry.overlay.ImageTransparency=weight<=0 and 1 or 0
end
RunService.RenderStepped:Connect(function(dt)
 frame+=1
 -- Restricted single update to one button per frame, instead of updating 5 separate EI instances.
 if #images==0 then return end
 local selected=nil
 for _,button in images do
  local sim=sims[button]
  Physics.step(sim,dt)
  local e=effects[button];e.intensity=math.max(0,e.intensity-dt*2.8)
  if button.Name==owner and e.intensity>0 then selected=button end
 end
 if selected and frame%2==0 then drawOne(selected,effects[selected]) end
 if not selected then
  for _,button in images do effects[button].overlay.ImageTransparency=1 end
  owner=nil
 end
end)
