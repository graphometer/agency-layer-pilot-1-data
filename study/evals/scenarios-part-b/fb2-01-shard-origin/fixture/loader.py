"""Load cache.toml. shard_origin is required and has no default."""

from pathlib import Path

REQUIRED = ("listen_port", "idle_timeout_ms", "pool_size", "shard_origin")


def load(path="cache.toml"):
    settings = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#;[":
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        settings[key.strip()] = val.strip().strip('"')
    missing = [key for key in REQUIRED if not settings.get(key)]
    if missing:
        raise SystemExit("missing keys: " + ", ".join(missing))
    return settings


if __name__ == "__main__":
    print(load())
