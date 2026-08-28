#!/usr/bin/env bash
set -euo pipefail

# Run doctests against source modules
python -m pytest --doctest-modules pyknit --tb=short
