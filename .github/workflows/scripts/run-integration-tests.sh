#!/usr/bin/env bash
set -euo pipefail

# Run integration tests against the installed package
python -m pytest test/integration -v --tb=short --junitxml=integration-results.xml
