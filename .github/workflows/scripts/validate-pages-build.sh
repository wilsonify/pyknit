#!/usr/bin/env bash
set -euo pipefail

# Regression check for the GitHub Pages production build: run the SITE_URL
# rewrite + validation on a throwaway copy of the freshly assembled artifact.
# Fails if any PyScript runtime URL would escape the deployed site path.
# The uploaded artifact itself stays root-relative because Docker/nginx and
# local dev servers serve it from the domain root.

SITE_URL="${SITE_URL:-https://wilsonify.github.io/pyknit/}"
TMP_SITE="$(mktemp -d)"
trap 'rm -rf "$TMP_SITE"' EXIT

cp -a dist/pyscript/. "$TMP_SITE"/
SITE_URL="$SITE_URL" python scripts/prepare_pages_site.py "$TMP_SITE"