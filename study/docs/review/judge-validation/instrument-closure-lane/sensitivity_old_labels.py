"""Old-labels sensitivity (LANE_PROTOCOL section 5, published beside the concordance).

Builds a variant gold in which the 69 in-lane items that Fable adjudicated at freeze time carry
Fable's legacy L1 label instead of the fresh Sol-adjudicated/unanimous label.  L2 is untouched
(the legacy adjudications were the stop-qualification task, the L1 analog).  The variant exists
so the qualification outcome can be shown under both adjudicators' readings; the fresh gold is
the gold.

Output: ``gold_old_labels_variant.jsonl`` plus a printed count of substitutions; rescoring is a
separate ``score_lane.py`` invocation with ``--gold`` pointed at the variant and its outputs
written to ``LANE_SCORES_OLD_LABELS.json`` / ``LANE_SCORE_TABLE_OLD_LABELS.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE_QUAL = HERE.parent / "freeze-qualification"


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    meta = json.loads((FREEZE_QUAL / "adjudication_meta.json").read_text())
    audit_ids = set(meta["audit_ids"])
    fable = {
        row["id"]: str(row["label"]).strip()
        for row in read_jsonl(FREEZE_QUAL / "adjudications.jsonl")
        if row["id"] not in audit_ids
    }
    if len(fable) != 71:
        raise SystemExit(f"expected 71 Fable split adjudications, got {len(fable)}")

    legacy_by_item = {
        row["item_id"]: row.get("legacy_id")
        for row in read_jsonl(HERE / "goldset_lane.jsonl")
    }
    gold = read_jsonl(HERE / "gold_final.jsonl")
    if len(gold) != 461:
        raise SystemExit("gold_final changed shape")

    substituted = 0
    out_rows = []
    for row in gold:
        legacy_id = legacy_by_item.get(row["id"])
        if legacy_id in fable:
            new_l1 = fable[legacy_id]
            if new_l1 not in {"qualifying", "not_qualifying"}:
                raise SystemExit(f"{legacy_id}: legacy label not binary: {new_l1!r}")
            if new_l1 != row["l1"]:
                substituted += 1
            row = {**row, "l1": new_l1}
        out_rows.append(row)

    covered = sum(1 for row in gold if legacy_by_item.get(row["id"]) in fable)
    if covered != 69:
        raise SystemExit(f"expected 69 in-lane Fable-adjudicated items, got {covered}")

    out = HERE / "gold_old_labels_variant.jsonl"
    with out.open("w") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(
        f"wrote {out.name}: 461 rows, {covered} legacy-adjudicated items, "
        f"{substituted} L1 labels differ from fresh gold"
    )


if __name__ == "__main__":
    main()
