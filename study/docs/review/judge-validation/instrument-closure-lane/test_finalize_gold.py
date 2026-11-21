"""Tests for finalize_gold.py and concordance_71.py on synthetic fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import concordance_71
import finalize_gold


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_world(
    tmp_path: Path,
    monkeypatch,
    *,
    n_items: int = 6,
    split_items: dict[str, list[int]] | None = None,
    audit_items: dict[str, list[int]] | None = None,
    sol_adj_answers: dict[str, dict[int, str]] | None = None,
    sol_audit_answers: dict[str, dict[int, str]] | None = None,
):
    """A tiny lane: items it-000..; unanimity everywhere except declared splits.

    Unanimous label is 'not_qualifying' / 'no_attempt'; a split item gets one dissenting
    'qualifying' / 'attempt' vote from grok.  Sol answer defaults: adjudications get the
    positive word, audits echo the unanimous label.  Sol's answers are written where the real
    lane keeps them — the committed ``sol_answers/`` directory beside the script — so every test
    here exercises the committed path the script actually reads.
    """
    split_items = split_items or {"l1": [], "l2": []}
    audit_items = audit_items or {"l1": [], "l2": []}
    sol_adj_answers = sol_adj_answers or {"l1": {}, "l2": {}}
    sol_audit_answers = sol_audit_answers or {"l1": {}, "l2": {}}
    here = tmp_path / "lane"
    labels_dir = here / "labels"
    sol_dir = here / "sol_answers"
    ids = [f"it-{i:03d}" for i in range(n_items)]
    neg = {"l1": "not_qualifying", "l2": "no_attempt"}
    pos = {"l1": "qualifying", "l2": "attempt"}

    write_jsonl(
        here / "goldset_lane.jsonl",
        [
            {"item_id": iid, "condition": "C", "channel": "prose", "stratum": "S1"}
            for iid in ids
        ],
    )
    for track in ("l1", "l2"):
        for labeller in finalize_gold.LABELLERS:
            rows = []
            for i, iid in enumerate(ids):
                answer = neg[track]
                if i in split_items[track] and labeller == "grok-4.6":
                    answer = pos[track]
                rows.append(
                    {"request_id": finalize_gold.request_id(iid, track), "parsed": answer}
                )
            write_jsonl(labels_dir / f"{labeller}__{track}.jsonl", rows)
        write_jsonl(
            here / f"adjudication_queue_{track}.jsonl",
            [
                {"request_id": finalize_gold.request_id(ids[i], track), "prompt": "x"}
                for i in split_items[track]
            ],
        )
        write_jsonl(
            here / f"audit_queue_{track}.jsonl",
            [
                {"request_id": finalize_gold.request_id(ids[i], track), "prompt": "x"}
                for i in audit_items[track]
            ],
        )
        write_jsonl(
            sol_dir / f"sol_adjudications_{track}.jsonl",
            [
                {
                    "request_id": finalize_gold.request_id(ids[i], track),
                    "answer": sol_adj_answers[track].get(i, pos[track]),
                }
                for i in split_items[track]
            ],
        )
        write_jsonl(
            sol_dir / f"sol_audit_{track}.jsonl",
            [
                {
                    "request_id": finalize_gold.request_id(ids[i], track),
                    "answer": sol_audit_answers[track].get(i, neg[track]),
                }
                for i in audit_items[track]
            ],
        )

    monkeypatch.setattr(finalize_gold, "HERE", here)
    monkeypatch.setattr(finalize_gold, "LABELS", labels_dir)
    monkeypatch.setattr(finalize_gold, "EXPECTED_ITEMS", n_items)
    return here, sol_dir, ids


def test_happy_path_merges_unanimous_and_adjudicated(tmp_path, monkeypatch):
    here, _, ids = build_world(
        tmp_path,
        monkeypatch,
        split_items={"l1": [1], "l2": [2]},
        audit_items={"l1": [0], "l2": [0]},
    )
    finalize_gold.main()
    gold = {r["id"]: r for r in map(json.loads, (here / "gold_final.jsonl").open())}
    assert len(gold) == 6
    assert gold[ids[1]]["l1"] == "qualifying"  # Sol's adjudication won
    assert gold[ids[1]]["l2"] == "no_attempt"  # unanimous on the other track
    assert gold[ids[2]]["l2"] == "attempt"
    prov = {r["id"]: r for r in map(json.loads, (here / "gold_provenance.jsonl").open())}
    assert prov[ids[1]]["l1_source"] == "adjudicated"
    assert prov[ids[1]]["l2_source"] == "unanimous"
    freeze = json.loads((here / "GOLD_FREEZE.json").read_text())
    assert freeze["tallies"]["l1"] == {"unanimous": 5, "adjudicated": 1}
    assert freeze["audit_gate"]["l1"]["disagreements"] == []


def test_determinism_two_runs_identical(tmp_path, monkeypatch):
    here, _, _ = build_world(
        tmp_path, monkeypatch, split_items={"l1": [1], "l2": []}
    )
    finalize_gold.main()
    first = (here / "gold_final.jsonl").read_bytes()
    finalize_gold.main()
    assert (here / "gold_final.jsonl").read_bytes() == first


def test_audit_gate_two_disagreements_refuses(tmp_path, monkeypatch):
    build_world(
        tmp_path,
        monkeypatch,
        audit_items={"l1": [0, 3, 4], "l2": []},
        sol_audit_answers={"l1": {0: "qualifying", 3: "qualifying"}, "l2": {}},
    )
    with pytest.raises(SystemExit, match="AUDIT GATE FAILED"):
        finalize_gold.main()


def test_audit_single_disagreement_passes_and_is_recorded(tmp_path, monkeypatch):
    here, _, _ = build_world(
        tmp_path,
        monkeypatch,
        audit_items={"l1": [0, 3], "l2": []},
        sol_audit_answers={"l1": {0: "qualifying"}, "l2": {}},
    )
    finalize_gold.main()
    freeze = json.loads((here / "GOLD_FREEZE.json").read_text())
    assert len(freeze["audit_gate"]["l1"]["disagreements"]) == 1


def test_audit_abstention_counts_as_disagreement(tmp_path, monkeypatch):
    build_world(
        tmp_path,
        monkeypatch,
        audit_items={"l1": [0, 3], "l2": []},
        sol_audit_answers={"l1": {0: "cannot_determine", 3: "qualifying"}, "l2": {}},
    )
    with pytest.raises(SystemExit, match="AUDIT GATE FAILED"):
        finalize_gold.main()


def test_sol_abstention_on_split_triggers_ratification_d(tmp_path, monkeypatch):
    build_world(
        tmp_path,
        monkeypatch,
        split_items={"l1": [1], "l2": []},
        sol_adj_answers={"l1": {1: "cannot_determine"}, "l2": {}},
    )
    with pytest.raises(SystemExit, match="RATIFICATION \\(d\\) TRIGGERED"):
        finalize_gold.main()


def test_missing_adjudication_refuses(tmp_path, monkeypatch):
    _, sol_dir, _ = build_world(
        tmp_path, monkeypatch, split_items={"l1": [1, 3], "l2": []}
    )
    rows = [json.loads(l) for l in (sol_dir / "sol_adjudications_l1.jsonl").open()]
    write_jsonl(sol_dir / "sol_adjudications_l1.jsonl", rows[:1])
    with pytest.raises(SystemExit, match="has no Sol adjudication"):
        finalize_gold.main()


def test_split_membership_mismatch_refuses(tmp_path, monkeypatch):
    here, _, _ = build_world(tmp_path, monkeypatch, split_items={"l1": [1], "l2": []})
    write_jsonl(here / "adjudication_queue_l1.jsonl", [])
    with pytest.raises(SystemExit, match="disagree with the committed"):
        finalize_gold.main()


def test_audit_answers_must_cover_queue_exactly(tmp_path, monkeypatch):
    _, sol_dir, _ = build_world(
        tmp_path, monkeypatch, audit_items={"l1": [0, 3], "l2": []}
    )
    rows = [json.loads(l) for l in (sol_dir / "sol_audit_l1.jsonl").open()]
    write_jsonl(sol_dir / "sol_audit_l1.jsonl", rows[:1])
    with pytest.raises(SystemExit, match="do not cover the audit queue"):
        finalize_gold.main()


# --- A-03: the committed sol_answers/ copy is the authoritative source ---


def test_committed_sol_answers_are_the_source(tmp_path, monkeypatch):
    """Normal operation reads sol_answers/ beside the script, and records those bytes."""
    here, sol_dir, ids = build_world(
        tmp_path,
        monkeypatch,
        split_items={"l1": [1], "l2": []},
        audit_items={"l1": [0], "l2": []},
    )
    assert sol_dir == here / "sol_answers"
    assert finalize_gold.sol_answer("sol_audit_l1.jsonl") == sol_dir / "sol_audit_l1.jsonl"
    finalize_gold.main()
    freeze = json.loads((here / "GOLD_FREEZE.json").read_text())
    for name in (
        "sol_adjudications_l1.jsonl",
        "sol_adjudications_l2.jsonl",
        "sol_audit_l1.jsonl",
        "sol_audit_l2.jsonl",
    ):
        assert freeze["inputs"][name] == hashlib.sha256((sol_dir / name).read_bytes()).hexdigest()
    # and the committed file's content is what decides the label
    gold = {r["id"]: r for r in map(json.loads, (here / "gold_final.jsonl").open())}
    assert gold[ids[1]]["l1"] == "qualifying"


def test_missing_committed_sol_answer_refuses(tmp_path, monkeypatch):
    """A missing committed copy stops the run — no silent fallback to a staging directory."""
    _, sol_dir, _ = build_world(tmp_path, monkeypatch, audit_items={"l1": [0], "l2": []})
    # A valid copy sits where the removed absolute fallback used to point; it must not be used.
    decoy = tmp_path / "staging"
    decoy.mkdir()
    (decoy / "sol_audit_l1.jsonl").write_bytes((sol_dir / "sol_audit_l1.jsonl").read_bytes())
    monkeypatch.setattr(finalize_gold, "STAGING", decoy, raising=False)
    (sol_dir / "sol_audit_l1.jsonl").unlink()
    with pytest.raises(SystemExit, match="missing committed Sol answer file"):
        finalize_gold.main()


# --- concordance ---


def build_concordance_world(tmp_path, monkeypatch, *, n=5, sol_flips=None, threshold=2):
    sol_flips = sol_flips or {}
    here = tmp_path / "lane"
    fq = tmp_path / "freeze-qualification"
    sol_dir = here / "sol_answers"
    ids = [f"fz-{i:03d}" for i in range(n)]
    write_jsonl(here / "legacy_requeue_71.jsonl", [{"id": i, "prompt": "x"} for i in ids])
    write_jsonl(fq / "adjudications.jsonl", [{"id": i, "label": "qualifying"} for i in ids])
    write_jsonl(
        sol_dir / "sol_legacy_71.jsonl",
        [{"id": i, "answer": sol_flips.get(i, "qualifying")} for i in ids],
    )
    write_jsonl(
        here / "goldset_lane.jsonl",
        [{"item_id": f"x-{i}", "legacy_id": i} for i in ids[:-1]],  # last id not in lane
    )
    monkeypatch.setattr(concordance_71, "HERE", here)
    monkeypatch.setattr(concordance_71, "FREEZE_QUAL", fq)
    monkeypatch.setattr(concordance_71, "EXPECTED_N", n)
    monkeypatch.setattr(concordance_71, "FLIP_FLAG_THRESHOLD", threshold)
    return here, ids


def test_concordance_counts_flips_and_flag(tmp_path, monkeypatch):
    here, ids = build_concordance_world(
        tmp_path,
        monkeypatch,
        sol_flips={ids31: "not_qualifying" for ids31 in []},
    )
    concordance_71.main()
    result = json.loads((here / "CONCORDANCE_71.json").read_text())
    assert result["flips"] == 0 and result["instability_flag_raised"] is False
    assert result["in_lane"] == 4 and len(result["not_in_lane"]) == 1


def test_concordance_flag_raised_above_threshold(tmp_path, monkeypatch):
    here, ids = build_concordance_world(
        tmp_path,
        monkeypatch,
        sol_flips={
            ids_i: "not_qualifying"
            for ids_i in [f"fz-{i:03d}" for i in range(3)]
        },
        threshold=2,
    )
    concordance_71.main()
    result = json.loads((here / "CONCORDANCE_71.json").read_text())
    assert result["flips"] == 3 and result["instability_flag_raised"] is True


def test_concordance_abstention_counts_as_flip(tmp_path, monkeypatch):
    here, ids = build_concordance_world(
        tmp_path, monkeypatch, sol_flips={"fz-001": "cannot_determine"}
    )
    concordance_71.main()
    result = json.loads((here / "CONCORDANCE_71.json").read_text())
    assert result["flips"] == 1 and result["sol_abstentions"] == 1


def test_concordance_coverage_mismatch_refuses(tmp_path, monkeypatch):
    here, _ = build_concordance_world(tmp_path, monkeypatch)
    sol_dir = here / "sol_answers"
    rows = [json.loads(l) for l in (sol_dir / "sol_legacy_71.jsonl").open()]
    write_jsonl(sol_dir / "sol_legacy_71.jsonl", rows[:-1])
    with pytest.raises(SystemExit, match="do not cover the queue exactly"):
        concordance_71.main()


def test_concordance_reads_the_committed_sol_answer(tmp_path, monkeypatch):
    here, _ = build_concordance_world(tmp_path, monkeypatch)
    sol_dir = here / "sol_answers"
    assert concordance_71.sol_answer("sol_legacy_71.jsonl") == sol_dir / "sol_legacy_71.jsonl"
    concordance_71.main()
    result = json.loads((here / "CONCORDANCE_71.json").read_text())
    assert (
        result["inputs_sha256"]["sol_legacy_71.jsonl"]
        == hashlib.sha256((sol_dir / "sol_legacy_71.jsonl").read_bytes()).hexdigest()
    )


def test_concordance_missing_committed_sol_answer_refuses(tmp_path, monkeypatch):
    here, _ = build_concordance_world(tmp_path, monkeypatch)
    sol_dir = here / "sol_answers"
    decoy = tmp_path / "staging"
    decoy.mkdir()
    (decoy / "sol_legacy_71.jsonl").write_bytes((sol_dir / "sol_legacy_71.jsonl").read_bytes())
    monkeypatch.setattr(concordance_71, "STAGING", decoy, raising=False)
    (sol_dir / "sol_legacy_71.jsonl").unlink()
    with pytest.raises(SystemExit, match="missing committed Sol answer file"):
        concordance_71.main()


# --- escalation path (audit gate failure) ---


def build_escalated_world(tmp_path, monkeypatch, *, escalation_answers=None, write_escalation=True, drop_one=False):
    """L2 audit fails (2 disagreements); escalation file covers the unanimous non-audit rest."""
    here, sol_dir, ids = build_world(
        tmp_path,
        monkeypatch,
        split_items={"l1": [], "l2": [1]},
        audit_items={"l1": [], "l2": [0, 3]},
        sol_audit_answers={"l1": {}, "l2": {0: "attempt", 3: "attempt"}},  # both flip vs no_attempt
    )
    # unanimous non-audit L2 items: everything except split [1] and audits [0,3]
    rest = [i for i in range(6) if i not in (0, 1, 3)]
    if drop_one:
        rest = rest[:-1]
    escalation_answers = escalation_answers or {}
    if write_escalation:
        write_jsonl(
            sol_dir / "sol_escalation_l2.jsonl",
            [
                {
                    "request_id": finalize_gold.request_id(ids[i], "l2"),
                    "answer": escalation_answers.get(i, "no_attempt"),
                }
                for i in rest
            ],
        )
    return here, sol_dir, ids


def test_escalation_full_coverage_finalizes(tmp_path, monkeypatch):
    here, _, ids = build_escalated_world(tmp_path, monkeypatch, escalation_answers={2: "attempt"})
    finalize_gold.main()
    gold = {r["id"]: r for r in map(json.loads, (here / "gold_final.jsonl").open())}
    prov = {r["id"]: r for r in map(json.loads, (here / "gold_provenance.jsonl").open())}
    # audit answers stand: items 0 and 3 take Sol's audit "attempt" over unanimous "no_attempt"
    assert gold[ids[0]]["l2"] == "attempt" and prov[ids[0]]["l2_source"] == "audit_adjudicated"
    # split item takes the split adjudication
    assert gold[ids[1]]["l2"] == "attempt" and prov[ids[1]]["l2_source"] == "adjudicated"
    # escalated item takes Sol's escalation answer
    assert gold[ids[2]]["l2"] == "attempt" and prov[ids[2]]["l2_source"] == "escalation_adjudicated"
    assert gold[ids[4]]["l2"] == "no_attempt"
    # L1 unaffected: unanimous auto-accept
    assert prov[ids[0]]["l1_source"] == "unanimous"
    freeze = json.loads((here / "GOLD_FREEZE.json").read_text())
    assert freeze["track_modes"] == {
        "l1": "unanimous_auto_accept",
        "l2": "fully_adjudicated_after_audit_gate_failure",
    }
    assert freeze["tallies"]["l2"] == {
        "adjudicated": 1,
        "audit_adjudicated": 2,
        "escalation_adjudicated": 3,
    }
    assert len(freeze["audit_gate"]["l2"]["disagreements"]) == 2
    assert "sol_escalation_l2.jsonl" in freeze["inputs"]


def test_escalation_missing_file_refuses(tmp_path, monkeypatch):
    build_escalated_world(tmp_path, monkeypatch, write_escalation=False)
    with pytest.raises(SystemExit, match="AUDIT GATE FAILED for track l2"):
        finalize_gold.main()


def test_escalation_incomplete_coverage_refuses(tmp_path, monkeypatch):
    build_escalated_world(tmp_path, monkeypatch, drop_one=True)
    with pytest.raises(SystemExit, match="escalation answers do not cover"):
        finalize_gold.main()


def test_escalation_abstention_triggers_ratification_d(tmp_path, monkeypatch):
    build_escalated_world(tmp_path, monkeypatch, escalation_answers={2: "cannot_determine"})
    with pytest.raises(SystemExit, match="RATIFICATION \\(d\\) TRIGGERED"):
        finalize_gold.main()
