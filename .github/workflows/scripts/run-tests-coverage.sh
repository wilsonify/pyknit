#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage for SonarCloud analysis
python -m pytest test/unit --cov=pyknit --cov-report=xml:coverage.xml --junitxml=sonar-results.xml
