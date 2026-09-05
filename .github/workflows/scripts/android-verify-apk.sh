#!/usr/bin/env bash
set -euo pipefail

# Verify the Android WebView APK: exists, reasonable size, bundles the
# offline web app (dist/) and contains no Chaquopy native Python.
APK_PATH="${1:-apk/app-debug.apk}"

test -f "$APK_PATH"
SIZE=$(stat -c%s "$APK_PATH" 2>/dev/null || stat -f%z "$APK_PATH")
test "$SIZE" -gt 1000000
echo "Android APK verified ($(du -h "$APK_PATH" | cut -f1))"

ENTRIES=$(unzip -l "$APK_PATH")
echo "$ENTRIES" | grep -q "assets/dist/index.html" || { echo "missing assets/dist/index.html"; exit 1; }
echo "$ENTRIES" | grep -q "assets/dist/_assets/pyodide/pyodide.asm.wasm" || { echo "missing pyodide wasm"; exit 1; }
echo "$ENTRIES" | grep -q "assets/dist/_wheel/pyknit-.*\.whl" || { echo "missing pyknit wheel"; exit 1; }
echo "$ENTRIES" | grep -q "assets/dist/sock-calculator/demo.html" || { echo "missing demo pages"; exit 1; }
if echo "$ENTRIES" | grep -q "libchaquopy\|chaquopy"; then echo "APK must not contain Chaquopy"; exit 1; fi
echo "APK contents verified: offline web app bundled, no Chaquopy"
