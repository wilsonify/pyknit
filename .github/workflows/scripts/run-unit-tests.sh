#!/usr/bin/env bash
set -euo pipefail

# Run unit tests
python -m pytest test/unit -v --tb=short --junitxml=unit-results.xml
