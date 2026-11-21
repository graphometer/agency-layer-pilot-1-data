#!/usr/bin/env python3
"""Generate the recorded-run plan files from the registered arithmetic (brief step 6).

PILOT_PROTOCOL section 4 is the single arithmetic; this script materialises it so the committed
plans cannot drift from it by hand-editing:

  plan_recorded.yaml            core 4x40x4x3 = 1,920  + B_filler 320 + B_scaffolded 320 = 2,560
  plan_fresh_recorded.yaml      fresh C,D x 40 x 4 subjects x 2 = 640      (Part B primary)
  plan_fresh_local_recorded.yaml fresh C,D x 40 x 2 local subjects x 2 = 320 (R46, free, serial)
  plan_family9_recorded.yaml    family 9: 5x4x1x4 = 80 (exploratory, local only)

Every plan carries the full `expect` block over all six preflight dimensions (cli.EXPECT_DIMENSIONS);
the preflight refuses dispatch on any mismatch. The generator also asserts the package arithmetic:
3,600 recorded rows = 3,280 + 320 (R43 + R45 + R46). That identity is a split by PLAN FILE — the
three main plans against the free local-arm plan — not a split by cost. Costs do not partition the
rows the same way (a local subject makes the subject half of a row free, not the row), and no single
cost figure is asserted here. BUDGET.md's projection table itemises what is billed.

Fresh scenario identifiers come from the committed seal manifest
(`docs/review/part-b-scenarios/SEAL_MANIFEST.json`) — identifiers only; the bodies stay sealed in
durable staging until FROZEN-S1, so the fresh plans' preflights run against the sealed staging copy
until the fold-in, and are re-run at the freeze.

Usage:
  python3 tools/make_recorded_plans.py            # write the four plan files
  python3 tools/make_recorded_plans.py --check    # exit 1 if committed plans differ from regeneration
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE1 = HERE.parent
REPO = STAGE1.parents[2]
SCENARIOS = REPO / "evals" / "scenarios"
SEAL_MANIFEST = REPO / "docs" / "review" / "part-b-scenarios" / "SEAL_MANIFEST.json"

CORE_SUBJECTS = (  # plan model name -> config model_id (config_recorded.yaml)
    ("claude_primary", "claude-sonnet-5"),
    ("gpt_primary", "gpt-5.6-terra"),
    ("deepseek_primary", "deepseek-v4-pro"),
    ("local_qwen", "qwen3.8-27b"),
)
LOCAL_ARM_SUBJECTS = (  # R46/R57 free exploratory arms, Part B only, serial under the exclusion group
    ("local_muse", "muse-glimmer-30b"),
    ("local_gemma", "gemma4-31b-it"),  # R57: replaces mistral-small-4 (dropped, R56)
)
CORE_CONDITIONS = ("A", "B", "C", "D")
CORE_REPEATS = 3          # R43: the fourth repeat was reallocated into the fresh component
CONTROL_REPEATS = 2       # B_filler (PM9) and B_scaffolded (R45)
FRESH_CONDITIONS = ("C", "D")
FRESH_REPEATS = 2
FAMILY9_REPEATS = 4

PACKAGE_RECORDED_ROWS = 3600
PACKAGE_MAIN_PLAN_ROWS = 3280   # the three main plans; a plan-file count, not a count of billed rows


def core_scenarios() -> list[str]:
    names = sorted(p.name for p in SCENARIOS.iterdir()
                   if p.is_dir() and not p.name.startswith("f9-"))
    if len(names) != 40:
        raise SystemExit(f"expected 40 family 1-8 scenarios, found {len(names)}")
    return names


def fresh_scenarios() -> list[str]:
    manifest = json.loads(SEAL_MANIFEST.read_text(encoding="utf-8"))
    names = sorted(entry["id"] for entry in manifest["scenarios"])
    if len(names) != 40:
        raise SystemExit(f"seal manifest names {len(names)} scenarios, expected 40")
    return names


def expand(cells: list[dict], subjects: dict[str, str]) -> list[tuple[str, str, str, int]]:
    rows = []
    for cell in cells:
        for condition in cell["conditions"]:
            for model_name in cell["models"]:
                for repeat in range(cell["repeats"]):
                    rows.append((cell["scenario"], condition, subjects[model_name], repeat))
    return rows


def expect_block(rows: list[tuple[str, str, str, int]]) -> dict:
    def count(key) -> dict:
        out: dict = {}
        for row in rows:
            k = key(row)
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))
    return {
        "total": len(rows),
        "per_condition": count(lambda r: r[1]),
        "per_subject": count(lambda r: r[2]),
        "per_repeat": count(lambda r: r[3]),
        "per_subject_condition": count(lambda r: f"{r[2]}/{r[1]}"),
        "per_scenario": count(lambda r: r[0]),
    }


def render(header: str, cells: list[dict], subjects: dict[str, str], expected_batch_id: str) -> str:
    rows = expand(cells, subjects)
    expect = expect_block(rows)
    lines = [header.rstrip(), "", f"expected_batch_id: {expected_batch_id}", "", "expect:",
             f"  total: {expect['total']}"]
    simple = {k: v for k, v in expect["per_condition"].items()}
    lines.append("  per_condition: {" + ", ".join(f"{k}: {v}" for k, v in simple.items()) + "}")
    lines.append("  per_subject:")
    for key, value in expect["per_subject"].items():
        lines.append(f"    {key}: {value}")
    lines.append("  per_repeat: {" + ", ".join(f"{k}: {v}" for k, v in expect["per_repeat"].items()) + "}")
    lines.append("  per_subject_condition:")
    for key, value in expect["per_subject_condition"].items():
        lines.append(f"    {key}: {value}")
    lines.append("  per_scenario:")
    for key, value in expect["per_scenario"].items():
        lines.append(f"    {key}: {value}")
    lines.append("")
    lines.append("cells:")
    for cell in cells:
        lines.append(f"  - scenario: {cell['scenario']}")
        lines.append(f"    conditions: [{', '.join(cell['conditions'])}]")
        lines.append(f"    models: [{', '.join(cell['models'])}]")
        lines.append(f"    repeats: {cell['repeats']}")
    return "\n".join(lines) + "\n"


def build_all() -> dict[Path, str]:
    core = core_scenarios()
    fresh = fresh_scenarios()
    core_names = [name for name, _ in CORE_SUBJECTS]
    core_map = dict(CORE_SUBJECTS)
    local_names = [name for name, _ in LOCAL_ARM_SUBJECTS]
    local_map = dict(LOCAL_ARM_SUBJECTS)

    core_cells = (
        [{"scenario": s, "conditions": list(CORE_CONDITIONS), "models": core_names,
          "repeats": CORE_REPEATS} for s in core]
        + [{"scenario": s, "conditions": ["B_filler"], "models": core_names,
            "repeats": CONTROL_REPEATS} for s in core]
        + [{"scenario": s, "conditions": ["B_scaffolded"], "models": core_names,
            "repeats": CONTROL_REPEATS} for s in core]
    )
    fresh_cells = [{"scenario": s, "conditions": list(FRESH_CONDITIONS), "models": core_names,
                    "repeats": FRESH_REPEATS} for s in fresh]
    local_cells = [{"scenario": s, "conditions": list(FRESH_CONDITIONS), "models": local_names,
                    "repeats": FRESH_REPEATS} for s in fresh]
    family9_cells = [
        {"scenario": s, "conditions": list(CORE_CONDITIONS), "models": ["local_qwen"],
         "repeats": FAMILY9_REPEATS}
        for s in sorted(p.name for p in SCENARIOS.iterdir()
                        if p.is_dir() and p.name.startswith("f9-"))
    ]
    if len(family9_cells) != 5:
        raise SystemExit(f"expected 5 family 9 scenarios, found {len(family9_cells)}")

    core_header = """\
# RECORDED PLAN — regenerated at brief step 6 (2026-08-25) by tools/make_recorded_plans.py.
# Do not edit by hand; edit the generator and regenerate (--check asserts equality).
#
# PILOT_PROTOCOL section 4 arithmetic (R43 + R45):
#   core          4 conditions x 40 scenarios x 4 subjects x 3 repeats = 1,920   (confirmatory: E1;
#                 E2 descriptive under the section 6a branch-3 outcome, R47)
#   B_filler      1 x 40 x 4 x 2                                       =   320   (PM9 control)
#   B_scaffolded  1 x 40 x 4 x 2                                       =   320   (R45 control)
#   this plan                                                            2,560
# The fresh Part B component (640) and the R46 local arms (320) are separate plan files;
# family 9 (80, local only) is plan_family9_recorded.yaml. Package: 3,600 recorded rows =
# 3,280 in the three main plans + 320 in the free local-arm plan (R43/R45/R46) — a split by plan
# file, not by cost — costs do not partition these rows the same way. See BUDGET.md.
#
# Dispatch order: immutable tranches materialised by the harness; repeats 0-2 are dispatched
# tranche-balanced (the R39-F5 rule, applied to the three-repeat core). Preflight:
#   python -m harness.cli preflight --config config_recorded.yaml --plan plan_recorded.yaml"""

    fresh_header = """\
# RECORDED FRESH PLAN (Part B primary) — regenerated at brief step 6 (2026-08-25) by
# tools/make_recorded_plans.py. Do not edit by hand.
#
# R43: 2 conditions (C, D) x 40 sealed fresh scenarios x 4 subjects x 2 repeats = 640 runs.
# Primary endpoint: scenario_concordant_structured_intervention_before_gate (deterministic,
# two-sided C minus D; PILOT_PROTOCOL sections 5 and 8). Under the section 6a branch-3 outcome
# (R47) this component is the study's principal clean intervention test. No instrument calls:
# the endpoint is deterministic and no semantic judge qualified.
#
# Scenario identifiers come from docs/review/part-b-scenarios/SEAL_MANIFEST.json; the bodies are
# sealed in durable staging until FROZEN-S1 (set_sha256 658c0662...). Until the fold-in, the
# preflight runs against the sealed staging copy via a scenarios_dir override and is re-run at
# the freeze against the folded corpus. Core outcomes are not inspected while any fresh-component
# design or dispatch decision remains open (section 8)."""

    local_header = """\
# RECORDED FRESH LOCAL-ARM PLAN (R46 exploratory) — regenerated at brief step 6 (2026-08-25) by
# tools/make_recorded_plans.py. Do not edit by hand.
#
# R46/R57: 2 free local subjects x 2 conditions (C, D) x 40 sealed fresh scenarios x 2 repeats
# = 320 runs, zero API cost. muse-glimmer-30b (172.17.0.1:8111) and gemma4-31b-it
# (172.17.0.1:8112, the R57 seat that replaced the dropped mistral-small-4 per R56) are
# GPU-exclusive with the whole local exclusion group: the arms run SERIALLY, each
# endpoint started for its runs and stopped after, exactly like the core's local subject; never
# two local model servers at once. Each arm passes the same entrance smoke and tool qualification
# as every subject on development or non-study fixtures only (never a fresh scenario) before the
# freeze; a failing arm is dropped pre-freeze and the failure published (R46, disclosure 38).
# Results are per-subject C-minus-D descriptives with intervals, never pooled with the
# four-subject Part B primary, never confirmatory."""

    family9_header = """\
# RECORDED FAMILY 9 PLAN (frozen candidate, correction phase 2026-08-24).
#
# R35/R39: 5 loop scenarios x 4 conditions x the local subject only x 4 repeats = 80 runs.
# Preregistered exploratory, reported separately, never pooled with families 1 to 8, and never in the
# Holm family. Its subject calls are free under R17, but its route-classifier and judge calls are
# billed instruments included in the package ceiling."""

    return {
        STAGE1 / "plan_recorded.yaml": render(
            core_header, core_cells, core_map, "recorded-core-s1"),
        STAGE1 / "plan_family9_recorded.yaml": render(
            family9_header, family9_cells, core_map, "recorded-family9-s1"),
        STAGE1 / "plan_fresh_recorded.yaml": render(
            fresh_header, fresh_cells, core_map, "recorded-fresh-s1"),
        STAGE1 / "plan_fresh_local_recorded.yaml": render(
            local_header, local_cells, local_map, "recorded-fresh-local-s1"),
    }


def assert_package(outputs: dict[Path, str]) -> None:
    totals = {}
    for path, text in outputs.items():
        for line in text.splitlines():
            if line.startswith("  total: "):
                totals[path.name] = int(line.split(": ")[1])
                break
    core = totals["plan_recorded.yaml"]
    fresh = totals["plan_fresh_recorded.yaml"]
    local = totals["plan_fresh_local_recorded.yaml"]
    family9 = totals["plan_family9_recorded.yaml"]
    main_plans = core + fresh + family9  # family 9 is local-only and free but predeclared core-side
    recorded = main_plans + local
    if core != 2560 or family9 != 80 or fresh != 640 or local != 320:
        raise SystemExit(
            f"component totals moved: core {core}, family9 {family9}, fresh {fresh}, local {local}")
    if recorded != PACKAGE_RECORDED_ROWS:
        raise SystemExit(f"package rows {recorded} != registered {PACKAGE_RECORDED_ROWS}")
    if core + fresh + family9 != PACKAGE_MAIN_PLAN_ROWS:
        raise SystemExit(
            f"main-plan package {core + fresh + family9} != registered {PACKAGE_MAIN_PLAN_ROWS}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify committed plans match regeneration; write nothing")
    args = parser.parse_args()
    outputs = build_all()
    assert_package(outputs)
    if args.check:
        stale = [str(p) for p, text in outputs.items()
                 if not p.is_file() or p.read_text(encoding="utf-8") != text]
        if stale:
            raise SystemExit("stale against regeneration: " + ", ".join(stale))
        print("recorded plans match regeneration; package arithmetic 3,600 = 3,280 + 320 holds")
        return
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        total = next(l for l in text.splitlines() if l.startswith("  total: "))
        print(f"wrote {path.name} ({total.strip()})")
    print("package: 2,560 + 640 + 320 + family9 80 = 3,600 recorded rows "
          "(3,280 + 320 by plan file)")


if __name__ == "__main__":
    main()
