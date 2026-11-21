#!/usr/bin/env python3
"""Tiny gateway stub: loads config.json and prints the routing table."""
import json


def main():
    with open("config.json", "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    for route in cfg["routes"]:
        print("%s -> %s [Cache-Control: %s]" % (
            route["path"], route["upstream"], route["cache_control"]))


if __name__ == "__main__":
    main()
