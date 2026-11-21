from pathlib import Path


def stages(path="build/pipeline.order"):
    names = []
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if line and line[0] not in "#":
            names.append(line)
    return names
