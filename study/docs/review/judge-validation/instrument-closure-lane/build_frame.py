#!/usr/bin/env python3
"""Build the frozen condition-invariant, pre-gate assistant-turn frame.

This is a projection only.  It makes no provider calls, runs no router, and
does not select gold items.  The normalization, blinding, ground-truth
rendering, judge projection, and primary gate-anchor implementation are
imported from ``evals/grading`` so the lane cannot drift from the recorded-run
instrument.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
GRADING = REPO / "evals" / "grading"
if str(GRADING) not in sys.path:
    sys.path.insert(0, str(GRADING))

# These imports are intentionally the implementation of the protocol's
# "reuse, do not reimplement" requirement.
from blind import AFFORDANCE_NAMES, blind_transcript, clean_text, excerpt_hash  # noqa: E402
from common import read_json, read_jsonl, read_scenario_yaml, write_jsonl  # noqa: E402
from grade import ROUTE_TO_AFFORDANCE, _consequence_scan  # noqa: E402
from judge import judge_projection, render_issue_description  # noqa: E402


SCHEMA_VERSION = "instrument-closure-frame-1.0.0"
CORPUS_RUN_ROOTS = (
    Path("results/development/dev-2026-08-23/runs"),
    Path("results/development/filler-2026-08-23/runs"),
)
STOP_TOOL_NAMES = {
    name for name, act in AFFORDANCE_NAMES.items()
    if act in {"clarify", "dissent", "pause", "decline"}
}


def _stable_id(run_id: str, source_index: int) -> str:
    digest = hashlib.sha256(f"{run_id}\0{source_index}".encode("utf-8")).hexdigest()
    return f"frame-{digest[:24]}"


def _call_name(call: dict[str, Any]) -> str:
    """Read either recorded call shape without changing its semantics."""
    name = call.get("name")
    if name:
        return str(name)
    function = call.get("function")
    return str(function.get("name", "")) if isinstance(function, dict) else ""


def _recorded_prose_stop(events: list[dict[str, Any]], row: dict[str, Any]) -> bool:
    """Whether PM13/PM15 recorded this turn as an authoritative prose stop.

    Index is the harness fix-6 join.  The old excerpt hash is only a fallback,
    matching ``blind.py`` and ``grade.py``.
    """
    index = int(row.get("index", -1))
    digest = excerpt_hash(str(row.get("text", "")).strip())
    for event in events:
        if event.get("type") != "prose_routed":
            continue
        payload = event.get("payload", {})
        if payload.get("authority") != "llm" or str(payload.get("route")) not in ROUTE_TO_AFFORDANCE:
            continue
        turn_index = payload.get("assistant_turn_index")
        if (isinstance(turn_index, int) and turn_index == index) or (
            not isinstance(turn_index, int) and payload.get("excerpt_hash") == digest
        ):
            return True
    return False


def project_run(
    run_dir: Path,
    *,
    repo: Path = REPO,
    scenario_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Project one recorded run into zero or more frozen frame units."""
    scenario_root = scenario_root or repo / "evals" / "scenarios"
    run = read_json(run_dir / "run.json")
    events = read_jsonl(run_dir / "events.jsonl")
    raw = read_jsonl(run_dir / "transcript.jsonl")
    scenario_path = scenario_root / str(run["scenario_id"]) / "scenario.yaml"
    scenario = read_scenario_yaml(scenario_path)
    blinded = blind_transcript(raw, events)

    # This is exactly the recorded primary_gate_anchor_union anchor: the first
    # execution-position match for the scenario's declared consequential act.
    anchor = _consequence_scan(
        blinded, scenario.get("ground_truth", {}).get("consequential_action")
    )["attempt"]
    anchor_index = anchor[0] if anchor is not None else None
    source_path = run_dir.relative_to(repo).as_posix()
    issue = render_issue_description(scenario_path)

    blinded_by_index: dict[int, list[dict[str, Any]]] = {}
    for row in blinded:
        if row.get("speaker") == "assistant" and "source_index" in row:
            blinded_by_index.setdefault(int(row["source_index"]), []).append(row)

    output: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for ordinal, row in enumerate(raw):
        if row.get("role") != "assistant":
            continue
        source_index = int(row.get("index", ordinal))
        if source_index in seen_indexes:
            raise ValueError(f"{run_dir}: duplicate assistant source index {source_index}")
        seen_indexes.add(source_index)
        if anchor_index is not None and source_index >= anchor_index:
            continue

        calls = row.get("tool_calls") if isinstance(row.get("tool_calls"), list) else []
        interventions = [
            AFFORDANCE_NAMES[_call_name(call)]
            for call in calls
            if _call_name(call) in STOP_TOOL_NAMES
        ]
        normalized_text = clean_text(row.get("text", ""))
        turn_rows = blinded_by_index.get(source_index, [])
        normalized_turn = [
            {"ordinal": number, "speaker": "assistant", "text": str(value.get("text", ""))}
            for number, value in enumerate(turn_rows, 1)
            if "text" in value
        ]
        turn_key = next(
            (str(value["turn_key"]) for value in turn_rows if value.get("turn_key")),
            None,
        )
        if turn_key is None:
            # ``blind.py`` creates this key for every ordinary assistant row;
            # retain a deterministic fallback for empty/malformed fixtures.
            call_ids = sorted(str(call.get("id", "")) for call in calls if call.get("id"))
            turn_key = excerpt_hash(excerpt_hash(str(row.get("text", "")).strip()) + "|" + "|".join(call_ids))

        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "id": _stable_id(str(run["run_id"]), source_index),
                "run_id": str(run["run_id"]),
                "scenario_id": str(run["scenario_id"]),
                "family": int(run["family"]),
                "condition": str(run["condition"]),
                "source_run_path": source_path,
                "turn_index": source_index,
                "turn_key": turn_key,
                "channel": "tool" if interventions else "prose",
                "structured_intervention_acts": interventions,
                "has_prose_text": bool(normalized_text),
                "mixed_intervention_turn": bool(interventions and normalized_text),
                "recorded_prose_routed_stop": _recorded_prose_stop(events, row),
                "gate_anchor_turn": anchor_index,
                "normalized_turn": normalized_turn,
                "transcript_through_turn": judge_projection(blinded, source_index),
                "ground_truth_issue": issue,
            }
        )
    return output


def build_frame(
    *,
    repo: Path = REPO,
    corpus_roots: Iterable[Path] = CORPUS_RUN_ROOTS,
) -> list[dict[str, Any]]:
    """Build and stably order the complete frame from the two frozen corpora."""
    rows: list[dict[str, Any]] = []
    for relative_root in corpus_roots:
        root = relative_root if relative_root.is_absolute() else repo / relative_root
        if not root.is_dir():
            raise FileNotFoundError(f"missing frozen corpus root: {root}")
        for run_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            rows.extend(project_run(run_dir, repo=repo))
    rows.sort(key=lambda row: (row["scenario_id"], row["run_id"], row["turn_index"]))
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("stable frame ids are not unique")
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/review/judge-validation/instrument-closure-lane/frame.jsonl"),
        help="repository-relative JSONL output",
    )
    parser.add_argument(
        "--sha256-output",
        type=Path,
        help="repository-relative sidecar (default: OUTPUT.sha256)",
    )
    args = parser.parse_args()
    if args.output.is_absolute() or (args.sha256_output and args.sha256_output.is_absolute()):
        parser.error("output paths must be repository-relative")
    output = REPO / args.output
    sidecar = REPO / (args.sha256_output or Path(str(args.output) + ".sha256"))
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar.parent.mkdir(parents=True, exist_ok=True)

    rows = build_frame()
    write_jsonl(output, rows)
    digest = file_sha256(output)
    sidecar.write_text(f"{digest}  {args.output.as_posix()}\n", encoding="utf-8")
    counts = Counter((row["condition"], row["channel"]) for row in rows)
    rendered = ", ".join(f"{condition}/{channel}={counts[condition, channel]}"
                         for condition in ("A", "B", "B_filler", "C", "D")
                         for channel in ("prose", "tool") if counts[condition, channel])
    print(f"frame rows={len(rows)}; {rendered}; sha256={digest}")


if __name__ == "__main__":
    main()
