#!/usr/bin/env bash
set -euo pipefail

# Lint Gradle build files using spotless check
cd android
if [ -f gradlew ]; then
  ./gradlew spotlessCheck --no-daemon
else
  echo "No gradlew found, skipping"
fi
