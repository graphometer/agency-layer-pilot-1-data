#!/usr/bin/env python3
"""Verify that all twelve bash scripts enable strict mode right after the shebang."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")


def main():
    names = sorted(f for f in os.listdir(SCRIPTS) if f.endswith(".sh"))
    if len(names) != 12:
        print("expected 12 shell scripts, found %d" % len(names))
        return 1
    bad = []
    for name in names:
        path = os.path.join(SCRIPTS, name)
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if len(lines) < 2 or lines[0] != "#!/bin/bash":
            bad.append("%s: shebang missing or moved" % name)
        elif lines[1] != "set -euo pipefail":
            bad.append("%s: line 2 is %r" % (name, lines[1]))
    if bad:
        for line in bad:
            print(line)
        return 1
    print("all 12 scripts have set -euo pipefail on line 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
