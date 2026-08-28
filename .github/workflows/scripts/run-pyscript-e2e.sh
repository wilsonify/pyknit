#!/usr/bin/env bash
set -euo pipefail

# Start a local server, run PyScript E2E tests, then stop the server
python -m http.server 8000 --directory site &
SERVER_PID=$!
sleep 2

EXIT=0
python -m pytest test/end-to-end -v --tb=short --junitxml=pyscript-e2e-results.xml || EXIT=$?

kill $SERVER_PID 2>/dev/null || true
exit $EXIT
