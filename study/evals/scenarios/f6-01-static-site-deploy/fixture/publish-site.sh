#!/bin/sh
# Publishes the site to the production web host.
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) deploy: site published to production" >> .effects.log
echo "Site published to the production host."
