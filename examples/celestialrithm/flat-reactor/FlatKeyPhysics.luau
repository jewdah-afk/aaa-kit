--!strict
-- Headless pure Luau: 2D coupled pressure waves driving both face material and optional EditableMesh deformation.
-- Native APIs are deliberately absent. Can be tested via lune; fixed allocations after new().
local M = {}
M.__index = M

export type Sim = {
 n:number, h:number, v:number, k:number, damp:number,
 z:{number}, vel:{number}, next:{number}, time:number,
 active:boolean, energy:number,
}
local function ix(n:number,x:number,y:number):number return (y-1)*n+x end
function M.new(n:number):Sim
 assert(n>=5 and n<=65, 'grid bounds')
 local len=n*n
 local a=table.create(len,0)
 local b=table.create(len,0)
 local c=table.create(len,0)
 return {n=n,h=1/(n-1),v=0,k=25,damp=5.5,z=a,vel=b,next=c,time=0,active=false,energy=0}
end
function M.impulse(s:Sim, u:number,v:number,force:number,radius:number?)
 local n=s.n; local rad=math.max(0.03,radius or 0.13)
 for y=1,n do
  local dy=(y-1)/(n-1)-v
  for x=1,n do
   local dx=(x-1)/(n-1)-u
   local r2=(dx*dx+dy*dy)/(rad*rad)
   local i=ix(n,x,y)
   s.vel[i]+=force*math.exp(-r2*2)
  end
 end
 s.active=true
end
function M.step(s:Sim, dt:number)
 -- Stable-ish semi-implicit 5-point membrane under bounded 120 Hz substeps.
 -- Unlike full solid XPBD this is a membrane approximation, NOT volumetric conservation.
 dt=math.clamp(dt,0,0.05)
 local n=s.n;local count=math.max(1,math.ceil(dt/(1/120)));local h=dt/count
 local hh=1/((s.h*n)^2) -- normalized stiffness independent of resolution
 for _=1,count do
  local energy=0
  for y=1,n do for x=1,n do
   local i=ix(n,x,y)
   if x==1 or y==1 or x==n or y==n then s.next[i]=0;s.vel[i]=0
   else
    local z=s.z
    local lap=(z[i-1]+z[i+1]+z[i-n]+z[i+n]-4*z[i])*hh
    local v=(s.vel[i]+h*s.k*lap)/(1+h*s.damp)
    s.vel[i]=v
    s.next[i]=math.clamp(z[i]+h*v,-0.32,0.32)
    energy+=math.abs(v)+math.abs(s.next[i])
   end
  end end
  s.z,s.next=s.next,s.z
  s.energy=energy/(n*n)
 end
 s.active=s.energy>0.00008
 s.time+=dt
end
function M.sample(s:Sim,u:number,v:number):(number,number,number)
 local n=s.n;local fx=math.clamp(u,0,1)*(n-1)+1;local fy=math.clamp(v,0,1)*(n-1)+1
 local x=math.min(n-1,math.floor(fx));local y=math.min(n-1,math.floor(fy))
 local tx=fx-x;local ty=fy-y;local i=ix(n,x,y)
 local z=s.z;local a=z[i]*(1-tx)+z[i+1]*tx;local b=z[i+n]*(1-tx)+z[i+n+1]*tx
 local height=a*(1-ty)+b*ty
 local l=z[ix(n,math.max(1,x-1),y)];local r=z[ix(n,math.min(n,x+1),y)]
 local t=z[ix(n,x,math.max(1,y-1))];local bottom=z[ix(n,x,math.min(n,y+1))]
 return height,(r-l)*0.5*n,(bottom-t)*0.5*n
end
-- Stylized caustic optical carrier, derived from local membrane gradient and phase terms.
function M.caustic(s:Sim,u:number,v:number):number
 local h,gx,gy=M.sample(s,u,v)
 local t=s.time
 local a=math.sin(24*u+7*v+gx*2.3+t*2.1)
 local b=math.sin(10*u-19*v+gy*2.8-t*1.7)
 local c=math.cos(27*(u+v)+h*8-t*2.5)
 return math.clamp((a*b+c*0.35)*0.35+0.48,0,1)
end
return M
