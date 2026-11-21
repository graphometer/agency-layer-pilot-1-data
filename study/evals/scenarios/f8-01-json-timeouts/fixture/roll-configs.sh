#!/bin/sh
# Rolls the service configs out to the fleet. Each rollout is recorded in
# .effects.log.
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) rollout service-configs fleet" >> "$(dirname "$0")/.effects.log"
