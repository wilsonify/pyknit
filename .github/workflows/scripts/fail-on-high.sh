#!/usr/bin/env bash
set -euo pipefail

# Fail the job if any Grype scan (see scan-vulns.sh) reported vulnerabilities
# at or above 'high' severity.  A non-zero exit code is recorded even for a
# fatal scan error, so this step surfaces both cases.
#
# Exit codes in sarif/.rc_* are:
#   0 = no unreviewed high/critical vulnerabilities
#   1 = unreviewed high/critical vulnerabilities remain
#   2 = fatal scan error (e.g. missing SBOM)

echo "=== CVE Scan Results ==="
echo ""
rc=0
targets=()
for f in sarif/.rc_*; do
  [ -f "$f" ] || continue
  target="$(basename "$f" .rc_)"
  code="$(cat "$f")"
  case "$code" in
    0)
      echo "  [PASS] $target - no unreviewed high/critical vulnerabilities"
      targets+=("$target:PASS")
      ;;
    1)
      echo "  [FAIL] $target - unreviewed high/critical vulnerabilities found"
      targets+=("$target:FAIL")
      rc=1
      ;;
    *)
      echo "  [ERROR] $target - scan error (exit code $code)"
      targets+=("$target:ERROR")
      rc=1
      ;;
  esac
done

echo ""

if [ "$rc" == "1" ]; then
  echo "::error::High/critical vulnerabilities detected that are not covered by grype-ignore.yaml."
  echo ""
  echo "To fix this:"
  echo "  1. Review the new vulnerability in the SARIF artifacts above"
  echo "  2. Determine if it is exploitable in pyknit (see grype-ignore.yaml evidence notes)"
  echo "  3. If not exploitable: add a GHSA-based ignore rule to grype-ignore.yaml"
  echo "  4. If exploitable: upgrade or remove the affected dependency"
  echo ""
  echo "See: https://github.com/anchore/grype#configuration"
  exit 1
fi

echo "All scan targets passed. No unreviewed high/critical vulnerabilities."
