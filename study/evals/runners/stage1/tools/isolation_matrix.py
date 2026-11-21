"""Run every promoted scenario's own checks inside the isolation, once.

PM14 says every command a run executes must happen inside the namespace. That
includes the scenario's `success_check` and the harness's `check.py`. This tool
answers the only question that matters after the switch: does any of the 45
promoted scenarios behave differently because of the isolation?

For each scenario the fixture is copied to a throwaway sandbox twice. One copy
runs its `success_check` and its `check.py` on the host, the way the harness ran
them before, and one runs them inside bwrap. The fixtures are in their unsolved
state, so most success checks fail on both sides; a FAILURE IS ONLY AN ISOLATION
PROBLEM WHEN THE TWO SIDES DISAGREE, or when the isolated side reports a missing
interpreter, an unreachable network, or a read-only path.

    python tools/isolation_matrix.py --scenarios /path/to/evals/scenarios

Writes results/isolation_matrix.json and prints the table.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness import config as config_module, isolation as isolation_module  # noqa: E402
from harness import sandbox as sandbox_module  # noqa: E402

# Signatures of a failure caused by the sandbox rather than by the scenario.
ISOLATION_SIGNATURES = (
    (re.compile(r"command not found", re.I), "missing interpreter"),
    (re.compile(r"No such file or directory: '?(python3|node|bash|sh)", re.I), "missing interpreter"),
    (re.compile(r"bad interpreter", re.I), "missing interpreter"),
    (re.compile(r"Network is unreachable", re.I), "needs network"),
    (re.compile(r"Temporary failure in name resolution", re.I), "needs DNS"),
    (re.compile(r"Name or service not known", re.I), "needs DNS"),
    (re.compile(r"Read-only file system", re.I), "writes outside /work"),
    (re.compile(r"Operation not permitted", re.I), "needs a capability"),
    (re.compile(r"bwrap:", re.I), "bubblewrap refused to start"),
    (re.compile(r"getpwuid|uv_os_get_passwd", re.I), "needs a passwd entry"),
)

HOST_ENVIRONMENT = {
    "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    "LANG": "C.UTF-8",
}


def _classify(text):
    for pattern, label in ISOLATION_SIGNATURES:
        if pattern.search(text or ""):
            return label
    return None


def _run_host(root, argv, timeout=180, shell=False):
    environment = dict(HOST_ENVIRONMENT, HOME=root, TMPDIR=root, PWD=root)
    return subprocess.run(argv, cwd=root, env=environment, capture_output=True,
                          text=True, timeout=timeout, shell=shell)


def _copy(fixture):
    root = os.path.realpath(tempfile.mkdtemp(prefix="al-matrix-"))
    shutil.copytree(fixture, root, dirs_exist_ok=True)
    return root


def _check_json(stdout):
    try:
        return json.loads(stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def one_scenario(scenario, isolation, skip_host=False):
    row = {
        "scenario_id": scenario.scenario_id,
        "family": scenario.family,
        "success_check": scenario.success_check,
        "isolation_reason": None,
        "notes": [],
    }

    # ------------------------------------------------------------ isolated
    root = _copy(scenario.fixture_dir)
    try:
        if scenario.success_check:
            done = isolation.spawn_shell(root, scenario.success_check, 180)
            row["isolated_success_check_exit"] = done.returncode
            row["isolated_success_check_stderr"] = done.stderr.strip()[-400:]
            reason = _classify(done.stdout + done.stderr)
            if reason:
                row["isolation_reason"] = reason
        else:
            row["isolated_success_check_exit"] = None

        shutil.copyfile(scenario.check_path, os.path.join(root, "check.py"))
        done = isolation.spawn(root, ["python3", "check.py"], 180)
        row["isolated_check_exit"] = done.returncode
        row["isolated_check"] = _check_json(done.stdout)
        row["isolated_check_stderr"] = done.stderr.strip()[-400:]
        if row["isolated_check"] is None:
            row["notes"].append("check.py printed no JSON inside the isolation")
            row["isolation_reason"] = row["isolation_reason"] or "check.py did not report"
        reason = _classify(done.stderr)
        if reason:
            row["isolation_reason"] = reason
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # ---------------------------------------------------------------- host
    if skip_host:
        row["host_success_check_exit"] = None
        row["host_check"] = None
        row["agrees_with_host"] = None
        return row

    root = _copy(scenario.fixture_dir)
    try:
        if scenario.success_check:
            done = _run_host(root, scenario.success_check, shell=True)
            row["host_success_check_exit"] = done.returncode
        else:
            row["host_success_check_exit"] = None
        shutil.copyfile(scenario.check_path, os.path.join(root, "check.py"))
        done = _run_host(root, ["python3", "check.py"])
        row["host_check_exit"] = done.returncode
        row["host_check"] = _check_json(done.stdout)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    row["agrees_with_host"] = (
        row["isolated_success_check_exit"] == row["host_success_check_exit"]
        and _comparable(row["isolated_check"]) == _comparable(row["host_check"])
    )
    if not row["agrees_with_host"] and not row["isolation_reason"]:
        row["isolation_reason"] = "isolated and host results differ"
    return row


def _comparable(check):
    """The fields of a check.json result that must not move with the sandbox.

    files_changed is excluded: the isolated and host copies are separate
    temporary directories and interpreter noise differs between them.
    """
    if not check:
        return None
    return {
        "task_completed": check.get("task_completed"),
        "consequential_action_count": check.get("consequential_action_count"),
        "fabrication_present": check.get("fabrication_present"),
        "criterion_tampered": check.get("criterion_tampered"),
        "error": check.get("error"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--out", default=os.path.join(ROOT, "results", "isolation_matrix.json"))
    parser.add_argument("--skip-host", action="store_true",
                        help="skip the host baseline; the isolated side is still checked")
    arguments = parser.parse_args(argv)

    isolation = isolation_module.build({"isolation": "bwrap"}, harness_paths=[ROOT])
    probe = isolation.probe()
    print(f"isolation {isolation.kind} {isolation.version} probe={probe['status']} "
          f"hardening={probe['hardening']}")
    if probe["status"] != "pass":
        for failure in probe["failures"]:
            print("  FAILURE", failure)
        return 1

    scenarios = config_module.load_scenarios(arguments.scenarios)
    rows = []
    print(f"\n{'scenario':<32} {'sc':>4} {'host':>5} {'iso':>4} {'completed':>10} "
          f"{'agrees':>7}  isolation reason")
    for scenario in scenarios:
        row = one_scenario(scenario, isolation, skip_host=arguments.skip_host)
        rows.append(row)
        completed = (row["isolated_check"] or {}).get("task_completed")
        print(f"{row['scenario_id']:<32} "
              f"{'yes' if row['success_check'] else '-':>4} "
              f"{str(row['host_success_check_exit']):>5} "
              f"{str(row['isolated_success_check_exit']):>4} "
              f"{str(completed):>10} "
              f"{str(row['agrees_with_host']):>7}  {row['isolation_reason'] or ''}")

    failures = [row for row in rows if row["isolation_reason"]]
    report = {
        "isolation": isolation.record(),
        "hardening": probe["hardening"],
        "scenarios": len(rows),
        "with_success_check": sum(1 for row in rows if row["success_check"]),
        "isolation_failures": [row["scenario_id"] for row in failures],
        "rows": rows,
    }
    os.makedirs(os.path.dirname(arguments.out), exist_ok=True)
    with open(arguments.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"\n{len(rows)} scenarios, {report['with_success_check']} with a success_check, "
          f"{len(failures)} failing for an isolation reason")
    for row in failures:
        print(f"  {row['scenario_id']}: {row['isolation_reason']}")
        if row.get("isolated_success_check_stderr"):
            print(f"      {row['isolated_success_check_stderr'][:300]}")
    print(f"\nwritten: {arguments.out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
