#!/usr/bin/env python3
"""Separate deterministic analysis artifact for Agency Layer Pilot I Part B."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable

from part_b_grade import grade_run_directory


ARTIFACT_VERSION = "part-b-analysis-1.2.0"
PACKAGE_ROOT = Path(__file__).resolve().parent
CODE_FILES = ("part_b_grade.py", "part_b_analysis.py")
ENDPOINT = "scenario_concordant_structured_intervention_before_gate"
STAGE1_ROOT = PACKAGE_ROOT.parent / "runners" / "stage1"
PRIMARY_PLAN = STAGE1_ROOT / "plan_fresh_recorded.yaml"
LOCAL_PLAN = STAGE1_ROOT / "plan_fresh_local_recorded.yaml"
SEALED_SCENARIOS_ROOT = PACKAGE_ROOT.parent / "scenarios-part-b"
SEAL_MANIFEST = PACKAGE_ROOT.parents[1] / "docs" / "review" / "part-b-scenarios" / "SEAL_MANIFEST.json"
SEALED_SET_SHA256 = "658c066240c1a16ba7570e727d2d7fc1de089c347caf4150b574efedc3c8fa94"
EXPECTED_BATCH_IDS = frozenset({"recorded-fresh-s1", "recorded-fresh-local-s1"})
OWNER_RELEASE_RULING = "R66-2026-09-03"


def _plan_subjects(path: Path) -> frozenset[str]:
    import yaml
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return frozenset(str(value) for value in payload["expect"]["per_subject"])


PRIMARY_SUBJECTS = _plan_subjects(PRIMARY_PLAN)
LOCAL_EXPLORATORY_SUBJECTS = _plan_subjects(LOCAL_PLAN)
ALLOWED_SUBJECTS = PRIMARY_SUBJECTS | LOCAL_EXPLORATORY_SUBJECTS
CONDITIONS = frozenset({"C", "D"})
Z95 = 1.959963984540054


def discover_repository_root(package_root: str | Path = PACKAGE_ROOT) -> Path | None:
    """Mirror analysis.py: find only the repository that owns this package."""
    package = Path(package_root).resolve()
    for candidate in (package, *package.parents):
        if not (candidate / "CONDITIONS.md").is_file() or not (candidate / ".git").exists():
            continue
        try:
            top = subprocess.run(["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
                                 check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
        if Path(top).resolve() == candidate:
            return candidate
    return None


REPOSITORY_ROOT = discover_repository_root()


def code_provenance() -> dict[str, Any]:
    """Mirror analysis.py's provenance block for the Part B code that produced this artifact.

    Part B's endpoint is deterministic and makes zero instrument calls, so the judge pair and the
    rubric versions Part A records have no counterpart here and none are asserted.
    """
    warnings: list[str] = []
    repository_commit = None
    if REPOSITORY_ROOT is None:
        warnings.append("repository_commit is null because the package is not inside its own Agency Layer git repository")
    else:
        try:
            repository_commit = subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            warnings.append(f"repository_commit is null because package repository discovery failed: {type(exc).__name__}")
    return {
        "repository_commit": repository_commit,
        "code_sha256": {name: hashlib.sha256((PACKAGE_ROOT / name).read_bytes()).hexdigest()
                        for name in CODE_FILES},
        "instrument_calls": 0,
        "note": "Part B is deterministic and makes zero instrument calls: no judge pair and no rubric versions apply.",
        "warnings": warnings,
    }


def stable_seed(*identifiers: Any) -> int:
    """Mirror analysis.py: sort string identifiers, hash with SHA-256, take 64 bits."""
    material = "|".join(sorted(str(value) for value in identifiers))
    return int(hashlib.sha256(material.encode()).hexdigest()[:16], 16)


def wilson(successes: int, n: int) -> dict[str, Any]:
    if n == 0:
        return {"successes": 0, "n": 0, "rate": None, "low": None, "high": None}
    proportion = successes / n
    denominator = 1 + Z95 * Z95 / n
    center = (proportion + Z95 * Z95 / (2 * n)) / denominator
    half = Z95 * math.sqrt(proportion * (1 - proportion) / n + Z95 * Z95 / (4 * n * n)) / denominator
    return {
        "successes": successes, "n": n, "rate": proportion,
        "low": max(0.0, center - half), "high": min(1.0, center + half),
    }


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def scenario_bootstrap(differences: list[dict[str, Any]], seed: int, samples: int = 2000) -> dict[str, Any]:
    if not differences:
        return {"estimate": None, "low": None, "high": None, "clusters": 0, "samples": samples}
    by_family: dict[int, list[float]] = defaultdict(list)
    for row in differences:
        by_family[int(row["family"])].append(float(row["difference"]))
    generator = random.Random(seed)
    draws: list[float] = []
    for _ in range(samples):
        sample: list[float] = []
        for family in sorted(by_family):
            values = by_family[family]
            sample.extend(generator.choice(values) for _ in range(len(values)))
        draws.append(mean(sample))
    return {
        "estimate": mean(float(row["difference"]) for row in differences),
        "low": quantile(draws, 0.025), "high": quantile(draws, 0.975),
        "clusters": len(differences), "samples": samples,
    }


def sign_flip_p(differences: list[dict[str, Any]], seed: int, samples: int = 20000) -> float | None:
    if not differences:
        return None
    values = [float(row["difference"]) for row in differences]
    observed = abs(mean(values))
    generator = random.Random(seed)
    exceed = 1
    for _ in range(samples):
        permuted = mean(value * (1 if generator.random() < 0.5 else -1) for value in values)
        exceed += abs(permuted) >= observed - 1e-15
    return exceed / (samples + 1)


def parse_run_id(run_id: str) -> dict[str, Any]:
    parts = (run_id.split("__") + ["", "", "", ""])[:4]
    scenario_id, condition, model_id, repeat = parts
    family = 0
    if scenario_id.startswith("fb") and "-" in scenario_id:
        try:
            family = int(scenario_id[2:].split("-", 1)[0])
        except ValueError:
            pass
    return {
        "run_id": run_id, "scenario_id": scenario_id, "condition": condition,
        "model_id": model_id, "repeat_index": repeat, "family": family,
    }


def _record_metadata(record: dict[str, Any]) -> dict[str, Any]:
    grade = record.get("grade", record)
    run = record.get("run", {})
    return {
        "run_id": str(grade.get("run_id") or run.get("run_id") or ""),
        "scenario_id": str(grade.get("scenario_id") or run.get("scenario_id") or ""),
        "condition": str(grade.get("condition") or run.get("condition") or ""),
        "model_id": str(grade.get("model_id") or run.get("model_id") or ""),
        "family": int(grade.get("family", 0) or 0),
    }


def adverse_missing_record(run_id: str, reason: str = "planned_run_missing") -> dict[str, Any]:
    metadata = parse_run_id(run_id)
    grade = {
        **metadata, "schema_version": "part-b-grade-1.0.0", "record_complete": False,
        "gradeable": False, "incomplete_reasons": [reason], ENDPOINT: False,
        "observable_chain": {
            "valid_invocation_before_gate": False,
            "scenario_concordant_invocation_before_gate": False,
            "promised_transition_performed": None,
            "consequential_action_prevented": None,
            "post_invocation_or_override": "missing_record",
        },
        "action_mix": {name: 0 for name in ("clarify", "dissent", "pause", "decline", "archive")},
        "non_concordant_stop": False, "gate_attempts": 0, "task_completed": False,
        "malformed_calls": 0, "post_invocation_behavior": "missing_record", "passthrough": {},
    }
    return {"run": metadata, "grade": grade, "planned_only": True}


def reconcile_records(records: list[dict[str, Any]], planned_run_ids: Iterable[str] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    planned_items = [str(item) for item in (planned_run_ids or [])]
    duplicate_planned = sorted(run_id for run_id, count in Counter(planned_items).items() if count > 1)
    planned = sorted(set(planned_items))
    archived = [record for record in records if record.get("archived_attempt", False)]
    active = [record for record in records if not record.get("archived_attempt", False)]
    observed_ids = [_record_metadata(record)["run_id"] for record in active]
    duplicate_observed = sorted(run_id for run_id, count in Counter(observed_ids).items() if run_id and count > 1)
    observed = set(observed_ids)
    missing = sorted(set(planned) - observed)
    unplanned = sorted(observed - set(planned)) if planned else sorted(observed)
    complete = active + [adverse_missing_record(run_id) for run_id in missing]
    reconciliation = {
        "manifest_present": bool(planned), "planned": len(planned), "observed": len(observed),
        "analysed": len(complete), "missing_planned": missing, "unplanned_observed": unplanned,
        "duplicate_planned": duplicate_planned, "duplicate_observed": duplicate_observed,
        "archived_attempts": len(archived),
        "reconciled": bool(planned) and not missing and not unplanned and not duplicate_planned and not duplicate_observed and len(complete) == len(planned),
    }
    return complete, reconciliation


def assert_primary_partition(
    records: list[dict[str, Any]], primary_pool: list[dict[str, Any]]
) -> None:
    """Guard the declared sets and the actual pool built from unfiltered records."""
    if len(PRIMARY_SUBJECTS) != 4:
        raise AssertionError("the Part B primary subject declaration is not the frozen four")
    if len(LOCAL_EXPLORATORY_SUBJECTS) != 2:
        raise AssertionError("the Part B local subject declaration is not the frozen two")
    if not PRIMARY_SUBJECTS.isdisjoint(LOCAL_EXPLORATORY_SUBJECTS):
        raise AssertionError("the primary and local exploratory subject declarations overlap")
    local_rows = [record for record in records if _record_metadata(record)["model_id"] in LOCAL_EXPLORATORY_SUBJECTS]
    if any(record in primary_pool for record in local_rows):
        raise AssertionError("a local exploratory subject entered the Part B primary pool")
    if any(_record_metadata(record)["model_id"] not in PRIMARY_SUBJECTS for record in primary_pool):
        raise AssertionError("the Part B primary pool contains an undeclared subject")


def _value(record: dict[str, Any], denominator: str) -> bool | None:
    grade = record.get("grade", record)
    value = grade.get(ENDPOINT)
    if denominator == "gradeable" and not grade.get("gradeable", False):
        return None
    if denominator == "all_attempts" and value is None:
        return False
    return bool(value) if value is not None else None


def _rates(records: list[dict[str, Any]], population: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for denominator in ("all_attempts", "gradeable"):
        for condition in ("C", "D"):
            subset = [record for record in records if _record_metadata(record)["condition"] == condition]
            values = [value for record in subset if (value := _value(record, denominator)) is not None]
            rows.append({
                "population": population, "endpoint": ENDPOINT, "denominator": denominator,
                "condition": condition, **wilson(sum(values), len(values)),
            })
    return rows


def scenario_differences(records: list[dict[str, Any]], denominator: str, model_id: str | None = None, family: int | None = None) -> list[dict[str, Any]]:
    cells: dict[tuple[int, str, str], list[bool]] = defaultdict(list)
    for record in records:
        metadata = _record_metadata(record)
        if metadata["condition"] not in CONDITIONS:
            continue
        if model_id is not None and metadata["model_id"] != model_id:
            continue
        if family is not None and metadata["family"] != family:
            continue
        value = _value(record, denominator)
        if value is not None:
            cells[(metadata["family"], metadata["scenario_id"], metadata["condition"])].append(value)
    differences: list[dict[str, Any]] = []
    for cell_family, scenario_id in sorted({(key[0], key[1]) for key in cells}):
        c_values = cells.get((cell_family, scenario_id, "C"), [])
        d_values = cells.get((cell_family, scenario_id, "D"), [])
        if c_values and d_values:
            differences.append({
                "family": cell_family, "scenario_id": scenario_id,
                "c_successes": sum(c_values), "c_n": len(c_values),
                "d_successes": sum(d_values), "d_n": len(d_values),
                "difference": mean(c_values) - mean(d_values),
            })
    return differences


def _contrast(records: list[dict[str, Any]], denominator: str, population: str, model_id: str | None = None, confirmatory: bool = False) -> dict[str, Any]:
    differences = scenario_differences(records, denominator, model_id)
    identifiers = sorted(row["scenario_id"] for row in differences)
    bootstrap_seed = stable_seed(ENDPOINT, denominator, model_id or "pooled", *identifiers)
    row = {
        "population": population, "endpoint": ENDPOINT, "denominator": denominator,
        "model_id": model_id or "pooled", "contrast": "C_minus_D",
        "c_successes": sum(row["c_successes"] for row in differences),
        "c_n": sum(row["c_n"] for row in differences),
        "d_successes": sum(row["d_successes"] for row in differences),
        "d_n": sum(row["d_n"] for row in differences),
        **scenario_bootstrap(differences, bootstrap_seed, 2000),
        "bootstrap_seed": bootstrap_seed,
        "paired_differences": differences,
        "confirmatory": confirmatory,
    }
    if confirmatory:
        sign_seed = stable_seed("two-sided", ENDPOINT, *identifiers)
        p_value = sign_flip_p(differences, sign_seed, 20000)
        row.update({
            "p_value": p_value, "p_value_source": "scenario_cluster_sign_flip_two_sided",
            "sign_flip_samples": 20000, "sign_flip_seed": sign_seed,
            "two_sided_rejection_0_05": p_value is not None and p_value <= 0.05,
            "direction": "C_greater_D" if row["estimate"] is not None and row["estimate"] > 0 else ("C_less_D" if row["estimate"] is not None and row["estimate"] < 0 else "tie"),
        })
    else:
        row.update({"p_value": None, "p_value_source": None, "two_sided_rejection_0_05": None})
    return row


def _subject_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_rates: list[dict[str, Any]] = []
    complete_pair_contrasts: list[dict[str, Any]] = []
    models = sorted({_record_metadata(record)["model_id"] for record in records if _record_metadata(record)["model_id"] in ALLOWED_SUBJECTS})
    for model in models:
        subset = [record for record in records if _record_metadata(record)["model_id"] == model]
        role = "local_exploratory" if model in LOCAL_EXPLORATORY_SUBJECTS else "primary_subject_descriptive"
        for denominator in ("all_attempts", "gradeable"):
            # Raw condition rates do not apply a paired-cell deletion rule.
            for row in _rates(subset, role):
                if row["denominator"] == denominator:
                    raw_rates.append({**row, "model_id": model,
                                      "population_basis": "all subject records in the named condition; no paired-scenario deletion"})
            contrast = _contrast(subset, denominator, role, model_id=model, confirmatory=False)
            observed_scenarios = sorted({_record_metadata(record)["scenario_id"] for record in subset
                                         if _record_metadata(record)["condition"] in CONDITIONS
                                         and _value(record, denominator) is not None})
            complete_scenarios = sorted(row["scenario_id"] for row in contrast["paired_differences"])
            complete_pair_contrasts.append({
                **contrast,
                "pairing_rule": "include a scenario only when the subject has one or more eligible observations in both C and D",
                "dropped_scenarios": sorted(set(observed_scenarios) - set(complete_scenarios)),
            })
    return {"raw_condition_rates": raw_rates, "complete_pair_contrasts": complete_pair_contrasts,
            "note": "Raw rates retain every eligible observation. Complete-pair contrasts exclude only scenarios missing an eligible observation in either condition, listed per subject and denominator."}


def _family_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in (2, 3, 4, 6):
        family_records = [record for record in records if _record_metadata(record)["family"] == family]
        for denominator in ("all_attempts", "gradeable"):
            for condition in ("C", "D"):
                subset = [record for record in family_records if _record_metadata(record)["condition"] == condition]
                values = [value for record in subset if (value := _value(record, denominator)) is not None]
                rows.append({"family": family, "denominator": denominator, "condition": condition, **wilson(sum(values), len(values))})
            differences = scenario_differences(family_records, denominator)
            identifiers = sorted(row["scenario_id"] for row in differences)
            rows.append({
                "family": family, "denominator": denominator, "condition": "C_minus_D",
                "c_successes": sum(row["c_successes"] for row in differences), "c_n": sum(row["c_n"] for row in differences),
                "d_successes": sum(row["d_successes"] for row in differences), "d_n": sum(row["d_n"] for row in differences),
                **scenario_bootstrap(differences, stable_seed("part-b-family", family, denominator, *identifiers)),
            })
    return rows


def _funnel(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "valid_invocation_before_gate", "scenario_concordant_invocation_before_gate",
        "promised_transition_performed", "consequential_action_prevented",
    )
    rows: list[dict[str, Any]] = []
    for condition in ("C", "D"):
        subset = [record for record in records if _record_metadata(record)["condition"] == condition]
        for field in fields:
            observed = [(record.get("grade", record).get("observable_chain") or {}).get(field) for record in subset]
            values = [bool(value) for value in observed if value is not None]
            rows.append({"condition": condition, "stage": field, **wilson(sum(values), len(values)), "scheduled_n": len(subset)})
    return rows


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    return {"n": len(values), "sum": sum(values) if values else 0, "mean": mean(values) if values else None}


def _descriptives(records: list[dict[str, Any]]) -> dict[str, Any]:
    action_mix: Counter[str] = Counter()
    post_behavior: Counter[str] = Counter()
    for record in records:
        grade = record.get("grade", record)
        action_mix.update({key: int(value or 0) for key, value in (grade.get("action_mix") or {}).items()})
        post_behavior[str(grade.get("post_invocation_behavior", "unknown"))] += 1
    numeric: dict[str, dict[str, Any]] = {}
    for field in ("latency_seconds", "input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "model_calls", "cost_usd"):
        values = []
        for record in records:
            value = (record.get("grade", record).get("passthrough") or {}).get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
        numeric[field] = _numeric_summary(values)
    return {
        "scheduled_n": len(records), "action_mix": dict(sorted(action_mix.items())),
        "non_concordant_stop": sum(bool(record.get("grade", record).get("non_concordant_stop")) for record in records),
        "gate_attempts": sum(int(record.get("grade", record).get("gate_attempts", 0) or 0) for record in records),
        "completion": sum(bool(record.get("grade", record).get("task_completed")) for record in records),
        "malformed_calls": sum(int(record.get("grade", record).get("malformed_calls", 0) or 0) for record in records),
        "post_invocation_behavior": dict(sorted(post_behavior.items())),
        "latency_tokens_cost": numeric,
    }


def build_artifact(records: list[dict[str, Any]], planned_run_ids: Iterable[str] | None,
                   source: str = "in-memory", *, recorded_mode: bool = False,
                   seal_validation: dict[str, Any] | None = None,
                   package_validation: dict[str, Any] | None = None,
                   owner_release_ruling: str | None = None) -> dict[str, Any]:
    reconciled_records, reconciliation = reconcile_records(records, planned_run_ids)
    invalid_cells = sorted({
        f"{metadata['run_id']}:{metadata['condition']}:{metadata['model_id']}"
        for record in reconciled_records
        if (metadata := _record_metadata(record))["condition"] not in CONDITIONS or metadata["model_id"] not in ALLOWED_SUBJECTS
    })
    primary_records = [record for record in reconciled_records if _record_metadata(record)["model_id"] in PRIMARY_SUBJECTS and _record_metadata(record)["condition"] in CONDITIONS]
    local_records = [record for record in reconciled_records if _record_metadata(record)["model_id"] in LOCAL_EXPLORATORY_SUBJECTS and _record_metadata(record)["condition"] in CONDITIONS]
    assert_primary_partition(reconciled_records, primary_records)
    local_arms_can_enter_primary_pool = any(
        _record_metadata(record)["model_id"] in LOCAL_EXPLORATORY_SUBJECTS
        for record in primary_records
    )
    primary_scenarios = sorted({_record_metadata(record)["scenario_id"] for record in primary_records})
    primary_models_observed = {_record_metadata(record)["model_id"] for record in primary_records}
    primary_cells = Counter(
        (_record_metadata(record)["scenario_id"], _record_metadata(record)["model_id"], _record_metadata(record)["condition"])
        for record in primary_records
    )
    primary_cell_violations = sorted(
        f"{scenario_id}|{model_id}|{condition}:{primary_cells.get((scenario_id, model_id, condition), 0)}"
        for scenario_id in primary_scenarios
        for model_id in sorted(PRIMARY_SUBJECTS)
        for condition in ("C", "D")
        if primary_cells.get((scenario_id, model_id, condition), 0) != 2
    )
    primary_contrast = _contrast(primary_records, "all_attempts", "part_b_primary", confirmatory=True)
    gradeable_contrast = _contrast(primary_records, "gradeable", "part_b_primary", confirmatory=False)
    seal = seal_validation or {"valid": False, "reason": "seal was not verified"}
    package = package_validation or {"valid": False, "reason": "combined primary and local package was not supplied"}
    sealed_ids = set(seal.get("scenario_ids", []))
    scenario_set_matches = bool(sealed_ids) and set(primary_scenarios) == sealed_ids
    confirmatory_ready = (
        len(primary_scenarios) == 40
        and primary_contrast["clusters"] == 40
        and primary_models_observed == PRIMARY_SUBJECTS
        and not primary_cell_violations
        and len(primary_records) == 640
    )
    technical_gates_passed = (recorded_mode and reconciliation["reconciled"] and not invalid_cells
                              and confirmatory_ready and scenario_set_matches
                              and bool(seal.get("valid")) and bool(package.get("valid")))
    release_ruling_valid = owner_release_ruling == OWNER_RELEASE_RULING
    release_approved = technical_gates_passed and release_ruling_valid
    warnings: list[str] = []
    if not reconciliation["reconciled"]:
        warnings.append("planned-to-analysed rows did not reconcile")
    if invalid_cells:
        warnings.append("the input contains undeclared Part B condition/subject cells")
    if not confirmatory_ready:
        warnings.append("the confirmatory analysis does not contain the frozen 40-scenario, four-subject, C/D, two-repeat matrix")
    if not recorded_mode:
        warnings.append("non-recorded analysis mode; this artifact cannot be published as the package result")
    if recorded_mode and not scenario_set_matches:
        warnings.append("the primary scenario id set does not equal the 40 sealed ids")
    if recorded_mode and not seal.get("valid"):
        warnings.append(f"Part B seal verification failed: {seal.get('reason', 'unknown reason')}")
    if recorded_mode and not package.get("valid"):
        warnings.append(f"combined Part B package validation failed: {package.get('reason', 'unknown reason')}")
    release_open_items: list[str] = []
    if not technical_gates_passed:
        release_open_items.append("technical artifact gates are not all satisfied")
    if not release_ruling_valid:
        release_open_items.append(f"owner release ruling {OWNER_RELEASE_RULING} was not supplied")
    warnings.extend(release_open_items)
    return {
        "schema_version": ARTIFACT_VERSION,
        "endpoint": ENDPOINT,
        "source": source,
        "provenance": code_provenance(),
        "technical_gates": {"passed": technical_gates_passed,
                            "recorded_mode": recorded_mode,
                            "reconciled": reconciliation["reconciled"],
                            "no_invalid_cells": not invalid_cells,
                            "confirmatory_ready": confirmatory_ready,
                            "sealed_scenarios_match": scenario_set_matches,
                            "seal_valid": bool(seal.get("valid")),
                            "package_valid": bool(package.get("valid"))},
        "owner_release_ruling": owner_release_ruling,
        "release_status": {"status": "approved_for_release" if release_approved else "blocked",
                           "open_items": release_open_items},
        "publishable_as_result": release_approved,
        "warnings": warnings,
        "analysis_mode": "recorded" if recorded_mode else "non-recorded",
        "seal_validation": seal,
        "package_validation": package,
        "reconciliation": reconciliation,
        "subject_partition": {
            "primary_subjects": sorted(PRIMARY_SUBJECTS),
            "local_exploratory_subjects": sorted(LOCAL_EXPLORATORY_SUBJECTS),
            "primary_pool_models_observed": sorted({_record_metadata(record)["model_id"] for record in primary_records}),
            "local_models_observed": sorted({_record_metadata(record)["model_id"] for record in local_records}),
            "local_arms_can_enter_primary_pool": local_arms_can_enter_primary_pool,
        },
        "methods": {
            "primary_contrast": "C_minus_D", "primary_denominator": "all_attempts",
            "estimand": "mean_scenario_paired_risk_difference",
            "sign_flip_sides": "two-sided", "sign_flip_samples": 20000,
            "bootstrap_samples": 2000, "bootstrap_unit": "scenario_cluster_within_family",
            "raw_rate_interval": "Wilson 95%", "confirmatory_family_size": 1,
            "direction_required": False, "part_a_confirmation_rule_applies": False,
        },
        "counts": {
            "analysed_rows": len(reconciled_records), "primary_rows": len(primary_records),
            "local_exploratory_rows": len(local_records), "primary_scenario_clusters": len(primary_scenarios),
            "primary_cell_violations": primary_cell_violations,
        },
        "primary": {
            "confirmatory_ready": confirmatory_ready,
            "all_attempts_contrast": primary_contrast,
            "gradeable_only_contrast": gradeable_contrast,
            "raw_rates": _rates(primary_records, "part_b_primary"),
        },
        "per_subject_c_minus_d": _subject_rows(primary_records + local_records),
        "published_field_notes": {"fabrication_present": {
            "status": "omitted",
            "reason": "The frozen Part B checkers do not provide a comparable fabrication signal across families, and the flag never enters the endpoint.",
        }},
        "per_family": _family_rows(primary_records),
        "observable_chain_funnel": _funnel(primary_records),
        "descriptives": {
            "primary": _descriptives(primary_records),
            "local_exploratory_by_subject": {
                model: _descriptives([record for record in local_records if _record_metadata(record)["model_id"] == model])
                for model in sorted(LOCAL_EXPLORATORY_SUBJECTS)
            },
        },
        "invalid_cells": invalid_cells,
    }


def load_manifest(path: str | Path) -> list[str]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = payload.get("tranches") if isinstance(payload, dict) else payload
    planned: list[str] = []
    for entry in entries or []:
        planned.extend(str(run_id) for run_id in entry.get("planned_run_ids", []))
    return planned


def manifest_metadata(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"path": str(path), "batch_id": payload.get("batch_id"),
            "planned_run_ids": load_manifest(path)}


def verify_sealed_scenarios(root: str | Path = SEALED_SCENARIOS_ROOT) -> dict[str, Any]:
    root = Path(root)
    committed = json.loads(SEAL_MANIFEST.read_text(encoding="utf-8"))
    manifests = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("fb")):
        entries = []
        for path in sorted(p for p in folder.rglob("*") if p.is_file()
                           and "__pycache__" not in p.parts and p.suffix != ".pyc"):
            entries.append({"path": path.relative_to(folder).as_posix(),
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        rolled = hashlib.sha256("\n".join(
            f"{entry['path']}:{entry['sha256']}" for entry in entries).encode()).hexdigest()
        manifests.append({"id": folder.name, "files": entries, "folder_sha256": rolled})
    set_hash = hashlib.sha256("\n".join(
        f"{item['id']}:{item['folder_sha256']}" for item in manifests).encode()).hexdigest()
    ids = [item["id"] for item in manifests]
    valid = (len(ids) == 40 and set_hash == SEALED_SET_SHA256
             and set_hash == committed.get("set_sha256")
             and manifests == committed.get("scenarios"))
    reason = "verified" if valid else (
        f"recomputed set hash {set_hash} / {len(ids)} scenarios does not match the committed seal")
    return {"valid": valid, "reason": reason, "set_sha256": set_hash,
            "expected_set_sha256": SEALED_SET_SHA256, "scenario_ids": ids}


def validate_combined_package(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    batch_ids = [item.get("batch_id") for item in manifests]
    planned_sets = [set(item["planned_run_ids"]) for item in manifests]
    disjoint = len(planned_sets) == 2 and not (planned_sets[0] & planned_sets[1])
    valid = (len(manifests) == 2 and set(batch_ids) == EXPECTED_BATCH_IDS and disjoint)
    reason = "verified" if valid else (
        f"need exactly the fixed, disjoint batches {sorted(EXPECTED_BATCH_IDS)}; got {batch_ids}")
    return {"valid": valid, "reason": reason, "batch_ids": batch_ids,
            "disjoint_planned_cells": disjoint}


def _find_scenario(scenarios_root: Path, scenario_id: str) -> Path:
    candidates = sorted(scenarios_root.rglob("scenario.yaml"))
    for candidate in candidates:
        if candidate.parent.name == scenario_id:
            return candidate
    raise FileNotFoundError(f"scenario.yaml not found for {scenario_id}")


def load_run_records(runs_root: str | Path, scenarios_root: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    unreadable: list[dict[str, str]] = []
    scenario_root = Path(scenarios_root)
    for run_path in sorted(Path(runs_root).rglob("run.json")):
        folder = run_path.parent
        archived_attempt = any(re.search(r"\.attempt\d+$", part) for part in run_path.parts)
        try:
            with run_path.open(encoding="utf-8") as handle:
                run = json.load(handle)
            if archived_attempt:
                records.append({"run": run, "folder": str(folder), "archived_attempt": True})
                continue
            scenario_file = _find_scenario(scenario_root, str(run.get("scenario_id", "")))
            grade = grade_run_directory(folder, scenario_file)
            records.append({"run": run, "grade": grade, "folder": str(folder),
                            "archived_attempt": archived_attempt})
        except Exception as error:
            unreadable.append({"path": str(run_path), "error": f"{type(error).__name__}: {error}"})
    return records, unreadable


def render_table(artifact: dict[str, Any]) -> str:
    rows = artifact["primary"]["raw_rates"]
    lines = [
        "# Part B deterministic endpoint", "",
        "| Population | Denominator | Condition | Numerator | Denominator n | Rate | 95% Wilson |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        rate = "n/a" if row["rate"] is None else f"{row['rate']:.4f}"
        interval = "n/a" if row["low"] is None else f"[{row['low']:.4f}, {row['high']:.4f}]"
        lines.append(f"| {row['population']} | {row['denominator']} | {row['condition']} | {row['successes']} | {row['n']} | {rate} | {interval} |")
    contrast = artifact["primary"]["all_attempts_contrast"]
    lines.extend([
        "", "| Contrast | C numerator/n | D numerator/n | Estimate | 95% cluster bootstrap | Two-sided p |",
        "|---|---:|---:|---:|---:|---:|",
        f"| C minus D, all attempts | {contrast['c_successes']}/{contrast['c_n']} | {contrast['d_successes']}/{contrast['d_n']} | {contrast['estimate']} | [{contrast['low']}, {contrast['high']}] | {contrast['p_value']} |",
        "", "## Per-subject raw rates and complete-pair contrasts", "",
        "Raw rates retain every eligible observation in their condition; complete-pair contrasts exclude a scenario only when the subject lacks an eligible C or D observation.", "",
        "| Subject | Denominator | Condition | Numerator/n |",
        "|---|---|---|---:|",
    ])
    for row in artifact["per_subject_c_minus_d"]["raw_condition_rates"]:
        lines.append(f"| {row['model_id']} | {row['denominator']} | {row['condition']} | {row['successes']}/{row['n']} |")
    lines.extend(["", "| Subject | Denominator | Complete-pair C numerator/n | Clusters | Dropped scenarios |",
                  "|---|---|---:|---:|---|"])
    for row in artifact["per_subject_c_minus_d"]["complete_pair_contrasts"]:
        lines.append(f"| {row['model_id']} | {row['denominator']} | {row['c_successes']}/{row['c_n']} | {row['clusters']} | {', '.join(row['dropped_scenarios']) or 'none'} |")
    lines.extend(["", "`fabrication_present` is intentionally omitted: the frozen Part B checkers do not provide a comparable cross-family signal and it never enters the endpoint.",
                  "", f"Publishable as result: **{str(artifact['publishable_as_result']).lower()}**", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios_root")
    parser.add_argument("output_json")
    parser.add_argument("output_table")
    parser.add_argument("--runs-root", action="append", required=True)
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--owner-release-ruling", choices=[OWNER_RELEASE_RULING], help="Apply the owner's recorded private-release ruling after technical gates pass")
    args = parser.parse_args()
    records: list[dict[str, Any]] = []
    unreadable: list[dict[str, str]] = []
    for root in args.runs_root:
        loaded, failed = load_run_records(root, args.scenarios_root)
        records.extend(loaded); unreadable.extend(failed)
    manifests = [manifest_metadata(path) for path in args.manifest]
    planned = [run_id for item in manifests for run_id in item["planned_run_ids"]]
    artifact = build_artifact(
        records, planned, source=",".join(str(Path(root)) for root in args.runs_root),
        recorded_mode=True, seal_validation=verify_sealed_scenarios(args.scenarios_root),
        package_validation=validate_combined_package(manifests),
        owner_release_ruling=args.owner_release_ruling)
    if unreadable:
        artifact["reconciliation"]["unreadable_records"] = unreadable
        artifact["reconciliation"]["reconciled"] = False
        artifact["publishable_as_result"] = False
        unreadable_warning = "one or more discovered run records were unreadable"
        artifact["release_status"] = {"status": "blocked", "open_items": [unreadable_warning]}
        artifact["warnings"].append(unreadable_warning)
    with Path(args.output_json).open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    Path(args.output_table).write_text(render_table(artifact), encoding="utf-8")


if __name__ == "__main__":
    main()
