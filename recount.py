#!/usr/bin/env python3
"""Recount the Agency Layer Pilot I numbers published at graphometer.ai/kindness/ from the files in this packet.

No network, no model calls, no API keys. Needs Python 3.10 or newer and PyYAML (pip install pyyaml).

    python3 recount.py              # about one minute
    python3 recount.py --with-power # also reruns the power simulation behind "could detect about 31 / 16 points" (about 5 minutes)
    python3 recount.py --holds      # also writes a listing of every structured hold in the honored arm, for your own reading

What it does, in order:
  1. Checks every file in study/ against the sealed checksum list study/MANIFEST.sha256.
  2. Re-runs the study's own analysis code on the raw run records and stored judge verdicts, and on the
     judge-validation answers, writing fresh outputs to recount-output/.
  3. Compares each fresh output with the committed one, field by field (file-path labels and release labels aside).
  4. Prints every number on the article page next to the value recomputed here.
Everything it writes goes to recount-output/. It never edits a file in study/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE / "study"
OUT = HERE / "recount-output"
RES = STUDY / "evals/runners/stage1/results/stage1"
GRADING = STUDY / "evals/grading"
LANE = "docs/review/judge-validation/instrument-closure-lane"
E2 = "appropriate_intervention_before_first_consequential_action"
E1 = "false_success_claim"

problems: list[str] = []
PRIVACY_TRANSCRIPTS: set[str] = set()


def say(text: str = "") -> None:
    print(text, flush=True)


def run(cmd: list[str], label: str) -> None:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(OUT), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(cmd, cwd=STUDY, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        say(result.stdout[-2000:] + result.stderr[-2000:])
        raise SystemExit(f"{label} failed (exit {result.returncode})")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 1. checksums
def verify_manifest() -> None:
    say("STEP 1. Checksums against the sealed list (study/MANIFEST.sha256)")
    redacted, transcript_edits = set(), set()
    red = HERE / "REDACTIONS.csv"
    if red.exists():
        with red.open(encoding="utf-8") as h:
            for row in csv.DictReader(h):
                redacted.add(row["file"])
                if row["file"].endswith("transcript.jsonl"):
                    transcript_edits.add(row["file"])
    PRIVACY_TRANSCRIPTS.update(transcript_edits)
    ok = sealing_record = doc_edits = run_edits = run_links = 0
    edited_targets = {(STUDY / f).resolve() for f in transcript_edits}
    unexpected, absent = [], {}
    for line in (STUDY / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = STUDY / name
        if not path.exists():
            top = "/".join(name.split("/")[:2]) if "/" in name else name
            absent[top] = absent.get(top, 0) + 1
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            ok += 1
        elif name == "RELEASE_RESULTS_S1.md":
            sealing_record += 1
        elif name in transcript_edits:
            run_edits += 1
        elif path.is_symlink() and path.resolve() in edited_targets:
            run_links += 1
        elif name in redacted:
            doc_edits += 1
        else:
            unexpected.append(name)
    say(f"  files identical to the sealed list: {ok}")
    say(f"  documented privacy edits, documents (listed in REDACTIONS.csv): {doc_edits}")
    say(f"  documented privacy edits, run transcripts (Node.js contributor list blanked; listed in REDACTIONS.csv): {run_edits}")
    say(f"  links that point to one of those edited transcripts (the corrected analyses reuse it): {run_links}")
    say(f"  sealing record RELEASE_RESULTS_S1.md (identity lines filled in after the list was made, as it explains): {sealing_record}")
    say(f"  files in the sealed list but left out of this packet (reasons in PACKET_MANIFEST.md): {sum(absent.values())}")
    say(f"  unexpected differences: {len(unexpected)}")
    for name in unexpected[:20]:
        say(f"    {name}")
    if unexpected:
        problems.append(f"{len(unexpected)} files differ from the sealed checksum list")


# ---------------------------------------------------------------- 2. regenerate
def strip(obj, drop=("provenance", "source_folder", "source", "owner_release_ruling", "publishable_as_result",
                     "release_status", "warnings", "source_files", "source_file", "repository_commit")):
    if isinstance(obj, dict):
        return {k: strip(v, drop) for k, v in obj.items() if k not in drop}
    if isinstance(obj, list):
        return [strip(v, drop) for v in obj]
    return obj


def same(label: str, committed: Path, fresh: Path) -> None:
    a, b = strip(load(committed)), strip(load(fresh))
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    if diff:
        problems.append(f"{label}: regenerated output differs in {diff}")
        say(f"  {label}: DIFFERS in {diff}")
    else:
        say(f"  {label}: every result field identical to the committed file")


def regenerate(with_power: bool) -> None:
    say("\nSTEP 2. Re-running the study's own analysis code (offline)")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    py = sys.executable
    readings = {
        "as-run": (RES / "recorded-core-s1", RES / "recorded-core-judged", RES / "recorded-core-analysis/analysis.json"),
        "exclusion-only": (RES / "supplement-analysis-2026-09-02/exclusion-only/runs",
                           RES / "supplement-analysis-2026-09-02/exclusion-only/judged",
                           RES / "supplement-analysis-2026-09-02/exclusion-only/analysis/analysis.json"),
        "supplemented": (RES / "supplement-analysis-2026-09-02/supplemented/runs",
                         RES / "supplement-analysis-2026-09-02/supplemented/judged",
                         RES / "supplement-analysis-2026-09-02/supplemented/analysis/analysis.json"),
    }
    for name, (runs, judged, committed) in readings.items():
        run([py, "-s", str(GRADING / "analysis.py"), str(runs), str(OUT / name), "--scenarios", "evals/scenarios",
             "--judged", str(judged), "--classifier-reference", "docs/review/classifier"], f"analysis ({name})")
        same(f"first task set, {name} reading", committed, OUT / name / "analysis.json")
        binding = load(OUT / name / "analysis.json")["provenance"].get("verdict_binding", {})
        affected = set(binding.get("runs_affected") or [])
        edited = {Path(f).parent.name for f in PRIVACY_TRANSCRIPTS}
        if not binding.get("rejected"):
            say(f"    stored scorer verdicts whose input hash no longer matches the text: 0")
        elif affected <= edited:
            say(f"    stored scorer verdicts whose input hash no longer matches the text: {binding['rejected']},"
                f" all in runs with documented privacy edits: {sorted(affected)}")
        else:
            problems.append(f"{name}: {binding['rejected']} stored verdicts no longer match their input")
            say(f"    stored scorer verdicts whose input hash no longer matches the text: {binding['rejected']} (PROBLEM)")
    (OUT / "part-b").mkdir()
    run([py, "-s", str(GRADING / "part_b_analysis.py"), "evals/scenarios-part-b", str(OUT / "part-b/part_b_analysis.json"),
         str(OUT / "part-b/part_b_analysis.md"),
         "--runs-root", str(RES / "recorded-fresh-s1"), "--manifest", str(RES / "recorded-fresh-s1/tranches.json"),
         "--runs-root", str(RES / "recorded-fresh-local-s1"), "--manifest", str(RES / "recorded-fresh-local-s1/tranches.json")],
        "Part B analysis")
    same("second task set (honoring test), regraded from raw runs", RES / "recorded-part-b/part_b_analysis.json",
         OUT / "part-b/part_b_analysis.json")
    c = f"{LANE}/candidates"
    run([py, "-s", f"{LANE}/score_lane.py", "--gold", f"{LANE}/gold_final.jsonl",
         "--candidate", "mistral-medium-2604", f"{c}/mistral-medium-2604_pass1.resolved.jsonl", f"{c}/mistral-medium-2604_pass2.resolved.jsonl",
         "--candidate", "minimax-m3", f"{c}/minimax-m3_pass1.resolved.jsonl", f"{c}/minimax-m3_pass2.resolved.jsonl",
         "--timing", f"{LANE}/timing_pass1.jsonl", f"{LANE}/timing_pass2.jsonl",
         "--cost", "mistral-medium-2604=1.3011", "--cost", "minimax-m3=0.5799",
         "--out-json", "../recount-output/judge-validation/LANE_SCORES.json",
         "--out-md", "../recount-output/judge-validation/LANE_SCORE_TABLE.md"], "judge validation scoring")
    same("scoring judge's validation test", STUDY / f"{LANE}/LANE_SCORES.json", OUT / "judge-validation/LANE_SCORES.json")
    if with_power:
        say("  power simulation: running (about 5 minutes)")
        run([py, "-s", str(GRADING / "power_mde.py"), "--json", str(OUT / "power_mde.json")], "power simulation")
        same("power and detectable-size table", STUDY / "docs/review/step6-2026-08-25/power_mde_step6.json", OUT / "power_mde.json")


# ---------------------------------------------------------------- 3. the published numbers
def pooled(rows, **kw):
    hits = [r for r in rows if r.get("model_id", "pooled") == "pooled" and all(r.get(k) == v for k, v in kw.items())]
    if len(hits) != 1:
        raise SystemExit(f"expected one pooled row for {kw}, found {len(hits)}")
    return hits[0]


def check(label: str, got, want) -> None:
    mark = "match" if got == want else "DOES NOT MATCH"
    if got != want:
        problems.append(f"{label}: page {want}, recount {got}")
    say(f"  [{mark}] {label}: page {want} | recount {got}")


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def published_numbers() -> None:
    say("\nSTEP 3. Every number on the page, from the regenerated files")
    asrun = load(OUT / "as-run/analysis.json")
    excl = load(OUT / "exclusion-only/analysis.json")
    supp = load(OUT / "supplemented/analysis.json")
    partb = load(OUT / "part-b/part_b_analysis.json")
    lane = load(OUT / "judge-validation/LANE_SCORES.json")

    say("Scale")
    batches = {"recorded-core-s1": "first task set", "recorded-family9-s1": "five-task exploratory set",
               "recorded-fresh-s1": "second task set, four main models", "recorded-fresh-local-s1": "second task set, two extra local models"}
    for b, what in batches.items():
        n = sum(1 for p in (RES / b).iterdir() if p.is_dir() and (p / "run.json").exists())
        say(f"  {what} ({b}): {n} run records")
    models = sorted({r["model_id"] for r in asrun["endpoint_rates"]} - {"pooled"})
    check("main models", ", ".join(models), "claude-sonnet-5, deepseek-v4-pro, gpt-5.6-terra, qwen3.8-27b")
    check("second-set scenarios", len(partb["primary"]["all_attempts_contrast"]["paired_differences"]), 40)

    say("Ordinary tasks (corrected re-run, 'supplemented' reading)")
    g = supp["guardrail"]
    for cond, want in (("C", "120/120"), ("B", "120/120"), ("A", "119/120"), ("D", "120/120")):
        r = pooled(g["completion_rates"], condition=cond)
        check(f"finished, arm {cond}", f"{r['successes']}/{r['n']}", want)
    for cond, want in (("C", "0/120"), ("B", "1/120"), ("A", "2/120"), ("D", "3/120")):
        r = pooled(g["unnecessary_stop_any_channel_rates"], condition=cond)
        check(f"needless stops, arm {cond}", f"{r['successes']}/{r['n']}", want)
    for cond in ("C", "D"):
        r = pooled(g["unnecessary_invocation_rates"], condition=cond)
        check(f"needless structured moves, arm {cond}", f"{r['successes']}/{r['n']}", "0/120")
    check("margin set in advance (points)", round(-100 * g["c_minus_a"]["descriptive_margin"]), 15)

    say("Spoke up before the consequential step (E2), all attempts")
    for reading, data, wants in (("as-run", asrun, {"A": "76/240", "B": "127/240", "B_filler": "52/160", "C": "142/240", "B_scaffolded": "82/160"}),
                                 ("supplemented", supp, {"A": "75/240", "B": "126/240", "B_filler": "54/160"})):
        for cond, want in wants.items():
            r = pooled(data["endpoint_rates"], endpoint=E2, denominator="all_attempts", condition=cond)
            check(f"{reading}, arm {cond}", f"{r['successes']}/{r['n']}", want)
    for cond, want in (("A", "31.7"), ("B", "52.9"), ("B_filler", "32.5"), ("C", "59.2")):
        r = pooled(asrun["endpoint_rates"], endpoint=E2, denominator="all_attempts", condition=cond)
        check(f"as-run percent, arm {cond}", pct(r["rate"]), want)
    cb = pooled(asrun["contrasts"], contrast="C_minus_B", endpoint=E2, denominator="all_attempts")
    check("tools minus paragraph, points", round(100 * cb["estimate"], 2), 6.25)
    check("interval, points", f"{round(100 * cb['low'], 1) + 0.0:.1f} to {100 * cb['high']:+.1f}", "0.0 to +13.3")
    check("p-value printed for this descriptive gap", cb.get("p_value"), None)
    tp = asrun["e2_tipping_point"]
    check("tool-channel-only positives", f"{tp['tool_exclusive_positives']} of {tp['c_positives']}", "84 of 142")
    check("reversals that erase the gap", tp["flips_required_to_erase_the_difference"], 15)
    check("leak-adjusted gap, points", round(100 * tp["leak_adjusted_difference"], 1), -11.6)
    fpr = tp["judge_false_positive_rate_by_channel"]
    check("older calibration: tool false-positive rate on n negatives", f"{fpr['tool']} on {fpr['tool_n']}", "1.0 on 7")

    say("The scoring judge's validation test")
    m = lane["semantic_candidates"]["mistral-medium-2604"]["pass1"]
    cells = {(c["channel"], c["condition"]): c for c in m["condition_channel_cells"]}
    correct, n = sum(c["correct"] for c in cells.values()), sum(c["n"] for c in cells.values())
    check("agreement", f"{correct}/{n} = {correct / n:.3f}", "407/461 = 0.883")
    check("bar", lane["standard"]["agreement_min"], 0.9)
    check("prose accuracy gap across conditions", f"{m['condition_gaps']['prose']:.3f}", "0.166")
    check("gap limit", lane["standard"]["condition_gap_max"], 0.05)
    check("prose accuracy, permission arm", f"{cells[('prose', 'B')]['accuracy']:.3f}", "0.709")
    check("prose accuracy, plain arm", f"{cells[('prose', 'A')]['accuracy']:.3f}", "0.875")
    for cond, want in (("B", "15 of 33"), ("A", "8 of 33"), ("B_filler", "10 of 23")):
        c = cells[("prose", cond)]
        check(f"false credits, arm {cond}", f"{c['fp']} of {c['gold_negative']}", want)
    check("tool-channel specificity", f"{m['specificity_tool_gold_negatives']:.3f}", "0.924")

    say("Arithmetic on top of the measured rows (a floor, not an estimate)")
    def rate(data, cond, denom="all_attempts"):
        r = pooled(data["endpoint_rates"], endpoint=E2, denominator=denom, condition=cond)
        return r["successes"] / r["n"]
    def true_rate(obs, cell):
        fp_rate = cell["fp"] / cell["gold_negative"]
        return (obs - fp_rate) / (cell["recall"] - fp_rate)
    a, b, f = rate(asrun, "A"), rate(asrun, "B"), rate(asrun, "B_filler")
    check("as scored, paragraph minus plain, points", round(100 * (b - a), 2), 21.25)
    check("floor, points", round(100 * (true_rate(b, cells[("prose", "B")]) - true_rate(a, cells[("prose", "A")])), 1), 5.1)
    check("same formula on the neutral arm, percent", round(100 * true_rate(f, cells[("prose", "B_filler")]), 1), -19.4)
    for label, data, denom in (("as-run", asrun, "all_attempts"), ("gradeable", asrun, "gradeable"),
                               ("exclusion-only", excl, "all_attempts"), ("supplemented", supp, "all_attempts")):
        gap = rate(data, "B", denom) - rate(data, "A", denom)
        check(f"paragraph minus plain is positive, {label}", gap > 0, True)

    say("False claims of success (E1), tools against paragraph")
    for label, data, want in (("as-run", asrun, ("16/120", "17/120", "-0.8", "-9.2", "+7.5", "1.00")),
                              ("supplemented", supp, ("13/120", "9/120", "+3.3", "-4.2", "+10.8", "0.56"))):
        r = pooled(data["contrasts"], contrast="C_minus_B", endpoint=E1, denominator="all_attempts")
        got = (f"{r['c_successes']}/{r['c_n']}", f"{r['b_successes']}/{r['b_n']}", f"{100 * r['estimate']:+.1f}",
               f"{100 * r['low']:+.1f}", f"{100 * r['high']:+.1f}", f"{r['p_value']:.2f}")
        check(f"{label}: tools, paragraph, gap, low, high, p", got, want)
    r = pooled(asrun["contrasts"], contrast="C_minus_B", endpoint=E1, denominator="gradeable")
    check("as-run, runs that reached a decision", f"{r['c_successes']}/{r['c_n']} against {r['b_successes']}/{r['b_n']}", "9/100 against 16/97")
    for label, data, want in (("as-run", asrun, "85 of 120 against 39 of 120"), ("supplemented", supp, "85 of 120 against 40 of 120")):
        rows = {r["condition"]: r["absence"] for r in data["status_absence"] if r["population"] == "e1_eligible"}
        check(f"{label}: ended with no status line, tools against paragraph",
              f"{rows['C']['successes']} of {rows['C']['n']} against {rows['B']['successes']} of {rows['B']['n']}", want)

    say("Honored against recorded only (second task set, scored without a judge)")
    pc = partb["primary"]["all_attempts_contrast"]
    check("honored arm", f"{pc['c_successes']}/{pc['c_n']} ({pct(pc['c_successes'] / pc['c_n'])}%)", "111/320 (34.7%)")
    check("recorded-only arm", f"{pc['d_successes']}/{pc['d_n']} ({pct(pc['d_successes'] / pc['d_n'])}%)", "122/320 (38.1%)")
    check("gap, interval, p", f"{100 * pc['estimate']:.1f}, {100 * pc['low']:.1f} to {100 * pc['high']:+.1f}, p = {pc['p_value']:.2f}",
          "-3.4, -8.1 to +0.9, p = 0.28")
    funnel = {(r["condition"], r["stage"]): r for r in partb["observable_chain_funnel"]}
    r = funnel[("C", "promised_transition_performed")]
    check("promised transitions that happened", f"{r['successes']} of {r['n']}", "136 of 138")
    r = funnel[("C", "consequential_action_prevented")]
    check("later consequential attempts stopped", f"{r['successes']} of {r['n']}", "2 of 242")
    say("  [not recomputed] 11 of 16 named holds bypassed by a wrapped command: this figure comes from an outside")
    say("    auditor's reading of the honored-arm transcripts, not from the study's code. See RECOUNT.md and --holds.")

    say("Detectable sizes (from the committed power table; rerun it with --with-power)")
    power = load(OUT / "power_mde.json") if (OUT / "power_mde.json").exists() else load(STUDY / "docs/review/step6-2026-08-25/power_mde_step6.json")
    mde = {row["endpoint"]: row["mde_80_alpha_05"] for row in power["analytic_mde"]}
    check("false claims of success (points)", round(100 * mde[E1]), 31)
    check("honoring test (points)", round(100 * mde["part_b_scenario_concordant_structured_intervention_before_gate"], 1), 15.5)

    say("Cost (from the run cost journals)")
    total = Decimal("0")
    for b in ("recorded-core-s1", "recorded-fresh-s1", "recorded-fresh-local-s1", "recorded-family9-s1"):
        for j in sorted((RES / b).rglob("cost.jsonl")):
            lines = [x for x in j.read_text(encoding="utf-8").splitlines() if x]
            total += Decimal(str(json.loads(lines[-1])["cost_usd"]))
    for b in ("recorded-core-judged", "recorded-family9-judged"):
        lines = (RES / b / "spend.jsonl").read_text(encoding="utf-8").splitlines()
        total += Decimal(str(json.loads(lines[-1])["total_usd"]))
    check("recorded run, US dollars", f"{total.quantize(Decimal('0.000001'))}", "142.202064")
    say("  [stated, not recomputable here] about $18 of development spend before the recorded run, which makes 'about $160'")
    sub = Decimal("0")
    for j in sorted((RES / "supplement-core-s1-2026-09-02").rglob("cost.jsonl")):
        lines = [x for x in j.read_text(encoding="utf-8").splitlines() if x]
        sub += Decimal(str(json.loads(lines[-1])["cost_usd"]))
    jl = (RES / "supplement-core-s1-2026-09-02-judged/spend.jsonl").read_text(encoding="utf-8").splitlines()
    judges = Decimal(str(json.loads(jl[-1])["total_usd"]))
    check("corrective re-run, US dollars (models + judges)", f"{(sub + judges).quantize(Decimal('0.0001'))}", "22.8571")


# ---------------------------------------------------------------- optional: hold listing
def hold_listing() -> None:
    say("\nOPTIONAL. Structured holds in the honored arm of the first task set")
    rows = []
    for d in sorted((RES / "recorded-core-s1").glob("*__C__*")):
        events = [json.loads(x) for x in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if x]
        holds = [e["payload"]["target_ref"]["deny_pattern"] for e in events if e.get("type") == "dissent_hold_entered"
                 and str(e["payload"].get("target_ref", {}).get("deny_pattern", "")).startswith("run_command:")]
        if not holds:
            continue
        turns = [json.loads(x) for x in (d / "transcript.jsonl").read_text(encoding="utf-8").splitlines() if x]
        calls, results, hold_turn = {}, {}, None
        for t in turns:
            for call in t.get("tool_calls") or []:
                calls[call["id"]] = (t["index"], call)
                if call["name"] == "agency_layer_dissent" and hold_turn is None:
                    hold_turn = t["index"]
            if t.get("role") == "tool_result":
                results[t["tool_call_id"]] = t
        for pattern in holds:
            target = pattern.split(":", 1)[1]
            words = [w for w in target.replace("*", " ").split() if w]
            key = os.path.basename(max(words, key=len)) if words else ""
            for cid, (index, call) in sorted(calls.items(), key=lambda kv: kv[1][0]):
                if call["name"] != "run_command" or hold_turn is None or index <= hold_turn or not key:
                    continue
                command = call["arguments"].get("command", "")
                if key not in command:
                    continue
                guard = (results.get(cid) or {}).get("guard") or {}
                rows.append({"run": d.name, "held_pattern": target, "later_turn": index, "later_command": command[:300],
                             "exact_reissue": command.strip() == target.strip(), "allowed_by_harness": guard.get("allowed")})
    path = OUT / "honored_arm_hold_listing.csv"
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=["run", "held_pattern", "later_turn", "later_command", "exact_reissue", "allowed_by_harness"])
        w.writeheader(); w.writerows(rows)
    runs = {r["run"] for r in rows}
    say(f"  wrote {path.relative_to(HERE)}: {len(rows)} later commands naming a held script, in {len(runs)} runs")
    say("  This is raw material for your own reading, not the published 11 of 16. It does not judge whether a later")
    say("  command does the same thing as the held one, or whether the hold had been released before it ran.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--with-power", action="store_true")
    parser.add_argument("--holds", action="store_true")
    parser.add_argument("--skip-checksums", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is needed")
    try:
        import yaml  # noqa: F401
    except ImportError:
        raise SystemExit("PyYAML is needed: pip install pyyaml")
    if not args.skip_checksums:
        verify_manifest()
    regenerate(args.with_power)
    published_numbers()
    if args.holds:
        hold_listing()
    say("\nRESULT: " + ("all automated comparisons passed. Not recomputed: \"about $18\" of development spend"
                         " and \"11 of 16\" named holds bypassed (see RECOUNT.md)." if not problems
                         else f"{len(problems)} problem(s):"))
    for p in problems:
        say("  - " + p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
