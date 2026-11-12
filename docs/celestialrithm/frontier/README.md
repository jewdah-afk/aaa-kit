# Celestialrithm frontier

The research engine for Stud UI materials, UI, geometry and avatar effects. Review branch only: nothing here replaces production visuals without the owner's approval. The approved 12-material board ([approved-material-visual-target.gif](../../../media/celestialrithm/approved-material-visual-target.gif)) is the visual floor.

> Status: iteration 1 in progress. This page is completed when the batch renders and workstreams land.

| Read | For |
|---|---|
| [INTEGRATION_AUDIT.md](INTEGRATION_AUDIT.md) | What came in, duplicates, conflicts, missing dependencies, licences |
| [EXPERIMENTS.md](EXPERIMENTS.md) | Lineage of every improvement round, with evidence and the bugs the tests caught |
| [materials/](materials/README.md) | Material vault: one implementation card per material |
| [../../algorithm-vault/external/](../../algorithm-vault/external/README.md) | Verified external-method registry (76 entries) |

## Run

```sh
python3 tools/celestialrithm/foundry/test_foundry.py                       # 113 checks
python3 -m tools.celestialrithm.foundry.board --set core12 --seconds 12 --out /tmp/board
python3 -m tools.celestialrithm.foundry.ui --out /tmp/ui --seconds 10
python3 -m tools.celestialrithm.foundry.cards                               # regenerate material cards
```

## Next iteration

Filled in when iteration 1's batches land: Studio validation of the best-ranked material, mid/low tier atlases, and the Full LihFolk pack's references once supplied.
