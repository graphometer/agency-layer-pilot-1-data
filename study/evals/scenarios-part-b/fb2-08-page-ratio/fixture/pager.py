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


def watch(path="alerts.yml"):
    cfg = parse_yaml(path)
    return {
        "window_s": int(cfg["window_s"]),
        "channel": cfg["channel"],
        "min_samples": int(cfg["min_samples"]),
        "page_ratio_cut": float(cfg["page_ratio_cut"]),
    }


if __name__ == "__main__":
    print(watch())
