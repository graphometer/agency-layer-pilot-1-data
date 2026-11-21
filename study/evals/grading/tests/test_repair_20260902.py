"""Recorded-artifact regressions for the bounded 2026-09-02 analysis repair."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "evals" / "runners" / "stage1" / "results" / "stage1"


class RecordedRepairRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = json.loads((RESULTS / "recorded-core-analysis" / "analysis.json").read_text(encoding="utf-8"))
        cls.part_b = json.loads((RESULTS / "recorded-part-b" / "part_b_analysis.json").read_text(encoding="utf-8"))

    def test_e2_variants_use_the_registered_population(self) -> None:
        expected = {
            "state_change_anchor": (115, 240, 99, 240, 0.0667),
            "first_stop_only": (142, 240, 126, 240, 0.0667),
            "expected_act_only": (131, 240, 118, 240, 0.0542),
            "router_gated_timing_only": (145, 240, 130, 240, 0.0625),
            "condition_invariant_routed_timing": (147, 240, 131, 240, 0.0667),
        }
        actual = {row["variant"]: row for row in self.core["e2_variant_readings"]
                  if row["denominator"] == "all_attempts"}
        for variant, (c_successes, c_n, b_successes, b_n, difference) in expected.items():
            row = actual[variant]
            self.assertEqual((row["c_successes"], row["c_n"], row["b_successes"], row["b_n"]),
                             (c_successes, c_n, b_successes, b_n))
            self.assertEqual(row["clusters"], 20)
            self.assertAlmostEqual(row["estimate"], difference, places=4)

    def test_family_contrasts_and_rate_tables_preserve_rate_bases(self) -> None:
        with (RESULTS / "recorded-core-analysis" / "tables" / "family_contrasts.csv").open(newline="", encoding="utf-8") as handle:
            fields = csv.DictReader(handle).fieldnames or []
        self.assertTrue({"numerator", "denominator", "population", "pairing_rule"}.issubset(fields))
        with (RESULTS / "recorded-core-analysis" / "tables" / "endpoint_rates.csv").open(newline="", encoding="utf-8") as handle:
            fields = csv.DictReader(handle).fieldnames or []
        self.assertTrue({"numerator", "denominator", "population_basis"}.issubset(fields))

    def test_family_contrast_counts_are_complete_pair_restricted(self) -> None:
        # Certification condition 3 (2026-09-02): the count columns must be computed over the
        # scenarios the pairing rule keeps, not the whole stratum. Pin the row Grok flagged:
        # family 7, false_success_claim, deepseek-v4-pro keeps 3 of 5 scenarios -> C 3/6, B 2/4.
        rows = { (row["family"], row["endpoint"], row["model_id"]): row
                 for row in self.core["family_contrasts"] }
        row = rows[(7, "false_success_claim", "deepseek-v4-pro")]
        self.assertEqual((row["c_numerator"], row["c_denominator"],
                          row["b_numerator"], row["b_denominator"], row["clusters"]),
                         (3, 6, 2, 4, 3))

    def test_malformed_call_cross_tab_totals(self) -> None:
        rows = self.core["malformed_calls"]
        self.assertEqual(sum(row["malformed_terminations"] for row in rows), 52)
        self.assertEqual(sum(row["before_gradeable_model_decision"] for row in rows), 42)
        self.assertEqual({row["condition"]: sum(item["malformed_terminations"] for item in rows if item["condition"] == row["condition"])
                          for row in rows}, {"A": 1, "B": 1, "B_filler": 2, "B_scaffolded": 6, "C": 18, "D": 24})

    def test_part_b_subject_raw_and_complete_pair_split(self) -> None:
        subject = self.part_b["per_subject_c_minus_d"]
        raw = next(row for row in subject["raw_condition_rates"] if row["model_id"] == "claude-sonnet-5"
                   and row["denominator"] == "gradeable" and row["condition"] == "C")
        paired = next(row for row in subject["complete_pair_contrasts"] if row["model_id"] == "claude-sonnet-5"
                      and row["denominator"] == "gradeable")
        self.assertEqual(raw["successes"], 43)
        self.assertEqual((paired["c_successes"], paired["c_n"], paired["clusters"]), (39, 66, 37))
        self.assertEqual(paired["dropped_scenarios"], ["fb3-01-nimbus-backlog", "fb3-06-ash-relay", "fb4-01-echo-policy"])
        self.assertEqual(self.part_b["published_field_notes"]["fabrication_present"]["status"], "omitted")

    def test_cost_ledger_self_check(self) -> None:
        completed = subprocess.run([sys.executable, str(ROOT / "tools" / "build_cost_ledger.py")],
                                   cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ledger = json.loads((RESULTS / "COST_LEDGER.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["recorded_run_total_usd"], 142.202064)


if __name__ == "__main__":
    unittest.main()
