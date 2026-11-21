from pathlib import Path


def instants(path="instants.txt"):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        name, day = line.split()
        out[name] = day
    return out


def parse_toml(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip().strip('"')
    return out


def load(path="frost.toml"):
    cfg = parse_toml(path)
    catalog = instants()
    open_day = catalog[cfg["open"]]
    close_day = catalog[cfg["close"]]
    if not open_day < close_day:
        raise SystemExit("empty window")
    return cfg
