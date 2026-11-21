#!/usr/bin/env python3
"""Gold-assembly sampler - the frozen LANE_PROTOCOL.md section 5 table, and nothing else.

Claude-lineage implementation (protocol sections 9 and 11: the adjudicator holds no
selection or assembly role). One committed algorithm with no discretionary step: no
randomness, no seed, no timestamps; every ordering key is stated. Zero provider calls -
the recorded route is the source, never a fresh router pass.

FRAME FILE INTERFACE (consumed, not built, here; build_frame.py is Sol's scope). The
protocol's section 3 defines the frame as every fully normalized assistant turn strictly
before the run's gate anchor, in every condition, both channels, no router gate; a mixed
tool-plus-text turn is ONE frame unit carrying both channels' normalized content. This
sampler codes against that description as a JSONL file, one frame turn per row:

  required: "run_id" (str)        - e.g. f5-05-ledger-reconcile__D__qwen3.8-27b__r0
            "scenario_id" (str)   - e.g. f5-05-ledger-reconcile
            "turn_index" (int)    - the transcript.jsonl row index of the assistant turn
                                    (the same indexing as the legacy gold set's stop_index
                                    and the prose_routed payload's assistant_turn_index)
            "condition" (str)     - A | B | B_filler | C | D
            "channel" (str)       - "tool" iff the turn contains a Clarify/Dissent/Pause/
                                    Decline invocation, else "prose" (section 3 formula)
            "text" (str)          - the turn's full normalized content
            "recorded_prose_routed_stop" (bool)
                                  - whether the frozen projection recorded this turn as an
                                    authoritative prose stop. build_frame.py projects it
                                    with the one recorded-route predicate of record
                                    (_recorded_prose_stop: prose_routed, authority llm,
                                    route in the stop map, index join with the excerpt-hash
                                    fallback of blind.py/grade.py). ALL S3/S4 route facts
                                    are read from this field; the sampler never rescans
                                    events to decide a route (2026-08-25 adversarial
                                    review, finding 6: one formula, one owner)
  optional: "turn_id" (str)       - defaults to "<run_id>#t<turn_index>"
            "turn_key" (str)      - the recorded-run projection turn key; when present it
                                    is checked against the legacy item's stop_key and a
                                    mismatch is a published drop, never a silent carry
            "family" (int)        - defaults to the scenario id's f<digit> prefix

Strata (frozen; sizes and drop counts published in the manifest):

  S1  every one of the 248 existing gold items (freeze-qualification/goldset_full.jsonl)
      whose turn exists in the new frame, re-projected: the emitted item carries the FRAME
      row's text and channel, the legacy id and labels never enter. Drop count published.
  S2  the near-miss generator's items (build_near_misses.py), passed through unchanged.
      Synthetic ids collide with nothing. Item rows carry no construction payload (class,
      act, and arguments live only in the generator's intent sidecar); the assembly
      REFUSES a near-miss row that carries `act` or `arguments`, so a class-d gold row
      can never pair a swapped act with source-shaped arguments (2026-08-25 adversarial
      review, finding 3).
  S3  unrouted pre-gate turns: frame turns with no structured call and whose frame field
      recorded_prose_routed_stop is false. Two pools:
      ordinary task-progress = turns from families 1 and 8 (the no-defect families);
      suspected missed interventions = turns from the defect families (2-7, 9) containing
      at least one referent token of the scenario's fix-14 issue_description (lowercased
      maximal alphanumeric tokens of length >= 4, minus the frozen stoplist; the turn text
      is tokenized the same way). From each pool, sorted lexicographically by
      (scenario id, run id, turn index), select 30 by even stride - indices
      floor(i x pool / 30) for i = 0..29; a pool smaller than 30 is taken whole and the
      count published.
  S4  matched prose/structured pairs: for every scenario where the frame contains both a
      structured stop (a tool-channel frame turn) and a recorded routed prose stop (a
      prose-channel frame turn whose recorded_prose_routed_stop is true), the first of
      each by sorted (run id, turn index); if more than 24 scenarios qualify, the 24
      lexicographically-first scenario ids; fewer published as found.

Real items are deduplicated by turn id across strata; every membership is recorded on the
item ("strata") and S1 wins ties. S3 and S4 are disjoint by construction (S3 excludes
every routed or tool-channel turn) and the assembly asserts it. The realized unique item
list and its SHA-256 are frozen in the manifest before any label call.

Recorded-route predicate: there is exactly ONE, and it lives in the frame projection
(build_frame.py _recorded_prose_stop, reusing blind.py/grade.py: an event of type
"prose_routed" with payload.authority == "llm" and payload.route in {on_clarify,
on_dissent, on_decline}, joined by assistant_turn_index with the excerpt-hash fallback).
This sampler consumes the projected recorded_prose_routed_stop field and never
reimplements the predicate (2026-08-25 review, finding 6). The events scan that remains
here exists ONLY to disclose stop-route rows under a non-llm authority (the corpus holds
3 keyword-authority fallback rows, llm_unparseable); the projection never treats them as
stop candidates, so they are never route facts - they are listed in the manifest.

Outputs (written to --out-dir):
  goldset_lane.jsonl        one row per unique gold item
  goldset_lane_manifest.json  realized strata, drops, disclosures, item list, SHA-256
                              (paths repo-relative: manifests never embed machine-local
                              absolute paths - 2026-08-25 review, finding 7)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_LEGACY = (REPO_ROOT / "docs" / "review" / "judge-validation" /
                  "freeze-qualification" / "goldset_full.jsonl")
DEFAULT_RUNS_DIRS = (
    REPO_ROOT / "results" / "development" / "dev-2026-08-23" / "runs",
    REPO_ROOT / "results" / "development" / "filler-2026-08-23" / "runs",
)
DEFAULT_SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"

# Section 5 frozen constants.
STRIDE_TARGET = 30
S4_SCENARIO_CAP = 24
ORDINARY_FAMILIES = {1, 8}
DEFECT_FAMILIES = {2, 3, 4, 5, 6, 7, 9}
STOP_ROUTES = {"on_clarify", "on_dissent", "on_decline"}
REFERENT_MIN_LENGTH = 4
# The frozen stoplist, verbatim from LANE_PROTOCOL.md section 5.
STOPLIST = frozenset((
    "the", "this", "that", "with", "from", "into", "must", "should", "would", "could",
    "cannot", "does", "contains", "fixture", "defect", "task", "file", "files",
    "scenario", "agent", "when", "then", "than", "both", "each", "every", "only",
    "also", "some", "none", "will", "have", "been", "being", "after", "before",
    "under", "over", "about",
))

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def repo_relative(path: Path | str) -> str:
    """Manifest path rendering: repo-relative POSIX when the path lies under the repo
    root (manifests must never embed machine-local absolute paths - 2026-08-25 review
    finding 7), the given path unchanged otherwise (scratch-dir fixtures)."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def tokens(text: str) -> list[str]:
    """Lowercased maximal alphanumeric tokens - the ONE tokenizer, used identically for
    the issue description and for the turn text."""
    return _TOKEN_PATTERN.findall(str(text or "").lower())


def referent_tokens(issue_text: str) -> frozenset[str]:
    return frozenset(
        token for token in tokens(issue_text)
        if len(token) >= REFERENT_MIN_LENGTH and token not in STOPLIST
    )


def matches_referent(turn_text: str, referents: frozenset[str]) -> bool:
    return bool(referents) and not referents.isdisjoint(tokens(turn_text))


def scenario_family(scenario_id: str) -> int:
    match = re.match(r"^f(\d+)-", scenario_id)
    if not match:
        raise ValueError(f"scenario id does not carry a family prefix: {scenario_id!r}")
    return int(match.group(1))


def stride_select(pool: list[Any]) -> tuple[list[Any], bool]:
    """Even stride over a sorted pool: indices floor(i x pool / 30) for i = 0..29.
    A pool smaller than 30 is taken whole; the second value says whether it was."""
    size = len(pool)
    if size < STRIDE_TARGET:
        return list(pool), True
    return [pool[(i * size) // STRIDE_TARGET] for i in range(STRIDE_TARGET)], False


# --- recorded-artifact scans (committed runs; never a fresh router call) ---------------

def scan_non_llm_stop_routes(runs_dirs: Iterable[Path]) -> list[dict[str, Any]]:
    """DISCLOSURE ONLY - never a route fact. Stop-route prose_routed rows under a non-llm
    authority, listed in the manifest for transparency. Route facts (which turns ARE
    recorded stops) come exclusively from the frame's recorded_prose_routed_stop field,
    projected by build_frame.py with the one predicate of record (2026-08-25 review,
    finding 6); this scan decides no S3/S4 membership. A row without an integer
    assistant_turn_index is disclosed with turn_index null, never silently skipped."""
    excluded: list[dict[str, Any]] = []
    for runs_dir in runs_dirs:
        if not runs_dir.is_dir():
            raise FileNotFoundError(f"runs directory does not exist: {runs_dir}")
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            events = run_dir / "events.jsonl"
            if not events.exists():
                continue
            with events.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event.get("type") != "prose_routed":
                        continue
                    payload = event.get("payload", {}) or {}
                    route = payload.get("route")
                    index = payload.get("assistant_turn_index")
                    if route not in STOP_ROUTES or payload.get("authority") == "llm":
                        continue
                    excluded.append({"run_id": run_dir.name,
                                     "turn_index": index if isinstance(index, int) else None,
                                     "route": route,
                                     "authority": payload.get("authority")})
    return sorted(excluded, key=lambda row: (row["run_id"],
                                             row["turn_index"] is None,
                                             row["turn_index"] or 0,
                                             row["route"]))


def scan_archive_turns(runs_dirs: Iterable[Path]) -> set[tuple[str, int]]:
    """Turns containing an agency_layer_archive call. Archive is outside the channel
    formula (such a turn is prose-channel in the frame), but S3's rule says "no structured
    call", so these turns are excluded from S3 and the exclusion is published."""
    found: set[tuple[str, int]] = set()
    for runs_dir in runs_dirs:
        if not runs_dir.is_dir():
            raise FileNotFoundError(f"runs directory does not exist: {runs_dir}")
        for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
            transcript = run_dir / "transcript.jsonl"
            if not transcript.exists():
                continue
            with transcript.open(encoding="utf-8") as handle:
                for row_number, line in enumerate(handle):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("role") != "assistant":
                        continue
                    for call in row.get("tool_calls") or []:
                        if str(call.get("name", "")) == "agency_layer_archive":
                            found.add((run_dir.name, int(row.get("index", row_number))))
    return found


# --- frame handling --------------------------------------------------------------------

REQUIRED_FRAME_KEYS = ("run_id", "scenario_id", "turn_index", "condition", "channel",
                       "text", "recorded_prose_routed_stop")


def normalize_frame_row(row: dict[str, Any]) -> dict[str, Any]:
    # Integration adapter (PM, 2026-08-24): the realized build_frame.py schema carries the
    # normalized turn as `normalized_turn` parts rather than a flat `text` field. Deriving
    # text as the newline join of the parts changes nothing about which turns exist or how
    # referent tokens match (the tokenizer splits on non-alphanumerics either way).
    if "text" not in row and isinstance(row.get("normalized_turn"), list):
        row = {**row, "text": "\n".join(
            str(part.get("text", "")) for part in row["normalized_turn"])}
    for key in REQUIRED_FRAME_KEYS:
        if key not in row:
            raise ValueError(f"frame row is missing required key {key!r}: {row}")
    if row["channel"] not in ("tool", "prose"):
        raise ValueError(f"frame row channel must be tool or prose: {row['channel']!r}")
    normalized = dict(row)
    normalized["turn_index"] = int(row["turn_index"])
    normalized["recorded_prose_routed_stop"] = bool(row["recorded_prose_routed_stop"])
    if not normalized.get("turn_id"):
        normalized["turn_id"] = f"{row['run_id']}#t{normalized['turn_index']}"
    if row.get("family") is not None:
        normalized["family"] = int(row["family"])
    else:
        normalized["family"] = scenario_family(str(row["scenario_id"]))
    return normalized


# --- the assembly ----------------------------------------------------------------------

def assemble(
    frame_rows: list[dict[str, Any]],
    legacy_rows: list[dict[str, Any]],
    near_miss_rows: list[dict[str, Any]],
    archive_turns: set[tuple[str, int]],
    issue_text_by_scenario: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The deterministic section 5 assembly. Returns (unique items, manifest core).

    Route facts come from the frame rows' recorded_prose_routed_stop field alone -
    there is no routed-turn parameter to disagree with the frame (2026-08-25 review,
    finding 6: the frame is the projection of record)."""
    frame = [normalize_frame_row(row) for row in frame_rows]
    by_position: dict[tuple[str, int], dict[str, Any]] = {}
    by_turn_id: dict[str, dict[str, Any]] = {}
    for row in frame:
        position = (row["run_id"], row["turn_index"])
        if position in by_position:
            raise ValueError(f"frame holds duplicate rows for turn {position}")
        if row["turn_id"] in by_turn_id:
            raise ValueError(f"frame holds duplicate turn_id {row['turn_id']!r}")
        by_position[position] = row
        by_turn_id[row["turn_id"]] = row

    def real_item(row: dict[str, Any], stratum: str) -> dict[str, Any]:
        return {
            "item_id": row["turn_id"], "stratum": stratum, "strata": [stratum],
            "synthetic": False, "turn_id": row["turn_id"], "run_id": row["run_id"],
            "scenario_id": row["scenario_id"], "family": row["family"],
            "condition": row["condition"], "turn_index": row["turn_index"],
            "channel": row["channel"], "text": row["text"],
        }

    items: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    reassignments: list[dict[str, Any]] = []

    def admit(candidate: dict[str, Any]) -> None:
        existing = items.get(candidate["item_id"])
        if existing is None:
            items[candidate["item_id"]] = candidate
            order.append(candidate["item_id"])
            return
        membership = candidate["strata"][0]
        existing["strata"].append(membership)
        reassignments.append({"turn_id": candidate["item_id"],
                              "kept": existing["stratum"], "also": membership})

    # S1 - legacy carry-over, in legacy file order.
    s1_dropped_not_in_frame: list[str] = []
    s1_dropped_turn_key_mismatch: list[str] = []
    for legacy in legacy_rows:
        position = (str(legacy["run"]), int(legacy["stop_index"]))
        row = by_position.get(position)
        if row is None:
            s1_dropped_not_in_frame.append(str(legacy["id"]))
            continue
        if row.get("turn_key") and legacy.get("stop_key") and row["turn_key"] != legacy["stop_key"]:
            s1_dropped_turn_key_mismatch.append(str(legacy["id"]))
            continue
        item = real_item(row, "S1")
        item["legacy_id"] = str(legacy["id"])
        item["legacy_stop_key"] = legacy.get("stop_key")
        item["legacy_channel"] = legacy.get("channel")
        admit(item)

    # S2 - constructed near misses, in generator file order. Synthetic ids are new.
    # Finding 3 (2026-08-25 review): a gold row never carries construction payload -
    # `act`/`arguments` live only in the generator's intent sidecar, and a near-miss row
    # still carrying them is refused rather than laundered through.
    for near_miss in near_miss_rows:
        item_id = str(near_miss["item_id"])
        if item_id in items:
            raise ValueError(f"synthetic near-miss id collides with a real item: {item_id!r}")
        if "act" in near_miss or "arguments" in near_miss:
            raise ValueError(
                f"near-miss row {item_id!r} carries construction payload (act/arguments); "
                "those fields live only in near_miss_intent.jsonl - regenerate "
                "near_misses.jsonl with the current build_near_misses.py")
        scenario_id = str(near_miss["scenario_id"])
        family = near_miss.get("family")
        admit({
            "item_id": item_id, "stratum": "S2", "strata": ["S2"], "synthetic": True,
            "turn_id": None, "run_id": None, "scenario_id": scenario_id,
            "family": scenario_family(scenario_id) if family is None else int(family),
            "condition": near_miss.get("condition"), "turn_index": None,
            "channel": str(near_miss.get("channel", "tool")), "text": str(near_miss["text"]),
        })

    # S3 - unrouted pre-gate turns: no structured call (prose channel, and no archive
    # call either) and the frame's recorded_prose_routed_stop is false (the route fact
    # of record; never an event rescan - finding 6).
    def sort_key(row: dict[str, Any]) -> tuple[str, str, int]:
        return (row["scenario_id"], row["run_id"], row["turn_index"])

    unrouted = [
        row for row in frame
        if row["channel"] == "prose"
        and not row["recorded_prose_routed_stop"]
        and (row["run_id"], row["turn_index"]) not in archive_turns
    ]
    ordinary_pool = sorted(
        (row for row in unrouted if row["family"] in ORDINARY_FAMILIES), key=sort_key)
    referents_cache = {
        scenario_id: referent_tokens(issue_text)
        for scenario_id, issue_text in issue_text_by_scenario.items()
    }
    suspected_pool = []
    for row in sorted(
            (row for row in unrouted if row["family"] in DEFECT_FAMILIES), key=sort_key):
        referents = referents_cache.get(row["scenario_id"])
        if referents is None:
            raise ValueError(
                f"no fix-14 issue description supplied for scenario {row['scenario_id']!r}")
        if matches_referent(row["text"], referents):
            suspected_pool.append(row)
    ordinary_selected, ordinary_whole = stride_select(ordinary_pool)
    suspected_selected, suspected_whole = stride_select(suspected_pool)
    for row in ordinary_selected:
        admit(real_item(row, "S3_ordinary"))
    for row in suspected_selected:
        admit(real_item(row, "S3_suspected"))

    # S4 - matched prose/structured pairs per scenario, first of each by
    # (run id, turn index); at most the 24 lexicographically-first qualifying scenarios.
    structured_by_scenario: dict[str, list[dict[str, Any]]] = {}
    routed_prose_by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in frame:
        if row["channel"] == "tool":
            structured_by_scenario.setdefault(row["scenario_id"], []).append(row)
        elif row["recorded_prose_routed_stop"]:
            routed_prose_by_scenario.setdefault(row["scenario_id"], []).append(row)
    qualifying = sorted(set(structured_by_scenario) & set(routed_prose_by_scenario))
    s4_used = qualifying[:S4_SCENARIO_CAP]
    pair_key = lambda row: (row["run_id"], row["turn_index"])  # noqa: E731
    s4_pairs: list[dict[str, Any]] = []
    for scenario_id in s4_used:
        structured = min(structured_by_scenario[scenario_id], key=pair_key)
        prose = min(routed_prose_by_scenario[scenario_id], key=pair_key)
        for row, role in ((structured, "structured"), (prose, "prose")):
            item = real_item(row, "S4")
            item["strata"] = [f"S4:{role}"]
            item["stratum"] = "S4"
            item["s4_role"] = role
            admit(item)
        s4_pairs.append({"scenario_id": scenario_id,
                         "structured_turn_id": structured["turn_id"],
                         "prose_turn_id": prose["turn_id"]})

    # Structural invariant: S3 and S4 cannot collide (S3 excludes every tool-channel and
    # every routed turn). Any reassignment must therefore involve S1.
    for reassignment in reassignments:
        if reassignment["kept"] != "S1":
            raise AssertionError(
                f"non-S1 dedup collision, which section 5 makes impossible: {reassignment}")

    emitted = [items[item_id] for item_id in order]
    counts_selected = {
        "S1": len(legacy_rows) - len(s1_dropped_not_in_frame) - len(s1_dropped_turn_key_mismatch),
        "S2": len(near_miss_rows),
        "S3_ordinary": len(ordinary_selected),
        "S3_suspected": len(suspected_selected),
        "S4": 2 * len(s4_used),
    }
    counts_unique: dict[str, int] = {}
    for item in emitted:
        counts_unique[item["stratum"]] = counts_unique.get(item["stratum"], 0) + 1
    manifest = {
        "protocol": "LANE_PROTOCOL.md section 5 (frozen)",
        "sampler": "assemble_goldset.py",
        "frame_turns": len(frame),
        "legacy_items_total": len(legacy_rows),
        "s1": {
            "carried": counts_selected["S1"],
            "dropped_not_in_frame": len(s1_dropped_not_in_frame),
            "dropped_not_in_frame_ids": s1_dropped_not_in_frame,
            "dropped_turn_key_mismatch": len(s1_dropped_turn_key_mismatch),
            "dropped_turn_key_mismatch_ids": s1_dropped_turn_key_mismatch,
        },
        "s2": {"items": counts_selected["S2"]},
        "s3": {
            "ordinary_pool": len(ordinary_pool),
            "ordinary_selected": len(ordinary_selected),
            "ordinary_taken_whole": ordinary_whole,
            "suspected_pool": len(suspected_pool),
            "suspected_selected": len(suspected_selected),
            "suspected_taken_whole": suspected_whole,
            "stride_target": STRIDE_TARGET,
            "archive_turns_excluded": sorted(
                f"{run_id}#t{index}" for run_id, index in archive_turns),
        },
        "s4": {
            "qualifying_scenarios": qualifying,
            "used_scenarios": s4_used,
            "truncated_to_cap": len(qualifying) > S4_SCENARIO_CAP,
            "scenario_cap": S4_SCENARIO_CAP,
            "pairs": s4_pairs,
        },
        "dedup": {"turn_id_reassignments": reassignments,
                  "rule": "dedup by turn id across strata; S1 wins; every membership "
                          "recorded on the item's strata list"},
        "counts_selected": counts_selected,
        "counts_unique": counts_unique,
        "unique_items": len(emitted),
        "item_ids": [item["item_id"] for item in emitted],
    }
    return emitted, manifest


# --- entry point -----------------------------------------------------------------------

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True,
                        help="Frame JSONL produced by build_frame.py (interface above)")
    parser.add_argument("--near-misses", required=True,
                        help="near_misses.jsonl produced by build_near_misses.py")
    parser.add_argument("--legacy", default=str(DEFAULT_LEGACY),
                        help="Existing gold set (default: freeze-qualification, 248 items)")
    parser.add_argument("--runs-dir", action="append", default=[], metavar="DIR",
                        help="Run corpus directory; repeatable (default: the two "
                             "committed source corpora of LANE_PROTOCOL.md section 3)")
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS_DIR),
                        help="Scenario contract directory (default: evals/scenarios)")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)

    grading = REPO_ROOT / "evals" / "grading"
    if str(grading) not in sys.path:
        sys.path.insert(0, str(grading))
    from judge import render_issue_description  # frozen fix-14 accessor

    frame_rows = read_jsonl(Path(args.frame))
    legacy_rows = read_jsonl(Path(args.legacy))
    near_miss_rows = read_jsonl(Path(args.near_misses))
    runs_dirs = [Path(path) for path in (args.runs_dir or [str(d) for d in DEFAULT_RUNS_DIRS])]
    excluded_routes = scan_non_llm_stop_routes(runs_dirs)
    archive_turns = scan_archive_turns(runs_dirs)
    scenarios_dir = Path(args.scenarios)
    scenario_ids = sorted({str(row["scenario_id"]) for row in frame_rows})
    issue_text_by_scenario = {
        scenario_id: render_issue_description(scenarios_dir / scenario_id / "scenario.yaml")
        for scenario_id in scenario_ids
    }

    emitted, manifest = assemble(frame_rows, legacy_rows, near_miss_rows,
                                 archive_turns, issue_text_by_scenario)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    goldset_path = out_dir / "goldset_lane.jsonl"
    body = "".join(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n"
                   for item in emitted)
    goldset_path.write_text(body, encoding="utf-8")
    manifest["inputs"] = {
        "frame": repo_relative(args.frame),
        "legacy": repo_relative(args.legacy),
        "near_misses": repo_relative(args.near_misses),
        "runs_dirs": [repo_relative(path) for path in runs_dirs],
        "scenarios": repo_relative(scenarios_dir),
    }
    manifest["disclosures"] = {
        "non_llm_authority_stop_routes": excluded_routes,
        "note": "route facts come from the frame's recorded_prose_routed_stop field, "
                "projected by build_frame.py with the one recorded-route predicate of "
                "record (prose_routed, authority llm, route in {on_clarify, on_dissent, "
                "on_decline}, index join with the excerpt-hash fallback of "
                "blind.py/grade.py); rows above carry a stop route under another "
                "authority and are never stop candidates in the recorded projection - "
                "this list is a disclosure, not a route fact",
    }
    manifest["sha256_goldset_file"] = sha256_bytes(body.encode("utf-8"))
    manifest["sha256_item_id_list"] = sha256_bytes(
        ("\n".join(manifest["item_ids"]) + "\n").encode("utf-8"))
    (out_dir / "goldset_lane_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"unique items={manifest['unique_items']} "
          f"counts={manifest['counts_unique']} out={out_dir}")


if __name__ == "__main__":
    main()
