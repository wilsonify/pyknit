#!/usr/bin/env bash
set -euo pipefail

# Rewrite a site directory for the canonical public GitHub Pages URL and
# validate the result (see scripts/prepare_pages_site.py). This is the
# production step run by the deploy-pages job; local development builds
# keep root-relative URLs and are served from the domain root.
#
# Usage: prepare-pages-site.sh [SITE_DIR]     (default: site)
# Env:   SITE_URL (required) — canonical public base URL of the deployed site.

SITE_URL="${SITE_URL:?SITE_URL must be set (e.g. https://wilsonify.github.io/pyknit/)}"
SITE_DIR="${1:-site}"

PYTHON_BIN="python"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
	PYTHON_BIN="python3"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
	echo "python or python3 is required" >&2
	exit 127
fi

"$PYTHON_BIN" scripts/prepare_pages_site.py "$SITE_DIR"