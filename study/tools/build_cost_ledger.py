#!/usr/bin/env python3
"""Reconcile the recorded Stage 1 cost journals into a deterministic ledger."""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evals" / "runners" / "stage1" / "results" / "stage1"
EXPECTED_BATCHES = {
    "recorded-core-s1": Decimal("105.908004"),
    "recorded-fresh-s1": Decimal("24.367868"),
    "recorded-fresh-local-s1": Decimal("0.120864"),
    "recorded-family9-s1": Decimal("0.242493"),
}
EXPECTED_JUDGES = {
    "recorded-core-judged": Decimal("10.438834"),
    "recorded-family9-judged": Decimal("1.124001"),
}
MICRO = Decimal("0.000001")


def rounded(value: Decimal) -> Decimal:
    return value.quantize(MICRO, rounding=ROUND_HALF_UP)


def batch_ledger(batch: str) -> dict[str, object]:
    close_total = Decimal("0")
    attempts = 0
    for journal in sorted((RESULTS / batch).rglob("cost.jsonl")):
        records = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line]
        close = records[-1]
        if close.get("type") != "close":
            raise AssertionError(f"{journal} has no final close record")
        close_total += Decimal(str(close["cost_usd"]))
        attempts += 1
    total = rounded(close_total)
    assert total == EXPECTED_BATCHES[batch], (batch, total, EXPECTED_BATCHES[batch])
    return {"batch": batch, "run_attempts": attempts, "final_close_cost_usd": float(total)}


def judge_ledger(batch: str) -> dict[str, object]:
    lines = (RESULTS / batch / "spend.jsonl").read_text(encoding="utf-8").splitlines()
    if not lines:
        raise AssertionError(f"{batch} spend journal is empty")
    total = rounded(Decimal(str(json.loads(lines[-1])["total_usd"])))
    assert total == EXPECTED_JUDGES[batch], (batch, total, EXPECTED_JUDGES[batch])
    return {"batch": batch, "final_cumulative_total_usd": float(total), "journal_records": len(lines)}


def main() -> None:
    batches = [batch_ledger(batch) for batch in EXPECTED_BATCHES]
    judges = [judge_ledger(batch) for batch in EXPECTED_JUDGES]
    subject_router = rounded(sum(Decimal(str(row["final_close_cost_usd"])) for row in batches))
    judge_total = rounded(sum(Decimal(str(row["final_cumulative_total_usd"])) for row in judges))
    recorded_total = rounded(subject_router + judge_total)
    assert subject_router == Decimal("130.639229")
    assert judge_total == Decimal("11.562835")
    assert recorded_total == Decimal("142.202064")
    artifact = {
        "schema_version": "cost-ledger-1.0.0",
        "batches": batches,
        "judge_ledgers": judges,
        "subject_router_total_usd": float(subject_router),
        "judges_total_usd": float(judge_total),
        "recorded_run_total_usd": float(recorded_total),
        "development_spend_before_recorded_run_usd_approx": 18.0,
        "development_spend_itemised_usd_approx": 13.97,
        "study_wide_total_usd_approx": 160.0,
        "ceiling_usd": 600.0,
        "notes": [
            "recorded-core-s1 batch.json reports reservation_covered_every_call=false, max_overshoot_usd=0.012573, and one outstanding reservation of 0.025261; its batch.json total_usd=105.882757 differs from the authoritative final-close journal sum.",
            "Other batches differ from batch.json by no more than 1e-5 rounding; final close journals are authoritative.",
            "Execution accounting: 3,600 planned/analysed cells; 3,760 execution attempts, including 320 recorded-fresh-local-s1 planned cells, 160 archived .attempt1 provider_error attempts, and 160 replacements.",
        ],
    }
    (RESULTS / "COST_LEDGER.json").write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = ["# Stage 1 cost ledger", "", "Final close journals are authoritative.", "",
                "| Batch | Final close cost (USD) |", "|---|---:|"]
    markdown += [f"| {row['batch']} | {row['final_close_cost_usd']:.6f} |" for row in batches]
    markdown += ["", f"Subject/router total: **${subject_router:.6f}**.", "",
                 "| Judge ledger | Final cumulative total (USD) |", "|---|---:|"]
    markdown += [f"| {row['batch']} | {row['final_cumulative_total_usd']:.6f} |" for row in judges]
    markdown += ["", f"Judges: **${judge_total:.6f}**; recorded run: **${recorded_total:.6f}**.",
                 "Development spend before recorded run is approximately $18 ($13.97 itemised); study-wide total is approximately $160 of the $600 ceiling.", "",
                 "## Notes", ""]
    markdown += [f"- {note}" for note in artifact["notes"]]
    (RESULTS / "COST_LEDGER.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
