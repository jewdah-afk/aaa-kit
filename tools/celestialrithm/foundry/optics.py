"""Optics for the material foundry: normals, refraction caustics, spectral colour,
thin-film interference, diffraction gratings, blackbody emission, OKLab.

Physics is real where it is cheap (Snell refraction for caustics, the thin-film
phase term, the grating equation, Planck's law); the final look is graded to the
kit's stylized palette by each material.
"""
from __future__ import annotations

import numpy as np

from .fields import F32, blur

# ---------------------------------------------------------------- spectral colour
# CIE 1931 2-degree observer, multi-lobe Gaussian fit (Wyman, Sloan & Shirley 2013).
def _g(x, mu, s1, s2):
    s = np.where(x < mu, s1, s2)
    return np.exp(-.5 * ((x - mu) / s) ** 2)


def cie_xyz(lam):
    lam = np.asarray(lam, np.float64)
    x = 1.056 * _g(lam, 599.8, 37.9, 31.0) + .362 * _g(lam, 442.0, 16.0, 26.7) - .065 * _g(lam, 501.1, 20.4, 26.2)
    y = .821 * _g(lam, 568.8, 46.9, 40.5) + .286 * _g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * _g(lam, 437.0, 11.8, 36.0) + .681 * _g(lam, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], -1)


XYZ2RGB = np.array([[3.2406, -1.5372, -.4986], [-.9689, 1.8758, .0415], [.0557, -.2040, 1.0570]])
LAMBDAS = np.linspace(390, 720, 34)
CMF = cie_xyz(LAMBDAS)                       # (34, 3)
CMF_RGB = CMF @ XYZ2RGB.T                    # linear sRGB response per wavelength
CMF_RGB /= CMF_RGB[:, 1].sum()               # unit luminance for a flat spectrum


def wavelength_rgb(lam):
    """Linear RGB of a pure wavelength (clipped, gently desaturated so it stays in gamut)."""
    rgb = cie_xyz(lam) @ XYZ2RGB.T
    rgb = np.clip(rgb, 0, None)
    m = rgb.max(-1, keepdims=True) + 1e-6
    return (rgb / m).astype(F32)


def thin_film(thickness_nm, cos_t=1.0, n_film=1.33, strength=1.0):
    """Reflected colour of a thin film (soap/oil) of given thickness.

    Two-beam interference: R(lambda) = 0.5 * (1 - cos(4*pi*n*d*cos(theta)/lambda)),
    the extra pi from the reflection at the denser interface. Integrated against
    the CIE matching functions -> linear RGB.
    """
    d = np.asarray(thickness_nm, F32)[..., None]
    phase = 4 * np.pi * n_film * d * np.asarray(cos_t, F32)[..., None] / LAMBDAS.astype(F32)
    R = .5 * (1 - np.cos(phase))
    rgb = (R @ CMF_RGB.astype(F32)) * 2.0 * strength
    return np.clip(rgb, 0, 4).astype(F32)


def grating(light_x, light_y, gx, gy, pitch_nm=1300.0, orders=(1, 2), bandwidth=22.0):
    """Diffraction-grating sparkle (holographic foil).

    For grating direction g and the projected light-minus-view tilt s, order m
    reflects wavelength lambda = pitch * |s . g| / m. Each pixel gets the colour
    of that wavelength, weighted by how close it is to the visible band.
    """
    s = np.abs(light_x * gx + light_y * gy)
    out = 0
    for m in orders:
        lam = pitch_nm * s / m
        w = np.exp(-.5 * np.clip((np.abs(lam - 555) - 165) / bandwidth, 0, None) ** 2)
        out = out + wavelength_rgb(np.clip(lam, 380, 730)) * w[..., None] / m
    return np.asarray(out, F32)


def blackbody(temp_k):
    """Linear RGB of a black body at temp_k (Planck), normalised to max channel 1."""
    t = np.asarray(temp_k, np.float64)[..., None]
    lam = LAMBDAS * 1e-9
    c1, c2 = 3.741771e-16, 1.4387769e-2
    spec = c1 / (lam ** 5 * (np.exp(np.minimum(c2 / (lam * t), 700)) - 1))
    rgb = spec @ CMF_RGB
    rgb = np.clip(rgb, 0, None)
    return (rgb / (rgb.max(-1, keepdims=True) + 1e-30)).astype(F32)


_BB_T = np.linspace(800, 12000, 512)
_BB_LUT = blackbody(_BB_T)


def blackbody_lut(temp_k):
    idx = np.clip((np.asarray(temp_k) - 800) / (12000 - 800) * 511, 0, 511).astype(int)
    return _BB_LUT[idx]


# ---------------------------------------------------------------- surfaces
def normals(height, scale=1.0, wrap=False):
    if wrap:
        gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5
        gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5
    else:
        gy, gx = np.gradient(height)
    nx = -gx * scale; ny = -gy * scale; nz = np.ones_like(nx)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / n).astype(F32), (ny / n).astype(F32), (nz / n).astype(F32)


def fresnel_schlick(cos_t, f0=.04):
    return f0 + (1 - f0) * (1 - np.clip(cos_t, 0, 1)) ** 5


def blinn(nx, ny, nz, lx, ly, lz, power):
    hx, hy, hz = lx, ly, lz + 1.0
    hn = np.sqrt(hx * hx + hy * hy + hz * hz)
    d = np.clip((nx * hx + ny * hy + nz * hz) / hn, 0, 1)
    return d ** power


def caustics(height, depth=18.0, ior=1.33, light=(0.0, 0.0), sigma=.8, wrap=True):
    """Photon-splat caustics: refract a vertical light grid through the height field.

    Every source texel is displaced by +depth * (1 - 1/ior) * grad(h) (small-angle
    Snell: the transmitted ray bends toward the normal, so a convex dome focuses
    light under its peak), then splatted bilinearly. Converging rays pile up into bright
    filaments: the real caustic network, not a cosine imitation.
    """
    H, W = height.shape
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5
    k = depth * (1 - 1 / ior)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    px = xx + k * gx + light[0]; py = yy + k * gy + light[1]
    x0 = np.floor(px).astype(int); y0 = np.floor(py).astype(int)
    fx = px - x0; fy = py - y0
    acc = np.zeros(H * W, np.float64)
    for ox, oy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi = (x0 + ox) % W if wrap else np.clip(x0 + ox, 0, W - 1)
        yi = (y0 + oy) % H if wrap else np.clip(y0 + oy, 0, H - 1)
        acc += np.bincount((yi * W + xi).ravel(), weights=w.ravel(), minlength=H * W)
    c = acc.reshape(H, W).astype(F32)
    return blur(c, sigma, wrap) if sigma > 0 else c


def env_reflect(nx, ny, nz, horizon, sky, ground, sun_dir=(-.35, -.6), sun_color=(1, 1, 1), sun_power=60, bias=0.0):
    """Stylized environment reflection (matcap-like) for chrome/mercury.

    Reflect the view vector (0,0,1) about the normal; the reflected y picks a
    sky -> horizon -> ground gradient, plus a sharp sun lobe.
    """
    ry = 2 * nz * ny
    rx = 2 * nz * nx
    t = np.clip((ry + bias) * .5 + .5, 0, 1)[..., None]
    sky, horizon, ground = (np.asarray(c, F32) for c in (sky, horizon, ground))
    lo = np.clip(t / .5, 0, 1); hi = np.clip((t - .5) / .5, 0, 1)
    col = np.where(t < .5, ground + (horizon - ground) * lo ** .7, horizon + (sky - horizon) * hi ** 1.4)
    band = np.exp(-((ry + bias + .05) / .05) ** 2)[..., None] * .6            # bright horizon line
    sd = np.clip(rx * sun_dir[0] + ry * sun_dir[1], 0, 1) ** sun_power
    return (col + band * horizon + sd[..., None] * np.asarray(sun_color, F32)).astype(F32)


# ---------------------------------------------------------------- colour science
def srgb_to_linear(c):
    c = np.asarray(c, F32)
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, F32), 0, None)
    return np.where(c <= .0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - .055)


def linear_to_oklab(rgb):
    """Ottosson 2020 OKLab from linear sRGB."""
    M1 = np.array([[.4122214708, .5363325363, .0514459929], [.2119034982, .6806995451, .1073969566],
                   [.0883024619, .2817188376, .6299787005]], F32)
    M2 = np.array([[.2104542553, .7936177850, -.0040720468], [1.9779984951, -2.4285922050, .4505937099],
                   [.0259040371, .7827717662, -.8086757660]], F32)
    lms = np.cbrt(np.clip(rgb @ M1.T, 0, None))
    return lms @ M2.T


def hex_rgb(h):
    """'#rrggbb' -> linear RGB float32."""
    h = h.lstrip('#')
    return srgb_to_linear(np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32))


def ramp(t, stops):
    """Piecewise-linear colour ramp. stops = [(pos, linear_rgb), ...] sorted by pos."""
    t = np.clip(np.asarray(t, F32), 0, 1)
    pos = np.array([p for p, _ in stops], F32)
    cols = np.stack([np.asarray(c, F32) for _, c in stops])
    i = np.clip(np.searchsorted(pos, t, side='right') - 1, 0, len(pos) - 2)
    a = pos[i]; b = pos[i + 1]
    f = ((t - a) / np.maximum(b - a, 1e-6))[..., None]
    return (cols[i] * (1 - f) + cols[i + 1] * f).astype(F32)


def tonemap(rgb, exposure=1.0, shoulder=.85):
    """Soft-clip highlights so bright optics bloom to white without hard clipping.

    Below `shoulder` the curve is linear (keeps graded palettes exact); above it
    approaches 1 asymptotically, desaturating toward white like film.
    """
    x = np.asarray(rgb, F32) * exposure
    over = np.maximum(x - shoulder, 0)
    comp = shoulder + (1 - shoulder) * (1 - np.exp(-over / (1 - shoulder)))
    y = np.where(x > shoulder, comp, x)
    lum = (x * np.array([.2126, .7152, .0722], F32)).sum(-1, keepdims=True)
    white = np.clip((lum - 1.0) * .35, 0, 1)                       # hot cores go white
    return np.clip(y * (1 - white) + white, 0, 1).astype(F32)
