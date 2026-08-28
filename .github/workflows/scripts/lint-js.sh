#!/usr/bin/env bash
set -euo pipefail

# Lint JavaScript files under demos/ (excluding _assets and node_modules)
npm install -g jshint

JS_FILES=$(find demos/ -name "*.js" -not -path "*/_assets/*" -not -path "*/node_modules/*" 2>/dev/null || true)
if [ -n "$JS_FILES" ]; then
  echo "$JS_FILES" | xargs jshint
else
  echo "No JS files found to lint"
fi
