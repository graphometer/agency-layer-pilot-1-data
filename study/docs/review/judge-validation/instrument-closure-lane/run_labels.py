#!/usr/bin/env python3
"""Metered, resume-safe panel labelling and deterministic F10 queue builder.

The live path is intentionally sequential: the append-only journals are the cost
authority, and a reservation is fsynced before every provider dispatch.  Tests
inject a transport; importing this module never constructs a client or reads a
credential.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from build_packets import add_panel_split


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PACKETS = HERE / "packets"
LABELS = HERE / "labels"
GLOBAL_PRICES = REPO / "evals" / "grading" / "instrument_prices.json"
LOCAL_PRICES = HERE / "label_prices.json"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
API_KEY_ENV = "OPENROUTER_API_KEY"
DEFAULT_BUDGET = 8.00
CHAT_OVERHEAD_TOKENS = 32
MAX_ATTEMPTS = 4

ALLOWED = {
    "l1": frozenset(("qualifying", "not_qualifying", "cannot_determine")),
    "l2": frozenset(("attempt", "no_attempt", "cannot_determine")),
}


@dataclass(frozen=True)
class Labeller:
    name: str
    model: str
    max_tokens: int = 256
    extra_body: dict[str, Any] | None = None


LABELLERS = (
    # The Gemini switch is the Google passthrough shape used by the successful
    # historical gold-set runner (2026-08-24_goldset/run_labels.py:22); the
    # OpenAI SDK merges this outer dict into OpenRouter's request body, leaving
    # the provider-specific Google block nested under the body key extra_body.
    # judge.py:319-321 records 256 as the probed floor. OpenRouter's listing
    # price row matches Google Vertex; OpenRouter provider pins use listing
    # slugs (google-vertex, xai, z-ai), and --probe confirms each exact route.
    Labeller(
        "gemini-3.7-flash", "google/gemini-3.7-flash", 256,
        {
            "provider": {"only": ["google-vertex"], "allow_fallbacks": False},
            "extra_body": {"google": {"thinking_config": {"thinking_budget": 0}}},
        },
    ),
    # PM wire diagnosis 2026-08-25 (three live variants, committed in the lane
    # README): xAI's routed endpoint returns 400 "Reasoning is mandatory for
    # this endpoint and cannot be disabled" for effort=none; effort=low with
    # exclude=true answered the probe in one word at 81 output tokens.  Both
    # reasoning labellers therefore share that shape, with caps set from the
    # probe evidence at 1024 (probe usage 81 out for a short prompt; real items
    # reason more, and an item that exhausts 1024 is journalled `exhausted` and
    # recoverable via --retry-exhausted, never frozen as a null label).  The
    # historical 8192 GLM floor belonged to the JSON-label wire with reasoning
    # returned; with exclude=true the probe settled at pennies.  Fallbacks are
    # disabled for priced-route fidelity.
    Labeller(
        "grok-4.6", "x-ai/grok-4.6", 1024,
        {
            "provider": {"only": ["xai"], "allow_fallbacks": False},
            "reasoning": {"effort": "low", "exclude": True},
        },
    ),
    Labeller(
        "glm-5.3", "z-ai/glm-5.3", 1024,
        {
            "provider": {"only": ["z-ai"], "allow_fallbacks": False},
            "reasoning": {"effort": "low", "exclude": True},
        },
    ),
)

PROBE_PACKETS = {
    "l1": [{
        "request_id": "probe-l1-one-word",
        "prompt": "Is this a qualifying answer? Reply with exactly one word: qualifying",
    }],
    "l2": [{
        "request_id": "probe-l2-one-word",
        "prompt": "Is this an attempt? Reply with exactly one word: attempt",
    }],
}


class RunnerError(RuntimeError):
    pass


class BudgetError(RunnerError):
    pass


class PacketError(RunnerError):
    pass


class PriceError(RunnerError):
    pass


@dataclass(frozen=True)
class TransportResult:
    raw: str
    input_tokens: int | None = None
    output_tokens: int | None = None


Transport = Callable[[Labeller, str], TransportResult]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise PacketError(f"cannot read {path}: {exc}") from exc
    with handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PacketError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise PacketError(f"{path}:{line_number}: expected JSON object")
            rows.append(row)
    return rows


def inspect_packets(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Collect usable rows and every validation error for dry-run diagnostics."""
    rows = read_jsonl(path)
    seen: set[str] = set()
    output: list[dict[str, str]] = []
    errors: list[str] = []
    for line_number, row in enumerate(rows, 1):
        if set(row) != {"request_id", "prompt"}:
            errors.append(
                f"{path}:{line_number}: packet keys must be exactly request_id,prompt; "
                f"got {sorted(row)}"
            )
            continue
        request_id, prompt = row["request_id"], row["prompt"]
        if not isinstance(request_id, str) or not request_id or request_id in seen:
            errors.append(f"{path}:{line_number}: missing or duplicate request_id")
            continue
        if not isinstance(prompt, str) or not prompt:
            errors.append(f"{path}:{line_number}: prompt must be a non-empty string")
            continue
        # Provenance blindness per the pre-score ratification (README): the ban is on OUR
        # tree's absolute paths, not on any "/mnt/" a subject model legitimately typed inside
        # its sandbox (e.g. "ls -d /mnt/*" or a suggested "BACKUP_DEST=/mnt/backup" while
        # hunting a missing backup destination - both occur in the real corpus).
        for forbidden in ("nm-", "/mnt/vault", "/home/core"):
            if forbidden in prompt:
                errors.append(
                    f"{path}:{line_number}: blindness violation in {request_id}: "
                    f"prompt contains {forbidden!r}"
                )
        seen.add(request_id)
        output.append({"request_id": request_id, "prompt": prompt})
    return sorted(output, key=lambda row: row["request_id"]), errors


def load_packets(path: Path) -> list[dict[str, str]]:
    rows, errors = inspect_packets(path)
    if errors:
        raise PacketError(errors[0])
    return rows


def load_prices(*paths: Path) -> dict[str, dict[str, Any]]:
    prices: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PriceError(f"cannot load price table {path}: {exc}") from exc
        table = document.get("prices") if isinstance(document, dict) else None
        if not isinstance(table, dict):
            raise PriceError(f"{path}: missing prices object")
        for model, row in table.items():
            if not isinstance(row, dict):
                raise PriceError(f"{path}: malformed price for {model}")
            prices[model] = row
    return prices


def require_prices(
    prices: dict[str, dict[str, Any]], labellers: Iterable[Labeller] = LABELLERS
) -> None:
    for labeller in labellers:
        row = prices.get(labeller.model)
        if row is None:
            raise PriceError(f"unpriced model: {labeller.model}")
        for key in ("input_per_mtok", "output_per_mtok"):
            value = row.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise PriceError(f"{labeller.model}: invalid {key}")
        if not isinstance(row.get("source"), str) or not row["source"].strip():
            raise PriceError(f"{labeller.model}: missing price source")
        if row.get("placeholder") is True or "placeholder" in row["source"].lower():
            raise PriceError(f"{labeller.model}: placeholder price is not dispatchable")


def input_token_bound(prompt: str) -> int:
    # Every token contains at least one input byte; adding a fixed chat-envelope
    # allowance makes this independent of a provider tokenizer and fail-closed.
    return len(prompt.encode("utf-8")) + CHAT_OVERHEAD_TOKENS


def cost_usd(price: dict[str, Any], input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * float(price["input_per_mtok"])
        + output_tokens * float(price["output_per_mtok"])
    ) / 1_000_000


def call_bound(price: dict[str, Any], prompt: str, max_tokens: int) -> float:
    return cost_usd(price, input_token_bound(prompt), max_tokens)


def parse_answer(raw: str, track: str) -> str | None:
    answer = raw.strip()
    return answer if answer in ALLOWED[track] else None


def _json_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"


def append_journal(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_json_line(row))
        handle.flush()
        os.fsync(handle.fileno())


def journal_state(
    path: Path,
) -> tuple[set[str], set[str], set[str], float, dict[str, dict[str, Any]]]:
    """Return completed, exhausted, ambiguous, charged USD, and output rows.

    A reservation without a later terminal event for its request is ambiguous,
    even if a settlement was written. It is charged at bound and never
    redispatched. Exhausted is terminal but may be explicitly re-queued.
    """
    if not path.exists():
        return set(), set(), set(), 0.0, {}
    rows = read_jsonl(path)
    reservations: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    settlements: dict[tuple[str, int], dict[str, Any]] = {}
    completed_rows: dict[str, dict[str, Any]] = {}
    exhausted_rows: dict[str, dict[str, Any]] = {}
    last_terminal_index: dict[str, int] = {}
    for row_index, row in enumerate(rows):
        request_id = row.get("request_id")
        event = row.get("event")
        if not isinstance(request_id, str) or event not in {
            "reserved", "settled", "completed", "exhausted"
        }:
            raise RunnerError(f"malformed journal event in {path}")
        if event == "reserved":
            reservations.setdefault(request_id, []).append((row_index, row))
        elif event == "settled":
            key = (request_id, int(row.get("attempt", 0)))
            if key in settlements:
                raise RunnerError(f"duplicate settlement for {request_id} attempt {key[1]} in {path}")
            settlements[key] = row
        else:
            if event == "completed" and request_id in completed_rows:
                raise RunnerError(f"duplicate completed event for {request_id} in {path}")
            if set(row.get("output", {})) != {"request_id", "raw", "parsed"}:
                raise RunnerError(f"malformed {event} output for {request_id} in {path}")
            last_terminal_index[request_id] = row_index
            if event == "completed":
                completed_rows[request_id] = row["output"]
                exhausted_rows.pop(request_id, None)
            else:
                if request_id in completed_rows:
                    raise RunnerError(f"exhausted event follows completed {request_id} in {path}")
                exhausted_rows[request_id] = row["output"]
    completed = set(completed_rows)
    exhausted = set(exhausted_rows)
    ambiguous = {
        request_id
        for request_id, attempts in reservations.items()
        if attempts[-1][0] > last_terminal_index.get(request_id, -1)
    }
    charged = 0.0
    for request_id, attempts in reservations.items():
        terminal_index = last_terminal_index.get(request_id, -1)
        for row_index, reservation in attempts:
            attempt = int(reservation.get("attempt", 0))
            settlement = settlements.get((request_id, attempt))
            # An interrupted logical item is ambiguous even when an attempt's
            # response settlement reached disk. The frozen cost-journal rule
            # charges every reservation after its latest terminal at bound.
            if row_index > terminal_index:
                charged += float(reservation.get("bound_usd", 0.0))
            else:
                charged += float(
                    settlement.get("charged_usd") if settlement is not None
                    else reservation.get("bound_usd", 0.0)
                )
    return completed, exhausted, ambiguous, charged, completed_rows


def write_outputs(path: Path, completed_rows: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for request_id in sorted(completed_rows):
            handle.write(_json_line(completed_rows[request_id]))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def projected_cost(
    packets_by_track: dict[str, list[dict[str, str]]],
    prices: dict[str, dict[str, Any]],
    labels_dir: Path,
    labellers: Iterable[Labeller] = LABELLERS,
    retry_exhausted: bool = False,
) -> tuple[float, list[dict[str, Any]]]:
    total = 0.0
    details: list[dict[str, Any]] = []
    for labeller in labellers:
        price = prices[labeller.model]
        for track in ("l1", "l2"):
            journal = labels_dir / f"{labeller.name}__{track}.journal.jsonl"
            completed, exhausted, ambiguous, charged, _ = journal_state(journal)
            if retry_exhausted:
                retryable = exhausted - completed - ambiguous
                remaining = [
                    row for row in packets_by_track[track]
                    if row["request_id"] in retryable
                ]
            else:
                skipped = completed | exhausted | ambiguous
                remaining = [
                    row for row in packets_by_track[track]
                    if row["request_id"] not in skipped
                ]
            bound = sum(
                call_bound(price, row["prompt"], labeller.max_tokens)
                for row in remaining
            )
            total += bound
            details.append({
                "labeller": labeller.name,
                "track": track,
                "items": len(packets_by_track[track]),
                "remaining": len(remaining),
                "ambiguous": len(ambiguous),
                "exhausted": len(exhausted),
                "charged_usd": charged,
                "worst_case_usd": bound,
            })
    return total, details


def run_one(
    labeller: Labeller,
    track: str,
    packets: list[dict[str, str]],
    price: dict[str, Any],
    labels_dir: Path,
    budget: float,
    transport: Transport,
    sleep: Callable[[float], None] = time.sleep,
    prior_charged: float = 0.0,
    retry_exhausted: bool = False,
) -> tuple[int, bool]:
    journal = labels_dir / f"{labeller.name}__{track}.journal.jsonl"
    output_path = labels_dir / f"{labeller.name}__{track}.jsonl"
    completed, exhausted, ambiguous, charged, completed_rows = journal_state(journal)
    write_outputs(output_path, completed_rows)
    made = 0
    stopped_at_cap = False
    for packet in sorted(packets, key=lambda row: row["request_id"]):
        request_id = packet["request_id"]
        if request_id in completed or request_id in ambiguous:
            continue
        if retry_exhausted and request_id not in exhausted:
            continue
        if not retry_exhausted and request_id in exhausted:
            continue
        previous_attempts = [
            int(row.get("attempt", 0))
            for row in read_jsonl(journal) if row.get("request_id") == request_id
        ] if journal.exists() else []
        first_attempt = max(previous_attempts, default=0) + 1
        last_raw = ""
        parsed: str | None = None
        dispatched = False
        for offset in range(MAX_ATTEMPTS):
            attempt = first_attempt + offset
            bound = call_bound(price, packet["prompt"], labeller.max_tokens)
            if charged + bound > budget + 1e-12:
                stopped_at_cap = True
                break
            append_journal(journal, {
                "event": "reserved", "request_id": request_id, "attempt": attempt,
                "bound_usd": bound,
                "input_token_bound": input_token_bound(packet["prompt"]),
                "output_token_bound": labeller.max_tokens,
            })
            made += 1
            dispatched = True
            try:
                result = transport(labeller, packet["prompt"])
                if not isinstance(result, TransportResult):
                    raise TypeError("transport must return TransportResult")
                last_raw = result.raw
                used_input = result.input_tokens
                used_output = result.output_tokens
                if used_input is None or used_output is None:
                    settled = bound
                else:
                    actual = cost_usd(price, max(0, used_input), max(0, used_output))
                    # A provider-reported charge above our conservative bound is
                    # still charged in full; settlement must never hide spend.
                    settled = actual
                append_journal(journal, {
                    "event": "settled", "request_id": request_id, "attempt": attempt,
                    "charged_usd": settled,
                    "input_tokens": used_input, "output_tokens": used_output,
                })
                charged += settled
                parsed = parse_answer(last_raw, track)
                if parsed is not None:
                    break
            except Exception as exc:  # provider/SDK errors follow the frozen retry convention
                append_journal(journal, {
                    "event": "settled", "request_id": request_id, "attempt": attempt,
                    "charged_usd": bound, "error_type": type(exc).__name__,
                })
                charged += bound
            if offset < MAX_ATTEMPTS - 1:
                sleep(4 * (offset + 1))
        if stopped_at_cap:
            # A partially attempted item is recoverable only by the explicit
            # --retry-exhausted switch; an untouched item remains ordinary work.
            if dispatched:
                output = {"request_id": request_id, "raw": last_raw, "parsed": parsed}
                append_journal(journal, {
                    "event": "exhausted", "request_id": request_id, "output": output
                })
            break
        output = {"request_id": request_id, "raw": last_raw, "parsed": parsed}
        terminal = "completed" if parsed is not None else "exhausted"
        append_journal(journal, {"event": terminal, "request_id": request_id, "output": output})
        if terminal == "completed":
            completed_rows[request_id] = output
        write_outputs(output_path, completed_rows)
        print(
            f"{labeller.name} {track} {request_id} lane_total=${prior_charged + charged:.6f}",
            flush=True,
        )
    return made, stopped_at_cap


def openrouter_transport() -> Transport:
    # Credential access is confined to live execution; dry-run, split computation,
    # imports, and tests do not read it.
    from openai import OpenAI

    client = OpenAI(base_url=OPENROUTER_BASE, api_key=os.environ[API_KEY_ENV], timeout=240)

    def send(labeller: Labeller, prompt: str) -> TransportResult:
        response = client.chat.completions.create(**request_payload(labeller, prompt))
        raw = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return TransportResult(
            raw=raw,
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        )

    return send


def request_payload(labeller: Labeller, prompt: str) -> dict[str, Any]:
    """Build the auditable request: the packet prompt is the only message content."""
    request: dict[str, Any] = {
        "model": labeller.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": labeller.max_tokens,
        "temperature": 0.0,
    }
    if labeller.extra_body is not None:
        request["extra_body"] = labeller.extra_body
    return request


def _label_file(labels_dir: Path, labeller: Labeller, track: str) -> Path:
    return labels_dir / f"{labeller.name}__{track}.jsonl"


def load_label_map(path: Path, allowed: frozenset[str]) -> dict[str, str | None]:
    output: dict[str, str | None] = {}
    for line_number, row in enumerate(read_jsonl(path), 1):
        if set(row) != {"request_id", "raw", "parsed"}:
            raise PacketError(f"{path}:{line_number}: malformed label row")
        request_id, parsed = row["request_id"], row["parsed"]
        if not isinstance(request_id, str) or request_id in output:
            raise PacketError(f"{path}:{line_number}: duplicate or invalid request_id")
        if not isinstance(row["raw"], str) or parsed is not None and parsed not in allowed:
            raise PacketError(f"{path}:{line_number}: invalid raw/parsed value")
        output[request_id] = parsed
    return output


def compute_splits(
    packets_dir: Path = PACKETS,
    labels_dir: Path = LABELS,
    out_dir: Path = HERE,
    labellers: Iterable[Labeller] = LABELLERS,
) -> dict[str, dict[str, int]]:
    labellers = tuple(labellers)
    joins = read_jsonl(packets_dir / "packet_join.jsonl")
    join_by_request: dict[str, str] = {}
    for row in joins:
        if set(row) != {"request_id", "item_id"} or not all(
            isinstance(row.get(key), str) and row[key] for key in ("request_id", "item_id")
        ):
            raise PacketError("malformed packet_join row")
        if row["request_id"] in join_by_request:
            raise PacketError(f"duplicate join request_id: {row['request_id']}")
        join_by_request[row["request_id"]] = row["item_id"]

    summary: dict[str, dict[str, int]] = {}
    for track in ("l1", "l2"):
        packets = load_packets(packets_dir / f"{track}_packets.jsonl")
        packet_by_id = {row["request_id"]: row for row in packets}
        votes = [load_label_map(_label_file(labels_dir, labeller, track), ALLOWED[track])
                 for labeller in labellers]
        expected = set(packet_by_id)
        for labeller, mapping in zip(labellers, votes):
            if set(mapping) != expected:
                missing = len(expected - set(mapping))
                extra = len(set(mapping) - expected)
                raise PacketError(
                    f"{labeller.name} {track}: labels do not match packets "
                    f"(missing={missing}, extra={extra})"
                )
        if any(request_id not in join_by_request for request_id in expected):
            raise PacketError(f"{track}: packet_join is incomplete")

        unanimous: list[str] = []
        split: list[str] = []
        for request_id in sorted(expected):
            panel = [mapping[request_id] for mapping in votes]
            if None not in panel and "cannot_determine" not in panel and len(set(panel)) == 1:
                unanimous.append(request_id)
            else:
                split.append(request_id)

        audit = sorted(
            unanimous,
            key=lambda request_id: (
                hashlib.sha256(
                    f"{join_by_request[request_id]}-{track}-audit".encode("utf-8")
                ).hexdigest(),
                join_by_request[request_id],
                request_id,
            ),
        )[:20]
        adjudication_rows = []
        for request_id in split:
            panel = [
                f"{labeller.name}: {mapping[request_id] or 'unparseable'}"
                for labeller, mapping in zip(labellers, votes)
            ]
            adjudication_rows.append(add_panel_split(packet_by_id[request_id], panel))
        audit_rows = [packet_by_id[request_id] for request_id in audit]
        write_jsonl(out_dir / f"adjudication_queue_{track}.jsonl", adjudication_rows)
        write_jsonl(out_dir / f"audit_queue_{track}.jsonl", audit_rows)
        summary[track] = {
            "unanimous": len(unanimous), "adjudication": len(split), "audit": len(audit)
        }
    return summary


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda row: row["request_id"])
    path.write_text("".join(_json_line(row) for row in ordered), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--compute-splits", action="store_true")
    mode.add_argument("--probe", action="store_true")
    parser.add_argument("--retry-exhausted", action="store_true")
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    parser.add_argument("--packets-dir", type=Path, default=PACKETS)
    parser.add_argument("--labels-dir", type=Path, default=LABELS)
    parser.add_argument("--out-dir", type=Path, default=HERE)
    parser.add_argument("--price-file", type=Path, default=LOCAL_PRICES)
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    transport: Transport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    args = parse_args(argv)
    if args.compute_splits:
        summary = compute_splits(args.packets_dir, args.labels_dir, args.out_dir)
        for track, row in summary.items():
            print(f"{track}: unanimous={row['unanimous']} adjudication={row['adjudication']} audit={row['audit']}")
        return 0
    if not isinstance(args.budget, float) or args.budget < 0:
        raise BudgetError("budget must be non-negative")
    packet_errors: list[str] = []
    if args.probe:
        packets_by_track = PROBE_PACKETS
        labels_dir = args.labels_dir / "probe"
    else:
        labels_dir = args.labels_dir
        packets_by_track: dict[str, list[dict[str, str]]] = {}
        for track in ("l1", "l2"):
            path = args.packets_dir / f"{track}_packets.jsonl"
            if args.dry_run:
                packets_by_track[track], errors = inspect_packets(path)
                packet_errors.extend(errors)
            else:
                packets_by_track[track] = load_packets(path)
    prices = load_prices(GLOBAL_PRICES, args.price_file)
    require_prices(prices)
    projection, details = projected_cost(
        packets_by_track, prices, labels_dir, retry_exhausted=args.retry_exhausted
    )
    already_charged = sum(row["charged_usd"] for row in details)
    for row in details:
        print(
            f"{row['labeller']} {row['track']}: items={row['items']} "
            f"remaining={row['remaining']} ambiguous={row['ambiguous']} "
            f"exhausted={row['exhausted']} "
            f"worst_case=${row['worst_case_usd']:.6f}"
        )
    print(
        f"charged=${already_charged:.6f} remaining_worst_case=${projection:.6f} "
        f"budget=${args.budget:.2f}"
    )
    if packet_errors:
        raise PacketError(
            f"dry-run found {len(packet_errors)} packet validation error(s); "
            f"first: {packet_errors[0]}"
        )
    if already_charged + projection > args.budget + 1e-12:
        raise BudgetError(
            f"refusing to start: charged plus remaining worst-case "
            f"${already_charged + projection:.6f} exceeds budget ${args.budget:.2f}"
        )
    if args.dry_run:
        return 0
    sender = transport or openrouter_transport()
    stopped = False
    for labeller in LABELLERS:
        for track in ("l1", "l2"):
            # run_one accounts in its own journal. Subtract every other
            # journal's authoritative charge to enforce one lane-wide cap.
            _, current_details = projected_cost(
                packets_by_track, prices, labels_dir,
                retry_exhausted=args.retry_exhausted,
            )
            target = next(
                row for row in current_details
                if row["labeller"] == labeller.name and row["track"] == track
            )
            total_charged = sum(row["charged_usd"] for row in current_details)
            other_charged = total_charged - target["charged_usd"]
            journal_budget = args.budget - other_charged
            _, at_cap = run_one(
                labeller, track, packets_by_track[track], prices[labeller.model],
                labels_dir, journal_budget, sender, prior_charged=other_charged,
                retry_exhausted=args.retry_exhausted, sleep=sleep,
            )
            stopped = stopped or at_cap
            if at_cap:
                print(f"clean stop at budget cap during {labeller.name} {track}")
                return 2
            if args.probe:
                journal = labels_dir / f"{labeller.name}__{track}.journal.jsonl"
                _, exhausted, ambiguous, charged, completed_rows = journal_state(journal)
                output = completed_rows.get(PROBE_PACKETS[track][0]["request_id"])
                if output is None:
                    terminal_outputs = [
                        row["output"] for row in read_jsonl(journal)
                        if row.get("request_id") == PROBE_PACKETS[track][0]["request_id"]
                        and row.get("event") == "exhausted"
                    ]
                    output = terminal_outputs[-1] if terminal_outputs else {
                        "raw": "", "parsed": None,
                    }
                    state = "ambiguous" if ambiguous else "exhausted" if exhausted else "missing"
                    print(
                        f"PROBE {labeller.name} {track}: raw={json.dumps(output['raw'])} "
                        f"parsed={json.dumps(output['parsed'])} cost=${charged:.6f} state={state}"
                    )
                else:
                    print(
                        f"PROBE {labeller.name} {track}: raw={json.dumps(output['raw'])} "
                        f"parsed={json.dumps(output['parsed'])} cost=${charged:.6f}"
                    )
    if args.probe:
        failed = False
        for labeller in LABELLERS:
            for track in ("l1", "l2"):
                state = journal_state(
                    labels_dir / f"{labeller.name}__{track}.journal.jsonl"
                )
                if PROBE_PACKETS[track][0]["request_id"] not in state[4]:
                    failed = True
        return 2 if failed else 0
    return 2 if stopped else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
