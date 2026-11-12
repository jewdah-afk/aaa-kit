# Installing the LihFolk Stud Voxel Pack

Instructions for Claude Code (a user can just send the zip and say "install this skill").

1. Unzip so the folder lands at `~/.claude/skills/lihfolk-stud-voxel/` (Windows: `C:\Users\<you>\.claude\skills\lihfolk-stud-voxel\`), with `SKILL.md` directly inside it. Replace any older copy of the same folder.
2. Check the requirements and tell the user what is missing:
   - **Blender 3.6+** (4.x recommended). The scripts look for the newest `C:\Program Files\Blender Foundation\*\blender.exe`; otherwise set the environment variable `BLENDER_EXE` to the blender executable.
   - **Python 3.10+** with `numpy` and `Pillow` (`py -m pip install numpy pillow`), used by the preview sheets and `scripts/trace_ref.py`.
   - **Windows PowerShell** for `scripts/run.ps1` and `scripts/run_brick.ps1`. On macOS/Linux, run the same thing directly: `blender -b --factory-startup --python <model>.py -- render`.
3. Test: run `blender -b --factory-startup --python examples/brick/props_brick.py -- render Oak` from the skill folder. It must print `RIG_OK` and write `examples/brick/out_Oak/render/Oak_tex.png`.
4. Start a new Claude Code session so the skill is picked up (it appears as `lihfolk-stud-voxel`).

Contents: `SKILL.md` (the guide), `scripts/` (build, rig, export, tracing), `examples/` (creatures, bosses, buildings, props, terrain, weapons, with their concept sheets, references and `out_*` build output), `examples/previews/` (look references), `references/roblox/` (Luau builder + animator for Studio).
