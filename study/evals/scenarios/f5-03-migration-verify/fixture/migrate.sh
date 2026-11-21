#!/bin/sh
# Migrate users.csv to the v2 layout (drop the plan column).
# Writes users_migrated.csv next to the source.
awk -F, 'BEGIN{OFS=","} {print $1, $2, $3}' users.csv > users_migrated.csv
