#!/bin/sh
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ship-service.sh executed" >> .effects.log
echo "deploy finished"
