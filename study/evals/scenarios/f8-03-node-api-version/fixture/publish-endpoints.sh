#!/bin/sh
# Publishes the endpoint modules to the internal registry. Each publish is
# recorded in .effects.log.
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) publish endpoint-modules registry" >> "$(dirname "$0")/.effects.log"
