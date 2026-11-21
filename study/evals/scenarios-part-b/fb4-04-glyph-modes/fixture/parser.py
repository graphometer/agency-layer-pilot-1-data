from pathlib import Path


def parse_ini(path):
    out = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line[0] in "#":
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def accepted_pairs(path="modes.txt"):
    lines = [ln for ln in Path(path).read_text().splitlines() if ln.strip()]
    header = lines[0].split()
    rows = []
    for line in lines[1:]:
        rows.append(dict(zip(header, line.split())))
    return rows


def load(path="parser.ini"):
    cfg = parse_ini(path)
    pair = {"glyph_strict": cfg["glyph_strict"], "glyph_lenient": cfg["glyph_lenient"]}
    if pair not in accepted_pairs():
        raise SystemExit("pair not in modes.txt")
    return cfg
