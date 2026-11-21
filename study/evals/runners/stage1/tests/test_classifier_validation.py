import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from harness import config as config_module
from harness.cli import build_route_classifier
from harness.llm_classifier import (FROZEN_PROMPT, FROZEN_PROMPT_VERSION,
                                    PREVIOUS_PROMPTS, LlmRouteClassifier)
from harness.models.anthropic_client import AnthropicClient
from harness.models.base import ModelReply
from harness.models.openai_client import OpenAICompatibleClient
from tools import classifier_validation


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CannedAnthropic(AnthropicClient):
    def generate(self, system_prompt, messages, tools, sampling):
        return ModelReply(
            text="on_dissent",
            usage={"input_tokens": 1, "output_tokens": 1},
            sent_params=self.sent_parameters(sampling),
        )


class ClassifierValidationArithmeticTest(unittest.TestCase):
    def test_pm15_prompt_version_and_precedence(self):
        self.assertEqual(FROZEN_PROMPT_VERSION, "prose-llm-prompt-0.3.0")
        self.assertIn("prose-llm-prompt-0.2.0", PREVIOUS_PROMPTS)
        self.assertIn("specific missing value, file, credential", FROZEN_PROMPT)
        self.assertIn("objects and asks only a bare decision question", FROZEN_PROMPT)

    def test_mock_probe_arithmetic(self):
        # The report also reads the rehearsal real-turns and label files, which are
        # WITHHELD staging data (PM14: rehearsal transcripts never enter the repo). This
        # test therefore ran only on the lab machine and silently depended on paths
        # outside the repository — surfaced when step 7 removed the absolute defaults.
        # It runs where the env vars point at the staging data and skips elsewhere.
        real = classifier_validation.DEFAULT_REAL_TURNS
        labels = classifier_validation.DEFAULT_LABELS_DIR
        if not (real and os.path.isfile(real) and labels and os.path.isdir(labels)):
            self.skipTest(
                "validation inputs are withheld staging data; set "
                "AL_CLASSIFIER_REAL_TURNS and AL_CLASSIFIER_LABELS_DIR to run this test")
        config_path = os.path.join(ROOT, "classifier_mock.yaml")
        config = config_module.load_config(config_path)
        classifier = build_route_classifier(config, config_dir=ROOT)
        report = classifier_validation.build_report(
            classifier,
            classifier_validation.DEFAULT_REAL_TURNS,
            classifier_validation.DEFAULT_LABELS_DIR,
        )

        # Hand calculation: default on_dissent gets 17 train probes right.
        # S01 and S05 are correct overrides, and empty B04 now correctly
        # short-circuits to none without consulting the mock: 20 of 40.
        self.assertEqual(report["probes"]["train"]["correct"], 20)
        self.assertEqual(report["probes"]["train"]["count"], 40)
        self.assertAlmostEqual(report["probes"]["train"]["accuracy"], 20 / 40)

        # No holdout text is overridden. Its nine on_dissent labels are right.
        self.assertEqual(report["probes"]["holdout"]["correct"], 9)
        self.assertEqual(report["probes"]["holdout"]["count"], 32)
        self.assertAlmostEqual(report["probes"]["holdout"]["accuracy"], 9 / 32)

        train_confusion = report["probes"]["train"]["confusion"]
        self.assertEqual(train_confusion["on_clarify"]["on_clarify"], 1)
        self.assertEqual(train_confusion["none"]["none"], 2)
        self.assertEqual(train_confusion["on_dissent"]["on_dissent"], 17)

        consensus = report["real_turns"]["labels"]["consensus"]
        self.assertEqual(consensus["count"], 34)
        self.assertIn("rt-28", consensus["labels"])
        self.assertIn("claude-sonnet-5", consensus["by_subject_model"])
        self.assertIn("mixed_precedence_flags", consensus)

    def test_sampling_sent_uses_provider_filter(self):
        unsupported = LlmRouteClassifier(CannedAnthropic("claude-sonnet-5"))
        supported = LlmRouteClassifier(CannedAnthropic("claude-haiku-4-5-20251001"))

        self.assertEqual(unsupported.classify("This is wrong.").sampling_sent, {})
        self.assertEqual(
            supported.classify("This is wrong.").sampling_sent,
            {"temperature": 0.0},
        )

    def test_mixed_precedence_flags_both_directions(self):
        real_results = [
            {"id": "x1", "got": "on_dissent", "model": "m1", "condition": "A",
             "family": 1},
            {"id": "x2", "got": "on_clarify", "model": "m2", "condition": "B",
             "family": 2},
        ]
        with tempfile.TemporaryDirectory() as labels_dir:
            for name in ("alpha", "beta"):
                rows = [
                    {"id": "x1", "label": "on_dissent", "specific_request": True,
                     "note": "mixed"},
                    {"id": "x2", "label": "on_clarify", "specific_request": False,
                     "note": "reverse"},
                ]
                with open(os.path.join(labels_dir, name + ".jsonl"), "w",
                          encoding="utf-8") as handle:
                    for row in rows:
                        handle.write(json.dumps(row) + "\n")
            with open(os.path.join(labels_dir, "consensus.jsonl"), "w",
                      encoding="utf-8") as handle:
                handle.write(json.dumps({"id": "x1", "label": "on_dissent"}) + "\n")
                handle.write(json.dumps({"id": "x2", "label": "on_clarify"}) + "\n")
            analysis = classifier_validation.label_analysis(real_results, labels_dir)
        flags = {item["id"]: item["flag"]
                 for item in analysis["consensus"]["mixed_precedence_flags"]}
        self.assertEqual(flags["x1"], "specific_request_but_on_dissent")
        self.assertEqual(flags["x2"], "on_clarify_without_specific_request")

    def test_openai_compatible_gemini_profile_and_extra_body(self):
        configured = {
            "extra_body": {"google": {"thinking_config": {"thinking_budget": 0}}}
        }
        client = OpenAICompatibleClient(
            "gemini-3.7-flash", provider="openai_compatible",
            base_url="https://example.invalid/v1", api_key_env="GOOGLE_API_KEY",
            extra_body=configured,
        )
        captured = {}

        def create(**request):
            captured.update(request)
            message = SimpleNamespace(content="on_dissent", tool_calls=[], refusal=None)
            choice = SimpleNamespace(message=message, finish_reason="stop")
            usage = SimpleNamespace(prompt_tokens=2, completion_tokens=1)
            return SimpleNamespace(choices=[choice], usage=usage, id="x", model=client.model_id,
                                   system_fingerprint=None)

        client._client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        reply = client.generate(FROZEN_PROMPT, [], [], {"temperature": 0.0, "max_tokens": 8})
        self.assertEqual(client.profile["thinking"], "none")
        self.assertTrue(client.profile["sampling_supported"])
        self.assertEqual(client.profile["max_tokens_field"], "max_tokens")
        self.assertEqual(captured["temperature"], 0.0)
        self.assertEqual(captured["extra_body"], configured["extra_body"])
        self.assertEqual(reply.sent_params["sampling_sent"], {
            "temperature": 0.0, "extra_body": configured,
        })


if __name__ == "__main__":
    unittest.main()
