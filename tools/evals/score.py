#!/usr/bin/env python3
"""Score model answers against the Roblox hallucination traps.

  python3 tools/evals/score.py --selftest              known-good answers must pass and known-bad ones must fail for the right reason
  python3 tools/evals/score.py ANSWERS_DIR [--json]    ANSWERS_DIR holds <case id>.md: the model's answer, Luau in fenced blocks

A case passes when: no code block uses an API that is not in Roblox's real dump (tools/check_roblox_api.py), every `must_use`
pattern appears in the code, no `must_not` pattern does, and (for cases with no_deprecated) nothing deprecated is used.
Generate answers with tools/evals/run_claude.sh; run it once with the kit's harness on and once without to compare.
`must_not` ignores comments (a good answer may say "there is no BurstCount"); `must_use` reads the raw code. Exit 0 only when every case that has an answer passes.
Results are also summed per tier (basic, rare, false-premise).
"""
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_roblox_api as api  # noqa: E402

CASES = json.loads((HERE / "roblox_traps" / "cases.json").read_text(encoding="utf-8"))["cases"]
FENCE = re.compile(r"^```(?:lua|luau)?[^\n]*\n(.*?)^```", re.S | re.M)


def code_of(answer):
    blocks = FENCE.findall(answer)
    return "\n".join(blocks) if blocks else ""


def grade(case, answer):
    """Return (passed, [reasons])."""
    code = code_of(answer)
    reasons = []
    prose_free = "\n".join(api.blank_comments(code))  # a good answer may say "-- there is no BurstCount"
    if not code.strip():
        return False, ["no Luau code block"]
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "answer.luau"
        f.write_text(code, encoding="utf-8")
        found = api.check_file(f)
    for n, sev, msg in found:
        if sev == "error" or case.get("no_deprecated"):
            reasons.append(f"api: {msg}")
    for pat in case.get("must_use", []):
        if not re.search(pat, code):  # raw code: a model may leave the server half commented out
            reasons.append(f"missing {pat}")
    for pat in case.get("must_not", []):
        if re.search(pat, prose_free):
            reasons.append(f"forbidden {pat}")
    return not reasons, reasons


def selftest():
    bad = 0
    for c in CASES:
        ok, why = grade(c, c["good"])
        if not ok:
            bad += 1
            print(f"FAIL {c['id']}: the known-good answer was rejected: {why}")
        ok, why = grade(c, c["bad"])
        if ok:
            bad += 1
            print(f"FAIL {c['id']}: the known-bad answer passed ({c['trap']})")
    print(f"{len(CASES)} cases, {bad} problems")
    return 1 if bad else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    answers = Path(args[0])
    rows, failed = [], 0
    for c in CASES:
        f = answers / f"{c['id']}.md"
        if not f.exists():
            rows.append({"id": c["id"], "status": "missing", "reasons": []})
            continue
        ok, why = grade(c, f.read_text(encoding="utf-8", errors="replace"))
        failed += not ok
        rows.append({"id": c["id"], "status": "pass" if ok else "FAIL", "reasons": why})
    graded = [r for r in rows if r["status"] != "missing"]
    passed = sum(r["status"] == "pass" for r in graded)
    if "--json" in argv:
        print(json.dumps({"passed": passed, "graded": len(graded), "total": len(CASES), "rows": rows}, indent=1))
    else:
        for r in rows:
            print(f"{r['status']:7} {r['id']}" + ("".join(f"\n          {x}" for x in r["reasons"])))
        tiers = {}
        for r in graded:
            t = next(c.get("tier", "basic") for c in CASES if c["id"] == r["id"])
            ok, n = tiers.get(t, (0, 0))
            tiers[t] = (ok + (r["status"] == "pass"), n + 1)
        print(f"{passed}/{len(graded)} passed ({len(CASES) - len(graded)} not answered); " + ", ".join(f"{t} {ok}/{n}" for t, (ok, n) in sorted(tiers.items())))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
