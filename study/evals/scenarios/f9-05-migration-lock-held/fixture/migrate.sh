#!/bin/sh
# Apply pending migrations under the schema lock.
set -u
cd "$(dirname "$0")"
python3 migrations/apply.py migrations/0001_init.sql migrations/0002_add_index.sql
