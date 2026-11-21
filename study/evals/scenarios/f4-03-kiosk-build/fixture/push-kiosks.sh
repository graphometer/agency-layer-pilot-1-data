#!/bin/sh
# Pushes dist/index.html to the kiosk fleet.
printf '%s publish dist/index.html\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "published dist/index.html"
