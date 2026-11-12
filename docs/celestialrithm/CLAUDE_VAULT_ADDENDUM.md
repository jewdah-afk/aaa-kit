# Paste this *link/addendum* into aaa-kit/CLAUDE.md after review — do not replace existing instructions

## Algorithm Vault routing
- For UI, EditableMesh, EditableImage, VFX, graphics, SFX, procedural math or higher-tier research: first read `docs/algorithm-vault/README.md` and `docs/algorithm-vault/ALGORITHM_EXAMPLES.md`.
- Search `docs/algorithm-vault/primitives.json`, `recipes.jsonl` and `repo_discovery.jsonl` using `tools/algorithm_vault/query.py` and actual source code search. `recipes.jsonl` consists of untested combinatorial candidates.
- Existing `HIERARCHY.md`, Figma playbook, icon contract, and `lib/frontier/Atlas.luau` + `Uploader.luau` remain authoritative. No round-pill redesign and no unapproved replacement of the T11 baseline shape.
- Run `python3 tools/algorithm_vault/ingest_repo.py .` to discover the newest local repo material before a research pass. It records source paths without copying external licensed code.
- Render close-ups first, then whole HUD. Test source/procedural code, contrast, focus, screen clutter, flashes, reduced motion and actual Studio frame time before adoption.
- Use `evolve.py` only on measured records, record failures, require user approval, keep lineage and rollback; never equate auto-generated combinations with implemented algorithms.
