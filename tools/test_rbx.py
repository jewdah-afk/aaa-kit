#!/usr/bin/env python3
"""Tests for tools/rbx.py: answers come from the real API dump and the kit's docs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rbx  # noqa: E402


class Api(unittest.TestCase):
    def test_class_lists_own_members_with_types(self):
        out = rbx.cmd_class(["ParticleEmitter"])
        self.assertIn("Rate: float", out)
        self.assertIn("Emit: (particleCount: int = 16)", out)
        self.assertNotIn("Parent:", out)  # inherited members only with --inherited
        self.assertIn("Parent:", rbx.cmd_class(["ParticleEmitter", "--inherited"]))

    def test_member_follows_inheritance(self):
        out = rbx.cmd_member(["Workspace.Raycast"])
        self.assertIn("inherited from WorldRoot", out)
        self.assertIn("RaycastResult", out)

    def test_invented_member_is_reported_with_the_chain(self):
        out = rbx.cmd_member(["ParticleEmitter.BurstCount"])
        self.assertIn("no member", out)
        self.assertIn("ParticleEmitter < Instance < Object", out)

    def test_typo_gets_a_suggestion(self):
        self.assertIn("ParticleEmitter", rbx.cmd_class(["ParticleEmiter"]))
        self.assertIn("Lifetime", rbx.cmd_member(["ParticleEmitter.Lifetim"]))

    def test_enum_and_filter(self):
        self.assertIn("Neon", rbx.cmd_enum(["Material"]))
        self.assertEqual(rbx.cmd_enum(["Material", "neon"]), "Enum.Material (1 items): Neon")
        self.assertIn("no enum", rbx.cmd_enum(["Materials"]))

    def test_member_without_class_lists_owners(self):
        self.assertIn("Debris.AddItem", rbx.cmd_member(["AddItem"]))

    def test_find(self):
        out = rbx.cmd_find(["rolloffmin"])
        self.assertIn("Sound.RollOffMinDistance", out)

    def test_long_defaults_are_trimmed(self):
        self.assertNotIn("FilterDescendantsInstances", rbx.cmd_member(["Workspace.Raycast"]))

    def test_every_class_in_the_checker_index_has_detail(self):
        self.assertEqual(set(rbx.index()["classes"]), set(rbx.detail()))


class Research(unittest.TestCase):
    def test_finds_the_emission_section(self):
        out = rbx.cmd_research(["Rate", "vs", "Emit", "particle"], )
        self.assertIn("docs/research/45-roblox-vfx-audio-and-game-feel.md", out)

    def test_nothing_found_says_so(self):
        self.assertIn("no section matches", rbx.cmd_research(["zzzqqqxxx"]))

    def test_results_have_file_and_line(self):
        line = rbx.cmd_research(["hierarchy", "tier"]).splitlines()[0]
        self.assertRegex(line, r"\.md:\d+  ")


if __name__ == "__main__":
    unittest.main(verbosity=0)
