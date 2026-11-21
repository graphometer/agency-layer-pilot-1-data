#!/bin/sh
# Hourly log roll-up. Counts lines in each log under logs/.
for f in logs/*.log; do
  n=$(wc -l < "$f")
  echo "processed: $(basename "$f") ($n lines)"
done
