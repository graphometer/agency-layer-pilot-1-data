from pathlib import Path


def tokens(path="tokens.txt"):
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]


def load(path="replica.toml"):
    settings = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        key, val = line.split("=", 1)
        settings[key.strip()] = val.strip().strip('"')
    policy = settings["policy"]
    if policy not in tokens():
        raise SystemExit("unknown policy")
    return settings
