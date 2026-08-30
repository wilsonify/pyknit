#!/usr/bin/env bash
set -euo pipefail

# Download and verify Grype binary.
# Usage: install-grype.sh <version>
# Requires: GRYPE_VERSION env var or version argument.

VERSION="${1:-${GRYPE_VERSION:-}}"
if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

INSTALL_DIR="/usr/local/bin"
BINARY="$INSTALL_DIR/grype"
ARCHIVE="/tmp/grype_${VERSION}_linux_amd64.tar.gz"
CHECKSUM="/tmp/grype_${VERSION}_checksums.txt"
BASE_URL="https://github.com/anchore/grype/releases/download/v${VERSION}"

# Skip if already installed at the correct version
if [ -x "$BINARY" ] && "$BINARY" version 2>/dev/null | grep -q "${VERSION}"; then
  echo "Grype ${VERSION} already installed"
  exit 0
fi

echo "Downloading Grype ${VERSION}..."
curl -sSfL -o "$ARCHIVE" "${BASE_URL}/grype_${VERSION}_linux_amd64.tar.gz"
curl -sSfL -o "$CHECKSUM" "${BASE_URL}/grype_${VERSION}_checksums.txt"

echo "Verifying checksum..."
cd /tmp && grep "grype_${VERSION}_linux_amd64.tar.gz$" "$CHECKSUM" | sha256sum -c -

echo "Installing Grype..."
tar -xzf "$ARCHIVE" -C /tmp grype
mv /tmp/grype "$BINARY"
chmod +x "$BINARY"

# Cleanup
rm -f "$ARCHIVE" "$CHECKSUM"

echo "Grype $("$BINARY" version) installed"
