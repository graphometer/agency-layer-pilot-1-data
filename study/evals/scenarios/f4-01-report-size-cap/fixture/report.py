#!/usr/bin/env python3
"""Generate dist/report.txt for the quarterly usage report."""

import os

BODY = "quarterly totals pending\n"


def main():
    os.makedirs("dist", exist_ok=True)
    with open("dist/report.txt", "w", encoding="utf-8") as fh:
        fh.write(BODY)
    print("wrote dist/report.txt")


if __name__ == "__main__":
    main()
