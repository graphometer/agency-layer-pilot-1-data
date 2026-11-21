"""Bind using listen.toml. nimbus_backlog is the SO_BACKLOG stand-in."""
from pathlib import Path


def settings(path="listen.toml"):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#;[":
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip().strip('"')
    return out
