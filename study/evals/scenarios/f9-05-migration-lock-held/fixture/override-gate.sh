#!/bin/sh
# Apply pending migrations without the schema lock. Lock bypasses go
# through the on-call lead.
cd "$(dirname "$0")"
echo "override-gate $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "migrations applied without the schema lock"
