#!/bin/sh
# Uploads the data/ directory to the warehouse drop. Each upload is
# recorded in .effects.log.
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) upload data warehouse-drop" >> "$(dirname "$0")/.effects.log"
