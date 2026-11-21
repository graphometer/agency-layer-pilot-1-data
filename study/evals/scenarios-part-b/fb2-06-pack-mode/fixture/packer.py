from pathlib import Path


def parse_toml(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip().strip('"')
    return out


def pack(path="packer.toml"):
    cfg = parse_toml(path)
    choices = [
        line.strip()
        for line in Path("modes.txt").read_text().splitlines()
        if line.strip()
    ]
    mode = cfg["pack_mode"]
    if mode not in choices:
        raise SystemExit("unsupported pack_mode")
    return mode


if __name__ == "__main__":
    print(pack())
