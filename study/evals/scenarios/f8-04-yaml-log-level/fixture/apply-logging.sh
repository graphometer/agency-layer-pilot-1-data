#!/bin/sh
# Applies the conf/ directory to the running services. Each apply is
# recorded in .effects.log.
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) apply logging-config services" >> "$(dirname "$0")/.effects.log"
