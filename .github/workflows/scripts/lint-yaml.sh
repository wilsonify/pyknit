#!/usr/bin/env bash
set -euo pipefail

# Lint workflow YAML files
pip install yamllint
yamllint -d relaxed .github/workflows/*.yml
