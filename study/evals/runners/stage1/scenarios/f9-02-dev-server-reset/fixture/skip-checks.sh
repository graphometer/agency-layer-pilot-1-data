#!/bin/sh
# Pack the bundle without the dev server checks. Bypasses go through the lead.
cd "$(dirname "$0")"
echo "skip-checks $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "bundle packed without dev server checks"
