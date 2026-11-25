#!/usr/bin/env python3
"""Merge vfxbench runs: keep the fastest ms per row across repeated runs of one mode,
then print one table with interpreter and native side by side.

Usage: python3 tools/vfxbench/merge.py results/raw > results/RESULTS.md
`results/raw/<mode>-<n>.md` are outputs of bench.luau (mode = interp-O2, native-O2, interp-O1).
Taking the minimum filters out time stolen by other processes; it doesn't flatter a variant,
because every variant gets the same treatment.
"""
import collections
import pathlib
import re
import sys

ROW = re.compile(r"\| (.*?) \| (.*?) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| (.*?) \|")


def load(path):
    rows, group = [], None
    for line in path.read_text().splitlines():
        m = ROW.match(line)
        if m:
            if m.group(1):
                group = m.group(1)
            rows.append((group, m.group(2), float(m.group(3)), float(m.group(4)), m.group(6)))
    return rows


def main(raw_dir):
    raw = pathlib.Path(raw_dir)
    modes = collections.defaultdict(list)
    for f in sorted(raw.glob("*.md")):
        modes[f.stem.rsplit("-", 1)[0]].append(load(f))
    best = {}
    order = []
    for mode, runs in modes.items():
        for run in runs:
            for group, variant, ms, ns, status in run:
                key = (group, variant)
                if key not in order:
                    order.append(key)
                cur = best.get((mode, key))
                if cur is None or ms < cur[0]:
                    best[(mode, key)] = (ms, ns, status)
    cols = [m for m in ("interp-O2", "native-O2", "interp-O1") if m in modes]
    print("# vfxbench results")
    print()
    print(f"Fastest of {min(len(r) for r in modes.values())} runs per mode. Luau CLI 0.740, -O2 unless noted. ms per call.")
    print("x = speed-up vs the first row of the group in the same mode. Output: checksum (or mean, ≈) matches the first row.")
    print()
    head = "| Group | Variant | " + " | ".join(f"{c} ms | x" for c in cols) + " | native gain | output |"
    print(head)
    print("|" + "---|" * (2 + 2 * len(cols) + 2))
    first = {}
    last_group = None
    for key in order:
        group, variant = key
        cells = []
        for c in cols:
            ms = best.get((c, key), (None,))[0]
            if (c, group) not in first:
                first[(c, group)] = ms
            ref = first[(c, group)]
            x = ref / ms if ms and ref else 0
            cells.append(f"{ms:.3f} | {x:.1f}" if ms is not None else "- | -")
        i2 = best.get(("interp-O2", key), (None,))[0]
        n2 = best.get(("native-O2", key), (None,))[0]
        gain = f"{i2 / n2:.1f}" if i2 and n2 else "-"
        status = best.get(("interp-O2", key), (0, 0, ""))[2]
        print(f"| {group if group != last_group else ''} | {variant} | " + " | ".join(cells) + f" | {gain} | {status} |")
        last_group = group


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tools/vfxbench/results/raw")
