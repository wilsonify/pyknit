#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# sanitize-sarif.sh
#
# Make every generated SARIF safe to upload to GitHub Code Scanning:
#   1. Guarantee a valid, non-empty JSON file for every target.
#   2. Drop results that lack usable locations (no locations, no
#      physicalLocation, or no artifactLocation with a non-empty uri).
#   3. Attempt to repair results where artifactLocation is missing or uri
#      is empty by synthesizing a plausible location from available data.
#   4. Never emit empty artifactLocation objects.
#   5. Log exactly what happened for CI debuggability.
#
# The script is idempotent and reads/writes the same sarif/<name>.sarif files
# produced by scan-vulns.sh.
# ---------------------------------------------------------------------------

python3 - <<'PY'
import json
import os
import sys

EXPECTED = ["source", "wheel", "android", "pyscript"]

EMPTY_SARIF = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {"driver": {"name": "grype", "version": "0.118.0"}},
            "results": [],
        }
    ],
}


def make_empty_sarif():
    """Return a fresh empty SARIF document (deep copy)."""
    return json.loads(json.dumps(EMPTY_SARIF))


def artifact_location_ok(loc):
    """Return True if loc['physicalLocation.artifactLocation'] is valid."""
    al = loc.get("physicalLocation", {}).get("artifactLocation")
    if not al or not isinstance(al, dict):
        return False
    uri = al.get("uri")
    return bool(uri and isinstance(uri, str) and uri.strip())


def try_repair_artifact_location(result):
    """
    Attempt to synthesise a usable artifactLocation for a result that has a
    physicalLocation but is missing or has an empty artifactLocation.

    Strategies:
      1. If physicalLocation has a uri but it's in artifactLocation.uri — already ok.
      2. If the result has a ruleId and a package reference, build a placeholder.
      3. As a last resort, use a synthetic "unknown" location so GitHub can
         at least ingest the result (it will show without a file link).
    Returns the repaired result or None if unrecoverable.
    """
    for loc in result.get("locations", []):
        phys = loc.get("physicalLocation")
        if not phys:
            continue
        al = phys.get("artifactLocation")

        # Case: artifactLocation exists but uri is empty/missing
        if al and isinstance(al, dict):
            uri = al.get("uri")
            if not uri or not isinstance(uri, str) or not uri.strip():
                # Try to use region address or other hints
                # Build a synthetic placeholder so GitHub can ingest
                rule_id = result.get("ruleId", result.get("rule", {}).get("id", "unknown"))
                al["uri"] = f"vulnerability/{rule_id}"
            # Now it should be ok
            return result

        # Case: artifactLocation missing entirely
        if not al or not isinstance(al, dict):
            # Synthesize artifactLocation from ruleId
            rule_id = result.get("ruleId", result.get("rule", {}).get("id", "unknown"))
            phys["artifactLocation"] = {"uri": f"vulnerability/{rule_id}"}
            return result

    return None


def has_valid_location(result):
    """
    Check whether result has at least one location with a usable
    physicalLocation.artifactLocation.uri.
    """
    for loc in result.get("locations", []):
        if artifact_location_ok(loc):
            return True
    return False


def sanitize_run(run):
    """
    Sanitize a single SARIF run. Returns (cleaned_results, stats_dict).
    """
    results = run.get("results", [])
    total = len(results)
    kept = 0
    repaired = 0
    removed_no_locations = 0
    removed_unrepairable = 0

    clean = []
    for r in results:
        locations = r.get("locations")

        # No locations at all → drop
        if not locations or not isinstance(locations, list) or len(locations) == 0:
            removed_no_locations += 1
            continue

        # Has a valid location → keep
        if has_valid_location(r):
            kept += 1
            clean.append(r)
            continue

        # Try to repair
        repaired_result = try_repair_artifact_location(r)
        if repaired_result and has_valid_location(repaired_result):
            repaired += 1
            clean.append(repaired_result)
            continue

        # Unrecoverable → drop
        removed_unrepairable += 1

    stats = {
        "total": total,
        "kept": kept,
        "repaired": repaired,
        "removed_no_locations": removed_no_locations,
        "removed_unrepairable": removed_unrepairable,
    }
    return clean, stats


def sanitize_file(path, name):
    """Sanitize a single SARIF file. Returns stats dict."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"[{name}] File missing or empty — writing empty SARIF")
        with open(path, "w") as fh:
            json.dump(make_empty_sarif(), fh)
        return {"total": 0, "kept": 0, "repaired": 0,
                "removed_no_locations": 0, "removed_unrepairable": 0}

    with open(path) as fh:
        try:
            doc = json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"[{name}] Corrupt JSON ({exc}) — writing empty SARIF")
            with open(path, "w") as fh:
                json.dump(make_empty_sarif(), fh)
            return {"total": 0, "kept": 0, "repaired": 0,
                    "removed_no_locations": 0, "removed_unrepairable": 0}

    total_stats = {"total": 0, "kept": 0, "repaired": 0,
                   "removed_no_locations": 0, "removed_unrepairable": 0}

    for run in doc.get("runs", []):
        cleaned, stats = sanitize_run(run)
        run["results"] = cleaned
        for k in total_stats:
            total_stats[k] += stats[k]

    # Ensure valid structure
    if not doc.get("runs"):
        doc["runs"] = [make_empty_sarif()["runs"][0]]

    with open(path, "w") as fh:
        json.dump(doc, fh, indent=2)

    return total_stats


# ---- main ----
grand = {"total": 0, "kept": 0, "repaired": 0,
         "removed_no_locations": 0, "removed_unrepairable": 0}

for name in EXPECTED:
    path = f"sarif/{name}.sarif"
    stats = sanitize_file(path, name)
    for k in grand:
        grand[k] += stats[k]
    print(f"[{name}] inspected={stats['total']}  kept={stats['kept']}  "
          f"repaired={stats['repaired']}  "
          f"removed(no-loc)={stats['removed_no_locations']}  "
          f"removed(unrepairable)={stats['removed_unrepairable']}")

print(f"\n[total] inspected={grand['total']}  kept={grand['kept']}  "
      f"repaired={grand['repaired']}  "
      f"removed(no-loc)={grand['removed_no_locations']}  "
      f"removed(unrepairable)={grand['removed_unrepairable']}")
PY
