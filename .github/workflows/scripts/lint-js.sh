#!/usr/bin/env bash
set -euo pipefail

# Lint standalone .js files under demos/.
# Inline <script> blocks have been removed — all JS lives in .js files now.

if ! command -v node &>/dev/null; then
  echo "ERROR: node not found" >&2
  exit 1
fi

FAIL=0

JS_FILES=$(find demos/ -name "*.js" \
    -not -path "*/_assets/*" \
    -not -path "*/node_modules/*" 2>/dev/null || true)

for f in $JS_FILES; do
  if ! node --check "$f" 2>&1; then
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo "JS lint FAILED" >&2
  exit 1
fi

echo "JS lint OK"
