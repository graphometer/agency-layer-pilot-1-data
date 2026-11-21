"""A mock model that replays a canned script, so the whole loop runs at zero cost.

The mock is deliberately deaf: it replays its turns in order whatever the harness
says back to it. That is the point. When the same script is run in condition C
and condition D, every difference in the result comes from the harness, because
the model behaviour was byte-identical by construction.

Past the end of its script the mock returns a final turn with no tool calls, so
a script can never hang the loop.
"""

import json

from .base import ModelClient, ModelReply


class MockModel(ModelClient):
    provider = "mock"
    endpoint = None
    seed_supported = True

    def __init__(self, script, model_id="mock-1"):
        self.model_id = model_id
        self.script = script
        self.turns = script.get("turns", [])
        self.default_turn = script.get(
            "default_turn", {"text": "Nothing further from me.", "tool_calls": []}
        )
        # Synthetic per-turn usage, so the cost meter is exercised end to end
        # rather than only in a unit test.
        self.usage = script.get("usage", {"input_tokens": 0, "output_tokens": 0})
        self.index = 0
        self.calls = []

    @classmethod
    def from_file(cls, path, model_id="mock-1"):
        with open(path, "r", encoding="utf-8") as handle:
            return cls(json.load(handle), model_id=model_id)

    api_surface = "mock"

    def count_prompt_tokens(self, system_prompt, messages, tools):
        """Exactly what this mock will report, so the bound is testable.

        A mock's reported usage is arbitrary by construction, so a mock that
        estimated its own prompt could never test whether a reservation covers a
        call. Returning the number it will actually report makes
        reserved >= actual a provable property of the meter rather than of the
        mock's honesty.
        """
        return int(self.usage.get("input_tokens", 0) or 0)

    def sent_parameters(self, sampling):
        return {
            "api_surface": self.api_surface,
            "thinking": self.script.get("thinking", "mock"),
            "reasoning_effort": self.script.get("reasoning_effort", "mock"),
            "sampling_sent": {k: v for k, v in sampling.items() if v is not None},
            "max_tokens": sampling.get("max_tokens"),
            "prompt_caching": "none",
            "tool_schema_rendering": "as_published",
        }

    def generate(self, system_prompt, messages, tools, sampling):
        turn = self.turns[self.index] if self.index < len(self.turns) else self.default_turn
        self.index += 1
        self.calls.append(
            {
                "turn_index": self.index,
                "tool_names_offered": [tool["name"] for tool in tools],
                "message_count": len(messages),
            }
        )
        tool_calls = []
        for position, call in enumerate(turn.get("tool_calls", [])):
            tool_calls.append(
                {
                    "id": call.get("id") or f"mock-{self.index}-{position}",
                    "name": call["name"],
                    "arguments": call.get("arguments", {}),
                }
            )
        return ModelReply(
            text=turn.get("text", ""),
            tool_calls=tool_calls,
            usage=dict(self.usage),
            stop_reason="tool_use" if tool_calls else "end_turn",
            system_fingerprint=turn.get("system_fingerprint", "mock-fingerprint"),
            raw={"mock_turn_index": self.index},
            sent_params=self.sent_parameters(sampling),
        )
