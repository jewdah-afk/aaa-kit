#!/usr/bin/env python3
"""Hierarchy auditor: measure whether the eye goes where the design says it should.

Needs only numpy and Pillow. Every model here is cited in docs/research/85-measuring-hierarchy.md.

  python3 tools/hierarchy/hierarchy.py audit shot.png --focus 120,40,200,80 [--out report]
  python3 tools/hierarchy/hierarchy.py apca '#888888' '#ffffff'
  python3 tools/hierarchy/hierarchy.py flash effect.gif
  python3 tools/hierarchy/hierarchy.py cvd shot.png --type deutan --out shot-deutan.png

audit   predicted scanpath (salience + winner-take-all + inhibition of return), focus lift,
        loudest competitor, squint value gap, colour-blind re-check, clutter. Writes a heatmap
        overlay PNG and a JSON report. Exit 1 on FAIL.
apca    APCA 0.0.98G Lc (text on background) plus the WCAG 2.x ratio.
flash   WCAG 2.3.1 general and red flash count per second over a GIF or a folder of frames.
cvd     Machado 2009 colour-vision-deficiency simulation.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageSequence

# ---------------------------------------------------------------- colour maths

def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    """sRGB 0..1 -> linear light (IEC 61966-2-1, the 0.04045 threshold WCAG uses since 2021)."""
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def relative_luminance(rgb01: np.ndarray) -> np.ndarray:
    """WCAG relative luminance from sRGB 0..1, shape (...,3)."""
    lin = srgb_to_linear(rgb01)
    return lin @ np.array([0.2126, 0.7152, 0.0722])


# Ottosson 2020, linear sRGB -> LMS -> OKLab
_OK_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
_OK_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])


def oklab(rgb01: np.ndarray) -> np.ndarray:
    lms = srgb_to_linear(rgb01) @ _OK_M1.T
    return np.cbrt(lms) @ _OK_M2.T


# Machado, Oliveira & Fernandes 2009, severity 1.0, applied to linear RGB
_CVD = {
    "protan": np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
    "tritan": np.array([[1.255528, -0.076749, -0.178779],
                        [-0.078411, 0.930809, 0.147602],
                        [0.004733, 0.691367, 0.303900]]),
}


def simulate_cvd(rgb01: np.ndarray, kind: str, severity: float = 1.0) -> np.ndarray:
    m = np.eye(3) * (1 - severity) + _CVD[kind] * severity
    return linear_to_srgb(srgb_to_linear(rgb01) @ m.T)


# ---------------------------------------------------------------- contrast

_APCA = dict(trc=2.4, r=0.2126729, g=0.7151522, b=0.0721750, normBG=0.56, normTXT=0.57,
             revTXT=0.62, revBG=0.65, blkThrs=0.022, blkClmp=1.414, scale=1.14, offset=0.027,
             deltaYmin=0.0005, loClip=0.1)


def _apca_y(rgb255) -> float:
    k = _APCA
    r, g, b = (float(v) / 255.0 for v in rgb255)
    return k["r"] * r ** k["trc"] + k["g"] * g ** k["trc"] + k["b"] * b ** k["trc"]


def apca_lc(text_rgb, bg_rgb) -> float:
    """APCA 0.0.98G-4g lightness contrast. Positive = dark text on light, negative = light on dark."""
    k = _APCA
    t, b = _apca_y(text_rgb), _apca_y(bg_rgb)
    if t <= k["blkThrs"]:
        t += (k["blkThrs"] - t) ** k["blkClmp"]
    if b <= k["blkThrs"]:
        b += (k["blkThrs"] - b) ** k["blkClmp"]
    if abs(b - t) < k["deltaYmin"]:
        return 0.0
    if b > t:
        s = (b ** k["normBG"] - t ** k["normTXT"]) * k["scale"]
        out = 0.0 if s < k["loClip"] else s - k["offset"]
    else:
        s = (b ** k["revBG"] - t ** k["revTXT"]) * k["scale"]
        out = 0.0 if s > -k["loClip"] else s + k["offset"]
    return out * 100.0


def wcag_ratio(a_rgb, b_rgb) -> float:
    la = float(relative_luminance(np.array(a_rgb, dtype=float) / 255.0))
    lb = float(relative_luminance(np.array(b_rgb, dtype=float) / 255.0))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def parse_hex(s: str):
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- filters

def _gauss_kernel(sigma: float) -> np.ndarray:
    r = max(1, int(math.ceil(sigma * 3)))
    x = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-(x * x) / (2 * sigma * sigma))
    return k / k.sum()


def blur(img: np.ndarray, sigma: float) -> np.ndarray:
    """Separable Gaussian blur with edge padding. img is 2-D float."""
    if sigma <= 0:
        return img
    k = _gauss_kernel(sigma)
    r = len(k) // 2
    p = np.pad(img, ((0, 0), (r, r)), mode="edge")
    out = np.zeros_like(img, dtype=float)
    for i, w in enumerate(k):
        out += w * p[:, i:i + img.shape[1]]
    p = np.pad(out, ((r, r), (0, 0)), mode="edge")
    out2 = np.zeros_like(img, dtype=float)
    for i, w in enumerate(k):
        out2 += w * p[i:i + img.shape[0], :]
    return out2


def _norm(a: np.ndarray) -> np.ndarray:
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def _resize(a: np.ndarray, w: int, h: int) -> np.ndarray:
    return np.array(Image.fromarray(a.astype(np.float32), mode="F").resize((w, h), Image.BILINEAR), dtype=float)


# ---------------------------------------------------------------- salience

def spectral_residual(gray: np.ndarray, width: int = 64) -> np.ndarray:
    """Hou & Zhang 2007: log-amplitude minus its local average, back to space, squared, blurred."""
    h, w = gray.shape
    sh = max(8, round(width * h / w))
    small = _resize(gray, width, sh)
    f = np.fft.fft2(small)
    log_amp = np.log(np.abs(f) + 1e-9)
    phase = np.angle(f)
    pad = np.pad(log_amp, 1, mode="wrap")
    avg = sum(pad[i:i + sh, j:j + width] for i in range(3) for j in range(3)) / 9.0
    sal = np.abs(np.fft.ifft2(np.exp((log_amp - avg) + 1j * phase))) ** 2
    sal = blur(sal, sigma=width / 64 * 2.5)
    return _resize(_norm(sal), w, h)


def center_surround(lab: np.ndarray, work_w: int = 160) -> np.ndarray:
    """Itti, Koch & Niebur 1998 in spirit: |fine - coarse| on OKLab L, a, b, summed across scales.
    Each channel map is normalised and weighted by how few strong peaks it has, so one odd item
    beats a texture of many."""
    h, w = lab.shape[:2]
    sh = max(8, round(work_w * h / w))
    chans = [_resize(lab[..., i], work_w, sh) for i in range(3)]
    chans[1] *= 2.0   # a/b span ~ +-0.3 vs L 0..1; bring them to a comparable range
    chans[2] *= 2.0
    total = np.zeros((sh, work_w))
    for c in chans:
        cmap = np.zeros_like(total)
        for centre, surround in ((1, 4), (1, 8), (2, 8), (2, 16)):
            cmap += np.abs(blur(c, centre) - blur(c, surround))
        cmap = _norm(cmap)
        peaks = (cmap > 0.5).mean()           # fraction of area that is "loud"
        weight = (1.0 - min(peaks * 4, 0.9))  # many loud spots = texture = less salient
        total += cmap * weight
    return _resize(_norm(total), w, h)


def salience_map(rgb01: np.ndarray, centre_bias: float = 0.0) -> np.ndarray:
    lab = oklab(rgb01)
    sal = 0.5 * spectral_residual(lab[..., 0]) + 0.5 * center_surround(lab)
    sal = _norm(sal) ** 2   # Itti's N(): promote few strong peaks over broad halos
    if centre_bias > 0:
        h, w = sal.shape
        yy, xx = np.mgrid[0:h, 0:w]
        g = np.exp(-(((xx - w / 2) / (0.35 * w)) ** 2 + ((yy - h / 2) / (0.35 * h)) ** 2) / 2)
        sal = (1 - centre_bias) * sal + centre_bias * g
    return _norm(sal)


def scanpath(sal: np.ndarray, n: int = 5, ior_radius: float = 0.08):
    """Winner-take-all with inhibition of return: take the peak, suppress a disc, repeat."""
    s = sal.copy()
    h, w = s.shape
    r = ior_radius * math.hypot(w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    out = []
    for _ in range(n):
        y, x = np.unravel_index(int(np.argmax(s)), s.shape)
        out.append((int(x), int(y), float(sal[y, x])))
        s = s * (1 - np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r / 2) ** 2)))
    return out


# ---------------------------------------------------------------- audit

def _in(rect, x, y):
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


def _mask(shape, rects):
    m = np.zeros(shape, dtype=bool)
    for rx, ry, rw, rh in rects:
        m[max(0, ry):ry + rh, max(0, rx):rx + rw] = True
    return m


def clutter(rgb01: np.ndarray) -> dict:
    """Edge density (Mack & Oliva) and OKLab chroma spread: cheap stand-ins for feature congestion."""
    lab = oklab(rgb01)
    L = lab[..., 0]
    gx = np.abs(np.diff(L, axis=1, prepend=L[:, :1]))
    gy = np.abs(np.diff(L, axis=0, prepend=L[:1, :]))
    edges = float(((gx + gy) > 0.04).mean())
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    return {"edge_density": round(edges, 4), "chroma_std": round(float(chroma.std()), 4)}


def audit(rgb01: np.ndarray, focus: list, centre_bias: float = 0.0, fixations: int = 5) -> dict:
    h, w = rgb01.shape[:2]
    sal = salience_map(rgb01, centre_bias)
    path = scanpath(sal, fixations)
    m = _mask(sal.shape, focus) if focus else None
    rep = {"size": [w, h], "fixations": [{"x": x, "y": y, "salience": round(v, 3),
                                           "in_focus": bool(focus and any(_in(r, x, y) for r in focus))}
                                          for x, y, v in path],
           "clutter": clutter(rgb01)}
    if focus:
        area = m.mean()
        share = float(sal[m].sum() / max(sal.sum(), 1e-9))
        focus_peak = float(sal[m].max())
        outside = sal.copy()
        outside[m] = 0
        comp_y, comp_x = np.unravel_index(int(np.argmax(outside)), outside.shape)
        competitor = float(outside[comp_y, comp_x]) / max(focus_peak, 1e-9)
        # squint test: blur ~1% of the diagonal, compare focus value against a ring around it
        L = oklab(rgb01)[..., 0]
        sq = blur(L, 0.01 * math.hypot(w, h))
        ring = _mask(sal.shape, [(x - rw // 2, y - rh // 2, rw * 2, rh * 2) for x, y, rw, rh in focus]) & ~m
        squint_gap = float(abs(sq[m].mean() - sq[ring].mean())) if ring.any() else 0.0
        first = rep["fixations"][0]["in_focus"]
        cvd = {}
        for kind in ("deutan", "protan"):
            s2 = salience_map(simulate_cvd(rgb01, kind), centre_bias)
            p2 = scanpath(s2, 1)[0]
            cvd[kind] = {"first_fixation_in_focus": any(_in(r, p2[0], p2[1]) for r in focus),
                         "lift": round(float(s2[m].sum() / max(s2.sum(), 1e-9)) / area, 2)}
        lift = share / area
        verdict = "PASS"
        reasons = []
        if not first:
            verdict, _ = "FAIL", reasons.append("first predicted fixation is outside the focus")
        if lift < 1.5:
            verdict = "FAIL" if lift < 1.0 else ("WARN" if verdict == "PASS" else verdict)
            reasons.append(f"focus lift {lift:.2f} (want >= 1.5: the focus should hold more than its share)")
        if competitor >= 0.9:
            verdict = "WARN" if verdict == "PASS" else verdict
            reasons.append(f"a competitor at ({comp_x},{comp_y}) reaches {competitor:.0%} of the focus peak")
        if squint_gap < 0.08:
            verdict = "WARN" if verdict == "PASS" else verdict
            reasons.append(f"squint value gap {squint_gap:.3f} OKLab L (want >= 0.08)")
        for kind, c in cvd.items():
            if not c["first_fixation_in_focus"]:
                verdict = "WARN" if verdict == "PASS" else verdict
                reasons.append(f"under {kind} simulation the first fixation leaves the focus")
        rep.update({"focus": focus, "focus_area": round(float(area), 4), "focus_share": round(share, 4),
                    "lift": round(lift, 2), "competitor": {"x": int(comp_x), "y": int(comp_y),
                                                           "ratio": round(competitor, 2)},
                    "squint_gap": round(squint_gap, 3), "cvd": cvd, "verdict": verdict,
                    "reasons": reasons})
    return rep, sal


def overlay(rgb01: np.ndarray, sal: np.ndarray, rep: dict) -> Image.Image:
    base = Image.fromarray((rgb01 * 255).astype(np.uint8)).convert("L").convert("RGB")
    s = sal[..., None]
    heat = np.concatenate([np.clip(s * 3, 0, 1), np.clip(s * 3 - 1, 0, 1), np.clip(s * 3 - 2, 0, 1)], -1)
    mix = (np.asarray(base, dtype=float) / 255 * 0.55 + heat * 0.45 * (0.3 + 0.7 * s))
    img = Image.fromarray((np.clip(mix, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for r in rep.get("focus") or []:
        d.rectangle([r[0], r[1], r[0] + r[2], r[1] + r[3]], outline=(80, 200, 255), width=2)
    rad = max(6, int(0.012 * math.hypot(*img.size)))
    for i, f in enumerate(rep["fixations"], 1):
        x, y = f["x"], f["y"]
        col = (60, 230, 120) if f["in_focus"] else (255, 70, 70)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], outline=col, width=3)
        d.text((x + rad + 2, y - rad), str(i), fill=col)
    return img


# ---------------------------------------------------------------- flash

def _uv(rgb01: np.ndarray) -> np.ndarray:
    lin = srgb_to_linear(rgb01)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    X, Y, Z = np.moveaxis(lin @ M.T, -1, 0)
    d = X + 15 * Y + 3 * Z + 1e-9
    return np.stack([4 * X / d, 9 * Y / d], -1)


def load_frames(path: Path, max_w: int = 64):
    frames, durs = [], []
    if path.is_dir():
        for p in sorted(path.glob("*.png")):
            frames.append(p)
        imgs = [Image.open(p).convert("RGB") for p in frames]
        durs = [1000 / 30] * len(imgs)
    else:
        im = Image.open(path)
        imgs = []
        for fr in ImageSequence.Iterator(im):
            imgs.append(fr.convert("RGB"))
            durs.append(fr.info.get("duration", im.info.get("duration", 33)) or 33)
    out = []
    for im in imgs:
        if im.width > max_w:
            # area-average: 64 blocks across ~ 0.5 deg each on a 30-deg-wide screen, so small fast
            # particles moving over a pixel are not counted as flashes; --fine analyses 256 across
            im = im.resize((max_w, max(1, round(im.height * max_w / im.width))), Image.BOX)
        out.append(np.asarray(im, dtype=float) / 255.0)
    return out, durs


def flash_check(frames, durs_ms) -> dict:
    """WCAG 2.3.1 (2.2 wording): a flash is a pair of opposing changes in relative luminance of
    >= 0.10 where the darker state is < 0.80; a red flash is a pair of opposing transitions to or
    from saturated red (R/(R+G+B) >= 0.8 and a u'v' change > 0.2). Fail when more than 3 flashes
    happen in any 1 s window over an area larger than 25% of a 10-degree field, i.e. 21,824 px of a
    1024x768 screen (2.78% of the frame)."""
    if len(frames) < 3:
        return {"frames": len(frames), "verdict": "PASS", "note": "too few frames"}
    h, w = frames[0].shape[:2]
    area_limit = 21824 / (1024 * 768)
    t = np.cumsum([0] + list(durs_ms[:-1])) / 1000.0
    Y = [relative_luminance(f) for f in frames]
    UV = [_uv(f) for f in frames]
    RED = [(f[..., 0] / (f.sum(-1) + 1e-9)) >= 0.8 for f in frames]

    def events(kind):
        last_sign = np.zeros((h, w), dtype=np.int8)
        ev = []   # per frame index: boolean mask of pixels completing a flash
        for i in range(1, len(frames)):
            if kind == "general":
                d = Y[i] - Y[i - 1]
                big = (np.abs(d) >= 0.10) & (np.minimum(Y[i], Y[i - 1]) < 0.80)
            else:
                # +1 = a transition into saturated red, -1 = out of it
                d = np.where(RED[i], 1.0, -1.0)
                big = (np.hypot(*np.moveaxis(UV[i] - UV[i - 1], -1, 0)) > 0.2) & (RED[i] != RED[i - 1])
            sign = np.sign(d).astype(np.int8) * big
            done = big & (last_sign != 0) & (sign == -last_sign)
            last_sign = np.where(big, sign, last_sign)
            ev.append((t[i], done))
        return ev

    result = {"frames": len(frames), "seconds": round(float(t[-1] + durs_ms[-1] / 1000), 2),
              "area_limit_fraction": round(area_limit, 4)}
    verdict = "PASS"
    for kind in ("general", "red"):
        ev = events(kind)
        worst = 0.0
        worst_t = 0.0
        for j, (tj, _) in enumerate(ev):
            window = [m for (tk, m) in ev[j:] if tk < tj + 1.0]
            count = np.sum(window, axis=0)
            frac = float((count > 3).mean())
            if frac > worst:
                worst, worst_t = frac, tj
        result[kind] = {"worst_area_fraction_over_3_per_s": round(worst, 4), "at_s": round(float(worst_t), 2)}
        if worst > area_limit:
            verdict = "FAIL"
    result["verdict"] = verdict
    return result


# ---------------------------------------------------------------- cli

def _load(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit")
    a.add_argument("image")
    a.add_argument("--focus", action="append", default=[], help="x,y,w,h of the element that should win (repeatable)")
    a.add_argument("--centre-bias", type=float, default=0.0, help="0..1 blend of a central Gaussian (Tatler 2007)")
    a.add_argument("--fixations", type=int, default=5)
    a.add_argument("--out", help="write <out>.png overlay and <out>.json report")
    c = sub.add_parser("apca")
    c.add_argument("text")
    c.add_argument("bg")
    f = sub.add_parser("flash")
    f.add_argument("path")
    f.add_argument("--fine", action="store_true", help="strict per-pixel mode (256 across); flags moving particles too")
    v = sub.add_parser("cvd")
    v.add_argument("image")
    v.add_argument("--type", choices=sorted(_CVD), default="deutan")
    v.add_argument("--severity", type=float, default=1.0)
    v.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "apca":
        t, b = parse_hex(args.text), parse_hex(args.bg)
        lc = apca_lc(t, b)
        print(json.dumps({"text": args.text, "bg": args.bg, "apca_lc": round(lc, 1),
                          "wcag_ratio": round(wcag_ratio(t, b), 2)}))
        return 0
    if args.cmd == "flash":
        frames, durs = load_frames(Path(args.path), 256 if args.fine else 64)
        rep = flash_check(frames, durs)
        print(json.dumps(rep, indent=2))
        return 0 if rep["verdict"] == "PASS" else 1
    if args.cmd == "cvd":
        out = simulate_cvd(_load(args.image), args.type, args.severity)
        Image.fromarray((out * 255).round().astype(np.uint8)).save(args.out)
        print(args.out)
        return 0
    rgb = _load(args.image)
    focus = [tuple(int(v) for v in s.split(",")) for s in args.focus]
    rep, sal = audit(rgb, focus, args.centre_bias, args.fixations)
    if args.out:
        overlay(rgb, sal, rep).save(args.out + ".png")
        Path(args.out + ".json").write_text(json.dumps(rep, indent=2) + "\n")
    print(json.dumps(rep, indent=2))
    return 1 if rep.get("verdict") == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
