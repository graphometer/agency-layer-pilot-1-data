from pathlib import Path


def parse_job(path):
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


def render():
    job = parse_job("job.toml")
    sql = Path("export.sql").read_text()
    return sql.replace("{{split}}", job["sku_split_col"])


if __name__ == "__main__":
    print(render())
