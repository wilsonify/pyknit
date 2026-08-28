#!/usr/bin/env bash
set -euo pipefail

# Lint CSS files under demos/ (excluding _assets)
npm install -g stylelint stylelint-config-standard

CSS_FILES=$(find demos/ -name "*.css" -not -path "*/_assets/*" 2>/dev/null || true)
if [ -n "$CSS_FILES" ]; then
  echo "$CSS_FILES" | xargs stylelint --config .stylelintrc.json
else
  echo "No CSS files found to lint"
fi
