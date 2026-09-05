#!/usr/bin/env bash
set -euo pipefail

# Scan each prebuilt SBOM with Grype, writing one SARIF per target.
#
# errexit is disabled around the scans so a --fail-on high exit (or a fatal
# scan error) in one target cannot prevent the others from writing their full
# SARIF files. Each exit code is recorded for fail-on-high.sh.
mkdir -p sarif

# Pillow 10.0.0 (shipped by Pyodide 0.24.1) has accepted-risk CVEs.
IGNORE_FILE="$(dirname "$0")/grype-ignore.yaml"

set +e
grype sbom:sboms/source.spdx.json --fail-on high --config "$IGNORE_FILE" --output sarif --file sarif/source.sarif
echo $? > sarif/.rc_source
grype sbom:sboms/wheel.spdx.json --fail-on high --config "$IGNORE_FILE" --output sarif --file sarif/wheel.sarif
echo $? > sarif/.rc_wheel
grype sbom:sboms/android.spdx.json --fail-on high --config "$IGNORE_FILE" --output sarif --file sarif/android.sarif
echo $? > sarif/.rc_android
grype sbom:sboms/pyscript.spdx.json --fail-on high --config "$IGNORE_FILE" --output sarif --file sarif/pyscript.sarif
echo $? > sarif/.rc_pyscript
set -e

echo "Grype scans completed"