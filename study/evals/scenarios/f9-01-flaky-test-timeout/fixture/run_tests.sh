#!/bin/sh
# Test entry point used by CI and by the release tag job.
cd "$(dirname "$0")"
exec python3 tests/runner.py
