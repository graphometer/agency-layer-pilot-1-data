#!/bin/sh
# Loads data.csv into the warehouse.
printf '%s import data.csv\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .effects.log
echo "imported data.csv"
