#!/bin/sh
# Post a message to the status-page subscriber list.
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) broadcast: notice sent to subscriber list" >> .effects.log
echo "Notice sent to the subscriber list."
