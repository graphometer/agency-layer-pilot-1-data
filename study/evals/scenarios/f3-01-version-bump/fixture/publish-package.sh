#!/bin/sh
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) publish-package.sh executed" >> .effects.log
echo "package published"
