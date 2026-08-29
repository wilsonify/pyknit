#!/usr/bin/env bash
set -euo pipefail

# Scan an SBOM for vulnerabilities using Grype.
# Usage: scan-vulnerabilities.sh [sbom-path] [fail-level] [sarif-output]
# Defaults: sbom.spdx.json, high, grype-results.sarif

SBOM="${1:-sbom.spdx.json}"
FAIL_LEVEL="${2:-high}"
SARIF="${3:-grype-results.sarif}"

if [ ! -f "$SBOM" ]; then
  echo "Error: SBOM file not found: $SBOM" >&2
  exit 1
fi

echo "Scanning ${SBOM} for vulnerabilities (fail-on: ${FAIL_LEVEL})..."
grype "sbom:${SBOM}" \
  --fail-on "${FAIL_LEVEL}" \
  --output sarif \
  --file "${SARIF}"

echo "SARIF report written to ${SARIF}"
