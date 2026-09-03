#!/usr/bin/env bash
set -euo pipefail

# Lint workflow YAML files
pip install yamllint
yamllint -d "{extends: relaxed, rules: {line-length: {max: 120}}}" .github/workflows/*.yml
