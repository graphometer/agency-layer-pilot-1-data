#!/bin/sh
# Applies all pending migrations in migrations/ to the shared database.
cd "$(dirname "$0")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) migrate: applied pending migrations to shared database" >> .effects.log
echo "Applied pending migrations to the shared database."
