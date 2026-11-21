"""Sol–Fable concordance on the 71 legacy split adjudications (LANE_PROTOCOL section 5).

A concordance study, not gold: fresh lane labels stand on their own, and the predeclared
instability flag — **more than 14 of 71 flipped** — is a flag for the closing ruling, never an
automatic branch kill.  Strict direction (matching the frozen convention and README ratification
(d)): a Sol ``cannot_determine`` on an item Fable labelled binary counts as a flip.

Inputs: ``legacy_requeue_71.jsonl`` (identical packets Fable received), Sol's answers from the
committed ``sol_answers/`` copy, Fable's original ``adjudications.jsonl``.  Output:
``CONCORDANCE_71.json``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE_QUAL = HERE.parent / "freeze-qualification"
# Sol's answer file is committed beside this script under ``sol_answers/`` (a byte-identical copy
# of the adjudication run's output), so the table regenerates from a clean clone with no absolute
# path.  That committed copy is the ONLY source: there is deliberately no fallback to the staging
# directory that produced it, because a fallback would keep this script working on the one machine
# that holds that directory and so hide a missing or wrong committed copy.
EXPECTED_N = 71
FLIP_FLAG_THRESHOLD = 14


def sol_answer(name: str) -> Path:
    """The committed copy of one Sol answer file under ``sol_answers/``; absence refuses."""
    path = HERE / "sol_answers" / name
    if not path.exists():
        raise SystemExit(
            f"missing committed Sol answer file: {path}. The concordance table regenerates only "
            "from the copy committed under sol_answers/; there is no staging fallback. Restore "
            "the file (its sha256 is recorded in CONCORDANCE_71.json) and re-run."
        )
    return path


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    queue_ids = [row["id"] for row in read_jsonl(HERE / "legacy_requeue_71.jsonl")]
    if len(queue_ids) != EXPECTED_N or len(set(queue_ids)) != EXPECTED_N:
        raise SystemExit("legacy queue changed shape")

    fable: dict[str, str] = {}
    for row in read_jsonl(FREEZE_QUAL / "adjudications.jsonl"):
        if row["id"] in fable:
            raise SystemExit(f"duplicate Fable adjudication for {row['id']}")
        fable[row["id"]] = str(row["label"]).strip()
    missing_fable = sorted(set(queue_ids) - set(fable))
    if missing_fable:
        raise SystemExit(f"queue ids missing from Fable adjudications: {missing_fable[:5]}")
    sol_rows = read_jsonl(sol_answer("sol_legacy_71.jsonl"))
    sol = {}
    for row in sol_rows:
        rid = str(row["id"]).strip()
        if rid in sol:
            raise SystemExit(f"duplicate Sol answer for {rid}")
        sol[rid] = str(row["answer"]).strip()
    if set(sol) != set(queue_ids):
        raise SystemExit(
            f"Sol answers do not cover the queue exactly: {len(sol)} answers, "
            f"missing {sorted(set(queue_ids) - set(sol))[:5]}"
        )

    lane_legacy = {
        row.get("legacy_id")
        for row in read_jsonl(HERE / "goldset_lane.jsonl")
        if row.get("legacy_id")
    }

    flips = []
    for item_id in queue_ids:
        if sol[item_id] != fable[item_id]:
            flips.append(
                {
                    "id": item_id,
                    "fable": fable[item_id],
                    "sol": sol[item_id],
                    "in_lane_gold": item_id in lane_legacy,
                }
            )

    result = {
        "n": EXPECTED_N,
        "agreements": EXPECTED_N - len(flips),
        "flips": len(flips),
        "flip_detail": flips,
        "sol_abstentions": sum(1 for f in flips if f["sol"] == "cannot_determine"),
        "instability_flag_raised": len(flips) > FLIP_FLAG_THRESHOLD,
        "flag_rule": "more than 14 of 71 flipped (abstentions count as flips, strict direction)",
        "in_lane": sum(1 for i in queue_ids if i in lane_legacy),
        "not_in_lane": sorted(i for i in queue_ids if i not in lane_legacy),
        "inputs_sha256": {
            "legacy_requeue_71.jsonl": hashlib.sha256(
                (HERE / "legacy_requeue_71.jsonl").read_bytes()
            ).hexdigest(),
            "sol_legacy_71.jsonl": hashlib.sha256(
                sol_answer("sol_legacy_71.jsonl").read_bytes()
            ).hexdigest(),
            "adjudications.jsonl": hashlib.sha256(
                (FREEZE_QUAL / "adjudications.jsonl").read_bytes()
            ).hexdigest(),
        },
    }
    (HERE / "CONCORDANCE_71.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(
        f"concordance: {result['agreements']}/{EXPECTED_N} agree, {result['flips']} flips "
        f"({result['sol_abstentions']} abstentions) — flag "
        f"{'RAISED' if result['instability_flag_raised'] else 'not raised'}"
    )


if __name__ == "__main__":
    main()
