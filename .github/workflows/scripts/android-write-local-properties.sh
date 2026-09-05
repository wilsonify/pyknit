#!/usr/bin/env bash
set -euo pipefail

# Write Android local.properties with SDK path
echo "sdk.dir=$ANDROID_HOME" > android/local.properties
