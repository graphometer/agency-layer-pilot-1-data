#!/usr/bin/env python3
"""Build out/rollups.csv: one "meter,total" row per meter, sorted."""
import csv
import os


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    totals = {}
    with open("data/readings.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            totals[row["meter"]] = totals.get(row["meter"], 0) + int(row["kwh"])
    os.makedirs("out", exist_ok=True)
    with open("out/rollups.csv", "w", newline="") as fh:
        for meter in sorted(totals):
            fh.write("%s,%d\n" % (meter, totals[meter]))
    print("built out/rollups.csv (%d rows)" % len(totals))


if __name__ == "__main__":
    main()
