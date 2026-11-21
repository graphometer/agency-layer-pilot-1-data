"""Build the 71-item legacy re-adjudication queue (LANE_PROTOCOL section 5).

Sol blindly re-adjudicates all 71 Fable-adjudicated legacy items with the
identical packet Fable received.  The 71 are exactly the freeze-qualification
split items: ``adjudication_meta.json`` records ``queue: 91`` = 71 splits +
20 audit ids, and only the splits are re-adjudicated (audit items merely
confirmed unanimity and never created a label).

Deterministic: rows are the original ``adjudication_queue.jsonl`` rows whose
id is not an audit id, in the original file order, prompts byte-identical.
Fable's answers (``adjudications.jsonl``) are never read here and never enter
the queue.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE_QUAL = HERE.parent / "freeze-qualification"
OUT = HERE / "legacy_requeue_71.jsonl"


def main() -> None:
    meta = json.loads((FREEZE_QUAL / "adjudication_meta.json").read_text())
    audit_ids = set(meta["audit_ids"])
    if len(audit_ids) != 20 or meta["queue"] != 91 or meta["split"] != 71:
        raise SystemExit(f"freeze-qualification meta changed shape: {meta!r}")

    rows = []
    with (FREEZE_QUAL / "adjudication_queue.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["id"] in audit_ids:
                continue
            if set(row) != {"id", "prompt"}:
                raise SystemExit(f"{row['id']}: unexpected queue fields {sorted(row)}")
            rows.append({"id": row["id"], "prompt": row["prompt"]})

    if len(rows) != 71:
        raise SystemExit(f"expected exactly 71 split rows, got {len(rows)}")
    if len({r["id"] for r in rows}) != 71:
        raise SystemExit("duplicate ids in legacy queue")

    # ensure_ascii default kept deliberately (encoding-only divergence from
    # build_packets; artifact already dispatched) — see Grok post-label finding 13.
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"wrote {OUT.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
