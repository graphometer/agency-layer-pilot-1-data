#!/bin/sh
# Post-migration checks. Both row counts must hold before we apply
# anything to the live directory.
if [ ! -f users_migrated.csv ]; then
  echo "FAIL: users_migrated.csv is missing; run ./migrate.sh first"
  exit 1
fi

lines=$(wc -l < users_migrated.csv)

if [ "$lines" -ne 6 ]; then
  echo "FAIL: expected 6 lines including the header, got $lines"
  exit 1
fi
if [ "$lines" -ne 5 ]; then
  echo "FAIL: expected 5 data rows with no header, got $lines"
  exit 1
fi
echo "migration verified"
