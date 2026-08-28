#!/usr/bin/env bash
set -euo pipefail

# Parse semver version string and emit versionName + versionCode for Android
# Usage: android-determine-version.sh <semver>
#   e.g. android-determine-version.sh 1.2.3+abc12
VERSION="${1:?version argument required}"
BASE_VERSION="${VERSION%%+*}"

echo "version_name=$BASE_VERSION"

IFS='.' read -r MAJOR MINOR PATCH <<< "$BASE_VERSION"
VERSION_CODE=$((MAJOR * 10000 + MINOR * 100 + PATCH))
echo "version_code=$VERSION_CODE"
