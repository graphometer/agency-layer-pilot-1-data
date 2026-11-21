"""The smoke test: the first real API calls this project makes.

One run per condition on f1-01, for each of three models: 12 runs, a $5 ceiling
enforced by the pre-dispatch reservation, and a short SMOKE_REPORT.md.

This is the real milestone, not the mock proof. The proof shows the guard, the
log and the state machine work; only this shows that a real model's calls arrive
in the shape the clients expect. The aerial review listed nine things that could
break on the first call, and each one is a checked line in the report rather
than something to notice afterwards in a transcript.

Keys come from the environment. An arm whose key is missing is skipped and said
to be skipped; it is never a crash and never a silent omission.

    export ANTHROPIC_API_KEY=...        # for the Sonnet 5 arm
    export OPENAI_API_KEY=...           # for the GPT arm
    .venv/bin/python tools/smoke.py --config smoke.yaml

Add --dry-run to print the plan, the resolved parameters and the estimated
worst-case spend without sending anything.
"""

import argparse
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from harness import cli as cli_module  # noqa: E402
from harness import config as config_module, cost, events as events_module, runner  # noqa: E402
from harness.models.base import ProviderError  # noqa: E402

SCENARIO = "f1-01-tax-rounding"
# The default matrix. A config may widen it (smoke_conditions) — the step-9 second
# smoke adds B_scaffolded so the R45 arm crosses the wire once before the freeze.
CONDITIONS = ["A", "B", "C", "D"]
KEY_BY_PROVIDER = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}


SDK_BY_PROVIDER = {"anthropic": "anthropic", "openai": "openai", "local": "openai",
                   "openai_compatible": "openai"}


def preflight():
    """The SDKs are not installed by the mock milestone. Say so before anything else."""
    missing = []
    for package in sorted(set(SDK_BY_PROVIDER.values())):
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    return missing


def available(model_config):
    """Whether this arm can run, and why not when it cannot."""
    provider = model_config["provider"]
    key = (model_config.get("api_key_env") if provider == "openai_compatible"
           else KEY_BY_PROVIDER.get(provider))
    if key and not os.environ.get(key):
        return False, f"{key} is not set in the environment"
    if provider == "local" and not model_config.get("base_url"):
        return False, "no base_url configured for the local endpoint"
    return True, None


def check_run(record, run_dir, model_config):
    """The aerial review's nine first-call risks, as checked lines."""
    checks = {}
    events = []
    events_path = os.path.join(run_dir, "events.jsonl")
    if os.path.exists(events_path):
        with open(events_path, "r", encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle if line.strip()]
    transcript = []
    transcript_path = os.path.join(run_dir, "transcript.jsonl")
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as handle:
            transcript = [json.loads(line) for line in handle if line.strip()]

    assistant = [e for e in transcript if e.get("role") == "assistant"]
    tool_results = [e for e in transcript if e.get("role") == "tool_result"]
    malformed = [e for e in transcript if e.get("role") == "malformed_tool_call"]

    # Which endpoint produced this run. The OpenAI arm moved to /v1/responses
    # after the first smoke returned a 400 on function tools plus
    # reasoning_effort in /v1/chat/completions.
    expected_surface = {"anthropic": "messages", "openai": "responses",
                        "local": "chat_completions",
                        "openai_compatible": "chat_completions"}[model_config["provider"]]
    checks["api surface"] = (record.get("api_surface") == expected_surface,
                             f"{record.get('api_surface')} (expected {expected_surface})")

    # The local endpoint builds a GBNF grammar from the tool schemas and cannot
    # parse the published affordance schemas; every other arm sends them as
    # published.
    expected_rendering = "flattened" if model_config["provider"] == "local" else "as_published"
    checks["tool schema rendering"] = (
        record.get("tool_schema_rendering") == expected_rendering,
        f"{record.get('tool_schema_rendering')} (expected {expected_rendering})")

    # R54: an arm that overrides the wire model (the OpenRouter DeepSeek pin) must
    # show the endpoint serving exactly that model, on disk, in run.json.
    wire_override = (model_config.get("extra_body") or {}).get("model")
    if wire_override:
        checks["served model matches the pinned wire model"] = (
            record.get("served_model") == wire_override,
            f"served={record.get('served_model')} "
            f"provider={record.get('served_provider')} (expected {wire_override})")
    # Grok step-9 note 6: the slug check alone would pass a third party serving the
    # same slug. A config that declares expected_served_provider also gates on the
    # gateway's serving-provider echo (OpenRouter's display name, e.g. "DeepSeek").
    expected_provider = model_config.get("expected_served_provider")
    if expected_provider:
        checks["served provider matches the pinned provider"] = (
            record.get("served_provider") == expected_provider,
            f"served_provider={record.get('served_provider')} (expected {expected_provider})")

    # 1 and 5: sampling. Nothing may be sent on the Anthropic arm.
    sent = record.get("sampling_sent", {})
    if model_config["provider"] == "anthropic":
        checks["no sampling sent to Anthropic"] = (sent == {}, json.dumps(sent))
    else:
        checks["sampling recorded as sent"] = (True, json.dumps(sent))

    # 2 and 5: thinking and effort pinned and recorded, never null.
    checks["thinking pinned and recorded"] = (
        record.get("thinking") is not None, repr(record.get("thinking")))
    checks["reasoning_effort recorded"] = (
        "reasoning_effort" in record, repr(record.get("reasoning_effort")))

    # 3: consecutive user turns. The client merges them, so a completed run with
    # a scripted follow-up proves the shape was accepted.
    followups = [e for e in transcript
                 if e.get("role") == "user"
                 and str(e.get("source", "")).startswith("scripted_operator")]
    checks["multi-turn accepted"] = (
        len(assistant) > 1, f"{len(assistant)} assistant turns, {len(followups)} follow-ups")

    # 4: refusal never scored as behaviour.
    checks["no provider refusal"] = (
        record["termination_reason"] != "provider_refusal", record["termination_reason"])

    # 6: thinking off on the local arm. The switch is sent, AND the result is
    # checked on the wire, because the flag being set is not the same as the
    # model having obeyed it.
    if model_config["provider"] == "local":
        checks["local thinking switch sent"] = (
            record.get("extra_body_sent", {}).get("chat_template_kwargs", {})
            .get("enable_thinking") is False,
            json.dumps(record.get("extra_body_sent", {})))
        leaked = [e for e in assistant
                  if "<think" in (e.get("text") or "").lower()
                  or "</think" in (e.get("text") or "").lower()]
        checks["local thinking off on the wire"] = (not leaked, f"{len(leaked)} turns with think tags")

    # 6 and 7: tool calling, and malformed calls that end a run under tolerance 0.
    checks["tool calls decoded"] = (
        len(tool_results) > 0, f"{len(tool_results)} tool results")
    checks["no malformed tool call"] = (
        not malformed, f"{len(malformed)}: " + ", ".join(m.get("tool_name", "?") for m in malformed))

    # 8: the follow-up budget, and whether it bound.
    checks["follow-up budget not exhausted"] = (
        len(followups) < 2, f"{len(followups)} of 2 used")

    # 9: prompt caching, Anthropic only.
    if model_config["provider"] == "anthropic":
        checks["prompt caching declared"] = (
            record.get("prompt_caching") == "system+tools", str(record.get("prompt_caching")))

    # The structured status line — under disclosure-32 semantics. The mid-run
    # completion probe (correction phase 2026-08-24, Sol finding 9) ends a run
    # at the turn where the scenario's success check passes, in every arm, so a
    # run truncated mid-tool-flow never reaches its wrap-up turn and a null
    # final_status is the EXPECTED record there, not a failure. STATUS is owed
    # only when the model actually got a closing prose turn (last assistant
    # entry carries no tool calls). The pre-correction form of this check
    # demanded STATUS unconditionally and failed 20/20 on the first post-
    # correction smoke — the check was stale, not the harness.
    last_assistant = next((e for e in reversed(transcript)
                           if e.get("role") == "assistant"), None)
    truncated_by_probe = (
        record.get("termination_reason") == "task_completed"
        and last_assistant is not None and bool(last_assistant.get("tool_calls")))
    if truncated_by_probe:
        checks["final status line (n/a: disclosure-32 completion truncation)"] = (
            True, f"run ended by the mid-run completion probe at turn "
                  f"{last_assistant.get('index')}; final_status={record.get('final_status')!r}")
    else:
        checks["final status line present"] = (
            record.get("final_status") is not None, repr(record.get("final_status")))

    # Reproducibility fields.
    checks["seed and fingerprint recorded"] = (
        "seed" in record and "system_fingerprint" in record,
        f"seed={record.get('seed')} supported={record.get('seed_supported')} "
        f"fingerprint={record.get('system_fingerprint')}")

    # Usage must be non-zero on a priced arm, or the meter is blind.
    checks["provider reported usage"] = (
        (record["input_tokens"] + record["output_tokens"]) > 0,
        f"{record['input_tokens']} in, {record['output_tokens']} out")

    denials = sum(1 for e in events if e["type"] == "execution_denied")
    return checks, {"turns": len(assistant), "denials": denials,
                    "events": len(events), "cost_usd": record["cost_usd"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agency Layer Stage 1 smoke test")
    parser.add_argument("--config", default=os.path.join(ROOT, "smoke.yaml"))
    parser.add_argument("--results", default=os.path.join(ROOT, "results"))
    parser.add_argument("--batch-id", default="smoke-real")
    parser.add_argument("--out", default=os.path.join(ROOT, "SMOKE_REPORT.md"))
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and the resolved parameters, send nothing")
    parser.add_argument("--scenario", default=SCENARIO,
                        help="scenario id to smoke (default f1-01; must be a non-study "
                             "development or fixture scenario — never a sealed one)")
    parser.add_argument("--recheck", action="store_true",
                        help="re-evaluate the checks over an EXISTING batch's run "
                             "directories and rewrite the report; dispatches nothing. "
                             "Exists so a check repaired after a smoke (e.g. the "
                             "disclosure-32 status rule) can be re-applied to the "
                             "already-paid-for artifacts instead of re-buying them.")
    arguments = parser.parse_args(argv)

    missing = preflight()
    if missing and not arguments.dry_run:
        print("The provider SDKs are not installed. Install them into this venv first:")
        print(f"  .venv/bin/python -m pip install {' '.join(missing)}")
        return 2

    config = config_module.load_config(arguments.config)
    scenarios = {s.scenario_id: s for s in
                 config_module.load_scenarios(os.path.join(ROOT, config["scenarios_dir"]))}
    scenario = scenarios[arguments.scenario]

    if arguments.recheck:
        rows = []
        for model_config in config["models"]:
            for condition in list(config.get("smoke_conditions") or CONDITIONS):
                run_dir = os.path.join(
                    arguments.results, "stage1", arguments.batch_id,
                    f"{arguments.scenario}__{condition}__{model_config['model_id']}")
                record_path = os.path.join(run_dir, "run.json")
                if not os.path.exists(record_path):
                    rows.append({"model": model_config["model_id"], "condition": condition,
                                 "error": f"no run.json at {run_dir}"})
                    print(f"MISS {model_config['model_id']:<18} {condition}  no run.json")
                    continue
                with open(record_path, "r", encoding="utf-8") as handle:
                    record = json.load(handle)
                checks, summary = check_run(record, run_dir, model_config)
                rows.append({"model": model_config["model_id"], "condition": condition,
                             "record": record, "checks": checks, "summary": summary})
                failed = [n for n, (ok_, _) in checks.items() if not ok_]
                print(f"{'ok  ' if not failed else 'CHECK'} {model_config['model_id']:<18} "
                      f"{condition}  {record['termination_reason']:<18} "
                      f"${record['cost_usd']:.4f}" + (f"  failed: {failed}" if failed else ""))
        meter = cost.CostMeter(
            prices=config.get("prices", {}),
            hard_ceiling_usd=float(config["spend"]["hard_ceiling_usd"]),
            report_at_usd=float(config["spend"]["report_at_usd"]))
        write_report(arguments.out, config, rows, [], meter, False,
                     scenario_id=arguments.scenario, recheck=True)
        print(f"\nwrote {arguments.out} (recheck; nothing dispatched)")
        return 0

    # PM14: the smoke tool builds live clients, so it is a live batch and takes
    # the same refusal. Built before any client, so an unisolatable host costs
    # nothing.
    isolation, probe = cli_module.build_isolation(
        config, allow_live=not arguments.dry_run,
        scenarios_dir=os.path.join(ROOT, config["scenarios_dir"]))
    print(f"isolation {isolation.kind} {isolation.version or ''} probe={probe['status']}")

    meter = cost.CostMeter(
        prices=config.get("prices", {}),
        hard_ceiling_usd=float(config["spend"]["hard_ceiling_usd"]),
        report_at_usd=float(config["spend"]["report_at_usd"]),
    )

    # The route classifier comes from the config, exactly as the batch CLI builds
    # it. The R38-era smoke hardcoded a mock here; the step-9 second smoke must
    # exercise the REAL billed classifier path (R52), so the config decides.
    route_classifier = (None if arguments.dry_run
                        else cli_module.build_route_classifier(config, allow_live=True))

    conditions = list(config.get("smoke_conditions") or CONDITIONS)

    rows = []
    skipped = []
    for model_config in config["models"]:
        ok, reason = available(model_config)
        if not ok:
            skipped.append((model_config["name"], model_config["model_id"], reason))
            print(f"SKIP {model_config['name']}: {reason}")
            continue

        for condition in conditions:
            client = config_module.build_model(model_config, allow_live=True)
            resolved = client.sent_parameters(config.get("sampling", {}))
            if arguments.dry_run:
                print(f"PLAN {model_config['model_id']:<18} {condition}  {json.dumps(resolved)}")
                rows.append({"model": model_config["model_id"], "condition": condition,
                             "dry_run": True, "resolved": resolved})
                continue

            settings = {
                "sampling": dict(config.get("sampling", {})),
                "cost_meter": meter,
                "command_timeout": config.get("command_timeout", 60),
                "malformed_tolerance": config.get("malformed_tolerance", 0),
                "llm_classifier": route_classifier,
                "isolation": isolation,
            }
            run_dir = os.path.join(arguments.results, "stage1", arguments.batch_id,
                                   f"{arguments.scenario}__{condition}__{model_config['model_id']}")
            try:
                run = runner.Run(
                    scenario=scenario, condition=condition, model=client, settings=settings,
                    batch_id=arguments.batch_id, repeat_index=0, run_dir=run_dir,
                    event_log_factory=events_module.EventLog,
                )
                record = run.execute()
                checks, summary = check_run(record, run.run_dir, model_config)
                rows.append({"model": model_config["model_id"], "condition": condition,
                             "record": record, "checks": checks, "summary": summary})
                failed = [n for n, (ok_, _) in checks.items() if not ok_]
                print(f"{'ok  ' if not failed else 'CHECK'} {model_config['model_id']:<18} "
                      f"{condition}  {record['termination_reason']:<18} "
                      f"${record['cost_usd']:.4f}" + (f"  failed: {failed}" if failed else ""))
            except (cost.CeilingReached, ProviderError) as error:
                rows.append({"model": model_config["model_id"], "condition": condition,
                             "error": f"{type(error).__name__}: {error}"})
                print(f"HALT {model_config['model_id']} {condition}: {error}")
                break
            except Exception as error:  # noqa: BLE001
                rows.append({"model": model_config["model_id"], "condition": condition,
                             "error": f"{type(error).__name__}: {error}",
                             "traceback": traceback.format_exc()[-2000:]})
                print(f"FAIL {model_config['model_id']} {condition}: {error}")

        if meter.halted:
            print(f"BATCH HALTED: {meter.halt_reason}")
            break

    # A dry run never overwrites a real report. This tool destroyed the
    # 2026-08-23 02:07 twelve-run report that way, and the runs behind it had
    # already been cleaned up, so it could not be rebuilt. Same rule as
    # CONTRACTS section 2 for runs: evidence is not silently replaced.
    out = arguments.out
    if arguments.dry_run and os.path.exists(out):
        out = os.path.splitext(arguments.out)[0] + ".dryrun.md"
        print(f"\n{arguments.out} already exists. A dry run never overwrites a report; "
              f"writing to {out} instead. Pass --out to choose another path.")
    write_report(out, config, rows, skipped, meter, arguments.dry_run,
                 scenario_id=arguments.scenario)
    print(f"\nwrote {out}")
    return 0


def write_report(path, config, rows, skipped, meter, dry_run, scenario_id=None, recheck=False):
    lines = ["# SMOKE_REPORT", ""]
    lines.append("First real API calls for the Agency Layer Stage 1 harness. One run per condition "
                 f"on `{scenario_id or SCENARIO}`, ceiling ${meter.hard_ceiling_usd:.2f}, "
                 "enforced before dispatch.")
    lines.append("")
    if dry_run:
        lines.append("**Dry run: nothing was sent.**")
        lines.append("")
    if recheck:
        total = sum(row["record"]["cost_usd"] for row in rows if "record" in row)
        lines.append("**Recheck: checks re-evaluated over existing run artifacts; nothing was "
                     f"dispatched.** Original recorded spend of the batch: ${total:.4f}. The "
                     "spend section below reflects this recheck process (zero), not the batch.")
        lines.append("")

    if skipped:
        lines.append("## Arms skipped")
        lines.append("")
        for name, model_id, reason in skipped:
            lines.append(f"- `{model_id}` ({name}): {reason}")
        lines.append("")

    lines.append("## Spend")
    lines.append("")
    summary = meter.summary()
    lines.append(f"- spent ${summary['total_usd']:.4f} of ${summary['hard_ceiling_usd']:.2f}, "
                 f"headroom ${summary['headroom_usd']:.4f}")
    lines.append(f"- calls dispatched {summary['calls_dispatched']}, refused "
                 f"{summary['calls_refused']}, largest reservation "
                 f"${summary['largest_reservation_usd']:.4f}")
    lines.append(f"- never exceeded the ceiling: {summary['never_exceeded_ceiling']}")
    if summary["halted"]:
        lines.append(f"- **halted** ({summary['halt_kind']}): {summary['halt_reason']}")
    lines.append("")

    lines.append("## Runs")
    lines.append("")
    lines.append("| model | cond | termination | status | thinking | effort | sampling sent | "
                 "cache read | cost |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for row in rows:
        if "record" not in row:
            note = row.get("error", "dry run")
            lines.append(f"| `{row['model']}` | {row['condition']} | {note} | | | | | | |")
            continue
        r = row["record"]
        lines.append(
            f"| `{r['model_id']}` | {r['condition']} | {r['termination_reason']} | "
            f"{r.get('final_status')} | {json.dumps(r.get('thinking'))} | "
            f"{r.get('reasoning_effort')} | {json.dumps(r.get('sampling_sent'))} | "
            f"{r.get('cache_read_input_tokens', 'n/a')} | ${r['cost_usd']:.4f} |")
    lines.append("")

    lines.append("## First-call checks")
    lines.append("")
    lines.append("Each line is one of the risks the aerial review listed for the first real call.")
    lines.append("")
    for row in rows:
        if "checks" not in row:
            continue
        lines.append(f"### `{row['model']}` condition {row['condition']}")
        lines.append("")
        for name, (ok, detail) in row["checks"].items():
            lines.append(f"- {'PASS' if ok else 'FAIL'} {name}: {detail}")
        lines.append("")

    failures = [(row["model"], row["condition"], name)
                for row in rows if "checks" in row
                for name, (ok, _) in row["checks"].items() if not ok]
    errors = [(row["model"], row["condition"], row["error"]) for row in rows if "error" in row]
    lines.append("## Verdict")
    lines.append("")
    if not rows:
        lines.append("No arm ran. Every model was skipped; see above.")
    elif not failures and not errors:
        lines.append("Every check passed on every arm that ran. The provider clients work on the "
                     "wire, and the run records carry what was actually sent.")
    else:
        lines.append(f"{len(failures)} failed checks and {len(errors)} errors. Details above.")
        for model, condition, name in failures:
            lines.append(f"- `{model}` {condition}: {name}")
        for model, condition, error in errors:
            lines.append(f"- `{model}` {condition}: {error}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
