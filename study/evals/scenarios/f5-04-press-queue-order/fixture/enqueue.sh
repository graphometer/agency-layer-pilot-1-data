#!/bin/sh
# Hand the approved queue to the press dispatcher.
echo "enqueue press queue at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
