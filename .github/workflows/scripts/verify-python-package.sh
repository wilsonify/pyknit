#!/usr/bin/env bash
set -euo pipefail

# Verify built Python package with twine
pip install twine
twine check dist/*.whl
