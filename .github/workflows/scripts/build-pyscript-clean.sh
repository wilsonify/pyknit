#!/usr/bin/env bash
set -euo pipefail

# Clean build of PyScript distribution
rm -rf build/
mkdir -p demos/_assets
printf '%s\n' \
  '"""Gauge conversion demo bootstrap."""' \
  'from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401' \
  > demos/_assets/gauge-conversion.py
python -m pip wheel . -w build/wheel --no-deps
