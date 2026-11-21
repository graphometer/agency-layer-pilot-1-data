#!/bin/sh
# Deletes rotated logs older than retention_days from log_dir.
set -e
. ./app.conf
find "$log_dir" -name '*.log.*' -mtime +"$retention_days" -delete
