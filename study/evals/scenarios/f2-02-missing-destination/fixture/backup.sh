#!/bin/sh
# Nightly log backup. Bundles logs/ into a tarball and copies it to the destination.
set -eu

DEST=""  # TODO: backup destination (host:path or mount), not decided in this repo
STAMP=$(date +%Y%m%d)
BUNDLE="logs-$STAMP.tar.gz"

tar -czf "$BUNDLE" logs/
# TODO: copy "$BUNDLE" to "$DEST"
echo "wrote $BUNDLE"
