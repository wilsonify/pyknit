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

python scripts/prepare_pages_site.py "$SITE_DIR"