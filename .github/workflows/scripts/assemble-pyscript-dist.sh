#!/usr/bin/env bash
set -euo pipefail

# ── Assemble a self-contained PyScript distribution ──────────────────
#
# Output layout (everything reachable from site root):
#
#   dist/pyscript/
#     index.html
#     <demo>/demo.html
#     pyodide/          (was _assets/pyodide/)
#     pyscript/         (was _assets/pyscript/)
#     wheels/           (merged from _assets/wheels/ + _wheel/)
#     common.css        (was _assets/common.css)
#     sock.jpg          (was _assets/sock.jpg)
#     sweater.jpg       (was _assets/sweater.jpg)
#     gauge-conversion.py (was _assets/gauge-conversion.py)
#
# Every asset URL in the built HTML is root-relative (e.g. /pyodide/pyodide.mjs),
# which is correct when served from the domain root (Docker/nginx, local dev).
# The GitHub Pages deployment rewrites these to absolute URLs under the public
# SITE_URL (see scripts/prepare_pages_site.py) so they survive the /pyknit/ prefix.

DIST="dist/pyscript"
rm -rf "$DIST"
mkdir -p "$DIST"

# 1. Copy the demos directory tree (HTML, demos, _shared, etc.)
cp -a demos/. "$DIST/"

# 2. Remove placeholder files that cause upload failures
rm -f "$DIST/favicon.ico"

# 3. Flatten _assets/ into the site root
if [ -d "$DIST/_assets/pyodide" ]; then
    cp -a "$DIST/_assets/pyodide/." "$DIST/pyodide/"
fi
if [ -d "$DIST/_assets/pyscript" ]; then
    cp -a "$DIST/_assets/pyscript/." "$DIST/pyscript/"
fi
mkdir -p "$DIST/wheels"
if [ -d "$DIST/_assets/wheels" ]; then
    cp -a "$DIST/_assets/wheels/." "$DIST/wheels/"
fi
# Copy runtime assets from build cache (may not exist in all build paths)
if [ -d build/pyscript ]; then
    cp -a build/pyscript/. "$DIST/pyscript/" 2>/dev/null || true
fi
if [ -d build/pyodide ]; then
    cp -a build/pyodide/. "$DIST/pyodide/" 2>/dev/null || true
fi
# Copy dependency wheels from build cache (may not exist in all build paths)
if [ -d build/wheels ]; then
    cp -a build/wheels/. "$DIST/wheels/" 2>/dev/null || true
fi
# Merge the committed pyknit wheel into wheels/
if [ -d "$DIST/_wheel" ]; then
    cp -a "$DIST/_wheel/." "$DIST/wheels/" 2>/dev/null || true
fi
# Also pull from the build wheel dir
if ls build/wheel/*.whl 1>/dev/null 2>&1; then
    cp build/wheel/*.whl "$DIST/wheels/" 2>/dev/null || true
fi

# Copy static assets from _assets/ to root. The gauge bootstrap is generated
# here as well as in the clean-build path so local and CI assemblies agree.
if [ ! -f "$DIST/_assets/gauge-conversion.py" ]; then
    printf '%s\n' \
        '"""Gauge conversion demo bootstrap (generated)."""' \
        'from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401  # auto-bootstraps' \
        > "$DIST/_assets/gauge-conversion.py"
fi
for f in common.css sock.jpg sweater.jpg gauge-conversion.py; do
    if [ -f "$DIST/_assets/$f" ]; then
        cp "$DIST/_assets/$f" "$DIST/$f"
    fi
done

# Remove the old nested directories
rm -rf "$DIST/_assets" "$DIST/_wheel"

# 4. Rewrite HTML paths: flatten _assets/ and _wheel/ references
#
#    /_assets/pyodide/  → /pyodide/
#    /_assets/pyscript/ → /pyscript/
#    /_assets/wheels/   → /wheels/
#    /_wheel/           → /wheels/
#    /_assets/common.css → /common.css
#    /_assets/gauge-conversion.py → /gauge-conversion.py
#    _assets/sock.jpg   → sock.jpg   (relative src in index.html)
#    _assets/sweater.jpg → sweater.jpg (relative src in index.html)

find "$DIST" -name '*.html' -exec sed -i \
    -e 's|/_assets/pyodide/|/pyodide/|g' \
    -e 's|/_assets/pyscript/|/pyscript/|g' \
    -e 's|/_assets/wheels/|/wheels/|g' \
    -e 's|/_wheel/|/wheels/|g' \
    -e 's|/_assets/common\.css|/common.css|g' \
    -e 's|/_assets/gauge-conversion\.py|/gauge-conversion.py|g' \
    -e 's|_assets/sock\.jpg|sock.jpg|g' \
    -e 's|_assets/sweater\.jpg|sweater.jpg|g' \
    {} +

# 5. Validate the published artifact before uploading it. This keeps a
# missing runtime file or source-tree path from reaching Docker or Pages.
required_files=(
    common.css
    sock.jpg
    sweater.jpg
    gauge-conversion.py
    pyscript/core.js
    pyscript/core.css
    pyodide/pyodide.mjs
    pyodide/pyodide.asm.js
    pyodide/pyodide.asm.wasm
    pyodide/pyodide-lock.json
    pyodide/python_stdlib.zip
    pyodide/micropip-0.5.0-py3-none-any.whl
    pyodide/packaging-23.1-py3-none-any.whl
    wheels/Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl
    wheels/pydantic-1.10.7-py3-none-any.whl
    wheels/typing_extensions-4.7.1-py3-none-any.whl
    wheels/pyknit-*.whl
)
for pattern in "${required_files[@]}"; do
    if ! compgen -G "$DIST/$pattern" | grep -q .; then
        echo "ERROR: missing or empty published asset: $DIST/$pattern" >&2
        exit 1
    fi
    while IFS= read -r file; do
        if [ ! -s "$file" ]; then
            echo "ERROR: empty published asset: $file" >&2
            exit 1
        fi
    done < <(compgen -G "$DIST/$pattern")
done

if grep -RInE '\.\./|_assets/|_wheel/' "$DIST" --include='*.html'; then
    echo "ERROR: generated HTML contains a source-tree or traversal asset path" >&2
    exit 1
fi

# 6. Summary
echo "=== Assembled PyScript distribution ==="
echo "Files:"
find "$DIST" -type f | head -40 | sed 's|^|  |'
echo "..."
echo "Total files: $(find "$DIST" -type f | wc -l)"
