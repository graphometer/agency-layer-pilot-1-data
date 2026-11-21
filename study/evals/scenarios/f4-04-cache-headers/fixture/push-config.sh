#!/bin/sh
# Reloads the gateway with the current config.json.
printf '%s apply config.json\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "gateway reloaded with config.json"
