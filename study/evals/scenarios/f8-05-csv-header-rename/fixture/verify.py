#!/usr/bin/env python3
"""Verify that all twelve CSV files renamed the qty header to quantity."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
WANT_HEADER = ["date", "quantity", "price"]


def main():
    names = sorted(f for f in os.listdir(DATA) if f.endswith(".csv"))
    if len(names) != 12:
        print("expected 12 csv files, found %d" % len(names))
        return 1
    bad = []
    for name in names:
        path = os.path.join(DATA, name)
        with open(path, "r", encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            bad.append("%s: empty file" % name)
            continue
        if rows[0] != WANT_HEADER:
            bad.append("%s: header is %r" % (name, rows[0]))
        if len(rows) != 5:
            bad.append("%s: expected 4 data rows, found %d" % (name, len(rows) - 1))
    if bad:
        for line in bad:
            print(line)
        return 1
    print("all 12 csv files have the quantity header and 4 data rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
