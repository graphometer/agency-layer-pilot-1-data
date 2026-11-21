"""Anthropic client.

Keys come from the environment only. The harness never reads a key from a file
and never writes one to a run record, a log, or an error message.

Corrected after the aerial review, against the bundled API reference (cached
2026-06-24). Four things this file gets right that the first version got wrong:

1. **No sampling parameters.** `temperature`, `top_p` and `top_k` are removed on
   Sonnet 5 and Opus 5 and return a 400. They are never sent, and `run.json`
   records `sampling_sent: {}` rather than a temperature that was not applied.
2. **Thinking is pinned, not omitted.** `{"type": "adaptive"}` with a pinned
   `output_config.effort`, both recorded. Omitting the parameter would still run
   adaptive but would leave the record saying null; disabling it risks Opus 5
   writing a tool call into visible text, which this harness would route to the
   prose classifier as a prose stop.
3. **Multi-block round-trip.** Assistant content is replayed verbatim, thinking
   blocks included, because they must come back unchanged on the same model.
4. **Prompt caching.** `cache_control` on the last tool and on the system
   prompt. Render order is tools, then system, then messages, so those two
   breakpoints cover the whole frozen prefix. It changes no output and roughly
   halves this arm's input cost.

Consecutive user turns are merged into one message, because the harness appends
tool results and then the scripted operator line, and a merged message is valid
on every provider whether or not consecutive ones are.

Not exercised in the mock milestone: nothing here has been run against the live
API. The smoke script is what proves it.
"""

import os

from .. import model_params
from .base import ModelClient, ModelReply, ProviderError

ENV_KEY = "ANTHROPIC_API_KEY"


class AnthropicClient(ModelClient):
    provider = "anthropic"
    endpoint = None
    api_surface = "messages"
    # A cache write bills above base input, so the reservation needs both rates.
    required_price_fields = ("input_per_mtok", "output_per_mtok",
                             "cache_read_per_mtok", "cache_write_per_mtok")
    # The Messages API exposes no seed, so this arm is best-effort reproducible
    # rather than seeded (methods 4.7).
    seed_supported = False

    def __init__(self, model_id, max_retries=2, timeout=600, profile_overrides=None):
        self.model_id = model_id
        self.max_retries = max_retries
        self.timeout = timeout
        self.profile = model_params.anthropic_profile(model_id, profile_overrides)
        self._client = None

    # ------------------------------------------------------------- the record

    def sent_parameters(self, sampling):
        """Exactly what this client will put on the wire, for run.json."""
        record = {
            "api_surface": self.api_surface,
            "thinking": self.profile["thinking"],
            "reasoning_effort": self.profile["effort"],
            "sampling_sent": {},
            "max_tokens": sampling.get("max_tokens", 4096),
            "prompt_caching": "system+tools",
            "tool_schema_rendering": "as_published",
        }
        if self.profile["sampling_supported"]:
            for name in ("temperature", "top_p", "top_k"):
                if sampling.get(name) is not None:
                    record["sampling_sent"][name] = sampling[name]
        return record

    def count_prompt_tokens(self, system_prompt, messages, tools):
        """The provider's own count, from the free count_tokens endpoint.

        Counted with the same system, messages, tools and thinking setting the
        real call will carry, so the number bounds that call rather than a
        simplified version of it.
        """
        try:
            client = self._ensure_client()
            request = {
                "model": self.model_id,
                "system": self._system(system_prompt),
                "messages": self._messages(messages),
                "thinking": self.profile["thinking"],
            }
            if tools:
                request["tools"] = self._tools(tools)
            return int(client.messages.count_tokens(**request).input_tokens)
        except Exception:
            # Never fatal: the meter falls back to the byte bound, which is
            # looser and still safe.
            return None

    # ------------------------------------------------------------------ setup

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        key = os.environ.get(ENV_KEY)
        if not key:
            raise ProviderError(
                f"{ENV_KEY} is not set in the environment. The harness reads keys "
                "from the environment only."
            )
        try:
            import anthropic
        except ImportError as error:
            raise ProviderError(f"the anthropic SDK is not installed: {error}")
        self._client = anthropic.Anthropic(
            api_key=key, max_retries=self.max_retries, timeout=self.timeout
        )
        return self._client

    def _tools(self, tools):
        """Tool definitions, with a cache breakpoint on the last one.

        Tools render first, so one breakpoint at the end of the tool list caches
        the whole list. The list is deterministic per run, which is what makes it
        cacheable at all; the per-run tool order changes between runs and simply
        starts a new cache entry.
        """
        rendered = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in tools
        ]
        if rendered:
            rendered[-1]["cache_control"] = {"type": "ephemeral"}
        return rendered

    def _system(self, system_prompt):
        return [{"type": "text", "text": system_prompt,
                 "cache_control": {"type": "ephemeral"}}]

    @staticmethod
    def _messages(messages):
        """Translate the harness's neutral message list into Anthropic blocks.

        Assistant turns are replayed from `raw_content` when the provider gave
        it, so thinking blocks and any block type this harness does not model
        come back unchanged, which the same model requires. Consecutive
        same-role messages are merged.
        """
        translated = []
        for message in messages:
            role = message["role"]
            if role == "user":
                content = []
                for block in message["content"]:
                    if block["type"] == "text":
                        content.append({"type": "text", "text": block["text"]})
                    elif block["type"] == "tool_result":
                        content.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block["tool_call_id"],
                                "content": block["content"],
                                "is_error": block.get("is_error", False),
                            }
                        )
                entry = {"role": "user", "content": content}
            else:
                raw = message.get("raw_content")
                if raw:
                    # Verbatim replay, thinking blocks included.
                    entry = {"role": "assistant", "content": raw}
                else:
                    content = []
                    if message.get("text"):
                        content.append({"type": "text", "text": message["text"]})
                    for call in message.get("tool_calls", []):
                        content.append(
                            {
                                "type": "tool_use",
                                "id": call["id"],
                                "name": call["name"],
                                "input": call["arguments"],
                            }
                        )
                    if not content:
                        continue
                    entry = {"role": "assistant", "content": content}

            if translated and translated[-1]["role"] == entry["role"]:
                # Merge consecutive same-role turns. The harness appends tool
                # results and then the scripted operator line; merging is valid
                # everywhere, whether or not consecutive user turns are accepted.
                translated[-1]["content"] = list(translated[-1]["content"]) + list(entry["content"])
            else:
                translated.append(entry)
        return translated

    # ------------------------------------------------------------- generation

    def generate(self, system_prompt, messages, tools, sampling):
        client = self._ensure_client()
        request = {
            "model": self.model_id,
            "system": self._system(system_prompt),
            "messages": self._messages(messages),
            "max_tokens": sampling.get("max_tokens", 4096),
            # Pinned and recorded. See harness/model_params.py.
            "thinking": self.profile["thinking"],
        }
        if self.profile["effort"] is not None:
            request["output_config"] = {"effort": self.profile["effort"]}
        if tools:
            request["tools"] = self._tools(tools)
        if self.profile["sampling_supported"]:
            # SDK 1.0.0 removed temperature, top_p and top_k from
            # Messages.create; on the models that still accept them they travel
            # in extra_body and reach the wire unchanged (probed 2026-08-23 on
            # Haiku 4.5: accepted with thinking disabled, 400 with adaptive).
            extra = {name: sampling[name] for name in ("temperature", "top_p", "top_k")
                     if sampling.get(name) is not None}
            if extra:
                request["extra_body"] = extra

        try:
            response = client.messages.create(**request)
        except Exception as error:
            raise ProviderError(f"anthropic call failed: {type(error).__name__}: {error}")

        text_parts = []
        tool_calls = []
        raw_content = []
        for block in response.content:
            raw_content.append(block.model_dump() if hasattr(block, "model_dump") else block)
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "arguments": block.input})

        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(
                response.usage, "cache_creation_input_tokens", 0) or 0,
        }

        # stop_details is populated only when stop_reason is refusal, and is null
        # for every other stop reason, so it is guarded before it is read.
        stop_details = None
        if response.stop_reason == "refusal":
            raw = getattr(response, "stop_details", None)
            if raw is not None:
                stop_details = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)

        return ModelReply(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            stop_reason=response.stop_reason,
            system_fingerprint=None,
            raw={"id": response.id, "model": response.model},
            raw_content=raw_content,
            stop_details=stop_details,
            sent_params=self.sent_parameters(sampling),
        )
