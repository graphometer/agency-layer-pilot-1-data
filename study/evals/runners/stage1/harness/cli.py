"""Batch driver.

A batch is a list of cells. Each cell is one scenario, one condition, one model,
one repeat index. Cells are shuffled with the batch seed so that condition order
is noise rather than bias (methods 4.6). The hard ceiling is reserved per call,
and an entire tranche's declared bound is checked before it starts (R17, R39-F5).

Three registered rules the first version of this file did not implement, all
added at the R32 gate.

Tranches. R39 amendment F5 predeclares balanced tranches: every repeat below the
final one dispatches everywhere before any final repeat begins, so a batch that
stops early is still balanced across conditions and subjects. One flat shuffle
of the whole plan cannot give that. The plan is split into immutable tranche
manifests, the manifests are written beside the results ONCE and verified on
every later invocation, and a tranche refuses to start before the tranche ahead
of it finished. Order within a tranche is still shuffled, so condition order
stays noise.

Spend checkpoints. Budget-drop decisions are taken between tranches at declared
checkpoints. Crossing one halts dispatch at a completed tranche boundary with a logged reason, and
only an operator resume flag naming that checkpoint releases it. The hard
ceiling is untouched and still refuses the call itself.

Preflight. A recorded plan declares the matrix it intends to run, and the
preflight subcommand asserts the expanded cell counts against that declaration
before anything is dispatched. Any non-mock plan must pass it.

Usage:
    python -m harness.cli --config config.yaml --batch-id smoke --plan plan.yaml
    python -m harness.cli preflight --config config.yaml --plan plan.yaml
"""

import argparse
import glob
import json
import os
import random
import re
import shutil
import sys

from . import (
    config as config_module, cost, events, ids, isolation as isolation_module,
    llm_classifier, outcomes, prose_classifier, runner, version,
)

HARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# R39 amendment F6: a run that failed before any gradeable decision may be
# re-dispatched once. Once, not twice.
MAX_REPLACEMENTS_PER_PLANNED_RUN = 1

# Every dimension a recorded plan's `expect` block must declare. All of them,
# because an assertion that can be switched off by omitting it is not one:
# per_condition carries the arm totals and per_subject_condition the subject by
# arm grid, which is where a balanced design actually drifts.
EXPECT_DIMENSIONS = ("total", "per_subject", "per_condition", "per_scenario",
                     "per_repeat", "per_subject_condition")


def build_cells(plan, scenarios_by_id):
    cells = []
    for entry in plan["cells"]:
        scenario = scenarios_by_id[entry["scenario"]]
        for condition in entry["conditions"]:
            for model_name in entry["models"]:
                for repeat in range(entry.get("repeats", 1)):
                    cells.append(
                        {
                            "scenario": scenario,
                            "condition": condition,
                            "model_name": model_name,
                            "repeat_index": repeat,
                        }
                    )
    return cells


class TrancheOrderError(RuntimeError):
    """A tranche was asked to dispatch before the tranche ahead of it finished."""


class TrancheManifestMismatch(RuntimeError):
    """The recorded tranche manifest does not describe the plan being dispatched.

    Sol's R14 review: a batch that completed condition A was resumed under the
    same batch id with condition B, and tranches.json was rewritten from the A
    planned run id to the B planned run id. Both runs stayed on disk while the
    current manifest hid the original plan, which defeats predeclaration
    entirely. The manifest is written once and is evidence from that moment on.
    """


class ResumeAccountingError(RuntimeError):
    """Audit item 4: resume evidence cannot be accounted for safely."""


class Tranche:
    """One immutable tranche manifest.

    Immutable on purpose: the manifest is materialized from the recorded plan
    before anything runs, and a driver that could append to it during a batch
    would be able to rebalance the design halfway through, which is the thing
    predeclared tranches exist to prevent.
    """

    __slots__ = ("index", "label", "repeat_indices", "_cells")

    def __init__(self, index, label, cells):
        self.index = int(index)
        self.label = str(label)
        self._cells = tuple(cells)
        self.repeat_indices = tuple(sorted({cell["repeat_index"] for cell in self._cells}))

    @property
    def cells(self):
        return self._cells

    def __len__(self):
        return len(self._cells)

    def run_ids(self, models_by_name, batch_id):
        return [
            ids.run_id(batch_id, cell["scenario"].scenario_id, cell["condition"],
                       models_by_name[cell["model_name"]]["model_id"], cell["repeat_index"])
            for cell in self._cells
        ]

    def manifest(self, models_by_name, batch_id):
        return {
            "tranche": self.index,
            "label": self.label,
            "repeat_indices": list(self.repeat_indices),
            "cells_planned": len(self._cells),
            "planned_run_ids": sorted(self.run_ids(models_by_name, batch_id)),
        }

    def __repr__(self):
        return f"Tranche({self.index}, {self.label!r}, {len(self._cells)} cells)"


def build_tranches(cells):
    """Split a recorded plan into predeclared balanced tranches (R39 amendment F5).

    Tranche 1 holds every cell whose repeat index is below the final repeat, so
    repeats 1 to 3 of a four-repeat plan dispatch everywhere first. Tranche 2
    holds the final repeats. A plan with a single repeat level is one tranche;
    an empty tranche is never materialized.
    """
    cells = list(cells)
    if not cells:
        return []
    repeat_levels = sorted({cell["repeat_index"] for cell in cells})
    final = repeat_levels[-1]
    early = [cell for cell in cells if cell["repeat_index"] < final]
    last = [cell for cell in cells if cell["repeat_index"] == final]
    tranches = []
    if early:
        tranches.append(Tranche(
            1, f"repeats {repeat_levels[0] + 1} to {final}, every cell", early))
    if last:
        tranches.append(Tranche(
            len(tranches) + 1, f"repeat {final + 1}, every cell", last))
    return tranches


def tranche_worst_case_reserved_cost(tranche, models_by_name, config, meter):
    """The worst-case reservation of the most expensive SINGLE CELL in a tranche.

    Amended 2026-08-30. This was the SUM of the same per-cell figure over every
    cell in the tranche, which refused the registered core batch at $0 spent:
    it asked for $3,240.36 of headroom under a $600 ceiling whose whole
    registered projection is $240.99. The sum charged all 1,920 cells at once
    although the harness dispatches one call at a time, and it did so on top of
    a UTF-8 byte bound that is already loose by three to four times, a
    to-the-turn-limit assumption for every cell, and three paid classifier
    attempts per turn. No registered control could reduce it, so the batch was
    permanently undispatchable.

    What is enforced now is the thing a tranche start can actually promise: no
    tranche begins unless the most expensive cell in it still fits under the
    ceiling. It is a tripwire and a fail-closed pricing check, NOT the spend
    guarantee. The spend guarantee is the registered one and it is untouched --
    CostMeter.reserve refuses each individual call against total spend plus
    every outstanding reservation, and it is exact because it bounds the prompt
    the client is actually about to send. (This per-cell figure never was such a
    bound: tool results re-enter the next prompt and are capped by
    sandbox.MAX_READ_BYTES / MAX_OUTPUT_CHARS, not by sampling.max_tokens.)
    """
    max_tokens = cost._count((config.get("sampling") or {}).get("max_tokens", 0),
                             "sampling.max_tokens")
    worst = 0.0
    classifier_config = config.get("route_classifier") or {}
    classifier_model_id = classifier_config.get("model_id")
    classifier_priced = classifier_model_id and meter.table.has(classifier_model_id)
    if classifier_priced:
        classifier_prompt_tokens = cost.bound_prompt_tokens(
            prompt_text=llm_classifier.FROZEN_PROMPT) + max_tokens
    prompt_cache = {}
    for cell in tranche.cells:
        model_id = models_by_name[cell["model_name"]]["model_id"]
        # Preserve the existing pre-dispatch diagnostic ordering: an unknown
        # provider is reported by model construction, while a valid provider
        # with an absent price is refused by assert_priced before its first call.
        if not meter.table.has(model_id):
            continue
        key = (cell["condition"], cell["scenario"].scenario_id)
        if key not in prompt_cache:
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts",
                                       f"condition_{cell['condition']}.md")
            with open(prompt_path, "r", encoding="utf-8") as handle:
                fixed_text = handle.read() + "\n" + cell["scenario"].task
            prompt_cache[key] = cost.bound_prompt_tokens(prompt_text=fixed_text)
        base_tokens = prompt_cache[key]
        max_turns = cost._count(cell["scenario"].limits["max_turns"],
                                f"{cell['scenario'].scenario_id}.max_turns")
        cell_total = 0.0
        for turn in range(max_turns):
            cell_total += meter.table.worst_case(
                model_id, base_tokens + turn * max_tokens, max_tokens)
            if classifier_priced:
                # Audit item 6: every one of the bounded classifier attempts is
                # a separately paid call in this cell's start figure.
                cell_total += 3 * meter.table.worst_case(
                    classifier_model_id, classifier_prompt_tokens, 8)
            cost._assert_amount(cell_total, "cell worst-case reserved cost")
        worst = max(worst, cell_total)
    return worst


class TrancheDispatcher:
    """Refuses to dispatch a tranche before the prior one completed."""

    def __init__(self, tranches):
        self.tranches = list(tranches)
        self.completed = set()
        self.dispatched = {tranche.index: set() for tranche in self.tranches}

    def assert_ready(self, index):
        for tranche in self.tranches:
            if tranche.index >= index:
                break
            if tranche.index not in self.completed:
                raise TrancheOrderError(
                    f"tranche {index} cannot dispatch: tranche {tranche.index} "
                    f"({tranche.label}) has not completed. Tranches are predeclared and "
                    "balanced, so every earlier repeat dispatches everywhere first "
                    "(R39 amendment F5)."
                )
        return True

    def record(self, index, run_identifier):
        self.dispatched.setdefault(index, set()).add(run_identifier)

    def complete(self, index):
        self.completed.add(index)

    def is_complete(self, index):
        return index in self.completed


TRANCHES_FILE = "tranches.json"


def _canonical_tranches(manifests):
    """The comparable form of a tranche manifest list: identity, not formatting."""
    canonical = []
    for entry in manifests or []:
        canonical.append({
            "tranche": int(entry.get("tranche", 0)),
            "repeat_indices": [int(value) for value in entry.get("repeat_indices", [])],
            "planned_run_ids": sorted(str(value) for value in
                                      entry.get("planned_run_ids", [])),
        })
    return sorted(canonical, key=lambda entry: entry["tranche"])


def _tranche_differences(recorded, rebuilt):
    """Name every way the plan in hand differs from the recorded manifest."""
    differences = []
    left = _canonical_tranches(recorded)
    right = _canonical_tranches(rebuilt)
    if len(left) != len(right):
        differences.append(
            f"the recorded manifest has {len(left)} tranche(s), this plan expands to "
            f"{len(right)}")
    by_index = {entry["tranche"]: entry for entry in left}
    for entry in right:
        prior = by_index.pop(entry["tranche"], None)
        if prior is None:
            differences.append(f"tranche {entry['tranche']} is not in the recorded manifest")
            continue
        if prior["repeat_indices"] != entry["repeat_indices"]:
            differences.append(
                f"tranche {entry['tranche']}: recorded repeat indices "
                f"{prior['repeat_indices']}, this plan {entry['repeat_indices']}")
        only_recorded = sorted(set(prior["planned_run_ids"]) - set(entry["planned_run_ids"]))
        only_now = sorted(set(entry["planned_run_ids"]) - set(prior["planned_run_ids"]))
        for run_identifier in only_recorded:
            differences.append(
                f"tranche {entry['tranche']}: {run_identifier} is in the recorded manifest "
                "and not in this plan")
        for run_identifier in only_now:
            differences.append(
                f"tranche {entry['tranche']}: {run_identifier} is in this plan and not in "
                "the recorded manifest")
    for index in sorted(by_index):
        differences.append(f"tranche {index} is in the recorded manifest and not in this plan")
    return differences


def assert_tranche_manifest_unchanged(batch_dir, batch_id, manifests, expected_batch_id=None):
    """Refuse to dispatch a plan the recorded manifest does not describe.

    A no-op when nothing has been recorded yet. Once tranches.json exists it is
    read and compared, never rewritten: predeclared tranches that a resume can
    silently redefine are not predeclared. A different matrix takes a new batch
    id.
    """
    path = os.path.join(batch_dir, TRANCHES_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            recorded = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TrancheManifestMismatch(
            f"{path} exists but could not be read ({type(error).__name__}: {error}). It is "
            "the predeclared record of this batch's matrix and is never overwritten; repair "
            "or move it by hand."
        )
    differences = _tranche_differences(recorded.get("tranches"), manifests)
    if recorded.get("batch_id") not in (None, batch_id):
        differences.append(
            f"the recorded manifest names batch {recorded.get('batch_id')!r}, "
            f"this dispatch is batch {batch_id!r}")
    if expected_batch_id is not None and recorded.get("expected_batch_id") != expected_batch_id:
        differences.append(
            f"the recorded manifest expected_batch_id is {recorded.get('expected_batch_id')!r}, "
            f"this plan expects {expected_batch_id!r}")
    if differences:
        raise TrancheManifestMismatch(
            f"{path} was recorded for a different plan, and a tranche manifest is never "
            "rewritten:\n  " + "\n  ".join(differences)
            + "\nDispatch a different matrix under a new batch id."
        )
    return recorded.get("tranches") or manifests


def record_tranche_manifest(batch_dir, batch_id, manifests, expected_batch_id=None):
    """Write the manifest once. An existing one is verified, never replaced."""
    path = os.path.join(batch_dir, TRANCHES_FILE)
    if os.path.exists(path):
        return assert_tranche_manifest_unchanged(
            batch_dir, batch_id, manifests, expected_batch_id=expected_batch_id)
    payload = {"batch_id": batch_id, "tranches": manifests}
    if expected_batch_id is not None:
        payload["expected_batch_id"] = expected_batch_id
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return manifests


def plan_counts(plan, models_by_name):
    """Expand a plan into the counts the preflight asserts, without loading scenarios.

    Kept independent of the scenario directory so the matrix can be checked
    before any fixture is staged, and so a preflight failure names the plan
    rather than a missing file.
    """
    counts = {"total": 0, "per_subject": {}, "per_condition": {},
              "per_scenario": {}, "per_repeat": {}, "per_subject_condition": {}}
    for entry in plan.get("cells") or []:
        scenario_id = entry["scenario"]
        for condition in entry["conditions"]:
            for model_name in entry["models"]:
                model = models_by_name.get(model_name)
                subject = model["model_id"] if model else f"unknown:{model_name}"
                for repeat in range(entry.get("repeats", 1)):
                    counts["total"] += 1
                    for key, value in (("per_subject", subject),
                                       ("per_condition", condition),
                                       ("per_scenario", scenario_id),
                                       ("per_repeat", str(repeat)),
                                       ("per_subject_condition", f"{subject}/{condition}")):
                        counts[key][value] = counts[key].get(value, 0) + 1
    return counts


def preflight(config, plan, verbose=False, require_complete=None):
    """Assert the expanded matrix against the plan's own declared expectation.

    The tripwire for the recorded plan built at the freeze: the plan states what
    it believes it runs, per subject, condition, scenario and repeat, plus the
    arm totals, and this refuses to dispatch anything if the expansion disagrees
    by a single cell. A plan that names a model the config does not define, or a
    scenario the scenarios directory does not hold, fails here rather than
    halfway through a paid batch.

    Every dimension in EXPECT_DIMENSIONS is required of a plan that reaches a
    real provider. An omitted dimension is a refusal, not a skipped check:
    otherwise the plan author chooses which parts of the matrix are asserted,
    and a total-only block passes while every arm inside it has drifted.
    """
    models_by_name = {entry["name"]: entry for entry in config.get("models", [])}
    counts = plan_counts(plan, models_by_name)
    declared = plan.get("expect")
    differences = []
    if require_complete is None:
        # A plan that reaches a real provider carries the whole expectation. A
        # mock plan may declare a partial block for local convenience, and what
        # it declares is still asserted.
        require_complete = not plan_is_mock(config, plan)

    unknown_models = sorted({
        model_name
        for entry in plan.get("cells") or []
        for model_name in entry["models"]
        if model_name not in models_by_name
    })
    for model_name in unknown_models:
        differences.append(f"plan names model {model_name!r}, which the config does not define")

    scenarios_dir = config.get("scenarios_dir")
    if scenarios_dir and not os.path.isdir(scenarios_dir):
        # Fail CLOSED (step-10 lane finding, 2026-08-25): a configured scenarios_dir that
        # does not resolve used to silently skip every per-scenario existence check, so a
        # typo'd override printed "preflight: pass" while asserting nothing about the
        # scenarios. A set-but-missing directory is now a refusal, not a skipped check.
        differences.append(
            f"scenarios_dir {scenarios_dir!r} is configured but is not a directory "
            f"(resolved against CWD {os.getcwd()!r}); refusing rather than skipping the "
            "scenario-existence checks")
    elif scenarios_dir:
        for scenario_id in sorted({entry["scenario"] for entry in plan.get("cells") or []}):
            if not os.path.isfile(os.path.join(scenarios_dir, scenario_id, "scenario.yaml")):
                differences.append(
                    f"plan names scenario {scenario_id!r}, which is not in {scenarios_dir}")

    if declared is None:
        differences.append(
            "the plan declares no `expect` block. A recorded plan states the matrix it "
            "intends to run, and the preflight asserts it before any dispatch."
        )
    else:
        missing = [name for name in EXPECT_DIMENSIONS if name not in declared]
        if missing and require_complete:
            # Sol's R14 review: a block holding only the correct total passed,
            # although it asserted nothing per subject, per condition, per
            # scenario, per repeat, or per subject and arm. An assertion the plan
            # author can switch off by omission is not a tripwire, so every
            # dimension is required and an omission refuses dispatch.
            differences.append(
                "the `expect` block is incomplete: it declares nothing for "
                + ", ".join(missing)
                + ". A recorded plan asserts every dimension, so a matrix that drifted "
                "in one of them cannot pass by omission. The expansion's own counts are "
                "printed above and can be pasted in."
            )
        if "total" in declared and int(declared["total"]) != counts["total"]:
            differences.append(
                f"total: plan expects {int(declared['total'])}, expansion gives {counts['total']}")
        for dimension in ("per_subject", "per_condition", "per_scenario", "per_repeat",
                          "per_subject_condition"):
            if dimension not in declared:
                continue
            expected = {str(key): int(value) for key, value in declared[dimension].items()}
            observed = counts[dimension]
            for key in sorted(set(expected) | set(observed)):
                if expected.get(key, 0) != observed.get(key, 0):
                    differences.append(
                        f"{dimension}[{key}]: plan expects {expected.get(key, 0)}, "
                        f"expansion gives {observed.get(key, 0)}")

    report = {"ok": not differences, "counts": counts, "declared": declared,
              "differences": differences}
    if verbose:
        print(f"preflight: {counts['total']} cells expanded")
        for dimension in EXPECT_DIMENSIONS[1:]:
            rendered = ", ".join(f"{key}={value}"
                                 for key, value in sorted(counts[dimension].items()))
            print(f"  {dimension}: {rendered}")
        for line in differences:
            print(f"  MISMATCH {line}", file=sys.stderr)
        print("preflight: " + ("pass" if report["ok"] else "REFUSED"))
    return report


def non_mock_models(config, plan):
    """Every model this plan names whose provider is not a mock, named and rendered.

    A model the config does not define at all counts as non-mock: an unknown
    provider is not a proof of anything, and the safe reading of "prove the plan
    is entirely mock" is that anything unproven is not mock.
    """
    models_by_name = {entry["name"]: entry for entry in config.get("models", [])}
    named = sorted({model_name for entry in plan.get("cells") or []
                    for model_name in entry["models"]})
    rendered = []
    for model_name in named:
        provider = (models_by_name.get(model_name) or {}).get("provider")
        if provider != "mock":
            rendered.append(f"{model_name} (provider {provider or 'undefined in this config'})")
    return rendered


def plan_is_mock(config, plan):
    """True when every model this plan names is a mock provider."""
    return not non_mock_models(config, plan)


def build_route_classifier(config, allow_live=False, config_dir=None):
    """The frozen route classifier that decides PM8 routing.

    Config `route_classifier.provider` selects it: `mock` replays canned answers
    at zero cost, anything else is a real provider call and needs allow_live.
    Absent, the keyword pass decides, which is the development path only and is
    recorded as `authority: keyword` on every routing decision.
    """
    spec = config.get("route_classifier")
    if not spec:
        return None
    provider = spec.get("provider")
    if provider == "mock":
        from .llm_classifier import MockLlmRouteClassifier

        if spec.get("answers_file"):
            path = spec["answers_file"]
            if not os.path.isabs(path):
                path = os.path.join(config_dir or os.getcwd(), path)
            return MockLlmRouteClassifier.from_file(
                path, model_id=spec.get("model_id", "mock-llm-1")
            )
        return MockLlmRouteClassifier(answers=spec.get("answers"),
                                      default=spec.get("default", "on_dissent"),
                                      model_id=spec.get("model_id", "mock-llm-1"))
    if not allow_live:
        raise RuntimeError(
            f"route_classifier provider {provider!r} calls a real endpoint. Pass allow_live."
        )
    from .llm_classifier import LlmRouteClassifier

    return LlmRouteClassifier(config_module.build_model(spec, allow_live=True))


def _normalized(identifier):
    """Fold case and separators, so mock-1, Mock_1 and MOCK.1 collide as one.

    A run id becomes a directory name, and on a case-insensitive filesystem two
    ids that differ only in case are the same directory. Normalizing here means
    the guard catches that too, rather than the filesystem catching it silently.
    """
    return re.sub(r"[^a-z0-9]+", "", identifier.lower())


def _assert_run_ids_unique(cells, models_by_name, batch_id, batch_dir, resume=False):
    """Refuse a plan whose cells would collide, or would overwrite stored evidence.

    CONTRACTS section 2: runs are never silently replaced. Two paths lead there
    and both are closed here: two cells in one plan deriving the same run id, and
    a batch id re-run over a directory that already holds results. Caught before
    anything is run rather than diagnosed afterwards from a short batch.json.
    """
    seen = {}
    for cell in cells:
        model_id = models_by_name[cell["model_name"]]["model_id"]
        identifier = ids.run_id(
            batch_id, cell["scenario"].scenario_id, cell["condition"], model_id,
            cell["repeat_index"],
        )
        key = _normalized(identifier)
        if key in seen:
            raise ValueError(
                f"two cells produce the same run_id {identifier!r}: "
                f"{seen[key]!r} and {cell['model_name']!r}. Give them distinct "
                "model_id values or distinct repeat indices; a run is never overwritten."
            )
        seen[key] = cell["model_name"]

        existing = os.path.join(batch_dir, identifier)
        if not resume and any(
            os.path.exists(os.path.join(existing, name)) for name in runner.RUN_FILES
        ):
            raise ValueError(
                f"{existing} already holds a completed run. A run is never silently "
                "replaced (CONTRACTS section 2). Use a new batch id, or the preregistered "
                "replacement rule."
            )


def build_isolation(config, allow_live=False, scenarios_dir=None):
    """Build the run isolation and prove it before anything runs (PM14).

    The rehearsal sandbox was a /tmp directory on the lab host with the whole
    filesystem readable, and models used it: they read the scenario's own source
    and ground truth, read the vault's documents, and listed credential files.
    Isolation is therefore a precondition of every further real-model run, not a
    hardening pass.

    The probe runs once per batch, on a throwaway sandbox, and a live batch
    refuses to start unless it passed. A mock batch is allowed to run without
    isolation, because the mocks emit fixed commands and no model is on the
    other end, but the state is recorded on every run either way.
    """
    harness_paths = [HARNESS_ROOT]
    if scenarios_dir:
        harness_paths.append(os.path.abspath(scenarios_dir))
    isolation = isolation_module.build(config, harness_paths=harness_paths)
    result = isolation.probe()
    if result["status"] != "pass" and allow_live:
        raise isolation_module.IsolationError(
            "the isolation probe did not pass, so no live batch can start (PM14). "
            + "; ".join(result["failures"])[:2000]
        )
    return isolation, result


def _write_scheduled_failure(cell, model_config, batch_id, batch_dir,
                             termination_reason, detail, isolation_record=None,
                             attempt_number=0):
    """Write the reconstructable row for an attempt that never reached a provider."""
    model_id = model_config["model_id"]
    run_identifier = ids.run_id(
        batch_id, cell["scenario"].scenario_id, cell["condition"], model_id,
        cell["repeat_index"],
    )
    run_dir = os.path.join(batch_dir, run_identifier)
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "run.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    partial_evidence = [name for name in runner.RUN_FILES if name != "run.json"
                        and os.path.exists(os.path.join(run_dir, name))]
    if partial_evidence:
        raise RuntimeError(
            f"refusing to mark {run_identifier} as a scheduled failure because its run "
            f"directory already holds evidence: {', '.join(partial_evidence)}"
        )
    now = ids.utc_now()
    record = {
        "run_id": run_identifier,
        "planned_run_id": run_identifier,
        "attempt_number": int(attempt_number or 0),
        "attempt_id": f"{run_identifier}#attempt{int(attempt_number or 0)}",
        "batch_id": batch_id,
        "stage": "stage1",
        "condition": cell["condition"],
        "model_id": model_id,
        "provider": model_config.get("provider", "unknown"),
        "scenario_id": cell["scenario"].scenario_id,
        "family": cell["scenario"].family,
        "repeat_index": cell["repeat_index"],
        "started_at": now,
        "ended_at": now,
        "termination_reason": termination_reason,
        "scheduled_failure": True,
        "failure_detail": str(detail)[:4000],
        "model_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cost_usd": 0.0,
        "status_lines": [],
        "final_status": None,
        "final_turn_has_status": False,
        "host_transition_failed": False,
        "isolation": isolation_record or {"kind": "unknown", "version": None, "probe": "not_run"},
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return record


def _run_usage(meter, run_identifier):
    """The usage known to the meter, including a partly executed run."""
    try:
        totals = meter.run_totals(run_identifier)
    except Exception:
        totals = {}
    return {
        "input_tokens": int(totals.get("input_tokens", 0) or 0),
        "output_tokens": int(totals.get("output_tokens", 0) or 0),
        "cache_read_input_tokens": int(
            totals.get("cache_read_input_tokens", 0) or 0
        ),
        "cache_creation_input_tokens": int(
            totals.get("cache_creation_input_tokens", 0) or 0
        ),
        "model_calls": int(totals.get("calls", 0) or 0),
        "cost_usd": round(float(totals.get("cost_usd", 0.0) or 0.0), 6),
    }


def _write_harness_error(cell, model_config, batch_id, batch_dir, detail, meter,
                         isolation_record, attempt_number=0):
    """Finish a started attempt without altering its existing evidence files.

    R43-review findings 1 and 4. An existing run.json is never rewritten: the
    failure goes to harness_error.jsonl beside it as a non-authoritative
    diagnostic, and the stored record — verified against the journal — remains
    the row of record. And a journal this driver cannot account for propagates
    as the refusal it is, at the moment the corruption is detected, rather
    than becoming a normal-looking row that only a later resume would refuse.
    """
    model_id = model_config["model_id"]
    run_identifier = ids.run_id(
        batch_id, cell["scenario"].scenario_id, cell["condition"], model_id,
        cell["repeat_index"],
    )
    run_dir = os.path.join(batch_dir, run_identifier)
    os.makedirs(run_dir, exist_ok=True)
    now = ids.utc_now()
    record_path = os.path.join(run_dir, "run.json")
    if os.path.exists(record_path):
        # Evidence preservation (CONTRACTS section 2): the attempt already has
        # its record of record. Append the diagnostic, then verify the stored
        # record against the journal; a contradiction refuses here and now.
        with open(os.path.join(run_dir, "harness_error.jsonl"), "a",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({
                "at": now, "run_id": run_identifier,
                "attempt_number": int(attempt_number or 0),
                "failure_detail": str(detail)[:4000],
            }, sort_keys=True) + "\n")
        record = _read_run_record(run_dir)
        _assert_journal_agrees(run_dir, record, _journal_state(run_dir))
        return record
    # R43 re-review: the same authority checks gate a SYNTHESIZED row, before
    # any record is built. A closed journal with no run record refuses here
    # and now — writing a fresh harness_error row over it would manufacture
    # exactly the termination contradiction resume refuses — and with no
    # journal at all, unjournaled paid usage refuses rather than becoming a
    # zero-cost row. Only an open, structurally and accountingly valid journal
    # may be closed into a new harness-error row.
    journal_state = _journal_state(run_dir)
    _assert_journal_agrees(run_dir, None, journal_state)
    if journal_state is None:
        _assert_no_unjournaled_usage(run_dir)
    record = {
        "run_id": run_identifier,
        "planned_run_id": run_identifier,
        "attempt_number": int(attempt_number or 0),
        "attempt_id": f"{run_identifier}#attempt{int(attempt_number or 0)}",
        "batch_id": batch_id,
        "stage": "stage1",
        "condition": cell["condition"],
        "model_id": model_id,
        "provider": model_config.get("provider", "unknown"),
        "scenario_id": cell["scenario"].scenario_id,
        "family": cell["scenario"].family,
        "repeat_index": cell["repeat_index"],
        "started_at": now,
        "ended_at": now,
        "termination_reason": "harness_error",
        "failure_detail": str(detail)[:4000],
        "status_lines": [],
        "final_status": None,
        "final_turn_has_status": False,
        "host_transition_failed": False,
        "isolation": isolation_record,
        **_run_usage(meter, run_identifier),
    }
    # R43 step 2 (Sol finding 8, fuller form): when the attempt left a journal,
    # this row's accounting is the journal's own conservative story — open
    # reservations charged at their bound — and the journal is closed with the
    # same figures, so a later resume finds a finished attempt whose record and
    # journal agree. A journal that cannot be accounted for raises out of here
    # uncaught (finding 4): the batch stops where the corruption is found, and
    # no normal-looking row is written over it.
    journal_usage = (_journal_accounting(journal_state, model_id, meter)
                     if journal_state is not None else None)
    if journal_usage is not None:
        for name in ("cost_usd", "model_calls", "input_tokens", "output_tokens",
                     "cache_read_input_tokens", "cache_creation_input_tokens"):
            record[name] = journal_usage[name]
    if journal_state is not None and not journal_state["closed"]:
        meter.bind_run_journal(run_identifier, os.path.join(run_dir, "cost.jsonl"))
        meter.close_run_journal(run_identifier, record)
    with open(record_path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return record


def _read_run_record(run_dir):
    path = os.path.join(run_dir, "run.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
    except json.JSONDecodeError as error:
        raise ResumeAccountingError(
            f"{path}: line {error.lineno}: unreadable run record: {error.msg}") from error
    except (OSError, UnicodeError) as error:
        raise ResumeAccountingError(f"{path}: line 1: unreadable run record: {error}") from error
    if not isinstance(record, dict):
        raise ResumeAccountingError(f"{path}: line 1: run record must be an object")
    return record


CHECKPOINTS_FILE = "checkpoints.jsonl"
REGISTERED_DROP_CLASSES = ("frontier_replication", "core_repeats_3_to_2")


def _assert_expected_batch_id(plan, batch_id):
    """Bind recorded-plan randomization to the batch id frozen in that plan."""
    expected = plan.get("expected_batch_id")
    if expected is not None and str(expected) != str(batch_id):
        raise ValueError(
            f"batch id {batch_id!r} does not match this plan's expected_batch_id "
            f"{expected!r}; refusing before dispatch, reservation, or results creation"
        )


def _registered_drop_run_ids(plan, config, batch_id, drop_class):
    """Derive one registered drop unit from a plan; never accept operator-supplied ids."""
    if drop_class not in REGISTERED_DROP_CLASSES:
        raise ValueError(
            f"unknown registered drop {drop_class!r}; choose exactly one of "
            + ", ".join(REGISTERED_DROP_CLASSES)
        )
    scenarios = config_module.load_scenarios(config["scenarios_dir"])
    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    models_by_name = {entry["name"]: entry for entry in config["models"]}
    cells = build_cells(plan, scenarios_by_id)
    if drop_class == "frontier_replication":
        selected = [cell for cell in cells
                    if cell["model_name"] in {"claude_frontier", "gpt_frontier"}]
        if not selected:
            raise ValueError("frontier_replication found no frontier cells in the frozen plan")
    else:
        if plan.get("expected_batch_id") != "recorded-core-s1":
            raise ValueError(
                "core_repeats_3_to_2 is registered only for plan_recorded.yaml "
                "(expected_batch_id recorded-core-s1)"
            )
        selected = [cell for cell in cells if int(cell["repeat_index"]) == 2]
        if not selected:
            raise ValueError("core_repeats_3_to_2 found no repeat-3 cells in the frozen plan")
    return sorted(ids.run_id(
        batch_id, cell["scenario"].scenario_id, cell["condition"],
        models_by_name[cell["model_name"]]["model_id"], cell["repeat_index"])
        for cell in selected)


def record_registered_drop(config, plan, batch_id, results_root, drop_class, reason,
                           operator="operator"):
    """Make a recorded checkpoint halt terminal under one preregistered drop rule."""
    _assert_expected_batch_id(plan, batch_id)
    if not str(reason).strip():
        raise ValueError("a registered drop requires a non-empty reason")
    batch_dir = os.path.join(results_root, "stage1", batch_id)
    batch_path = os.path.join(batch_dir, "batch.json")
    tranches_path = os.path.join(batch_dir, TRANCHES_FILE)
    try:
        with open(batch_path, "r", encoding="utf-8") as handle:
            batch = json.load(handle)
        with open(tranches_path, "r", encoding="utf-8") as handle:
            tranche_record = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"cannot elect a registered drop without readable batch.json and tranches.json: {error}"
        ) from error
    if batch.get("batch_id") != batch_id or tranche_record.get("batch_id") != batch_id:
        raise ValueError("batch.json and tranches.json must both name the requested batch id")
    prior_drops = batch.get("registered_drops") or []
    if any(entry.get("drop_class") == drop_class for entry in prior_drops):
        raise ValueError(f"this batch already records the registered drop {drop_class!r}")
    halt = batch.get("checkpoint_halt")
    if not isinstance(halt, dict) or float(halt.get("checkpoint_usd", -1)) not in {300.0, 450.0}:
        raise ValueError(
            "a registered drop may be elected only from a recorded discretionary $300/$450 "
            "checkpoint halt, never from a pause or mid-flight state"
        )
    derived_ids = _registered_drop_run_ids(plan, config, batch_id, drop_class)
    planned_by_tranche = {
        int(entry["tranche"]): set(map(str, entry.get("planned_run_ids", [])))
        for entry in tranche_record.get("tranches", [])
    }
    completed = {int(value) for value in batch.get("tranches_completed", [])}
    if drop_class == "core_repeats_3_to_2":
        pending = set().union(*(ids_ for index, ids_ in planned_by_tranche.items()
                              if index not in completed)) if planned_by_tranche else set()
        if set(derived_ids) != pending:
            raise ValueError(
                "core repeat-3 ids are not exactly the undispatched tranche after the "
                "recorded checkpoint; refusing an ambiguous or mid-flight drop"
            )
    else:
        pending = set().union(*(ids_ for index, ids_ in planned_by_tranche.items()
                              if index not in completed)) if planned_by_tranche else set()
        if set(derived_ids) != pending:
            raise ValueError(
                "frontier replication ids are not exactly the undispatched tranche after "
                "the recorded checkpoint"
            )
    record = {
        "event": "checkpoint_drop", "drop_class": drop_class, "at": ids.utc_now(),
        "operator": str(operator), "reason": str(reason).strip(),
        "checkpoint_usd": float(halt["checkpoint_usd"]),
        "checkpoint_tranche_index": int(halt["tranche_index"]),
        "undispatched_run_ids": derived_ids,
    }
    batch["registered_drops"] = [*prior_drops, record]
    batch["cells_not_dispatched"] = sum(
        len(entry.get("undispatched_run_ids", [])) for entry in batch["registered_drops"])
    batch["halted_reason"] = f"registered drop elected: {drop_class}: {record['reason']}"
    temporary = batch_path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(batch, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, batch_path)
    with open(os.path.join(batch_dir, CHECKPOINTS_FILE), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def recorded_checkpoint_halts(batch_dir):
    """Every checkpoint this batch has actually halted at, from its own log."""
    values = set()
    path = os.path.join(batch_dir, CHECKPOINTS_FILE)
    for line_number, row in enumerate(_read_jsonl(path), 1):
        if row.get("event") != "checkpoint_halt":
            continue
        try:
            values.add(cost._finite_number(row.get("checkpoint_usd"),
                                           "checkpoint_usd", positive=True))
            cost._assert_amount(row.get("total_usd"), "total_usd")
        except cost.AccountingError as error:
            raise ResumeAccountingError(
                f"{path}: line {line_number}: invalid checkpoint accounting: {error}") from error
    return values


def _release_checkpoints(meter, batch_dir, batch_id, resume_checkpoints, resume,
                         operator="operator", verbose=False):
    """Honor an operator's checkpoint releases, or refuse them.

    Three conditions, all of them Sol's R14 remedy: the batch must be a resume,
    because a release answers a halt that already happened; the batch must have
    RECORDED a halt at that checkpoint, so the release names a real event in this
    batch's own log rather than a number; and the meter must have crossed it,
    which is why this runs after prior spend is restored. The meter enforces the
    third; the first two are the driver's, because only the driver knows the
    batch.

    Releases are never persisted as standing permission: each invocation names
    the checkpoint it releases, so an unattended rerun cannot inherit one.
    """
    if not resume_checkpoints:
        return []
    named = ", ".join(f"${float(value):.2f}" for value in resume_checkpoints)
    if not resume:
        raise ValueError(
            f"--resume-checkpoint {named} is only valid with --resume. A checkpoint release "
            "answers a halt that has already happened in this batch; released on a fresh "
            "launch it would pre-acknowledge a checkpoint that then never halts."
        )
    halted_at = recorded_checkpoint_halts(batch_dir)
    released = []
    for value in resume_checkpoints:
        checkpoint = float(value)
        if checkpoint not in halted_at:
            raise ValueError(
                f"batch {batch_id} has recorded no halt at ${checkpoint:.2f}. The checkpoints "
                "this batch halted at are "
                + (", ".join(f"${entry:.2f}" for entry in sorted(halted_at)) or "none")
                + f"; a release names a halt in {os.path.join(batch_dir, CHECKPOINTS_FILE)}."
            )
        # Raises unless the restored spend has genuinely crossed it.
        released.append(meter.acknowledge_checkpoint(
            checkpoint, operator=operator, note=f"resume of batch {batch_id}"))
    with open(os.path.join(batch_dir, CHECKPOINTS_FILE), "a", encoding="utf-8") as handle:
        for entry in released:
            handle.write(json.dumps(dict(entry, at=ids.utc_now()), sort_keys=True) + "\n")
    if verbose:
        for entry in released:
            print(f"checkpoint ${entry['checkpoint_usd']:.2f} released by {operator}")
    return released


def _read_jsonl(path):
    """Audit item 4: read JSONL fail-closed, except a truncated final write."""
    rows = []
    try:
        handle = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        return rows
    except (OSError, UnicodeError) as error:
        raise ResumeAccountingError(f"{path}: line 1: unreadable JSONL: {error}") from error
    with handle:
        lines = handle.readlines()
        for line_number, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except (UnicodeError, json.JSONDecodeError) as error:
                # A crash can leave only the last append incomplete. A newline
                # proves the writer completed that line, so malformed data with
                # a newline is never excused as truncation.
                if line_number == len(lines) and not raw_line.endswith("\n"):
                    break
                raise ResumeAccountingError(
                    f"{path}: line {line_number}: malformed JSONL: {error}") from error
            if not isinstance(row, dict):
                raise ResumeAccountingError(
                    f"{path}: line {line_number}: JSONL record must be an object")
            rows.append(row)
    return rows


def gradeable_decision(run_dir, record=None):
    """The grader's pre-decision test, read off stored evidence.

    R39 amendment F6 permits one re-dispatch of a run that failed BEFORE any
    gradeable decision, and forbids replacing a run that reached one. Four
    things count as a gradeable decision, and each is read from the artifact a
    grader would read:

      * an affordance invocation event, which is a decision by definition;
      * an authoritative LLM prose route, which is what makes a prose stop a
        primary E2 candidate;
      * check.json's task_completed, the scenario's own verdict;
      * any STATUS line, which is the structured claim E1 scores.

    Returns the name of the first one found, or None. Evidence is read from the
    files rather than from run.json alone, so an attempt interrupted before its
    run record was written is still protected.
    """
    record = record if record is not None else _read_run_record(run_dir)
    if record:
        if record.get("status_lines"):
            return "status_line"
        if record.get("termination_reason") == "task_completed":
            return "check.task_completed"
    for event in _read_jsonl(os.path.join(run_dir, "events.jsonl")):
        event_type = event.get("type")
        if event_type in outcomes.INVOCATION_EVENT_TYPES and event.get("actor") == "agent":
            return "affordance_invocation"
        if event_type == "prose_routed" and (event.get("payload") or {}).get("authority") == "llm":
            return "authoritative_llm_prose_route"
    for row in _read_jsonl(os.path.join(run_dir, "routing.jsonl")):
        if row.get("authority") == "llm":
            return "authoritative_llm_prose_route"
    try:
        with open(os.path.join(run_dir, "check.json"), "r", encoding="utf-8") as handle:
            check = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        check = None
    if isinstance(check, dict) and check.get("task_completed"):
        return "check.task_completed"
    for row in _read_jsonl(os.path.join(run_dir, "transcript.jsonl")):
        if row.get("role") != "assistant":
            continue
        if runner.Run.STATUS_PATTERN.search(row.get("text") or ""):
            return "status_line"
    return None


def _resume_action(run_dir):
    """What resume does with one planned cell. Returns (action, record, detail).

    skip      keep what is on disk and do not dispatch again
    refused   a failed run whose one permitted replacement is already spent
    keep      an interrupted attempt that must not be replaced; finish its row
    replace   re-dispatch once, archiving the failed original immutably
    dispatch  nothing on disk for this cell yet

    R43 step 2 (Sol finding 8, fuller form): whether the attempt finished is
    the journal's to say — its closing record marks a finished attempt, its
    absence an interrupted one — and a run record that contradicts the journal
    raises rather than letting either story win, because trusting run.json
    could re-dispatch a finished cell and trusting a stray journal could
    replace one.
    """
    record = _read_run_record(run_dir)
    state = _journal_state(run_dir)
    if state is None:
        # Sol R43-review finding 2: with no journal at all, paid usage evidenced
        # anywhere else refuses the cell BEFORE any record — a zero-claim
        # run.json included — can be accepted, restored, or replaced.
        _assert_no_unjournaled_usage(run_dir)
    _assert_journal_agrees(run_dir, record, state)
    evidence = any(os.path.exists(os.path.join(run_dir, name)) for name in runner.RUN_FILES)
    replacements_used = len(glob.glob(run_dir + ".attempt[0-9]*"))
    decision = gradeable_decision(run_dir, record)
    budget_spent = replacements_used >= MAX_REPLACEMENTS_PER_PLANNED_RUN

    if record is not None:
        reason = record.get("termination_reason")
        if decision:
            return "skip", record, f"a gradeable decision exists ({decision})"
        if not outcomes.is_failure(reason):
            return "skip", record, f"the run finished ({reason})"
        if budget_spent:
            return "refused", record, (
                f"failed ({reason}) but the one permitted replacement is already spent")
        return "replace", None, f"failed before any gradeable decision ({reason})"

    if not evidence:
        return "dispatch", None, "no attempt on disk"
    if decision:
        return "keep", None, f"an interrupted attempt reached a gradeable decision ({decision})"
    if budget_spent:
        return "keep", None, "the one permitted replacement is already spent"
    return "replace", None, "an interrupted attempt with no gradeable decision"


def _archive_attempt(run_dir):
    """Move an incomplete or failed attempt aside, choosing the first free suffix."""
    if not os.path.exists(run_dir):
        return None
    index = 1
    while os.path.exists(f"{run_dir}.attempt{index}"):
        index += 1
    destination = f"{run_dir}.attempt{index}"
    shutil.move(run_dir, destination)
    return destination


def _journal_state(run_dir):
    """Parse one attempt's cost journal fail-closed, its closing record included.

    R43 step 2 (Sol finding 8, fuller form): the journal is the sole resume
    authority, so this parse is where every structural refusal lives. Returns
    None when no journal exists, else a dict with `closed` (the journal carries
    the attempt's closing record), `close` (that record, or None), and the
    `reservations` and `actuals` rows as (line_number, row) pairs. A duplicate
    reservation, a duplicate or unmatched actual, an unknown record type, an
    invalid amount, a second close, or any row after the close is a refusal,
    never a warning.
    """
    journal_path = os.path.join(run_dir, "cost.jsonl")
    if not os.path.exists(journal_path):
        return None
    reservations = []
    actuals = []
    close = None
    seen_reservations = set()
    seen_actuals = set()
    for line_number, row in enumerate(_read_jsonl(journal_path), 1):
        if close is not None:
            raise ResumeAccountingError(
                f"{journal_path}: line {line_number}: a record follows the closing record; "
                "a closed journal accepts nothing further")
        row_type = row.get("type")
        if row_type == "close":
            try:
                cost._assert_amount(row.get("cost_usd"), "cost_usd")
                cost._assert_amount(row.get("outstanding_reservations_usd", 0.0),
                                    "outstanding_reservations_usd")
                for name in ("model_calls", "input_tokens", "output_tokens",
                             "cache_read_input_tokens", "cache_creation_input_tokens",
                             "outstanding_reservations"):
                    cost._count(row.get(name, 0), name)
            except cost.AccountingError as error:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: invalid closing record: "
                    f"{error}") from error
            # R43 re-review: the writer quantizes every closing figure through
            # cost.micro_usd, so a close carrying sub-microdollar precision was
            # not written by this harness. It is refused as non-canonical here
            # rather than compared approximately at the floor.
            for name in ("cost_usd", "outstanding_reservations_usd"):
                if cost.sub_micro_usd(row.get(name, 0.0)):
                    raise ResumeAccountingError(
                        f"{journal_path}: line {line_number}: the closing record's {name} "
                        f"({row.get(name)!r}) carries sub-microdollar precision, which the "
                        "writer never produces. The close is refused as non-canonical.")
            close = row
            continue
        if row_type not in ("reservation", "actual"):
            raise ResumeAccountingError(
                f"{journal_path}: line {line_number}: unknown cost-journal record type")
        reservation_id = row.get("reservation_id")
        if not isinstance(reservation_id, (str, int)) or isinstance(reservation_id, bool):
            raise ResumeAccountingError(
                f"{journal_path}: line {line_number}: missing or invalid reservation_id")
        if row_type == "reservation":
            if reservation_id in seen_reservations:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: duplicate reservation id "
                    f"{reservation_id!r}")
            seen_reservations.add(reservation_id)
            try:
                cost._assert_amount(row["reserved_usd"], "reserved_usd")
                if "prompt_tokens_bound" in row:
                    cost._count(row["prompt_tokens_bound"], "prompt_tokens_bound")
                if "max_tokens" in row:
                    cost._count(row["max_tokens"], "max_tokens")
            except (KeyError, cost.AccountingError) as error:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: invalid reservation: {error}") from error
            reservations.append((line_number, row))
        else:
            if reservation_id not in seen_reservations:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: actual has unmatched reservation id "
                    f"{reservation_id!r}")
            if reservation_id in seen_actuals:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: duplicate actual for reservation id "
                    f"{reservation_id!r}")
            seen_actuals.add(reservation_id)
            try:
                cost._assert_amount(row["cost_usd"], "cost_usd")
            except (KeyError, cost.AccountingError) as error:
                raise ResumeAccountingError(
                    f"{journal_path}: line {line_number}: invalid actual: {error}") from error
            actuals.append((line_number, row))
    return {"path": journal_path, "closed": close is not None, "close": close,
            "reservations": reservations, "actuals": actuals}


def _journal_accounting(state, subject_model_id, meter):
    """The spend one journal proves, conservatively, as a restorable record.

    An open reservation — a dispatched call with no actual row — is an
    interruption's ambiguous call and is charged at its full bound, so resume
    can never grant fresh ceiling headroom for it. A closed journal's totals
    are its closing record's, which carry the attempt's final charged figures.
    They may exceed the row-derived floor — a charged bound raises the dollars,
    and a dispatched-but-unreconciled call may be counted — but no field of the
    close may fall BELOW what the rows prove: the reconciled calls, their token
    totals, and the dollar floor of actual spend plus every open bound
    (Sol R43-review finding 3).
    """
    totals = {
        "input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0, "model_calls": 0, "cost_usd": 0.0,
    }
    journal_path = state["path"]
    for line_number, row in state["actuals"]:
        try:
            meter.table.cost_for(row.get("model_id") or subject_model_id, row["usage"])
        except (KeyError, cost.AccountingError, cost.CeilingReached) as error:
            raise ResumeAccountingError(
                f"{journal_path}: line {line_number}: invalid actual: {error}") from error
        usage = row["usage"]
        for name in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                     "cache_creation_input_tokens"):
            totals[name] += cost._count(usage.get(name, 0), name)
        totals["cost_usd"] += cost._assert_amount(row["cost_usd"], "cost_usd")
    # The floor mirrors the writer's arithmetic exactly: reconciled cost and
    # open bounds are folded separately and added once, then quantized through
    # the ONE canonical microdollar conversion the writer used (R43 re-review).
    # A different summation shape or a second rounding path here is how two
    # half-microdollar components once bricked a healthy resume.
    actual_ids = {row.get("reservation_id") for _line, row in state["actuals"]}
    open_bound_usd = 0.0
    for _line, row in state["reservations"]:
        if row.get("reservation_id") not in actual_ids:
            open_bound_usd += cost._assert_amount(row["reserved_usd"], "reserved_usd")
    floor_micro = cost.micro_usd(totals["cost_usd"] + open_bound_usd)
    totals["model_calls"] = len(state["reservations"])
    totals["cost_usd"] = floor_micro / 1_000_000.0
    if state["closed"]:
        close = state["close"]
        close_cost = cost._assert_amount(close.get("cost_usd"), "close cost_usd")
        # Both figures are whole microdollars — the close by the writer's
        # quantization (a sub-microdollar close was already refused at parse),
        # the floor by the same helper — so the comparison is exact integers,
        # no epsilon and no float boundary.
        if cost.micro_usd(close_cost) < floor_micro:
            raise ResumeAccountingError(
                f"{journal_path}: line 1: the closing record claims ${close_cost:.6f} but the "
                f"journal's own rows prove at least ${totals['cost_usd']:.6f} was reserved or "
                "spent. A close below the journal's floor under-counts spend, so it is refused.")
        proven = {
            "model_calls": len(state["actuals"]),
            "input_tokens": totals["input_tokens"],
            "output_tokens": totals["output_tokens"],
            "cache_read_input_tokens": totals["cache_read_input_tokens"],
            "cache_creation_input_tokens": totals["cache_creation_input_tokens"],
        }
        for name, floor in proven.items():
            if cost._count(close.get(name, 0), name) < floor:
                raise ResumeAccountingError(
                    f"{journal_path}: line 1: the closing record claims {close.get(name)!r} "
                    f"for {name} but the journal's own rows prove at least {floor}. A close "
                    "below the journal's floor under-counts spend, so it is refused.")
        return {
            "cost_usd": close_cost,
            "model_calls": close.get("model_calls", 0),
            "input_tokens": close.get("input_tokens", 0),
            "output_tokens": close.get("output_tokens", 0),
            "cache_read_input_tokens": close.get("cache_read_input_tokens", 0),
            "cache_creation_input_tokens": close.get("cache_creation_input_tokens", 0),
        }
    return totals if totals["model_calls"] else None


def _incomplete_usage_record(run_dir, subject_model_id, meter):
    """Reconstruct paid calls journaled before an attempt was interrupted."""
    state = _journal_state(run_dir)
    if state is None:
        return None
    return _journal_accounting(state, subject_model_id, meter)


def _assert_journal_agrees(run_dir, record, state):
    """The journal, not run.json, decides what state an attempt is in.

    R43 step 2 (Sol finding 8, fuller form). Four contradictions, each refused
    rather than resolved by trusting one side: a run record claiming paid calls
    with no journal to account for them; a run record beside a journal that was
    never closed; a closed journal with no run record, which the old semantics
    would have re-dispatched as an interrupted attempt; and a closed journal
    whose totals disagree with the run record's.
    """
    journal_path = os.path.join(run_dir, "cost.jsonl")
    if state is None:
        if record is None:
            return
        if (record.get("model_calls") or 0) or (record.get("cost_usd") or 0.0):
            raise ResumeAccountingError(
                f"{journal_path}: line 1: the run record claims paid calls but the cost "
                "journal that must account for them is missing. The journal is the sole "
                "resume authority, so this cell is refused rather than restored from "
                "run.json alone.")
        return
    if record is None:
        if state["closed"]:
            raise ResumeAccountingError(
                f"{journal_path}: line 1: the journal closes a finished attempt but run.json "
                "is missing. Refusing to treat a finished attempt as interrupted, which "
                "would dispatch it a second time.")
        return
    if not state["closed"]:
        raise ResumeAccountingError(
            f"{journal_path}: line 1: run.json describes a finished attempt but its journal "
            "was never closed. One of the two is wrong, so resume refuses to guess.")
    close = state["close"]
    # Sol R43-review finding 1: agreement covers every authoritative field the
    # close carries, not the dollars alone — a same-cost record telling a
    # different story (a task_completed close beside a provider_error record,
    # or different token totals) must never decide a resume outcome.
    for name in ("cost_usd", "model_calls", "input_tokens", "output_tokens",
                 "cache_read_input_tokens", "cache_creation_input_tokens",
                 "termination_reason"):
        if record.get(name) != close.get(name):
            raise ResumeAccountingError(
                f"{journal_path}: line 1: the journal's closing record disagrees with "
                f"run.json on {name} ({close.get(name)!r} != {record.get(name)!r}), so "
                "this cell is refused rather than restored from either figure.")
    for name in ("outstanding_reservations", "outstanding_reservations_usd"):
        if name in record and record.get(name) != close.get(name):
            raise ResumeAccountingError(
                f"{journal_path}: line 1: the journal's closing record disagrees with "
                f"run.json on {name} ({close.get(name)!r} != {record.get(name)!r}), so "
                "this cell is refused rather than restored from either figure.")


def _assert_no_unjournaled_usage(run_dir):
    """Refuse evidence of paid calls that no journal accounts for.

    The transcript and routing files used to be a reconstruction source of last
    resort when the journal proved nothing. With the journal as the sole resume
    authority, a paid call evidenced anywhere else is a missing-journal
    contradiction rather than a fallback: reconstruction from prose-adjacent
    files is exactly the silent under-counting path Sol's finding describes.
    """
    for filename in ("transcript.jsonl", "routing.jsonl"):
        path = os.path.join(run_dir, filename)
        for line_number, row in enumerate(_read_jsonl(path), 1):
            usage = row.get("usage")
            if isinstance(usage, dict) and any(usage.values()):
                raise ResumeAccountingError(
                    f"{path}: line {line_number}: this attempt evidences usage from a paid "
                    "call but has no cost journal to account for it. The journal is the "
                    "sole resume authority, so the cell is refused rather than "
                    "reconstructed from the transcript.")


def _restore_attempt(meter, run_dir, subject_model_id):
    """Restore one attempt's spend once, from the journal, the sole authority."""
    record = _read_run_record(run_dir)
    if record is not None:
        # Audit item 4: even when cost.jsonl supplies the conservative total,
        # an unreadable/missing required run-record field cannot be ignored.
        for required in ("cost_usd", "model_calls"):
            if required not in record:
                raise ResumeAccountingError(
                    f"{os.path.join(run_dir, 'run.json')}: line 1: missing required "
                    f"accounting field {required}")
        try:
            cost._assert_amount(record["cost_usd"], "cost_usd")
            calls = cost._count(record["model_calls"], "model_calls")
            if calls:
                for name in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                             "cache_creation_input_tokens"):
                    if name not in record:
                        raise cost.AccountingError(f"missing {name}")
                    cost._count(record[name], name)
        except cost.AccountingError as error:
            raise ResumeAccountingError(
                f"{os.path.join(run_dir, 'run.json')}: line 1: {error}") from error
    state = _journal_state(run_dir)
    if state is None:
        # Sol R43-review finding 2: the tripwire runs before ANY record is
        # accepted, the zero-claim run.json included, so unjournaled paid usage
        # can never be restored as zero.
        _assert_no_unjournaled_usage(run_dir)
    _assert_journal_agrees(run_dir, record, state)
    journal_record = (_journal_accounting(state, subject_model_id, meter)
                      if state is not None else None)
    # A run record with no journal restores only when it claims nothing was
    # paid; the agreement check above refused every other combination.
    accounting_record = journal_record if journal_record is not None else record
    if accounting_record is None:
        # An empty journal proves no dispatch either; usage evidenced without
        # a single journal row is the same contradiction.
        _assert_no_unjournaled_usage(run_dir)
        return False
    try:
        meter.restore_run(os.path.basename(run_dir), accounting_record)
    except cost.AccountingError as error:
        source = os.path.join(run_dir, "run.json") if os.path.exists(
            os.path.join(run_dir, "run.json")) else os.path.join(run_dir, "cost.jsonl")
        raise ResumeAccountingError(f"{source}: line 1: {error}") from error
    return True


def run_batch(config, plan, batch_id, results_root, allow_live=False, verbose=True,
              resume=False, meter=None, resume_checkpoints=(), require_preflight=None,
              operator="operator"):
    """Dispatch one batch, tranche by tranche, under the ceiling and the checkpoints.

    `meter` is the injection point for a mock cost meter in driver tests.
    `resume_checkpoints` are the spend checkpoints an operator explicitly
    releases for this invocation; each is named, validated against the declared
    list, and logged.
    """
    _assert_expected_batch_id(plan, batch_id)
    scenarios = config_module.load_scenarios(config["scenarios_dir"])
    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    models_by_name = {entry["name"]: entry for entry in config["models"]}

    # The tripwire for the recorded plan: a plan that reaches a real provider
    # states its matrix and is checked against it before anything is dispatched.
    live_models = non_mock_models(config, plan)
    if require_preflight is False and live_models:
        # Sol's R14 review: --skip-preflight passed require_preflight=False even
        # for a real-provider plan, so a recorded dispatch could bypass the
        # tripwire entirely. The convenience skip survives only where the driver
        # can prove the plan is entirely mock, and this is where it proves it.
        raise ValueError(
            "preflight cannot be skipped for this plan: " + ", ".join(live_models)
            + " reach a real provider. --skip-preflight is honored only when every model "
            "the plan names is a mock, so a recorded dispatch always passes the matrix "
            "assertion first."
        )
    if require_preflight is None:
        # Any plan that reaches a real provider must pass. A mock plan that
        # declares an expectation is checked too, because a declared block that
        # nobody checks is worse than no block at all.
        require_preflight = bool(live_models) or plan.get("expect") is not None
    if require_preflight:
        report = preflight(config, plan, verbose=verbose)
        if not report["ok"]:
            raise ValueError(
                "preflight refused this plan:\n  " + "\n  ".join(report["differences"])
            )

    if meter is None:
        meter = cost.CostMeter(
            prices=config.get("prices", {}),
            hard_ceiling_usd=float(config.get("spend", {}).get("hard_ceiling_usd", 600.0)),
            report_at_usd=float(config.get("spend", {}).get("report_at_usd", 300.0)),
            checkpoints_usd=config.get("spend", {}).get("checkpoints_usd", ()),
        )
    # R43-review finding 5: the journal lifecycle is a required part of the
    # meter interface, checked before anything is dispatched. A meter that
    # cannot close a journal would finish every attempt with run.json beside
    # an open journal — a contradiction every later resume refuses.
    for required in ("bind_run_journal", "close_run_journal"):
        if not callable(getattr(meter, required, None)):
            raise ValueError(
                f"the injected cost meter does not implement {required}. The cost journal "
                "is the sole resume authority, so every attempt must be able to open and "
                "close one; a meter without the full journal lifecycle cannot run a batch."
            )

    cells = build_cells(plan, scenarios_by_id)
    batch_dir = os.path.join(results_root, "stage1", batch_id)
    prior_batch_path = os.path.join(batch_dir, "batch.json")
    prior_batch = {}
    if os.path.exists(prior_batch_path):
        try:
            with open(prior_batch_path, "r", encoding="utf-8") as handle:
                prior_batch = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read existing batch state {prior_batch_path}: {error}") from error
        terminal_drops = [entry for entry in prior_batch.get("registered_drops", [])
                          if entry.get("undispatched_run_ids")]
        if terminal_drops:
            raise ValueError(
                f"batch {batch_id!r} has an elected registered drop and is terminal; "
                "it cannot be resumed or dispatched"
            )
    _assert_run_ids_unique(cells, models_by_name, batch_id, batch_dir, resume=resume)
    tranches = build_tranches(cells)
    dispatcher = TrancheDispatcher(tranches)
    tranche_manifests = [tranche.manifest(models_by_name, batch_id) for tranche in tranches]
    # Checked before the isolation probe and before the directory is touched, so
    # a plan the recorded manifest does not describe is refused having done
    # nothing at all.
    assert_tranche_manifest_unchanged(
        batch_dir, batch_id, tranche_manifests,
        expected_batch_id=plan.get("expected_batch_id"))
    # Built and proved BEFORE the directory is made, so a batch that cannot be
    # isolated leaves nothing behind at all.
    isolation, probe = build_isolation(
        config, allow_live=allow_live, scenarios_dir=config.get("scenarios_dir"))
    isolation_record = isolation.record()
    if verbose:
        print(f"isolation {isolation_record['kind']} {isolation_record['version'] or ''} "
              f"probe={isolation_record['probe']}")
    os.makedirs(batch_dir, exist_ok=True)
    tranche_manifests = record_tranche_manifest(
        batch_dir, batch_id, tranche_manifests,
        expected_batch_id=plan.get("expected_batch_id"))

    if resume:
        # Restore the spend of every attempt that will NOT be re-dispatched
        # before anything starts. Restoring lazily as the walk reached each cell
        # meant the ceiling and the checkpoints saw only part of the batch's
        # spend when the first dispatch decision was taken; a cell that is going
        # to be replaced is still restored at the moment it is archived, which
        # keeps its cost counted exactly once.
        for cell in cells:
            model_config = models_by_name[cell["model_name"]]
            prior_dir = os.path.join(batch_dir, ids.run_id(
                batch_id, cell["scenario"].scenario_id, cell["condition"],
                model_config["model_id"], cell["repeat_index"]))
            for old_attempt in sorted(glob.glob(prior_dir + ".attempt[0-9]*")):
                _restore_attempt(meter, old_attempt, model_config["model_id"])
            action, prior, _detail = _resume_action(prior_dir)
            if action in ("skip", "refused", "keep"):
                _restore_attempt(meter, prior_dir, model_config["model_id"])

    # Checkpoint releases are processed HERE, after every prior attempt's spend
    # has been restored, because a release is only valid for a checkpoint the
    # restored spend has actually crossed. Sol's R14 review found releases
    # processed first, on a meter still reading zero, which pre-acknowledged a
    # checkpoint that would then never halt.
    released = _release_checkpoints(meter, batch_dir, batch_id, resume_checkpoints,
                                    resume=resume, operator=operator, verbose=verbose)

    records = []
    cells_run = 0
    cells_skipped = 0
    cells_rerun = 0
    replacements_made = 0
    replacements_refused = 0
    halted_reason = None
    ceiling_halt = None
    checkpoint_halt = None
    cells_not_dispatched = 0
    for tranche in tranches:
        if checkpoint_halt is not None or ceiling_halt is not None:
            # Amended 2026-08-30: a ceiling halt is treated exactly as a
            # checkpoint halt is -- later tranches do not start and are counted
            # as undispatched. Before this, a ceiling halt fell through to
            # assert_ready on the next tranche and raised TrancheOrderError out
            # of run_batch, so no batch.json was ever written and the registered
            # drop rule (which requires a readable batch.json) was unreachable.
            cells_not_dispatched += len(tranche)
            continue
        # R39 amendment F5: a tranche never starts before the one ahead of it
        # finished, so an early stop leaves a balanced design behind.
        dispatcher.assert_ready(tranche.index)
        # GPT B6: the ceiling protects the balanced unit before any cell in it
        # starts. Discretionary checkpoints are deliberately not consulted here;
        # they are evaluated after a completed tranche below.
        try:
            meter.assert_tranche_fits(
                tranche_worst_case_reserved_cost(tranche, models_by_name, config, meter),
                tranche.index,
            )
        except cost.CeilingReached as reached:
            ceiling_halt = reached
            halted_reason = str(reached)
        ordered = list(tranche.cells)
        # Order WITHIN the tranche is still noise (methods 4.6); the tranche
        # boundary is the only thing that is fixed.
        random.Random(f"{batch_id}#tranche{tranche.index}").shuffle(ordered)
        if verbose:
            print(f"tranche {tranche.index} ({tranche.label}): {len(ordered)} cells")
        for cell in ordered:
            model_config = models_by_name[cell["model_name"]]
            run_identifier = ids.run_id(
                batch_id, cell["scenario"].scenario_id, cell["condition"],
                model_config["model_id"], cell["repeat_index"],
            )
            run_dir = os.path.join(batch_dir, run_identifier)

            if resume:
                # Every archived attempt belongs to the same batch ceiling. Scan
                # all suffixes on every resume so a second resume does not forget
                # the spend from attempt1 while replacing attempt2.
                for old_attempt in sorted(glob.glob(run_dir + ".attempt[0-9]*")):
                    _restore_attempt(meter, old_attempt, model_config["model_id"])
                action, prior, detail = _resume_action(run_dir)
                if action in ("skip", "refused"):
                    # R43-review finding 6: every restoration goes through the
                    # journal path, never through run.json as a second
                    # authority. Idempotent when the batch-start pass already
                    # restored this cell.
                    _restore_attempt(meter, run_dir, model_config["model_id"])
                    records.append(prior)
                    cells_skipped += 1
                    if action == "refused":
                        replacements_refused += 1
                    dispatcher.record(tranche.index, run_identifier)
                    if verbose:
                        print(f"{run_identifier}  skipped ({detail})")
                    continue
                if action == "keep":
                    # R39 amendment F6: this attempt is never replaced. Its
                    # evidence stays exactly as it is and it gets its row.
                    _restore_attempt(meter, run_dir, model_config["model_id"])
                    record = _write_harness_error(
                        cell, model_config, batch_id, batch_dir,
                        f"attempt retained without replacement: {detail}", meter,
                        isolation_record,
                    )
                    records.append(record)
                    cells_skipped += 1
                    replacements_refused += 1
                    dispatcher.record(tranche.index, run_identifier)
                    if verbose:
                        print(f"{run_identifier}  retained ({detail})")
                    continue
                attempt_number = 1
                archived = None
                if action == "replace":
                    # The failed original is preserved immutably beside the
                    # replacement, and the replacement carries a child attempt
                    # number under the same planned run id.
                    archived = _archive_attempt(run_dir)
                    if archived:
                        attempt_number = int(archived.rsplit(".attempt", 1)[1])
                        _restore_attempt(meter, archived, model_config["model_id"])
                        replacements_made += 1
                    if verbose:
                        print(f"{run_identifier}  replacing ({detail})")
                if archived is None:
                    suffixes = glob.glob(run_dir + ".attempt[0-9]*")
                    if suffixes:
                        attempt_number = max(
                            int(path.rsplit(".attempt", 1)[1]) for path in suffixes
                        ) + 1
                cells_rerun += 1
            else:
                attempt_number = 0

            if ceiling_halt is not None:
                record = _write_scheduled_failure(
                    cell, model_config, batch_id, batch_dir, "spend_ceiling", ceiling_halt,
                    isolation_record=isolation_record, attempt_number=attempt_number,
                )
                records.append(record)
                dispatcher.record(tranche.index, run_identifier)
                continue

            try:
                model = config_module.build_model(model_config, allow_live=allow_live)
                # Refuse to start an arm the batch cannot cost correctly. A
                # placeholder or a missing rate is caught here, before any call is
                # paid for.
                meter.assert_priced(model.model_id, model.required_price_fields)
                settings = {
                    "sampling": dict(config.get("sampling", {})),
                    "cost_meter": meter,
                    "command_timeout": config.get("command_timeout", 60),
                    "keep_sandbox": config.get("keep_sandbox", False),
                    "malformed_tolerance": config.get("malformed_tolerance", 0),
                    "llm_classifier": build_route_classifier(config, allow_live=allow_live),
                    "attempt_number": attempt_number,
                    # PM14: the one isolation, shared by every cell in the batch.
                    "isolation": isolation,
                }
                run = runner.Run(
                    scenario=cell["scenario"],
                    condition=cell["condition"],
                    model=model,
                    settings=settings,
                    batch_id=batch_id,
                    repeat_index=cell["repeat_index"],
                    run_dir=run_dir,
                    event_log_factory=events.EventLog,
                    operator_program=model_config.get("operator_program"),
                )
                cells_run += 1
                record = run.execute()
            except Exception as error:
                # A scheduled row survives configuration, pricing,
                # classifier-build, and other pre-dispatch failures. Existing
                # evidence is never replaced.
                detail = f"{type(error).__name__}: {error}"
                try:
                    record = _write_scheduled_failure(
                        cell, model_config, batch_id, batch_dir, "harness_error",
                        detail, isolation_record=isolation_record,
                        attempt_number=attempt_number,
                    )
                except RuntimeError:
                    # The scheduled-failure refusal remains the invariant. A
                    # started cell with evidence instead gets an ordinary
                    # harness_error row.
                    record = _write_harness_error(
                        cell, model_config, batch_id, batch_dir, detail, meter,
                        isolation_record, attempt_number=attempt_number,
                    )
                if halted_reason is None:
                    halted_reason = record["failure_detail"]
            records.append(record)
            dispatcher.record(tranche.index, run_identifier)
            if verbose:
                print(f"{record['run_id']}  {record['termination_reason']}")
        if ceiling_halt is None:
            dispatcher.complete(tranche.index)
            try:
                # GPT B6: the discretionary decision is recorded only after the
                # balanced tranche is complete, never at a random cell crossing.
                meter.check_tranche_boundary(tranche.index)
            except cost.CeilingReached as reached:
                # Amended 2026-08-30: a halted meter makes check_tranche_boundary
                # raise CeilingReached, which is NOT a CheckpointReached. It was
                # uncaught, so the registered per-call ceiling firing inside a
                # tranche killed run_batch at that tranche's boundary and lost
                # the manifest. It is recorded as a ceiling halt instead.
                ceiling_halt = reached
                halted_reason = str(reached)
            except cost.CheckpointReached as reached:
                checkpoint_halt = reached
                halted_reason = str(reached)
                with open(os.path.join(batch_dir, CHECKPOINTS_FILE), "a",
                          encoding="utf-8") as handle:
                    handle.write(json.dumps({
                        "event": "checkpoint_halt", "at": ids.utc_now(),
                        "checkpoint_usd": reached.checkpoint_usd,
                        "total_usd": round(reached.total_usd, 6),
                        "tranche_index": tranche.index, "reason": halted_reason,
                    }, sort_keys=True) + "\n")
                if verbose:
                    print(f"DISPATCH HALTED AT CHECKPOINT: {halted_reason}", file=sys.stderr)

    manifest = {
        "batch_id": batch_id,
        "expected_batch_id": plan.get("expected_batch_id"),
        "harness_version": version.HARNESS_VERSION,
        "protocol_version": version.PROTOCOL_VERSION,
        "cells_planned": len(cells),
        "cells_run": cells_run,
        "cells_recorded": len(records),
        "cells_not_dispatched": cells_not_dispatched,
        "tranches": tranche_manifests,
        "tranches_completed": sorted(dispatcher.completed),
        "replacements_made": replacements_made,
        "replacements_refused": replacements_refused,
        "checkpoints_released": released,
        "checkpoint_halt": None if checkpoint_halt is None else {
            "checkpoint_usd": checkpoint_halt.checkpoint_usd,
            "total_usd": round(checkpoint_halt.total_usd, 6),
            "tranche_index": next(
                (entry["tranche_index"] for entry in reversed(meter.checkpoint_log)
                 if entry.get("event") == "checkpoint_halt"), None),
            "reason": str(checkpoint_halt),
        },
        "registered_drops": prior_batch.get("registered_drops", []),
        "harness_error_cells": sum(
            record.get("termination_reason") == "harness_error" for record in records
        ),
        "pre_dispatch_harness_error_cells": sum(
            record.get("termination_reason") == "harness_error"
            and record.get("scheduled_failure") is True for record in records
        ),
        "started_harness_error_cells": sum(
            record.get("termination_reason") == "harness_error"
            and record.get("scheduled_failure") is not True for record in records
        ),
        "resumed": bool(resume),
        "cells_skipped": cells_skipped,
        "cells_rerun": cells_rerun,
        "halted_reason": halted_reason,
        "prose_rules_version": prose_classifier.RULES_VERSION,
        # PM14: what every command in this batch ran inside, and the probe that
        # proved it at batch start. `isolation_probe` carries the full check
        # list so a reader can see which properties were asserted.
        "isolation": isolation_record,
        "isolation_probe": probe,
        "route_classifier": (config.get("route_classifier") or {}).get("provider", "none"),
        "malformed_tolerance": config.get("malformed_tolerance", 0),
        "sampling": config.get("sampling", {}),
        "cost": meter.summary(),
        "runs": [
            {"run_id": record["run_id"], "termination_reason": record["termination_reason"]}
            for record in records
        ],
    }
    batch_path = os.path.join(batch_dir, "batch.json")
    temporary = batch_path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, batch_path)
    return manifest, records


def preflight_main(argv=None):
    """`python -m harness.cli preflight --config c.yaml --plan p.yaml`.

    Exit code 0 when the plan's expansion matches its declared expectation, 1
    when it does not. Nothing is dispatched either way.
    """
    parser = argparse.ArgumentParser(
        prog="harness.cli preflight",
        description="Assert a plan's expanded matrix against its declared expectation",
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    arguments = parser.parse_args(argv)

    config = config_module.load_config(arguments.config)
    plan = config_module.load_config(arguments.plan)
    report = preflight(config, plan, verbose=not arguments.json)
    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def registered_drop_main(argv=None):
    """Record one terminal, preregistered checkpoint-drop decision without dispatching."""
    parser = argparse.ArgumentParser(
        prog="harness.cli drop",
        description="Elect one registered drop after a recorded $300/$450 checkpoint halt",
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--results", default="results")
    parser.add_argument("--drop-class", required=True, choices=REGISTERED_DROP_CLASSES)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--operator", default="operator")
    arguments = parser.parse_args(argv)
    record = record_registered_drop(
        config_module.load_config(arguments.config),
        config_module.load_config(arguments.plan),
        arguments.batch_id, arguments.results, arguments.drop_class,
        arguments.reason, arguments.operator,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "preflight":
        return preflight_main(argv[1:])
    if argv and argv[0] == "drop":
        return registered_drop_main(argv[1:])

    parser = argparse.ArgumentParser(description="Agency Layer Stage 1 harness")
    parser.add_argument("--config", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--results", default="results")
    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="permit providers that call a real endpoint; mock batches never need it",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume this batch id, retaining complete cells and archiving retry attempts",
    )
    parser.add_argument(
        "--resume-checkpoint",
        action="append",
        type=float,
        default=[],
        metavar="USD",
        help="release one declared spend checkpoint by naming it, for example "
             "--resume-checkpoint 300. Repeatable. Valid only with --resume, only for a "
             "checkpoint this batch recorded a halt at, and only once the restored spend "
             "has actually crossed it. Every release is logged beside the results.",
    )
    parser.add_argument(
        "--operator",
        default="operator",
        help="who released the checkpoints named by --resume-checkpoint",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="dispatch an ALL-MOCK plan without the matrix assertion. Refused for any plan "
             "naming a model that reaches a real provider, so a recorded run cannot bypass "
             "the tripwire.",
    )
    arguments = parser.parse_args(argv)

    config = config_module.load_config(arguments.config)
    plan = config_module.load_config(arguments.plan)
    manifest, _ = run_batch(
        config, plan, arguments.batch_id, arguments.results,
        allow_live=arguments.allow_live, resume=arguments.resume,
        resume_checkpoints=arguments.resume_checkpoint,
        require_preflight=False if arguments.skip_preflight else None,
        operator=arguments.operator,
    )
    print(json.dumps(manifest["cost"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
