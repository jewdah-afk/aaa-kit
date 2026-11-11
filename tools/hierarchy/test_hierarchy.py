#!/usr/bin/env python3
"""Tests for the hierarchy auditor: known values and synthetic scenes with a known answer."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import hierarchy as H  # noqa: E402


def grey(w=320, h=200, v=0.5):
    return np.full((h, w, 3), v)


class Contrast(unittest.TestCase):
    def test_apca_reference_values(self):
        # Published APCA 0.0.98G reference pairs (apca-w3 README)
        self.assertAlmostEqual(H.apca_lc((0, 0, 0), (255, 255, 255)), 106.04, places=1)
        self.assertAlmostEqual(H.apca_lc((255, 255, 255), (0, 0, 0)), -107.88, places=1)
        self.assertAlmostEqual(H.apca_lc((0x88,) * 3, (255, 255, 255)), 63.06, places=1)
        self.assertAlmostEqual(H.apca_lc((255, 255, 255), (0x88,) * 3), -68.54, places=1)
        self.assertEqual(H.apca_lc((120, 120, 120), (120, 120, 120)), 0.0)

    def test_wcag_ratio(self):
        self.assertAlmostEqual(H.wcag_ratio((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(H.wcag_ratio((118, 118, 118), (255, 255, 255)), 4.54, places=1)

    def test_oklab_white_black(self):
        lab = H.oklab(np.array([[1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]))
        self.assertAlmostEqual(lab[0, 0], 1.0, places=3)
        self.assertAlmostEqual(abs(lab[0, 1]) + abs(lab[0, 2]), 0.0, places=3)
        self.assertAlmostEqual(lab[1, 0], 0.0, places=6)

    def test_cvd_red_green_collapse(self):
        red, green = np.array([0.8, 0.2, 0.2]), np.array([0.35, 0.55, 0.2])
        normal = np.linalg.norm(H.oklab(red) - H.oklab(green))
        deut = np.linalg.norm(H.oklab(H.simulate_cvd(red, "deutan")) - H.oklab(H.simulate_cvd(green, "deutan")))
        self.assertLess(deut, normal * 0.6, "deutan simulation should pull red and green together")
        self.assertTrue(np.allclose(H.simulate_cvd(np.array([0.5, 0.5, 0.5]), "deutan"), 0.5, atol=0.01),
                        "greys stay grey")


class Salience(unittest.TestCase):
    def test_odd_one_out_wins(self):
        img = grey()
        img[90:110, 230:250] = [0.9, 0.15, 0.1]   # one red patch on grey
        rep, _ = H.audit(img, [(225, 85, 30, 30)])
        self.assertTrue(rep["fixations"][0]["in_focus"], rep["fixations"])
        self.assertGreater(rep["lift"], 3)

    def test_wrong_focus_fails(self):
        img = grey()
        img[90:110, 230:250] = [0.9, 0.15, 0.1]
        rep, _ = H.audit(img, [(20, 20, 40, 40)])
        self.assertEqual(rep["verdict"], "FAIL")

    def test_texture_loses_to_singleton(self):
        rng = np.random.default_rng(1)
        img = grey()
        for _ in range(40):                       # many small same-colour dots: a texture
            x, y = rng.integers(10, 300), rng.integers(10, 180)
            img[y:y + 4, x:x + 4] = [0.2, 0.4, 0.9]
        img[95:115, 150:170] = [1.0, 0.85, 0.1]   # one bigger yellow item
        rep, _ = H.audit(img, [(145, 90, 30, 30)])
        self.assertTrue(rep["fixations"][0]["in_focus"], rep["fixations"])

    def test_red_green_only_cue_warns_under_cvd(self):
        field = np.array([0.35, 0.55, 0.2])
        patch = np.array([0.62, 0.40, 0.2])
        lo, hi = 0.3, 1.5                         # scale the patch to the field's OKLab lightness
        for _ in range(40):
            k = (lo + hi) / 2
            lo, hi = (k, hi) if H.oklab(np.clip(patch * k, 0, 1))[0] < H.oklab(field)[0] else (lo, k)
        img = np.full((200, 320, 3), field)
        img[90:110, 150:170] = np.clip(patch * lo, 0, 1)  # isoluminant: differs only on red-green
        rep, _ = H.audit(img, [(145, 85, 30, 30)])
        self.assertIn("deutan", rep["cvd"])
        self.assertLess(rep["cvd"]["deutan"]["lift"], rep["lift"])

    def test_scanpath_visits_distinct_places(self):
        img = grey()
        img[20:40, 20:40] = 1.0
        img[150:170, 270:290] = 0.0
        path = H.scanpath(H.salience_map(img), 2)
        (x1, y1, _), (x2, y2, _) = path
        self.assertGreater(abs(x1 - x2) + abs(y1 - y2), 100, "inhibition of return moves the eye on")


class Flash(unittest.TestCase):
    def _frames(self, n, period, colour_a, colour_b, area=1.0):
        frames = []
        for i in range(n):
            f = grey(64, 48, 0.1)
            on = (i // period) % 2 == 0
            hh = int(48 * area)
            f[:hh] = colour_a if on else colour_b
            frames.append(f)
        return frames

    def test_fast_full_screen_flash_fails(self):
        frames = self._frames(30, 2, [1, 1, 1], [0, 0, 0])   # 7.5 Hz at 30 fps
        rep = H.flash_check(frames, [1000 / 30] * 30)
        self.assertEqual(rep["verdict"], "FAIL")

    def test_slow_flash_passes(self):
        frames = self._frames(60, 15, [1, 1, 1], [0, 0, 0])  # 1 Hz
        self.assertEqual(H.flash_check(frames, [1000 / 30] * 60)["verdict"], "PASS")

    def test_small_flash_passes(self):
        frames = self._frames(30, 2, [1, 1, 1], [0, 0, 0], area=0.02)
        self.assertEqual(H.flash_check(frames, [1000 / 30] * 30)["verdict"], "PASS")

    def test_red_flash_counted(self):
        frames = self._frames(30, 2, [1.0, 0.0, 0.0], [0.3, 0.3, 0.3])
        rep = H.flash_check(frames, [1000 / 30] * 30)
        self.assertGreater(rep["red"]["worst_area_fraction_over_3_per_s"], 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=1)
