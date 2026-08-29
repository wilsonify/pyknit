#!/usr/bin/env bash
set -euo pipefail

# Download and verify Syft binary.
# Usage: install-syft.sh <version>
# Requires: SYFT_VERSION env var or version argument.

VERSION="${1:-${SYFT_VERSION:-}}"
if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

INSTALL_DIR="/usr/local/bin"
BINARY="$INSTALL_DIR/syft"
ARCHIVE="/tmp/syft.tar.gz"
CHECKSUM="/tmp/syft.tar.gz.sha256"
BASE_URL="https://github.com/anchore/syft/releases/download/v${VERSION}"

# Skip if already installed at the correct version
if [ -x "$BINARY" ] && "$BINARY" --version 2>/dev/null | grep -q "syft/${VERSION}"; then
  echo "Syft ${VERSION} already installed"
  exit 0
fi

echo "Downloading Syft ${VERSION}..."
curl -sSfL -o "$ARCHIVE" "${BASE_URL}/syft_${VERSION}_linux_amd64.tar.gz"
curl -sSfL -o "$CHECKSUM" "${BASE_URL}/syft_${VERSION}_linux_amd64.tar.gz.sha256"

echo "Verifying checksum..."
cd /tmp && sha256sum -c "$CHECKSUM"

echo "Installing Syft..."
tar -xzf "$ARCHIVE" -C /tmp syft
mv /tmp/syft "$BINARY"
chmod +x "$BINARY"

# Cleanup
rm -f "$ARCHIVE" "$CHECKSUM"

echo "Syft $("$BINARY" --version) installed"
