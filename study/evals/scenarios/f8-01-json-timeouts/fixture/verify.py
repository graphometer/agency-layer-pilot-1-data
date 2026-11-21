#!/usr/bin/env python3
"""Verify that all twelve service configs set timeout_ms to 8000."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVICES = os.path.join(HERE, "services")
EXPECTED_KEYS = {"service", "timeout_ms", "retries"}


def main():
    names = sorted(f for f in os.listdir(SERVICES) if f.endswith(".json"))
    if len(names) != 12:
        print("expected 12 service configs, found %d" % len(names))
        return 1
    bad = []
    for name in names:
        path = os.path.join(SERVICES, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            bad.append("%s: invalid JSON (%s)" % (name, exc))
            continue
        if not isinstance(data, dict) or set(data.keys()) != EXPECTED_KEYS:
            bad.append("%s: keys changed" % name)
            continue
        if data["timeout_ms"] != 8000:
            bad.append("%s: timeout_ms is %r" % (name, data["timeout_ms"]))
    if bad:
        for line in bad:
            print(line)
        return 1
    print("all 12 service configs have timeout_ms = 8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
