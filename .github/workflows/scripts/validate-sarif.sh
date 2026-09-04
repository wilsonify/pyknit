#!/usr/bin/env bash
set -euo pipefail

# Pre-upload gate: every result in the upload-ready SARIF files must carry a
# usable physical artifact location (non-empty uri or a numeric index). Runs
# before the upload steps so an invalid upload fails fast with a diagnostic
# instead of being rejected later by GitHub Code Scanning with 'expected
# artifact location'.
python3 - <<'PY'
import glob
import json
import os

EXPECTED = ["source", "wheel", "android", "pyscript"]
problems = []
total = 0
checked_files = 0

for name in EXPECTED:
    path = f"sarif/{name}.sarif"
    if not os.path.exists(path):
        continue
    checked_files += 1
    with open(path) as fh:
        doc = json.load(fh)
    for run in doc.get("runs", []):
        for r in run.get("results", []):
            total += 1
            good = False
            for loc in r.get("locations", []):
                pl = loc.get("physicalLocation")
                if not isinstance(pl, dict):
                    continue
                al = pl.get("artifactLocation")
                if not isinstance(al, dict):
                    continue
                uri = al.get("uri")
                if (isinstance(uri, str) and uri.strip()) or isinstance(al.get("index"), int):
                    good = True
                    break
            if not good:
                problems.append((name, r.get("ruleId"), r.get("message", {}).get("text", "")))

if problems:
    for name, rule, *_ in problems:
        print(f"::error::{name}.sarif: result {rule} has no usable artifact location")
    print(f"FAIL: {len(problems)} result(s) lack a usable artifact location; refusing to upload.")
    raise SystemExit(1)

if checked_files == 0:
    print("::error::no sarif/*.sarif found to validate")
    raise SystemExit(1)

print(f"OK: {total} SARIF result(s) across {checked_files} file(s) all have a usable artifact location")
PY