from pathlib import Path


def parse_features(path="features.toml"):
    section = None
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            out[section] = {}
            continue
        key, val = line.split("=", 1)
        out[section][key.strip()] = val.strip().strip('"')
    return out


def load(path="features.toml"):
    feats = parse_features(path)
    for name, row in feats.items():
        if row.get("state") != "on":
            continue
        need_off = row.get("requires_off") or ""
        if need_off and feats.get(need_off, {}).get("state") == "on":
            raise SystemExit(name + " requires_off " + need_off)
    return feats
