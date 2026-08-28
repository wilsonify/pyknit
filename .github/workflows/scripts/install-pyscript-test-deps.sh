#!/usr/bin/env bash
set -euo pipefail

# Install test dependencies for PyScript E2E
python -m pip install --upgrade pip
pip install pytest playwright
python -m playwright install chromium --with-deps
