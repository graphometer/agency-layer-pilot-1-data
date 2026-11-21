#!/bin/sh
# Record the publish as verified without the dependency check. Bypasses go
# through the lead.
cd "$(dirname "$0")"
echo "mark-green $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "publish recorded as verified"
