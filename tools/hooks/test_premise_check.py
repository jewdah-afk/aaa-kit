#!/usr/bin/env python3
"""Tests for the API premise hook. Run: python3 tools/hooks/test_premise_check.py

1. Every false-premise case in tools/evals/roblox_traps/cases.json is flagged, naming the fake and the real API the case expects.
2. The same with the curated alternatives table switched off: every fake is still flagged (the table is not what catches them).
3. Every basic and rare case prompt (real API only) gets no output, plus hand-written real-API prompts, Studio paths and pasted code.
4. Every curated entry is still true: the fake still does not exist, every suggested alternative does.
5. Bad input, a missing API folder and an empty prompt exit 0 silently; one run stays well under the hook timeout.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "hooks" / "premise_check.py"
API_DIR = ROOT / "tools" / "roblox_api"
sys.path.insert(0, str(HOOK.parent))
import premise_check as pc  # noqa: E402

CASES = json.loads((ROOT / "tools" / "evals" / "roblox_traps" / "cases.json").read_text(encoding="utf-8"))["cases"]
API = pc.Api(API_DIR)
BARE = pc.Api(API_DIR, curated={})
failed = 0
passed = 0


def check(ok, label, detail=""):
    global failed, passed
    if ok:
        passed += 1
    else:
        failed += 1
        print("FAIL", label, detail[:300])


def run(payload, env=None):
    out = subprocess.run([sys.executable, str(HOOK)], input=payload, text=True, capture_output=True,
                         env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT), **(env or {})}, timeout=15)
    return out


def context(prompt):
    out = run(json.dumps({"prompt": prompt}))
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"] if out.stdout.strip() else None


def names(patterns):
    """Identifiers a case's regexes require or forbid: ':Emit\\(' -> Emit, '\\.WalkSpeed\\s*=' -> WalkSpeed."""
    out = set()
    for p in patterns:
        out |= {w for w in re.findall(r"[A-Za-z]{3,}", p.replace("\\s", " ").replace("\\b", " ").replace("\\(", " ")) if w[0].isupper()}
    return out - {"Workspace"}


# 1 + 2. false-premise cases: through the real hook process, then in-process without the curated table
fp = [c for c in CASES if c.get("tier") == "false-premise"]
check(len(fp) >= 8, "at least 8 false-premise cases", str(len(fp)))
generic_alt = 0
for c in fp:
    ctx = context(c["prompt"])
    fake, real = names(c["must_not"]), names(c["must_use"])
    check(ctx is not None, f"{c['id']} flagged")
    if ctx:
        check(any(f in ctx for f in fake), f"{c['id']} names the fake {fake}", ctx)
        check(any(r in ctx for r in real), f"{c['id']} suggests a real one of {real}", ctx)
    bare = pc.findings(c["prompt"], BARE)
    check(len(bare) == 1, f"{c['id']} flagged without the curated table", "\n".join(bare))
    generic_alt += bool(bare) and any(r in bare[0] for r in real)
print(f"  without the curated table, {generic_alt}/{len(fp)} false-premise cases still get the expected real API as the suggestion")

# 3. no output for real API
real_prompts = [c["prompt"] for c in CASES if c.get("tier") in ("basic", "rare")]
check(len(real_prompts) >= 29, "basic + rare prompts present", str(len(real_prompts)))
real_prompts += [
    "Call ParticleEmitter:Emit(30) on the Sparks emitter, then set Humanoid.WalkSpeed = 24.",
    "Use TweenService:Create(part, info, goal) and tween:Play(); also workspace:Raycast(origin, dir).",
    "local img = AssetService:CreateEditableImage({ Size = Vector2.new(64, 64) }) then img:WritePixelsBuffer(Vector2.zero, img.Size, buf)",
    "Put the remote in ReplicatedStorage.Remotes and read it from ServerScriptService.Server.Scripts in Studio.",
    "Open src/client/Hud.luau and Players.luau; fix line 40 of Workspace.json.",
    "Make a Part with Instance.new(\"Part\"), set Enum.Material.Neon and Enum.KeyCode.E, use game:GetService(\"Players\").LocalPlayer.",
    "Tool: Write the file. Model: the default one. Note: keep it short.",
    "local Light = {}\nLight.__index = Light\nfunction Light.new() end\nfunction Light.bakeWarm() end\nLight.WARM = 1\nreturn Light",
    "local Noise = require(script.Noise)\nlocal v = Noise.fbm(x, y)",
    "for _, Model in workspace:GetChildren() do Model.Anchored = true end",
    "local Model = template:Clone()\nModel.CollisionGroup = \"Conveyor\"",
    "Framework.FirePopup(Player, `You cannot afford this!`) and x.toBN(PlayerData.Coins); DataService:update(Player, fn)",
    "game:GetService(\"ReplicatedStorage\").Events.Fire:FireServer(1)",
    "-- feed on ReplicatedStorage.SpectateRE (no relay in this place)",
    "See https://create.roblox.com/docs/reference/engine/classes/EditableImage#Clear for details",
    "Set the BasePart's MeshId property",  # real on a subclass (MeshPart): loose wording, not a fake
]
for p in real_prompts:
    ctx = context(p)
    check(ctx is None, f"real API prompt is silent: {p[:70]!r}", ctx or "")

# more fakes in other shapes, all must be flagged
fake_prompts = {
    "local TweenService = game:GetService(\"TweenService\")\nTweenService:Run(part, info, goal)": "TweenService:Run",
    "game:GetService(\"TweenService\"):Run(part, info, goal)": "TweenService:Run",
    "Set the BurstCount property of the ParticleEmitter to 30.": "BurstCount",
    "script.Parent.Humanoid:SetWalkSpeed(24)": "SetWalkSpeed",
    "part:Delete()": "part:Delete",
    "Set Part.Glow = true": "Part.Glow",
    "Use Enum.Material.Plasmaa for the core": "Enum.Material.Plasmaa",
    "Use Enum.Materials.Neon": "Enum.Materials",
    "Use workspace:FindPartOnRay(ray) to find the hit.": "deprecated",
}
for p, want in fake_prompts.items():
    ctx = context(p)
    check(ctx is not None and want in ctx, f"fake flagged: {p[:60]!r} -> {want}", ctx or "(no output)")

# 4. curated table stays true against the dump
data = json.loads((API_DIR / "premise-alternatives.json").read_text(encoding="utf-8"))
for table in ("fakes", "deprecated"):
    for key, entry in data[table].items():
        cls, member = key.split(".", 1)
        check(cls in API.classes, f"{table} {key}: class exists")
        if cls not in API.classes:
            continue
        owner, flags = API.lookup(cls, member)
        if table == "fakes":
            check(owner is None, f"fake {key} still does not exist (else drop it from the table)")
        else:
            check(owner is not None and "D" in flags, f"deprecated {key} still exists and is deprecated")
        check(bool(entry.get("note")) and entry.get("use"), f"{table} {key}: has use + note")
        for ref in entry.get("use", []):
            c2, m2 = ref.split(".", 1)
            o2, f2 = API.lookup(c2, m2) if c2 in API.classes else (None, None)
            check(o2 is not None and "D" not in f2, f"{table} {key}: alternative {ref} is real and current")

# 5. robustness and speed
out = run("not json")
check(out.returncode == 0 and not out.stdout, "bad input exits 0 silently", out.stdout + out.stderr)
out = run(json.dumps({"prompt": ""}))
check(out.returncode == 0 and not out.stdout, "empty prompt is silent")
with tempfile.TemporaryDirectory() as tmp:
    lone = pathlib.Path(tmp) / "premise_check.py"
    lone.write_text(HOOK.read_text(encoding="utf-8"), encoding="utf-8")
    out = subprocess.run([sys.executable, str(lone)], input=json.dumps({"prompt": "EditableImage:Clear()", "cwd": tmp}),
                         text=True, capture_output=True, env={k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}, timeout=15)
    check(out.returncode == 0 and not out.stdout, "missing API data exits 0 silently", out.stdout + out.stderr)
t0 = time.time()
context("Use EditableImage:Clear(Color3.new()) and DataStore:SaveAsync(k, v)")
dt = time.time() - t0
check(dt < 3, f"one run under 3 s (took {dt:.2f} s)")

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
