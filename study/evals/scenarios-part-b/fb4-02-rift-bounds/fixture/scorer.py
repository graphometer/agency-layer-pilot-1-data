from pathlib import Path


def parse_yaml(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        key, val = line.split(":", 1)
        out[key.strip()] = val.strip()
    return out


def window(path="bounds.yaml"):
    cfg = parse_yaml(path)
    lo = int(cfg["rift_floor"])
    hi = int(cfg["rift_ceil"])
    if lo > hi:
        raise SystemExit("empty window")
    return range(lo, hi + 1)
