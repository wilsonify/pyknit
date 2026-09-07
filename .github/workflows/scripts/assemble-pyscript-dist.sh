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
# Every asset URL in the built HTML is root-relative (e.g. /pyodide/pyodide.mjs).
# The deployment target sets <base href> so they resolve under the correct prefix.

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

# Copy static assets from _assets/ to root
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

# 5. Summary
echo "=== Assembled PyScript distribution ==="
echo "Files:"
find "$DIST" -type f | head -40 | sed 's|^|  |'
echo "..."
echo "Total files: $(find "$DIST" -type f | wc -l)"
