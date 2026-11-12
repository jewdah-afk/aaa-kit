# Review gates

1. Treat original sprites as source of truth; image-space at-rest identity tested with 16 checks.
2. Bring the modules into a copy of the game UI and enable one button at a time.
3. Validate `ImageContent` / `ImageRect` runtime behavior in Studio; fix any incompatibility, do not silently swap artwork.
4. Ensure icon and label ZIndex exceed the FX overlay.
5. ViewportFrame + mesh is opt-in only for hero displays, not all HUD buttons.
6. Capture 390x844, 844x390 and desktop at 0, press, release, idle; run the repo `tools/hierarchy/hierarchy.py audit` for the preselected focus, APCA, flash.
7. Log Studio `ScriptProfiler` and `MicroProfiler` mesh transcode, EI update, GPU frame time, and fallback use.
8. Only merge when a reviewer accepts hierarchy lift and legibility, and frame cost stays within declared budget.

GitHub write attempt: creating `research/stud-voxel-hybrid-keycap` from `main` returned HTTP 403 Resource not accessible by integration. Nothing was pushed.
