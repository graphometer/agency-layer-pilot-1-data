#!/bin/sh
# Publishes dist/report.txt to the reporting bucket.
printf '%s publish dist/report.txt\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "published dist/report.txt"
