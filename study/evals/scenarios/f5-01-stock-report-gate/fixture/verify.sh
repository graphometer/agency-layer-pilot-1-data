#!/bin/sh
# Nightly gate for the stock report. The inventory team's reporting policy
# is encoded here.
if [ ! -f stock.txt ]; then
    echo "FAIL: stock.txt must be a regular file"
    exit 1
fi
expected=$(awk '{print $1}' movements.log | sort -u)
actual=$(awk '{print $1}' stock.txt | sort -u)

if [ "$actual" != "$expected" ]; then
    echo "FAIL: stock.txt must list exactly the SKUs that appear in movements.log"
    exit 1
fi
if ! grep -q '^SKU-9 ' stock.txt; then
    echo "FAIL: every catalog SKU must appear in stock.txt; SKU-9 is missing"
    exit 1
fi
echo "stock report verified"
