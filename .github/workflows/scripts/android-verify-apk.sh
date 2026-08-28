#!/usr/bin/env bash
set -euo pipefail

# Verify that the Android APK exists and is a reasonable size (>1MB)
APK_PATH="${1:-apk/app-debug.apk}"

test -f "$APK_PATH"
SIZE=$(stat -c%s "$APK_PATH" 2>/dev/null || stat -f%z "$APK_PATH")
test "$SIZE" -gt 1000000
echo "Android APK verified ($(du -h "$APK_PATH" | cut -f1))"
