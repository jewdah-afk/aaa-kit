#!/usr/bin/env bash
# Trace the war rhino's plates from its concept, rebuild, and write the match report.
# Run from the repo root. Needs Blender's bpy (pip install bpy), numpy and Pillow.
set -euo pipefail
SV=.claude/skills/lihfolk-stud-voxel
# 1. trace: fit the concept's side view to the SHIPPED model and write the plate map the rebuild reads
python3 $SV/scripts/concept_match.py $SV/examples/brick/war_rhino_brick.py $SV/examples/concepts/WarRhino_concept.jpg \
    190 5 541 178 /tmp/rhino_trace --trace $SV/examples/brick/refs/WarRhino_plates.npz
# 2. match: build the rebuild from that map and report how close it is
python3 $SV/scripts/concept_match.py $SV/examples/brick/war_rhino_plated_brick.py $SV/examples/concepts/WarRhino_concept.jpg \
    190 5 541 178 /tmp/rhino_match
