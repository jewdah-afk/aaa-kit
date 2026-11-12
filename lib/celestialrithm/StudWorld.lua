-- Deterministic procedural stud-world CHUNK DATA generator; no Roblox API dependency.
-- Terrain augmentation only: preserve existing authored maps as authoritative.
local M={}
local function hash(x,z,seed)
 local n=math.sin(x*127.1+z*311.7+seed*74.7)*43758.5453
 return n-math.floor(n)
end
function M.sample(x,z,seed,opts)
 opts=opts or {}; local step=opts.step or 2
 -- Tiered block geometry, broad terracing and low-frequency height. Avoid realistic noise soup.
 local n=math.sin(x*.075+seed*.31)*.50+math.cos(z*.071-seed*.19)*.34 + (hash(math.floor(x/8),math.floor(z/8),seed)-.5)*.19
 local h=math.floor((opts.base or 8)+n*7)
 h=math.floor(h/step)*step
 local roadWidth=opts.roadWidth or 5
 if math.abs(x)<roadWidth then h=opts.roadHeight or 4 end
 local biome = h>=12 and 'snow' or (h>=8 and 'frost' or 'stone')
 return {height=h,biome=biome,studs=true,road=math.abs(x)<roadWidth}
end
function M.chunk(cx,cz,seed,opts)
 opts=opts or {}; local side=opts.side or 16; local tile=opts.tile or 4
 local cells={};local props={};local total=0
 for z=0,side-1 do
  for x=0,side-1 do
   local wx=(cx*side+x)*tile;local wz=(cz*side+z)*tile
   local q=M.sample(wx,wz,seed,opts)
   cells[#cells+1]={x=wx,z=wz,height=q.height,biome=q.biome,road=q.road}
   total+=1
   -- sparse, grounded props. Existing world props are not replaced.
   if not q.road and hash(wx,wz,seed+11)>.971 then
    props[#props+1]={x=wx,z=wz,y=q.height,kind=q.biome=='snow' and 'snow_pine' or 'frost_pine'}
   end
  end
 end
 return {cx=cx,cz=cz,seed=seed,cellCount=total,cells=cells,props=props,topology='square-stud-terraced'}
end
return M
