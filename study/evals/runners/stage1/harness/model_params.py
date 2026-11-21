"""What each model actually accepts, and what this harness pins.

The aerial review found the clients carrying assumptions the current APIs
reject. Confirmed against the bundled Anthropic API reference (cached
2026-06-24) via the claude-api skill:

  Sonnet 5 and Opus 5
    temperature, top_p and top_k are REMOVED and return a 400. There is no
    sampling knob on this arm, which also settles the methods debate about
    "provider default temperature": there is nothing to set, so run.json records
    what was sent, which is nothing.
    budget_tokens is removed and returns a 400.
    thinking: {"type": "adaptive"} is the on-mode. Omitting the parameter runs
    adaptive on both. {"type": "disabled"} is accepted on Sonnet 5, and on
    Opus 5 only at effort high or below.
    effort lives in output_config, not top level: low | medium | high | xhigh | max.

  Why thinking is pinned ON for the Anthropic arms
    The reference warns that with thinking disabled, Opus 5 sometimes writes a
    tool call into visible text instead of a tool_use block, and can leak
    thinking tags into the response. In this harness that text would reach the
    prose classifier and be routed as a prose stop, which is a confound nobody
    wants. Adaptive thinking with a pinned effort is the setting that avoids it.

Every value here is recorded in run.json as what was actually sent. Nothing is
left null and inferred later.
"""

# Sampling parameters this harness will send, per model family. An empty tuple
# means the provider exposes no sampling control and none is sent.
ANTHROPIC_NO_SAMPLING = ("claude-sonnet-5", "claude-opus-5", "claude-opus-4-8",
                         "claude-opus-4-7", "claude-fable-5")

# OpenAI reasoning-series models reject temperature and take
# max_completion_tokens rather than max_tokens.
OPENAI_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")
OPENAI_CLASSIC_PREFIXES = ("gemini-",)

# Anthropic models from before the Claude 5 generation (Haiku 4.5 is the one this
# harness uses, as the route classifier). They still accept temperature, but the
# Python SDK 1.0.0 removed the sampling keywords from Messages.create, so the
# client sends them through extra_body. Adaptive thinking and output_config are
# not sent: the API rejects temperature 0 with thinking on, and a one-word
# classifier has nothing to think about.
ANTHROPIC_CLASSIC_PREFIXES = ("claude-haiku-4-5",)

DEFAULT_ANTHROPIC_CLASSIC = {
    "thinking": {"type": "disabled"},
    "effort": None,
    "sampling_supported": True,
}

DEFAULT_ANTHROPIC = {
    # Pinned, recorded, and deliberate. See the module docstring.
    "thinking": {"type": "adaptive"},
    "effort": "high",
    "sampling_supported": False,
}

DEFAULT_OPENAI_REASONING = {
    "thinking": "reasoning_series",
    "reasoning_effort": "high",
    "sampling_supported": False,
    "max_tokens_field": "max_completion_tokens",
}

DEFAULT_OPENAI_CLASSIC = {
    "thinking": "none",
    "reasoning_effort": None,
    "sampling_supported": True,
    "max_tokens_field": "max_tokens",
}

# R14 fixes the local model at thinking off. It is asserted on the wire by the
# smoke script, not assumed from a unit file.
DEFAULT_LOCAL = {
    "thinking": "off",
    "reasoning_effort": None,
    "sampling_supported": True,
    "max_tokens_field": "max_tokens",
}


def anthropic_profile(model_id, overrides=None):
    if any(model_id.startswith(p) for p in ANTHROPIC_CLASSIC_PREFIXES):
        profile = dict(DEFAULT_ANTHROPIC_CLASSIC)
    else:
        profile = dict(DEFAULT_ANTHROPIC)
        profile["sampling_supported"] = model_id not in ANTHROPIC_NO_SAMPLING
    profile.update(overrides or {})
    return profile


def openai_profile(model_id, provider="openai", overrides=None):
    reasoning = any(model_id.startswith(p) for p in OPENAI_REASONING_PREFIXES)
    if provider == "local":
        profile = dict(DEFAULT_LOCAL)
    elif any(model_id.startswith(p) for p in OPENAI_CLASSIC_PREFIXES):
        profile = dict(DEFAULT_OPENAI_CLASSIC)
        if model_id.startswith("gemini-"):
            # Gemini 3.7 Flash emits nothing under a cap below about 256 even with the
            # thinking budget at zero (hidden tokens are reserved inside max_tokens);
            # probed 2026-08-23: 8, 16, 32, 64 empty; 256 and 512 answer with 4 tokens.
            profile["min_max_tokens"] = 2048
    else:
        profile = dict(DEFAULT_OPENAI_REASONING if reasoning else DEFAULT_OPENAI_CLASSIC)
    profile.update(overrides or {})
    return profile
