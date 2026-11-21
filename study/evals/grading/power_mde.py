#!/usr/bin/env python3
"""Scenario-cluster minimum detectable effect for the recorded plan (correction phase 2026-08-24).

The preregistration draft said, correctly, that no power calculation had been performed. The GPT
review (M2) required one before the claims are written, because "sized by budget" is not a sample-size
justification and a null from an underpowered design cannot be reported as evidence of absence.

This is a simulation, not a closed-form calculation, because the confirmatory test is the scenario-
cluster sign-flip test on scenario-paired differences and the clusters are few (20 for E2, 10 for E1).
Structure of one simulated study, matching `plan_recorded.yaml`:

  * K scenario clusters (E2: families 2, 3, 4 and 6 at five variants each = 20; E1: families 5 and 7 = 10)
  * S subjects x R repeats runs per scenario per arm (4 x 3 = 12 in the three-repeat recorded
    core, R43; the Part B fresh component is 4 x 2 = 8 over 40 fresh clusters)
  * a scenario-level random effect drawn so that the between-scenario spread matches what the
    development run actually showed, then a per-run Bernoulli draw inside each scenario
  * the scenario-paired difference and the two-sided sign-flip p value, as `analysis.py` computes them.
    The Holm column is a CONSERVATIVE BOUND, not a simulation of the joint procedure: it applies the
    worst-case threshold alpha/2 to a single endpoint rather than simulating both endpoints' p values
    and running Holm across them (Sol review finding 12). The analytic figures below are likewise a
    normal approximation from an estimated between-scenario variance, not exact-test power.

Between-scenario spread is the parameter that matters, and it is taken from the development run
(`results/development/dev-2026-08-23`): pooled E2 rates by condition of about B 0.55 and C 0.75 with
scenario-level rates ranging across the whole interval, which a Beta with concentration 4 reproduces.
The concentration is a deliberate choice and the script reports power at three values so the reader can
see how sensitive the answer is to it.

Usage: python3 power_mde.py [--iterations 2000] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import hashlib
import random
import statistics
from pathlib import Path

SIGN_FLIP_DRAWS = 2000          # the analysis uses 20,000; 2,000 is enough inside a power loop
ALPHA = 0.05
HOLM_FAMILY = 2                 # E1 and E2


def sign_flip_p(differences: list[float], rng: random.Random, draws: int = SIGN_FLIP_DRAWS) -> float:
    """Two-sided sign-flip test on scenario-paired differences (analysis.sign_flip_p, in miniature)."""
    values = [value for value in differences if value is not None]
    if not values:
        return 1.0
    observed = abs(sum(values) / len(values))
    hits = 0
    for _ in range(draws):
        flipped = sum(value if rng.random() < 0.5 else -value for value in values) / len(values)
        if abs(flipped) >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (draws + 1)


def one_study(clusters: int, runs_per_arm: int, base_rate: float, effect: float,
              concentration: float, rng: random.Random) -> list[float]:
    """Simulate one study and return its scenario-paired differences."""
    differences = []
    for _ in range(clusters):
        # A scenario's own difficulty, shared by both arms: the paired design removes it from the
        # contrast, which is why the paired difference is the right estimand for few clusters.
        alpha = base_rate * concentration
        beta = (1 - base_rate) * concentration
        scenario_base = min(0.995, max(0.005, rng.betavariate(alpha, beta)))
        scenario_treated = min(0.995, max(0.005, scenario_base + effect))
        b_hits = sum(1 for _ in range(runs_per_arm) if rng.random() < scenario_base)
        c_hits = sum(1 for _ in range(runs_per_arm) if rng.random() < scenario_treated)
        differences.append(c_hits / runs_per_arm - b_hits / runs_per_arm)
    return differences


def power_at(effect: float, clusters: int, runs_per_arm: int, base_rate: float,
             concentration: float, iterations: int, seed: int,
             holm_family: int | None = HOLM_FAMILY) -> dict[str, float]:
    rng = random.Random(seed)
    rejections = 0
    holm_rejections = 0
    estimates = []
    for _ in range(iterations):
        differences = one_study(clusters, runs_per_arm, base_rate, effect, concentration, rng)
        estimates.append(sum(differences) / len(differences))
        p = sign_flip_p(differences, rng)
        if p <= ALPHA:
            rejections += 1
        # The superseded pre-branch-3 Holm bracket: the worst case for this endpoint is that the
        # other endpoint's p value is larger, so it is tested at alpha / family. Not computed for
        # Part B, which was never in that family (Grok step-6 confirm, residual 2).
        if holm_family and p <= ALPHA / holm_family:
            holm_rejections += 1
    return {"effect": effect, "power_unadjusted": rejections / iterations,
            "power_holm_worst_case_superseded": (holm_rejections / iterations
                                                 if holm_family else None),
            "mean_estimate": statistics.fmean(estimates),
            "estimate_sd": statistics.pstdev(estimates)}


def variance_decomposition_mde(artifact_path: Path | None = None) -> list[dict[str, object]]:
    """The analytic MDE from the development run's own between-scenario variance.

    Added in the correction phase's second pass (2026-08-24, independent methodologist sweep, finding
    4), which pointed out that a simulation's answer depends on an assumed between-scenario spread
    while the development run measured one. This is the number the registration quotes, because it is
    the conservative one and it does not depend on a shape assumption.

    Method: the development run gives the standard deviation of the per-scenario paired C minus B
    difference at 2 runs per scenario-condition cell. That variance is the sum of a between-scenario
    component and a within component that shrinks as 2/n_cell; decompose it, then recompute the
    standard error at the recorded plan's 16 runs per cell. The MDE at 80 percent power is
    (z_{1-alpha/2} + z_{0.8}) x SE, which is 2.80 x SE at alpha 0.05 and 3.04 x SE at the
    Holm-protected 0.025.
    """
    root = artifact_path or (Path(__file__).resolve().parents[2]
                             / "results" / "development" / "dev-2026-08-23" / "analysis" / "analysis.json")
    if not root.exists():
        return []
    artifact = json.loads(root.read_text(encoding="utf-8"))
    rows = []
    for endpoint, clusters, development_cell_runs, recorded_cell_runs, rates, status in (
        # R43 three-repeat core: 4 subjects x 3 repeats = 12 runs per scenario-condition cell.
        # Branch 3 (R47): E1 is the core's sole confirmatory endpoint, tested at plain alpha
        # (a Holm family of one); E2 is descriptive only, its precision reported for honesty
        # about what a descriptive null can and cannot say.
        ("appropriate_intervention_before_first_consequential_action", 20, 2, 12, (0.55, 0.75),
         "descriptive only under branch 3 (R47)"),
        ("false_success_claim", 10, 2, 12, (0.40, 0.10),
         "core confirmatory endpoint; Holm family of one under branch 3, plain alpha applies"),
        # Part B fresh component: 40 clusters x (4 subjects x 2 repeats) = 8 runs per cell, C-D.
        # No fresh scenario has ever been run, so no measured between-scenario variance exists for
        # them; the between component is BORROWED from the development E2 measurement (stated in
        # the output) and the within component uses worst-case p(1-p) = 0.25 in both arms. Its own
        # single-test family: two-sided plain alpha, no Holm (PILOT_PROTOCOL section 8).
        ("part_b_scenario_concordant_structured_intervention_before_gate", 40, 2, 8, (0.50, 0.50),
         "Part B confirmatory endpoint; own family, two-sided plain alpha; between-scenario "
         "variance = the development E2 measurement's own decomposed between component "
         "(donor rates 0.55/0.75 at the development cell size), with worst-case p(1-p) within "
         "at the recorded 8 runs per cell"),
    ):
        borrowed = endpoint.startswith("part_b_")
        source_endpoint = ("appropriate_intervention_before_first_consequential_action"
                           if borrowed else endpoint)
        paired = next((row for row in artifact.get("direction_consistency", [])
                       if row.get("endpoint") == source_endpoint and row.get("denominator") == "all_attempts"), None)
        differences = [item["difference"] for item in (paired or {}).get("scenario_paired_differences", [])
                       if item.get("difference") is not None]
        if len(differences) < 3:
            continue
        observed_sd = statistics.pstdev(differences)
        base, treated = rates
        if borrowed:
            # The borrowed quantity is the DONOR's between-scenario variance: decompose the donor's
            # observed paired SD under the donor's own development rates (Grok step-6 review,
            # finding 3 — re-decomposing under Part B's worst-case within shrinks the between
            # component, which is the anti-conservative direction for the principal test).
            donor_base, donor_treated = 0.55, 0.75
            donor_within = (donor_base * (1 - donor_base)
                            + donor_treated * (1 - donor_treated)) / development_cell_runs
            between = max(0.0, observed_sd ** 2 - donor_within)
        else:
            within = (base * (1 - base) + treated * (1 - treated)) / development_cell_runs
            between = max(0.0, observed_sd ** 2 - within)
        recorded_within = (base * (1 - base) + treated * (1 - treated)) / recorded_cell_runs
        se = math.sqrt((between + recorded_within) / clusters)
        floor_se = math.sqrt(between / clusters) if between else 0.0
        rows.append({
            "endpoint": endpoint, "clusters": clusters,
            "runs_per_cell": recorded_cell_runs,
            "confirmatory_status": status,
            "observed_paired_sd": round(observed_sd, 4),
            "between_scenario_variance": round(between, 4),
            "recorded_se": round(se, 4),
            "mde_80_alpha_05": round(2.80 * se, 3),
            "mde_80_holm_025_superseded": round(3.04 * se, 3),
            "se_floor_infinite_runs": round(floor_se, 4),
            "mde_floor_80": round(2.80 * floor_se, 3),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--json", default=None)
    args = parser.parse_args()

    designs = [
        # name, clusters, runs per scenario per arm, base rate observed in development
        ("E2 (families 2,3,4,6), descriptive under branch 3", 20, 12, 0.55),
        ("E1 (families 5,7), core confirmatory", 10, 12, 0.15),
        ("Part B fresh C-D, 40 clusters, deterministic endpoint", 40, 8, 0.50),
        ("E2 core at the R34 drop rung, repeats 3 to 2", 20, 8, 0.55),
        ("E1 core at the R34 drop rung, repeats 3 to 2", 10, 8, 0.15),
    ]
    effects = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    concentrations = [2.0, 4.0, 8.0]
    report: dict[str, object] = {"alpha": ALPHA,
                                 "holm_family_superseded_pre_branch3": HOLM_FAMILY,
                                 "holm_family_core_branch3": 1,
                                 "holm_family_part_b": 1,
                                 "multiplicity_note": "Branch 3 (R47): the core confirmatory family "
                                 "is E1 alone and Part B is its own single two-sided test, so plain "
                                 "alpha applies to each; the bracketed Holm columns are the "
                                 "superseded pre-branch-3 bound and never applied to Part B, which "
                                 "was never in that family.",
                                 "iterations": args.iterations, "designs": []}
    for name, clusters, runs, base in designs:
        print(f"\n{name}: {clusters} scenario clusters, {runs} runs per scenario per arm, "
              f"base rate {base}")
        print("  effect |" + "".join(f"  power@k={k:<4}" for k in concentrations)
              + "   (Holm worst case in brackets)")
        rows = []
        for effect in effects:
            cells = []
            for concentration in concentrations:
                # A stable seed: Python's hash() is randomised per process, so the simulation was not
                # reproducible across runs (Sol review finding 12).
                digest = hashlib.sha256(f"{name}|{effect}|{concentration}".encode("utf-8")).hexdigest()
                result = power_at(effect, clusters, runs, base, concentration, args.iterations,
                                  seed=int(digest[:8], 16),
                                  holm_family=None if name.startswith("Part B") else HOLM_FAMILY)
                cells.append(result)
            print(f"   {effect:+.2f} |" + "".join(
                f"  {cell['power_unadjusted']:.2f} "
                + ("[n/a]" if cell['power_holm_worst_case_superseded'] is None
                   else f"[{cell['power_holm_worst_case_superseded']:.2f}]")
                for cell in cells))
            rows.append({"effect": effect, "by_concentration": dict(zip(map(str, concentrations), cells))})
        report["designs"].append({"design": name, "clusters": clusters, "runs_per_arm": runs,
                                  "base_rate": base, "rows": rows})
    print("\nRead this as: the smallest effect with power at least 0.80 under the middle spread "
          "(k=4) is the design's minimum detectable effect. Under the branch-3 outcome (R47) the "
          "core has ONE confirmatory endpoint (E1, plain alpha) and Part B is its own single "
          "two-sided test, so the unadjusted column is the number to quote for each; the Holm "
          "worst-case column is retained in brackets as the pre-branch-3 registered bound.")
    print("\nAnalytic MDE from the development run's measured between-scenario variance")
    print("  endpoint                                   clusters cell   SE     MDE(.05)  MDE(Holm,superseded)  floor")
    analytic = variance_decomposition_mde()
    for row in analytic:
        print(f"  {row['endpoint'][:42]:42} {row['clusters']:>5} {row['runs_per_cell']:>4}   {row['recorded_se']:.4f}   "
              f"{row['mde_80_alpha_05']:.3f}     {row['mde_80_holm_025_superseded']:.3f}                 {row['mde_floor_80']:.3f}")
        print(f"      {row['confirmatory_status']}")
    print("  The floor is what infinite repeats and subjects would buy: precision is capped by the")
    print("  number of scenario clusters, so more runs cannot go below it. This is the registered number.")
    report["analytic_mde"] = analytic
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=1)
            handle.write("\n")


if __name__ == "__main__":
    main()
