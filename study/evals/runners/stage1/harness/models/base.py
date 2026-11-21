"""The narrow model interface every provider implements.

Deliberately small. The loop, the guard and the event log know nothing about
providers, and a provider knows nothing about the protocol. That boundary is
what lets a fourth implementation be added later without touching the parts of
the harness the study's claims rest on.
"""


class ModelReply:
    """One assistant turn, normalized."""

    def __init__(
        self,
        text="",
        tool_calls=None,
        usage=None,
        stop_reason=None,
        system_fingerprint=None,
        raw=None,
        raw_content=None,
        stop_details=None,
        sent_params=None,
    ):
        self.text = text
        # Each: {"id": str, "name": str, "arguments": dict}
        self.tool_calls = tool_calls or []
        # Provider-reported usage. The cost meter sums exactly this and never a
        # local token estimate, so the published spend is the provider's number.
        self.usage = usage or {"input_tokens": 0, "output_tokens": 0}
        self.stop_reason = stop_reason
        self.system_fingerprint = system_fingerprint
        self.raw = raw or {}
        # The provider's own content blocks, replayed verbatim on later turns so
        # thinking blocks and any block type the harness does not model come back
        # unchanged, which the same model requires.
        self.raw_content = raw_content
        # Populated only when stop_reason is refusal.
        self.stop_details = stop_details
        # Exactly what the client put on the wire, for run.json. Never null.
        self.sent_params = sent_params or {}


class ProviderError(Exception):
    """A provider call failed. Never scored as model behaviour (SPEC 4.5)."""


class ModelClient:
    """Interface.

    model_id      the dated provider identifier recorded in run.json
    provider      anthropic | openai | local | mock
    endpoint      base_url for local and openai-compatible endpoints, else null
    seed_supported whether the provider accepts a seed (methods 4.7: Anthropic
                  exposes none, so its runs are best-effort reproducible)
    """

    model_id = "unset"
    provider = "unset"
    endpoint = None
    seed_supported = False
    # Which endpoint this client speaks to, recorded in run.json so a reader
    # never has to infer it. The OpenAI arm moved to /v1/responses after the
    # first real smoke; the local arm stayed on chat completions.
    api_surface = "unset"

    def generate(self, system_prompt, messages, tools, sampling):
        raise NotImplementedError

    # Which price fields this arm's reservation needs. Anthropic adds the cache
    # rates, because a cache write costs more than base input and a reservation
    # priced at the input rate would under-reserve every call that writes one.
    required_price_fields = ("input_per_mtok", "output_per_mtok")

    def count_prompt_tokens(self, system_prompt, messages, tools):
        """The provider's own count of this prompt, or None.

        None means the meter falls back to the UTF-8 byte length, which bounds
        any byte-level BPE tokenizer from above. A client returning a number is
        promising it is the provider's count, not an estimate.
        """
        return None

    def sent_parameters(self, sampling):
        """What this client would put on the wire. Recorded in run.json."""
        return {"thinking": None, "reasoning_effort": None, "sampling_sent": {},
                "max_tokens": sampling.get("max_tokens"), "prompt_caching": "none"}
