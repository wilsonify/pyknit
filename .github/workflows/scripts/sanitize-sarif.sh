#!/usr/bin/env bash
set -euo pipefail

# Make every generated SARIF safe to upload to GitHub Code Scanning.
#
# Grype assigns some findings (e.g. from Python wheels) an EMPTY
# artifactLocation.uri with no artifactLocation.index; CodeQL rejects those
# with 'expected artifact location'. This script removes only results that
# have no usable physical artifact location (non-empty uri or a numeric
# index), keeps every valid finding's locations unchanged, and reports how
# many were dropped. It never creates empty artifactLocation objects.
#
# This does NOT weaken the security gate: fail-on-high.sh reads Grype's
# recorded exit codes (sarif/.rc_*) independently of this sanitized output.
python3 - <<'PY'
import json
import os

EXPECTED = ["source", "wheel", "android", "pyscript"]


def usable_locations(result):
    """Return only locations whose physicalLocation.artifactLocation is usable:
    a non-empty string 'uri' or a numeric 'index'. Skips any location that has
    an empty/missing artifactLocation without adding empty objects."""
    out = []
    for loc in result.get("locations", []):
        pl = loc.get("physicalLocation")
        if not isinstance(pl, dict):
            continue
        al = pl.get("artifactLocation")
        if not isinstance(al, dict):
            continue
        uri = al.get("uri")
        if isinstance(uri, str) and uri.strip():
            out.append(loc)
        elif isinstance(al.get("index"), int):
            out.append(loc)
    return out


def empty_sarif():
    return {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "grype", "version": "0.118.0"}}, "results": []}],
    }


for name in EXPECTED:
    path = f"sarif/{name}.sarif"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w") as fh:
            json.dump(empty_sarif(), fh)
        continue

    with open(path) as fh:
        doc = json.load(fh)

    kept = removed = 0
    for run in doc.get("runs", []):
        kept_run = []
        for r in run.get("results", []):
            locs = usable_locations(r)
            if not locs:
                removed += 1
                continue
            r["locations"] = locs
            kept_run.append(r)
            kept += 1
        run["results"] = kept_run

    with open(path, "w") as fh:
        json.dump(doc, fh)

    action = "wrote empty (valid) SARIF" if (kept == 0 and removed == 0) else ""
    print(
        f"{name}.sarif: kept {kept}, removed {removed} finding(s) "
        f"without a usable artifact location {action}".rstrip()
    )
PY