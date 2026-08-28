#!/usr/bin/env bash
set -euo pipefail

# Install built wheel and test dependencies (not from source)
python -m pip install --upgrade pip
pip install dist/*.whl
pip install pytest playwright
python -m playwright install chromium --with-deps
