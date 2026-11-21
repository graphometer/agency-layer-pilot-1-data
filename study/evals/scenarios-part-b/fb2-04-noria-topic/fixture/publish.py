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


def load(path="publisher.toml"):
    cfg = parse_toml(path)
    return {
        "client_id": cfg["client_id"],
        "qos": int(cfg["qos"]),
        "retry_ms": int(cfg["retry_ms"]),
        "keepalive_s": int(cfg["keepalive_s"]),
        "noria_topic": cfg["noria_topic"],
    }


if __name__ == "__main__":
    print(load())
