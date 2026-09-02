#!/usr/bin/env bash
set -euo pipefail

# Download PyScript runtime assets into demos/_assets/ so the demo server
# can serve them during integration / index tests.

PYSCRIPT=https://pyscript.net/releases/2024.10.1
PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full

mkdir -p demos/_assets/pyscript demos/_assets/pyodide demos/_assets/wheels

for f in core.css core.js core.js.map core-DHft4mQJ.js \
         core-DHft4mQJ.js.map \
         toml-CvAfdf9_.js toml-DiUM0_qs.js \
         zip-Bf48tRr5.js \
         deprecations-manager-BDRw2fed.js \
         donkey-c355Wa24.js \
         error-CdZsd8BO.js \
         py-editor-BRZBRs2T.js \
         py-terminal-D_z3jMz-.js; do
    curl -fsSL -o "demos/_assets/pyscript/$f" "$PYSCRIPT/$f"
done

for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm pyodide-lock.json \
         python_stdlib.zip micropip-0.5.0-py3-none-any.whl \
         packaging-23.1-py3-none-any.whl; do
    curl -fsSL -o "demos/_assets/pyodide/$f" "$PYODIDE/$f"
done

for f in typing_extensions-4.7.1-py3-none-any.whl \
         pydantic-1.10.7-py3-none-any.whl \
         Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl; do
    curl -fsSL -o "demos/_assets/wheels/$f" "$PYODIDE/$f"
done
