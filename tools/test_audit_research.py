#!/usr/bin/env python3
"""Tests for tools/audit_research.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_research as a  # noqa: E402


def msgs(text):
    return [m for _, m in a.audit_text(text)]


class Audit(unittest.TestCase):
    def test_real_names_pass(self):
        self.assertEqual(msgs("Use `ParticleEmitter.Rate` and `ParticleEmitter:Emit(5)`, then `Enum.Material.Neon`."), [])

    def test_invented_member_is_found_with_a_suggestion(self):
        r = msgs("Set `ParticleEmitter.BurstCount` to burst.")
        self.assertEqual(len(r), 1)
        self.assertIn("BurstCount", r[0])
        self.assertTrue(msgs("Call `Part:Frobnicate()` first."))

    def test_invented_enum_item(self):
        self.assertTrue(msgs("Use `Enum.Material.Plasma`."))
        self.assertTrue(msgs("Use `Enum.Materials`."))

    def test_prose_files_and_other_libraries_are_left_alone(self):
        self.assertEqual(msgs("See `ParticleEmitter.yaml`, `Instance.new`, `Object.keys` and `ReplicatedStorage.Packages`."), [])

    def test_service_and_player_children_are_children(self):
        self.assertEqual(msgs("Read `Player.PlayerGui` from `ReplicatedStorage.Shared`."), [])

    def test_history_and_negation_are_excused(self):
        self.assertEqual(msgs("There is no `EditableImage:Clone()` in the docs."), [])
        self.assertEqual(msgs("- **Then:** `EditableImage:ReadPixels(position, size)`"), [])
        self.assertEqual(msgs("`Part:Nope()` <!-- api-ok -->"), [])

    def test_an_excuse_covers_only_the_next_line(self):
        self.assertEqual(msgs("Old signature `Part:Nope()` and\n`Part:AlsoNope()` too."), [])
        self.assertTrue(msgs("Old signature `Part:Nope()` and\nmore text\n`Part:AlsoNope()` too."))

    def test_code_fences_are_not_judged_here(self):
        self.assertEqual(msgs("```luau\nlocal x = `Part.Nope`\n```"), [])

    def test_the_shelf_itself_is_clean(self):
        self.assertEqual(a.main([]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=0)
