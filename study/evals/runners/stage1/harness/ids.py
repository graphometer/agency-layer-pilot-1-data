"""Deterministic identifiers, timestamps and per-run seeds.

Every id a run needs is derived from the run's own coordinates, so a batch is
reproducible and two runs of the same cell in the same batch never collide.
"""

import datetime
import hashlib

# The seed space accepted by the OpenAI seed parameter and by llama.cpp.
SEED_MODULUS = 2**31 - 1


def utc_now() -> str:
    """RFC 3339 UTC timestamp with millisecond precision, as the schema wants."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def run_id(batch_id, scenario_id, condition, model_id, repeat_index) -> str:
    """A run id that names its own cell, so results/ is readable without an index."""
    safe_model = model_id.replace("/", "-").replace(":", "-")
    return f"{scenario_id}__{condition}__{safe_model}__r{repeat_index}"


def _digest(*parts) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def run_seed(batch_id, scenario_id, condition, model_id, repeat_index) -> int:
    """Per-run seed, derived so the whole batch replays from the batch id alone.

    Methods 4.6 wants run order randomized and every run reproducible; a derived
    seed gives both without a seed file that can drift from the results.
    """
    raw = _digest(batch_id, scenario_id, condition, model_id, repeat_index, "seed")
    return int(raw[:16], 16) % SEED_MODULUS


def tool_order_seed(batch_id, scenario_id, condition, model_id, repeat_index) -> int:
    """A seed for tool ordering that is independent of the sampling seed.

    Kept separate so that changing the sampling seed in a replication does not
    silently change the tool order as well (methods 4.10).
    """
    raw = _digest(batch_id, scenario_id, condition, model_id, repeat_index, "tool_order")
    return int(raw[:16], 16) % SEED_MODULUS


def session_id(run_identifier) -> str:
    return f"sess-{_digest(run_identifier, 'session')[:16]}"


def instance_id(run_identifier, generation=0) -> str:
    return f"inst-{_digest(run_identifier, 'instance', generation)[:16]}"


def event_id(run_identifier, sequence) -> str:
    return f"evt-{_digest(run_identifier, 'event', sequence)[:16]}"


def tool_call_id(run_identifier, turn, index) -> str:
    return f"call-{_digest(run_identifier, 'call', turn, index)[:12]}"


def task_id(run_identifier, generation=0) -> str:
    return f"task-{_digest(run_identifier, 'task', generation)[:12]}"
