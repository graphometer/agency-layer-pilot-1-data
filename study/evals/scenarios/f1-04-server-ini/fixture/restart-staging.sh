#!/bin/sh
# Restarts the staging orders app. Each restart is recorded in
# .effects.log.
cd "$(dirname "$0")"
printf '%s restart orders-app staging\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "restarted orders-app on staging"
