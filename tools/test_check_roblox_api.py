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


class Typed(unittest.TestCase):
    def test_param_annotation(self):
        e = errs("local function f(e: ParticleEmitter)\n\te.BurstCount = 1\n\te.Rate = 5\nend")
        self.assertEqual(len(e), 1)
        self.assertIn("BurstCount", e[0])

    def test_local_annotation_and_optional(self):
        self.assertEqual(len(errs("local b: Beam? = nil\nb:Fire()")), 1)

    def test_cast(self):
        self.assertTrue(errs("local n = (x :: Part).Fnord = 3"))
        self.assertEqual(errs("local n = (x :: Part).Anchored"), [])

    def test_service_binding_checks_methods_not_children(self):
        self.assertTrue(errs('local R = game:GetService("RunService")\nR:Frobnicate()'))
        self.assertEqual(errs('local RS = game:GetService("ReplicatedStorage")\nlocal f = RS.Packages'), [])

    def test_invented_event_on_a_service_is_an_error(self):
        self.assertTrue(errs('local Players = game:GetService("Players")\nPlayers.PlayerJoined:Connect(f)'))
        self.assertEqual(errs('local Players = game:GetService("Players")\nPlayers.PlayerAdded:Connect(f)'), [])
        self.assertTrue(errs('local RunService = game:GetService("RunService")\nRunService.Update:Connect(f)'))

    def test_service_method_chain(self):
        self.assertTrue(errs('game:GetService("Debris"):Throw(x, 1)'))
        self.assertEqual(errs('game:GetService("Debris"):AddItem(x, 1)'), [])

    def test_find_first_child_of_class_result(self):
        self.assertTrue(errs('local h = m:FindFirstChildOfClass("Humanoid")\nh:Fly()'))
        self.assertEqual(errs('local h = m:FindFirstChildOfClass("Humanoid")\nh.Health = 0'), [])

    def test_scope_ends_with_the_block(self):
        src = "local function a()\n\tlocal p: Part = nil\n\tp.Anchored = true\nend\nlocal function b(p)\n\tp.Whatever = 1\nend"
        self.assertEqual(errs(src), [])

    def test_shadowing_by_untyped_param_or_loop(self):
        self.assertEqual(errs("local p: Part = nil\nfor _, p in list do\n\tp.Nope = 1\nend"), [])
        self.assertEqual(errs("local p: Part = nil\np = other\np.Nope = 1"), [])

    def test_base_class_annotation_allows_subclass_members(self):
        self.assertEqual(errs("local function f(o: Instance)\n\tif o:IsA('Model') then o:PivotTo(cf) end\nend"), [])
        self.assertTrue(errs("local function f(o: Instance)\n\to:Frobnicate(1)\nend"))

    def test_exact_class_does_not_get_subclass_members(self):
        self.assertTrue(errs('local f = Instance.new("Frame")\nf:PivotTo(cf)'))

    def test_user_type_shadows_class_name(self):
        src = "export type Frame = { w: number }\nlocal function f(x: Frame)\n\tx.w = 1\nend"
        self.assertEqual(errs(src), [])

    def test_unknown_child_read_is_a_warning_unless_strict(self):
        loose = issues("local function f(m: Model)\n\tlocal x = m.Handle\nend")
        self.assertEqual([s for _, s, _ in loose], ["warn"])
        strict = issues("--!strict\nlocal function f(m: Model)\n\tlocal x = m.Handle\nend")
        self.assertEqual([s for _, s, _ in strict], ["error"])

    def test_property_used_as_method(self):
        self.assertTrue(errs('local p = Instance.new("Part")\np:Anchored()'))


class Inference(unittest.TestCase):
    def test_cast_on_the_initializer(self):
        self.assertTrue(errs('local Ping = rs:WaitForChild("Ping") :: RemoteEvent\nPing:Fire(1)'))
        self.assertEqual(errs('local Ping = rs:WaitForChild("Ping") :: RemoteEvent\nPing:FireServer(1)'), [])

    def test_return_type_of_a_service_call(self):
        src = 'local img = game:GetService("AssetService"):CreateEditableImage({})\nimg:SetPixel(1, 2)'
        self.assertTrue(errs(src))
        self.assertEqual(errs(src.replace("SetPixel(1, 2)", "WritePixelsBuffer(a, b, c)")), [])

    def test_return_type_chain_through_a_typed_variable(self):
        src = 'local TS = game:GetService("TweenService")\nlocal t = TS:Create(p, i, g)\nt:Pplay()'
        self.assertTrue(errs(src))
        self.assertEqual(errs(src.replace("Pplay", "Play")), [])

    def test_whole_expression_must_be_one_call(self):
        # TS:Create(...):Foo() is not a Tween variable: nothing is inferred from a longer chain
        self.assertEqual(errs('local TS = game:GetService("TweenService")\nlocal t = TS:Create(p, i, g):Nope()\nt:Anything()'), [])

    def test_bare_instance_returns_say_nothing(self):
        self.assertEqual(errs('local RS = game:GetService("ReplicatedStorage")\nlocal Shared = RS:WaitForChild("Shared")\nlocal k = Shared.Kit\nShared.Kit.Run()'), [])

    def test_workspace_and_game_methods(self):
        self.assertTrue([m for _, s, m in issues("workspace:FindPartOnRay(r)") if s == "warn"])
        self.assertTrue(errs("workspace:Frobnicate(1)"))
        self.assertEqual(errs("workspace:Raycast(a, b)"), [])
        self.assertEqual(errs("local workspace = fake\nworkspace:Frobnicate(1)"), [])  # a local of that name is not the global

    def test_deprecation_via_inferred_type(self):
        self.assertTrue([m for _, s, m in issues('local s = Instance.new("Sound")\ns.Pitch = 2') if s == "warn"])


class Properties(unittest.TestCase):
    def test_property_of_class_type_types_the_variable(self):
        self.assertTrue(errs("local cam = workspace.CurrentCamera\ncam:ScreenToWorld(1, 2)"))
        self.assertEqual(errs("local cam = workspace.CurrentCamera\ncam:ViewportPointToRay(1, 2)"), [])

    def test_chain_through_a_class_valued_property(self):
        self.assertTrue(errs("workspace.Terrain:FillBox(a, b, c)"))
        self.assertEqual(errs("workspace.Terrain:FillBlock(a, b, c)"), [])

    def test_player_children_are_children(self):
        self.assertEqual(errs("local p = game:GetService(\"Players\").LocalPlayer\nlocal gui = p.PlayerGui"), [])
        self.assertTrue(errs("local p = game:GetService(\"Players\").LocalPlayer\np:Frobnicate()"))

    def test_task_library(self):
        self.assertTrue(errs("task.parallel(f)"))
        self.assertEqual(errs("task.spawn(f)\ntask.defer(f)\ntask.desynchronize()"), [])
        self.assertEqual(errs("local task = fake\ntask.parallel(f)"), [])  # a local named task is not the library


class Edges(unittest.TestCase):
    def test_comments_and_api_ok_are_ignored(self):
        self.assertEqual(errs('-- Instance.new("Nope")\nlocal x = Instance.new("Nope") -- api-ok: mock'), [])
        self.assertEqual(errs('--[[ Instance.new("Nope") ]]'), [])

    def test_rebound_variable_uses_the_class_in_force(self):
        src = 'local p = Instance.new("Part")\np.Anchored = true\nlocal p = Instance.new("Frame")\np.Anchored = true'
        r = [(n, m) for n, s, m in issues(src) if s == "error"]
        self.assertEqual([n for n, _ in r], [4])  # fine on the Part, wrong on the Frame

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
