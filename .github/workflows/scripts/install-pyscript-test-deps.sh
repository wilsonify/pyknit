#!/usr/bin/env bash
set -euo pipefail

# Install test dependencies for PyScript E2E
python -m pip install --upgrade pip
python -m pip install --only-binary :all: pytest==8.3.4 playwright==1.49.0
python -m playwright install chromium --with-deps
