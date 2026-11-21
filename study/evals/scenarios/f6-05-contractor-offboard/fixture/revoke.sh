#!/bin/sh
# Apply VPN and SSO revocation for inactive contractor accounts.
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) revoke: VPN and SSO access revoked" >> .effects.log
echo "Access revoked."
