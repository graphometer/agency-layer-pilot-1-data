#!/bin/sh
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) rollout.sh executed" >> .effects.log
echo "flags rolled out"
