"""Cost the full R15 matrix from the rehearsal's measured tokens (R34).

R34 asks for the matrix to be costed from measured tokens rather than guessed,
and for a drop order fixed before any result is seen. R37 accepted the proposed
order: frontier-tier replication first, then repeats 4 to 3, scenarios never.
This script reads the rehearsal output and applies that order in sequence,
printing the running cost against the $600 ceiling (R17) at each step.

What it measures, from results/stage1/rehearsal/:

    per model, per family, per condition: mean input, output, cache-read and
    cache-write tokens per run, and the mean number of prose stops, which is
    what the route classifier is billed for.

What it projects:

    primary matrix   R15: 4 conditions x 40 scenarios x 4 repeats, per API arm.
                     The local arm is free (R17) and is counted at zero.
    frontier tier    R29: Opus 5 and Sol on the primary contrast cells
                     (B against C, per PM1) across the full scenario set at 2
                     repeats.
    route classifier PM8: one call per prose stop, in every arm and condition.

Three things it does NOT do quietly, because a projection that hides its
assumptions is worse than no projection:

  * The rehearsal covers five families. Families 3, 4 and 6 are priced from the
    mean of the measured families for the same model and condition, and the
    report says what fraction of the total rests on that substitution.
  * It assumes no cross-run cache reuse. Repeats of the same cell run close
    together may share a warm prefix and cost less. Assuming that saving would
    make the projection optimistic, which is the wrong direction for a ceiling.
  * An unpriced arm is named and left out of the total rather than guessed at.

Usage:

    .venv/bin/python tools/cost_projection.py --config rehearsal.yaml
    .venv/bin/python tools/cost_projection.py --config rehearsal.yaml --json out.json
"""

import argparse
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from harness import config as config_module, cost  # noqa: E402

# R15: 8 families x 5 variants, 4 conditions, 4 repeats.
FAMILIES = list(range(1, 9))
SCENARIOS_PER_FAMILY = 5
CONDITIONS = ["A", "B", "C", "D"]
PRIMARY_REPEATS = 4

# R29 / PM1: the frontier tier replicates the primary contrast, C against B.
FRONTIER_CONDITIONS = ["B", "C"]
FRONTIER_REPEATS = 2
FRONTIER_OF = {"claude-sonnet-5": "claude-opus-5", "gpt-5.6-terra": "gpt-5.6-sol"}

CEILING_USD = 600.0
REPORT_AT_USD = 300.0


def load_runs(results_dir):
    runs = []
    for path in sorted(glob.glob(os.path.join(results_dir, "*", "run.json"))):
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        routing = os.path.join(os.path.dirname(path), "routing.jsonl")
        prose_stops = 0
        if os.path.exists(routing):
            with open(routing, "r", encoding="utf-8") as handle:
                prose_stops = sum(1 for line in handle
                                  if line.strip() and json.loads(line).get("trigger") == "prose_stop")
        record["prose_stops"] = prose_stops
        runs.append(record)
    return runs


def measure(runs):
    """Mean token usage per run, keyed by (model_id, family, condition)."""
    buckets = {}
    for record in runs:
        key = (record["model_id"], record["family"], record["condition"])
        buckets.setdefault(key, []).append(record)
    measured = {}
    for key, records in buckets.items():
        measured[key] = {
            "runs": len(records),
            "input_tokens": statistics.mean(r["input_tokens"] for r in records),
            "output_tokens": statistics.mean(r["output_tokens"] for r in records),
            "cache_read": statistics.mean(r.get("cache_read_input_tokens", 0) for r in records),
            "cache_write": statistics.mean(r.get("cache_creation_input_tokens", 0) for r in records),
            "prose_stops": statistics.mean(r.get("prose_stops", 0) for r in records),
            "cost_usd": statistics.mean(r["cost_usd"] for r in records),
        }
    return measured


def cell_usage(measured, model_id, family, condition):
    """Measured usage for this cell, or the model-and-condition mean as a stand-in."""
    exact = measured.get((model_id, family, condition))
    if exact:
        return exact, False
    peers = [value for (m, _f, c), value in measured.items()
             if m == model_id and c == condition]
    if not peers:
        return None, True
    averaged = {
        name: statistics.mean(p[name] for p in peers)
        for name in ("input_tokens", "output_tokens", "cache_read", "cache_write", "prose_stops")
    }
    averaged["runs"] = 0
    averaged["cost_usd"] = statistics.mean(p["cost_usd"] for p in peers)
    return averaged, True


def price_usage(table, model_id, usage):
    """Cost one run's measured usage at the frozen rates."""
    return table.cost_for(model_id, {
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cache_read_input_tokens": usage["cache_read"],
        "cache_creation_input_tokens": usage["cache_write"],
    })


def project(measured, table, api_models, classifier_model, classifier_usage, repeats):
    """The whole matrix at a given repeat count. Returns components and warnings."""
    components = {}
    warnings = []
    substituted_usd = 0.0
    total_measured_usd = 0.0

    # ---- primary matrix, per API arm
    for model_id in api_models:
        if not table.has(model_id):
            warnings.append(f"{model_id} has no price; its primary cells are not counted")
            continue
        subtotal = 0.0
        for family in FAMILIES:
            for condition in CONDITIONS:
                usage, substituted = cell_usage(measured, model_id, family, condition)
                if usage is None:
                    warnings.append(f"no rehearsal data for {model_id} condition {condition}")
                    continue
                per_run = price_usage(table, model_id, usage)
                cells = SCENARIOS_PER_FAMILY * repeats
                subtotal += per_run * cells
                if substituted:
                    substituted_usd += per_run * cells
                else:
                    total_measured_usd += per_run * cells
        components[f"primary:{model_id}"] = subtotal

    # ---- frontier tier (R29), primary contrast cells only
    for model_id in api_models:
        frontier = FRONTIER_OF.get(model_id)
        if frontier is None:
            continue
        if not table.has(frontier):
            warnings.append(
                f"{frontier} has no price, so the frontier half replicating {model_id} is "
                "NOT in the total. Price it before relying on the frontier figure.")
            components[f"frontier:{frontier}"] = None
            continue
        subtotal = 0.0
        for family in FAMILIES:
            for condition in FRONTIER_CONDITIONS:
                usage, _ = cell_usage(measured, model_id, family, condition)
                if usage is None:
                    continue
                # Token counts come from the primary arm of the same family and
                # condition: a scenario's length is mostly a property of the task,
                # not of the model. Priced at the frontier model's own rates.
                subtotal += price_usage(table, frontier, usage) * SCENARIOS_PER_FAMILY \
                    * FRONTIER_REPEATS
        components[f"frontier:{frontier}"] = subtotal

    # ---- the route classifier, one call per prose stop, every arm
    if classifier_model and table.has(classifier_model):
        stops = 0.0
        for model_id in api_models:
            for family in FAMILIES:
                for condition in CONDITIONS:
                    usage, _ = cell_usage(measured, model_id, family, condition)
                    if usage:
                        stops += usage["prose_stops"] * SCENARIOS_PER_FAMILY * repeats
        per_call = table.cost_for(classifier_model, classifier_usage)
        components["route_classifier"] = stops * per_call
        components["_classifier_calls"] = stops
    elif classifier_model:
        warnings.append(f"the route classifier model {classifier_model} has no price; "
                        "its calls are not counted")
        components["route_classifier"] = None

    components["_substituted_usd"] = substituted_usd
    components["_measured_usd"] = total_measured_usd
    return components, warnings


def total_of(components, drop_frontier=False):
    total = 0.0
    for name, value in components.items():
        if name.startswith("_") or value is None:
            continue
        if drop_frontier and name.startswith("frontier:"):
            continue
        total += value
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cost the R15 matrix from the R34 rehearsal")
    parser.add_argument("--config", default=os.path.join(ROOT, "rehearsal.yaml"))
    parser.add_argument("--results", default=os.path.join(ROOT, "results", "stage1", "rehearsal"))
    parser.add_argument("--classifier-model", default="claude-haiku-4-5-20251001",
                        help="the frozen route classifier's model, billed once per prose stop")
    parser.add_argument("--classifier-input-tokens", type=int, default=1200)
    parser.add_argument("--classifier-output-tokens", type=int, default=8)
    parser.add_argument("--json", help="also write the projection as JSON")
    arguments = parser.parse_args(argv)

    config = config_module.load_config(arguments.config)
    table = cost.PriceTable(config.get("prices", {}))

    runs = load_runs(arguments.results)
    if not runs:
        print(f"No rehearsal runs under {arguments.results}.")
        print("Run the rehearsal first:")
        print("  .venv/bin/python -m harness.cli --config rehearsal.yaml "
              "--plan rehearsal_plan.yaml --batch-id rehearsal --results results")
        return 1

    measured = measure(runs)
    api_models = [entry["model_id"] for entry in config["models"]
                  if entry["provider"] in ("anthropic", "openai")]
    free_models = [entry["model_id"] for entry in config["models"]
                   if entry["provider"] == "local"]
    classifier_usage = {"input_tokens": arguments.classifier_input_tokens,
                        "output_tokens": arguments.classifier_output_tokens}

    print(f"Rehearsal: {len(runs)} runs, "
          f"${sum(r['cost_usd'] for r in runs):.4f} actually spent")
    print(f"Measured families: {sorted({r['family'] for r in runs})}; "
          f"unmeasured: {sorted(set(FAMILIES) - {r['family'] for r in runs})}")
    print(f"Free arms counted at zero: {', '.join(free_models) or 'none'}")
    print()

    print("Measured mean tokens per run")
    print(f"  {'model':<18}{'fam':>4}{'cond':>6}{'in':>9}{'out':>8}{'cache r':>9}"
          f"{'cache w':>9}{'stops':>7}{'$/run':>9}")
    for (model_id, family, condition), value in sorted(measured.items()):
        print(f"  {model_id:<18}{family:>4}{condition:>6}{value['input_tokens']:>9.0f}"
              f"{value['output_tokens']:>8.0f}{value['cache_read']:>9.0f}"
              f"{value['cache_write']:>9.0f}{value['prose_stops']:>7.1f}"
              f"{value['cost_usd']:>9.4f}")
    print()

    steps = []
    full, warnings = project(measured, table, api_models, arguments.classifier_model,
                             classifier_usage, PRIMARY_REPEATS)
    steps.append(("full plan, R15 with the R29 frontier tier",
                  total_of(full), full, PRIMARY_REPEATS, True))

    # R34 drop order, in sequence. Fixed before any result was seen (R37).
    steps.append(("drop 1: frontier-tier replication (R29)",
                  total_of(full, drop_frontier=True), full, PRIMARY_REPEATS, False))

    reduced, _ = project(measured, table, api_models, arguments.classifier_model,
                         classifier_usage, 3)
    steps.append(("drop 2: repeats 4 to 3",
                  total_of(reduced, drop_frontier=True), reduced, 3, False))

    print("Components of the full plan")
    for name, value in sorted(full.items()):
        if name.startswith("_"):
            continue
        shown = "UNPRICED, not counted" if value is None else f"${value:,.2f}"
        print(f"  {name:<34}{shown:>24}")
    if full.get("_classifier_calls"):
        print(f"  {'(route classifier calls)':<34}{full['_classifier_calls']:>24,.0f}")
    print()

    substituted = full["_substituted_usd"]
    measured_usd = full["_measured_usd"]
    if substituted:
        share = 100.0 * substituted / max(1e-9, substituted + measured_usd)
        print(f"Families 3, 4 and 6 were not rehearsed. ${substituted:,.2f} of the primary "
              f"matrix ({share:.0f} percent) is priced")
        print("from the mean of the measured families, not from measurement.")
        print()

    print(f"R34 drop order, applied in sequence, against the ${CEILING_USD:.0f} ceiling (R17)")
    print(f"  {'step':<44}{'total':>13}{'headroom':>13}  verdict")
    for label, total, _components, _repeats, _frontier in steps:
        headroom = CEILING_USD - total
        if total > CEILING_USD:
            verdict = "OVER the ceiling"
        elif total > REPORT_AT_USD:
            verdict = f"fits, past the ${REPORT_AT_USD:.0f} report line"
        else:
            verdict = "fits"
        money = f"${total:,.2f}"
        room = f"${headroom:,.2f}"
        print(f"  {label:<44}{money:>13}{room:>13}  {verdict}")
    print("  scenarios are never dropped (R34)")
    print()

    affordable = [(label, total) for label, total, *_ in steps if total <= CEILING_USD]
    if affordable:
        label, total = affordable[0]
        print(f"Earliest step that fits: {label} at ${total:,.2f}. "
              "No further drops are needed.")
    else:
        print("No step in the drop order fits the ceiling. The order is exhausted and the "
              "decision goes back to Grant, since scenarios are never dropped.")
    for warning in warnings:
        print(f"  NOTE {warning}")

    if arguments.json:
        payload = {
            "rehearsal_runs": len(runs),
            "rehearsal_spend_usd": sum(r["cost_usd"] for r in runs),
            "measured": {f"{m}|{f}|{c}": v for (m, f, c), v in measured.items()},
            "steps": [{"label": label, "total_usd": total, "repeats": repeats,
                       "includes_frontier": frontier}
                      for label, total, _c, repeats, frontier in steps],
            "components": {k: v for k, v in full.items() if not k.startswith("_")},
            "substituted_usd": substituted,
            "ceiling_usd": CEILING_USD,
            "warnings": warnings,
        }
        with open(arguments.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"\nwrote {arguments.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
