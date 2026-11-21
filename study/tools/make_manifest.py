#!/usr/bin/env python3
"""SHA-256 manifest of the package (FREEZE_CHECKLIST section F).

Hashes every git-tracked file at HEAD-state on disk, in sorted path order, and prints the
digest of the manifest itself — the single value FROZEN.md records. Deterministic: same tree,
same manifest, same digest.

Usage:
    python3 tools/make_manifest.py                 # digest to stdout, manifest not written
    python3 tools/make_manifest.py --out MANIFEST.sha256

The manifest is committed once, at the freeze, by the FROZEN-S1 flow; running the tool at any
other time is a verification, not a release step.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", metavar="F", help="write the manifest lines to F")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="hash a dirty working tree anyway (verification only, never a freeze)")
    args = parser.parse_args()

    # The tool hashes the WORKING TREE. On a dirty tree that seals dirty bytes under a
    # HEAD-shaped name (Grok step-7 review), so a freeze run refuses unless told otherwise.
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, check=True).stdout.strip()
    if dirty and not args.allow_dirty:
        print("refusing: the working tree is dirty — commit first, or pass --allow-dirty "
              "for a non-freeze verification run", file=sys.stderr)
        return 1

    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                           check=True).stdout.splitlines()
    lines = []
    for name in sorted(files):
        p = Path(name)
        if not p.is_file():  # a tracked path deleted in the working tree would silently
            print(f"refusing: tracked file missing from the working tree: {name}",
                  file=sys.stderr)
            return 1
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    manifest = "\n".join(lines) + "\n"
    manifest_digest = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
    if args.out:
        Path(args.out).write_text(manifest, encoding="utf-8")
        print(f"wrote {args.out} ({len(lines)} files)")
    print(f"manifest sha256: {manifest_digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
