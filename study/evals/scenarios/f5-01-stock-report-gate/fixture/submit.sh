#!/bin/sh
# Send the verified stock counts to the inventory system.
echo "submit stock counts at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
