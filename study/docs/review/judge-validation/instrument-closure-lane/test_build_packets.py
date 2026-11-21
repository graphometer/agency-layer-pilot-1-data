"""Golden tests for opaque, deterministic lane labelling packets."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_packets import add_panel_split, build_packets, write_packets  # noqa: E402


class PacketBuilderTests(unittest.TestCase):
    def fixture(self):
        gold = [
            {"item_id": "real-item", "scenario_id": "scenario", "run_id": "run",
             "turn_index": 2, "synthetic": False, "condition": "D", "channel": "tool",
             "stratum": "S1", "text": "flattened real text"},
            {"item_id": "nm-a-secret", "scenario_id": "scenario", "synthetic": True,
             "condition": "C", "channel": "tool", "stratum": "S2",
             "text": "Assistant raises a constructed concern."},
        ]
        frame = [{
            "run_id": "run", "turn_index": 2, "scenario_id": "scenario",
            "ground_truth_issue": "FIX-14 ISSUE SENTINEL",
            "normalized_turn": [
                {"speaker": "assistant", "text": "CURRENT TURN SENTINEL"},
            ],
            "transcript_through_turn": [
                {"speaker": "user", "text": "PRIOR TURN SENTINEL"},
                {"speaker": "assistant", "text": "CURRENT TURN SENTINEL"},
            ],
        }]
        near = [{
            "item_id": "nm-a-secret", "act": "clarify",
            "arguments": {"reason": "private structural value"},
            "construction_class": "a", "condition": "C", "channel": "tool",
            "text": "Assistant raises a constructed concern.",
        }]
        intent = [{
            "item_id": "nm-a-secret", "act": "clarify", "construction_class": "a",
        }]
        return gold, frame, near, intent

    def built(self):
        return build_packets(*self.fixture(), "LIVE L1 RUBRIC SENTINEL")

    def test_packets_expose_only_opaque_binding_and_prompt(self) -> None:
        l1, l2, joins = self.built()
        visible = json.dumps(l1 + l2, sort_keys=True)
        self.assertEqual({"request_id", "prompt"}, set(l1[0]))
        self.assertNotIn("nm-", visible)
        self.assertNotIn("real-item", visible)
        self.assertNotIn('"act"', visible)
        self.assertNotIn("clarify", visible)
        self.assertNotIn("arguments", visible)
        self.assertNotIn("construction_class", visible)
        self.assertNotIn("stratum", visible)
        self.assertNotIn('"condition":', visible)
        self.assertNotIn('"channel":', visible)
        self.assertNotIn("/mnt/vault/", visible)
        expected = hashlib.sha256(b"real-item-l1-packet").hexdigest()[:24]
        self.assertEqual(l1[0]["request_id"], expected)
        self.assertEqual(len(joins), 4)
        self.assertEqual(set(joins[0]), {"request_id", "item_id"})

    def test_l1_real_has_through_turn_but_s2_has_constructed_text_only(self) -> None:
        l1, _, _ = self.built()
        self.assertIn("PRIOR TURN SENTINEL", l1[0]["prompt"])
        self.assertIn("CURRENT TURN SENTINEL", l1[0]["prompt"])
        self.assertIn("FIX-14 ISSUE SENTINEL", l1[1]["prompt"])
        self.assertIn("Assistant raises a constructed concern.", l1[1]["prompt"])
        self.assertNotIn("PRIOR TURN SENTINEL", l1[1]["prompt"])

    def test_l2_has_current_turn_only_and_no_ground_truth(self) -> None:
        _, l2, _ = self.built()
        self.assertIn("CURRENT TURN SENTINEL", l2[0]["prompt"])
        self.assertNotIn("PRIOR TURN SENTINEL", l2[0]["prompt"])
        self.assertNotIn("FIX-14 ISSUE SENTINEL", l2[0]["prompt"])
        adjudication = add_panel_split(l2[0], ["attempt", "no_attempt"])
        self.assertNotIn("FIX-14 ISSUE SENTINEL", adjudication["prompt"])

    def test_output_is_byte_deterministic_across_two_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            write_packets(first, *self.built())
            write_packets(second, *self.built())
            for name in ("l1_packets.jsonl", "l2_packets.jsonl", "packet_join.jsonl"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
