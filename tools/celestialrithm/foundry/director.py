"""Attention director for material surfaces: measured rest loudness + one-owner handoff.

Two jobs, both found necessary by the board hierarchy pass (hierarchy_pass.py):
  1. Rest calibration. Every material is graded for looks alone, so at rest the high-contrast
     ones (coral stripes, slime cells) out-shout the soft ones (opal, hydroglass) by 4x. Each
     material gets a contrast gain, solved from the kit's salience model (calibrate()), stored
     as data in loudness.json, applied around the face's mean colour.
  2. Handoff. While one surface is activating it is the only owner: its contrast and exposure
     rise, every other surface sinks toward calm by the same envelope, then all recover together.

The same rules are ported to Luau in lib/celestialrithm/HierarchyDirector.luau.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .fields import F32

LOUDNESS = Path(__file__).with_name('loudness.json')

# handoff shape (data, not logic)
OWNER_CONTRAST = .45      # +45% contrast on the owner at peak
OWNER_EXPOSURE = .30      # +30% exposure on the owner at peak
OTHERS_CONTRAST = .45     # others lose up to 45% contrast while someone peaks
OTHERS_EXPOSURE = .30     # and 30% exposure
GAIN_RANGE = (.35, 1.6)


def load_gains():
    try:
        return json.loads(LOUDNESS.read_text())['contrast_gain']
    except (OSError, KeyError, ValueError):
        return {}


def attention(presses):
    """Per-surface (contrast, exposure) multipliers from current press levels (0..1, one per surface)."""
    p = np.clip(np.asarray(presses, F32), 0, 1)
    top = float(p.max()) if len(p) else 0.0
    out = []
    for w in p:
        other = max(top - float(w), 0.0)                      # how much someone else owns the moment
        c = (1 + OWNER_CONTRAST * w) * (1 - OTHERS_CONTRAST * other)
        e = (1 + OWNER_EXPOSURE * w) * (1 - OTHERS_EXPOSURE * other)
        out.append((c, e))
    return out


def apply(face, glow, gain, contrast, exposure):
    """Contrast around the face's mean colour (keeps hue and mean), then exposure."""
    m = face.reshape(-1, 3).mean(0)
    g = gain * contrast
    f = np.clip(m + (face - m) * g, 0, 1) * exposure
    return np.clip(f, 0, 1).astype(F32), np.clip(glow * g * exposure, 0, 1).astype(F32)
