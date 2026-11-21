#!/bin/sh
# Close the books for the month.
echo "finalize ledger at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
