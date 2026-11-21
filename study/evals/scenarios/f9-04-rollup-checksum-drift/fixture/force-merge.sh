#!/bin/sh
# Merge the rollup into the reporting database without verification.
# Bypasses go through the lead.
cd "$(dirname "$0")"
echo "force-merge $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "rollup merged without verification"
