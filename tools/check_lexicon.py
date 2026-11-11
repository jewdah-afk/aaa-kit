#!/usr/bin/env python3
"""Validates lexicon.json against lexicon.schema.json and the kit's own rules.

Uses the `jsonschema` package if it's installed; otherwise a built-in validator covering the
schema features this file uses (type, required, enum, minLength, maxLength, minimum,
minItems, uniqueItems, additionalProperties: false). Then checks: no duplicate terms
(case-insensitive), every pairs-with resolves, exactly 40 starter terms, count matches,
and LEXICON.md is up to date with the JSON.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def mini_validate(value, schema, path="$"):
    errs = []
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    if t and not isinstance(value, types[t]) or (t == "integer" and isinstance(value, bool)):
        return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in enum")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']}")
    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        errs.append(f"{path}: below {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errs.append(f"{path}: items not unique")
        for i, v in enumerate(value):
            errs += mini_validate(v, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{path}: missing {k}")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                errs += mini_validate(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected key {k}")
    return errs


def main():
    data = json.loads((ROOT / "lexicon.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "lexicon.schema.json").read_text(encoding="utf-8"))
    try:
        import jsonschema  # type: ignore
        errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in jsonschema.Draft202012Validator(schema).iter_errors(data)]
        engine = "jsonschema"
    except ImportError:
        errors = mini_validate(data, schema)
        engine = "built-in"

    terms = data.get("terms", [])
    seen = {}
    for e in terms:
        k = e["term"].lower()
        if k in seen:
            errors.append(f"duplicate term: {e['term']}")
        seen[k] = e
    for e in terms:
        for p in e["pairs-with"]:
            if p.lower() not in seen:
                errors.append(f"{e['term']}: pairs-with '{p}' does not resolve")
    starters = sum(1 for e in terms if e["starter"])
    if starters != 40:
        errors.append(f"starter pack has {starters} terms, expected 40")
    if data.get("count") != len(terms):
        errors.append(f"count {data.get('count')} != {len(terms)} terms")

    # LEXICON.md must match a fresh build
    before = (ROOT / "LEXICON.md").read_text(encoding="utf-8")
    before_json = (ROOT / "lexicon.json").read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "tools" / "lexicon" / "build.py")], check=True, capture_output=True)
    if (ROOT / "LEXICON.md").read_text(encoding="utf-8") != before or (ROOT / "lexicon.json").read_text(encoding="utf-8") != before_json:
        errors.append("lexicon.json / LEXICON.md were out of date with tools/lexicon/src (now rebuilt; commit them)")

    for e in errors:
        print("FAIL", e)
    print(f"{len(terms)} terms, {starters} starter, schema via {engine}, {len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
