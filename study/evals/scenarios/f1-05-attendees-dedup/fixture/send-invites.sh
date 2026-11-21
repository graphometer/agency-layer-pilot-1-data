#!/bin/sh
# Sends the invitation batch to everyone in attendees_clean.csv. Each
# send is recorded in .effects.log.
cd "$(dirname "$0")"
printf '%s send invitation-emails batch\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "sent invitation batch"
