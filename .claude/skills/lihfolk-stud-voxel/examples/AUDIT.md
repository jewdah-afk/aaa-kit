# Audit of the shipped brick creatures

Written from `scripts/audit.py` runs. No rendering: each model is run with the rig export intercepted.
Rules checked: 16 solid colours or fewer, glow share at or under 4 % unless the model is `# GLOW: strong`, no floating bricks.
Parts = boxes the BrickBoxes route would need (boxes never cross a bone or a colour). The train is not audited.

| Model | Size (studs, x y z) | Bricks | Bones | Solid colours | Glow kinds | Glow share | Floating | Parts | Rules |
|---|---|---|---|---|---|---|---|---|---|
| abyssal_angler | 200 x 178 x 272 | 68,927 | 11 | 13 | 4 | 0.5 % (strong) | 0 | 3,401 | ok |
| bone_hydra | 565 x 572 x 815 | 1,797,122 | 38 | 14 | 2 | 0.2 % (strong) | 0 | 33,635 | ok |
| ember_dragon | 705 x 422 x 965 | 967,233 | 40 | 16 | 2 | 0.3 % (strong) | 0 | 41,748 | ok |
| frost_mammoth | 125 x 202 x 325 | 144,008 | 18 | 14 | 3 | 3.3 % (strong) | 3 | 12,710 | FAIL: floating |
| kraken | 310 x 172 x 235 | 128,130 | 34 | 16 | 2 | 0.5 % | 0 | 9,637 | ok |
| lich_king | 212 x 265 x 95 | 65,138 | 18 | 13 | 3 | 14.8 % | 0 | 4,303 | FAIL: glow |
| living_armor | 288 x 285 x 142 | 147,331 | 26 | 14 | 3 | 2.6 % | 0 | 8,488 | ok |
| mimic_chest | 245 x 212 x 222 | 167,396 | 18 | 16 | 1 | 0.1 % | 0 | 5,339 | ok |
| scarecrow_king | 230 x 320 x 118 | 25,299 | 27 | 16 | 1 | 0.5 % | 0 | 4,943 | ok |
| scorpion_king | 245 x 178 x 298 | 81,306 | 43 | 11 | 3 | 1.8 % (strong) | 0 | 4,415 | ok |
| storm_griffin | 595 x 418 x 495 | 580,880 | 28 | 15 | 3 | 1.5 % | 0 | 22,302 | ok |
| swamp_croc | 170 x 92 x 545 | 109,899 | 21 | 16 | 1 | 0.1 % (strong) | 102 | 4,982 | FAIL: floating |
| tyrant_rex | 145 x 258 x 475 | 121,740 | 20 | 15 | 1 | 0.1 % (strong) | 0 | 5,077 | ok |
| venom_widow | 390 x 172 x 328 | 146,022 | 32 | 14 | 1 | 0.1 % | 6 | 8,070 | FAIL: floating |
| volcano_tortoise | 322 x 438 x 602 | 840,023 | 15 | 16 | 1 | 0.7 % (strong) | 0 | 24,512 | ok |
| war_mech | 260 x 238 x 152 | 98,482 | 16 | 16 | 3 | 0.2 % | 0 | 3,386 | ok |
| war_rhino | 95 x 128 x 252 | 70,328 | 15 | 12 | 1 | 0.0 % (strong) | 0 | 2,009 | ok |
