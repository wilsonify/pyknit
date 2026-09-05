#!/usr/bin/env bash
set -euo pipefail

# Start a local server, run PyScript E2E tests, then stop the server
PYTHON=${PYTHON:-python3}
$PYTHON -m http.server 8000 --directory site &
SERVER_PID=$!

for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/ > /dev/null 2>&1; then
        break
    fi
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "Server process died" >&2
        exit 1
    fi
    sleep 0.5
done
curl -sf http://127.0.0.1:8000/ > /dev/null || { echo "Server failed to start after 15s"; exit 1; }

EXIT=0
$PYTHON -m pytest test/end-to-end -v --tb=short --junitxml=pyscript-e2e-results.xml || EXIT=$?

kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
exit $EXIT
