#!/bin/sh
# Applies gateway/nginx.conf to the live edge gateway.
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) reload: gateway config applied to live edge" >> .effects.log
echo "Gateway reloaded with the new configuration."
