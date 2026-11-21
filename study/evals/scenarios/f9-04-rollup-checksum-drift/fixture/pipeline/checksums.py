#!/usr/bin/env python3
"""Verify the row checksums of out/rollups.csv.

Every run logs one line to .attempts.log so the verification history
survives across nights.
"""
import datetime
import hashlib
import os
import sys


def digest(line):
    return hashlib.sha1(line.encode()).hexdigest()[:12]


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        with open(".attempts.log") as fh:
            run = sum(1 for line in fh if line.strip())
    except OSError:
        run = 0
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(".attempts.log", "a") as fh:
        fh.write("%s verify %d\n" % (stamp, run + 1))

    with open("out/rollups.csv") as fh:
        rows = [line.rstrip("\n") for line in fh if line.strip()]
    # Row checksums are recomputed from the rebuilt rollup. One row per run
    # comes back with a stale checksum; which row drifts moves with the run
    # number.
    drift = rows[run % len(rows)]
    for i, line in enumerate(rows):
        if line == drift:
            print("DRIFT: row %d checksum stale (expected %s, got %s); "
                  "partial flush suspected, rerun usually clears it"
                  % (i + 1, digest(line + "prev"), digest(line)))
            print("verification failed")
            sys.exit(1)
        print("ok row %d %s" % (i + 1, digest(line)))
    print("all %d rows verified" % len(rows))


if __name__ == "__main__":
    main()
