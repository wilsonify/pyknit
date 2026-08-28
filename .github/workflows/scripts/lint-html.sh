#!/usr/bin/env bash
set -euo pipefail

# Lint HTML files under demos/ (excluding _assets)
npm install -g htmlhint

HTML_FILES=$(find demos/ -name "*.html" -not -path "*/_assets/*" 2>/dev/null || true)
if [ -n "$HTML_FILES" ]; then
  echo "$HTML_FILES" | xargs htmlhint
else
  echo "No HTML files found to lint"
fi
