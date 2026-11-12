--!strict
-- Optional hero-only EditableMesh under-face behind the existing painted GUI keycap.
-- No icon, label, ink or UI textures are modified. Fixed topology: 13x13 => 169 vertices, 288 triangles.
-- Call bridge:update(sim) only while sim.active, not every RenderStepped on an idle HUD.
-- Requires Roblox Studio editable-mesh permission; creation may return nil.
local AssetService=game:GetService('AssetService')
local Bridge={}
Bridge.__index=Bridge
function Bridge.new(parent:Instance, size:number?):any
 local cells=12
 local em=AssetService:CreateEditableMesh()
 if em==nil then return nil,'EditableMesh unavailable (permission/memory)' end
 local vertexIds={}
 local normals={}
 local uvIds={}
 local tris={}
 local s=size or 2
 for y=0,cells do
  for x=0,cells do
   local u,v=x/cells,y/cells
   local px=(u-0.5)*s;local pz=(v-0.5)*s
   table.insert(vertexIds,em:AddVertex(Vector3.new(px,0,pz)))
   table.insert(normals,em:AddNormal(Vector3.new(0,1,0)))
   table.insert(uvIds,em:AddUV(Vector2.new(u,v)))
  end
 end
 local n=cells+1
 for y=0,cells-1 do
  for x=0,cells-1 do
   local a=y*n+x+1;local b=a+1;local c=a+n;local d=c+1
   for _,tri in {{a,c,b},{b,c,d}} do
    local f=em:AddTriangle(vertexIds[tri[1]],vertexIds[tri[2]],vertexIds[tri[3]])
    em:SetFaceNormals(f,{normals[tri[1]],normals[tri[2]],normals[tri[3]]})
    em:SetFaceUVs(f,{uvIds[tri[1]],uvIds[tri[2]],uvIds[tri[3]]})
   end
  end
 end
 local ok,part=pcall(function()
  return AssetService:CreateMeshPartAsync(Content.fromObject(em),{CollisionFidelity=Enum.CollisionFidelity.Box})
 end)
 if not ok or part==nil then em:Destroy();return nil,'MeshPart creation failed' end
 part.Anchored=true;part.CanCollide=false;part.CanTouch=false;part.CanQuery=false
 part.Material=Enum.Material.SmoothPlastic
 part.Color=Color3.fromRGB(55,138,184)
 part.Parent=parent
 return setmetatable({mesh=em,part=part,ids=vertexIds,size=s,cells=cells,lastActive=true},Bridge)
end
function Bridge.update(self:any,sim:any)
 if not sim.active then
  if not self.lastActive then return end
  self.lastActive=false
 else self.lastActive=true end
 local n=self.cells;local s=self.size
 for y=0,n do for x=0,n do
  local u=x/n;local v=y/n
  local z=sim.z[math.floor(v*(sim.n-1)+0.5)*sim.n+math.floor(u*(sim.n-1)+0.5)+1]
  local i=y*(n+1)+x+1
  self.mesh:SetPosition(self.ids[i],Vector3.new((u-.5)*s,z*.13,(v-.5)*s))
 end end
 -- Visual updates are immediate; do NOT regenerate collision geometry here.
end
function Bridge.destroy(self:any)
 self.part:Destroy();self.mesh:Destroy()
end
return Bridge
