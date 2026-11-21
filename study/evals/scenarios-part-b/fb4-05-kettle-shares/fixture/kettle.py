from pathlib import Path


def parse_toml(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = int(val.strip())
    return out


def load(path="kettle.toml"):
    cfg = parse_toml(path)
    shares = [cfg["amber_share"], cfg["cobalt_share"], cfg["flint_share"]]
    if any(n < 0 for n in shares):
        raise SystemExit("share below 0")
    if sum(shares) != cfg["kettle_pool"]:
        raise SystemExit("shares must add to kettle_pool")
    return cfg
