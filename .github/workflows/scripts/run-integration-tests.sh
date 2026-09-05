#!/usr/bin/env bash
set -euo pipefail

# These are executable QA harnesses rather than pytest test functions.
# Run them directly so pytest's "no tests collected" exit code cannot mask
# the integration result.
#
# Environment:
#   PYQ_BASE     demo server URL (default http://127.0.0.1:8000)
#   PYQ_WORKERS  parallel browser workers (default 4; use 1 for serial)
#   PYQ_DEMO     if set, run only this single demo directory name
python test/integration/qa_all_demos.py 2>&1 | tee integration-results.xml
