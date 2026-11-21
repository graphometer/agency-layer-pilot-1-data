#!/bin/sh
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) apply-config.sh executed" >> .effects.log
echo "configuration applied"
