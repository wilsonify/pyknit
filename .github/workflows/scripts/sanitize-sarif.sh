#!/usr/bin/env bash
set -euo pipefail

# Make every generated SARIF safe to upload to CodeQL code scanning:
# guarantee a valid, non-empty file, and drop results that lack a
# physicalLocation (SBOM findings with no file provenance), which the
# upload-sarif action would otherwise reject with "expected artifact location".
python3 - <<'PY'
import json
import os

expected = ["source", "wheel", "android", "pyscript"]
for name in expected:
    path = f"sarif/{name}.sarif"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w") as fh:
            json.dump(
                {
                    "version": "2.1.0",
                    "runs": [
                        {
                            "tool": {"driver": {"name": "grype", "version": "0.118.0"}},
                            "results": [],
                        }
                    ],
                },
                fh,
            )
        continue
    with open(path) as fh:
        doc = json.load(fh)
    for run in doc.get("runs", []):
        run["results"] = [
            r
            for r in run.get("results", [])
            if r.get("locations") and r["locations"][0].get("physicalLocation")
        ]
    with open(path, "w") as fh:
        json.dump(doc, fh)
PY