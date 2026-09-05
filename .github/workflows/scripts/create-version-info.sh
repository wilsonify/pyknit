#!/usr/bin/env bash
set -euo pipefail

# Generate version-info.json for release metadata
# Usage: create-version-info.sh <version> <base_version> <commit_sha>
VERSION="${1:?version required}"
BASE_VERSION="${2:?base_version required}"
COMMIT="${3:?commit required}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

cat > version-info.json << EOF
{
  "version": "$VERSION",
  "base_version": "$BASE_VERSION",
  "commit": "$COMMIT",
  "timestamp": "$TIMESTAMP"
}
EOF

echo "Created version-info.json"
