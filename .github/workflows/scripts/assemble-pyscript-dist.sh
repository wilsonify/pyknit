#!/usr/bin/env bash
set -euo pipefail

# Assemble PyScript distribution from demos + runtime + wheel
mkdir -p dist/pyscript
cp -a demos/. dist/pyscript/
mkdir -p dist/pyscript/_wheel
cp build/wheel/*.whl dist/pyscript/_wheel/
mkdir -p dist/pyscript/_assets/pyodide dist/pyscript/_assets/wheels dist/pyscript/_assets/pyscript
cp -a build/pyodide/. dist/pyscript/_assets/pyodide/ 2>/dev/null || true
cp -a build/wheels/. dist/pyscript/_assets/wheels/ 2>/dev/null || true
cp -a build/pyscript/. dist/pyscript/_assets/pyscript/ 2>/dev/null || true
