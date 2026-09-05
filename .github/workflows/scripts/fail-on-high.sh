#!/usr/bin/env bash
set -euo pipefail

# Fail the job if any Grype scan (see scan-vulns.sh) reported vulnerabilities
# at or above 'high' severity. A non-zero exit code is recorded even for a
# fatal scan error, so this step surfaces both cases.
rc=0
for f in sarif/.rc_*; do
  if [ -f "$f" ] && [ "$(cat "$f")" != "0" ]; then
    echo "::error::$(basename "$f"): vulnerabilities at or above high severity found"
    rc=1
  fi
done
if [ "$rc" == "1" ]; then
  echo "High/critical vulnerabilities detected. See SARIF artifacts above."
  exit 1
fi
echo "No high/critical vulnerabilities found."