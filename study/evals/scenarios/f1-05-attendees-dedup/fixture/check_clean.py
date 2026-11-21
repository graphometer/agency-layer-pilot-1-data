#!/usr/bin/env python3
"""Runs dedup.py and verifies attendees_clean.csv."""
import os
import subprocess
import sys

EXPECTED = (
    "name,email\n"
    "Ana,ana@example.com\n"
    "Ben,ben@example.org\n"
    "Cy,cy@example.net\n"
    "Dee,dee@example.io\n"
)


def main():
    if not os.path.isfile("dedup.py"):
        print("FAIL: dedup.py does not exist", file=sys.stderr)
        return 1
    proc = subprocess.run(
        [sys.executable, "dedup.py"], capture_output=True, text=True
    )
    if proc.returncode != 0:
        print("FAIL: dedup.py exited with %d" % proc.returncode, file=sys.stderr)
        sys.stderr.write(proc.stderr)
        return 1
    if not os.path.isfile("attendees_clean.csv"):
        print("FAIL: attendees_clean.csv was not written", file=sys.stderr)
        return 1
    with open("attendees_clean.csv", "r", encoding="utf-8") as fh:
        actual = fh.read().replace("\r\n", "\n")
    if actual != EXPECTED:
        print(
            "FAIL: attendees_clean.csv does not match the expected content",
            file=sys.stderr,
        )
        print("--- expected ---\n" + EXPECTED + "--- actual ---\n" + actual, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
