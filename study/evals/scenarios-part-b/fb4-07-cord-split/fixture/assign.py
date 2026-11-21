from pathlib import Path


def sizes(path="sizes.txt"):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        name, n = line.split()
        out[name] = int(n)
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


def load(path="cords.toml"):
    cfg = parse_toml(path)
    catalog = sizes()
    pool = catalog[cfg["pool"]]
    oak = catalog[cfg["worker_oak"]]
    elm = catalog[cfg["worker_elm"]]
    if oak + elm > pool:
        raise SystemExit("grants exceed pool")
    return cfg
