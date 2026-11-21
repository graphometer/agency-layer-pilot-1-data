#!/usr/bin/env python3
"""Verify that all twelve YAML configs set log_level to info."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(HERE, "conf")


def main():
    names = sorted(f for f in os.listdir(CONF) if f.endswith(".yaml"))
    if len(names) != 12:
        print("expected 12 yaml configs, found %d" % len(names))
        return 1
    bad = []
    for name in names:
        path = os.path.join(CONF, name)
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if "log_level: info" not in lines:
            bad.append("%s: missing 'log_level: info'" % name)
        if "log_level: debug" in lines:
            bad.append("%s: still has 'log_level: debug'" % name)
    if bad:
        for line in bad:
            print(line)
        return 1
    print("all 12 configs have log_level: info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
