"""Candidate scoring runs for the instrument-closure lane (LANE_PROTOCOL sections 2, 7, 9).

Runs the closed candidate set over the frozen L1 packets, two passes each at the locked
configurations, plus the timing instrument's router half (the frozen production classifier,
prompt ``prose-llm-prompt-0.3.0``, ``mistral-medium-2604`` at temperature 0), and assembles the
timing pass files.  No candidate, prompt variant, or threshold beyond the frozen list.

Frozen production pieces are imported, never re-implemented: ``judge.parse_verdict`` (the strict
first-line parser the seated judges run under), ``llm_classifier.FROZEN_PROMPT`` /
``parse_route`` / ``FROZEN_SAMPLING`` (the route classifier), and ``blind.clean_text`` via
``build_frame`` (the router's production input normalization).

Metering follows ``run_labels.py``'s fail-closed journal design (its functions are imported):
reserve-before-dispatch at bound, journals are the sole resume authority, exhausted is terminal
but re-queueable, and the LANE cap (30 USD, section 9) is enforced across the label journals and
every candidate journal together.  Dispatch order is cheapest-first (router, mistral, minimax) so
an interruption strands the least; each candidate's incompleteness fails its seat only.

Timing assembly (section 2 turn-level definition): a tool-channel gold item is an intervention
signal deterministically; a prose item routes through the classifier and counts iff the route is
``on_clarify``, ``on_dissent`` or ``on_decline``; a prose item with no prose text short-circuits
to ``none`` exactly as production ``classify("")`` does, with no call.  A router item exhausted
or unparseable after retries becomes ``cannot_determine`` (the strict convention counts it
against the instrument).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "evals" / "grading"))
sys.path.insert(0, str(REPO / "evals" / "runners" / "stage1" / "harness"))

from build_frame import clean_text  # noqa: E402  (re-exported from blind.py)
from judge import parse_verdict  # noqa: E402
from llm_classifier import FROZEN_PROMPT, FROZEN_SAMPLING, parse_route  # noqa: E402
from run_labels import (  # noqa: E402
    BudgetError,
    PriceError,
    RunnerError,
    append_journal,
    call_bound,
    cost_usd,
    input_token_bound,
    journal_state,
    load_prices,
    read_jsonl,
    write_outputs,
)

PACKETS = HERE / "packets"
LABELS = HERE / "labels"
OUT = HERE / "candidates"
PRICE_FILE = HERE / "candidate_prices.json"
LANE_CAP_USD = 30.00
# 4 matches run_labels.py, not production's CLASSIFIER_MAX_ATTEMPTS = 3; after
# exhaustion the lane answers cannot_determine under the strict convention and
# NEVER falls back to the keyword route (Grok post-label finding 12, note only).
MAX_ATTEMPTS = 4
INTERVENTION_ROUTES = {"on_clarify", "on_dissent", "on_decline"}


@dataclass(frozen=True)
class Endpoint:
    name: str
    model: str
    base_url: str
    api_key_env: str
    max_tokens: int
    temperature: float = 0.0
    stop: tuple[str, ...] | None = None
    price_key: str = ""

    def price_id(self) -> str:
        return self.price_key or self.model


# The locked seat configurations (LANE_PROTOCOL section 2; evals/grading/judge.py
# COMPATIBLE_JUDGE_CONFIGS is the source of record for the seated pair).
CANDIDATES = (
    Endpoint(
        name="mistral-medium-2604",
        model="mistral-medium-2604",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        max_tokens=8,
        stop=("\n",),
    ),
    Endpoint(
        name="minimax-m3",
        model="minimax/minimax-m3",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        max_tokens=8192,
        stop=None,
    ),
)

ROUTER = Endpoint(
    name="router-mistral-medium-2604",
    model="mistral-medium-2604",
    base_url="https://api.mistral.ai/v1",
    api_key_env="MISTRAL_API_KEY",
    max_tokens=int(FROZEN_SAMPLING["max_tokens"]),
    temperature=float(FROZEN_SAMPLING["temperature"]),
    stop=None,
    price_key="mistral-medium-2604",
)


def router_request_id(item_id: str) -> str:
    return hashlib.sha256(f"{item_id}-router".encode()).hexdigest()[:24]


def load_gold_and_join() -> tuple[list[dict[str, Any]], dict[str, str]]:
    gold = read_jsonl(HERE / "goldset_lane.jsonl")
    if len(gold) != 461:
        raise RunnerError(f"gold set changed shape: {len(gold)}")
    join = {}
    for row in read_jsonl(PACKETS / "packet_join.jsonl"):
        join[str(row["request_id"])] = str(row["item_id"])
    return gold, join


def prose_router_inputs(gold: list[dict[str, Any]]) -> dict[str, str]:
    """item_id -> production router input text for every prose-channel gold item.

    Recomputed from the committed source runs with the frozen normalization
    (``clean_text`` on the raw assistant turn), then cross-checked against the
    frozen frame's ``has_prose_text`` bit for every item.  Empty text means the
    production short-circuit (route ``none``) and never a paid call.
    """
    frame_bits = {
        (str(row["run_id"]), int(row["turn_index"])): (
            bool(row["has_prose_text"]),
            str(row["source_run_path"]),
        )
        for row in read_jsonl(HERE / "frame.jsonl")
    }
    transcripts: dict[str, dict[int, str]] = {}
    inputs: dict[str, str] = {}
    for row in gold:
        if row["channel"] != "prose":
            continue
        if row.get("synthetic"):
            raise RunnerError(f"{row['item_id']}: synthetic item on the prose channel")
        run_id = str(row["run_id"])
        turn_index = int(row["turn_index"])
        key = (run_id, turn_index)
        if key not in frame_bits:
            raise RunnerError(f"{row['item_id']}: no frame row for {key}")
        has_prose, source_path = frame_bits[key]
        if run_id not in transcripts:
            raw = read_jsonl(REPO / source_path / "transcript.jsonl")
            transcripts[run_id] = {
                int(r.get("index", ordinal)): str(r.get("text", ""))
                for ordinal, r in enumerate(raw)
                if r.get("role") == "assistant"
            }
        text = clean_text(transcripts[run_id].get(turn_index, ""))
        if bool(text) != has_prose:
            raise RunnerError(
                f"{row['item_id']}: recomputed prose presence {bool(text)} contradicts the "
                f"frozen frame's has_prose_text {has_prose}; refusing"
            )
        inputs[str(row["item_id"])] = text
    return inputs


def lane_charged_so_far(journal_paths: list[Path]) -> float:
    total = 0.0
    for path in journal_paths:
        _, _, _, charged, _ = journal_state(path)
        total += charged
    return total


def all_journals() -> list[Path]:
    # labels/probe/ journals are paid lane spend too (Grok post-label finding 14).
    paths = sorted(LABELS.glob("*.journal.jsonl"))
    paths.extend(sorted((LABELS / "probe").glob("*.journal.jsonl")))
    paths.extend(sorted(OUT.glob("*.journal.jsonl")))
    return paths


def validate_prices(prices: dict[str, dict[str, Any]]) -> None:
    """Refuse placeholder or malformed rows before any dispatch (finding 6)."""
    for endpoint in (*CANDIDATES, ROUTER):
        row = prices.get(endpoint.price_id())
        if row is None:
            raise PriceError(f"no committed price row for {endpoint.price_id()}")
        for key in ("input_per_mtok", "output_per_mtok"):
            value = row.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                raise PriceError(f"{endpoint.price_id()}: {key} must be a positive number")
        source = str(row.get("source", ""))
        if not source or "placeholder" in source.lower():
            raise PriceError(f"{endpoint.price_id()}: price row lacks a verified source")


def require_freeze() -> None:
    """No candidate or router answer may exist before gold freezes (finding 3).

    LANE_PROTOCOL section 9 steps 3-4: gold freezes with its hash recorded first.
    The gate also checks the frozen hash still matches the file on disk.
    """
    freeze_path = HERE / "GOLD_FREEZE.json"
    gold_path = HERE / "gold_final.jsonl"
    if not freeze_path.exists() or not gold_path.exists():
        raise RunnerError(
            "GOLD_FREEZE.json / gold_final.jsonl not found: gold has not frozen, so no "
            "candidate or router call may be made (LANE_PROTOCOL section 9)."
        )
    frozen = json.loads(freeze_path.read_text())
    actual = hashlib.sha256(gold_path.read_bytes()).hexdigest()
    if frozen.get("gold_final_sha256") != actual:
        raise RunnerError("gold_final.jsonl does not match GOLD_FREEZE.json; refusing")


def make_client(endpoint: Endpoint):
    from openai import OpenAI

    api_key = os.environ.get(endpoint.api_key_env)
    if not api_key:
        raise RunnerError(f"{endpoint.api_key_env} is not set; source the .env first")
    return OpenAI(base_url=endpoint.base_url, api_key=api_key, timeout=240)


def one_call(
    client, endpoint: Endpoint, system: str | None, user: str
) -> tuple[str, int | None, int | None]:
    """Return (content, input_tokens, output_tokens); missing usage stays None.

    Settlement decides what missing usage costs (the reserved bound, never 0) —
    the run_labels.py convention this module imports (Grok post-label finding 1).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    kwargs: dict[str, Any] = dict(
        model=endpoint.model,
        messages=messages,
        max_tokens=endpoint.max_tokens,
        temperature=endpoint.temperature,
    )
    if endpoint.stop:
        kwargs["stop"] = list(endpoint.stop)
    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    raw_input = getattr(usage, "prompt_tokens", None)
    raw_output = getattr(usage, "completion_tokens", None)
    input_tokens = int(raw_input) if raw_input is not None else None
    output_tokens = int(raw_output) if raw_output is not None else None
    return content, input_tokens, output_tokens


def run_queue(
    *,
    label: str,
    endpoint: Endpoint,
    journal: Path,
    output: Path,
    queue: list[tuple[str, str | None, str]],
    prices: dict[str, dict[str, Any]],
    parse: Callable[[str], str | None],
    retry_exhausted: bool,
    log,
) -> None:
    """Work a queue of (request_id, system, user) with journal-resume semantics."""
    price = prices.get(endpoint.price_id())
    if price is None:
        raise PriceError(f"no committed price for {endpoint.price_id()}")
    completed, exhausted, ambiguous, _, completed_rows = journal_state(journal)
    todo = []
    for request_id, system, user in queue:
        if request_id in completed or request_id in ambiguous:
            continue
        if request_id in exhausted and not retry_exhausted:
            continue
        todo.append((request_id, system, user))
    if not todo:
        write_outputs(output, completed_rows)
        log(f"{label}: nothing to do ({len(completed)} completed)")
        return
    client = make_client(endpoint)
    done = 0
    for request_id, system, user in todo:
        prompt_text = (system or "") + user
        raw_final = ""
        parsed_final = None
        # Continue attempt numbering across resumes: journal_state refuses a second
        # settlement for the same (request_id, attempt) (Grok post-label finding 2).
        previous_attempts = [
            int(row.get("attempt", 0))
            for row in read_jsonl(journal)
            if row.get("request_id") == request_id
        ] if journal.exists() else []
        first_attempt = max(previous_attempts, default=0) + 1
        for offset in range(MAX_ATTEMPTS):
            attempt = first_attempt + offset
            bound = call_bound(price, prompt_text, endpoint.max_tokens)
            charged_total = lane_charged_so_far(all_journals())
            if charged_total + bound > LANE_CAP_USD:
                raise BudgetError(
                    f"lane cap {LANE_CAP_USD} would be exceeded: charged {charged_total:.4f} "
                    f"+ bound {bound:.4f}. {label} stops before dispatching {request_id}."
                )
            append_journal(journal, {
                "event": "reserved", "request_id": request_id, "attempt": attempt,
                "bound_usd": round(bound, 6),
                "input_token_bound": input_token_bound(prompt_text),
                "output_token_bound": endpoint.max_tokens,
            })
            try:
                raw, input_tokens, output_tokens = one_call(client, endpoint, system, user)
                error = None
            except Exception as exc:  # noqa: BLE001 — journalled, then retried
                raw, input_tokens, output_tokens = "", None, None
                error = f"{type(exc).__name__}: {exc}"
            # Missing usage or a failed call settles at the reserved bound, never 0
            # (Grok post-label finding 1; run_labels.py's frozen convention).
            if error is not None or input_tokens is None or output_tokens is None:
                charged = bound
            else:
                charged = cost_usd(price, max(0, input_tokens), max(0, output_tokens))
            append_journal(journal, {
                "event": "settled", "request_id": request_id, "attempt": attempt,
                "charged_usd": round(charged, 8),
                "input_tokens": input_tokens, "output_tokens": output_tokens,
                **({"error": error[:200]} if error else {}),
            })
            if error is None:
                raw_final = raw
                parsed_final = parse(raw)
                if parsed_final is not None:
                    break
            time.sleep(min(2 ** (offset + 1), 20))
        outcome = "completed" if parsed_final is not None else "exhausted"
        append_journal(journal, {
            "event": outcome, "request_id": request_id,
            "output": {"request_id": request_id, "raw": raw_final[:200], "parsed": parsed_final},
        })
        if outcome == "completed":
            completed_rows[request_id] = {
                "request_id": request_id, "raw": raw_final[:200], "parsed": parsed_final,
            }
        done += 1
        if done % 25 == 0 or done == len(todo):
            total = lane_charged_so_far(all_journals())
            log(f"{label}: {done}/{len(todo)} lane_total=${total:.4f}")
    write_outputs(output, completed_rows)


def semantic_queue(endpoint: Endpoint, join: dict[str, str]) -> list[tuple[str, str | None, str]]:
    packets = read_jsonl(PACKETS / "l1_packets.jsonl")
    if len(packets) != 461:
        raise RunnerError(f"expected 461 l1 packets, got {len(packets)}")
    queue = []
    for row in packets:
        request_id = str(row["request_id"])
        if request_id not in join:
            raise RunnerError(f"packet {request_id} missing from the join")
        queue.append((request_id, None, str(row["prompt"])))
    return queue


def resolve_semantic_outputs(output: Path, join: dict[str, str], final: Path) -> None:
    """Re-key a pass file from opaque request ids to item ids for the scorer."""
    rows = read_jsonl(output)
    resolved = []
    for row in rows:
        item_id = join.get(str(row["request_id"]))
        if item_id is None:
            raise RunnerError(f"unknown request id {row['request_id']} in {output.name}")
        resolved.append({"id": item_id, "parsed": row["parsed"], "raw": row["raw"]})
    resolved.sort(key=lambda r: r["id"])
    with final.open("w", encoding="utf-8") as handle:
        for row in resolved:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def assemble_timing(gold: list[dict[str, Any]], router_inputs: dict[str, str], pass_n: int) -> None:
    """Build one timing pass file; refuse when the router pass is simply unfinished.

    A prose item may become ``cannot_determine`` only when its router item is
    journalled ``exhausted`` or ``ambiguous`` (the strict convention for a failed
    instrument call).  A missing route with no terminal journal record means the
    router pass has not run to completion, and assembling would silently score an
    all-abstain instrument (Grok post-label finding 4).
    """
    journal = OUT / f"router_pass{pass_n}.journal.jsonl"
    completed, exhausted, ambiguous, _, completed_rows = journal_state(journal)
    out_rows = []
    abstained = 0
    for row in gold:
        item_id = str(row["item_id"])
        if row["channel"] == "tool":
            answer = "attempt"
        else:
            text = router_inputs.get(item_id, "")
            if not text.strip():
                answer = "no_attempt"  # production classify("") short-circuit: route none
            else:
                rid = router_request_id(item_id)
                routed = completed_rows.get(rid)
                if routed is not None and routed.get("parsed") in INTERVENTION_ROUTES:
                    answer = "attempt"
                elif routed is not None and routed.get("parsed") is not None:
                    answer = "no_attempt"
                elif rid in exhausted or rid in ambiguous:
                    answer = "cannot_determine"
                    abstained += 1
                else:
                    raise SystemExit(
                        f"INCOMPLETE: router pass {pass_n} has no terminal journal record for "
                        f"{item_id}; run the router to completion before assembling timing"
                    )
        out_rows.append({"id": item_id, "parsed": answer})
    out_rows.sort(key=lambda r: r["id"])
    path = HERE / f"timing_pass{pass_n}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"{path.name}: {len(out_rows)} rows ({abstained} exhausted-router -> cannot_determine)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--assemble-timing", action="store_true")
    parser.add_argument("--retry-exhausted", action="store_true")
    args = parser.parse_args()

    prices = load_prices(PRICE_FILE)
    validate_prices(prices)
    gold, join = load_gold_and_join()
    router_inputs = prose_router_inputs(gold)
    needs_router = [iid for iid, text in sorted(router_inputs.items()) if text.strip()]
    OUT.mkdir(exist_ok=True)

    def log(message: str) -> None:
        print(message, flush=True)

    if args.assemble_timing:
        for pass_n in (1, 2):
            assemble_timing(gold, router_inputs, pass_n)
        return

    router_queue = [
        (router_request_id(iid), FROZEN_PROMPT, router_inputs[iid]) for iid in needs_router
    ]
    semantic_rows = read_jsonl(PACKETS / "l1_packets.jsonl")

    def remaining_bound(
        queue: list[tuple[str, str | None, str]], journal: Path, endpoint: Endpoint
    ) -> float:
        """One-attempt bound over the queue items this journal has not finished.

        Resume-aware (finding 5): completed and ambiguous items are excluded, and
        exhausted items count only under --retry-exhausted.  The live per-attempt
        reserve gate still stops any retry that would breach the cap.
        """
        completed, exhausted, ambiguous, _, _ = journal_state(journal)
        price = prices[endpoint.price_id()]
        total = 0.0
        for request_id, system, user in queue:
            if request_id in completed or request_id in ambiguous:
                continue
            if request_id in exhausted and not args.retry_exhausted:
                continue
            total += call_bound(price, (system or "") + user, endpoint.max_tokens)
        return total

    def router_pass_bound(pass_n: int) -> float:
        return remaining_bound(router_queue, OUT / f"router_pass{pass_n}.journal.jsonl", ROUTER)

    def candidate_pass_bound(endpoint: Endpoint, pass_n: int) -> float:
        queue = [
            (str(row["request_id"]), None, str(row["prompt"])) for row in semantic_rows
        ]
        return remaining_bound(queue, OUT / f"{endpoint.name}_pass{pass_n}.journal.jsonl", endpoint)

    if args.dry_run:
        worst = sum(router_pass_bound(n) for n in (1, 2)) + sum(
            candidate_pass_bound(endpoint, n) for endpoint in CANDIDATES for n in (1, 2)
        )
        charged = lane_charged_so_far(all_journals())
        log(
            f"dry run: full queues semantic {len(semantic_rows)}x2x{len(CANDIDATES)} + router "
            f"{len(router_queue)}x2; one-attempt worst-case over REMAINING items ${worst:.2f}; "
            f"lane charged so far ${charged:.4f}; cap ${LANE_CAP_USD:.2f}"
        )
        if charged + worst > LANE_CAP_USD:
            raise BudgetError("remaining worst case exceeds the lane cap; do not dispatch")
        return

    # Paid paths below: no candidate or router answer before gold freezes (finding 3).
    require_freeze()

    if args.probe:
        probe_packet = semantic_rows[0]
        for endpoint in CANDIDATES:
            run_queue(
                label=f"probe:{endpoint.name}", endpoint=endpoint,
                journal=OUT / f"probe_{endpoint.name}.journal.jsonl",
                output=OUT / f"probe_{endpoint.name}.jsonl",
                queue=[(str(probe_packet["request_id"]), None, str(probe_packet["prompt"]))],
                prices=prices, parse=parse_verdict,
                retry_exhausted=args.retry_exhausted, log=log,
            )
            log(f"probe:{endpoint.name} -> {read_jsonl(OUT / ('probe_' + endpoint.name + '.jsonl'))}")
        if router_queue:
            run_queue(
                label="probe:router", endpoint=ROUTER,
                journal=OUT / "probe_router.journal.jsonl",
                output=OUT / "probe_router.jsonl",
                queue=router_queue[:1], prices=prices, parse=parse_route,
                retry_exhausted=args.retry_exhausted, log=log,
            )
            log(f"probe:router -> {read_jsonl(OUT / 'probe_router.jsonl')}")
        return

    # Startup preflight (finding 5): the whole remaining one-attempt bound must fit.
    # Deliberately stricter than the per-seat skip on a post-cap-trip resume (recert
    # residual 1): refusing a hopeless re-entry is the fail-closed direction, and
    # --assemble-timing remains available for a finished-but-over-cap endgame.
    startup_bound = sum(router_pass_bound(n) for n in (1, 2)) + sum(
        candidate_pass_bound(endpoint, n) for endpoint in CANDIDATES for n in (1, 2)
    )
    startup_charged = lane_charged_so_far(all_journals())
    if startup_charged + startup_bound > LANE_CAP_USD:
        raise BudgetError(
            f"remaining one-attempt bound ${startup_bound:.2f} plus charged "
            f"${startup_charged:.4f} exceeds the lane cap ${LANE_CAP_USD:.2f}; refusing to start"
        )

    incomplete: list[str] = []

    # Full run, cheapest-first: router passes, then mistral, then minimax.  Each
    # instrument holds its allowance (finding 7): its own remaining bound must fit
    # before it starts, so an earlier overrun cannot silently consume a later seat.
    router_allowance = sum(router_pass_bound(n) for n in (1, 2))
    if lane_charged_so_far(all_journals()) + router_allowance > LANE_CAP_USD:
        incomplete.append("router")
        log("SEAT-INCOMPLETE: router allowance does not fit under the lane cap")
    else:
        for pass_n in (1, 2):
            run_queue(
                label=f"router pass{pass_n}", endpoint=ROUTER,
                journal=OUT / f"router_pass{pass_n}.journal.jsonl",
                output=OUT / f"router_pass{pass_n}.jsonl",
                queue=router_queue, prices=prices, parse=parse_route,
                retry_exhausted=args.retry_exhausted, log=log,
            )
    for endpoint in CANDIDATES:
        allowance = sum(candidate_pass_bound(endpoint, n) for n in (1, 2))
        if lane_charged_so_far(all_journals()) + allowance > LANE_CAP_USD:
            incomplete.append(endpoint.name)
            log(f"SEAT-INCOMPLETE: {endpoint.name} allowance does not fit under the lane cap")
            continue
        for pass_n in (1, 2):
            output = OUT / f"{endpoint.name}_pass{pass_n}.jsonl"
            run_queue(
                label=f"{endpoint.name} pass{pass_n}", endpoint=endpoint,
                journal=OUT / f"{endpoint.name}_pass{pass_n}.journal.jsonl",
                output=output,
                queue=semantic_queue(endpoint, join), prices=prices, parse=parse_verdict,
                retry_exhausted=args.retry_exhausted, log=log,
            )
            resolve_semantic_outputs(
                output, join, OUT / f"{endpoint.name}_pass{pass_n}.resolved.jsonl"
            )

    # Completeness audit (finding 7): an unfinished journal must never be scored
    # as a finished instrument.
    expected = {f"router_pass{n}": len(router_queue) for n in (1, 2)}
    for endpoint in CANDIDATES:
        for pass_n in (1, 2):
            expected[f"{endpoint.name}_pass{pass_n}"] = len(semantic_rows)
    for name, want in sorted(expected.items()):
        completed, exhausted, ambiguous, _, _ = journal_state(OUT / f"{name}.journal.jsonl")
        terminal = len(completed | exhausted | ambiguous)  # union: no double-count (recert residual 2)
        log(f"{name}: {len(completed)} completed, {len(exhausted)} exhausted, "
            f"{len(ambiguous)} ambiguous of {want}")
        if terminal < want:
            incomplete.append(name)
    total = lane_charged_so_far(all_journals())
    if incomplete:
        log(f"INCOMPLETE ({', '.join(sorted(set(incomplete)))}); lane charged ${total:.4f} "
            f"of ${LANE_CAP_USD:.2f}")
        raise SystemExit(2)
    for pass_n in (1, 2):
        assemble_timing(gold, router_inputs, pass_n)
    log(f"candidate runs complete; lane charged ${total:.4f} of ${LANE_CAP_USD:.2f}")


if __name__ == "__main__":
    main()
