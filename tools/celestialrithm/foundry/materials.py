"""Celestialrithm material registry.

Every material is a class with a stable canonical id, a full spec (palettes,
bevel, ink, geometry, optics, motion, interaction, hierarchy, tiers, reduced
motion, rarity) and a `frame(t, press)` that returns linear RGB + an emissive
mask for one face. State (simulations) lives on the instance, so frames must be
requested in time order; `seed` makes every run bit-identical.

Methods are real field/simulation techniques (wave equation + refracted
caustics, thin-film interference, Planck emission, Worley facets, metaballs,
Gray-Scott, Stam fluids, midpoint-displacement lightning, gravitational lensing,
diffraction gratings), graded to the kit's stylized palettes.
"""
from __future__ import annotations

import math
import zlib

import numpy as np

from . import fields as fl
from . import optics as op
from .fields import F32, smoothstep

REGISTRY: dict[str, type] = {}


def register(cls):
    REGISTRY[cls.ID] = cls
    return cls


def H(h):
    return op.hex_rgb(h)


class Material:
    ID = 'base'
    NAME = 'Base'
    FAMILY = ''
    METHOD = ''                      # one line: the actual algorithm chain
    PALETTE = {}                     # base / highlight / shadow / rim (hex)
    SPEC = {}                        # the rest of the material contract
    COST = 'med'

    def __init__(self, fw, fh, seed=0, quality='high'):
        self.fw, self.fh, self.seed, self.quality = fw, fh, seed, quality
        self.x, self.y = fl.grid(fw, fh)              # x in [0, fw/fh], y in [0, 1]
        self.n = fl.Noise(seed * 7919 + zlib.crc32(self.ID.encode()) % 997)
        self.rng = np.random.default_rng(seed + 1234)
        self.xh, self.yh = fl.grid(max(fw // 2, 1), max(fh // 2, 1))   # half-res grid for smooth fields
        self.xr = self.x[:1, :]                                         # one row, for x-only fields

    def up(self, f):
        """Upsample a half-res field (or (h, w, 3) colour) to face resolution."""
        return fl.resize(f, self.fw, self.fh)

    @classmethod
    def tint(cls):
        p = cls.PALETTE
        return {'rim': H(p['rim']), 'shadow': H(p['shadow']), 'highlight': H(p['highlight'])}

    @classmethod
    def spec(cls):
        return {'id': cls.ID, 'name': cls.NAME, 'family': cls.FAMILY, 'method': cls.METHOD,
                'palette': cls.PALETTE, 'cost': cls.COST, **cls.SPEC}

    def frame(self, t: float, press: float):
        raise NotImplementedError


COMMON = {
    'bevel': 'stepped 3-band extrusion under a squared cap, lit bezel ring',
    'ink': 'near-black 4 px silhouette + 2 px inner line, never tinted',
    'reduced_motion': 'time x0.2, no light sweep, press = exposure lift only',
    'tiers': {'high': 'full simulation at face resolution', 'mid': 'half-res field, bilinear up',
              'low': 'pre-baked 32-frame loop in an atlas page'},
}


# ======================================================================= 1
@register
class Hydroglass(Material):
    ID = 'hydroglass'; NAME = 'Hydroglass'; FAMILY = 'fluid / optics'
    METHOD = '3D-noise swell + damped wave equation -> Snell refraction photon-splat caustics -> Fresnel sky + Blinn glints'
    PALETTE = {'base': '#0b4f86', 'highlight': '#bff6ff', 'shadow': '#06233f', 'rim': '#2fd3ff'}
    SPEC = {**COMMON, 'geometry': 'water height field (noise swell + wave sim)',
            'optics': 'real refraction caustics (photon splat), Schlick Fresnel, sun glints',
            'motion': 'slow swell; rain-sized drops every ~0.4 s', 'interaction': 'press = central drop; ring waves refract into caustic rings',
            'hierarchy': 'tier 5 material; caustic highlights kept to a minority of the face (hot-pixel share is measured by qa.py)', 'rarity': 'Rare: deeper blue, gold caustics'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.wave = fl.WaveSim(self.fw, self.fh, c=.45, damp=.993, seed=self.seed)
        self.next_drop = .2; self.pressed = False

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        if t >= self.next_drop:
            self.wave.drop(self.rng.uniform(0, self.fw), self.rng.uniform(0, self.fh), 2.2, self.rng.uniform(.4, .8))
            self.next_drop = t + self.rng.uniform(.25, .6)
        if press > .6 and not self.pressed:
            self.wave.drop(self.fw * .5, self.fh * .5, 6, 5.0); self.pressed = True
        if press < .1:
            self.pressed = False
        w = self.wave.step(2)
        swell = n.fbm(x * 2.0, y * 2.0, t * .3, 4) + .3 * n(x * 5 + t * .25, y * 5, t * .5)
        h = swell * 4.2 + w * .9
        c = op.caustics(h, depth=40, ior=1.33, sigma=.45)
        c = np.clip(c - 1.15, 0, None) ** 1.15 * 1.5
        nx, ny, nz = op.normals(h, .35)
        fres = op.fresnel_schlick(nz, .03)
        depth = .55 + .45 * n.fbm(x * 1.3 + 3, y * 1.3, t * .1, 3)
        base = op.ramp(np.clip(depth * (1 - .3 * y), 0, 1),
                       [(0, H('#04305a')), (.45, H('#0870b0')), (.8, H('#10a8e0')), (1, H('#2cd2f2'))])
        caus = c[..., None] * (H('#8ff6ff') * .75 + .12)
        sky = op.ramp(1 - y, [(0, H('#0d7fc0')), (1, H('#c9f7ff'))])
        glint = op.blinn(nx, ny, nz, -.4, -.7, .6, 220) * 2.2
        rgb = base * (.8 + .2 * nz[..., None]) + caus + sky * fres[..., None] * .25 + glint[..., None]
        if getattr(self, 'debug', None) is not None:          # layer capture for breakdown reels
            self.debug.update(height=h, normals=(nx, ny, nz), caustics=c, base=base, glints=glint)
        return op.tonemap(rgb), np.clip(c * .6, 0, 1)


# ======================================================================= 2
@register
class PrismGel(Material):
    ID = 'prism_gel'; NAME = 'Prism Gel'; FAMILY = 'thin film / gel'
    METHOD = 'two-level domain-warped thickness field -> spectral thin-film interference (CIE-integrated) over a violet gel with dispersion fringes'
    PALETTE = {'base': '#3a1670', 'highlight': '#ffe4ff', 'shadow': '#1a0638', 'rim': '#d77bff'}
    SPEC = {**COMMON, 'geometry': 'gel height = warped fbm', 'optics': 'thin-film 34-wavelength spectrum, Fresnel-weighted',
            'motion': 'film drains downward and swirls (warp in time)', 'interaction': 'press = film thins at centre -> colour bands race outward',
            'hierarchy': 'tier 5; iridescence saturation capped so it never outshines tier 6', 'rarity': 'Mythic: gold-black film'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        xh, yh = self.xh, self.yh
        f, qx, qy, rx, ry = n.warp(xh * 1.1, yh * 1.1 + t * .1, t * .2, amount=1.5, octaves=3)
        f, qx, rx = self.up(f), self.up(qx), self.up(rx)
        r = np.sqrt((x - x.mean()) ** 2 + (y - .5) ** 2)
        thick = 380 + 220 * (f * .5 + .5) + 80 * y - press * 200 * np.exp(-(r / .55) ** 2)
        h = f * 1.5 + .5 * qx
        nx, ny, nz = op.normals(h * 6, 1.0)
        film = op.thin_film(thick, cos_t=np.clip(nz, .3, 1), strength=1.0)
        gel = op.ramp(np.clip(.5 + .6 * rx, 0, 1), [(0, H('#24074f')), (.45, H('#5a1aa8')), (.8, H('#b13ee0')), (1, H('#f07cf5'))])
        fres = op.fresnel_schlick(nz, .2)
        spec = op.blinn(nx, ny, nz, -.3, -.8, .5, 90) * 1.2
        vein = np.clip(n.ridged(x * 2.2 + qx * .3, y * 2.2, t * .3, 3) - .62, 0, 1) * 3.2
        rim_f = np.clip((fres - .2) / .8, 0, 1)
        core = press * np.exp(-(r / .6) ** 2)                      # press: the gel lights from inside
        gel = gel * (1 + 1.2 * core)[..., None]; vein = vein * (1 + 1.5 * press)
        rgb = gel * .6 + film * (.3 * rim_f)[..., None] + spec[..., None] * .8 + vein[..., None] * H('#ffd2ff') * .8
        return op.tonemap(rgb), np.clip(vein * .5 + spec * .3, 0, 1)


# ======================================================================= 3
@register
class SolarPlasma(Material):
    ID = 'solar_plasma'; NAME = 'Solar Plasma'; FAMILY = 'emission'
    METHOD = 'curl-advected ridged multifractal temperature field + Worley granulation -> blackbody-ordered temperature ramp -> filmic shoulder'
    PALETTE = {'base': '#d26a08', 'highlight': '#fff1b0', 'shadow': '#4a1402', 'rim': '#ffb21f'}
    SPEC = {**COMMON, 'geometry': 'flat face; granulation cells modulate temperature', 'optics': 'pure emission (Planck), filmic highlight roll-off',
            'motion': 'filaments flow along curl noise; granules boil', 'interaction': 'press = flare: +1800 K travelling front from the centre',
            'hierarchy': 'tier 5; brightest emissive material, so one per screen at most', 'rarity': 'Legendary: blue-white 9000 K core'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        cx, cy = n.curl(x * 1.2, y * 1.2, t * .15, eps=.02, octaves=2)
        wx = x + .25 * cx; wy = y + .25 * cy
        rid = n.ridged(wx * 2.6 + t * .08, wy * 2.6, t * .45, 5)
        f1, f2, _, _, _ = fl.voronoi(x * 9, y * 9, self.seed, t * .7, wander=.18)
        gran = smoothstep(0, .35, f2 - f1)
        r = np.sqrt((x - x.mean()) ** 2 + (y - .5) ** 2)
        front = np.exp(-((r - press * 1.3) / .18) ** 2) * press
        T = 2300 + 3600 * rid ** 1.5 + 500 * gran + 1800 * front + 1600 * press * np.exp(-(r / .5) ** 2)
        # Planck sets the order of hues (red < orange < yellow < white); the ramp grades it to the kit palette
        tn = np.clip((T - 2300) / 4400, 0, 1)
        rgb = op.ramp(tn, [(0, H('#6a1300')), (.25, H('#d84a00')), (.5, H('#ff8a00')), (.72, H('#ffc21a')), (.9, H('#fff07a')), (1, H('#ffffff'))]) * 1.15
        return op.tonemap(rgb, 1.0), np.clip(tn * 1.1, 0, 1)


# ======================================================================= 4
@register
class BioSlime(Material):
    ID = 'bio_slime'; NAME = 'Bio Slime'; FAMILY = 'living fluid'
    METHOD = 'metaball membrane field + morphing Worley cytoplasm + rising bubbles; wrap-lit subsurface + membrane specular'
    PALETTE = {'base': '#5fbf12', 'highlight': '#f4ffb8', 'shadow': '#1f4a05', 'rim': '#a8ff2e'}
    SPEC = {**COMMON, 'geometry': 'metaball heights over a cellular gel', 'optics': 'wrap diffuse (SSS approximation), wet specular, bubble caps',
            'motion': 'blobs drift on Lissajous paths, cells breathe, bubbles rise', 'interaction': 'press = blobs swell 25% and merge, then wobble back (spring)',
            'hierarchy': 'tier 5; bubbles are the only small bright marks', 'rarity': 'Epic: toxic magenta nuclei'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        r = self.rng
        self.blobs = [(r.uniform(.2, 2.0), r.uniform(.2, .8), r.uniform(.15, .27), r.uniform(.2, .6), r.uniform(0, 6.3)) for _ in range(7)]
        self.bub = [(r.uniform(0, self.fw / self.fh), r.uniform(0, 1), r.uniform(.012, .03), r.uniform(.05, .14)) for _ in range(16)]

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        swell = 1 + .25 * press + .06 * math.sin(t * 9) * press
        field = np.zeros_like(x)
        for (bx, by, br, sp, ph) in self.blobs:
            px = bx + .25 * math.sin(t * sp + ph); py = by + .18 * math.cos(t * sp * 1.3 + ph)
            field += (br * swell) ** 2 / ((x - px) ** 2 + (y - py) ** 2 + 1e-3)
        f1, f2, cid, _, _ = fl.voronoi(x * 4.5 + .2 * n(x, y, t * .2), y * 4.5, self.seed + 3, t * .5, wander=.3)
        cell = smoothstep(.0, .25, f2 - f1)
        h = np.clip(field, 0, 3) * .6 + cell * .35 + .15 * n.fbm(x * 4, y * 4, t * .3, 3)
        nx, ny, nz = op.normals(h * 7, 1.0)
        wrap = np.clip((nx * -.4 + ny * -.6 + nz * .7 + .5) / 1.5, 0, 1)
        nuclei = smoothstep(.55, .2, f1) * (1 - smoothstep(.8, 1.6, field)) * .6
        base = op.ramp(np.clip(.2 + .22 * np.clip(field, 0, 2) + .3 * cell - nuclei * .5, 0, 1),
                       [(0, H('#173d04')), (.35, H('#3e8d0a')), (.7, H('#7bd317')), (1, H('#c6ff4a'))])
        sss = H('#c8ff50') * (smoothstep(1.2, 3.0, field) * .18)[..., None]
        spec = op.blinn(nx, ny, nz, -.3, -.75, .6, 70) * 1.2
        rgb = base * (.42 + .42 * wrap)[..., None] + sss + spec[..., None]   # deeper than crystal ice (tritan pass)
        bub_glow = np.zeros_like(x)
        for (bx, by0, br, sp) in self.bub:
            by = (by0 - t * sp) % 1.15 - .07
            bxx = bx + .02 * math.sin(t * 3 + by0 * 20)
            d = np.sqrt((x - bxx) ** 2 + (y - by) ** 2)
            ring = smoothstep(br, br * .7, d) - smoothstep(br * .75, br * .4, d) * .7
            cap = np.exp(-(((x - bxx + br * .35) ** 2 + (y - by + br * .35) ** 2) / (br * br * .08)))
            rgb = rgb * (1 - .25 * smoothstep(br, br * .6, d))[..., None] + (ring * .45 + cap * 1.2)[..., None] * H('#f2ffc8')
            bub_glow += cap
        return op.tonemap(rgb), np.clip(bub_glow * .5 + sss[..., 1] * .5, 0, 1)


# ======================================================================= 5
@register
class CrystalIce(Material):
    ID = 'crystal_ice'; NAME = 'Crystal Ice'; FAMILY = 'crystal / refraction'
    METHOD = 'Worley facets with per-cell tilted normals -> faceted refraction of a noise backdrop + per-facet Blinn glints under an orbiting light; F2-F1 fracture lines; frost speckle'
    PALETTE = {'base': '#9cc9f2', 'highlight': '#ffffff', 'shadow': '#2a4d7a', 'rim': '#cfe9ff'}
    SPEC = {**COMMON, 'geometry': 'faceted (piecewise-planar) relief from Worley cells', 'optics': 'per-facet refraction offset + sharp glints, frosted edges',
            'motion': 'light orbits slowly so facets twinkle in sequence; facets do not move', 'interaction': 'press = crack-light: a bright fracture front runs facet to facet',
            'hierarchy': 'tier 5; glint count capped per frame', 'rarity': 'Legendary: rose-gold facets'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        f1, f2, cid, dx, dy = fl.voronoi(x * 5.2, y * 5.2, self.seed + 11, 0.0, wander=0)
        a = fl.hash01(cid) * 6.2832; tilt = .12 + .22 * fl.hash01(cid + 7)
        nx = np.cos(a) * tilt; ny = np.sin(a) * tilt; nz = np.sqrt(1 - tilt * tilt)
        la = t * .9
        lx, ly, lz = .7 * math.cos(la), .7 * math.sin(la) - .3, .6
        bx = x + nx * .18; by = y + ny * .18
        back = n.fbm(bx * 1.6, by * 1.6, .5 + t * .05, 4) * .5 + .5
        streak = np.clip(n.ridged(bx * 1.8 + by * .6, by * 2.4, t * .08, 3) - .5, 0, 1) * 1.8
        base = op.ramp(np.clip(back * .75 + .25 * (1 - y) + streak * .3, 0, 1), [(0, H('#20457a')), (.4, H('#5c93cf')), (.75, H('#b5d9f7')), (1, H('#f2f9ff'))])
        diff = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
        glint = np.minimum(op.blinn(nx, ny, nz, lx, ly, lz, 400) * 1.6, .45) * smoothstep(.0, .5, f1 * 1.2 + .3 * np.sin(dx * 9 + dy * 7))
        edge = smoothstep(.035, .0, f2 - f1) * (.5 + .5 * np.clip(nx * lx + ny * ly, 0, 1))
        r = np.sqrt((x - x.mean()) ** 2 + (y - .5) ** 2)
        crack = np.exp(-((r - press * 1.4) / .12) ** 2) * press * edge * 3 + press * edge * .6   # front + lit fracture net at peak
        frost = (fl.hash01((self.x * 997).astype(np.int64) * 131 + (self.y * 991).astype(np.int64)) > .985) * .5
        rgb = base * (.8 + .42 * diff)[..., None] + H('#dff0ff') * .06 + glint[..., None] + streak[..., None] * H('#e8f6ff') * .35 + edge[..., None] * H('#e8f6ff') * .45 + crack[..., None] * H('#bff0ff') + frost[..., None] * .5
        return op.tonemap(rgb), np.clip(glint * .4 + crack, 0, 1)


# ======================================================================= 6
@register
class HoloFoil(Material):
    ID = 'holo_foil'; NAME = 'Holographic Foil'; FAMILY = 'interference + diffraction'
    METHOD = 'high-order thin-film interference on brushed silver (thickness = slow warped fbm, gives pastel swirls) + embossed Worley micro-cells as diffraction-grating sparkle under a sweeping light'
    PALETTE = {'base': '#b9bfd0', 'highlight': '#ffffff', 'shadow': '#4c5168', 'rim': '#e8d6ff'}
    SPEC = {**COMMON, 'geometry': 'embossed micro-cells on a flat foil', 'optics': 'thin film (orders 2-4 -> pastel), grating sparkle, anisotropic brushed silver',
            'motion': 'swirls drift; sparkle follows a slowly tilting light', 'interaction': 'press = tilt sweep: every band shifts one full order',
            'hierarchy': 'tier 5; saturation capped at rest, full on press', 'rarity': 'any: the foil itself reads as premium'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        w, qx, qy, _, _ = n.warp(self.xh * .9, self.yh * .9, t * .07, amount=1.4, octaves=3)
        w = self.up(w); qx = self.up(qx)
        s = t * .5 + press * 2.5
        tilt = .5 * math.sin(s)
        thick = 600 + 520 * w + 260 * (x * .35 + y * .2) + 300 * tilt
        film = op.thin_film(thick, cos_t=.9, n_film=1.45, strength=1.0)
        f1, f2, cid, dx, dy = fl.voronoi(x * 9, y * 9, self.seed + 5, 0.0, wander=0)
        ang = fl.hash01(cid) * 3.1416
        lx = .55 * math.sin(s * 1.3) + .3 * qx; ly = .35 * math.cos(s)
        spark = op.grating(lx, ly, np.cos(ang), np.sin(ang), pitch_nm=1500, bandwidth=12) * smoothstep(.0, .12, f2 - f1)[..., None]
        brushed = .6 + .07 * n(x * 1.2, y * 70, 0) + .15 * (1 - y)
        silver = np.asarray(op.ramp(brushed, [(0, H('#4a5068')), (.6, H('#a6adc4')), (1, H('#f2f3ff'))]), F32)
        sat = .7 + .3 * press
        rgb = silver * .55 + film * (.42 * sat) + spark * .2
        return op.tonemap(rgb), np.clip(spark.max(-1) * .3, 0, 1)


# ======================================================================= 7
@register
class Void(Material):
    ID = 'void'; NAME = 'Void Singularity'; FAMILY = 'lensing'
    METHOD = 'point-mass lens (deflection theta_E^2 / r) over a hashed starfield + polar-swirled fbm accretion ring + photon ring'
    PALETTE = {'base': '#2a0a4a', 'highlight': '#f2b8ff', 'shadow': '#07020f', 'rim': '#b13cff'}
    SPEC = {**COMMON, 'geometry': 'flat; distortion is optical', 'optics': 'gravitational lensing of the backdrop, Einstein ring',
            'motion': 'accretion swirls (Keplerian: faster near the core)', 'interaction': 'press = lens mass x2, ring flares then relaxes',
            'hierarchy': 'tier 5; dark material: a contrast anchor among bright keys', 'rarity': 'Mythic: second orbiting singularity'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        cx, cy = x.max() * .5 + .08 * math.sin(t * .4), .5 + .05 * math.cos(t * .5)
        dx, dy = x - cx, y - cy
        r = np.sqrt(dx * dx + dy * dy) + 1e-4
        thE = .17 * (1 + .9 * press)
        defl = thE * thE / r
        sx = x + dx / r * defl; sy = y + dy / r * defl
        cell = 34.0
        ix = np.floor(sx * cell).astype(np.int64); iy = np.floor(sy * cell).astype(np.int64)
        hsh = fl.hash01(ix * 7349 + iy * 1931)
        fx = sx * cell - ix - .5; fy = sy * cell - iy - .5
        star = (hsh > .93) * np.exp(-(fx * fx + fy * fy) / .02) * (.6 + .4 * np.sin(t * 3 + hsh * 50))
        neb = n.fbm(sx * 2.5, sy * 2.5, t * .05, 4) * .5 + .5
        sky = op.ramp(neb, [(0, H('#05020c')), (.6, H('#1c0738')), (1, H('#4b1580'))])
        ang = np.arctan2(dy, dx)
        omega = .9 / (r + .15) ** 1.5
        swirl = n.fbm(np.cos(ang - t * omega) * 2 + r * 6, np.sin(ang - t * omega) * 2, t * .2, 4)
        disk = np.exp(-((r - thE * 1.55) / (.09 + .03 * swirl)) ** 2) * (.6 + .6 * swirl)
        ring = np.exp(-((r - thE) / .012) ** 2) * (1.2 + 2 * press)
        hole = smoothstep(thE * .95, thE * .7, r)
        rgb = sky + star[..., None] * 1.6 + disk[..., None] * op.ramp(np.clip(swirl * .5 + .5, 0, 1), [(0, H('#6a12c9')), (.6, H('#d14cff')), (1, H('#ffd0ff'))]) * 1.3 + ring[..., None] * H('#f7c8ff')
        rgb = rgb * (1 - hole)[..., None]
        return op.tonemap(rgb), np.clip(disk * .6 + ring * .5, 0, 1)


# ======================================================================= 8
@register
class ElectricGlass(Material):
    ID = 'electric_glass'; NAME = 'Electric Glass'; FAMILY = 'discharge'
    METHOD = 'midpoint-displacement bolts with recursive branches, re-struck on a jittered timer; segment distance field -> core + exp glow; afterimage decay; plasma backdrop'
    PALETTE = {'base': '#0a2a8f', 'highlight': '#e6f4ff', 'shadow': '#020a2e', 'rim': '#2f8bff'}
    SPEC = {**COMMON, 'geometry': 'flat glass', 'optics': 'emissive arcs, faint refraction backdrop',
            'motion': 'a bolt every 0.25-0.6 s, flickers 3 frames then fades over 0.3 s', 'interaction': 'press = 3 bolts at once fork from the centre',
            'hierarchy': 'tier 5; flash-safe: luminance change kept under the WCAG red-flash/general-flash limits (checked in QA)', 'rarity': 'Epic: violet arcs'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.bolts = []; self.next = 0.0; self.burst = False

    def _strike(self, t, center=False):
        W = self.fw / self.fh
        if center:
            a = (W / 2, .5); ang = self.rng.uniform(0, 6.28)
            b = (W / 2 + math.cos(ang) * W * .55, .5 + math.sin(ang) * .6)
        else:
            a = (self.rng.uniform(-.1, .2), self.rng.uniform(0, 1)); b = (W + self.rng.uniform(-.2, .1), self.rng.uniform(0, 1))
        segs = fl.lightning_path(self.rng, a, b, depth=7, disp=.22)
        d, lv = fl.segment_distance(self.x, self.y, segs)
        self.bolts.append([t, d, lv])

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        if t >= self.next:
            self._strike(t); self.next = t + self.rng.uniform(.18, .4)
        if press > .6 and not self.burst:
            for _ in range(3):
                self._strike(t, True)
            self.burst = True
        if press < .1:
            self.burst = False
        self.bolts = [b for b in self.bolts if t - b[0] < 1.1]
        plasma = n.fbm(x * 2, y * 2, t * .4, 4) * .5 + .5
        base = op.ramp(plasma, [(0, H('#031056')), (.6, H('#0a3bc0')), (1, H('#2a7cff'))])
        light = np.zeros_like(x)
        for (t0, d, lv) in self.bolts:
            age = t - t0
            fl_ = (1.0 if age < .05 else .7 + .3 * math.cos(age * 70)) * (math.exp(-age * 9) * .7 + math.exp(-age * 2.2) * .3)
            width = np.where(lv == 0, .014, .008)
            light += fl_ * (np.exp(-(d / width) ** 2) * 2.6 + np.exp(-d / .04) * .8 + np.exp(-d / .12) * .3)
        rgb = base + light[..., None] * op.ramp(np.clip(light / 2, 0, 1), [(0, H('#2f8bff')), (.5, H('#8fd0ff')), (1, H('#ffffff'))])
        return op.tonemap(rgb), np.clip(light * .5, 0, 1)


# ======================================================================= 9
@register
class MoltenCore(Material):
    ID = 'molten_core'; NAME = 'Molten Core'; FAMILY = 'emission / crust'
    METHOD = 'drifting Worley crust plates; F2-F1 cracks carry a travelling heat pulse -> Planck colour in cracks, cooled basalt plates with ember speckle'
    PALETTE = {'base': '#8a0f12', 'highlight': '#ffd27a', 'shadow': '#24030a', 'rim': '#ff3b30'}
    SPEC = {**COMMON, 'geometry': 'raised crust plates (height = F1 dome)', 'optics': 'Planck emission in cracks, matte crust with rim light',
            'motion': 'plates drift and grind; heat pulses run along cracks', 'interaction': 'press = crust splits wider, cracks reach 2400 K',
            'hierarchy': 'tier 5; red reserved for danger in HUD, so use as rarity/material only', 'rarity': 'Legendary: gold cracks'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        wx = x + .15 * n(x * 1.5, y * 1.5, t * .1); wy = y + .15 * n(x * 1.5 + 4, y * 1.5, t * .1)
        f1, f2, cid, _, _ = fl.voronoi(wx * 4.2 + t * .05, wy * 4.2, self.seed + 9, t * .25, wander=.22)
        gap = f2 - f1
        width = .08 + .06 * press
        crack = smoothstep(width, 0, gap)
        pulse = .6 + .4 * np.sin(fl.hash01(cid) * 30 + t * 2.5 - (x + y) * 4)
        T = 900 + 1500 * crack * pulse + 600 * press * crack
        hot = op.blackbody_lut(T) * (crack * (.4 + .9 * pulse))[..., None] * 1.6
        dome = np.clip(1 - f1 * 1.4, 0, 1)
        nx, ny, nz = op.normals(dome * 8, 1.0)
        rimlit = np.clip(nx * -.5 + ny * -.7, 0, 1) ** 2
        crust = op.ramp(np.clip(dome * .8 + .2 * n(x * 9, y * 9, 0), 0, 1), [(0, H('#24030a')), (.5, H('#4a0a10')), (1, H('#7a1a17'))])
        ember = (fl.hash01((x * 211).astype(np.int64) * 977 + (y * 197).astype(np.int64) + int(t * 6)) > .995) * .8
        rgb = crust * (.6 + .5 * rimlit)[..., None] + hot + ember[..., None] * H('#ff9a3a') + H('#ff3b30') * (crack * .25)[..., None]
        return op.tonemap(rgb), np.clip(crack * pulse, 0, 1)


# ======================================================================= 10
@register
class VerdantCoral(Material):
    ID = 'verdant_coral'; NAME = 'Verdant Coral'; FAMILY = 'reaction-diffusion'
    METHOD = 'Gray-Scott reaction-diffusion (f,k drifting through the coral/mitosis regime) -> height -> normals -> emerald subsurface + wet specular'
    PALETTE = {'base': '#0f8a5a', 'highlight': '#d8fff0', 'shadow': '#033823', 'rim': '#2bf0a0'}
    SPEC = {**COMMON, 'geometry': 'RD concentration as relief', 'optics': 'subsurface tint by thickness, wet specular',
            'motion': 'pattern grows and reorganises (never loops exactly)', 'interaction': 'press = feed rate pulse -> spots divide (mitosis)',
            'hierarchy': 'tier 5; fine pattern: keep the face >= 96 px tall or switch to mid tier', 'rarity': 'Epic: bioluminescent tips'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.rd = fl.GrayScott(self.fw // 2, self.fh // 2, f=.029, k=.057, seed=self.seed)
        self.rd.step(1400)

    def frame(self, t, press):
        x, y = self.x, self.y
        f = .029 + .003 * math.sin(t * .2) + .008 * press
        v = self.rd.step(10, f=f, k=.057)
        v = fl.resize(v, self.fw, self.fh)
        h = fl.blur(v, 1.0)
        nx, ny, nz = op.normals(h * 40, 1.0)
        th = np.clip(h * 3.2 * (1 + .35 * press), 0, 1)
        base = op.ramp(th, [(0, H('#032a1b')), (.35, H('#0b6e48')), (.7, H('#19c486')), (1, H('#b8ffe3'))])
        la = t * .35                                                # light drifts so wet highlights crawl
        spec = op.blinn(nx, ny, nz, -.35 + .25 * math.cos(la), -.7 + .2 * math.sin(la), .6, 60) * 1.0
        tips = smoothstep(.28, .36, h) * (.5 + .5 * math.sin(t * 2)) * press
        rgb = base * (.6 + .5 * nz)[..., None] + spec[..., None] + tips[..., None] * H('#7dffd0')
        return op.tonemap(rgb), np.clip(th * .4 + tips, 0, 1)


# ======================================================================= 11
@register
class Opal(Material):
    ID = 'opal'; NAME = 'Opal'; FAMILY = 'diffraction / milk'
    METHOD = 'milky domain-warped fbm body + Worley silica domains, each diffracting toward its own direction: angle-selective flashes with spectral hue under a circling light'
    PALETTE = {'base': '#d9e4f2', 'highlight': '#ffffff', 'shadow': '#6f7f99', 'rim': '#ffd6f4'}
    SPEC = {**COMMON, 'geometry': 'smooth dome', 'optics': 'per-patch diffraction (silica-sphere lattice idea), milky scatter',
            'motion': 'patches flash in and out as the light drifts', 'interaction': 'press = light swings, every patch flashes once in sequence',
            'hierarchy': 'tier 5; bright pastel: needs the dark ink to read', 'rarity': 'Mythic: black opal (dark body)'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        milk, *_ = n.warp(self.xh * 1.4, self.yh * 1.4, t * .05, amount=1.2, octaves=3)
        milk = self.up(milk)
        f1, f2, cid, dx, dy = fl.voronoi(x * 6.5 + .5 * milk, y * 6.5, self.seed + 21, 0.0, wander=0)
        s = t * .45 + press * 3.0
        lx, ly = math.cos(s), math.sin(s * .8)
        a = fl.hash01(cid) * 6.2832                               # each silica domain diffracts toward its own direction
        align = np.cos(a) * lx + np.sin(a) * ly
        flash = smoothstep(.1, .9, align) ** 1.3                 # strong angular selectivity -> patches flash in turn
        hue_t = np.clip(.5 + .5 * np.sin(fl.hash01(cid + 9) * 12 + s * 1.5 + (dx * 2 + dy)), 0, 1)
        lam = 450 + 200 * hue_t
        play = op.wavelength_rgb(lam) * (flash * (1 - smoothstep(.1, .6, f1)) * smoothstep(0, .08, f2 - f1))[..., None]
        body = op.ramp(milk * .5 + .5, [(0, H('#5d76a3')), (.5, H('#a9bfe0')), (1, H('#eaf2ff'))])
        rgb = body * .75 + play * 1.15
        return op.tonemap(rgb), np.clip(play.max(-1) * .35, 0, 1)


# ======================================================================= 12
@register
class Nebula(Material):
    ID = 'nebula'; NAME = 'Nebula'; FAMILY = 'volumetric emission'
    METHOD = '4-slice ray-marched emission/absorption through warped fbm density + twinkling stars + a comet arc on a parametric curve'
    PALETTE = {'base': '#1a0b3d', 'highlight': '#ffd6ff', 'shadow': '#05030f', 'rim': '#8a5cff'}
    SPEC = {**COMMON, 'geometry': 'flat; depth is from 4 parallax slices', 'optics': 'front-to-back emission-absorption compositing',
            'motion': 'slices drift at different speeds (parallax), comet traces a slow arc', 'interaction': 'press = star birth: a core brightens and blows a bubble',
            'hierarchy': 'tier 5; dark: pairs with bright neighbours', 'rarity': 'Legendary: gold dust lane'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        rgb = np.zeros(x.shape + (3,), F32); trans = np.ones_like(x)
        cols = [H('#ff4fd8'), H('#7a5cff'), H('#2fb7ff'), H('#ff9ad5')]
        for i in range(4):
            sp = .03 * (i + 1)
            d, *_ = n.warp(self.xh * (1.2 + .5 * i) + t * sp, self.yh * (1.2 + .5 * i), t * .07 + i * 3.1, amount=1.3, octaves=3)
            d = self.up(d)
            dens = np.clip(d * 1.6 + .1, 0, 1) ** 1.6
            emit = cols[i] * (dens * .62)[..., None]          # darker than prism gel: tritan-safe by lightness
            rgb += trans[..., None] * emit
            trans *= np.exp(-dens * .9)
        cx, cy = x.max() * .5, .5
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        birth = press * (np.exp(-(r / .07) ** 2) * 3 + np.exp(-((r - press * .5) / .05) ** 2) * 1.2)
        ix = np.floor(x * 40).astype(np.int64); iy = np.floor(y * 40).astype(np.int64)
        hs = fl.hash01(ix * 4441 + iy * 1013)
        fx = x * 40 - ix - .5; fy = y * 40 - iy - .5
        stars = (hs > .9) * np.exp(-(fx * fx + fy * fy) / .03) * (.5 + .5 * np.sin(t * 4 + hs * 70))
        u = (t * .12) % 1.4 - .2
        cxp = u * x.max(); cyp = .8 - .9 * u + .6 * u * u
        dcom = np.sqrt((x - cxp) ** 2 + (y - cyp) ** 2)
        comet = np.exp(-(dcom / .015) ** 2) * 1.5
        rgb = rgb + H('#05030f') + stars[..., None] * 1.3 + (birth + comet)[..., None] * H('#ffe6ff')
        return op.tonemap(rgb), np.clip(birth + comet + stars * .5, 0, 1)


# ======================================================================= 13
@register
class LiquidChrome(Material):
    ID = 'liquid_chrome'; NAME = 'Liquid Chrome'; FAMILY = 'mirror fluid'
    METHOD = 'metaball + noise height with wave-sim ripples -> normals -> reflected vector sampled against a studio softbox strip environment + sun lobe'
    PALETTE = {'base': '#9aa4b5', 'highlight': '#ffffff', 'shadow': '#1d2230', 'rim': '#dfe8ff'}
    SPEC = {**COMMON, 'geometry': 'fluid mirror height', 'optics': 'environment reflection (matcap), sharp horizon line',
            'motion': 'mercury beads merge and split slowly', 'interaction': 'press = ripple rings bend the reflected horizon',
            'hierarchy': 'tier 5; neutral: lets the icon colour lead', 'rarity': 'any; gold variant = Molten Gold'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.wave = fl.WaveSim(self.fw, self.fh, c=.5, damp=.985, seed=self.seed); self.hit = False

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        if press > .6 and not self.hit:
            self.wave.drop(self.fw / 2, self.fh / 2, 5, 6); self.hit = True
        if press < .1:
            self.hit = False
        w = self.wave.step(2)
        field = np.zeros_like(x)
        for i in range(5):
            px = (i + .5) / 5 * x.max() + .3 * math.sin(t * .5 + i * 1.7); py = .5 + .25 * math.cos(t * .6 + i * 2.3)
            field += .03 / ((x - px) ** 2 + (y - py) ** 2 + .01)
        h = np.clip(field, 0, 4) * .5 + .3 * n.fbm(x * 2, y * 2, t * .2, 3) + w * .25
        nx, ny, nz = op.normals(h * 7, 1.0)
        # studio softbox environment: reflected direction sweeps alternating light strips
        rx = 2 * nz * nx; ry = 2 * nz * ny
        v = ry * 1.6 + rx * .4 + y * 1.1
        strip = .5 + .5 * np.sin(v * 2.4 + .9)
        strip = smoothstep(.1, .9, strip) ** 1.3
        rgb = op.ramp(strip, [(0, H('#07090f')), (.35, H('#3a4560')), (.7, H('#b9c6e4')), (1, H('#ffffff'))])
        rgb = rgb + op.blinn(nx, ny, nz, -.3, -.8, .5, 300)[..., None] * 1.5
        return op.tonemap(rgb), np.zeros_like(x)


# ======================================================================= 14
@register
class Aurora(Material):
    ID = 'aurora'; NAME = 'Aurora'; FAMILY = 'curtain emission'
    METHOD = 'curtain sheets: a 1D fbm-displaced fold line per layer, vertically extruded with exponential ray falloff and altitude colour ramp (green -> magenta), over a starry gradient'
    PALETTE = {'base': '#06243a', 'highlight': '#d4ffe9', 'shadow': '#020a14', 'rim': '#3dffb0'}
    SPEC = {**COMMON, 'geometry': 'flat', 'optics': 'additive emission curtains, altitude-coded colour',
            'motion': 'folds travel sideways, rays shimmer', 'interaction': 'press = substorm: curtains brighten and ripple fast',
            'hierarchy': 'tier 5; calm material: good for idle surfaces', 'rarity': 'Epic: red top fringe'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        sky = op.ramp(y, [(0, H('#020a14')), (1, H('#0b3550'))])
        rgb = sky.copy(); glow = np.zeros_like(x)
        spd = 1 + 3 * press
        for i in range(3):
            line = .62 + .1 * i + .22 * n.fbm(self.xr * 2.2 + i * 4, np.full_like(self.xr, i * 2.0), t * .15 * spd, 4)
            dy = y - line
            curtain = np.where(dy < 0, np.exp(dy / (.22 + .06 * i)), np.exp(-dy / .02))
            rays = .6 + .4 * n(self.xr * 22 + i * 9, np.full_like(self.xr, float(i)), t * .8 * spd) ** 2 * 3
            inten = np.clip(curtain * rays * (.8 + .9 * press), 0, 2)
            col = op.ramp(np.clip(-dy * 2.4, 0, 1), [(0, H('#7dffcf')), (.25, H('#1fe08a')), (.7, H('#17a86e')), (1, H('#c04cff'))])
            rgb = rgb + col * inten[..., None] * (.6 - .12 * i)
            glow += inten
        return op.tonemap(rgb), np.clip(glow * .3, 0, 1)


# ======================================================================= 15
@register
class Ferrofluid(Material):
    ID = 'ferrofluid'; NAME = 'Ferrofluid'; FAMILY = 'magnetic fluid'
    METHOD = 'Rosensweig-style spike lattice: hexagonal cone field whose height follows a moving magnet potential; glossy black dielectric with sharp env highlights'
    PALETTE = {'base': '#15161c', 'highlight': '#e8ecff', 'shadow': '#050507', 'rim': '#7a8cff'}
    SPEC = {**COMMON, 'geometry': 'hex spike lattice gated by magnet strength', 'optics': 'black gloss, coloured env reflection, rim light',
            'motion': 'magnet circles; spikes rise and fall in a travelling crown', 'interaction': 'press = magnet pulls to the centre, spikes stand up',
            'hierarchy': 'tier 5; dark but sharp: high detail per pixel, keep away from small text', 'rarity': 'Legendary: liquid-gold variant'}

    def frame(self, t, press):
        x, y, n = self.x, self.y, self.n
        mx = x.max() * (.5 + .35 * math.cos(t * .5) * (1 - press)); my = .5 + .25 * math.sin(t * .7) * (1 - press)
        mx2 = x.max() - mx * .8; my2 = 1 - my
        mag = np.exp(-((x - mx) ** 2 + (y - my) ** 2) / (.2 + .12 * press)) + .8 * np.exp(-((x - mx2) ** 2 + (y - my2) ** 2) / .14) * (1 - press)
        s = 9.0
        qx = x * s; qy = y * s / .866
        row = np.floor(qy)
        qx2 = qx + .5 * (row % 2)
        cx = np.floor(qx2) + .5; cy = row + .5
        dd = np.sqrt((qx2 - cx) ** 2 + ((qy - cy) * .866) ** 2)
        spike = np.clip(1 - dd / .5, 0, 1) ** 1.6 * smoothstep(.15, .7, mag) * (1 + .3 * press)
        h = spike * 1.2 + mag * .6 + .05 * n(x * 3, y * 3, t * .3)
        nx, ny, nz = op.normals(h * 3, 1.0)
        env = op.env_reflect(nx, ny, nz, H('#a9b8f0'), H('#2a3156'), H('#030305'), sun_dir=(-.35, -.8), sun_color=(1.4, 1.45, 1.6), sun_power=90, bias=-.85)
        rgb = H('#040509') + env * (.12 + .88 * smoothstep(.02, .5, spike + mag * .25))[..., None]
        return op.tonemap(rgb), np.zeros_like(x)


# ======================================================================= 16
@register
class QuantumInk(Material):
    ID = 'quantum_ink'; NAME = 'Quantum Ink'; FAMILY = 'stable fluid'
    METHOD = 'Stam stable fluids (semi-Lagrangian advection, 24 Jacobi pressure iterations, vorticity confinement) with orbiting neon dye emitters in a dark gel'
    PALETTE = {'base': '#140a2a', 'highlight': '#e6fbff', 'shadow': '#05030c', 'rim': '#00e5ff'}
    SPEC = {**COMMON, 'geometry': 'flat gel', 'optics': 'additive dye emission, faint refraction',
            'motion': 'two emitters orbit, dye curls into vortices', 'interaction': 'press = central radial burst of white dye',
            'hierarchy': 'tier 5; high entropy: one per screen', 'rarity': 'Mythic: tri-colour dye'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.sim = fl.StableFluid(self.fw // 2, self.fh // 2, self.seed); self.burst = False

    def frame(self, t, press):
        s = self.sim; W, Hh = s.w, s.h
        for i, col in enumerate(((0, .9, 1.0), (1.0, .2, .8))):
            a = t * .8 + i * 3.1416
            px = W / 2 + W * .32 * math.cos(a); py = Hh / 2 + Hh * .3 * math.sin(a * 1.3)
            s.splat(px, py, -math.sin(a) * 1.4, math.cos(a) * 1.4, np.array(col) * .14, r=3.0)
        if press > .6 and not self.burst:
            for k in range(8):
                a = k / 8 * 6.2832
                s.splat(W / 2, Hh / 2, math.cos(a) * 5, math.sin(a) * 5, (.5, .5, .55), r=4)
            self.burst = True
        if press < .1:
            self.burst = False
        dye = s.step(1.0, iters=24, vort=.35, fade=.985)
        dye = fl.resize(dye, self.fw, self.fh)
        rgb = op.srgb_to_linear(np.full(3, .06, F32)) + H('#140a2a') + dye * 1.4
        return op.tonemap(rgb), np.clip(dye.max(-1), 0, 1)


ORDER_12 = ['hydroglass', 'prism_gel', 'solar_plasma', 'bio_slime',
            'crystal_ice', 'holo_foil', 'void', 'electric_glass',
            'molten_core', 'verdant_coral', 'opal', 'nebula']
ORDER_EXTRA = ['liquid_chrome', 'aurora', 'ferrofluid', 'quantum_ink']
