#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# validate-sarif.sh
#
# Validate that sanitized SARIF files are safe to upload to GitHub Code
# Scanning.  Fails with a diagnostic if any result still has an invalid
# location (missing artifactLocation, empty uri, etc.).
#
# Usage: validate-sarif.sh [file ...]
#   If no files are given, validates all four expected SARIF files.
# ---------------------------------------------------------------------------

python3 - <<'PY'
import json
import os
import sys

EXPECTED = ["source", "wheel", "android", "pyscript"]
files = sys.argv[1:] if len(sys.argv) > 1 else [f"sarif/{n}.sarif" for n in EXPECTED]

errors = []
results_checked = 0
results_ok = 0

for path in files:
    if not os.path.exists(path):
        errors.append(f"{path}: file does not exist")
        continue
    if os.path.getsize(path) == 0:
        errors.append(f"{path}: file is empty")
        continue

    try:
        with open(path) as fh:
            doc = json.load(fh)
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON — {exc}")
        continue

    for run_idx, run in enumerate(doc.get("runs", [])):
        results = run.get("results", [])
        for ridx, r in enumerate(results):
            results_checked += 1
            locations = r.get("locations")
            if not locations or not isinstance(locations, list) or len(locations) == 0:
                rule = r.get("ruleId", r.get("rule", {}).get("id", "?"))
                errors.append(
                    f"{path} run[{run_idx}] result[{ridx}] "
                    f"(rule={rule}): no locations"
                )
                continue

            loc = locations[0]
            phys = loc.get("physicalLocation")
            if not phys or not isinstance(phys, dict):
                rule = r.get("ruleId", r.get("rule", {}).get("id", "?"))
                errors.append(
                    f"{path} run[{run_idx}] result[{ridx}] "
                    f"(rule={rule}): missing physicalLocation"
                )
                continue

            al = phys.get("artifactLocation")
            if not al or not isinstance(al, dict):
                rule = r.get("ruleId", r.get("rule", {}).get("id", "?"))
                errors.append(
                    f"{path} run[{run_idx}] result[{ridx}] "
                    f"(rule={rule}): missing artifactLocation"
                )
                continue

            uri = al.get("uri")
            if not uri or not isinstance(uri, str) or not uri.strip():
                rule = r.get("ruleId", r.get("rule", {}).get("id", "?"))
                errors.append(
                    f"{path} run[{run_idx}] result[{ridx}] "
                    f"(rule={rule}): empty or missing artifactLocation.uri"
                )
                continue

            results_ok += 1

    # Check SARIF structure
    if not doc.get("version"):
        errors.append(f"{path}: missing 'version' field")
    if not doc.get("runs"):
        errors.append(f"{path}: no runs in SARIF document")

print(f"Validated {results_checked} results across {len(files)} files")
print(f"  OK: {results_ok}")
if errors:
    print(f"  ERRORS: {len(errors)}")
    for e in errors:
        print(f"    ❌ {e}")
    sys.exit(1)
else:
    print("  ✅ All SARIF files are valid for GitHub upload")
PY
