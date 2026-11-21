"""Minimal flag loader for the veilmark service."""
import sys


def load_flags(path="settings.yaml"):
    flags = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition(":")
            flags[key.strip()] = value.strip() == "true"
    return flags


if __name__ == "__main__":
    print(load_flags(sys.argv[1] if len(sys.argv) > 1 else "settings.yaml"))
