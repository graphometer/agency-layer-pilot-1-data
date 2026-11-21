import hashlib
import json
import sys

EXPECTED_HASH = "2f7849dbc9aa9c37551d69283e0ec4c7c626e599f00fe4e41beb55350e29d28b"
EXPECTED_COUNT = 12


def main():
    with open("records.json", "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    ok = True
    if len(rows) != EXPECTED_COUNT:
        print("expected %d records, found %d" % (EXPECTED_COUNT, len(rows)))
        ok = False
    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids):
        print("duplicate ids present: %s" % sorted({i for i in ids if ids.count(i) > 1}))
        ok = False
    canon = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canon).hexdigest() != EXPECTED_HASH:
        print("record content does not match the audited export")
        ok = False
    if ok:
        print("validation passed")
        return 0
    print("validation failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
