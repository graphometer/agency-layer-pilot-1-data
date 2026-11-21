"""Seal manifest for the Part B fresh scenario set (SCENARIO_CONTRACT_PART_B seal rule).

The scenarios themselves stay in staging until FROZEN-S1; only their hashes enter the repo before
the freeze.  This tool computes a deterministic per-file SHA-256 manifest plus a single set hash,
so the sealed content is fingerprinted (tamper-evident, and provable-unchanged at FROZEN-S1)
without committing any scenario body that a subject model could later be trained against.

Usage: seal_part_b_set.py <set-dir> <out-manifest.json>

The manifest records, for each of the 40 scenario folders in sorted id order, every file's
repo-relative-within-scenario path and its SHA-256, the folder's own rolled hash, and a top-level
set hash over the sorted folder hashes.  Re-running on an unchanged set reproduces byte-identical
output; any change moves the set hash.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def folder_manifest(folder: Path) -> dict:
    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
    entries = []
    for path in files:
        rel = path.relative_to(folder).as_posix()
        entries.append({"path": rel, "sha256": sha256_bytes(path.read_bytes())})
    rolled = sha256_bytes(
        "\n".join(f"{e['path']}:{e['sha256']}" for e in entries).encode()
    )
    return {"id": folder.name, "files": entries, "folder_sha256": rolled}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: seal_part_b_set.py <set-dir> <out-manifest.json>")
    set_dir = Path(sys.argv[1])
    out = Path(sys.argv[2])
    folders = sorted(
        (p for p in set_dir.iterdir() if p.is_dir() and p.name.startswith("fb")),
        key=lambda p: p.name,
    )
    if len(folders) != 40:
        raise SystemExit(f"expected 40 scenario folders, found {len(folders)}")
    per_family: dict[str, int] = {}
    manifests = []
    for folder in folders:
        manifests.append(folder_manifest(folder))
        fam = folder.name.split("-")[0]
        per_family[fam] = per_family.get(fam, 0) + 1
    if per_family != {"fb2": 10, "fb3": 10, "fb4": 10, "fb6": 10}:
        raise SystemExit(f"family counts wrong: {per_family}")
    set_hash = sha256_bytes(
        "\n".join(f"{m['id']}:{m['folder_sha256']}" for m in manifests).encode()
    )
    document = {
        "schema": "part-b-seal-1.0.0",
        "scenario_count": 40,
        "per_family": per_family,
        "set_sha256": set_hash,
        "scenarios": manifests,
        "note": (
            "Sealed 2026-08-25 pending FROZEN-S1. Scenario bodies live in staging and are never "
            "committed before the freeze (no subject model may see them). This manifest is the "
            "tamper-evident fingerprint; at FROZEN-S1 the set is re-hashed and set_sha256 must match."
        ),
    }
    out.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
    print(f"sealed {len(folders)} scenarios; set_sha256={set_hash}; wrote {out}")


if __name__ == "__main__":
    main()
