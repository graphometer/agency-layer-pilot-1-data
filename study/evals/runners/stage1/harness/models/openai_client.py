"""OpenAI and OpenAI-compatible clients.

Two surfaces, because the first real smoke proved one is not enough.

    /v1/responses          the OpenAI arm (gpt-5.6 and the reasoning series)
    /v1/chat/completions    the local llama.cpp arm

The smoke returned a 400 on every gpt-5.6-terra run:

    Function tools with reasoning_effort are not supported for gpt-5.6-terra in
    /v1/chat/completions. To use function tools, use /v1/responses or set
    reasoning_effort to 'none'.

Setting effort to none was the wrong fix: this study pins and records reasoning
effort, and dropping it to satisfy a legacy endpoint would change the arm rather
than the plumbing. So the OpenAI arm moved to the Responses API, which is where
function tools and reasoning effort coexist. The local arm stays on chat
completions, which is what llama.cpp serves.

`run.json` records `api_surface`, so a reader never has to infer which endpoint
produced a run.

Shapes below were read from the installed SDK (openai 3.3.1) rather than
recalled. Two differences from chat completions bite:

  * usage is `input_tokens` / `output_tokens`, not `prompt_tokens` /
    `completion_tokens`. Reading the old names would have reported zero usage,
    which the cost meter treats as a halt, so this is a spend-control bug as
    well as a reporting one.
  * a truncated response is `status: "incomplete"` with
    `incomplete_details.reason == "max_output_tokens"`, not a finish reason.

Keys come from the environment only. A base_url is a config value, not a secret.
"""

import json
import os

from .. import affordances, model_params
from .base import ModelClient, ModelReply, ProviderError

ENV_KEY = "OPENAI_API_KEY"

# Response-only keys that must not be replayed as input. The second smoke
# returned 400 "Unknown parameter: 'input[1].status'" on turn two: the SDK's
# model_dump of an output item carries fields the server writes and will not
# read back. Whitelisting per item type is safer than blacklisting, because the
# next response-only field the API adds is then dropped by default rather than
# discovered as another 400 mid-batch.
_INPUT_KEYS_BY_ITEM_TYPE = {
    "message": ("type", "role", "content"),
    "function_call": ("type", "call_id", "name", "arguments", "id"),
    "reasoning": ("type", "id", "summary", "content", "encrypted_content"),
}
# Dropped wherever they appear, including inside content blocks.
_RESPONSE_ONLY_KEYS = frozenset(["status", "annotations", "logprobs", "phase"])


def _scrub_for_input(node):
    """Strip response-only keys from a replayed output item, at every depth."""
    if isinstance(node, list):
        return [_scrub_for_input(item) for item in node]
    if not isinstance(node, dict):
        return node
    allowed = _INPUT_KEYS_BY_ITEM_TYPE.get(node.get("type"))
    cleaned = {}
    for key, value in node.items():
        if key in _RESPONSE_ONLY_KEYS:
            continue
        if allowed is not None and key not in allowed:
            continue
        if value is None:
            continue
        cleaned[key] = _scrub_for_input(value)
    return cleaned


# The local llama.cpp chat template raises on any other value and the endpoint
# returns HTTP 500, so the harness refuses to send one rather than discovering it
# mid-batch (models/MODEL_REFERENCE.md, Qwen3.8-27B client traps).
LOCAL_REASONING_EFFORTS = ("xhigh", "medium", "low")


class OpenAIResponsesClient(ModelClient):
    """The OpenAI arm, on /v1/responses."""

    provider = "openai"
    endpoint = None
    api_surface = "responses"

    def __init__(self, model_id, base_url=None, max_retries=2, timeout=600,
                 profile_overrides=None):
        self.model_id = model_id
        self.endpoint = base_url
        self.seed_supported = False   # the Responses API takes no seed
        self.max_retries = max_retries
        self.timeout = timeout
        self.profile = model_params.openai_profile(model_id, "openai", profile_overrides)
        self._client = None

    def sent_parameters(self, sampling):
        record = {
            "api_surface": self.api_surface,
            "thinking": self.profile["thinking"],
            "reasoning_effort": self.profile["reasoning_effort"],
            "sampling_sent": {},
            "max_tokens_field": "max_output_tokens",
            "max_tokens": sampling.get("max_tokens", 4096),
            "prompt_caching": "automatic",
            "tool_schema_rendering": "as_published",
        }
        if self.profile["sampling_supported"]:
            for name in ("temperature", "top_p"):
                if sampling.get(name) is not None:
                    record["sampling_sent"][name] = sampling[name]
        return record

    def count_prompt_tokens(self, system_prompt, messages, tools):
        """tiktoken over everything that will be serialized into the request.

        The Responses API has no count endpoint, so the tokenizer is run locally
        over the instructions, the input items and the tool definitions. Framing
        tokens the serialization does not show are covered by counting the JSON
        rather than the bare text, which is longer than the wire form.
        """
        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(self.model_id)
            except Exception:
                encoding = tiktoken.get_encoding("o200k_base")
            payload = json.dumps(
                {"instructions": system_prompt,
                 "input": self._input_items(messages),
                 "tools": self._tools(tools) if tools else []},
                ensure_ascii=False, default=str)
            return len(encoding.encode(payload))
        except Exception:
            return None

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
            import openai
        except ImportError as error:
            raise ProviderError(f"the openai SDK is not installed: {error}")
        kwargs = {"api_key": key, "max_retries": self.max_retries, "timeout": self.timeout}
        if self.endpoint:
            kwargs["base_url"] = self.endpoint
        self._client = openai.OpenAI(**kwargs)
        return self._client

    @staticmethod
    def _tools(tools):
        """Responses tool definitions are flat: no nested function object."""
        return [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
            for tool in tools
        ]

    @staticmethod
    def _input_items(messages):
        """The harness's message list as Responses input items.

        Assistant turns replay the provider's own output items verbatim when it
        gave them, so reasoning items round-trip. Dropping them on a reasoning
        model throws away the state the next turn is supposed to build on.
        """
        items = []
        for message in messages:
            if message["role"] == "user":
                for block in message["content"]:
                    if block["type"] == "text":
                        items.append({"role": "user",
                                      "content": [{"type": "input_text", "text": block["text"]}]})
                    elif block["type"] == "tool_result":
                        items.append({"type": "function_call_output",
                                      "call_id": block["tool_call_id"],
                                      "output": str(block["content"])})
                continue

            raw = message.get("raw_content")
            if raw:
                # Replayed verbatim apart from the response-only fields the
                # server writes and will not read back.
                items.extend(_scrub_for_input(item) for item in raw)
                continue
            if message.get("text"):
                items.append({"role": "assistant",
                              "content": [{"type": "output_text", "text": message["text"]}]})
            for call in message.get("tool_calls", []):
                items.append({"type": "function_call", "call_id": call["id"],
                              "name": call["name"],
                              "arguments": json.dumps(call["arguments"])})
        return items

    def generate(self, system_prompt, messages, tools, sampling):
        client = self._ensure_client()
        request = {
            "model": self.model_id,
            "instructions": system_prompt,
            "input": self._input_items(messages),
            "max_output_tokens": sampling.get("max_tokens", 4096),
            "store": False,
        }
        if tools:
            request["tools"] = self._tools(tools)
            request["tool_choice"] = "auto"
        if self.profile["reasoning_effort"]:
            request["reasoning"] = {"effort": self.profile["reasoning_effort"]}
        if self.profile["sampling_supported"]:
            for name in ("temperature", "top_p"):
                if sampling.get(name) is not None:
                    request[name] = sampling[name]

        try:
            response = client.responses.create(**request)
        except Exception as error:
            raise ProviderError(f"openai responses call failed: "
                                f"{type(error).__name__}: {error}")

        text_parts = []
        tool_calls = []
        raw_content = []
        refusal_text = None
        for item in response.output:
            raw_content.append(item.model_dump() if hasattr(item, "model_dump") else item)
            kind = getattr(item, "type", None)
            if kind == "function_call":
                try:
                    arguments = json.loads(item.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {"__malformed__": item.arguments}
                tool_calls.append({"id": item.call_id, "name": item.name,
                                   "arguments": arguments})
            elif kind == "message":
                for block in getattr(item, "content", []) or []:
                    block_type = getattr(block, "type", None)
                    if block_type == "output_text":
                        text_parts.append(block.text)
                    elif block_type == "refusal":
                        refusal_text = block.refusal

        usage_object = getattr(response, "usage", None)
        input_details = getattr(usage_object, "input_tokens_details", None)
        usage = {
            "input_tokens": getattr(usage_object, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage_object, "output_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(input_details, "cached_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(input_details, "cache_write_tokens", 0) or 0,
        }

        stop_reason = "end_turn"
        stop_details = None
        if refusal_text:
            stop_reason = "refusal"
            stop_details = {"type": "refusal", "explanation": str(refusal_text)[:2000]}
        elif getattr(response, "status", None) == "incomplete":
            reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
            stop_reason = "max_tokens" if reason == "max_output_tokens" else str(reason)
        elif tool_calls:
            stop_reason = "tool_use"

        return ModelReply(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            stop_reason=stop_reason,
            # The Responses API returns no system_fingerprint.
            system_fingerprint=None,
            raw={"id": response.id, "model": response.model},
            raw_content=raw_content,
            stop_details=stop_details,
            sent_params=self.sent_parameters(sampling),
        )


class OpenAICompatibleClient(ModelClient):
    """The local llama.cpp arm, on /v1/chat/completions.

    Two endpoint-specific traps, both from models/MODEL_REFERENCE.md and both now
    handled rather than discovered mid-batch:

      * Qwen3.8-27B thinks by default and has a real off switch,
        `chat_template_kwargs {"enable_thinking": false}`. R14 fixes the local
        model at thinking off, and this is what actually turns it off; the smoke
        still proves it on the wire rather than trusting the flag.
      * `reasoning_effort` accepts only xhigh, medium or low. Any other value
        returns HTTP 500, because the chat template raises. The client refuses to
        send anything else.
    """

    api_surface = "chat_completions"

    def __init__(self, model_id, provider="local", base_url=None, max_retries=2, timeout=600,
                 profile_overrides=None, api_key_env=None, extra_body=None):
        self.model_id = model_id
        self.provider = provider
        self.endpoint = base_url
        self.seed_supported = True
        self.max_retries = max_retries
        self.timeout = timeout
        self.api_key_env = api_key_env
        self.request_overrides = dict(extra_body or {})
        self.profile = model_params.openai_profile(model_id, provider, profile_overrides)
        self._client = None
        if provider == "openai_compatible" and not self.endpoint:
            raise ProviderError("an openai_compatible client needs base_url in the config")
        if provider == "openai_compatible" and not self.api_key_env:
            raise ProviderError(
                "an openai_compatible client needs api_key_env naming the environment "
                "variable that holds its key"
            )
        effort = self.profile.get("reasoning_effort")
        if effort is not None and effort not in LOCAL_REASONING_EFFORTS:
            raise ProviderError(
                f"reasoning_effort {effort!r} is not accepted by the local endpoint, which takes "
                f"only {', '.join(LOCAL_REASONING_EFFORTS)} and returns HTTP 500 on anything else."
            )

    def count_prompt_tokens(self, system_prompt, messages, tools):
        """llama.cpp's own /tokenize endpoint, which is exact for this server."""
        if self.provider != "local":
            return None
        try:
            import urllib.request

            payload = json.dumps(
                {"content": json.dumps(
                    {"messages": self._messages(system_prompt, messages),
                     "tools": self._tools(tools) if tools else []},
                    ensure_ascii=False, default=str)}
            ).encode("utf-8")
            url = self.endpoint.rstrip("/").removesuffix("/v1") + "/tokenize"
            request = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return len(json.loads(response.read()).get("tokens", []))
        except Exception:
            return None

    def _effective_max_tokens(self, sampling):
        """The requested cap, raised to the profile's floor where a provider needs one.

        Recorded in sampling_sent as the value actually sent (PM patch 2026-08-23,
        Gemini floor; see model_params).
        """
        requested = int(sampling.get("max_tokens", 4096))
        floor = int(self.profile.get("min_max_tokens", 0) or 0)
        return max(requested, floor)

    def _thinking_kwargs(self):
        """The chat template switch that actually turns thinking off."""
        if self.profile.get("thinking") == "off":
            return {"chat_template_kwargs": {"enable_thinking": False}}
        return {}

    def sent_parameters(self, sampling):
        body_sent = dict(self._thinking_kwargs())
        body_sent.update(self.request_overrides)
        record = {
            "api_surface": self.api_surface,
            "thinking": self.profile["thinking"],
            "reasoning_effort": self.profile["reasoning_effort"],
            "sampling_sent": {},
            "max_tokens_field": "max_tokens",
            "max_tokens": self._effective_max_tokens(sampling),
            "prompt_caching": "none",
            "extra_body": body_sent,
            # This endpoint builds a GBNF grammar from the tool parameter
            # schemas and cannot parse the published affordance schemas.
            "tool_schema_rendering": ("flattened" if self.provider == "local"
                                      else "as_published"),
        }
        if self.profile["sampling_supported"]:
            for name in ("temperature", "top_p"):
                if sampling.get(name) is not None:
                    record["sampling_sent"][name] = sampling[name]
        if self.request_overrides:
            record["sampling_sent"]["extra_body"] = self.request_overrides
        if sampling.get("seed") is not None:
            record["sampling_sent"]["seed"] = sampling["seed"]
        return record

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if self.provider == "local":
            # A local llama.cpp server ignores the key; the SDK still requires a
            # non-empty string. No secret is involved and none is read.
            key = "local-endpoint-no-key"
            if not self.endpoint:
                raise ProviderError("the local arm needs a base_url in the config")
        else:
            if not self.api_key_env:
                raise ProviderError(
                    "an openai_compatible client needs api_key_env naming the environment "
                    "variable that holds its key"
                )
            key = os.environ.get(self.api_key_env)
            if not key:
                raise ProviderError(
                    f"{self.api_key_env} is not set in the environment. The harness reads keys "
                    "from the environment only."
                )
        try:
            import openai
        except ImportError as error:
            raise ProviderError(f"the openai SDK is not installed: {error}")
        kwargs = {"api_key": key, "max_retries": self.max_retries, "timeout": self.timeout}
        if self.endpoint:
            kwargs["base_url"] = self.endpoint
        self._client = openai.OpenAI(**kwargs)
        return self._client

    def _tools(self, tools):
        """Tool definitions with grammar-safe parameters.

        llama.cpp builds a GBNF grammar from these schemas, and the published
        affordance schemas defeat its converter. The flattening keeps every
        property, type, enum and description, and drops only what a grammar
        cannot express. Recorded in run.json as tool_schema_rendering.
        """
        source = (affordances.flatten_tools_for_grammar(tools)
                  if self.provider == "local" else tools)
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in source
        ]

    @staticmethod
    def _messages(system_prompt, messages):
        translated = [{"role": "system", "content": system_prompt}]
        for message in messages:
            if message["role"] == "user":
                for block in message["content"]:
                    if block["type"] == "text":
                        translated.append({"role": "user", "content": block["text"]})
                    elif block["type"] == "tool_result":
                        translated.append({"role": "tool",
                                           "tool_call_id": block["tool_call_id"],
                                           "content": block["content"]})
            else:
                entry = {"role": "assistant", "content": message.get("text") or None}
                if message.get("tool_calls"):
                    entry["tool_calls"] = [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {"name": call["name"],
                                         "arguments": json.dumps(call["arguments"])},
                        }
                        for call in message["tool_calls"]
                    ]
                translated.append(entry)
        return translated

    def generate(self, system_prompt, messages, tools, sampling):
        client = self._ensure_client()
        request = {
            "model": self.model_id,
            "messages": self._messages(system_prompt, messages),
            "max_tokens": self._effective_max_tokens(sampling),
        }
        if tools:
            request["tools"] = self._tools(tools)
            request["tool_choice"] = "auto"
        if self.profile["sampling_supported"]:
            for name in ("temperature", "top_p"):
                if sampling.get(name) is not None:
                    request[name] = sampling[name]
        effort = self.profile.get("reasoning_effort")
        if effort in LOCAL_REASONING_EFFORTS:
            request["reasoning_effort"] = effort
        if sampling.get("seed") is not None:
            request["seed"] = sampling["seed"]
        extra_body = self._thinking_kwargs()
        if extra_body:
            request["extra_body"] = extra_body
        request.update(self.request_overrides)

        try:
            response = client.chat.completions.create(**request)
        except Exception as error:
            raise ProviderError(f"{self.provider} call failed: {type(error).__name__}: {error}")

        choice = response.choices[0]
        message = choice.message
        tool_calls = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"__malformed__": call.function.arguments}
            tool_calls.append({"id": call.id, "name": call.function.name,
                               "arguments": arguments})

        usage_object = getattr(response, "usage", None)
        usage = {
            "input_tokens": getattr(usage_object, "prompt_tokens", 0) or 0,
            "output_tokens": getattr(usage_object, "completion_tokens", 0) or 0,
        }
        stop_reason = choice.finish_reason
        stop_details = None
        refusal = getattr(message, "refusal", None)
        if refusal:
            stop_reason = "refusal"
            stop_details = {"type": "refusal", "explanation": str(refusal)[:2000]}
        elif stop_reason == "content_filter":
            stop_reason = "refusal"
            stop_details = {"type": "refusal", "category": "content_filter"}
        return ModelReply(
            text=message.content or "",
            tool_calls=tool_calls,
            usage=usage,
            stop_reason=stop_reason,
            system_fingerprint=getattr(response, "system_fingerprint", None),
            # raw.model is the endpoint's own claim of what served the call, and
            # raw.provider is OpenRouter's serving-provider echo (absent on other
            # endpoints). Both are persisted per turn and in run.json (R54: this
            # is the on-disk evidence that the provider pin was honored).
            raw={"id": response.id, "model": response.model,
                 "provider": getattr(response, "provider", None)},
            stop_details=stop_details,
            sent_params=self.sent_parameters(sampling),
        )
