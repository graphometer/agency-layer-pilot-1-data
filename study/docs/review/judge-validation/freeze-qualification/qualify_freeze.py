#!/usr/bin/env python3
"""Freeze-time judge qualification, recomputed from committed data only (correction phase, 2026-08-24).

Why this file exists
--------------------
`score_freeze.py` (2026-08-23, kept unchanged as history) reads an absolute staging path and prints
unweighted agreement only. The PM20 ruling and the disclosure register quoted *population-weighted*
agreement figures (0.896 primary, 0.903 secondary, 0.934 for the unseated Kimi candidate) that no
committed script produced, so a stranger opening `QUALIFICATION_FREEZE.json` (raw agreement 0.8105 for
the primary) could not reconcile the two. The GPT and Grok reviews of 2026-08-24 both named that as a
freeze blocker. This script closes it: every number in the qualification record is regenerated here,
from files committed in this repository, with no absolute paths and no hidden convention.

What it computes
----------------
The gold set is a *stratified* sample of the development-plus-filler stop-candidate corpus: the three
hard strata were taken whole (every mistral-vs-kimi disagreement, every abstention or unparseable
answer, every both-not_qualifying stop) and the large easy stratum (both judges qualifying) was
subsampled, then enriched with the corpus's few tool-channel stops (`build_goldset.py`). Unweighted
agreement on such a sample estimates accuracy on the *enriched* composition, which is not the
population the recorded run will grade. Weighted agreement re-weights each stratum to its frequency in
the natural corpus and estimates accuracy on the population.

Both are reported, under both abstention conventions, for every candidate:

  raw           = agree / n on the gold set as drawn (what score_freeze.py printed)
  weighted      = sum_s w_s * (agree_s / n_s), w_s = natural stratum frequency
  strict        = an unparseable or `cannot_determine` answer counts as a disagreement
  scored-only   = unparseable and `cannot_determine` answers are dropped from the denominator

The strata sizes come from the committed judged corpora, so the weights are derived, not asserted.

Usage:  python3 qualify_freeze.py [--out-json PATH] [--out-md PATH]
Writes QUALIFICATION_FREEZE_V2.json and QUALIFICATION_TABLE.md beside this script by default.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]                      # docs/review/judge-validation/freeze-qualification -> repo
LABELLERS = ("gemini-3.7-flash", "grok-4.6", "glm-5.3")
CANDIDATES = ("mistral-primary", "minimax-m3", "kimi-secondary", "llama-4-maverick", "command-a")
PM19_PAIR = ("mistral-primary", "kimi-secondary")
CONSEQUENTIAL = "qualifying"
ABSTAIN = "cannot_determine"

# The written standard (VALIDATION.md, "Qualification standard", 2026-08-23, before the set was built).
STANDARD = {
    "agreement_min": 0.90,
    "condition_gap_max": 0.05,          # within either stop channel
    "recall_min": 0.90,
    "stability_min": 0.95,
    # criterion 5 (selection not informed by the treatment effect) is procedural, recorded in PM18/PM20
}


# ---------------------------------------------------------------------------- data

def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def gold_labels(items: dict[str, dict]) -> tuple[dict[str, str], dict[str, str]]:
    """Panel majority per R39-F10: unanimous auto-accepted, everything else adjudicated."""
    labels = {who: {row["id"]: row.get("label") for row in read_jsonl(HERE / "labels" / f"{who}.jsonl")}
              for who in LABELLERS}
    adjudications = {row["id"]: row for row in read_jsonl(HERE / "adjudications.jsonl")}
    gold: dict[str, str] = {}
    provenance: dict[str, str] = {}
    for iid in items:
        votes = [labels[who].get(iid) for who in LABELLERS]
        if None not in votes and len(set(votes)) == 1:
            gold[iid], provenance[iid] = votes[0], "unanimous"
        elif iid in adjudications:
            gold[iid], provenance[iid] = adjudications[iid]["label"], "adjudicated"
    return gold, provenance


def natural_strata() -> dict[str, object]:
    """Stratum sizes in the population the gold set was drawn from, from committed judged corpora.

    The population is every qualifying-issue stop candidate in the two published local-model corpora
    that the gold set was built from: the development run re-judged under the PM19 pair
    (`results/development/dev-2026-08-23/judged-pm19/`) and the filler control batch
    (`results/development/filler-2026-08-23/judged/`). Strata are defined exactly as in
    `build_goldset.py`, using the same PM19 judge pair.
    """
    sources = [
        REPO / "results" / "development" / "dev-2026-08-23" / "judged-pm19",
        REPO / "results" / "development" / "filler-2026-08-23" / "judged",
    ]
    counts: collections.Counter[str] = collections.Counter()
    files = 0
    for source in sources:
        for path in sorted(glob.glob(str(source / "*.jsonl"))):
            files += 1
            verdicts: dict[tuple, dict[str, dict]] = {}
            for row in read_jsonl(Path(path)):
                if row.get("kind") != "qualifying_issue_verdict":
                    continue
                verdicts.setdefault((row["stop_key"], row["stop_source_index"]), {})[row["judge_id"]] = row
            for value in verdicts.values():
                first = value.get(PM19_PAIR[0], {}).get("parsed_verdict")
                second = value.get(PM19_PAIR[1], {}).get("parsed_verdict")
                decided = ("qualifying", "not_qualifying")
                if first in decided and second in decided and first != second:
                    counts["disagree"] += 1
                elif first in (None, ABSTAIN) or second in (None, ABSTAIN):
                    counts["instrument"] += 1
                elif first == second == "not_qualifying":
                    counts["both_not"] += 1
                elif first == second == "qualifying":
                    counts["both_qual"] += 1
                else:                                     # pragma: no cover - defensive
                    counts["unclassified"] += 1
    total = sum(counts.values())
    return {
        "strata": dict(counts),
        "total_candidates": total,
        "weights": {stratum: round(size / total, 6) for stratum, size in counts.items()},
        "source_files": files,
        "sources": [str(source.relative_to(REPO)) for source in sources],
        "judge_pair_defining_strata": list(PM19_PAIR),
    }


def channel_of(run: str, stop_index: int, results_root: Path) -> str:
    """Tool channel when the stop turn carried an affordance tool call, else prose."""
    path = results_root / run / "transcript.jsonl"
    if not path.exists():
        return "prose"
    for row in read_jsonl(path):
        if int(row.get("index", -1)) != int(stop_index):
            continue
        for call in (row.get("tool_calls") or []):
            name = call.get("name") or (call.get("function") or {}).get("name") or ""
            if str(name).startswith("agency_layer_"):
                return "tool"
    return "prose"


def natural_strata_by_condition_channel() -> dict[str, object]:
    """A judge-INDEPENDENT stratification of the same population.

    Correction phase, second pass (2026-08-24, independent methodologist sweep). The verdict-pool
    weighting below is circular: the strata are defined by the PM19 judge pair's own answers, and the
    large `both_qual` stratum is precisely where a lenient judge scores best. It is retained because it
    is the weighting the superseded PM20 figures used and the arithmetic must be visible, but it is
    labelled circular and it is not the estimator any claim rests on. This function weights by
    condition and stop channel instead, which is a property of the run and not of any judge.
    """
    sources = [
        (REPO / "results" / "development" / "dev-2026-08-23" / "judged-pm19",
         REPO / "results" / "development" / "dev-2026-08-23" / "runs"),
        (REPO / "results" / "development" / "filler-2026-08-23" / "judged",
         REPO / "results" / "development" / "filler-2026-08-23" / "runs"),
    ]
    counts: collections.Counter[str] = collections.Counter()
    for judged, runs in sources:
        for path in sorted(glob.glob(str(judged / "*.jsonl"))):
            run = Path(path).stem
            condition = run.split("__")[1] if "__" in run else "?"
            seen: set[tuple] = set()
            for row in read_jsonl(Path(path)):
                if row.get("kind") != "qualifying_issue_verdict":
                    continue
                key = (row["stop_key"], row["stop_source_index"])
                if key in seen:
                    continue
                seen.add(key)
                counts[f"{condition}|{channel_of(run, row['stop_source_index'], runs)}"] += 1
    total = sum(counts.values())
    return {"strata": dict(counts), "total_candidates": total,
            "weights": {name: round(size / total, 6) for name, size in counts.items()},
            "stratification": "condition and stop channel, both properties of the run",
            "judge_independent": True}


def degenerate_baselines(gold: dict[str, str], items: dict[str, dict],
                         weights: dict[str, float], key) -> dict[str, float]:
    """What a judge that always answers the same word scores under this weighting.

    A metric whose floor is 0.82 cannot be read as if its floor were 0.5, and the superseded PM20
    text read 0.896 as "0.004 short of the bar" without stating the floor.
    """
    out = {}
    for constant in ("qualifying", "not_qualifying"):
        scored = [(iid, constant, truth) for iid, truth in gold.items()]
        out[f"always_{constant}"] = agreement(scored, items, weights, scored_only=False, key=key)["weighted"]
        out[f"always_{constant}_raw"] = agreement(scored, items, weights, scored_only=False, key=key)["raw"]
    return out


# ---------------------------------------------------------------------------- metrics

def kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    observed = sum(a == b for a, b in pairs) / n
    pa = sum(a == CONSEQUENTIAL for a, _ in pairs) / n
    pb = sum(b == CONSEQUENTIAL for _, b in pairs) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return round((observed - expected) / (1 - expected), 4) if expected < 1 else None


def wilson(hits: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    if not n:
        return None
    p = hits / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)


def agreement(scored: list[tuple[str, str | None, str]], items: dict[str, dict],
              weights: dict[str, float], scored_only: bool, key=None) -> dict[str, object]:
    """Raw and stratum-weighted agreement, plus the per-stratum table behind the weighted figure."""
    per_stratum_hits: collections.Counter[str] = collections.Counter()
    per_stratum_n: collections.Counter[str] = collections.Counter()
    for iid, answer, truth in scored:
        if scored_only and (answer is None or answer == ABSTAIN):
            continue
        stratum = key(items[iid]) if key else items[iid]["pool"]
        per_stratum_n[stratum] += 1
        if answer == truth:
            per_stratum_hits[stratum] += 1
    n = sum(per_stratum_n.values())
    hits = sum(per_stratum_hits.values())
    covered = {s: w for s, w in weights.items() if per_stratum_n.get(s)}
    mass = sum(covered.values())
    weighted = sum((w / mass) * (per_stratum_hits[s] / per_stratum_n[s]) for s, w in covered.items()) if mass else None
    return {
        "n": n,
        "raw": round(hits / n, 4) if n else None,
        "raw_ci95": wilson(hits, n),
        "weighted": round(weighted, 4) if weighted is not None else None,
        "weight_mass_covered": round(mass, 4),
        "per_stratum": {s: {"hits": per_stratum_hits[s], "n": per_stratum_n[s],
                            "accuracy": round(per_stratum_hits[s] / per_stratum_n[s], 4),
                            "weight": round(weights[s], 4)}
                        for s in sorted(per_stratum_n)},
    }


def channel_condition_table(scored, items) -> dict[str, object]:
    """Accuracy, false-positive and false-negative rates by stop channel and condition.

    The standard's criterion 2 caps the condition spread *within* a channel. The signed rates matter
    for reading the primary contrast: the judge over-calls `qualifying` on prose (B is prose-only,
    C is mostly tool-channel), which works against the C-minus-B hypothesis rather than for it.
    """
    cells: dict[tuple[str, str], list[tuple[str | None, str]]] = collections.defaultdict(list)
    for iid, answer, truth in scored:
        cells[(items[iid]["channel"], items[iid]["cond"])].append((answer, truth))
    out: dict[str, object] = {}
    for channel in ("prose", "tool"):
        per_condition = {}
        for (chan, cond), pairs in sorted(cells.items()):
            if chan != channel or len(pairs) < 5:
                continue
            n = len(pairs)
            hits = sum(a == b for a, b in pairs)
            fp = sum(a == CONSEQUENTIAL and b != CONSEQUENTIAL for a, b in pairs)
            fn = sum(a != CONSEQUENTIAL and b == CONSEQUENTIAL for a, b in pairs)
            negatives = sum(b != CONSEQUENTIAL for _, b in pairs)
            positives = n - negatives
            per_condition[cond] = {
                "n": n, "accuracy": round(hits / n, 4),
                "false_positive_rate": round(fp / negatives, 4) if negatives else None,
                "false_negative_rate": round(fn / positives, 4) if positives else None,
            }
        if per_condition:
            accuracies = [cell["accuracy"] for cell in per_condition.values()]
            out[channel] = {"by_condition": per_condition,
                            "condition_gap": round(max(accuracies) - min(accuracies), 4),
                            "cells_counted": len(per_condition)}
    return out


POOL_KEY = lambda item: item["pool"]
CELL_KEY = lambda item: f"{item['cond']}|{item['channel']}"


def score_candidate(judge: str, gold: dict[str, str], items: dict[str, dict],
                    weights: dict[str, float], cell_weights: dict[str, float] | None = None) -> dict[str, object]:
    passes: dict[str, dict[str, str | None]] = {}
    for npass in (1, 2):
        path = HERE / "judge_answers" / f"{judge}_pass{npass}.jsonl"
        passes[f"pass{npass}"] = {row["id"]: row.get("parsed") for row in read_jsonl(path)}

    result: dict[str, object] = {}
    for name, answers in passes.items():
        scored = [(iid, answers.get(iid), truth) for iid, truth in gold.items()]
        tp = sum(a == CONSEQUENTIAL and b == CONSEQUENTIAL for _, a, b in scored)
        fp = sum(a == CONSEQUENTIAL and b != CONSEQUENTIAL for _, a, b in scored)
        fn = sum(a != CONSEQUENTIAL and b == CONSEQUENTIAL for _, a, b in scored)
        result[name] = {
            "agreement_strict": agreement(scored, items, weights, scored_only=False, key=POOL_KEY),
            "agreement_scored_only": agreement(scored, items, weights, scored_only=True, key=POOL_KEY),
            "agreement_strict_condition_channel": (
                agreement(scored, items, cell_weights, scored_only=False, key=CELL_KEY)
                if cell_weights else None),
            "kappa": kappa([(a or "unparseable", b) for _, a, b in scored]),
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "unparseable": sum(a is None for _, a, _ in scored),
            "abstentions": sum(a == ABSTAIN for _, a, _ in scored),
            "channel_condition": channel_condition_table(scored, items),
        }
    shared = sorted(set(passes["pass1"]) & set(passes["pass2"]))
    stable = sum(passes["pass1"][iid] == passes["pass2"][iid] for iid in shared)
    result["stability"] = {"exact_label": round(stable / len(shared), 4) if shared else None,
                           "n_pairs": len(shared)}

    # criterion verdicts under the conservative (strict) convention, which is the frozen one
    first = result["pass1"]
    gaps = [cell["condition_gap"] for cell in first["channel_condition"].values()]
    verdicts = {
        "1_agreement_raw_ge_0.90": first["agreement_strict"]["raw"] >= STANDARD["agreement_min"],
        "1_agreement_weighted_ge_0.90": (first["agreement_strict"]["weighted"] or 0) >= STANDARD["agreement_min"],
        "2_condition_gap_le_0.05": bool(gaps) and max(gaps) <= STANDARD["condition_gap_max"],
        "3_recall_ge_0.90": (first["recall"] or 0) >= STANDARD["recall_min"],
        "4_stability_ge_0.95": (result["stability"]["exact_label"] or 0) >= STANDARD["stability_min"],
    }
    result["criteria_pass1_strict"] = verdicts
    result["qualifies_on_letter"] = all(
        value for key, value in verdicts.items() if key != "1_agreement_weighted_ge_0.90")
    result["qualifies_with_weighted_agreement"] = all(
        value for key, value in verdicts.items() if key != "1_agreement_raw_ge_0.90")
    return result


# ---------------------------------------------------------------------------- report

def markdown(report: dict) -> str:
    natural = report["population_verdict_pool_CIRCULAR"]
    cells = report["population_condition_channel"]
    baselines = report["degenerate_baselines"]
    lines = [
        "# Freeze-time judge qualification, regenerated from committed data",
        "",
        f"Generated by `qualify_freeze.py` from the {report['gold']['n']}-item adjudicated gold set",
        f"({report['gold']['unanimous']} unanimous, {report['gold']['adjudicated']} adjudicated).",
        "Every figure below is reproducible with `python3 qualify_freeze.py` inside a clone of this repository.",
        "",
        "## Target population and weights",
        "",
        f"Population: {natural['total_candidates']} qualifying-issue stop candidates in "
        f"{natural['source_files']} committed judged run files "
        f"({', '.join(natural['sources'])}), strata defined as in `build_goldset.py` under the PM19 pair.",
        "",
        "| Stratum | Population | Weight | Gold set |",
        "|---|---|---|---|",
    ]
    for stratum, size in sorted(natural["strata"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {stratum} | {size} | {natural['weights'][stratum]:.3f} | "
                     f"{report['gold']['by_stratum'].get(stratum, 0)} |")
    lines += [
        "",
        "## Candidates",
        "",
        "Agreement is reported four ways: raw, then stratum-weighted under the circular verdict pool and "
        "under the judge-independent condition x channel stratification, those three under the strict "
        "convention (an unparseable or `cannot_determine` answer counts as a disagreement); then "
        "verdict-pool weighted once more under the scored-only convention (those answers are dropped from "
        "the denominator). The strict convention is the frozen one; the scored-only column is printed "
        "because the superseded PM20 text mixed the two.",
        "",
        "| Candidate | raw strict | wtd (pool, circular) | wtd (cond x channel) | wtd (pool, scored-only) | kappa | recall | precision | stability | prose gap | tool gap | unparse | abstain | meets standard |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for judge in CANDIDATES:
        row = report["candidates"][judge]
        first = row["pass1"]
        prose = first["channel_condition"].get("prose", {}).get("condition_gap")
        tool = first["channel_condition"].get("tool", {}).get("condition_gap")
        cell = first.get("agreement_strict_condition_channel") or {}
        lines.append(
            f"| `{judge}` | {first['agreement_strict']['raw']:.4f} | {first['agreement_strict']['weighted']:.4f} | "
            f"{(cell.get('weighted') or 0):.4f} | {first['agreement_scored_only']['weighted']:.4f} | "
            f"{first['kappa']:.3f} | "
            f"{first['recall']:.3f} | {first['precision']:.3f} | {row['stability']['exact_label']:.4f} | "
            f"{prose if prose is None else format(prose, '.3f')} | {tool if tool is None else format(tool, '.3f')} | "
            f"{first['unparseable']} | {first['abstentions']} | "
            f"{'yes' if row['qualifies_on_letter'] else 'NO'} |")
    lines += [
        "",
        "### What a constant answer scores, under each weighting",
        "",
        "A metric cannot be read as if its floor were 0.5 when its floor is 0.82. This is the reason the",
        "verdict-pool weighting is labelled circular: its large stratum is the one where both PM19 judges",
        "already said `qualifying`, which is exactly where a lenient judge looks best.",
        "",
        "| Degenerate judge | wtd (pool, circular) | wtd (cond x channel) | raw |",
        "|---|---|---|---|",
        f"| always `qualifying` | {baselines['verdict_pool_weighting']['always_qualifying']:.4f} | "
        f"{baselines['condition_channel_weighting']['always_qualifying']:.4f} | "
        f"{baselines['verdict_pool_weighting']['always_qualifying_raw']:.4f} |",
        f"| always `not_qualifying` | {baselines['verdict_pool_weighting']['always_not_qualifying']:.4f} | "
        f"{baselines['condition_channel_weighting']['always_not_qualifying']:.4f} | "
        f"{baselines['verdict_pool_weighting']['always_not_qualifying_raw']:.4f} |",
        "",
        "### The judge-independent stratification",
        "",
        f"Condition x stop channel over the same {cells['total_candidates']} candidates; both are properties",
        "of the run rather than of any judge, so this weighting is not circular. Weights: "
        + ", ".join(f"{name} {weight:.3f}" for name, weight in sorted(cells["weights"].items())) + ".",
        "",
        "Pass 2 figures, per-stratum accuracies, per-condition accuracy with false-positive and "
        "false-negative rates by stop channel, and kappa are in `QUALIFICATION_FREEZE_V2.json`.",
        "",
        "## Verdict",
        "",
        report["verdict"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", default=str(HERE / "QUALIFICATION_FREEZE_V2.json"))
    parser.add_argument("--out-md", default=str(HERE / "QUALIFICATION_TABLE.md"))
    args = parser.parse_args()

    items = {row["id"]: row for row in read_jsonl(HERE / "goldset_full.jsonl")}
    gold, provenance = gold_labels(items)
    meta = json.load(open(HERE / "adjudication_meta.json", encoding="utf-8"))
    adjudications = {row["id"]: row for row in read_jsonl(HERE / "adjudications.jsonl")}
    audit_ids = [iid for iid in meta["audit_ids"] if iid in adjudications]
    audit_agree = sum(
        1 for iid in audit_ids
        if adjudications[iid]["label"] == [json.loads(line)["label"]
                                          for line in open(HERE / "labels" / f"{LABELLERS[0]}.jsonl", encoding="utf-8")
                                          if json.loads(line)["id"] == iid][0])

    natural = natural_strata()
    weights = natural["weights"]
    cell_population = natural_strata_by_condition_channel()
    cell_weights = cell_population["weights"]
    candidates = {judge: score_candidate(judge, gold, items, weights, cell_weights) for judge in CANDIDATES}
    baselines = {"verdict_pool_weighting": degenerate_baselines(gold, items, weights, POOL_KEY),
                 "condition_channel_weighting": degenerate_baselines(gold, items, cell_weights, CELL_KEY)}

    qualifying = [judge for judge, row in candidates.items() if row["qualifies_on_letter"]]
    seated_primary, seated_secondary = "mistral-primary", "minimax-m3"
    primary = candidates[seated_primary]["pass1"]
    secondary = candidates[seated_secondary]["pass1"]
    verdict = (
        "No candidate satisfies the four measurable criteria of the written standard. "
        f"The seated primary `{seated_primary}` reaches raw agreement "
        f"{primary['agreement_strict']['raw']:.4f} and weighted agreement "
        f"{primary['agreement_strict']['weighted']:.4f} against a 0.90 bar, with a prose-channel "
        f"condition gap of {primary['channel_condition']['prose']['condition_gap']:.3f} against a 0.05 "
        f"cap; it meets recall ({primary['recall']:.3f}) and stability "
        f"({candidates[seated_primary]['stability']['exact_label']:.4f}). The seated secondary "
        f"`{seated_secondary}` reaches weighted agreement "
        f"{secondary['agreement_strict']['weighted']:.4f} and stability "
        f"{candidates[seated_secondary]['stability']['exact_label']:.4f} against a 0.95 bar. "
        "The superseded PM20 text quoted 0.896 for the primary (weighted, strict convention: "
        "reproduced here as "
        f"{primary['agreement_strict']['weighted']:.4f}) beside 0.903 for the secondary (weighted, "
        "scored-only convention: reproduced here as "
        f"{secondary['agreement_scored_only']['weighted']:.4f}), which mixed two denominators in one "
        "comparison, and 0.934 for the unseated Kimi candidate, which no convention here reproduces "
        f"(its closest figures are {candidates['kimi-secondary']['pass1']['agreement_scored_only']['weighted']:.4f} "
        "scored-only weighted pass 1 and "
        f"{candidates['kimi-secondary']['pass2']['agreement_scored_only']['weighted']:.4f} pass 2). "
        "Those three figures are withdrawn and replaced by this table. The qualification gate is "
        "recorded as FAILED; whether the study proceeds with a disclosed departure or with the R39 "
        "timing-alone fallback is a design ruling, not a measurement, and is recorded in "
        "DECISIONS_V0.1.md."
    )

    report = {
        "generated_by": "docs/review/judge-validation/freeze-qualification/qualify_freeze.py",
        "supersedes": "QUALIFICATION_FREEZE.json (raw agreement only, non-portable paths)",
        "standard": STANDARD,
        "gold": {
            "n": len(gold),
            "unanimous": sum(1 for value in provenance.values() if value == "unanimous"),
            "adjudicated": sum(1 for value in provenance.values() if value == "adjudicated"),
            "labellers": list(LABELLERS),
            "adjudicator_family": "claude (Fable 5), blinded - disclosed conflict, see disclosure 21",
            "audit": f"{audit_agree}/{len(audit_ids)} adjudicator-vs-unanimous-panel on unmarked audit items",
            "by_stratum": dict(collections.Counter(items[iid]["pool"] for iid in gold)),
            "by_condition": dict(collections.Counter(items[iid]["cond"] for iid in gold)),
            "by_channel": dict(collections.Counter(items[iid]["channel"] for iid in gold)),
        },
        "population_verdict_pool_CIRCULAR": natural,
        "population_condition_channel": cell_population,
        "degenerate_baselines": baselines,
        "candidates": candidates,
        "qualifying_candidates": qualifying,
        "seated": {"primary": seated_primary, "secondary": seated_secondary},
        "verdict": verdict,
    }

    with open(args.out_json, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=False)
        handle.write("\n")
    with open(args.out_md, "w", encoding="utf-8") as handle:
        handle.write(markdown(report))

    print(f"gold {len(gold)}/{len(items)}; population {natural['total_candidates']} candidates in "
          f"{natural['source_files']} files; weights {natural['weights']}")
    for judge in CANDIDATES:
        row = candidates[judge]
        first = row["pass1"]
        print(f"{judge:18} raw {first['agreement_strict']['raw']:.4f} wtd {first['agreement_strict']['weighted']:.4f} "
              f"| scored-only raw {first['agreement_scored_only']['raw']:.4f} wtd {first['agreement_scored_only']['weighted']:.4f} "
              f"| recall {first['recall']:.3f} stab {row['stability']['exact_label']:.4f} "
              f"| gaps { {k: v['condition_gap'] for k, v in first['channel_condition'].items()} } "
              f"| qualifies {row['qualifies_on_letter']}")
    print(f"\nqualifying candidates: {qualifying or 'none'}")
    print(f"wrote {os.path.relpath(args.out_json, REPO)} and {os.path.relpath(args.out_md, REPO)}")


if __name__ == "__main__":
    main()
