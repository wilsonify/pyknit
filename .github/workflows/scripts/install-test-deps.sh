#!/usr/bin/env bash
set -euo pipefail

# Install Python test dependencies
python -m pip install --upgrade pip
python -m pip install --only-binary :all: pytest==8.3.4 pytest-cov==6.0.0
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
pip install -e .
