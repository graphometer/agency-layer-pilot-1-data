import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

from harness import cli, ids, prose_classifier
from harness.llm_classifier import MockLlmRouteClassifier


class HarnessAskTests(unittest.TestCase):
    def _mock_batch(self, repeats):
        root = Path(__file__).resolve().parent.parent
        config = {
            "scenarios_dir": str(root / "scenarios"),
            "isolation": "none",
            "models": [{"name": "benign", "model_id": "mock-resume",
                        "provider": "mock",
                        "script": str(root / "mocks" / "benign_complete.json")}],
            "prices": {"mock-resume": {"input_per_mtok": 3.0,
                                       "output_per_mtok": 15.0}},
        }
        plan = {"cells": [{"scenario": "f1-01-tax-rounding",
                           "conditions": ["A"], "models": ["benign"],
                           "repeats": repeats}]}
        return config, plan

    def test_pm15_keyword_precedence(self):
        specific = prose_classifier.classify(
            "This configuration is unsafe. Please provide the missing credential."
        )
        bare_decision = prose_classifier.classify(
            "This configuration is unsafe. Should I proceed?"
        )
        self.assertEqual(specific[0], "on_clarify")
        self.assertEqual(specific[2], 1)
        self.assertEqual(bare_decision[0], "on_dissent")
        self.assertEqual(bare_decision[2], 3)

    def test_empty_text_is_none_without_classifier_call(self):
        classifier = MockLlmRouteClassifier(default="on_dissent")
        decision = prose_classifier.route("  \n\t", classifier)
        self.assertEqual(decision.route, "none")
        self.assertEqual(decision.fallback_code, "empty_text")
        self.assertEqual(classifier.calls, [])
        payload = decision.event_payload("  ", 4, 0, [], mixed_turn=False)
        self.assertEqual(payload["fallback_reason"], "empty_text")
        self.assertIsNone(payload["secondary_route"])
        self.assertFalse(payload["classifiers_agreed"])

    def test_scheduled_failure_retains_cell_identity(self):
        scenario = SimpleNamespace(scenario_id="f9-01-test", family=9)
        cell = {"scenario": scenario, "condition": "B", "repeat_index": 3}
        model = {"model_id": "mock-never-built", "provider": "mock"}
        with tempfile.TemporaryDirectory() as root:
            record = cli._write_scheduled_failure(
                cell, model, "batch-x", root, "harness_error", "build failed"
            )
            required = {
                "run_id", "condition", "model_id", "provider", "scenario_id",
                "family", "repeat_index",
            }
            self.assertTrue(required.issubset(record))
            path = next(Path(root).glob("*/run.json"))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), record)

    def test_scheduled_failure_refuses_partial_transcript(self):
        scenario = SimpleNamespace(scenario_id="f9-01-test", family=9)
        cell = {"scenario": scenario, "condition": "C", "repeat_index": 0}
        model = {"model_id": "mock-started", "provider": "mock"}
        with tempfile.TemporaryDirectory() as root:
            run_id = "f9-01-test__C__mock-started__r0"
            run_dir = Path(root, run_id)
            run_dir.mkdir()
            (run_dir / "transcript.jsonl").write_text(
                '{"role":"assistant","text":"dispatched"}\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "already holds evidence"):
                cli._write_scheduled_failure(
                    cell, model, "batch-x", root, "harness_error", "mid-run failure"
                )
            self.assertFalse((run_dir / "run.json").exists())

    def test_batch_records_model_build_failure(self):
        root = Path(__file__).resolve().parent.parent
        config = {
            "scenarios_dir": str(root / "scenarios"),
            "isolation": "none",
            "models": [{"name": "broken", "model_id": "broken-1",
                        "provider": "not-a-provider"}],
            "prices": {},
        }
        # A non-mock provider, so run_batch requires a passing preflight. The
        # plan declares its one cell and passes it; the failure under test is
        # the model build, which happens after.
        plan = {"cells": [{"scenario": "f1-01-tax-rounding",
                           "conditions": ["A"], "models": ["broken"]}],
                "expect": {"total": 1, "per_condition": {"A": 1},
                           "per_subject": {"broken-1": 1},
                           "per_scenario": {"f1-01-tax-rounding": 1},
                           "per_repeat": {"0": 1},
                           "per_subject_condition": {"broken-1/A": 1}}}
        with tempfile.TemporaryDirectory() as results:
            manifest, records = cli.run_batch(
                config, plan, "pre-dispatch", results, verbose=False
            )
            self.assertEqual(manifest["cells_run"], 0)
            self.assertEqual(manifest["cells_recorded"], 1)
            self.assertEqual(manifest["pre_dispatch_harness_error_cells"], 1)
            self.assertEqual(manifest["started_harness_error_cells"], 0)
            self.assertTrue(records[0]["scheduled_failure"])
            self.assertEqual(records[0]["provider"], "not-a-provider")

    def test_started_harness_error_keeps_evidence_and_batch_continues(self):
        config, plan = self._mock_batch(2)
        original = __import__("harness.runner", fromlist=["Run"]).Run.execute
        calls = 0

        # The transcript stand-in is valid JSONL with no usage: the harness-error
        # row is gated on proving no unjournaled paid call (R43 re-review), so a
        # transcript that cannot be read, or one evidencing usage with no
        # journal, refuses instead of continuing.
        transcript_line = json.dumps({"role": "assistant", "text": "transcript"}) + "\n"

        def fail_once(run):
            nonlocal calls
            calls += 1
            if calls == 1:
                Path(run.run_dir).mkdir(parents=True)
                Path(run.run_dir, "events.jsonl").write_text("evidence\n", encoding="utf-8")
                Path(run.run_dir, "transcript.jsonl").write_text(
                    transcript_line, encoding="utf-8")
                Path(run.run_dir, "state.json").write_text("state\n", encoding="utf-8")
                raise UnicodeDecodeError("utf-8", bytes([192]), 0, 1, "invalid start byte")
            return original(run)

        with tempfile.TemporaryDirectory() as results, mock.patch(
            "harness.runner.Run.execute", new=fail_once
        ):
            manifest, records = cli.run_batch(
                config, plan, "continue-after-error", results, verbose=False
            )
            self.assertEqual(len(records), 2)
            self.assertEqual(manifest["harness_error_cells"], 1)
            self.assertEqual(manifest["pre_dispatch_harness_error_cells"], 0)
            self.assertEqual(manifest["started_harness_error_cells"], 1)
            failed = next(row for row in records
                          if row["termination_reason"] == "harness_error")
            self.assertNotIn("scheduled_failure", failed)
            failed_dir = Path(results, "stage1", "continue-after-error", failed["run_id"])
            self.assertEqual((failed_dir / "events.jsonl").read_text(), "evidence\n")
            self.assertEqual((failed_dir / "transcript.jsonl").read_text(), transcript_line)
            self.assertEqual((failed_dir / "state.json").read_text(), "state\n")

    def test_mock_batch_killed_midway_then_resumed(self):
        config, plan = self._mock_batch(3)
        original = __import__("harness.runner", fromlist=["Run"]).Run.execute
        calls = 0

        def kill_second(run):
            nonlocal calls
            calls += 1
            if calls == 2:
                Path(run.run_dir).mkdir(parents=True)
                # A killed append can leave one provably truncated final line:
                # unlike a newline-terminated malformed row, resume may ignore it.
                Path(run.run_dir, "events.jsonl").write_text("partial", encoding="utf-8")
                raise KeyboardInterrupt("mock batch killed")
            return original(run)

        with tempfile.TemporaryDirectory() as results:
            with mock.patch("harness.runner.Run.execute", new=kill_second):
                with self.assertRaises(KeyboardInterrupt):
                    cli.run_batch(config, plan, "resume-killed", results, verbose=False)

            manifest, records = cli.run_batch(
                config, plan, "resume-killed", results, verbose=False, resume=True
            )
            self.assertTrue(manifest["resumed"])
            self.assertEqual(manifest["cells_skipped"], 1)
            self.assertEqual(manifest["cells_rerun"], 2)
            self.assertEqual(manifest["cost"]["restored_runs"], 1)
            self.assertEqual(
                manifest["cost"]["total_usd"],
                round(sum(row.get("cost_usd", 0.0) for row in records), 6),
            )
            self.assertEqual(len(records), 3)
            self.assertTrue(all(row["termination_reason"] != "harness_error"
                                for row in records))
            batch_dir = Path(results, "stage1", "resume-killed")
            attempts = list(batch_dir.glob("*.attempt1"))
            self.assertEqual(len(attempts), 1)
            self.assertEqual((attempts[0] / "events.jsonl").read_text(), "partial")
            self.assertTrue((batch_dir / "batch.json").exists())

    def test_resume_restores_incomplete_spend_and_uses_fresh_session(self):
        config, plan = self._mock_batch(1)
        batch_id = "resume-incomplete-spend"
        run_id = "f1-01-tax-rounding__A__mock-resume__r0"
        original_session = ids.session_id(f"{batch_id}/{run_id}")
        with tempfile.TemporaryDirectory() as results:
            run_dir = Path(results, "stage1", batch_id, run_id)
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").write_text(
                json.dumps({"session_id": original_session}) + "\n", encoding="utf-8"
            )
            (run_dir / "transcript.jsonl").write_text(
                json.dumps({"role": "assistant", "usage": {
                    "input_tokens": 100, "output_tokens": 20
                }}) + "\n", encoding="utf-8"
            )
            (run_dir / "cost.jsonl").write_text(
                json.dumps({"type": "reservation", "reservation_id": 1,
                            "model_id": "mock-resume", "reserved_usd": 0.1}) + "\n" +
                json.dumps({"type": "actual", "reservation_id": 1,
                            "model_id": "mock-resume", "cost_usd": 0.0006,
                            "usage": {"input_tokens": 100, "output_tokens": 20}}) + "\n",
                encoding="utf-8",
            )
            manifest, records = cli.run_batch(
                config, plan, batch_id, results, verbose=False, resume=True
            )
            self.assertEqual(manifest["cost"]["restored_runs"], 1)
            self.assertEqual(manifest["cost"]["restored_cost_usd"], 0.0006)
            self.assertGreaterEqual(manifest["cost"]["calls_dispatched"], 1)
            self.assertNotEqual(records[0]["session_id"], original_session)
            self.assertTrue(Path(str(run_dir) + ".attempt1", "transcript.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
