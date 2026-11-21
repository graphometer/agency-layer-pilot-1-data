#!/bin/sh
# Rebuild the rollup and verify the row checksums.
set -u
cd "$(dirname "$0")"
python3 pipeline/build.py || exit 1
python3 pipeline/checksums.py
