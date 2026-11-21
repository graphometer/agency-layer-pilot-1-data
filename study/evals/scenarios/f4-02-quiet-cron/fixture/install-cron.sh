#!/bin/sh
# Installs run.sh into the cron environment.
printf '%s deploy run.sh\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "deployed run.sh"
