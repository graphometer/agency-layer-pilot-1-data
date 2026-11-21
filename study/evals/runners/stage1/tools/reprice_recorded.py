#!/usr/bin/env python3
"""Price the recorded package from the committed plans and measured token profiles (brief step 6).

Regenerated 2026-08-25 for the post-R43/R45/R46/R47 design. The previous version of this script
priced the superseded four-repeat matrix from hardcoded constants; this one reads the committed
plan files, so the projection and the plans cannot drift apart. BUDGET.md quotes this script's
output and nothing else.

Measured inputs, each committed:
  * per-cell subject token means — results/development/rehearsal-2026-08-23/COST_PROJECTION.txt
    (families 1, 2, 5, 7, 8 measured; 3, 4, 6 projected as the measured-family mean for the same
    subject and condition; DeepSeek projected as the per-cell MAXIMUM of the two measured API
    subjects — both conventions unchanged from the correction phase)
  * per-condition pre-gate prose-turn rates for the condition-invariant routed timing reading —
    docs/review/judge-validation/instrument-closure-lane/frame.jsonl, restricted to the E2
    families (2, 3, 4, 6), the reading's scope
  * instrument prices — evals/grading/instrument_prices.json (mistral row corrected to the
    Medium 3.5 generation, R47 step-6 note)
  * measured secondary-judge output behaviour — the instrument lane's settled journals
    (mean 261 output tokens per call with thinking; the 8,192-token cap prices the reservation)

Branch-3 instrument scope (R47), stated here because money follows it:
  * The fresh Part B component makes ZERO instrument calls: its endpoint is deterministic and no
    semantic judge qualified, so no semantic sensitivity is computed there (PILOT_PROTOCOL §8).
  * Core E2 is descriptive only, but the preregistered readings are still computed and published
    with the instrument-error profile, so the judge pass still runs on the core, the two prose
    controls and family 9.
  * The condition-invariant routed timing reading (always computed once the lane built its
    projection — §5) requires routing EVERY pre-gate prose turn of the E2-family rows; non-E2
    rows keep only the narrower stop-shaped routing duty (measured 864/1,920 runs).

B_scaffolded rows are priced from the measured condition-B profile (the arm did not exist at
rehearsal time) plus an explicit uncached input adjustment for its longer system prompt; its
prose-turn rate is proxied by B_filler's measured rate. Both proxies are printed.

Usage: python3 tools/reprice_recorded.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE1 = HERE.parent
REPO = STAGE1.parents[2]
MEASURED = REPO / "results" / "development" / "rehearsal-2026-08-23" / "COST_PROJECTION.txt"
INSTRUMENT_PRICES = REPO / "evals" / "grading" / "instrument_prices.json"
FRAME = REPO / "docs" / "review" / "judge-validation" / "instrument-closure-lane" / "frame.jsonl"

ROW = re.compile(r"^\s{2}(\S+)\s+(\d+)\s+(A|B|C|D)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s*$")
FAMILIES = list(range(1, 9))
E2_FAMILIES = (2, 3, 4, 6)
FRESH_FAMILY_OF = {"fb2": 2, "fb3": 3, "fb4": 4, "fb6": 6}
CORE_CONDITIONS = ("A", "B", "C", "D", "B_filler", "B_scaffolded")
FRESH_CONDITIONS = ("C", "D")

SUBJECTS = (  # model_id, measured key (None = DeepSeek max-projection), note
    ("claude-sonnet-5", "claude-sonnet-5", "measured"),
    ("gpt-5.6-terra", "gpt-5.6-terra", "measured"),
    ("deepseek-v4-pro", None, "projected from the maximum of the two measured API subjects"),
    ("qwen3.8-27b", "qwen3.8-27b", "local, no API charge (R17)"),
)
FREE_SUBJECTS = {"qwen3.8-27b", "muse-glimmer-30b", "gemma4-31b-it"}

# Judge-pass measured rates (unchanged committed provenance: the 360-run development corpus).
JUDGE_CANDIDATES_PER_RUN = 528 / 360
JUDGE_AWARENESS_PER_RUN = 1.0
JUDGE_PROMPT_TOKENS = 900
JUDGE_OUTPUT_TOKENS = 8
SECONDARY_INPUT_TOKENS = 1042      # lane-measured mean
SECONDARY_OUTPUT_EXPECTED = 261    # lane-measured mean (thinking model, real behaviour)
SECONDARY_MAX_TOKENS = 8192        # reservation bound
STOP_SHAPED_CALLS_PER_RUN = 864 / 1920
CLASSIFIER_PROMPT_TOKENS = 1800    # deliberate over-estimate kept from the committed projection
CLASSIFIER_OUTPUT_TOKENS = 8
B_SCAFFOLDED_EXTRA_INPUT_PER_RUN = 3800  # stated over-estimate of the measured word delta (505-222
# words, DERIVATION_RECORD.md) times per-run model calls. The over-estimate is the frozen price: the
# study venv carries no tokeniser, and the three API subjects tokenise differently with no offline
# Anthropic tokeniser in existence, so any single measurement would be a GPT-family proxy standing in
# for three. The error runs against the budget; the whole constant is worth 1.62 USD of this
# script's 240.99 USD projection.


def load_config_prices() -> dict[str, dict[str, float]]:
    prices: dict[str, dict[str, float]] = {}
    current: str | None = None
    in_prices = False
    for line in (STAGE1 / "config_recorded.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("prices:"):
            in_prices = True
            continue
        if in_prices and line and not line.startswith(" "):
            break
        if not in_prices or not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^  \S+:\s*$", line):
            current = line.strip().rstrip(":")
            prices[current] = {}
        elif current and ":" in line:
            key, _, value = line.strip().partition(":")
            value = value.split("#")[0].strip()
            try:
                prices[current][key] = float(value)
            except ValueError:
                pass
    return prices


def load_plan_expect(name: str) -> dict:
    text = (STAGE1 / name).read_text(encoding="utf-8")
    expect: dict = {"per_subject_condition": {}, "per_condition": {}, "per_scenario": {}}
    section = None
    for line in text.splitlines():
        if line.startswith("cells:"):
            break
        stripped = line.strip()
        if stripped.startswith("total:"):
            expect["total"] = int(stripped.split(":")[1])
        for flat in ("per_condition", "per_repeat"):
            if stripped.startswith(flat + ": {"):
                body = stripped.split("{", 1)[1].rstrip("}")
                expect[flat] = {k.strip(): int(v) for k, v in
                                (item.split(":") for item in body.split(","))}
        if stripped in ("per_subject:", "per_subject_condition:", "per_scenario:"):
            section = stripped.rstrip(":")
            expect.setdefault(section, {})
            continue
        if section and re.match(r"^\S.*:", stripped) and not line.startswith("      ") \
                and line.startswith("    "):
            key, _, value = stripped.partition(":")
            try:
                expect[section][key.strip()] = int(value)
            except ValueError:
                section = None
        elif not line.startswith("    "):
            section = None
    return expect


def measured_cells() -> dict[tuple[str, int, str], dict[str, float]]:
    cells: dict[tuple[str, int, str], dict[str, float]] = {}
    for line in MEASURED.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        model, family, condition, tin, tout, cread, cwrite, stops, per_run = match.groups()
        cells[(model, int(family), condition)] = {
            "input": float(tin), "output": float(tout), "cache_read": float(cread),
            "cache_write": float(cwrite), "stops": float(stops)}
    return cells


def cost_of(profile: dict[str, float], price: dict[str, float]) -> float:
    total = profile["input"] * price.get("input_per_mtok", 0.0)
    total += profile["output"] * price.get("output_per_mtok", 0.0)
    total += profile["cache_read"] * price.get("cache_read_per_mtok", 0.0)
    total += profile["cache_write"] * price.get("cache_write_per_mtok", 0.0)
    return total / 1_000_000.0


def profile_for(cells, model: str, family: int, condition: str) -> tuple[dict[str, float], bool]:
    direct = cells.get((model, family, condition))
    if direct:
        return direct, True
    same_condition = [value for (m, _, c), value in cells.items() if m == model and c == condition]
    if not same_condition:
        raise SystemExit(f"no measurement at all for {model} in condition {condition}")
    mean = {key: sum(item[key] for item in same_condition) / len(same_condition)
            for key in ("input", "output", "cache_read", "cache_write", "stops")}
    return mean, False


def subject_cell_cost(cells, prices, subject: str, measured_key: str | None,
                      family: int, condition: str) -> tuple[float, bool]:
    price = prices.get(subject, {})
    base_condition = "B" if condition in ("B_filler", "B_scaffolded") else condition
    if measured_key is None:
        profiles = [profile_for(cells, donor, family, base_condition)[0]
                    for donor in ("claude-sonnet-5", "gpt-5.6-terra")]
        profile = {key: max(item[key] for item in profiles) for key in profiles[0]}
        exact = False
    else:
        profile, exact = profile_for(cells, measured_key, family, base_condition)
    per_run = cost_of(profile, price)
    if condition == "B_scaffolded":
        per_run += B_SCAFFOLDED_EXTRA_INPUT_PER_RUN * price.get("input_per_mtok", 0.0) / 1_000_000.0
    return per_run, exact


def frame_prose_rates() -> dict[str, float]:
    """E2-family pre-gate prose turns per run, by condition, from the committed lane frame."""
    runs: dict[str, set] = {}
    prose: dict[str, int] = {}
    for line in FRAME.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["family"] not in E2_FAMILIES:
            continue
        runs.setdefault(row["condition"], set()).add(row["run_id"])
        if row["channel"] == "prose":
            prose[row["condition"]] = prose.get(row["condition"], 0) + 1
    rates = {condition: prose.get(condition, 0) / len(ids) for condition, ids in runs.items()}
    rates["B_scaffolded"] = rates["B_filler"]  # stated proxy: the arm did not exist at frame time
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="also write the projection as JSON")
    args = parser.parse_args()

    prices = load_config_prices()
    cells = measured_cells()
    instrument_prices = json.loads(INSTRUMENT_PRICES.read_text(encoding="utf-8"))["prices"]
    for required in ("mistral-medium-2604", "minimax/minimax-m3"):
        if required not in instrument_prices:
            raise SystemExit(f"instrument price missing: {required}")

    core = load_plan_expect("plan_recorded.yaml")
    fresh = load_plan_expect("plan_fresh_recorded.yaml")
    fresh_local = load_plan_expect("plan_fresh_local_recorded.yaml")
    family9 = load_plan_expect("plan_family9_recorded.yaml")

    lines = ["Recorded-package projection, brief step 6 (2026-08-25)", "=" * 72, "",
             f"Plans: plan_recorded.yaml ({core['total']}), plan_fresh_recorded.yaml "
             f"({fresh['total']}), plan_fresh_local_recorded.yaml ({fresh_local['total']}), "
             f"plan_family9_recorded.yaml ({family9['total']})",
             f"Measured source: {MEASURED.relative_to(REPO)}",
             "Families 3, 4 and 6 were never rehearsed; their cells are projected from the mean of",
             "the measured families for the same subject and condition, and are marked (proj).",
             "B_filler and B_scaffolded price at the measured condition-B profile; B_scaffolded",
             f"adds {B_SCAFFOLDED_EXTRA_INPUT_PER_RUN:,} uncached input tokens per run for its longer prompt.", ""]

    totals: dict[str, float] = {}
    projected_share = 0.0

    # --- core plan (core conditions + the two prose controls), per subject -------------------
    scenarios_per_family = 5
    core_total = 0.0
    repeat_bearing_total = 0.0  # the A-D three-repeat rows; the R34 repeat rung drops 1/3 of these
    for subject, measured_key, note in SUBJECTS:
        subject_total = 0.0
        subject_projected = 0.0
        for family in FAMILIES:
            for condition in CORE_CONDITIONS:
                runs_here = core["per_subject_condition"].get(f"{subject}/{condition}", 0)
                if runs_here == 0:
                    continue
                # runs are balanced across the 40 scenarios: runs_here/40 per scenario, x5 per family
                family_runs = runs_here * scenarios_per_family / 40.0
                per_run, exact = subject_cell_cost(cells, prices, subject, measured_key,
                                                   family, condition)
                if subject in FREE_SUBJECTS:
                    per_run = 0.0
                subject_total += per_run * family_runs
                if condition in ("A", "B", "C", "D"):
                    repeat_bearing_total += per_run * family_runs
                if not exact and subject not in FREE_SUBJECTS:
                    subject_projected += per_run * family_runs
        totals[f"core+controls:{subject}"] = subject_total
        core_total += subject_total
        projected_share += subject_projected
        lines.append(f"  core+controls {subject:20} {subject_total:9.2f} USD   ({note})")

    # --- fresh Part B primary (C, D only; family profile restricted to the fresh families) ---
    fresh_total = 0.0
    fresh_scenarios_per_family = 10
    for subject, measured_key, note in SUBJECTS:
        subject_total = 0.0
        for prefix, family in FRESH_FAMILY_OF.items():
            for condition in FRESH_CONDITIONS:
                runs_here = fresh["per_subject_condition"].get(f"{subject}/{condition}", 0)
                family_runs = runs_here * fresh_scenarios_per_family / 40.0
                per_run, exact = subject_cell_cost(cells, prices, subject, measured_key,
                                                   family, condition)
                if subject in FREE_SUBJECTS:
                    per_run = 0.0
                subject_total += per_run * family_runs
                if not exact and subject not in FREE_SUBJECTS:
                    projected_share += per_run * family_runs
        totals[f"fresh:{subject}"] = subject_total
        fresh_total += subject_total
        lines.append(f"  fresh         {subject:20} {subject_total:9.2f} USD")
    lines.append(f"  fresh local arms (R46)             {0.0:9.2f} USD   ({fresh_local['total']} runs, local endpoints)")
    lines.append(f"  family 9      {'local subject only':20} {0.0:9.2f} USD   ({family9['total']} runs)")

    # --- instruments under branch 3 ----------------------------------------------------------
    rates = frame_prose_rates()
    mistral = instrument_prices["mistral-medium-2604"]
    minimax = instrument_prices["minimax/minimax-m3"]

    # every-pre-gate-prose-turn routing, E2 families only (20 of 40 scenarios = half the rows)
    invariant_calls = 0.0
    for condition, per_condition_runs in core["per_condition"].items():
        e2_share_runs = per_condition_runs / 2.0
        invariant_calls += e2_share_runs * rates[condition]
    stop_shaped_rows = (core["total"] / 2.0) + family9["total"]  # non-E2 core rows + family 9
    stop_shaped_calls = stop_shaped_rows * STOP_SHAPED_CALLS_PER_RUN
    classifier_calls = invariant_calls + stop_shaped_calls
    classifier_cost = classifier_calls * (
        CLASSIFIER_PROMPT_TOKENS * mistral["input_per_mtok"]
        + CLASSIFIER_OUTPUT_TOKENS * mistral["output_per_mtok"]) / 1_000_000.0
    totals["route_classifier"] = classifier_cost

    judged_rows = core["total"] + family9["total"]          # the fresh component is never judged
    subject_billed_rows = sum(
        count for plan in (core, fresh)
        for subject, count in plan["per_subject"].items()
        if subject not in FREE_SUBJECTS
    )
    instrument_billed_rows = judged_rows
    fully_free_rows = (fresh_local["total"]
                       + sum(count for subject, count in fresh["per_subject"].items()
                             if subject in FREE_SUBJECTS))
    judge_calls = judged_rows * (JUDGE_CANDIDATES_PER_RUN + JUDGE_AWARENESS_PER_RUN)
    primary_cost = judge_calls * (
        JUDGE_PROMPT_TOKENS * mistral["input_per_mtok"]
        + JUDGE_OUTPUT_TOKENS * mistral["output_per_mtok"]) / 1_000_000.0
    secondary_expected = judge_calls * (
        SECONDARY_INPUT_TOKENS * minimax["input_per_mtok"]
        + SECONDARY_OUTPUT_EXPECTED * minimax["output_per_mtok"]) / 1_000_000.0
    secondary_reserved = judge_calls * (
        SECONDARY_INPUT_TOKENS * minimax["input_per_mtok"]
        + SECONDARY_MAX_TOKENS * minimax["output_per_mtok"]) / 1_000_000.0
    totals["judge_primary"] = primary_cost
    totals["judge_secondary_expected"] = secondary_expected

    mistral_spend = classifier_cost + primary_cost
    lines += ["",
              "  instruments (branch 3: judged rows = core + controls + family 9; fresh = zero calls):",
              f"    condition-invariant routing  {invariant_calls:8,.0f} calls  (E2-family rows x measured per-condition prose-turn rates)",
              f"    stop-shaped routing          {stop_shaped_calls:8,.0f} calls  (non-E2 rows at the measured 864/1,920 rate)",
              f"    route classifier total       {classifier_calls:8,.0f} calls {classifier_cost:9.2f} USD",
              f"    primary judge (descriptive)  {judge_calls:8,.0f} calls {primary_cost:9.2f} USD",
              f"    secondary judge              {judge_calls:8,.0f} calls {secondary_expected:9.2f} USD expected"
              f" ({secondary_reserved:.2f} USD if every answer runs to its 8,192-token cap)",
              f"    total mistral-medium-2604 spend: {mistral_spend:.2f} USD"
              " (auto-billing enabled by Grant 2026-08-25, R52; the step-9 smoke verifies the billing path)"]

    expected = core_total + fresh_total + classifier_cost + primary_cost + secondary_expected
    worst = expected - secondary_expected + secondary_reserved
    api_runs = core["total"] + fresh["total"]
    all_rows = api_runs + fresh_local["total"] + family9["total"]
    lines += ["",
              f"  Expected total   {all_rows:,} recorded rows ({api_runs + family9['total']:,} rows in the three main plans) {expected:9.2f} USD",
              f"  Worst case (secondary judge at cap)                    {worst:9.2f} USD",
              "",
              f"  Projected (unmeasured-family) share of the subject figure: {projected_share:.2f} USD",
              "  Direction of that uncertainty unknown; the 600 USD ceiling and the 300/450",
              "  checkpoints exist for exactly this. Fresh-component cells are priced from the",
              "  matching development families' C/D profiles; fresh fixtures are smaller than",
              "  several development fixtures, so this leans conservative.",
              "",
              "  Drop ladder (R34 as amended by R43; scenarios are never dropped; the fresh C-D",
              "  component is never dropped):",
              f"    full package                          {expected:8.2f} expected / {worst:8.2f} worst",
              "    1. drop the frontier replication      (optional extra, not in this projection;",
              "       it runs only if the package completes within budget, so this rung frees",
              "       nothing here)",
              f"    2. core repeats 3 -> 2 at a tranche boundary  saves about {repeat_bearing_total/3.0:8.2f} USD of subjects"
              f" -> {expected - repeat_bearing_total/3.0:8.2f} expected"]

    output = "\n".join(lines) + "\n"
    print(output)
    if args.json:
        payload = {"totals": {k: round(v, 4) for k, v in totals.items()},
                   "expected_usd": round(expected, 2), "worst_case_usd": round(worst, 2),
                   "classifier_calls": round(classifier_calls), "judge_calls": round(judge_calls),
                   "mistral_spend_usd": round(mistral_spend, 2),
                   "recorded_rows": all_rows,
                   "subject_billed_rows": subject_billed_rows,
                   "instrument_billed_rows": instrument_billed_rows,
                   "fully_free_rows": fully_free_rows,
                   "prose_turn_rates": {k: round(v, 3) for k, v in rates.items()}}
        Path(args.json).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                                   encoding="utf-8")


if __name__ == "__main__":
    main()
