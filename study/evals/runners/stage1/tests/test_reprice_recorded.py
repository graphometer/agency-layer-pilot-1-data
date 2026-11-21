"""Offline regression for the recorded-package repricer."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


STAGE1 = Path(__file__).resolve().parents[1]
TOOL = STAGE1 / "tools" / "reprice_recorded.py"
SPEC = importlib.util.spec_from_file_location("reprice_recorded", TOOL)
repricer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(repricer)


def _plan(name: str) -> dict:
    return yaml.safe_load((STAGE1 / name).read_text(encoding="utf-8"))


def test_constants_are_bound_to_frozen_plans_and_totals_reproduce(tmp_path: Path) -> None:
    core = _plan("plan_recorded.yaml")
    fresh = _plan("plan_fresh_recorded.yaml")
    local = _plan("plan_fresh_local_recorded.yaml")
    family9 = _plan("plan_family9_recorded.yaml")
    subjects = {subject for subject, _, _ in repricer.SUBJECTS}
    assert subjects == set(core["expect"]["per_subject"]) == set(fresh["expect"]["per_subject"])
    assert repricer.FREE_SUBJECTS == ({"qwen3.8-27b"}
                                     | set(local["expect"]["per_subject"])
                                     | set(family9["expect"]["per_subject"]))
    assert set(repricer.CORE_CONDITIONS) == set(core["expect"]["per_condition"])
    assert set(repricer.FRESH_CONDITIONS) == set(fresh["expect"]["per_condition"])

    output = tmp_path / "projection.json"
    subprocess.run([sys.executable, str(TOOL), "--json", str(output)], check=True,
                   cwd=STAGE1, capture_output=True, text=True)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert (payload["expected_usd"], payload["worst_case_usd"]) == (240.99, 302.97)
    subject_billed = sum(
        count for plan in (core, fresh)
        for subject, count in plan["expect"]["per_subject"].items()
        if subject not in repricer.FREE_SUBJECTS
    )
    instrument_billed = core["expect"]["total"] + family9["expect"]["total"]
    fully_free = (local["expect"]["total"]
                  + sum(count for subject, count in fresh["expect"]["per_subject"].items()
                        if subject in repricer.FREE_SUBJECTS))
    assert (payload["subject_billed_rows"], payload["instrument_billed_rows"],
            payload["fully_free_rows"]) == (subject_billed, instrument_billed, fully_free)
    assert (subject_billed, instrument_billed, fully_free) == (2400, 2640, 480)
    assert "api_priced_rows" not in payload
