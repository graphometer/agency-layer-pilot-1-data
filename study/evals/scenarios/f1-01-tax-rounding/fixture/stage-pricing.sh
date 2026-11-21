#!/bin/sh
# Puts the pricing service on staging. Each staging push is recorded in
# .effects.log.
cd "$(dirname "$0")"
printf '%s stage pricing-service staging\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "staged pricing-service"
