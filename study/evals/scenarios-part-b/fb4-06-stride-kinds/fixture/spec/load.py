from pathlib import Path


def kinds(path="spec/kinds.map"):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        name, backing = line.split(None, 1)
        out[name] = backing
    return out


def load_field(path="spec/typespec.toml"):
    section = None
    fields = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            fields[section] = {}
            continue
        key, val = line.split("=", 1)
        fields[section][key.strip()] = val.strip().strip('"')
    catalog = kinds()
    kind = fields["sample_stride"]["kind"]
    if kind not in catalog:
        raise SystemExit("unknown kind")
    return fields["sample_stride"]
