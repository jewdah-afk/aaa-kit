# Build + render a BRICK-pipeline model (examples/brick/*.py), then outline/glow post and a contact sheet.
# Usage: .\run_brick.ps1 <path\to\model.py> [view names...]      (no views = all views)
# Output: <model folder>\out_<model name>\  -> <ID>.blend, render\*.png, render\*_fx.png, sheet.png
param([Parameter(Mandatory)][string]$Model, [Parameter(ValueFromRemainingArguments)][string[]]$Views)
$blender = $env:BLENDER_EXE
if (-not $blender) { $blender = (Get-ChildItem 'C:\Program Files\Blender Foundation\*\blender.exe' | Sort-Object FullName -Descending | Select-Object -First 1).FullName }
$Model = (Resolve-Path $Model).Path
$out = Join-Path (Split-Path $Model) ('out_' + [IO.Path]::GetFileNameWithoutExtension($Model))
$a = @('-b', '--factory-startup', '--python', $Model, '--', 'render') + $Views
& $blender @a 2>&1 | Select-String 'VOX_OK|PALETTE|BL_OK|RIG_|Traceback|Error|line \d+' | ForEach-Object { $_.Line }
$strong = Select-String -Path $Model -Pattern '^# GLOW: strong' -Quiet
if ($strong) { $env:GLOW_STRONG = '1' } else { Remove-Item Env:GLOW_STRONG -ErrorAction SilentlyContinue }
py "$PSScriptRoot\post_glow.py" (Join-Path $out 'render')
py "$PSScriptRoot\brick_sheet.py" (Join-Path $out 'render') (Join-Path $out 'sheet.png')
Remove-Item Env:GLOW_STRONG -ErrorAction SilentlyContinue
