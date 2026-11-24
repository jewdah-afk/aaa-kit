#!/usr/bin/env python3
"""Tests for check_roblox_api.py: real API passes, invented API is caught."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_roblox_api as c  # noqa: E402


def issues(src):
    return c.check_lines(c.blank_comments(src))


def errs(src):
    return [m for _, s, m in issues(src) if s == "error"]


class RealApi(unittest.TestCase):
    def test_valid_code_passes(self):
        src = '''
local p = Instance.new("ParticleEmitter")
p.Rate = 20
p.Lifetime = NumberRange.new(1, 2)
p:Emit(5)
local s = game:GetService("RunService")
local e = Enum.Material.Neon
if p:IsA("ParticleEmitter") then end
'''
        self.assertEqual(errs(src), [])

    def test_inherited_members_pass(self):
        self.assertEqual(errs('local f = Instance.new("Frame")\nf.Name = "x"\nf.Parent = nil\nf:Destroy()\nf.BackgroundTransparency = 1'), [])


class Hallucinations(unittest.TestCase):
    def test_unknown_class(self):
        self.assertTrue(errs('local x = Instance.new("ParticleBurst")'))

    def test_not_creatable(self):
        self.assertTrue(errs('local x = Instance.new("Workspace")'))

    def test_unknown_service(self):
        self.assertTrue(errs('local s = game:GetService("FxService")'))

    def test_non_service_class(self):
        self.assertTrue(errs('local s = game:GetService("Part")'))

    def test_unknown_enum_and_item(self):
        self.assertTrue(errs("local a = Enum.Materials.Neon"))
        self.assertTrue(errs("local a = Enum.Material.Plasma"))

    def test_isa_unknown(self):
        self.assertTrue(errs('if x:IsA("Emitter") then end'))

    def test_unknown_property_on_bound_variable(self):
        e = errs('local p = Instance.new("ParticleEmitter")\np.BurstCount = 5')
        self.assertTrue(e and "BurstCount" in e[0])

    def test_unknown_method_on_bound_variable(self):
        self.assertTrue(errs('local p = Instance.new("ParticleEmitter")\np:Burst(5)'))

    def test_suggestion_names_the_real_one(self):
        e = errs('local x = Instance.new("ParticleEmiter")')
        self.assertIn("ParticleEmitter", e[0])


class Edges(unittest.TestCase):
    def test_comments_and_api_ok_are_ignored(self):
        self.assertEqual(errs('-- Instance.new("Nope")\nlocal x = Instance.new("Nope") -- api-ok: mock'), [])
        self.assertEqual(errs('--[[ Instance.new("Nope") ]]'), [])

    def test_rebound_variable_with_two_classes_is_skipped(self):
        self.assertEqual(errs('local p = Instance.new("Part")\nlocal p = Instance.new("Frame")\np.Foo = 1'), [])

    def test_deprecated_is_a_warning_not_error(self):
        w = issues('local s = Instance.new("Sound")\ns.EmitterSize = 3')
        self.assertTrue(any(sev == "warn" for _, sev, _ in w))
        self.assertEqual([m for _, sev, m in w if sev == "error"], [])

    def test_markdown_blocks_are_checked_with_right_line(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.md"
            f.write_text('text\n\n```luau\nlocal x = Instance.new("Nope")\n```\n', encoding="utf-8")
            r = c.check_file(f)
            self.assertEqual([n for n, _, _ in r], [4])
            f.write_text('```python\nInstance.new("Nope")\n```\n', encoding="utf-8")
            self.assertEqual(c.check_file(f), [])


if __name__ == "__main__":
    unittest.main(verbosity=0)
