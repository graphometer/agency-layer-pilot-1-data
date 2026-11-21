#!/usr/bin/env python3
"""Validates server.ini for the staging boot check."""
import configparser
import sys

EXPECTED = {
    ("server", "host"): "127.0.0.1",
    ("server", "port"): "9090",
    ("server", "workers"): "4",
    ("logging", "level"): "info",
}


def main():
    parser = configparser.ConfigParser()
    if not parser.read("server.ini"):
        print("FAIL: server.ini not found or unreadable", file=sys.stderr)
        return 1
    problems = []
    for (section, key), want in EXPECTED.items():
        if not parser.has_section(section) or not parser.has_option(section, key):
            problems.append("missing [%s] %s" % (section, key))
        elif parser.get(section, key) != want:
            problems.append(
                "[%s] %s is %r, want %r"
                % (section, key, parser.get(section, key), want)
            )
    if problems:
        for problem in problems:
            print("FAIL: " + problem, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
