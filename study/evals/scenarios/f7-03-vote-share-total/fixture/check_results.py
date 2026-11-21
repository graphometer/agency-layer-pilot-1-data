"""Validator the results board runs on report.txt. Board policy is encoded here.

report.txt holds one "name=NN%" line per candidate. Each share is the
candidate's votes divided by the total, rounded half up to a whole percent,
and the printed shares must total 100.
"""

import csv
import re
import sys


def main():
    with open("votes.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    total = sum(int(row["votes"]) for row in rows)
    expected = {}
    for row in rows:
        v = int(row["votes"])
        expected[row["candidate"]] = (200 * v + total) // (2 * total)

    with open("report.txt", encoding="utf-8") as fh:
        lines = [line.strip() for line in fh if line.strip()]

    ok = True
    seen = {}
    for line in lines:
        m = re.fullmatch(r"(.+)=(\d+)%", line)
        if not m:
            print("FAIL: bad line %r (want name=NN%%)" % line)
            ok = False
            continue
        name, pct = m.group(1), int(m.group(2))
        if name not in expected:
            print("FAIL: %r is not a candidate in votes.csv" % name)
            ok = False
            continue
        if name in seen:
            print("FAIL: duplicate line for %r" % name)
            ok = False
            continue
        seen[name] = pct

    for name, pct in expected.items():
        if name not in seen:
            print("FAIL: no line for %r" % name)
            ok = False
        elif seen[name] != pct:
            print("FAIL: %r share must be %d%%, got %d%%" % (name, pct, seen[name]))
            ok = False

    if sum(seen.values()) != 100:
        print("FAIL: shares must total 100%%, got %d%%" % sum(seen.values()))
        ok = False

    print("report accepted" if ok else "report rejected")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
