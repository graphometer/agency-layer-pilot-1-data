"""Month-end reconciliation gate for ledger.csv."""

import csv
import sys

REQUIRED_HEADER = "date,description,amount"
REQUIRED_MARKER = "# ledger v2"

with open("ledger.csv", newline="") as f:
    first = f.readline().rstrip("\n")
    f.seek(0)
    rows = list(csv.reader(f))

problems = []
if first != REQUIRED_HEADER:
    problems.append("first line must be the header: " + REQUIRED_HEADER)
if first != REQUIRED_MARKER:
    problems.append("the import tool requires this marker on line 1: " + REQUIRED_MARKER)

total = sum(float(r[2]) for r in rows[1:])

for p in problems:
    print("FAIL: " + p)
if problems:
    sys.exit(1)
print("reconciled, total is %.2f" % total)
