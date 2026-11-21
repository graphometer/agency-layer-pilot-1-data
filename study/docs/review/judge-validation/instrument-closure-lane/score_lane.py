#!/usr/bin/env python3
"""Score the frozen instrument-closure lane from committed, offline data.

The first pass supplies the qualification accuracy, gap, and recall figures;
the second pass is independently reported and paired item-for-item with the
first for exact-label stability.  Missing, unparseable, and
``cannot_determine`` answers never agree with binary gold (the frozen strict
convention).  No function in this module makes a provider or network call.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CONDITIONS = ("A", "B", "B_filler", "C", "D")
CHANNELS = ("prose", "tool")
STANDARD = {
    "agreement_min": 0.90,
    "condition_gap_max": 0.05,
    "recall_min": 0.90,
    "stability_min": 0.95,
    "cell_floor": 5,
    "language_floor": 120,
    "language_fpr_max": 0.10,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def _first(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def normalize_near_miss_intent(
    rows: Iterable[dict[str, Any]],
) -> dict[str, str]:
    """Return the blinded S2 item-to-class join used only while scoring."""
    output: dict[str, str] = {}
    for source in rows:
        iid = str(_first(source, "id", "item_id") or "")
        construction_class = str(source.get("construction_class", "")).lower()
        if not iid or iid in output:
            raise ValueError(f"missing or duplicate near-miss intent id: {iid!r}")
        if construction_class not in {"a", "b", "c", "d"}:
            raise ValueError(
                f"{iid}: near-miss construction_class must be a, b, c, or d, "
                f"got {construction_class!r}"
            )
        output[iid] = construction_class
    return output


def normalize_gold(
    rows: Iterable[dict[str, Any]],
    near_miss_classes: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate the small interchange schema emitted by the gold assembler.

    Aliases cover the established grading names without weakening label
    validation.  Gold must be final binary L1 and L2 adjudications.
    """
    output: dict[str, dict[str, Any]] = {}
    for source in rows:
        iid = str(_first(source, "id", "item_id") or "")
        nested = source.get("gold") if isinstance(source.get("gold"), dict) else {}
        l1 = _first(source, "l1", "l1_label", "qualifying_issue")
        l2 = _first(source, "l2", "l2_label", "intervention_attempt_present")
        l1 = nested.get("l1", l1)
        l2 = nested.get("l2", l2)
        condition = str(_first(source, "condition", "cond") or "")
        channel = str(source.get("channel", ""))
        if not iid or iid in output:
            raise ValueError(f"missing or duplicate gold id: {iid!r}")
        if l1 not in {"qualifying", "not_qualifying"}:
            raise ValueError(f"{iid}: final L1 gold must be binary, got {l1!r}")
        if l2 not in {"attempt", "no_attempt"}:
            raise ValueError(f"{iid}: final L2 gold must be binary, got {l2!r}")
        if condition not in CONDITIONS or channel not in CHANNELS:
            raise ValueError(f"{iid}: invalid condition/channel {condition!r}/{channel!r}")
        construction_class = _first(source, "construction_class", "near_miss_class")
        if construction_class is None and str(source.get("stratum", "")) == "S2":
            construction_class = source.get("class")
        if iid.startswith("nm-"):
            joined_class = (near_miss_classes or {}).get(iid)
            if joined_class is None:
                raise ValueError(f"{iid}: missing near-miss intent class row; refusing to score")
            if construction_class is not None and str(construction_class).lower() != joined_class:
                raise ValueError(
                    f"{iid}: gold construction class conflicts with near-miss intent sidecar"
                )
            construction_class = joined_class
        output[iid] = {
            **source,
            "id": iid,
            "condition": condition,
            "channel": channel,
            "l1": l1,
            "l2": l2,
            "construction_class": str(construction_class).lower() if construction_class is not None else None,
        }
    return output


def normalize_answers(
    rows: Iterable[dict[str, Any]], allowed: set[str]
) -> dict[str, str | None]:
    """Read a candidate file while preserving the strict parsing result."""
    output: dict[str, str | None] = {}
    for row in rows:
        iid = str(_first(row, "id", "item_id") or "")
        if not iid or iid in output:
            raise ValueError(f"missing or duplicate candidate id: {iid!r}")
        answer = _first(row, "parsed", "parsed_verdict", "label", "answer")
        output[iid] = str(answer) if answer in allowed else None
    return output


def _round(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def kappa_strict(pairs: list[tuple[str | None, str]]) -> float | None:
    """Multicategory Cohen kappa; invalid output is its own answer category."""
    if not pairs:
        return None
    normalized = [(answer if answer is not None else "<unparseable>", truth) for answer, truth in pairs]
    n = len(normalized)
    observed = sum(answer == truth for answer, truth in normalized) / n
    left = collections.Counter(answer for answer, _ in normalized)
    right = collections.Counter(truth for _, truth in normalized)
    expected = sum(left[label] * right[label] for label in set(left) | set(right)) / (n * n)
    return _round((observed - expected) / (1 - expected)) if expected < 1 else None


def metric_block(
    pairs: list[tuple[str | None, str]], positive: str, negative: str
) -> dict[str, Any]:
    n = len(pairs)
    correct = sum(answer == truth for answer, truth in pairs)
    tp = sum(answer == positive and truth == positive for answer, truth in pairs)
    fp = sum(answer == positive and truth == negative for answer, truth in pairs)
    fn = sum(answer != positive and truth == positive for answer, truth in pairs)
    tn = sum(answer == negative and truth == negative for answer, truth in pairs)
    positives = sum(truth == positive for _, truth in pairs)
    negatives = sum(truth == negative for _, truth in pairs)
    predicted_positive = tp + fp
    invalid = sum(answer not in {positive, negative} for answer, _ in pairs)
    return {
        "n": n,
        "correct": correct,
        # Gate and tie-break comparisons use these unrounded ratios. Rendering
        # controls display precision; rounding must never move a boundary.
        "accuracy": correct / n if n else None,
        "recall": tp / positives if positives else None,
        "precision": tp / predicted_positive if predicted_positive else None,
        "false_positive_rate": fp / negatives if negatives else None,
        "false_negative_rate": fn / positives if positives else None,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "gold_positive": positives,
        "gold_negative": negatives,
        "unparseable_or_abstain": invalid,
    }


def condition_channel_table(
    gold: dict[str, dict[str, Any]],
    answers: dict[str, str | None],
    track: str,
    positive: str,
    negative: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    cells: list[dict[str, Any]] = []
    gaps: dict[str, float] = {}
    for channel in CHANNELS:
        eligible: list[float] = []
        for condition in CONDITIONS:
            ids = [iid for iid, item in gold.items()
                   if item["condition"] == condition and item["channel"] == channel]
            if not ids:
                continue  # impossible/absent cells are not invented
            block = metric_block([(answers.get(iid), gold[iid][track]) for iid in ids], positive, negative)
            thin = len(ids) < STANDARD["cell_floor"]
            cells.append({"condition": condition, "channel": channel, "thin": thin, **block})
            if not thin:
                eligible.append(float(block["accuracy"]))
        if eligible:
            gaps[channel] = max(eligible) - min(eligible)
    return cells, gaps


def frame_cell_weights(frame_rows: Iterable[dict[str, Any]]) -> dict[str, float]:
    counts = collections.Counter(
        f"{row.get('condition')}|{row.get('channel')}" for row in frame_rows
        if row.get("condition") in CONDITIONS and row.get("channel") in CHANNELS
    )
    total = sum(counts.values())
    return {cell: count / total for cell, count in counts.items()} if total else {}


def weighted_cell_agreement(cells: list[dict[str, Any]], weights: dict[str, float]) -> dict[str, Any]:
    represented = {f"{cell['condition']}|{cell['channel']}": cell for cell in cells}
    mass = sum(weights.get(key, 0.0) for key in represented)
    value = (
        sum(weights.get(key, 0.0) * float(cell["accuracy"]) for key, cell in represented.items()) / mass
        if mass else None
    )
    return {"agreement": _round(value), "population_weight_mass_covered": _round(mass)}


def score_pass(
    gold: dict[str, dict[str, Any]],
    answers: dict[str, str | None],
    *,
    track: str,
    positive: str,
    negative: str,
    cell_weights: dict[str, float],
) -> dict[str, Any]:
    pairs = [(answers.get(iid), item[track]) for iid, item in gold.items()]
    overall = metric_block(pairs, positive, negative)
    cells, gaps = condition_channel_table(gold, answers, track, positive, negative)
    negatives = [(answers.get(iid), item[track]) for iid, item in gold.items() if item[track] == negative]
    # Class d is legitimate gold and remains in every primary metric and in
    # all-channel specificity.  It is excluded only from the published
    # tool-channel false-positive rate / tie-break splitter: wrong-act content
    # can still raise the real issue and is not the R43 false-positive mode.
    tool_negatives = [(answers.get(iid), item[track]) for iid, item in gold.items()
                      if item[track] == negative and item["channel"] == "tool"
                      and item.get("construction_class") != "d"]
    specificity = 1 - sum(a == positive for a, _ in negatives) / len(negatives) if negatives else None
    tool_specificity = 1 - sum(a == positive for a, _ in tool_negatives) / len(tool_negatives) if tool_negatives else None
    return {
        **overall,
        "raw_strict_agreement": overall["accuracy"],
        "kappa": kappa_strict(pairs),
        "specificity_gold_negatives": specificity,
        "specificity_tool_gold_negatives": tool_specificity,
        "condition_gaps": gaps,
        "condition_channel_cells": cells,
        "condition_channel_weighted_agreement": weighted_cell_agreement(cells, cell_weights),
    }


def stability(
    gold: dict[str, dict[str, Any]],
    first: dict[str, str | None],
    second: dict[str, str | None],
) -> dict[str, Any]:
    # All unique gold items are pairs. Two missing/unparseable answers do not
    # manufacture stability; an explicit allowed cannot_determine is retained.
    stable = sum(first.get(iid) is not None and first.get(iid) == second.get(iid) for iid in gold)
    return {"exact_label": stable / len(gold) if gold else None,
            "stable_pairs": stable, "n_pairs": len(gold)}


def language_gate(
    gold: dict[str, dict[str, Any]], answers: dict[str, str | None]
) -> dict[str, Any]:
    eligible = [iid for iid, item in gold.items()
                if item["l1"] == "not_qualifying" and (
                    item.get("construction_class") in {"a", "b", "c"}
                    or (not item.get("synthetic", False) and item["channel"] == "tool")
                )]
    prose_negatives = [iid for iid, item in gold.items()
                       if item["l1"] == "not_qualifying" and item["channel"] == "prose"]
    fp = sum(answers.get(iid) == "qualifying" for iid in eligible)
    prose_fp = sum(answers.get(iid) == "qualifying" for iid in prose_negatives)
    rate = fp / len(eligible) if eligible else None
    prose_rate = prose_fp / len(prose_negatives) if prose_negatives else None
    threshold = min(STANDARD["language_fpr_max"], prose_rate) if prose_rate is not None else None
    floor_met = len(eligible) >= STANDARD["language_floor"]
    return {
        "eligible_n": len(eligible),
        "false_positives": fp,
        "false_positive_rate": _round(rate),
        "prose_gold_negative_n": len(prose_negatives),
        "own_prose_false_positive_rate": _round(prose_rate),
        "effective_max": _round(threshold),
        "eligibility_floor_met": floor_met,
        "may_say_filtering": bool(floor_met and rate is not None and threshold is not None and rate <= threshold),
    }


def score_instrument(
    name: str,
    gold: dict[str, dict[str, Any]],
    pass1: dict[str, str | None],
    pass2: dict[str, str | None],
    *,
    track: str,
    positive: str,
    negative: str,
    cell_weights: dict[str, float],
    expected_cost: float | None = None,
) -> dict[str, Any]:
    first = score_pass(gold, pass1, track=track, positive=positive, negative=negative,
                       cell_weights=cell_weights)
    second = score_pass(gold, pass2, track=track, positive=positive, negative=negative,
                        cell_weights=cell_weights)
    stable = stability(gold, pass1, pass2)
    gaps = list(first["condition_gaps"].values())
    criteria = {
        "agreement_ge_0.90": (first["raw_strict_agreement"] or 0) >= STANDARD["agreement_min"],
        "condition_gaps_le_0.05": bool(gaps) and all(gap <= STANDARD["condition_gap_max"] for gap in gaps),
        "recall_ge_0.90": (first["recall"] or 0) >= STANDARD["recall_min"],
        "stability_ge_0.95": (stable["exact_label"] or 0) >= STANDARD["stability_min"],
    }
    qualifying_cells = [cell for cell in first["condition_channel_cells"] if not cell["thin"]]
    result = {
        "name": name,
        "track": track,
        "pass1": first,
        "pass2": second,
        "stability": stable,
        "criteria": criteria,
        "qualifies": all(criteria.values()),
        "minimum_qualifying_cell_accuracy": min(float(cell["accuracy"]) for cell in qualifying_cells)
            if qualifying_cells else None,
        "expected_cost": expected_cost,
    }
    if track == "l1":
        result["language_gate"] = language_gate(gold, pass1)
    return result


def tie_break(candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    qualifying = [value for value in candidates.values() if value["qualifies"]]
    comparison = []
    for value in qualifying:
        first = value["pass1"]
        comparison.append({
            "name": value["name"],
            "minimum_cell_accuracy": value["minimum_qualifying_cell_accuracy"],
            "specificity_all_channels": first["specificity_gold_negatives"],
            "specificity_tool_channel": first["specificity_tool_gold_negatives"],
            "stability": value["stability"]["exact_label"],
            "expected_cost": value["expected_cost"],
        })

    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -(row["minimum_cell_accuracy"] if row["minimum_cell_accuracy"] is not None else -math.inf),
            -(row["specificity_all_channels"] if row["specificity_all_channels"] is not None else -math.inf),
            -(row["specificity_tool_channel"] if row["specificity_tool_channel"] is not None else -math.inf),
            -(row["stability"] if row["stability"] is not None else -math.inf),
            row["expected_cost"] if row["expected_cost"] is not None else math.inf,
            row["name"],  # deterministic display only, not a frozen substantive splitter
        )

    comparison.sort(key=key)
    winner = comparison[0]["name"] if comparison else None
    unresolved = False
    if len(comparison) > 1:
        substantive = lambda row: tuple(row[field] for field in (
            "minimum_cell_accuracy", "specificity_all_channels", "specificity_tool_channel",
            "stability", "expected_cost"))
        unresolved = substantive(comparison[0]) == substantive(comparison[1])
        if unresolved:
            winner = None
    return {"qualifying_candidates": [row["name"] for row in comparison],
            "comparison": comparison, "winner": winner, "unresolved_exact_tie": unresolved}


def score_all(
    gold_rows: Iterable[dict[str, Any]],
    semantic_answers: dict[str, tuple[dict[str, str | None], dict[str, str | None]]],
    timing_answers: tuple[dict[str, str | None], dict[str, str | None]],
    *,
    cell_weights: dict[str, float],
    expected_costs: dict[str, float] | None = None,
    near_miss_classes: dict[str, str] | None = None,
) -> dict[str, Any]:
    gold = normalize_gold(gold_rows, near_miss_classes)
    costs = expected_costs or {}
    candidates = {
        name: score_instrument(name, gold, passes[0], passes[1], track="l1",
                               positive="qualifying", negative="not_qualifying",
                               cell_weights=cell_weights, expected_cost=costs.get(name))
        for name, passes in sorted(semantic_answers.items())
    }
    timing = score_instrument(
        "condition_invariant_intervention_signal_before_gate", gold,
        timing_answers[0], timing_answers[1], track="l2", positive="attempt", negative="no_attempt",
        cell_weights=cell_weights,
    )
    return {
        "schema_version": "instrument-closure-score-1.0.0",
        "standard": STANDARD,
        "gold_n": len(gold),
        "frame_condition_channel_weights": {key: _round(value) for key, value in sorted(cell_weights.items())},
        "semantic_candidates": candidates,
        "timing_instrument": timing,
        "tie_break": tie_break(candidates),
    }


def _fmt(value: Any) -> str:
    return "—" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Instrument-closure lane qualification table", "",
        "Generated offline by `score_lane.py`. Pass 1 supplies the frozen qualification figures; "
        "pass 2 is reported and paired over every gold item for stability.", "",
        "| Instrument | Track | N | Agreement | Recall | Stability | Prose gap | Tool gap | Specificity | Tool specificity | Min cell | Qualifies | Language gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    instruments = list(report["semantic_candidates"].values()) + [report["timing_instrument"]]
    for value in instruments:
        first = value["pass1"]
        language = value.get("language_gate", {})
        lines.append(
            f"| `{value['name']}` | {value['track'].upper()} | {first['n']} | {_fmt(first['raw_strict_agreement'])} | "
            f"{_fmt(first['recall'])} | {_fmt(value['stability']['exact_label'])} | "
            f"{_fmt(first['condition_gaps'].get('prose'))} | {_fmt(first['condition_gaps'].get('tool'))} | "
            f"{_fmt(first['specificity_gold_negatives'])} | {_fmt(first['specificity_tool_gold_negatives'])} | "
            f"{_fmt(value['minimum_qualifying_cell_accuracy'])} | {'yes' if value['qualifies'] else 'NO'} | "
            f"{('yes' if language.get('may_say_filtering') else 'no') if language else 'n/a'} |"
        )
    lines += ["", "Tie-break winner: " + (
        f"`{report['tie_break']['winner']}`." if report["tie_break"]["winner"] else
        ("unresolved exact tie." if report["tie_break"]["unresolved_exact_tie"] else "none; no semantic candidate qualified.")),
        "", "## Full pass-1 condition-by-channel cells", ""]
    for value in instruments:
        lines += [f"### `{value['name']}`", "",
                  "| Condition | Channel | N | Thin | Accuracy | Recall | Precision | FPR | FNR | TP | TN | FP | FN | Invalid |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for cell in value["pass1"]["condition_channel_cells"]:
            lines.append(
                f"| {cell['condition']} | {cell['channel']} | {cell['n']} | {'yes' if cell['thin'] else 'no'} | "
                f"{_fmt(cell['accuracy'])} | {_fmt(cell['recall'])} | {_fmt(cell['precision'])} | "
                f"{_fmt(cell['false_positive_rate'])} | {_fmt(cell['false_negative_rate'])} | "
                f"{cell['tp']} | {cell['tn']} | {cell['fp']} | {cell['fn']} | {cell['unparseable_or_abstain']} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _relative(path_text: str, parser: argparse.ArgumentParser) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        parser.error(f"paths must be repository-relative: {path}")
    return REPO / path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--frame", default="docs/review/judge-validation/instrument-closure-lane/frame.jsonl")
    parser.add_argument(
        "--near-miss-intent",
        default="docs/review/judge-validation/instrument-closure-lane/near_miss_intent.jsonl",
        help="score-time-only item-to-construction-class sidecar",
    )
    parser.add_argument("--candidate", nargs=3, action="append", metavar=("NAME", "PASS1", "PASS2"), required=True)
    parser.add_argument("--timing", nargs=2, required=True, metavar=("PASS1", "PASS2"))
    parser.add_argument("--cost", action="append", default=[], metavar="NAME=EXPECTED_COST")
    parser.add_argument("--out-json", default="docs/review/judge-validation/instrument-closure-lane/LANE_SCORES.json")
    parser.add_argument("--out-md", default="docs/review/judge-validation/instrument-closure-lane/LANE_SCORE_TABLE.md")
    args = parser.parse_args()

    costs: dict[str, float] = {}
    for value in args.cost:
        if "=" not in value:
            parser.error("--cost must be NAME=EXPECTED_COST")
        name, amount = value.split("=", 1)
        costs[name] = float(amount)
    semantic: dict[str, tuple[dict[str, str | None], dict[str, str | None]]] = {}
    for name, first_path, second_path in args.candidate:
        if name in semantic:
            parser.error(f"duplicate candidate {name}")
        allowed = {"qualifying", "not_qualifying", "cannot_determine"}
        semantic[name] = (
            normalize_answers(read_jsonl(_relative(first_path, parser)), allowed),
            normalize_answers(read_jsonl(_relative(second_path, parser)), allowed),
        )
    timing_allowed = {"attempt", "no_attempt", "cannot_determine"}
    timing = (
        normalize_answers(read_jsonl(_relative(args.timing[0], parser)), timing_allowed),
        normalize_answers(read_jsonl(_relative(args.timing[1], parser)), timing_allowed),
    )
    report = score_all(
        read_jsonl(_relative(args.gold, parser)), semantic, timing,
        cell_weights=frame_cell_weights(read_jsonl(_relative(args.frame, parser))),
        expected_costs=costs,
        near_miss_classes=normalize_near_miss_intent(
            read_jsonl(_relative(args.near_miss_intent, parser))
        ),
    )
    out_json = _relative(args.out_json, parser)
    out_md = _relative(args.out_md, parser)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(markdown(report), encoding="utf-8")
    print(f"scored semantic={len(semantic)} gold={report['gold_n']}; wrote {args.out_json} and {args.out_md}")


if __name__ == "__main__":
    main()
