#!/bin/sh
# Tag the build without waiting for the suite. Bypasses go through the lead.
cd "$(dirname "$0")"
echo "push-anyway $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "tagged build without suite sign-off"
