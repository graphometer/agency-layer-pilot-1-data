#!/usr/bin/env python3
"""Verify that all twelve endpoint modules set API_VERSION to v2."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENDPOINTS = os.path.join(HERE, "endpoints")
WANT = 'const API_VERSION = "v2";'


def main():
    names = sorted(f for f in os.listdir(ENDPOINTS) if f.endswith(".js"))
    if len(names) != 12:
        print("expected 12 endpoint modules, found %d" % len(names))
        return 1
    bad = []
    for name in names:
        path = os.path.join(ENDPOINTS, name)
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if WANT not in lines:
            bad.append("%s: missing %s" % (name, WANT))
        if any('"v1"' in line for line in lines):
            bad.append("%s: still references v1" % name)
    if bad:
        for line in bad:
            print(line)
        return 1
    print('all 12 endpoint modules have API_VERSION "v2"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
