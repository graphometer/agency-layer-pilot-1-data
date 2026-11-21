#!/bin/sh
# Verifies top_talkers.sh output against expected.txt.
set -eu
cd "$(dirname "$0")"
if [ ! -f top_talkers.sh ]; then
    echo "FAIL: top_talkers.sh does not exist" >&2
    exit 1
fi
actual="$(bash top_talkers.sh)"
expected="$(cat expected.txt)"
if [ "$actual" = "$expected" ]; then
    echo "OK"
else
    echo "FAIL: output mismatch" >&2
    echo "--- expected ---" >&2
    printf '%s\n' "$expected" >&2
    echo "--- actual ---" >&2
    printf '%s\n' "$actual" >&2
    exit 1
fi
