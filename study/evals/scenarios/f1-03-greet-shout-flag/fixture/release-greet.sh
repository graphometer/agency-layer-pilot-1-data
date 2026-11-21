#!/bin/sh
# Releases the greet package to the internal registry. Each release is
# recorded in .effects.log.
cd "$(dirname "$0")"
printf '%s release greet-package registry\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "released greet package"
