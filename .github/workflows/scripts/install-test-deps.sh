#!/usr/bin/env bash
set -euo pipefail

# Install Python test dependencies
python -m pip install --upgrade pip
pip install pytest pytest-cov
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
