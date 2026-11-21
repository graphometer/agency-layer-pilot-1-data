"""Build the L2 escalation queue after the section 5 audit gate failed for L2.

LANE_PROTOCOL section 5: "if the adjudicator disagrees with more than 1 of the 20 in a track,
unanimous auto-accept is suspended for that track and every unanimous item in it is adjudicated."
The realized L2 audit had 3/20 disagreements (recorded in GOLD_FREEZE.json at finalize time), so
all 413 unanimous L2 items are adjudicated.  The 20 audit items were already adjudicated in the
track's own packet form and their answers stand; this queue is the remaining 393, presented in the
same plain L2 packet form (no votes — matching the audit presentation; showing the failed
unanimity would anchor the adjudicator toward it).

Deterministic: rows come from ``packets/l2_packets.jsonl`` in file order, restricted to request
ids that are neither L2 splits nor L2 audit items.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "escalation_queue_l2.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    split_rids = {str(r["request_id"]) for r in read_jsonl(HERE / "adjudication_queue_l2.jsonl")}
    audit_rids = {str(r["request_id"]) for r in read_jsonl(HERE / "audit_queue_l2.jsonl")}
    if len(split_rids) != 48 or len(audit_rids) != 20 or split_rids & audit_rids:
        raise SystemExit("queue shapes changed; refusing")

    packets = read_jsonl(HERE / "packets" / "l2_packets.jsonl")
    if len(packets) != 461:
        raise SystemExit(f"expected 461 l2 packets, got {len(packets)}")

    rows = []
    for row in packets:
        rid = str(row["request_id"])
        if rid in split_rids or rid in audit_rids:
            continue
        rows.append({"request_id": rid, "prompt": row["prompt"]})

    if len(rows) != 461 - 48 - 20:
        raise SystemExit(f"expected {461 - 48 - 20} escalation rows, got {len(rows)}")
    # json.dumps defaults to ensure_ascii=True, unlike build_packets: non-ASCII in
    # prompts is escaped (—), an encoding difference only — json.loads yields the
    # identical prompt string. Kept as-is because the artifact was already dispatched
    # to the adjudicator; byte stability of a dispatched queue wins (Grok finding 13).
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"wrote {OUT.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
