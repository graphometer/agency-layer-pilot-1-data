#!/bin/sh
# Installs the scripts/ directory on the job host. Each install is recorded
# in .effects.log.
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) install scripts job-host" >> "$(dirname "$0")/.effects.log"
