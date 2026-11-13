# Scorecard of the shipped brick creatures

Written by `scripts/scorecard.py baseline`. Measures are defined at the top of that script; they are taken on flat measuring views of the brick grid, not on the Blender renders. Frozen in `BASELINE.json`; `scorecard.py check` fails when a model drops below it.

| Model | Match | Structure | Bands | Edges | Flat | Contrast | Relief | Backed | Small (48 px) | At 100 studs | Colours | Glow | Largest piece (tris) | Rules |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| abyssal_angler | 0.72 | 86 | 6.3 | 33 % | 5 % | 2.45 | 17 % | 78 % | 0.64 | 1.00 | 13 | 0.5 % | 8,652 | ok |
| bone_hydra | 0.53 | 90 | 7.0 | 23 % | 16 % | 2.70 | 17 % | 79 % | 0.28 | 1.00 | 14 | 0.2 % | 13,572 | ok |
| ember_dragon | 0.61 | 85 | 6.0 | 21 % | 12 % | 2.22 | 14 % | 70 % | 0.35 | 1.00 | 16 | 0.3 % | 15,714 | ok |
| frost_mammoth | 0.68 | 80 | 7.0 | 46 % | 1 % | 2.10 | 31 % | 77 % | 0.60 | 1.00 | 14 | 3.3 % | 17,702 | ok |
| kraken (anchor) | 0.68 | 84 | 6.0 | 40 % | 0 % | 2.05 | 23 % | 74 % | 0.69 | 1.00 | 16 | 0.5 % | 10,102 | ok |
| lich_king | 0.61 | 86 | 6.3 | 34 % | 8 % | 2.85 | 19 % | 72 % | 0.49 | 1.00 | 13 | 14.8 % | 4,430 | FAIL: glow |
| living_armor | 0.73 | 81 | 5.0 | 19 % | 19 % | 1.79 | 15 % | 69 % | 0.51 | 1.00 | 14 | 2.6 % | 4,812 | ok |
| mimic_chest | 0.65 | 69 | 6.3 | 34 % | 4 % | 2.09 | 7 % | 55 % | 0.64 | 1.00 | 16 | 0.1 % | 9,664 | ok |
| scarecrow_king | 0.37 | 83 | 6.7 | 39 % | 2 % | 2.06 | 43 % | 68 % | 0.42 | 1.00 | 16 | 0.5 % | 6,958 | ok |
| scorpion_king | 0.62 | 94 | 6.3 | 26 % | 7 % | 2.69 | 23 % | 78 % | 0.71 | 1.00 | 11 | 1.8 % | 4,186 | ok |
| storm_griffin | 0.52 | 89 | 6.0 | 25 % | 14 % | 2.40 | 17 % | 72 % | 0.34 | 1.00 | 15 | 1.5 % | 15,610 | ok |
| swamp_croc (anchor) | 0.75 | 70 | 6.3 | 42 % | 8 % | 2.58 | 10 % | 78 % | 1.00 | 1.00 | 16 | 0.1 % | 7,228 | ok |
| tyrant_rex | 0.50 | 87 | 6.3 | 31 % | 10 % | 2.43 | 18 % | 72 % | 0.53 | 1.00 | 15 | 0.1 % | 5,676 | ok |
| venom_widow | 0.59 | 86 | 5.3 | 27 % | 11 % | 2.25 | 18 % | 71 % | 0.70 | 1.00 | 14 | 0.1 % | 15,230 | ok |
| volcano_tortoise | 0.54 | 84 | 7.0 | 36 % | 4 % | 2.02 | 19 % | 69 % | 0.33 | 1.00 | 16 | 0.7 % | 13,126 | ok |
| war_mech | 0.57 | 84 | 6.7 | 39 % | 2 % | 2.33 | 21 % | 71 % | 0.57 | 1.00 | 16 | 0.2 % | 8,432 | ok |
| war_rhino (anchor) | 0.78 | 83 | 5.7 | 22 % | 16 % | 1.97 | 15 % | 60 % | 0.79 | 1.00 | 12 | 0.0 % | 4,880 | ok |
