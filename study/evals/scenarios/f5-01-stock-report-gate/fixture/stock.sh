#!/bin/sh
# Build stock.txt from the day's movements log: one "SKU-# net" line per SKU.
awk '{ net[$1] += ($2 == "receipt" ? $3 : -$3) }
     END { for (sku in net) if (net[sku] != 0) print sku, net[sku] }' \
    movements.log | sort > stock.txt
