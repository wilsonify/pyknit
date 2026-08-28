#!/usr/bin/env bash
set -euo pipefail

# Clean build of Python wheel
rm -rf build/ dist/ *.egg-info
python -m pip install --upgrade pip build
python -m build --wheel --outdir dist/
