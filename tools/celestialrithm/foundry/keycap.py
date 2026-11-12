"""Squared Stud UI keycap shell, composited from signed-distance functions.

Layers, back to front (all in linear RGB):
  drop shadow -> stepped under-face extrusion (the depth) -> black ink silhouette
  -> lit bezel ring (normal from the SDF gradient) -> inner ink line
  -> material face -> inner glass rim in the material colour -> inner shadow
  (SDF ambient occlusion) -> thin clearcoat strip -> top-lip specular -> optional sweep.

The face never moves: interaction only changes light, never position or the
hitbox (VISUAL_APPROVAL_CONTRACT: stationary keys, no cursor magnetism).
All geometry masks are computed once per Shell and cached; per frame only the
colour arithmetic and one small glow blur run.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .fields import F32, blur, smoothstep


def sd_round_rect(x, y, hw, hh, r):
    qx = np.abs(x) - hw + r; qy = np.abs(y) - hh + r
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2)
    return (out + np.minimum(np.maximum(qx, qy), 0) - r).astype(F32)


def cover(d, aa=.75):
    """Anti-aliased coverage of the region d < 0."""
    return np.clip(.5 - d / (2 * aa), 0, 1).astype(F32)


@dataclass(frozen=True)
class Shell:
    w: int = 272                  # outer width incl. ink
    h: int = 148
    radius: float = 9             # tight squared corners
    ink: float = 4.0              # black outer silhouette
    bezel: float = 7.0            # lit frame ring between ink and face
    inner_ink: float = 2.0
    depth: int = 10               # visible extrusion under the face (px)
    steps: int = 3                # stepped bevel bands in the extrusion
    pad: int = 24

    @property
    def face_w(self):
        return int(self.w - 2 * (self.ink + self.bezel + self.inner_ink))

    @property
    def face_h(self):
        return int(self.h - 2 * (self.ink + self.bezel + self.inner_ink)) - self.depth


INK = np.array([0.0035, 0.004, 0.0075], F32)


@lru_cache(maxsize=8)
def geometry(sh: Shell):
    """All static masks for one shell size."""
    pad = sh.pad
    W = sh.w + 2 * pad; H = sh.h + 2 * pad + sh.depth
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    px = xx + .5 - (pad + sh.w / 2); py = yy + .5 - (pad + sh.h / 2)
    top_h = sh.h - sh.depth
    cyo = -sh.depth / 2
    hw = sh.w / 2
    g = {'W': W, 'H': H}
    d_cap = sd_round_rect(px, py - cyo, hw, top_h / 2, sh.radius)
    d_body = sd_round_rect(px, py - cyo - sh.depth / 2, hw, top_h / 2 + sh.depth / 2, sh.radius)
    sd = sd_round_rect(px, py - cyo - sh.depth - 5, hw - 3, top_h / 2 + sh.depth / 2, sh.radius + 5)
    g['shadow'] = blur(cover(sd, 1.0), 6) * .7
    g['body'] = cover(d_body)
    under = np.clip((py - cyo - top_h / 2 + sh.ink) / max(sh.depth + sh.ink, 1), 0, 1)
    step_i = np.floor(under * sh.steps); band_t = under * sh.steps - step_i
    g['side_shade'] = ((0.8 - .2 * step_i) * (1 - .55 * (np.abs(px) / hw) ** 6)).astype(F32)
    g['side_edge'] = (smoothstep(.3, 0, band_t) * (step_i < sh.steps) * (step_i > 0)).astype(F32)
    ink = cover(d_body) * (1 - cover(d_body + sh.ink))
    ink_top = cover(d_cap) * (1 - cover(d_cap + sh.ink))
    seam = cover(np.abs(py - cyo - top_h / 2 + .5) - 1.0) * cover(d_body + sh.ink * .5)
    g['ink'] = np.maximum(np.maximum(ink, ink_top), seam)
    g['cap'] = cover(d_cap + sh.ink)
    gx = np.gradient(d_cap, axis=1); gy = np.gradient(d_cap, axis=0)
    gn = np.sqrt(gx * gx + gy * gy) + 1e-6
    nx, ny = gx / gn, gy / gn
    across = np.clip((-d_cap - sh.ink) / sh.bezel, 0, 1)
    facing = -(nx * -.5 + ny * -.86)            # >0 where the outward normal faces the top-left key light
    outer = (1 - across) ** 1.5
    g['bez_light'] = (.25 + .55 * np.clip(facing, -1, 1) * outer - .35 * np.clip(facing, -1, 1) * across).astype(F32)
    g['bez_spec'] = (np.exp(-((across - .2) / .09) ** 2) * np.clip(facing, 0, 1) ** 2).astype(F32)
    g['bez_inner'] = (across ** 3).astype(F32)   # inner edge: catches the face's glow
    fw, fh = sh.face_w, sh.face_h
    face_d = sd_round_rect(px, py - cyo, fw / 2, fh / 2, max(sh.radius - sh.bezel * .7, 2.0))
    g['face'] = cover(face_d)
    g['inner_line'] = cover(face_d - sh.inner_ink) * (1 - g['face'])
    g['fx0'] = int(round(pad + sh.w / 2 - fw / 2)); g['fy0'] = int(round(pad + sh.h / 2 + cyo - fh / 2))
    din = np.clip(-face_d, 0, None)
    fv = (py - cyo + fh / 2) / fh; fu = (px + fw / 2) / fw
    g['fu'], g['fv'] = fu, fv
    g['ao'] = (1 - .5 * np.exp(-din / 4.0) - .18 * np.exp(-din / 14.0) * smoothstep(.2, 1.0, fv)).astype(F32)
    g['rim'] = (np.exp(-din / 2.2) * .55 + np.exp(-din / 7) * .12).astype(F32)       # inner glass rim
    g['clear'] = (smoothstep(.02, .07, fv) * smoothstep(.2, .1, fv) * smoothstep(0, .08, fu) * smoothstep(1, .92, fu)).astype(F32)
    g['lip'] = (np.exp(-((din - 1.6) / .9) ** 2) * smoothstep(.3, .0, fv)).astype(F32)
    g['corner'] = np.exp(-(((px + fw / 2 - 6) ** 2 + (py - cyo + fh / 2 - 5) ** 2) / 10)).astype(F32)
    return g


def compose(canvas, cx, cy, shell: Shell, face, glow, tint, t, sweep=-1.0, press=0.0):
    """Draw one key centred at (cx, cy) on canvas (H, W, 3 linear).

    face  : (fh, fw, 3) linear material colour
    glow  : (fh, fw) emissive amount 0..1 (bleeds into the bezel, never outside the ink)
    tint  : dict of 'rim', 'shadow', 'highlight' linear colours from the material
    sweep : 0..1 position of a diagonal light sweep (<0 = none)
    press : 0..1 activation: lifts exposure and rim light, no movement
    """
    sh = shell; g = geometry(sh)
    W, H = g['W'], g['H']
    x0 = int(cx - sh.w / 2) - sh.pad; y0 = int(cy - sh.h / 2) - sh.pad
    # clip against the canvas: work on a full-size temp, write back the overlap
    CH, CW = canvas.shape[:2]
    ya, yb = max(y0, 0), min(y0 + H, CH); xa, xb = max(x0, 0), min(x0 + W, CW)
    region = np.zeros((H, W, 3), F32)
    region[ya - y0:yb - y0, xa - x0:xb - x0] = canvas[ya:yb, xa:xb]
    out = region * (1 - g['shadow'])[..., None]
    fh, fw = face.shape[:2]
    fx0, fy0 = g['fx0'], g['fy0']
    mean_face = face.reshape(-1, 3).mean(0)

    # extrusion: material-tinted dark sides, lit step edges
    side = (tint['shadow'] * .7 + mean_face * .12) * g['side_shade'][..., None] + tint['rim'] * (g['side_edge'] * .22)[..., None]
    out = out * (1 - g['body'][..., None]) + side * g['body'][..., None]

    # bezel: dark gunmetal, key-lit, material-coloured inner edge
    base = np.array([.016, .02, .034], F32)
    bez = base * (1 + 2.2 * g['bez_light'])[..., None] + (tint['highlight'] * .35 + .25) * (g['bez_spec'] * .7)[..., None]
    bez = bez + tint['rim'] * (g['bez_inner'] * (.10 + .25 * press))[..., None]
    # glow bleed: the face's emissive light spills onto the inner bezel only
    gb = np.zeros((H, W, 3), F32)
    gb[fy0:fy0 + fh, fx0:fx0 + fw] = face * glow[..., None]
    small = gb[::2, ::2]
    small = np.stack([blur(small[..., c], 3.0) for c in range(3)], -1)
    bleed = np.repeat(np.repeat(small, 2, 0), 2, 1)[:H, :W]
    bez = bez + bleed * (g['bez_inner'] * (.9 + .9 * press))[..., None]
    out = out * (1 - g['cap'][..., None]) + bez * g['cap'][..., None]
    out = out * (1 - g['inner_line'][..., None]) + INK * g['inner_line'][..., None]

    # face + glass treatment
    fb = np.zeros((H, W, 3), F32)
    fb[fy0:fy0 + fh, fx0:fx0 + fw] = face * (1 + .25 * press)
    hl = tint['highlight'] * .35 + .65
    fr = fb * g['ao'][..., None]
    fr = fr + tint['rim'] * (g['rim'] * (.55 + .5 * press))[..., None] * .5 + fb * g['rim'][..., None] * .35
    fr = fr + hl * (g['clear'] * .016 + g['lip'] * .3 + g['corner'] * .5)[..., None]
    if sweep >= 0:
        s = (g['fu'] + .45 * g['fv']) / 1.45
        c = sweep * 1.5 - .25
        band = np.exp(-((s - c) / .05) ** 2) * .22 + np.exp(-((s - c + .07) / .012) ** 2) * .35
        fr = fr + hl * band[..., None]
    out = out * (1 - g['face'][..., None]) + fr * g['face'][..., None]
    out = out * (1 - g['ink'][..., None]) + INK * g['ink'][..., None]
    canvas[ya:yb, xa:xb] = out[ya - y0:yb - y0, xa - x0:xb - x0]
    return (x0 + fx0, y0 + fy0, fw, fh)
