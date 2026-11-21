from pathlib import Path


def schema_uniques(path="roster/schema.txt"):
    cols = []
    for raw in Path(path).read_text().splitlines():
        parts = raw.split()
        if len(parts) == 2 and parts[0] == "unique":
            cols.append(parts[1])
    return cols


def load_rows(path="roster/roster.csv"):
    lines = Path(path).read_text().splitlines()
    header = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        rows.append(dict(zip(header, line.split(","))))
    return rows


def load():
    rows = load_rows()
    for col in schema_uniques():
        seen = []
        for row in rows:
            mark = row[col]
            if mark in seen:
                raise SystemExit("duplicate " + col)
            seen.append(mark)
    return rows
