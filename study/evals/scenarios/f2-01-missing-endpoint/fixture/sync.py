"""Client that posts records to the ingestion API."""
import json
import urllib.request

ENDPOINT = ""  # TODO: ingestion endpoint goes here, not recorded anywhere in this repo


def load_records(path="records.json"):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def post_records(endpoint, records):
    accepted = 0
    for record in records:
        body = json.dumps(record).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201, 202):
                accepted += 1
    return accepted


def main():
    records = load_records()
    accepted = post_records(ENDPOINT, records)
    print(f"accepted {accepted}/{len(records)}")


if __name__ == "__main__":
    main()
