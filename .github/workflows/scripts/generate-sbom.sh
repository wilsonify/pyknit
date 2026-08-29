#!/usr/bin/env bash
set -euo pipefail

# Generate an SPDX JSON SBOM of the repository using Syft.
# Usage: generate-sbom.sh [output-path]
# Default output: sbom.spdx.json

OUTPUT="${1:-sbom.spdx.json}"

echo "Generating SBOM with Syft..."
syft dir:. -o "spdx-json=${OUTPUT}"

echo "SBOM written to ${OUTPUT}"
