#!/bin/sh
# Build the asset bundle: serve the assets over loopback with the local dev
# server, then pack them with src/pack.py. Every run logs one line to
# .attempts.log so the build history survives across runs.
set -u
cd "$(dirname "$0")"

run=$(awk 'END {print NR + 0}' .attempts.log 2>/dev/null || echo 0)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) build $((run + 1))" >> .attempts.log

rm -f .server_ready
python3 scripts/dev_server.py "$run" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null' EXIT

i=0
while [ ! -f .server_ready ] && [ "$i" -lt 40 ]; do
    sleep 0.05
    i=$((i + 1))
done
if [ ! -f .server_ready ]; then
    echo "build failed: dev server did not start"
    exit 1
fi
port=$(cat .server_ready)
python3 src/pack.py "$port" assets.txt bundle
status=$?
rm -f .server_ready
exit "$status"
