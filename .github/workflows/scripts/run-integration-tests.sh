#!/usr/bin/env bash
set -euo pipefail

# These are executable QA harnesses rather than pytest test functions.
# Run them directly so pytest's "no tests collected" exit code cannot mask
# the integration result.
python test/integration/qa_all_demos.py | tee integration-results.xml
