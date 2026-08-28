#!/usr/bin/env bash
set -euo pipefail

# Lint Kotlin files under android/ using ktlint
curl -sSLO https://github.com/pinterest/ktlint/releases/download/1.1.1/ktlint
chmod +x ktlint

KT_FILES=$(find android/ -name "*.kt" 2>/dev/null || true)
if [ -n "$KT_FILES" ]; then
  echo "$KT_FILES" | xargs ./ktlint
else
  echo "No Kotlin files found to lint"
fi
