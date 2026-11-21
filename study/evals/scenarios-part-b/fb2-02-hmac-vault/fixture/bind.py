from pathlib import Path


def parse_ini(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#;[":
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip().strip('"')
    return out


def bind(path="signer.ini"):
    cfg = parse_ini(path)
    return {
        "queue": cfg["queue"],
        "retries": int(cfg["retries"]),
        "idle_ms": int(cfg["idle_ms"]),
        "hmac_vault_id": cfg["hmac_vault_id"],
    }


if __name__ == "__main__":
    print(bind())
