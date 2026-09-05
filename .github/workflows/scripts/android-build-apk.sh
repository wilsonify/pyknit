#!/usr/bin/env bash
set -euo pipefail

# Build Android debug APK
# Usage: android-build-apk.sh <versionName> <versionCode>
VERSION_NAME="${1:?versionName required}"
VERSION_CODE="${2:?versionCode required}"

cd android
chmod +x gradlew
./gradlew assembleDebug \
  -PversionName="$VERSION_NAME" \
  -PversionCode="$VERSION_CODE" \
  --no-daemon
