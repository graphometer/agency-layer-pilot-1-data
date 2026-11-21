#!/bin/sh
# Publishes the traffic report to the internal dashboard. Each publish is
# recorded in .effects.log.
cd "$(dirname "$0")"
printf '%s publish traffic-report dashboard\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "published traffic report"
