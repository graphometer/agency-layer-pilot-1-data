"""Config and scenario loading.

Two rules this module exists to enforce.

No key is ever in a file. The config names models, providers, prices, limits and
a base_url for the local endpoint. ANTHROPIC_API_KEY and OPENAI_API_KEY are read
from the environment by the provider clients and by nothing else. Loading a
config that carries anything key-shaped is a hard error rather than a warning,
because a warning is how a key reaches a git history.

A scenario is read, never written. The fixture is copied per run; the scenario
folder is opened read-only and no run touches it.
"""

import os
import re

from . import cost

import yaml

# Matched against the key name with separators and case stripped, so api_key,
# apiKey and API-KEY all land on "apikey". Exact names, not substrings: a
# substring rule rejects max_tokens, which is a sampling parameter.
FORBIDDEN_CONFIG_KEYS = frozenset(
    [
        "apikey",
        "anthropicapikey",
        "openaiapikey",
        "secret",
        "secretkey",
        "password",
        "passwd",
        "token",
        "authtoken",
        "accesstoken",
        "bearertoken",
        "authorization",
        "credential",
        "credentials",
        "privatekey",
        "key",
    ]
)

# Value-side check, which is the one that actually catches a pasted key.
KEY_SHAPED_VALUE = re.compile(r"^(sk-|sk-ant-|sk-proj-|xai-|gsk_|hf_|ghp_|Bearer\s)")


class Scenario:
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)
        with open(os.path.join(self.directory, "scenario.yaml"), "r", encoding="utf-8") as handle:
            self.raw = yaml.safe_load(handle)

        self.scenario_id = self.raw["id"]
        self.family = self.raw["family"]
        self.variant = self.raw["variant"]
        self.title = self.raw["title"]
        self.task = self.raw["task"].strip()

        ground_truth = self.raw.get("ground_truth", {})
        self.expected = ground_truth.get("expected")
        self.consequential_action = ground_truth.get("consequential_action")
        self.fabrication_marker = ground_truth.get("fabrication_marker")
        self.success_check = ground_truth.get("success_check")
        self.impossible = bool(ground_truth.get("impossible", False))
        # 1 when running the shipped script is a correct part of a benign task,
        # so that "run this script" does not predict a trap (SCENARIO_CONTRACT,
        # notes added after the 2026-08-22 review).
        self.expected_consequential_runs = cost._count(
            ground_truth.get("expected_consequential_runs", 0),
            f"{self.scenario_id}.ground_truth.expected_consequential_runs")

        self.post_invocation = self.raw.get("post_invocation", {})
        raw_limits = self.raw.get("limits", {})
        self.limits = {
            "max_turns": cost._count(raw_limits.get("max_turns", 12),
                                      f"{self.scenario_id}.limits.max_turns"),
            "max_tool_calls": cost._count(raw_limits.get("max_tool_calls", 30),
                                           f"{self.scenario_id}.limits.max_tool_calls"),
            "wall_seconds": cost._count(raw_limits.get("wall_seconds", 300),
                                         f"{self.scenario_id}.limits.wall_seconds"),
        }
        if any(value <= 0 for value in self.limits.values()):
            raise ValueError(f"{self.scenario_id}: scenario limits must be positive integers")
        self.neutrality_check = self.raw.get("neutrality_check")

        self.fixture_dir = os.path.join(self.directory, "fixture")
        self.check_path = os.path.join(self.directory, "check.py")
        for required in (self.fixture_dir, self.check_path):
            if not os.path.exists(required):
                raise FileNotFoundError(f"{self.scenario_id} is missing {required}")

    def __repr__(self):
        return f"Scenario({self.scenario_id}, family {self.family})"


def load_scenarios(root):
    scenarios = []
    for name in sorted(os.listdir(root)):
        directory = os.path.join(root, name)
        if os.path.isfile(os.path.join(directory, "scenario.yaml")):
            scenarios.append(Scenario(directory))
    return scenarios


def _normalize_key(key):
    return "".join(character for character in str(key).lower() if character.isalnum())


def _assert_no_secrets(node, path="config"):
    """Refuse to load a config that carries anything credential-shaped.

    A hard error, not a warning, because a warning is how a key reaches a git
    history. Both the key name and the value are checked: the name check catches
    a field someone added on purpose, and the value check catches a key pasted
    into a field with an innocent name.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if _normalize_key(key) in FORBIDDEN_CONFIG_KEYS:
                raise ValueError(
                    f"{path}.{key} is a credential-shaped field. The harness reads "
                    "ANTHROPIC_API_KEY and OPENAI_API_KEY from the environment only, "
                    "and no key belongs in a config file."
                )
            _assert_no_secrets(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _assert_no_secrets(item, f"{path}[{index}]")
    elif isinstance(node, str) and KEY_SHAPED_VALUE.match(node):
        # The value is not echoed back, since that would put it in a traceback.
        raise ValueError(
            f"{path} holds a value that looks like an API key. Remove it: the "
            "harness reads keys from the environment only."
        )


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    _assert_no_secrets(config)
    _validate_accounting_controls(config, path)
    return config


def _validate_accounting_controls(config, path="config"):
    """Audit item 5: reject numeric bypasses when configuration is loaded."""
    if not isinstance(config, dict):
        raise ValueError(f"{path}: config must be an object")
    spend = config.get("spend") or {}
    ceiling = cost._finite_number(  # The meter repeats every one of these checks.
        spend.get("hard_ceiling_usd", 600.0),
        f"{path}.spend.hard_ceiling_usd", positive=True)
    cost._finite_number(spend.get("report_at_usd", 300.0),
                        f"{path}.spend.report_at_usd", positive=True)
    checkpoints = spend.get("checkpoints_usd", ()) or ()
    if not isinstance(checkpoints, (list, tuple)):
        raise ValueError(f"{path}.spend.checkpoints_usd must be a list")
    values = [cost._finite_number(value, f"{path}.spend.checkpoints_usd[{index}]",
                                  positive=True)
              for index, value in enumerate(checkpoints)]
    if any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError(f"{path}.spend.checkpoints_usd must be strictly increasing")
    if any(value >= ceiling for value in values):
        raise ValueError(f"{path}: every spend checkpoint must be below the hard ceiling")

    prices = config.get("prices") or {}
    if not isinstance(prices, dict):
        raise ValueError(f"{path}.prices must be an object")
    for model_id, entry in prices.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}.prices.{model_id} must be an object")
        for name, value in entry.items():
            if str(name).endswith("_per_mtok"):
                cost._finite_number(value, f"{path}.prices.{model_id}.{name}",
                                    non_negative=True)

    sampling = config.get("sampling") or {}
    if "max_tokens" in sampling:
        cost._count(sampling["max_tokens"], f"{path}.sampling.max_tokens")
    for name in ("command_timeout", "malformed_tolerance"):
        if name in config:
            cost._count(config[name], f"{path}.{name}")


def build_model(model_config, allow_live=False):
    """Instantiate a model client from its config entry.

    Live clients refuse to build unless allow_live is set, so a mock batch can
    never reach a provider by accident.
    """
    provider = model_config["provider"]
    model_id = model_config["model_id"]

    if provider == "mock":
        from .models.mock import MockModel

        return MockModel.from_file(model_config["script"], model_id=model_id)

    if not allow_live:
        raise RuntimeError(
            f"model {model_id} has provider {provider}, which calls a real endpoint. "
            "Pass allow_live to build it."
        )

    if provider == "anthropic":
        from .models.anthropic_client import AnthropicClient

        return AnthropicClient(model_id, profile_overrides=model_config.get("profile_overrides"))

    if provider == "openai":
        # /v1/responses. Function tools and reasoning_effort are not supported
        # together on /v1/chat/completions for gpt-5.6, which is what the first
        # real smoke returned a 400 on.
        from .models.openai_client import OpenAIResponsesClient

        return OpenAIResponsesClient(
            model_id, base_url=model_config.get("base_url"),
            profile_overrides=model_config.get("profile_overrides"),
        )

    if provider == "local":
        # /v1/chat/completions, which is what llama.cpp serves.
        from .models.openai_client import OpenAICompatibleClient

        profile_overrides = dict(model_config.get("profile_overrides") or {})
        if "enable_thinking" in model_config:
            profile_overrides["thinking"] = (
                "on" if bool(model_config["enable_thinking"]) else "off"
            )
        return OpenAICompatibleClient(
            model_id, provider=provider, base_url=model_config.get("base_url"),
            profile_overrides=profile_overrides,
        )

    if provider == "openai_compatible":
        from .models.openai_client import OpenAICompatibleClient

        return OpenAICompatibleClient(
            model_id,
            provider=provider,
            base_url=model_config.get("base_url"),
            api_key_env=model_config.get("api_key_env"),
            extra_body=model_config.get("extra_body"),
            profile_overrides=model_config.get("profile_overrides"),
        )

    raise ValueError(f"unknown provider: {provider}")
