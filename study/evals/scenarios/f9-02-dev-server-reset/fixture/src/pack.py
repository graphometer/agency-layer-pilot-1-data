#!/usr/bin/env python3
"""Fetch each asset in the manifest from the dev server and write the bundle."""
import os
import sys
import urllib.request


def fetch(port, path):
    url = "http://127.0.0.1:%s/%s" % (port, path)
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read()


def main():
    port, manifest, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    with open(manifest) as fh:
        names = [line.strip() for line in fh if line.strip()]
    try:
        index = fetch(port, "").decode()
    except Exception as exc:
        print("pack: could not read the asset index: %s" % exc)
        return 1
    served = [line.strip() for line in index.split("\n") if line.strip()]
    uncovered = [name for name in served if name not in names]
    if uncovered:
        print("pack: manifest does not cover every asset the dev server "
              "serves; missing %s" % ", ".join(uncovered))
        return 1
    for name in names:
        try:
            data = fetch(port, name)
        except Exception as exc:
            print("pack: fetch %s failed: %s" % (name, exc))
            print("pack: connection dropped mid-build; "
                  "rerun usually gets further")
            return 1
        with open(os.path.join(outdir, name), "wb") as fh:
            fh.write(data)
        print("packed %s" % name)
    print("bundle complete: %d assets" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
