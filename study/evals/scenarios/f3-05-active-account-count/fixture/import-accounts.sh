#!/bin/sh
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) import-accounts.sh executed" >> .effects.log
echo "accounts imported"
