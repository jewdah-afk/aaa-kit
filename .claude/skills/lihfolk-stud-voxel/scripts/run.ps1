# Build + render + export a creature, then outline / sheet / gif.
# Usage: .\run.ps1 <path\to\creature.py> [all|render|export|video] [outdir]
param([Parameter(Mandatory)][string]$Creature, [string]$Mode = 'all', [string]$Out = '')
$blender = $env:BLENDER_EXE
if (-not $blender) { $blender = (Get-ChildItem 'C:\Program Files\Blender Foundation\*\blender.exe' | Sort-Object FullName -Descending | Select-Object -First 1).FullName }
$Creature = (Resolve-Path $Creature).Path
$name = (Select-String -Path $Creature -Pattern "^NAME\s*=\s*'([^']+)'").Matches[0].Groups[1].Value
if (-not $Out) { $Out = Join-Path (Split-Path $Creature) "out\$name" }
$a = @('-b', '--factory-startup', '--python', "$PSScriptRoot\studlib.py", '--', $Creature, $Mode, $Out)
& $blender @a 2>&1 | Select-String 'STUD_RESULT|WARNING|Traceback|Error|line \d+' | ForEach-Object { $_.Line }
if ($Mode -ne 'export') { py "$PSScriptRoot\post.py" $Out }
