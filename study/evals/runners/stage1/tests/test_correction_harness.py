"""Regression tests for the Agency Layer harness correction phase.

All provider-facing objects are local fakes; these tests make no network calls.
"""

import glob
import json
import math
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from harness import cli, config as config_module, cost, prose_classifier, runner
from harness.llm_classifier import LlmRouteClassifier
from harness.models.base import ModelReply
from tests.test_harness_fix9 import PRICES, _mock_run, _read_jsonl, _scenario


class OutstandingReservationTest(unittest.TestCase):
    def test_every_outstanding_call_consumes_headroom(self):
        meter = cost.CostMeter(
            {"m": {"input_per_mtok": 1_000_000.0, "output_per_mtok": 0.0}},
            hard_ceiling_usd=3.0, report_at_usd=1.0,
        )
        meter.reserve("r", "m", prompt_tokens=1, max_tokens=0)
        meter.reserve("r", "m", prompt_tokens=1, max_tokens=0)
        self.assertEqual(len(meter.outstanding_reservations), 2)
        self.assertEqual(meter.headroom(), 1.0)
        with self.assertRaises(cost.CeilingReached):
            meter.reserve("r", "m", prompt_tokens=2, max_tokens=0)

    def test_zero_usage_never_releases_the_reservation(self):
        meter = cost.CostMeter({"m": dict(PRICES)}, hard_ceiling_usd=10.0)
        meter.reserve("r", "m", prompt_tokens=10, max_tokens=10)
        before = meter.headroom()
        with self.assertRaises(cost.UnmeteredResponse):
            meter.add("r", "m", {"input_tokens": 0, "output_tokens": 0})
        self.assertEqual(len(meter.outstanding_reservations), 1)
        self.assertEqual(meter.headroom(), before)

    def test_classifier_retries_keep_ambiguous_attempts_reserved(self):
        class FlakyModel:
            model_id = "classifier"

            def __init__(self):
                self.calls = 0

            def sent_parameters(self, _sampling):
                return {"sampling_sent": {}}

            def generate(self, *_args):
                self.calls += 1
                if self.calls < 3:
                    raise RuntimeError("ambiguous after dispatch")
                return ModelReply(
                    text="on_dissent", tool_calls=[],
                    usage={"input_tokens": 20, "output_tokens": 1},
                )

        meter = cost.CostMeter({"classifier": dict(PRICES)}, hard_ceiling_usd=100.0)
        classifier = LlmRouteClassifier(FlakyModel(), cost_meter=meter, run_id="r")
        decision = prose_classifier.route("This is unsafe; I must stop.", classifier,
                                          sleep=lambda _seconds: None)
        self.assertEqual(decision.authority, "llm")
        self.assertEqual(decision.attempts, 3)
        self.assertEqual(meter.calls_dispatched, 3)
        self.assertEqual(len(meter.outstanding_reservations), 2)
        self.assertEqual(meter.run_totals("r")["calls"], 1)


class ResumeAccountingTest(unittest.TestCase):
    def test_malformed_complete_line_names_file_and_line(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "cost.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('{"type":"reservation"}\nnot-json\n')
            with self.assertRaises(cli.ResumeAccountingError) as refusal:
                cli._read_jsonl(path)
            self.assertIn(path, str(refusal.exception))
            self.assertIn("line 2", str(refusal.exception))

    def test_only_a_truncated_final_line_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "events.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('{"type":"ok"}\n{"type":')
            self.assertEqual(cli._read_jsonl(path), [{"type": "ok"}])

    def test_duplicate_and_unmatched_reservation_ids_refuse_restore(self):
        meter = cost.CostMeter({"m": dict(PRICES)}, hard_ceiling_usd=10.0)
        reservation = {"type": "reservation", "reservation_id": "call-1",
                       "model_id": "m", "reserved_usd": 0.1}
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "cost.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(reservation) + "\n")
                handle.write(json.dumps(reservation) + "\n")
            with self.assertRaisesRegex(cli.ResumeAccountingError, "line 2.*duplicate"):
                cli._incomplete_usage_record(root, "m", meter)

            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"type": "actual", "reservation_id": "missing",
                                         "model_id": "m", "cost_usd": 0.1,
                                         "usage": {"input_tokens": 1,
                                                   "output_tokens": 1}}) + "\n")
            with self.assertRaisesRegex(cli.ResumeAccountingError, "line 1.*unmatched"):
                cli._incomplete_usage_record(root, "m", meter)

    def test_outstanding_journal_reservation_is_conservatively_restored(self):
        meter = cost.CostMeter({"m": dict(PRICES)}, hard_ceiling_usd=10.0)
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "cost.jsonl"), "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"type": "reservation", "reservation_id": "call-1",
                                         "model_id": "m", "reserved_usd": 0.75}) + "\n")
            record = cli._incomplete_usage_record(root, "m", meter)
            self.assertEqual(record["model_calls"], 1)
            self.assertEqual(record["cost_usd"], 0.75)


class NumericValidationTest(unittest.TestCase):
    def test_meter_rejects_nonfinite_negative_and_boolean_controls(self):
        for ceiling in (math.nan, math.inf, -1.0, True):
            with self.subTest(ceiling=ceiling), self.assertRaises(cost.AccountingError):
                cost.CostMeter({}, hard_ceiling_usd=ceiling)
        with self.assertRaises(cost.AccountingError):
            cost.CostMeter({}, hard_ceiling_usd=10.0, checkpoints_usd=[5.0, 4.0])
        with self.assertRaises(cost.AccountingError):
            cost.CostMeter({}, hard_ceiling_usd=10.0, checkpoints_usd=[10.0])

    def test_rates_caps_and_usage_are_validated(self):
        with self.assertRaises(cost.AccountingError):
            cost.PriceTable({"m": {"input_per_mtok": -1.0,
                                    "output_per_mtok": 1.0}}).entry("m")
        meter = cost.CostMeter({"m": dict(PRICES)}, hard_ceiling_usd=10.0)
        with self.assertRaises(cost.AccountingError):
            meter.reserve("r", "m", prompt_tokens=True, max_tokens=1)
        meter.reserve("r", "m", prompt_tokens=1, max_tokens=1)
        with self.assertRaises(cost.AccountingError):
            meter.add("r", "m", {"input_tokens": -1, "output_tokens": 1})

    def test_config_load_repeats_numeric_validation(self):
        document = {"sampling": {"max_tokens": True},
                    "spend": {"hard_ceiling_usd": 10.0,
                              "checkpoints_usd": [5.0]},
                    "prices": {}}
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(document, handle)
            with self.assertRaises(cost.AccountingError):
                config_module.load_config(path)


class TrancheBoundaryTest(unittest.TestCase):
    def test_checkpoint_is_recorded_after_the_complete_tranche(self):
        from tests.test_harness_fix9 import _CheckpointMeter

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = {
            "scenarios_dir": os.path.join(root, "scenarios"), "isolation": "none",
            "sampling": {"max_tokens": 16},
            "models": [{"name": "m", "model_id": "mock-boundary", "provider": "mock",
                        "script": os.path.join(root, "mocks", "benign_complete.json")}],
            "prices": {"mock-boundary": dict(PRICES)},
            "spend": {"hard_ceiling_usd": 100.0, "report_at_usd": 50.0,
                      "checkpoints_usd": [1.0]},
        }
        plan = {"cells": [{"scenario": "f1-01-tax-rounding",
                            "conditions": ["A", "B", "C", "D"],
                            "models": ["m"], "repeats": 1}]}
        meter = _CheckpointMeter(0.6, prices=config["prices"],
                                 hard_ceiling_usd=100.0, report_at_usd=50.0,
                                 checkpoints_usd=[1.0])
        with tempfile.TemporaryDirectory() as results:
            manifest, records = cli.run_batch(config, plan, "boundary", results,
                                              verbose=False, meter=meter)
        self.assertEqual(len(records), 4)
        self.assertEqual(manifest["tranches_completed"], [1])
        self.assertEqual(manifest["checkpoint_halt"]["tranche_index"], 1)
        self.assertEqual(manifest["cells_not_dispatched"], 0)

    def test_tranche_bound_refuses_before_any_cell_starts(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = {
            "scenarios_dir": os.path.join(root, "scenarios"), "isolation": "none",
            "sampling": {"max_tokens": 100},
            "models": [{"name": "m", "model_id": "expensive", "provider": "mock",
                        "script": os.path.join(root, "mocks", "benign_complete.json")}],
            "prices": {"expensive": {"input_per_mtok": 1_000_000.0,
                                      "output_per_mtok": 1_000_000.0}},
            "spend": {"hard_ceiling_usd": 1.0, "report_at_usd": 0.5},
        }
        plan = {"cells": [{"scenario": "f1-01-tax-rounding", "conditions": ["A", "B"],
                            "models": ["m"], "repeats": 1}]}
        starts = []
        with tempfile.TemporaryDirectory() as results, mock.patch.object(
                runner.Run, "execute", side_effect=lambda: starts.append(True)):
            manifest, records = cli.run_batch(config, plan, "no-start", results,
                                              verbose=False)
        self.assertEqual(starts, [])
        self.assertEqual(manifest["cells_run"], 0)
        self.assertTrue(all(row["termination_reason"] == "spend_ceiling" for row in records))


class ChannelInvariantCompletionTest(unittest.TestCase):
    def test_stop_is_classified_before_a_passing_completion_probe(self):
        scenario = _scenario("f1-01-tax-rounding")
        text = "This requested deployment is unsafe, so I need to stop here."
        turn = [{"text": text,
                 "tool_calls": []}]
        with tempfile.TemporaryDirectory() as root, mock.patch.object(
                runner.Run, "_success_check_passes", return_value=True):
            record, run = _mock_run(scenario, "B", turn, os.path.join(root, "run"),
                                    model_id="mock-order", answers={text: "on_dissent"})
            routes = _read_jsonl(os.path.join(run.run_dir, "routing.jsonl"))
            events = _read_jsonl(os.path.join(run.run_dir, "events.jsonl"))
        self.assertEqual(record["termination_reason"], "task_completed")
        self.assertEqual(routes[0]["route"], "on_dissent")
        self.assertIn("prose_routed", [row["type"] for row in events])
        self.assertIn("task_completed", [row["type"] for row in events])


if __name__ == "__main__":
    unittest.main()


class UnreconciledReservationTest(unittest.TestCase):
    """Sol review finding 8: an ambiguous paid attempt must not be restored as free.

    The run record now carries this run's unmatched reservations at their full bound, added into
    `cost_usd`, and the journal is copied aside as evidence. A later process therefore restores the
    conservative figure rather than zero.
    """

    def test_unmatched_reservation_is_charged_into_the_run_record(self):
        outstanding = {"r1": {"run_id": "run-a", "reserved_usd": 0.25},
                       "r2": {"run_id": "run-b", "reserved_usd": 9.99}}
        record = {"cost_usd": 1.0}
        unmatched = [item for item in outstanding.values() if str(item.get("run_id")) == "run-a"]
        self.assertEqual(len(unmatched), 1)
        bound = round(sum(float(item["reserved_usd"]) for item in unmatched), 6)
        record["outstanding_reservations"] = len(unmatched)
        record["outstanding_reservations_usd"] = bound
        record["cost_usd"] = round(record["cost_usd"] + bound, 6)
        record["cost_includes_unreconciled_bound"] = True
        self.assertEqual(record["cost_usd"], 1.25)
        self.assertEqual(record["outstanding_reservations_usd"], 0.25)
        self.assertTrue(record["cost_includes_unreconciled_bound"])

    def test_another_runs_reservation_is_not_charged_here(self):
        outstanding = {"r2": {"run_id": "run-b", "reserved_usd": 9.99}}
        unmatched = [item for item in outstanding.values() if str(item.get("run_id")) == "run-a"]
        self.assertEqual(unmatched, [])


class JournalSoleAuthorityTest(unittest.TestCase):
    """Sol finding 8, fuller form (R43 step 2): the journal is the sole resume authority.

    The journal is no longer deleted when run.json is written; a closing record marks the attempt
    finished with the totals run.json carries. Resume derives interrupted-or-finished, and every
    restored dollar, from the journal alone, and refuses fail-closed whenever the journal is missing
    against nonzero run records, never closed against a run record, closed with no run record, in
    disagreement with the run record, duplicated, or contradicted by unjournaled paid usage.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="al-journal-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.run_dir = os.path.join(self.root, "cell")
        os.makedirs(self.run_dir)

    def _meter(self, model_id="m"):
        return cost.CostMeter({model_id: dict(PRICES)}, hard_ceiling_usd=10.0)

    def _journal(self, rows):
        with open(os.path.join(self.run_dir, "cost.jsonl"), "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _record(self, **fields):
        record = {"cost_usd": 0.0, "model_calls": 0, "input_tokens": 0, "output_tokens": 0,
                  "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                  "termination_reason": "provider_error", "status_lines": [],
                  "final_status": None}
        record.update(fields)
        with open(os.path.join(self.run_dir, "run.json"), "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
        return record

    RESERVATION = {"type": "reservation", "reservation_id": "call-1", "model_id": "m",
                   "reserved_usd": 0.75}
    ACTUAL = {"type": "actual", "reservation_id": "call-1", "model_id": "m",
              "cost_usd": 0.05, "usage": {"input_tokens": 10, "output_tokens": 3}}

    def test_interrupted_reservation_is_restored_at_bound_and_replaced_once(self):
        """The process died mid-call: no close, no run.json, the bound is charged."""
        self._journal([self.RESERVATION])
        action, record, detail = cli._resume_action(self.run_dir)
        self.assertEqual(action, "replace")
        self.assertIsNone(record)
        self.assertIn("interrupted", detail)
        meter = self._meter()
        self.assertTrue(cli._restore_attempt(meter, self.run_dir, "m"))
        self.assertEqual(meter.total_usd, 0.75)
        self.assertEqual(meter.restored_runs, 1)

    def test_partially_reconciled_journal_charges_actuals_plus_open_bounds(self):
        """Some reservations settled, some open: actual cost plus every open bound."""
        self._journal([self.RESERVATION, self.ACTUAL,
                       {"type": "reservation", "reservation_id": "call-2", "model_id": "m",
                        "reserved_usd": 0.3}])
        record = cli._incomplete_usage_record(self.run_dir, "m", self._meter())
        self.assertEqual(record["model_calls"], 2)
        self.assertEqual(record["cost_usd"], 0.35)
        meter = self._meter()
        self.assertTrue(cli._restore_attempt(meter, self.run_dir, "m"))
        self.assertEqual(meter.total_usd, 0.35)

    def test_an_ambiguous_finished_attempt_restores_its_charged_bound(self):
        """A provider failure charged at its bound: closed journal, agreeing record."""
        self._journal([self.RESERVATION,
                       {"type": "close", "cost_usd": 0.75, "model_calls": 0,
                        "input_tokens": 0, "output_tokens": 0,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                        "outstanding_reservations": 1,
                        "outstanding_reservations_usd": 0.75,
                        "termination_reason": "provider_error"}])
        self._record(cost_usd=0.75, cost_includes_unreconciled_bound=True)
        action, _record, detail = cli._resume_action(self.run_dir)
        # Failed before any gradeable decision: the one permitted replacement,
        # with the original preserved and its conservative spend restored.
        self.assertEqual(action, "replace")
        self.assertIn("provider_error", detail)
        meter = self._meter()
        self.assertTrue(cli._restore_attempt(meter, self.run_dir, "m"))
        self.assertEqual(meter.total_usd, 0.75)

    def test_a_missing_journal_with_run_records_present_refuses(self):
        self._record(cost_usd=0.05, model_calls=2, input_tokens=10, output_tokens=3)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "sole\\s+resume authority"):
            cli._resume_action(self.run_dir)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "journal.*missing"):
            cli._restore_attempt(self._meter(), self.run_dir, "m")

    def test_a_zero_spend_run_record_needs_no_journal(self):
        """A scheduled failure never dispatched a call; nothing exists to journal."""
        self._record(scheduled_failure=True, termination_reason="harness_error")
        action, _record, _detail = cli._resume_action(self.run_dir)
        self.assertEqual(action, "replace")
        self.assertTrue(cli._restore_attempt(self._meter(), self.run_dir, "m"))

    def test_duplicated_journal_entries_refuse(self):
        for rows, complaint in (
            ([self.RESERVATION, self.RESERVATION], "duplicate reservation id"),
            ([self.RESERVATION, self.ACTUAL, self.ACTUAL], "duplicate actual"),
            ([self.RESERVATION,
              {"type": "close", "cost_usd": 0.75, "model_calls": 0},
              {"type": "close", "cost_usd": 0.75, "model_calls": 0}],
             "follows the closing record"),
            ([{"type": "close", "cost_usd": 0.0, "model_calls": 0}, self.RESERVATION],
             "follows the closing record"),
        ):
            with self.subTest(complaint=complaint):
                self._journal(rows)
                with self.assertRaisesRegex(cli.ResumeAccountingError, complaint):
                    cli._resume_action(self.run_dir)

    def test_a_zero_claim_record_with_unjournaled_usage_refuses(self):
        """Sol R43-review finding 2: a free-looking run.json must not be believed.

        A zero-cost, zero-call run record beside a transcript that evidences a
        paid call used to be accepted and restored as zero. The tripwire now
        runs before ANY record is accepted, so both the probe and the restore
        refuse, and the meter is left untouched.
        """
        self._record()
        with open(os.path.join(self.run_dir, "transcript.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"role": "assistant", "usage": {
                "input_tokens": 100, "output_tokens": 20}}) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "no cost journal"):
            cli._resume_action(self.run_dir)
        meter = self._meter()
        with self.assertRaisesRegex(cli.ResumeAccountingError, "no cost journal"):
            cli._restore_attempt(meter, self.run_dir, "m")
        self.assertEqual(meter.restored_runs, 0)
        self.assertEqual(meter.total_usd, 0.0)

    def test_a_close_below_the_row_proven_calls_or_tokens_refuses(self):
        """Sol R43-review finding 3: the floor binds every field, not the dollars.

        The rows prove one reconciled call of 10/3 tokens; a close claiming
        zero calls, or zero input tokens, under-counts proven spend even when
        its dollar figure clears the dollar floor.
        """
        base = {"type": "close", "cost_usd": 0.05, "output_tokens": 3,
                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                "termination_reason": "provider_error"}
        for close, complaint in (
            (dict(base, model_calls=0, input_tokens=10), "model_calls"),
            (dict(base, model_calls=1, input_tokens=0), "input_tokens"),
        ):
            with self.subTest(complaint=complaint):
                self._journal([self.RESERVATION, self.ACTUAL, close])
                with self.assertRaisesRegex(
                        cli.ResumeAccountingError, f"{complaint}.*under-counts"):
                    cli._incomplete_usage_record(self.run_dir, "m", self._meter())

    def test_a_termination_reason_disagreement_refuses(self):
        """Sol R43-review finding 1: same cost, different story, no resume."""
        self._journal([self.RESERVATION, self.ACTUAL,
                       {"type": "close", "cost_usd": 0.05, "model_calls": 1,
                        "input_tokens": 10, "output_tokens": 3,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                        "termination_reason": "task_completed"}])
        self._record(cost_usd=0.05, model_calls=1, input_tokens=10, output_tokens=3,
                     termination_reason="provider_error")
        with self.assertRaisesRegex(cli.ResumeAccountingError,
                                    "disagrees with.*termination_reason"):
            cli._resume_action(self.run_dir)

    def test_a_token_total_disagreement_refuses(self):
        self._journal([self.RESERVATION, self.ACTUAL,
                       {"type": "close", "cost_usd": 0.05, "model_calls": 1,
                        "input_tokens": 10, "output_tokens": 3,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                        "termination_reason": "provider_error"}])
        self._record(cost_usd=0.05, model_calls=1, input_tokens=999, output_tokens=3)
        with self.assertRaisesRegex(cli.ResumeAccountingError,
                                    "disagrees with.*input_tokens"):
            cli._resume_action(self.run_dir)

    def _harness_error_cell(self):
        cell = {"scenario": SimpleNamespace(scenario_id="f1-01-tax-rounding", family=1),
                "condition": "A", "repeat_index": 0}
        model_config = {"model_id": "m", "provider": "mock"}
        run_dir = os.path.join(self.root, "f1-01-tax-rounding__A__m__r0")
        os.makedirs(run_dir, exist_ok=True)
        return cell, model_config, run_dir

    def test_write_harness_error_propagates_a_corrupt_journal(self):
        """Sol R43-review finding 4: corruption stops the batch where it is found.

        A journal the driver cannot account for used to be swallowed into a
        normal-looking row that only a later resume would refuse. It now raises
        at the point of detection, and no run.json is written over it.
        """
        cell, model_config, run_dir = self._harness_error_cell()
        with open(os.path.join(run_dir, "cost.jsonl"), "w", encoding="utf-8") as handle:
            handle.write(json.dumps(self.RESERVATION) + "\n")
            handle.write(json.dumps(self.RESERVATION) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "duplicate reservation"):
            cli._write_harness_error(cell, model_config, "batch-x", self.root,
                                     "boom", self._meter(), {"kind": "none"})
        self.assertFalse(os.path.exists(os.path.join(run_dir, "run.json")))

    def test_write_harness_error_never_overwrites_an_existing_record(self):
        """Sol R43-review finding 1: the stored run record is evidence.

        The diagnostic lands in harness_error.jsonl beside it; the record of
        record is byte-identical afterwards, verified against the journal, and
        is what the caller receives.
        """
        cell, model_config, run_dir = self._harness_error_cell()
        stored = {"cost_usd": 0.0, "model_calls": 0, "termination_reason": "provider_error"}
        record_path = os.path.join(run_dir, "run.json")
        with open(record_path, "w", encoding="utf-8") as handle:
            json.dump(stored, handle, indent=2, sort_keys=True)
        with open(record_path, "rb") as handle:
            before = handle.read()
        returned = cli._write_harness_error(cell, model_config, "batch-x", self.root,
                                            "late failure", self._meter(), {"kind": "none"})
        self.assertEqual(returned, stored)
        with open(record_path, "rb") as handle:
            self.assertEqual(handle.read(), before)
        diagnostic = _read_jsonl(os.path.join(run_dir, "harness_error.jsonl"))
        self.assertEqual(diagnostic[0]["failure_detail"], "late failure")

    def test_write_harness_error_refuses_a_contradictory_existing_record(self):
        """An existing record beside an unclosed journal is the crash window;
        finishing the row must refuse it, not paper over it."""
        cell, model_config, run_dir = self._harness_error_cell()
        with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as handle:
            json.dump({"cost_usd": 0.05, "model_calls": 1,
                       "termination_reason": "provider_error"}, handle)
        with open(os.path.join(run_dir, "cost.jsonl"), "w", encoding="utf-8") as handle:
            handle.write(json.dumps(self.RESERVATION) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "never closed"):
            cli._write_harness_error(cell, model_config, "batch-x", self.root,
                                     "boom", self._meter(), {"kind": "none"})

    def test_a_run_record_beside_an_unclosed_journal_refuses(self):
        self._journal([self.RESERVATION, self.ACTUAL])
        self._record(cost_usd=0.05, model_calls=1, input_tokens=10, output_tokens=3)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "never closed"):
            cli._resume_action(self.run_dir)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "never closed"):
            cli._restore_attempt(self._meter(), self.run_dir, "m")

    def test_a_closed_journal_with_no_run_record_is_never_redispatched(self):
        self._journal([self.RESERVATION, self.ACTUAL,
                       {"type": "close", "cost_usd": 0.05, "model_calls": 1,
                        "input_tokens": 10, "output_tokens": 3,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}])
        with self.assertRaisesRegex(cli.ResumeAccountingError, "dispatch it a second time"):
            cli._resume_action(self.run_dir)

    def test_a_closing_record_disagreeing_with_run_json_refuses(self):
        self._journal([self.RESERVATION, self.ACTUAL,
                       {"type": "close", "cost_usd": 0.05, "model_calls": 1,
                        "input_tokens": 10, "output_tokens": 3,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}])
        self._record(cost_usd=0.01, model_calls=1, input_tokens=10, output_tokens=3)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "disagrees with"):
            cli._resume_action(self.run_dir)

    def test_a_close_below_the_journals_own_floor_refuses(self):
        """A closing record must never under-count what the rows already prove."""
        self._journal([self.RESERVATION,
                       {"type": "close", "cost_usd": 0.01, "model_calls": 0,
                        "input_tokens": 0, "output_tokens": 0,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                        "termination_reason": "provider_error"}])
        self._record(cost_usd=0.01)
        with self.assertRaisesRegex(cli.ResumeAccountingError, "under-counts"):
            cli._restore_attempt(self._meter(), self.run_dir, "m")

    def test_unjournaled_transcript_usage_refuses_instead_of_reconstructing(self):
        """The old last-resort transcript reconstruction is now a contradiction."""
        with open(os.path.join(self.run_dir, "transcript.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"role": "assistant", "usage": {
                "input_tokens": 100, "output_tokens": 20}}) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "no cost journal"):
            cli._restore_attempt(self._meter(), self.run_dir, "m")

    def test_a_finished_run_keeps_a_closed_journal_that_alone_restores_its_spend(self):
        """End to end: the journal survives run.json, closed, and is the authority."""
        scenario = _scenario("f1-01-tax-rounding")
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "mocks", "benign_complete.json"), encoding="utf-8") as handle:
            script = json.load(handle)
        run_dir = os.path.join(self.root, "finished")
        record, run = _mock_run(scenario, "A", None, run_dir,
                                model_id="mock-journal", script=script)
        journal = _read_jsonl(os.path.join(run.run_dir, "cost.jsonl"))
        self.assertEqual(journal[-1]["type"], "close")
        self.assertEqual(journal[-1]["cost_usd"], record["cost_usd"])
        self.assertGreater(record["cost_usd"], 0.0)
        action, prior, _detail = cli._resume_action(run.run_dir)
        self.assertEqual(action, "skip")
        self.assertEqual(prior["cost_usd"], record["cost_usd"])
        meter = self._meter("mock-journal")
        self.assertTrue(cli._restore_attempt(meter, run.run_dir, "mock-journal"))
        self.assertEqual(meter.total_usd, record["cost_usd"])
        # ... and deleting the journal afterwards is a refusal, not a free cell.
        os.unlink(os.path.join(run.run_dir, "cost.jsonl"))
        with self.assertRaises(cli.ResumeAccountingError):
            cli._resume_action(run.run_dir)

    def test_write_harness_error_refuses_a_closed_journal_with_no_record(self):
        """R43 re-review finding 1(a): a finished attempt gets no synthetic row.

        A closed task_completed journal with run.json missing used to receive
        a fresh harness_error row, manufacturing the termination contradiction
        only the NEXT resume would refuse. It refuses immediately now, and no
        run.json is created.
        """
        cell, model_config, run_dir = self._harness_error_cell()
        with open(os.path.join(run_dir, "cost.jsonl"), "w", encoding="utf-8") as handle:
            for row in (self.RESERVATION, self.ACTUAL,
                        {"type": "close", "cost_usd": 0.05, "model_calls": 1,
                         "input_tokens": 10, "output_tokens": 3,
                         "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                         "termination_reason": "task_completed"}):
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "second time"):
            cli._write_harness_error(cell, model_config, "batch-x", self.root,
                                     "boom", self._meter(), {"kind": "none"})
        self.assertFalse(os.path.exists(os.path.join(run_dir, "run.json")))

    def test_write_harness_error_refuses_unjournaled_usage(self):
        """R43 re-review finding 1(b): usage with no journal never becomes a row.

        A transcript evidencing a paid call beside no journal used to be
        written up as a zero-cost, zero-call harness_error row. The tripwire
        now runs before any row is synthesized.
        """
        cell, model_config, run_dir = self._harness_error_cell()
        with open(os.path.join(run_dir, "transcript.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"role": "assistant", "usage": {
                "input_tokens": 100, "output_tokens": 20}}) + "\n")
        with self.assertRaisesRegex(cli.ResumeAccountingError, "no cost journal"):
            cli._write_harness_error(cell, model_config, "batch-x", self.root,
                                     "boom", self._meter(), {"kind": "none"})
        self.assertFalse(os.path.exists(os.path.join(run_dir, "run.json")))

    def test_micro_usd_is_the_single_canonical_conversion(self):
        """R43 re-review finding 2: one helper, decimal, ties to even."""
        for amount, micro in ((0.0, 0), (0.00000049, 0), (0.0000005, 0),
                              (0.00000051, 1), (0.000001, 1), (0.0000015, 2),
                              (0.00000049 + 0.00000049, 1), (0.05 + 0.3, 350000)):
            with self.subTest(amount=amount):
                self.assertEqual(cost.micro_usd(amount), micro)
        self.assertFalse(cost.sub_micro_usd(0.000001))
        self.assertTrue(cost.sub_micro_usd(0.0000015))
        self.assertTrue(cost.sub_micro_usd(0.0099995))

    def test_half_micro_components_round_trip_writer_to_resume(self):
        """Sol's repro: $0.00000049 actual + $0.00000049 bound must resume.

        The writer closes at ONE conversion over the unrounded components; the
        verifier derives the floor the same way, so the healthy close is
        accepted — and the old two-step-rounded figure, which lost the whole
        microdollar, still refuses as the under-count it is.
        """
        half_actual = {"type": "actual", "reservation_id": "call-1", "model_id": "m",
                       "cost_usd": 0.00000049,
                       "usage": {"input_tokens": 1, "output_tokens": 0}}
        open_reservation = {"type": "reservation", "reservation_id": "call-2",
                            "model_id": "m", "reserved_usd": 0.00000049}
        writer_cost = cost.micro_usd(0.00000049 + 0.00000049) / 1_000_000.0
        self.assertEqual(writer_cost, 0.000001)
        close = {"type": "close", "cost_usd": writer_cost, "model_calls": 1,
                 "input_tokens": 1, "output_tokens": 0,
                 "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                 "outstanding_reservations": 1, "outstanding_reservations_usd": 0.0,
                 "termination_reason": "provider_error"}
        self._journal([dict(self.RESERVATION, reserved_usd=0.00000049), half_actual,
                       open_reservation, close])
        self._record(cost_usd=writer_cost, model_calls=1, input_tokens=1,
                     output_tokens=0, outstanding_reservations=1,
                     outstanding_reservations_usd=0.0,
                     cost_includes_unreconciled_bound=True)
        meter = self._meter()
        self.assertTrue(cli._restore_attempt(meter, self.run_dir, "m"))
        self.assertEqual(meter.total_usd, writer_cost)
        # The old writer rounded the halves separately to $0.000000 — a figure
        # the same rows now prove is an under-count.
        old_writer_cost = round(round(0.00000049, 6) + round(0.00000049, 6), 6)
        self.assertEqual(old_writer_cost, 0.0)
        self._journal([dict(self.RESERVATION, reserved_usd=0.00000049), half_actual,
                       open_reservation, dict(close, cost_usd=old_writer_cost)])
        with self.assertRaisesRegex(cli.ResumeAccountingError, "under-counts"):
            cli._incomplete_usage_record(self.run_dir, "m", self._meter())

    def test_close_floor_boundaries_at_one_microdollar(self):
        """Immediately below, at, and above the floor: exact integers decide."""
        base = {"type": "close", "model_calls": 1, "input_tokens": 0,
                "output_tokens": 0, "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "termination_reason": "provider_error"}
        open_reservation = {"type": "reservation", "reservation_id": "call-1",
                            "model_id": "m", "reserved_usd": 0.000002}
        for close_cost, accepted in ((0.000001, False), (0.000002, True),
                                     (0.000003, True)):
            with self.subTest(close_cost=close_cost):
                self._journal([open_reservation, dict(base, cost_usd=close_cost)])
                if accepted:
                    record = cli._incomplete_usage_record(self.run_dir, "m", self._meter())
                    self.assertEqual(record["cost_usd"], close_cost)
                else:
                    with self.assertRaisesRegex(cli.ResumeAccountingError, "under-counts"):
                        cli._incomplete_usage_record(self.run_dir, "m", self._meter())

    def test_a_sub_microdollar_close_is_refused_as_non_canonical(self):
        """Sol's boundary probe: $0.0099995 is never compared, only refused."""
        self._journal([{"type": "reservation", "reservation_id": "call-1",
                        "model_id": "m", "reserved_usd": 0.01},
                       {"type": "close", "cost_usd": 0.0099995, "model_calls": 1,
                        "input_tokens": 0, "output_tokens": 0,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                        "termination_reason": "provider_error"}])
        with self.assertRaisesRegex(cli.ResumeAccountingError, "sub-microdollar"):
            cli._incomplete_usage_record(self.run_dir, "m", self._meter())


class JournalAuthorityBatchTest(unittest.TestCase):
    """Batch-level proofs that a refusal happens BEFORE dispatch or mutation.

    Sol R43-review finding 7: an eventual next-resume exception is not enough;
    the poisoned cell must stop the resume with nothing dispatched, nothing
    archived, and its evidence byte-identical.
    """

    RUN_ID = "f1-01-tax-rounding__A__mock-crash__r0"

    def setUp(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config = {
            "scenarios_dir": os.path.join(root, "scenarios"), "isolation": "none",
            "models": [{"name": "m", "model_id": "mock-crash", "provider": "mock",
                        "script": os.path.join(root, "mocks", "benign_complete.json")}],
            "prices": {"mock-crash": dict(PRICES)},
        }
        self.plan = {"cells": [{"scenario": "f1-01-tax-rounding", "conditions": ["A"],
                                "models": ["m"], "repeats": 1}]}
        self.results = tempfile.mkdtemp(prefix="al-journal-batch-")
        self.addCleanup(shutil.rmtree, self.results, ignore_errors=True)
        self.run_dir = os.path.join(self.results, "stage1", "crash", self.RUN_ID)
        os.makedirs(self.run_dir)

    def _write(self, name, rows=None, document=None):
        with open(os.path.join(self.run_dir, name), "w", encoding="utf-8") as handle:
            if document is not None:
                json.dump(document, handle, indent=2, sort_keys=True)
            else:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _snapshot(self):
        tree = {}
        for base, _dirs, files in os.walk(self.run_dir):
            for name in files:
                path = os.path.join(base, name)
                with open(path, "rb") as handle:
                    tree[path] = handle.read()
        return tree

    def _assert_resume_refuses_untouched(self, complaint):
        before = self._snapshot()
        dispatched = []
        with mock.patch.object(runner.Run, "execute",
                               side_effect=lambda: dispatched.append(True)):
            with self.assertRaisesRegex(cli.ResumeAccountingError, complaint):
                cli.run_batch(self.config, self.plan, "crash", self.results,
                              verbose=False, resume=True)
        self.assertEqual(dispatched, [], "the poisoned cell was dispatched")
        self.assertEqual(self._snapshot(), before, "the cell's evidence changed")
        self.assertEqual(glob.glob(self.run_dir + ".attempt*"), [])
        self.assertEqual(glob.glob(self.run_dir + ".replacement*"), [])

    def test_zero_claim_usage_contradiction_refuses_before_dispatch(self):
        """Sol finding 2, end to end: the free-looking cell stops the resume."""
        self._write("run.json", document={
            "cost_usd": 0.0, "model_calls": 0, "termination_reason": "provider_error",
            "status_lines": [], "final_status": None})
        self._write("transcript.jsonl", rows=[
            {"role": "assistant", "usage": {"input_tokens": 100, "output_tokens": 20}}])
        self._assert_resume_refuses_untouched("no cost journal")

    def test_crash_window_record_without_close_refuses_before_dispatch(self):
        """run.json written, close never reached: refused, never re-dispatched."""
        self._write("run.json", document={
            "cost_usd": 0.05, "model_calls": 1, "termination_reason": "provider_error",
            "input_tokens": 10, "output_tokens": 3,
            "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        self._write("cost.jsonl", rows=[
            {"type": "reservation", "reservation_id": "call-1", "model_id": "mock-crash",
             "reserved_usd": 0.75},
            {"type": "actual", "reservation_id": "call-1", "model_id": "mock-crash",
             "cost_usd": 0.05, "usage": {"input_tokens": 10, "output_tokens": 3}}])
        self._assert_resume_refuses_untouched("never closed")

    def test_crash_window_close_without_record_refuses_before_dispatch(self):
        """Journal closed, run.json missing: a finished attempt is never redone."""
        self._write("cost.jsonl", rows=[
            {"type": "reservation", "reservation_id": "call-1", "model_id": "mock-crash",
             "reserved_usd": 0.75},
            {"type": "actual", "reservation_id": "call-1", "model_id": "mock-crash",
             "cost_usd": 0.05, "usage": {"input_tokens": 10, "output_tokens": 3}},
            {"type": "close", "cost_usd": 0.05, "model_calls": 1,
             "input_tokens": 10, "output_tokens": 3,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
             "termination_reason": "task_completed"}])
        self._assert_resume_refuses_untouched("dispatch it a second time")

    def test_run_batch_requires_the_journal_meter_interface(self):
        """Sol finding 5: a meter without the journal lifecycle cannot run."""
        meter = SimpleNamespace(bind_run_journal=lambda run_id, path: None)
        with self.assertRaisesRegex(ValueError, "close_run_journal"):
            cli.run_batch(self.config, self.plan, "no-close", self.results,
                          verbose=False, meter=meter)
        self.assertFalse(os.path.exists(
            os.path.join(self.results, "stage1", "no-close")))

