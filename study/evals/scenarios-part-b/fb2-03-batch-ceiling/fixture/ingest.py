from pathlib import Path


def parse_yaml(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        out[key.strip()] = val.strip().strip('"')
    return out


def load(path="limiter.yaml"):
    cfg = parse_yaml(path)
    return {
        "concurrency": int(cfg["concurrency"]),
        "window_ms": int(cfg["window_ms"]),
        "max_inflight": int(cfg["max_inflight"]),
        "batch_ceiling": int(cfg["batch_ceiling"]),
    }


if __name__ == "__main__":
    print(load())
